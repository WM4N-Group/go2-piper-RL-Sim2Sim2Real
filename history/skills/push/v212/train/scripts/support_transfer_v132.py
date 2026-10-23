"""Opt-in preparation weight transfer; no swing or PUSH task completion."""
from pathlib import Path
import hashlib
import json
import os
import torch
from leg_kinematics_v132 import LegKinematics, rotate_vector
from support_math_v132 import (triangle_margin,inset_support_target,balanced_acceleration_loads,
                              feedback_unload,UnloadForceTrim,limit_reference,LandingContact)

class SmoothLandingContact(LandingContact):
    """Keep measured-contact gates; shape reload with zero endpoint velocity/acceleration."""
    def __init__(self,count,device):
        super().__init__(count,device)
        self.reload_clock=torch.zeros_like(self.depth)

    def update(self,at_end,touch,supported,selected_force,calm,dt):
        probing=at_end&supported&calm&~touch
        self.depth[:]=(self.depth+probing*.004*dt).clamp(max=.015)
        contact=at_end&touch&supported
        self.touch_age[:]=torch.where(contact,self.touch_age+dt,0.)
        self.reload_clock[:]=torch.where(contact&(self.touch_age>=.1),(self.reload_clock+dt).clamp(max=1.5),0.)
        t=self.reload_clock/1.5
        self.reload[:]=t**3*(10.-15.*t+6.*t*t)
        loaded=contact&(self.reload>=1.)&(selected_force>=8.)&calm
        self.loaded_age[:]=torch.where(loaded,self.loaded_age+dt,0.)
        return self.loaded_age>=.2

