"""Validate measured-pose scenario initialization; not replay or original-start acceptance."""
from pathlib import Path
import hashlib,json,os
import torch
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
from isaaclab.managers import SceneEntityCfg
from support_math_v128 import limit_reference,triangle_margin
from leg_kinematics_v128 import LegKinematics,rotate_vector
from isaaclab.utils.math import quat_apply
class StageHold:
    def __init__(self,env,quota):
        self.env,self.quota=env,quota;self.robot=env.scene['robot'];self.box=env.scene['box']
        self.term=env.action_manager.get_term('joint_pos');self.c=self.term.controller
        bank=json.loads(Path(os.environ['STAGE_BANK']).read_text());assert bank['joint_names']==list(self.robot.joint_names)
        self.bank_hash=hashlib.sha256(Path(os.environ['STAGE_BANK']).read_bytes()).hexdigest()
        t=lambda key:torch.tensor([x[key] for x in bank['snapshots']],device=env.device,dtype=torch.float32)
        root=self.robot.data.default_root_state.clone();root[:,:3]=t('robot_position')+env.scene.env_origins;root[:,3:7]=t('robot_quaternion');root[:,7:10]=t('robot_velocity');root[:,10:13]=t('robot_angular_velocity')
        self.robot.write_root_state_to_sim(root);self.robot.write_joint_state_to_sim(t('robot_joint_position'),t('robot_joint_velocity'))
        boxroot=self.box.data.default_root_state.clone();boxroot[:,:3]=t('box_position')+env.scene.env_origins;boxroot[:,3:7]=t('box_quaternion');boxroot[:,7:]=0.
        self.box.write_root_state_to_sim(boxroot)
        self.target=t('robot_joint_position_target');self.robot.set_joint_position_target(self.target)
        self.origin=root[:,:3].clone();self.orientation=root[:,3:7].clone()
        ids=self.term.delegate._joint_ids
        if isinstance(ids,slice):ids=list(range(self.robot.num_joints))[ids]
        self.ids=list(ids)
        self.hand=SceneEntityCfg('robot',body_names='end_effector');self.hand.resolve(env.scene)
        self.sensor_ids=env.scene['contact_forces'].find_bodies([f'{x}_foot' for x in ('FL','FR','RL','RR')],preserve_order=True)[0]
        self.old_apply=self.c.apply;self.c.apply=self.apply
        self.c.lock_arm_on_contact=True
        self.count=torch.zeros(env.num_envs,dtype=torch.long,device=env.device);self.three=self.count.clone();self.air=self.count.clone()
        self.age=torch.zeros(env.num_envs,device=env.device);self.min_clear=torch.full_like(self.age,float('inf'));self.max_ratio=self.age.clone();self.max_vz=self.age.clone();self.max_force=self.age.clone();self.max_sumforce=self.age.clone();self.max_drift=self.age.clone();self.halted=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device);self.trace=[]
        self.arm_ref=t('debug_reference_post_geometry');self.c.reference=self.arm_ref.clone()
        # Restore a steady-target history without changing sampled delay values.
        self.buffer_audit=[]
        self.robot.set_joint_velocity_target(torch.zeros_like(self.target))
        self.robot.set_joint_effort_target(torch.zeros_like(self.target))
        for name,actuator in self.robot.actuators.items():
            for field,target in [('positions_delay_buffer',self.target),('velocities_delay_buffer',torch.zeros_like(self.target)),('efforts_delay_buffer',torch.zeros_like(self.target))]:
                buffer=getattr(actuator,field,None)
                if buffer is None:continue
                lags=buffer.time_lags.clone();buffer.reset()
                value=target[:,actuator.joint_indices]
                for _ in range(buffer.history_length+1): delayed=buffer.compute(value)
                assert torch.equal(lags,buffer.time_lags) and torch.equal(delayed,value)
                self.buffer_audit.append(dict(actuator=name,buffer=field,time_lags=lags.cpu().tolist(),history_length=buffer.history_length,maximum_target_error=float((delayed-value).abs().max())))
        self.prephysics=[]
        env.scene.write_data_to_sim()
        self.leg_ids=self.robot.find_joints([f'{x}_{y}_joint' for x in ('FL','FR','RL','RR') for y in ('hip','thigh','calf')],preserve_order=True)[0]
        self.feet=self.robot.find_bodies([f'{x}_foot' for x in ('FL','FR','RL','RR')],preserve_order=True)[0]
        self.kin=LegKinematics.from_usd(self.robot.cfg.spawn.usd_path,env.device)
        self.mass=self.robot.root_physx_view.get_masses().to(env.device);self.weight=self.mass.sum(1)*9.81
        self.selected=torch.zeros_like(self.halted);self.selected[[0,2,3,4]]=True
        self.started=torch.zeros_like(self.halted);self.start_time=torch.full_like(self.age,-1.);self.drive_age=self.age.clone();self.finish_age=self.age.clone();self.contact_age=self.age.clone()
        self.reference=self.target[:,self.leg_ids].clone();self.velocity=torch.zeros_like(self.reference);self.body_ref=self.origin.clone();self.last_ref=self.origin.clone();self.initial_leg=self.reference.clone()
        self.fixed_arm=self.arm_ref.clone();self.anchors=None;self.box_origin=None;self.axis=None;self.max_hand=self.age.clone();self.max_foot_drift=self.age.clone();self.max_box=self.age.clone();self.max_leg_step=self.age.clone();self.max_leg_acc=self.age.clone()
        self.command_valid=torch.ones_like(self.halted);self.first_contact=torch.full_like(self.age,-1.);self.trace=[]
        self.terminal_stopped=torch.zeros_like(self.halted);self.stop_targets=self.target.clone();self.stop_times=torch.full_like(self.age,-1.);self.stop_trace=[]

    def apply(self,actions):
        out=self.old_apply(actions);r=self.robot;c=self.c;dt=self.env.step_dt;active=self.quota.active;now=self.env.episode_length_buf*dt
        feet=r.data.body_pos_w[:,self.feet];force=self.env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids];fz=force[:,:,2]
        hand_sensor=self.env.scene['box_contact_hand'].data;hand_force=hand_sensor.force_matrix_w.sum(dim=(1,2));fn=hand_force.norm(dim=1);legal=box_push.hand_contact(self.env,self.hand)
        contact_point=hand_sensor.contact_pos_w[:,0,0];point=torch.where(torch.isfinite(contact_point).all(1)[:,None],contact_point,r.data.body_pos_w[:,c.hand_id])
        ratio=(r.data.applied_torque.abs()/r.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        calm=(r.data.root_lin_vel_w.norm(dim=1)<.025)&(r.data.root_ang_vel_w.norm(dim=1)<.1)&(r.data.projected_gravity_b[:,2]<-.96)
        measured=active&(self.env.episode_length_buf>0)
        if self.anchors is None:
            self.anchors=feet.clone();self.box_origin=self.box.data.root_pos_w.clone();axis=torch.zeros_like(self.origin);axis[:,0]=1.;self.axis=quat_apply(self.box.data.root_quat_w,axis)
        drift=(feet-self.anchors).norm(dim=2).amax(1)
        com=(r.data.body_com_pos_w*self.mass[:,:,None]).sum(1)/self.mass.sum(1)[:,None]
        margin=triangle_margin(com[:,:2],feet[:,[0,1,3,2],:2])[0].amin(1)
        body_error=(r.data.root_pos_w-self.body_ref).norm(dim=1)
        safe=measured&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(c.clearance_distance>=.10)&(body_error<.01)&(drift<.01)&(margin>=.025)&(fn<=22.)
        unsafe=(ratio>=.98)|(c.geometry_clearance<.055)|(c.clearance_distance<.10)|(body_error>=.01)|(drift>=.01)|(fn>22.)|~torch.isfinite(r.data.joint_pos).all(1)
        self.halted|=measured&self.selected&unsafe
        self.contact_age=torch.where(measured,torch.where(legal,self.contact_age+dt,0.),self.contact_age)
        self.first_contact=torch.where(measured&legal&(self.first_contact<0),now,self.first_contact)
        ready=safe&legal&self.selected&~self.halted
        self.age=torch.where(~self.started,torch.where(ready,self.age+dt,0.),self.age)
        new=ready&(self.age>=2.)&(now>=3.)&~self.started
        self.started|=new;self.start_time=torch.where(new,now,self.start_time)
        self.origin=torch.where(new[:,None],r.data.root_pos_w,self.origin);self.orientation=torch.where(new[:,None],r.data.root_quat_w,self.orientation)
        self.anchors=torch.where(new[:,None,None],feet,self.anchors)
        moving=active&self.started
        local_time=(now-self.start_time).clamp_min(0.)
        ramp=(local_time/2.).clamp(0.,1.);ramp=ramp**3*(10.-15.*ramp+6.*ramp*ramp)
        u=(self.drive_age/8.).clamp(0.,1.);blend=u**3*(10.-15.*u+6.*u*u)
        proposal=self.origin+.05*blend[:,None]*self.axis
        proposal=torch.where((moving&~self.halted)[:,None],proposal,self.body_ref)
        ref_velocity=(proposal[:,:2]-self.body_ref[:,:2])/dt
        acceleration=4.*(ref_velocity-r.data.root_lin_vel_w[:,:2])+8.*(proposal[:,:2]-r.data.root_pos_w[:,:2])
        acceleration*= (.4/acceleration.norm(dim=1).clamp_min(.4))[:,None]
        # Four-foot wrench balance includes actual hand reaction at its measured contact point.
        n=self.env.num_envs;eye=torch.eye(3,device=self.env.device,dtype=feet.dtype);rel=feet-com[:,None]
        skew=torch.zeros((n,4,3,3),device=self.env.device,dtype=feet.dtype)
        skew[:,:,0,1]=-rel[:,:,2];skew[:,:,0,2]=rel[:,:,1];skew[:,:,1,0]=rel[:,:,2];skew[:,:,1,2]=-rel[:,:,0];skew[:,:,2,0]=-rel[:,:,1];skew[:,:,2,1]=rel[:,:,0]
        matrix=torch.cat((eye[None,None].expand(n,4,-1,-1),skew),dim=2).permute(0,2,1,3).reshape(n,6,12)
        target_force=torch.cat((self.weight[:,None]*acceleration/9.81,self.weight[:,None]),dim=1)-hand_force
        target_moment=-torch.cross(point-com,hand_force,dim=1)
        rhs=torch.cat((target_force,target_moment),dim=1)
        loads=(matrix.transpose(1,2)@torch.linalg.solve(matrix@matrix.transpose(1,2)+1e-7*torch.eye(6,device=self.env.device)[None],rhs[:,:,None])).squeeze(2).reshape(n,4,3)
        residual=(matrix@loads.reshape(n,12,1)).squeeze(2)-rhs
        feasible=(residual.abs().amax(1)<.02)&(loads[:,:,2]>8.).all(1)&(loads[:,:,:2].abs().sum(2)<=.4*loads[:,:,2]).all(1)
        qlocal=rotate_vector(self.orientation[:,None],self.anchors-proposal[:,None],inverse=True);nominal=self.kin.inverse(qlocal)
        fk_ok=(self.kin.forward(nominal)-qlocal).norm(dim=2).amax(1)<.001
        jac=r.root_physx_view.get_jacobians();gravity=r.root_physx_view.get_gravity_compensation_forces();dof_offset=0 if r.is_fixed_base else 6;grav_offset=0 if gravity.shape[1]==r.num_joints else 6
        torque=torch.zeros_like(nominal)
        for leg in range(4):
            ids=self.leg_ids[leg*3:leg*3+3];body=self.feet[leg]-(1 if r.is_fixed_base else 0);j=jac[:,body,:3][:,:,[i+dof_offset for i in ids]]
            torque[:,leg]=gravity[:,[i+grav_offset for i in ids]]-(j.transpose(1,2)@loads[:,leg,:,None]).squeeze(2)
        desired=(nominal+torque/30.).reshape(n,12);desired=torch.lerp(self.initial_leg,desired,ramp[:,None])
        bounds=r.data.soft_joint_pos_limits[:,self.leg_ids];excess=torch.maximum(bounds[...,0]-desired,desired-bounds[...,1]).clamp_min(0).amax(1)
        valid=feasible&fk_ok&(excess<1e-6)&torch.isfinite(desired).all(1)
        self.command_valid=valid;self.halted|=moving&~valid
        desired=torch.where((moving&valid&~self.halted)[:,None],desired,self.reference)
        previous=self.reference.clone();prev_velocity=self.velocity.clone()
        q,v=limit_reference(self.reference,self.velocity,desired,bounds[...,0],bounds[...,1],torch.full_like(desired,.8),torch.full_like(desired,3.),dt)
        self.reference=torch.where(moving[:,None],q,self.reference);self.velocity=torch.where(moving[:,None],v,self.velocity)
        self.body_ref=torch.where((moving&valid&~self.halted)[:,None],proposal,self.body_ref)
        physical=self.target.clone();physical[:,self.leg_ids]=self.reference
        cols=c.joint_ids if gravity.shape[1]==r.num_joints else c.jacobian_columns
        # Locked arm reference with original gravity compensation. No additional arm pressing.
        arm=torch.where(self.selected[:,None],self.fixed_arm,self.target[:,c.joint_ids]-gravity[:,cols]/c.stiffness)
        limits=r.data.soft_joint_pos_limits[:,c.joint_ids].clone();limits[:,3,0]=limits[:,3,0].clamp_min(.8)
        projected,clear,blocked=c.geometry_shield.project(r.data.joint_pos[:,c.joint_ids].cpu().numpy(),r.data.joint_vel[:,c.joint_ids].cpu().numpy(),arm.cpu().numpy(),limits[...,0].cpu().numpy(),limits[...,1].cpu().numpy(),active.cpu().numpy())
        projected=torch.as_tensor(projected,device=self.env.device,dtype=arm.dtype);clear=torch.as_tensor(clear,device=self.env.device,dtype=arm.dtype);correction=(projected-arm).abs().amax(1)
        self.halted|=measured&self.selected&(correction>1e-6)
        physical[:,c.joint_ids]=projected+gravity[:,cols]/c.stiffness
        out[:]=(physical[:,self.ids]-r.data.default_joint_pos[:,self.ids])/c.scale
        c.reference=projected;c.geometry_clearance=clear;c.geometry_blocked=torch.as_tensor(blocked,device=self.env.device);c.debug_reference_post_geometry=projected.clone()
        advance=ready&moving&valid&(local_time>=3.)&(self.contact_age>=2.)&(body_error<.01)&(fn<21.)
        self.drive_age+=dt*advance
        box_delta=((self.box.data.root_pos_w-self.box_origin)*self.axis).sum(1);body_delta=((r.data.root_pos_w-self.origin)*self.axis).sum(1)
        finished=ready&moving&valid&(box_delta>=.01)&(self.box.data.root_lin_vel_w.norm(dim=1)<.08)&(u>=1.)
        self.finish_age=torch.where(active,torch.where(finished,self.finish_age+dt,0.),self.finish_age)
        self.count+=measured;self.three+=measured&((fz>8.).sum(1)>=3);self.air+=measured&(fz<=2).all(1)
        self.min_clear=torch.where(active,torch.minimum(self.min_clear,clear),self.min_clear);self.max_ratio=torch.maximum(self.max_ratio,torch.where(active,ratio,0.));self.max_vz=torch.maximum(self.max_vz,torch.where(active,r.data.root_lin_vel_w[:,2].abs(),0.));self.max_force=torch.maximum(self.max_force,torch.where(active,force.norm(dim=2).amax(1),0.));self.max_sumforce=torch.maximum(self.max_sumforce,torch.where(active,force.sum(1).norm(dim=1),0.));self.max_drift=torch.maximum(self.max_drift,torch.where(active,body_error,0.));self.max_hand=torch.maximum(self.max_hand,torch.where(active,fn,0.));self.max_foot_drift=torch.maximum(self.max_foot_drift,torch.where(active,drift,0.));self.max_box=torch.maximum(self.max_box,torch.where(active,box_delta,0.))
        self.max_leg_step=torch.maximum(self.max_leg_step,(self.reference-previous).abs().amax(1));self.max_leg_acc=torch.maximum(self.max_leg_acc,((self.velocity-prev_velocity)/dt).abs().amax(1))
        for i in torch.where(active)[0].tolist():self.trace.append(dict(env_id=i,time_s=float(now[i]),sensor_valid=bool(measured[i]),selected=bool(self.selected[i]),started=bool(self.started[i]),legal_contact=bool(legal[i]),contact_hold_s=float(self.contact_age[i]),final_hold_s=float(self.finish_age[i]),hand_force_N=hand_force[i].cpu().tolist(),hand_force_norm_N=float(fn[i]),geometry_m=float(clear[i]),torque_ratio=float(ratio[i]),foot_force_z_N=fz[i].cpu().tolist(),foot_drift_m=float(drift[i]),body_error_m=float(body_error[i]),body_forward_m=float(body_delta[i]),body_reference_forward_m=float(.05*blend[i]),box_forward_m=float(box_delta[i]),box_speed_m_s=float(self.box.data.root_lin_vel_w[i].norm()),support_margin_m=float(margin[i]),wrench_residual=residual[i].cpu().tolist(),support_feasible=bool(feasible[i]),command_valid=bool(valid[i]),halted=bool(self.halted[i]),advance=bool(advance[i]),shield_correction_rad=float(correction[i])))
        # A terminated episode keeps its physical state and last commanded target.
        # This is a separately measured stop diagnostic, never a task success.
        hold=(self.stop_targets[:,self.ids]-r.data.default_joint_pos[:,self.ids])/c.scale
        out=torch.where(self.terminal_stopped[:,None],hold,out)
        return out
    def stop_for_terminal(self,env_ids):
        selected=env_ids[~self.terminal_stopped[env_ids]]
        self.stop_targets[selected]=self.robot.data.joint_pos_target[selected].clone()
        self.stop_times[selected]=self.env.episode_length_buf[selected]*self.env.step_dt
        self.terminal_stopped[selected]=True
    def record_stop(self):
        r=self.robot;now=self.env.episode_length_buf*self.env.step_dt
        forces=self.env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids]
        for i in torch.where(self.terminal_stopped)[0].tolist():
            self.stop_trace.append(dict(env_id=i,time_s=float(now[i]),since_stop_s=float(now[i]-self.stop_times[i]),robot_position=(r.data.root_pos_w[i]-self.env.scene.env_origins[i]).cpu().tolist(),robot_gravity=r.data.projected_gravity_b[i].cpu().tolist(),robot_velocity=r.data.root_lin_vel_w[i].cpu().tolist(),angular_velocity=r.data.root_ang_vel_w[i].cpu().tolist(),foot_force=forces[i].cpu().tolist(),geometry_m=float(self.c.geometry_shield.clearance(r.data.joint_pos[i,self.c.joint_ids].cpu().numpy())),torque_ratio=float((r.data.applied_torque[i].abs()/r.data.joint_effort_limits[i].clamp_min(1e-6)).max()),target_change_rad=float((r.data.joint_pos_target[i]-self.stop_targets[i]).abs().max()),termination_flags={name:bool(self.env.termination_manager.get_term(name)[i]) for name in self.env.termination_manager.active_terms}))
    def summary(self):
        (Path(os.environ['STAGE_BANK']).parent/'stage-trace.json').write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        (Path(os.environ['STAGE_BANK']).parent/'post-terminal-trace.json').write_text(json.dumps(self.stop_trace,separators=(',',':'))+'\n')
        fields=dict(selected=self.selected,started=self.started,initial_stable_s=self.age,first_contact_s=self.first_contact,final_contact_hold_s=self.contact_age,final_healthy_hold_s=self.finish_age,body_drive_age_s=self.drive_age,maximum_box_forward_m=self.max_box,control_samples=self.count,three_support_samples=self.three,airborne_samples=self.air,maximum_torque_ratio=self.max_ratio,minimum_geometry_m=self.min_clear,maximum_abs_vz_m_s=self.max_vz,maximum_foot_resultant_N=self.max_force,maximum_total_foot_vector_norm_N=self.max_sumforce,maximum_body_reference_error_m=self.max_drift,maximum_foot_drift_m=self.max_foot_drift,maximum_hand_force_N=self.max_hand,maximum_leg_reference_step_rad=self.max_leg_step,maximum_leg_reference_acceleration_rad_s2=self.max_leg_acc,halted=self.halted)
        return dict(scope='24s fresh stage-start3kg/0.3 planted body forward PUSH diagnostic. Only previously stable contact env0/2/3/4 selected, other4 remain hold controls. Actual contact/support rechecked, body advances5cm over8s while arm reference holds; measured hand wrench included in stance.22N force stop validated statically. Requires>=1cm actual box displacement and2s end hold. No full0.6m PUSH, no original-start or sim2sim acceptance.',helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),bank_sha256=self.bank_hash,delay_buffer_initialization=self.buffer_audit,**{k:v.cpu().tolist() for k,v in fields.items()})
