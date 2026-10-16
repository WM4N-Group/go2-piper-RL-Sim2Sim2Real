"""Validate measured-pose scenario initialization; not replay or original-start acceptance."""
from pathlib import Path
import hashlib,json,os
import torch
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
from isaaclab.managers import SceneEntityCfg
from support_math_v128 import limit_reference,triangle_margin
from isaaclab.utils.math import compute_pose_error,quat_apply
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
        self.started=torch.zeros_like(self.halted);self.locked=self.started.clone();self.press_age=self.age.clone();self.contact_age=self.age.clone();self.max_contact_age=self.age.clone();self.initial_age=self.age.clone();self.first_contact=torch.full_like(self.age,-1.)
        self.reference=self.arm_ref.clone();self.reference_velocity=torch.zeros_like(self.reference);self.locked_reference=self.reference.clone();self.max_hand_force=self.age.clone();self.max_foot_drift=self.age.clone()
        self.feet=self.robot.find_bodies([f'{x}_foot' for x in ('FL','FR','RL','RR')],preserve_order=True)[0]
        self.anchor=None;self.hand_start=None;self.quat_start=None;self.axis=None;self.trace=[]

    def apply(self,actions):
        out=self.old_apply(actions);r=self.robot;c=self.c;dt=self.env.step_dt;active=self.quota.active;now=self.env.episode_length_buf*dt
        force=self.env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids];fz=force[:,:,2]
        handforce=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2));fn=handforce.norm(dim=1);legal=box_push.hand_contact(self.env,self.hand)
        ratio=(r.data.applied_torque.abs()/r.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        calm=(r.data.root_lin_vel_w.norm(dim=1)<.025)&(r.data.root_ang_vel_w.norm(dim=1)<.1)&(r.data.projected_gravity_b[:,2]<-.96)
        body_error=(r.data.root_pos_w-self.origin).norm(dim=1);measured=active&(self.env.episode_length_buf>0)
        if self.anchor is None:
            self.anchor=r.data.body_pos_w[:,self.feet].clone();self.hand_start=r.data.body_pos_w[:,c.hand_id].clone();self.quat_start=r.data.body_quat_w[:,c.hand_id].clone()
            axis=torch.zeros_like(self.hand_start);axis[:,0]=1.;self.axis=quat_apply(self.box.data.root_quat_w,axis)
        drift=(r.data.body_pos_w[:,self.feet]-self.anchor).norm(dim=2).amax(1)
        masses=r.root_physx_view.get_masses().to(self.env.device);com=(r.data.body_com_pos_w*masses[:,:,None]).sum(1)/masses.sum(1)[:,None]
        margin=triangle_margin(com[:,:2],r.data.body_pos_w[:,self.feet][:,[0,1,3,2],:2])[0].amin(1)
        stable=measured&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(body_error<.01)&(drift<.01)&(margin>=.025)
        self.halted|=measured&((ratio>=.98)|(c.geometry_clearance<.055)|(c.clearance_distance<.10)|(body_error>=.01)|(drift>=.01)|(fn>20.)|~torch.isfinite(r.data.joint_pos).all(1))
        init=stable&(fn<=1.)&~legal&~self.halted&~self.started
        self.initial_age=torch.where(~self.started,torch.where(init,self.initial_age+dt,0.),self.initial_age)
        new=init&(self.initial_age>=2.)&(now>=3.)
        self.started|=new
        self.hand_start=torch.where(new[:,None],r.data.body_pos_w[:,c.hand_id],self.hand_start);self.quat_start=torch.where(new[:,None],r.data.body_quat_w[:,c.hand_id],self.quat_start)
        fresh=active&self.started&legal&~self.locked&~self.halted
        self.locked_reference=torch.where(fresh[:,None],self.reference,self.locked_reference);self.locked|=fresh;self.first_contact=torch.where(fresh,now,self.first_contact)
        u=(self.press_age/8.).clamp(0.,1.);distance=.003*u**3*(10.-15.*u+6.*u*u)
        hp=self.hand_start+distance[:,None]*self.axis
        pe,re=compute_pose_error(r.data.body_pos_w[:,c.hand_id],r.data.body_quat_w[:,c.hand_id],hp,self.quat_start,rot_error_type='axis_angle')
        ep=pe.norm(dim=1);er=re.norm(dim=1);normal=(pe*self.axis).sum(1);tangent=(pe-normal[:,None]*self.axis).norm(dim=1)
        j=r.root_physx_view.get_jacobians()[:,c.jacobian_body][:,:,c.jacobian_columns];weights=torch.tensor([1.,1.,1.,.25,.25,.25],device=self.env.device);j=j*weights[None,:,None]
        error=torch.cat((pe,re),1)*weights;eye=torch.eye(6,device=self.env.device)[None].expand(self.env.num_envs,-1,-1)
        pinv=j.transpose(1,2)@torch.linalg.solve(j@j.transpose(1,2)+.0025**2*eye,eye)
        delta=(pinv@error[:,:,None]).squeeze(2);delta*= (.04/delta.abs().amax(1).clamp_min(.04))[:,None]
        desired=r.data.joint_pos[:,c.joint_ids]+delta
        desired=torch.where(self.locked[:,None],self.locked_reference,desired);desired=torch.where(self.halted[:,None],self.reference,desired)
        gravity=r.root_physx_view.get_gravity_compensation_forces();cols=c.joint_ids if gravity.shape[1]==r.num_joints else c.jacobian_columns
        fixed_ref=self.target[:,c.joint_ids]-gravity[:,cols]/c.stiffness
        desired=torch.where(self.started[:,None],desired,fixed_ref)
        limits=r.data.soft_joint_pos_limits[:,c.joint_ids].clone();limits[:,3,0]=limits[:,3,0].clamp_min(.8)
        q,v=limit_reference(self.reference,self.reference_velocity,desired,limits[...,0],limits[...,1],torch.full_like(self.reference,.25),torch.full_like(self.reference,3.),dt)
        q=torch.where(self.started[:,None],q,fixed_ref);v=torch.where(self.started[:,None],v,torch.zeros_like(v))
        projected,clear,blocked=c.geometry_shield.project(r.data.joint_pos[:,c.joint_ids].cpu().numpy(),r.data.joint_vel[:,c.joint_ids].cpu().numpy(),q.cpu().numpy(),limits[...,0].cpu().numpy(),limits[...,1].cpu().numpy(),active.cpu().numpy())
        projected=torch.as_tensor(projected,device=self.env.device,dtype=q.dtype);clear=torch.as_tensor(clear,device=self.env.device,dtype=q.dtype);correction=(projected-q).abs().amax(1)
        self.halted|=active&(correction>1e-6);accept=active&(correction<=1e-6)
        self.reference=torch.where(accept[:,None],q,self.reference);self.reference_velocity=torch.where(accept[:,None],v,torch.zeros_like(v))
        physical=self.target.clone();physical[:,c.joint_ids]=self.reference+gravity[:,cols]/c.stiffness
        out[:]=(physical[:,self.ids]-r.data.default_joint_pos[:,self.ids])/c.scale
        c.reference=self.reference.clone();c.geometry_clearance=clear;c.geometry_blocked=torch.as_tensor(blocked,device=self.env.device);c.debug_reference_post_geometry=self.reference.clone()
        advance=stable&self.started&~self.locked&~self.halted&(ep<.004)&(er<.04)&(fn<1.)
        self.press_age+=dt*advance
        healthy=stable&self.started&self.locked&legal&~self.halted&(clear>=.055)&(fn<=20.)
        self.contact_age=torch.where(active,torch.where(healthy,self.contact_age+dt,0.),self.contact_age);self.max_contact_age=torch.maximum(self.max_contact_age,self.contact_age)
        self.count+=measured;self.three+=measured&((fz>8.).sum(1)>=3);self.air+=measured&(fz<=2).all(1)
        self.min_clear=torch.where(active,torch.minimum(self.min_clear,clear),self.min_clear);self.max_ratio=torch.maximum(self.max_ratio,torch.where(active,ratio,0.));self.max_vz=torch.maximum(self.max_vz,torch.where(active,r.data.root_lin_vel_w[:,2].abs(),0.));self.max_force=torch.maximum(self.max_force,torch.where(active,force.norm(dim=2).amax(1),0.));self.max_sumforce=torch.maximum(self.max_sumforce,torch.where(active,force.sum(1).norm(dim=1),0.));self.max_drift=torch.maximum(self.max_drift,torch.where(active,body_error,0.));self.max_hand_force=torch.maximum(self.max_hand_force,torch.where(active,fn,0.));self.max_foot_drift=torch.maximum(self.max_foot_drift,torch.where(active,drift,0.))
        for i in torch.where(active)[0].tolist():self.trace.append(dict(env_id=i,time_s=float(now[i]),sensor_valid=bool(measured[i]),started=bool(self.started[i]),legal_contact=bool(legal[i]),locked=bool(self.locked[i]),contact_hold_s=float(self.contact_age[i]),initial_stable_s=float(self.initial_age[i]),hand_force_N=handforce[i].cpu().tolist(),normal_force_N=float(-(handforce[i]*self.axis[i]).sum()),torque_ratio=float(ratio[i]),geometry_m=float(clear[i]),body_error_m=float(body_error[i]),foot_drift_m=float(drift[i]),foot_force_z_N=fz[i].cpu().tolist(),support_margin_m=float(margin[i]),normal_error_m=float(normal[i]),tangent_error_m=float(tangent[i]),reference_distance_m=float(distance[i]),shield_correction_rad=float(correction[i]),halted=bool(self.halted[i])))
        return out
    def summary(self):
        (Path(os.environ['STAGE_BANK']).parent/'stage-trace.json').write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(started=self.started,locked=self.locked,initial_stable_s=self.initial_age,first_contact_s=self.first_contact,final_healthy_hold_s=self.contact_age,maximum_contact_hold_s=self.max_contact_age,control_samples=self.count,three_support_samples=self.three,airborne_samples=self.air,maximum_torque_ratio=self.max_ratio,minimum_geometry_m=self.min_clear,maximum_abs_vz_m_s=self.max_vz,maximum_foot_resultant_N=self.max_force,maximum_total_foot_vector_norm_N=self.max_sumforce,maximum_body_drift_m=self.max_drift,maximum_foot_drift_m=self.max_foot_drift,maximum_hand_force_N=self.max_hand_force,halted=self.halted)
        return dict(scope='16s fresh stage-start contact-compliance diagnostic from measured v185 terminal states. Fixed saved leg PD targets; not full v179 body controller, not equivalent replay or original-start success. Native collision, delay, geometry and actual contact gates retained;3mm bounded normal reference, original4mm overall tracking limit. No sustained push.',helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),bank_sha256=self.bank_hash,delay_buffer_initialization=self.buffer_audit,contact_sample_scope='Physical contact counts after first step; torque/geometry include initialization.',**{k:v.cpu().tolist() for k,v in fields.items()})