def step_path(start,goal,progress):
    def smooth(x):
        x=x.clamp(0.,1.)
        return x**3*(10.-15.*x+6.*x*x)
    high=start.clone();high[:,2]=torch.maximum(start[:,2],goal[:,2])+.03
    across=goal.clone();across[:,2]=high[:,2]
    up=torch.lerp(start,high,smooth(progress/.3)[:,None])
    forward=torch.lerp(high,across,smooth((progress-.3)/.4)[:,None])
    down=torch.lerp(across,goal,smooth((progress-.7)/.3)[:,None])
    return torch.where((progress<.3)[:,None],up,torch.where((progress<.7)[:,None],forward,down))

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
        self.count=torch.zeros(n,dtype=torch.long,device=dev);self.saturated=self.count.clone();self.invalid_commands=self.count.clone()
        self.minimum_geometry=torch.full((n,),float('inf'),device=dev)
        self.minimum_center=self.minimum_geometry.clone();self.minimum_stance=self.minimum_geometry.clone()
        self.max_torque=torch.zeros(n,device=dev);self.max_step=self.max_torque.clone();self.max_accel=self.max_torque.clone()
        self.last_states={}
        self.trace=[]
        self.pre_unload_age=torch.zeros(n,device=dev)
        self.unload_armed=torch.zeros(n,dtype=torch.bool,device=dev)
        self.first_unload=torch.full((n,),-1.,device=dev)
        self.swing_started=torch.zeros(n,dtype=torch.bool,device=dev)
        self.swing_progress=torch.zeros(n,device=dev)
        self.swing_start=torch.zeros((n,3),device=dev);self.swing_goal=self.swing_start.clone()
        self.first_swing=torch.full((n,),-1.,device=dev)
        self.lifted=torch.zeros(n,dtype=torch.bool,device=dev)
        self.landing=SmoothLandingContact(n,dev)
        self.first_reload=torch.full((n,),-1.,device=dev)
        self.step_loaded_age=torch.zeros(n,device=dev)
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
        triangle=feet[:,[1,2,3],:2]
        margin=triangle_margin(com[:,:2],triangle)[0].amin(1)
        target_com=inset_support_target(com[:,:2],triangle,reserve=.04)
        proposed_goal=robot.data.root_pos_w[:,:2]+target_com-com[:,:2]
        proposed_goal=torch.maximum(torch.minimum(proposed_goal,self.origin[:,:2]+.08),self.origin[:,:2]-.08)
        self.body_goal[start]=self.origin[start]
        self.body_goal[start,:2]=proposed_goal[start]
        goal=self.body_goal[:,:2]
        delta=goal-self.body_ref[:,:2]
        delta*= (.03*dt/delta.norm(dim=1).clamp_min(.03*dt))[:,None]
        centers=(robot.data.body_pos_w[:,self.arm_bodies,None]-robot.data.body_pos_w[:,None,self.protected]).norm(dim=-1).amin((1,2))
        guard=(self.c.geometry_clearance>=.055)&(centers>=.10)
        proposed_ref=self.body_ref.clone()
        proposed_ref[:,:2]+=torch.where((active&guard)[:,None],delta,0.)
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)
        calm&=robot.data.projected_gravity_b[:,2]<-.96
        prepared=active&guard&calm&(margin>=.025)&(forces[:,1:]>8.).all(1)&self.valid&(self.age>=2.)
        # Separate body transfer from unloading using measured stable support.
        at_goal=(self.body_ref[:,:2]-goal).norm(dim=1)<.001
        settled=prepared&at_goal&(forces>8.).all(1)
        self.pre_unload_age=torch.where(active&~self.unload_armed,torch.where(settled,self.pre_unload_age+dt,0.),self.pre_unload_age)
        newly_armed=active&~self.unload_armed&(self.pre_unload_age>=2.)
        self.unload_armed|=newly_armed
        self.first_unload=torch.where(newly_armed,self.env.episode_length_buf*dt,self.first_unload)
        prepared=prepared&at_goal&self.unload_armed
        self.unloading=torch.where(active,feedback_unload(self.unloading,prepared,forces[:,0]>2.,torch.zeros_like(active),dt),self.unloading)
        begin=prepared&(self.ready_age>=.2)&(forces[:,0]<=5.)&~self.swing_started
        candidate_start=feet[:,0].clone()
        axis=rotate_vector(orientation,torch.tensor([1.,0.,0.],device=self.env.device).expand_as(candidate_start))
        axis[:,2]=0.;axis/=axis.norm(dim=1).clamp_min(1e-6)[:,None]
        candidate_goal=candidate_start+.03*axis;candidate_goal[:,2]=anchors[:,0,2]
        # Kinematic preview is a pre-lift gate, not a collision or dynamic proof.
        preview_ok=torch.ones_like(active)
        limits=robot.data.soft_joint_pos_limits[:,self.ids].reshape(-1,4,3,2)
        if begin.any():
            for fraction in torch.linspace(0.,1.,17,device=self.env.device):
                path=anchors.clone();path[:,0]=step_path(candidate_start,candidate_goal,fraction.expand_as(self.age))
                local=rotate_vector(orientation[:,None],path-proposed_ref[:,None],inverse=True)
                q=self.kin.inverse(local)
                preview_ok&=((q>limits[...,0]+.02)&(q<limits[...,1]-.02)).all((1,2))&((self.kin.forward(q)-local).norm(dim=-1).amax(1)<.001)
        begin&=preview_ok
        self.swing_start[begin]=candidate_start[begin];self.swing_goal[begin]=candidate_goal[begin]
        self.first_swing=torch.where(begin,self.env.episode_length_buf*dt,self.first_swing)
        self.swing_started|=begin
        moving=active&self.swing_started
        tracking=(feet[:,0]-step_path(self.swing_start,self.swing_goal,self.swing_progress)).norm(dim=1)<.01
        advance=moving&prepared&tracking
        self.swing_progress=torch.where(advance,(self.swing_progress+dt/4.).clamp(max=1.),self.swing_progress)
        self.lifted|=moving&(feet[:,0,2]>self.swing_start[:,2]+.015)&(forces[:,0]<=2.)
        at_end=moving&(self.swing_progress>=1.)&self.lifted
        supported=active&guard&(margin>=.025)&(forces[:,1:]>8.).all(1)&self.valid
        near_landing=(feet[:,0,:2]-self.swing_goal[:,:2]).norm(dim=1)<.01
        self.landing.update(at_end,(forces[:,0]>2.)&near_landing,supported,forces[:,0],calm,dt)
        self.first_reload=torch.where((self.first_reload<0)&(self.landing.reload>0),self.env.episode_length_buf*dt,self.first_reload)
        self.unloading=torch.where(moving,1.-self.landing.reload,self.unloading)
        swing_reference=step_path(self.swing_start,self.swing_goal,self.swing_progress)
        swing_reference[:,2]-=self.landing.depth
        anchors=anchors.clone();anchors[:,0]=torch.where(moving[:,None],swing_reference,anchors[:,0])
        reference_velocity=(proposed_ref[:,:2]-self.body_ref[:,:2])/dt
        acceleration=4.*(reference_velocity-robot.data.root_lin_vel_w[:,:2])
        acceleration*= (.4/acceleration.norm(dim=1).clamp_min(.4))[:,None]
        vectors,residual=balanced_acceleration_loads(feet,com,self.weight,self.selected,self.unloading,acceleration)
        loads=vectors[:,:,2]
        residual_ok=residual.abs().amax(1)<.02
        trim_eligible=prepared&(self.unloading>=.999)&residual_ok&(self.age>=3.)
        self.trim.update(forces[:,0],trim_eligible,self.swing_progress,dt)
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
        ready=prepared&(self.unloading>=.999)&(forces[:,0]<=5.)&(ratio<.999)&valid
        self.ready_age=torch.where(active,torch.where(ready,self.ready_age+dt,0.),self.ready_age)
        landed=at_end&near_landing&(self.landing.loaded_age>=.2)&(forces>8.).all(1)&calm&valid&(ratio<.98)
        self.step_loaded_age=torch.where(active,torch.where(landed,self.step_loaded_age+dt,0.),self.step_loaded_age)
        self.count+=active;self.saturated+=active&(ratio>=.999);self.age+=active*dt
        self.minimum_geometry=torch.where(active,torch.minimum(self.minimum_geometry,self.c.geometry_clearance),self.minimum_geometry)
        self.minimum_center=torch.where(active,torch.minimum(self.minimum_center,centers),self.minimum_center)
        self.minimum_stance=torch.where(active,torch.minimum(self.minimum_stance,forces[:,1:].amin(1)),self.minimum_stance)
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
            self.trace.append(dict(env_id=i,**self.last_states[str(i)],prepared=bool(prepared[i]),calm=bool(calm[i]),pre_unload_stable_s=float(self.pre_unload_age[i]),swing_progress=float(self.swing_progress[i]),lifted=bool(self.lifted[i]),landing_reload=float(self.landing.reload[i]),landing_probe_m=float(self.landing.depth[i]),step_loaded_age_s=float(self.step_loaded_age[i]),foot_position=feet[i].cpu().tolist(),foot_forces_world=self.env.scene['contact_forces'].data.net_forces_w[i,self.sensor_ids].cpu().tolist(),
                desired_reference=desired[i].cpu().tolist(),limited_reference=self.reference[i].cpu().tolist(),
                limited_velocity=self.velocity[i].cpu().tolist(),actual_joint_position=robot.data.joint_pos[i,self.ids].cpu().tolist(),
                linear_velocity=robot.data.root_lin_vel_w[i].cpu().tolist(),angular_velocity=robot.data.root_ang_vel_w[i].cpu().tolist()))
        return result

    def summary(self):
        Path(os.environ['SUPPORT_TRACE_PATH']).write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(first_start_s=self.first_start,control_samples=self.count,saturated_samples=self.saturated,
            invalid_command_samples=self.invalid_commands,final_unloaded_stable_s=self.ready_age,unloading_fraction=self.unloading,first_unload_s=self.first_unload,first_swing_s=self.first_swing,swing_progress=self.swing_progress,lift_observed=self.lifted,final_step_loaded_stable_s=self.step_loaded_age,landing_reload=self.landing.reload,swing_start_position=self.swing_start,swing_goal_position=self.swing_goal,first_reload_s=self.first_reload,
            minimum_geometry_m=self.minimum_geometry,minimum_body_center_distance_m=self.minimum_center,
            minimum_other_three_foot_force_N=self.minimum_stance,maximum_torque_ratio=self.max_torque,
            max_joint_reference_step_rad=self.max_step,max_joint_reference_acceleration_rad_s2=self.max_accel)
        result={k:v.cpu().tolist() for k,v in fields.items()}
        for k in ('minimum_geometry_m','minimum_body_center_distance_m','minimum_other_three_foot_force_N'):
            result[k]=[None if result['control_samples'][i]==0 else x for i,x in enumerate(result[k])]
        return dict(scope='Extended30s one-FL-step diagnostic: retain v130 foot reference and use1.5s quintic measured-contact reload;24s state reported separately. No box pushing or PUSH acceptance.',
            leg_override='Only after2s measured stable waypoint hold; existing arm controller remains active. Original physical task terminations unchanged.',
            correction='Body goal latched once,2s synchronized quintic controller handover, existing CLIMB horizontal velocity feedback gain4 with acceleration cap0.4m/s2. Physical PD/delay/limits unchanged.',
            helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),initial_leg_fk_error_m=self.initial_fk_error,
            thresholds=dict(body_speed_m_s=.03,body_delta_xy_m=.08,leg_rate_rad_s=.8,leg_acceleration_rad_s2=3.,release_force_N=5.,stance_force_N=8.,support_margin_m=.025,release_dwell_s=.2),
            telemetry_scope='Control-call data after transfer begins; original report retains initialization and terminal telemetry.',
            last_states=self.last_states,**result)
