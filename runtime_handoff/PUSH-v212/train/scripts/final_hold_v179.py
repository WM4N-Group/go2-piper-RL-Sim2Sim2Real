"""Opt-in preparation weight transfer; no swing or PUSH task completion."""
from pathlib import Path
import hashlib
import json
import os
import torch
from leg_kinematics_v128 import LegKinematics, rotate_vector
from support_math_v128 import (triangle_margin,inset_support_target,balanced_acceleration_loads,
                              feedback_unload,UnloadForceTrim,limit_reference)

class SupportTransfer:
    def __init__(self,env,quota,entry_hold):
        self.env,self.quota,self.entry=env,quota,entry_hold
        self.robot=env.scene['robot'];term=env.action_manager.get_term('joint_pos');self.c=term.controller
        self.old_apply,self.old_reset=self.c.apply,self.c.reset
        legs=('FL','FR','RL','RR')
        joint_names=[f'{leg}_{part}_joint' for leg in legs for part in ('hip','thigh','calf')]
        self.ids=self.robot.find_joints(joint_names,preserve_order=True)[0]
        action_ids=self.robot.find_joints(env.cfg.actions.joint_pos.joint_names,preserve_order=True)[0]
        delegate_ids=term.delegate._joint_ids
        if isinstance(delegate_ids,slice):delegate_ids=list(range(self.robot.num_joints))[delegate_ids]
        assert list(delegate_ids)==action_ids
        self.slots=[action_ids.index(i) for i in self.ids]
        assert set(self.slots)==set(self.c.leg_slots)
        assert float(self.robot.cfg.actuators['base_legs'].stiffness)==30.
        self.feet=self.robot.find_bodies([f'{leg}_foot' for leg in legs],preserve_order=True)[0]
        self.sensor_ids=env.scene['contact_forces'].find_bodies([f'{leg}_foot' for leg in legs],preserve_order=True)[0]
        self.arm_bodies=self.robot.find_bodies('link[2-6]|end_effector')[0]
        self.protected=self.robot.find_bodies('base|.*_(hip|thigh|calf|foot)')[0]
        self.kin=LegKinematics.from_usd(self.robot.cfg.spawn.usd_path,env.device)
        fk=rotate_vector(self.robot.data.root_quat_w[:,None],self.kin.forward(self.robot.data.joint_pos[:,self.ids].reshape(-1,4,3)))+self.robot.data.root_pos_w[:,None]
        self.initial_fk_error=float((fk-self.robot.data.body_pos_w[:,self.feet]).norm(dim=-1).max())
        assert self.initial_fk_error<1e-4,self.initial_fk_error
        self.mass=self.robot.root_physx_view.get_masses().to(env.device)
        self.weight=self.mass.sum(1)*9.81
        n=env.num_envs;dev=env.device
        self.active=torch.zeros(n,dtype=torch.bool,device=dev)
        self.first_start=torch.full((n,),-1.,device=dev)
        self.origin=torch.zeros((n,3),device=dev);self.body_ref=self.origin.clone();self.body_goal=self.origin.clone()
        self.orientation=torch.zeros((n,4),device=dev)
        self.anchors=torch.zeros((n,4,3),device=dev)
        self.reference=torch.zeros((n,12),device=dev);self.velocity=self.reference.clone();self.initial_reference=self.reference.clone()
        self.max_velocity=torch.full((1,12),.8,device=dev);self.max_acceleration=torch.full((1,12),3.,device=dev)
        self.unloading=torch.zeros(n,device=dev);self.age=self.unloading.clone();self.ready_age=self.unloading.clone()
        self.trim=UnloadForceTrim(n,dev);self.selected=torch.zeros(n,dtype=torch.long,device=dev)
        self.valid=torch.ones(n,dtype=torch.bool,device=dev)
        self.spacing_active=torch.zeros(n,dtype=torch.bool,device=dev);self.spacing_origin_gap=torch.zeros(n,device=dev);self.spacing_delta=torch.zeros((n,2),device=dev)
        self.count=torch.zeros(n,dtype=torch.long,device=dev);self.saturated=self.count.clone();self.invalid_commands=self.count.clone()
        self.minimum_geometry=torch.full((n,),float('inf'),device=dev)
        self.minimum_center=self.minimum_geometry.clone();self.minimum_stance=self.minimum_geometry.clone()
        self.max_torque=torch.zeros(n,device=dev);self.max_step=self.max_torque.clone();self.max_accel=self.max_torque.clone()
        self.last_states={}
        self.trace=[]
        self.c.apply=self.apply;self.c.reset=self.reset

    def reset(self,env_ids=None):
        self.old_reset(env_ids)
        self.active[slice(None) if env_ids is None else env_ids]=False

    def apply(self,actions):
        result=self.old_apply(actions)
        robot=self.robot;dt=self.env.step_dt
        start=(self.entry.stable_age>=2.)&self.entry.paused&~self.active&self.quota.active
        self.origin[start]=robot.data.root_pos_w[start];self.body_ref[start]=self.origin[start]
        self.orientation[start]=robot.data.root_quat_w[start]
        self.anchors[start]=robot.data.body_pos_w[start][:,self.feet]
        self.reference[start]=robot.data.joint_pos_target[start][:,self.ids]
        self.initial_reference[start]=self.reference[start]
        self.velocity[start]=0.
        self.first_start=torch.where(start,self.env.episode_length_buf*dt,self.first_start)
        self.active|=start
        active=self.active&self.quota.active
        if not active.any():return result
        # Inactive rows still need a valid quaternion for batched kinematics.
        orientation=torch.where(active[:,None],self.orientation,robot.data.root_quat_w)
        anchors=torch.where(active[:,None,None],self.anchors,robot.data.body_pos_w[:,self.feet])
        forces=self.env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids,2]
        feet=robot.data.body_pos_w[:,self.feet]
        com=(robot.data.body_com_pos_w*self.mass[:,:,None]).sum(1)/self.mass.sum(1)[:,None]
        # Cyclic order of all four planted feet, not a swing-foot triangle.
        triangle=feet[:,[0,1,3,2],:2]
        margin=triangle_margin(com[:,:2],triangle)[0].amin(1)
        axis=rotate_vector(orientation,torch.tensor([1.,0.,0.],device=self.env.device).expand_as(self.origin))
        axis[:,2]=0.;axis/=axis.norm(dim=1).clamp_min(1e-6)[:,None]
        box=self.env.scene['box']
        box_axis=rotate_vector(box.data.root_quat_w,torch.tensor([1.,0.,0.],device=self.env.device).expand_as(self.origin))
        box_side=rotate_vector(box.data.root_quat_w,torch.tensor([0.,1.,0.],device=self.env.device).expand_as(self.origin))
        local_offset=self.origin-box.data.root_pos_w
        gap=-(local_offset*box_axis).sum(1)-self.env.cfg.box_size[0]/2.
        lateral=(local_offset*box_side).sum(1)
        near=gap<.48
        proposed=box.data.root_pos_w-(self.env.cfg.box_size[0]/2.+.515)*box_axis+lateral.clamp(-.08,.08)[:,None]*box_side
        delta=(proposed[:,:2]-self.origin[:,:2]).clamp(-.065,.065)
        proposed_goal=self.origin[:,:2]+torch.where(near[:,None],delta,torch.zeros_like(delta))
        self.spacing_active[start]=near[start]
        self.spacing_origin_gap[start]=gap[start]
        self.spacing_delta[start]=torch.where(near[:,None],delta,torch.zeros_like(delta))[start]
        self.body_goal[start]=self.origin[start]
        self.body_goal[start,:2]=proposed_goal[start]
        self.body_goal[start,2]-=.04
        goal=self.body_goal[:,:2]
        delta=goal-self.body_ref[:,:2]
        delta*= (.03*dt/delta.norm(dim=1).clamp_min(.03*dt))[:,None]
        centers=(robot.data.body_pos_w[:,self.arm_bodies,None]-robot.data.body_pos_w[:,None,self.protected]).norm(dim=-1).amin((1,2))
        guard=(self.c.geometry_clearance>=.055)&(centers>=.10)
        # Eight-second quintic body reference: peak XY<=0.01875m/s,
        # peak Z<=0.009375m/s. Original joint/force/physical gates still apply.
        body_fraction=(self.age/8.).clamp(0.,1.)
        body_blend=body_fraction**3*(10.-15.*body_fraction+6.*body_fraction*body_fraction)
        proposed_ref=torch.lerp(self.origin,self.body_goal,body_blend[:,None])
        if hasattr(self,"external_body_reference"):
            proposed_ref=torch.where(self.external_body_active[:,None],self.external_body_reference,proposed_ref)
        proposed_ref=torch.where((active&guard)[:,None],proposed_ref,self.body_ref)
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)
        calm&=robot.data.projected_gravity_b[:,2]<-.96
        prepared=active&guard&calm&(margin>=.025)&(forces>8.).all(1)&self.valid&(self.age>=8.)
        # Controlled ablation: retain all four stance feet throughout transfer.
        # Isolate handover/body motion from the unload/reload feedback loop.
        self.unloading.zero_()
        reference_velocity=(proposed_ref[:,:2]-self.body_ref[:,:2])/dt
        acceleration=4.*(reference_velocity-robot.data.root_lin_vel_w[:,:2])
        if hasattr(self,"external_position_gain"):
            acceleration+=self.external_position_gain[:,None]*(proposed_ref[:,:2]-robot.data.root_pos_w[:,:2])
        acceleration*= (.4/acceleration.norm(dim=1).clamp_min(.4))[:,None]
        vectors,residual=balanced_acceleration_loads(feet,com,self.weight,self.selected,self.unloading,acceleration)
        loads=vectors[:,:,2]
        residual_ok=residual.abs().amax(1)<.02
        trim_eligible=prepared&(self.unloading>=.999)&residual_ok&(self.age>=3.)
        self.trim.update(forces[:,0],trim_eligible,torch.zeros_like(self.age),dt)
        qlocal=rotate_vector(orientation[:,None],anchors-proposed_ref[:,None],inverse=True)
        nominal=self.kin.inverse(qlocal)
        fk_ok=(self.kin.forward(nominal)-qlocal).norm(dim=-1).amax(1)<.001
        jac=robot.root_physx_view.get_jacobians()
        gravity=robot.root_physx_view.get_gravity_compensation_forces()
        dof_offset=0 if robot.is_fixed_base else 6
        grav_offset=0 if gravity.shape[1]==robot.num_joints else 6
        torque=torch.zeros_like(nominal)
        for leg in range(4):
            ids=self.ids[3*leg:3*leg+3]
            body=self.feet[leg]-(1 if robot.is_fixed_base else 0)
            linear_jac=jac[:,body,:3][:,:,[i+dof_offset for i in ids]]
            jz=linear_jac[:,2]
            contact_torque=(linear_jac.transpose(1,2)@vectors[:,leg,:,None]).squeeze(-1)
            torque[:,leg]=gravity[:,[i+grav_offset for i in ids]]-contact_torque
            if leg==0:torque[:,leg]+=jz*self.trim.applied_n[:,None]
        desired=(nominal+torque/30.).reshape(-1,12)
        fraction=(self.age/2.).clamp(0.,1.)
        blend=fraction**3*(10.-15.*fraction+6.*fraction*fraction)
        desired=torch.lerp(self.initial_reference,desired,blend[:,None])
        bounds=robot.data.soft_joint_pos_limits[:,self.ids]
        excess=torch.maximum(bounds[...,0]-desired,desired-bounds[...,1]).clamp_min(0.).amax(1)
        valid=active&guard&fk_ok&residual_ok&(excess<1e-6)&torch.isfinite(desired).all(1)
        self.valid=torch.where(active,valid,self.valid)
        self.invalid_commands+=active&~valid
        self.body_ref=torch.where(valid[:,None],proposed_ref,self.body_ref)
        desired=torch.where(valid[:,None],desired,self.reference)
        previous=self.reference.clone();old_velocity=self.velocity.clone()
        next_ref,next_vel=limit_reference(self.reference,self.velocity,desired,bounds[...,0],bounds[...,1],self.max_velocity,self.max_acceleration,dt)
        self.reference=torch.where(active[:,None],next_ref,self.reference)
        self.velocity=torch.where(active[:,None],next_vel,self.velocity)
        encoded=(self.reference-robot.data.default_joint_pos[:,self.ids])/self.c.scale
        result[:,self.slots]=torch.where(active[:,None],encoded,result[:,self.slots])
        ratio=(robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        body_error=(robot.data.root_pos_w-self.body_goal).norm(dim=1)
        ready=prepared&(ratio<.98)&valid&(body_error<.01)&((robot.data.root_pos_w[:,2]-self.body_goal[:,2]).abs()<.005)
        self.ready_age=torch.where(active,torch.where(ready,self.ready_age+dt,0.),self.ready_age)
        self.count+=active;self.saturated+=active&(ratio>=.999);self.age+=active*dt
        self.minimum_geometry=torch.where(active,torch.minimum(self.minimum_geometry,self.c.geometry_clearance),self.minimum_geometry)
        self.minimum_center=torch.where(active,torch.minimum(self.minimum_center,centers),self.minimum_center)
        self.minimum_stance=torch.where(active,torch.minimum(self.minimum_stance,forces.amin(1)),self.minimum_stance)
        self.max_torque=torch.where(active,torch.maximum(self.max_torque,ratio),self.max_torque)
        self.max_step=torch.where(active,torch.maximum(self.max_step,(self.reference-previous).abs().amax(1)),self.max_step)
        self.max_accel=torch.where(active,torch.maximum(self.max_accel,((self.velocity-old_velocity)/dt).abs().amax(1)),self.max_accel)
        for i in torch.where(active)[0].tolist():
            self.last_states[str(i)]=dict(time_s=float(self.env.episode_length_buf[i]*dt),body_position=(robot.data.root_pos_w[i]-self.env.scene.env_origins[i]).cpu().tolist(),
                body_reference=(self.body_ref[i]-self.env.scene.env_origins[i]).cpu().tolist(),support_margin_m=float(margin[i]),
                body_goal=(self.body_goal[i]-self.env.scene.env_origins[i]).cpu().tolist(),handover_blend=float(blend[i]),
                foot_forces_N=forces[i].cpu().tolist(),desired_vertical_loads_N=loads[i].cpu().tolist(),load_residual=residual[i].cpu().tolist(),
                unloading=float(self.unloading[i]),force_trim_N=float(self.trim.applied_n[i]),joint_command_excess_rad=float(excess[i]),
                command_valid=bool(valid[i]),ready=bool(ready[i]),root_speed=float(robot.data.root_lin_vel_w[i].norm()),root_angular_speed=float(robot.data.root_ang_vel_w[i].norm()))
            self.trace.append(dict(env_id=i,**self.last_states[str(i)],full_support_hull_margin_m=float(margin[i]),body_goal_error_m=float(body_error[i]),stable_hold_s=float(self.ready_age[i]),foot_position=feet[i].cpu().tolist(),foot_anchors=anchors[i].cpu().tolist(),foot_forces_world=self.env.scene['contact_forces'].data.net_forces_w[i,self.sensor_ids].cpu().tolist(),
                desired_reference=desired[i].cpu().tolist(),limited_reference=self.reference[i].cpu().tolist(),
                limited_velocity=self.velocity[i].cpu().tolist(),actual_joint_position=robot.data.joint_pos[i,self.ids].cpu().tolist(),
                linear_velocity=robot.data.root_lin_vel_w[i].cpu().tolist(),angular_velocity=robot.data.root_ang_vel_w[i].cpu().tolist()))
        return result

    def summary(self):
        Path(os.environ['SUPPORT_TRACE_PATH']).write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(spacing_adjusted=self.spacing_active,spacing_original_gap_m=self.spacing_origin_gap,spacing_reference_delta_xy_m=self.spacing_delta,first_start_s=self.first_start,control_samples=self.count,saturated_samples=self.saturated,
            invalid_command_samples=self.invalid_commands,final_body_stable_s=self.ready_age,unloading_fraction=self.unloading,
            minimum_geometry_m=self.minimum_geometry,minimum_body_center_distance_m=self.minimum_center,
            minimum_four_foot_force_N=self.minimum_stance,maximum_torque_ratio=self.max_torque,
            max_joint_reference_step_rad=self.max_step,max_joint_reference_acceleration_rad_s2=self.max_accel)
        result={k:v.cpu().tolist() for k,v in fields.items()}
        for k in ('minimum_geometry_m','minimum_body_center_distance_m','minimum_four_foot_force_N'):
            result[k]=[None if result['control_samples'][i]==0 else x for i,x in enumerate(result[k])]
        return dict(scope='Final planted body pose: conditional near-box retreat to515mm and lateral clamp80mm, lower4cm over8s, full support hull and actual4foot load/settling gates. No foot swing or box pushing.',
            leg_override='Only after2s measured stable waypoint hold; existing arm controller remains active. Original physical task terminations unchanged.',
            correction='Body goal latched once,2s synchronized quintic controller handover, existing CLIMB horizontal velocity feedback gain4 with acceleration cap0.4m/s2. Physical PD/delay/limits unchanged.',
            helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),initial_leg_fk_error_m=self.initial_fk_error,
            thresholds=dict(body_speed_m_s=.03,body_delta_xy_m=.065,leg_rate_rad_s=.8,leg_acceleration_rad_s2=3.,release_force_N=5.,stance_force_N=8.,support_margin_m=.025,release_dwell_s=.2),
            telemetry_scope='Control-call data after transfer begins; original report retains initialization and terminal telemetry.',
            last_states=self.last_states,**result)
