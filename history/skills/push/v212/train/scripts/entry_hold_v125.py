"""Pause an actual safe-waypoint prefix for a preparation-hold diagnostic."""
from pathlib import Path
import hashlib
import torch

class EntryHold:
    def __init__(self,env,quota,foot_ids,sensor_ids):
        self.env,self.quota=env,quota
        self.robot=env.scene['robot']
        self.c=env.action_manager.get_term('joint_pos').controller
        assert self.c.hold_legs_until_ready and not self.c.full_body_preapproach
        assert not self.c.safe_approach_hold and len(self.c.safe_approach_waypoints)>14
        self.foot_ids,self.sensor_ids=foot_ids,sensor_ids
        self.original_apply,self.original_reset=self.c.apply,self.c.reset
        self.original_next=self.c.safe_approach_waypoints[14].clone()
        self.hold_waypoint=self.c.safe_approach_waypoints[13].clone()
        self.c.safe_approach_waypoints[14]=self.hold_waypoint
        n=env.num_envs;device=env.device
        self.paused=torch.zeros(n,dtype=torch.bool,device=device)
        self.first_pause=torch.full((n,),-1.,device=device)
        self.samples=torch.zeros(n,dtype=torch.int64,device=device)
        self.saturated=self.samples.clone();self.leg_released=self.samples.clone()
        self.stable_age=torch.zeros(n,device=device)
        self.minimum=torch.full((n,),float('inf'),device=device)
        self.maximum_torque=torch.zeros(n,device=device)
        self.minimum_foot_force=torch.full((n,),float('inf'),device=device)
        self.maximum_vz=torch.zeros(n,device=device)
        self.maximum_foot_force=torch.zeros(n,device=device)
        self.last_states={}
        self.c.apply=self.apply;self.c.reset=self.reset

    def reset(self,env_ids=None):
        self.original_reset(env_ids)
        self.paused[slice(None) if env_ids is None else env_ids]=False

    def apply(self,actions):
        self.c.safe_approach_index[self.paused]=13
        result=self.original_apply(actions)
        newly=(self.c.safe_approach_index>=14)&~self.paused&self.quota.active
        self.first_pause=torch.where(newly,self.env.episode_length_buf*self.env.step_dt,self.first_pause)
        self.paused|=newly
        active=self.paused&self.quota.active
        if not active.any():return result
        force=self.env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids]
        ratio=(self.robot.data.applied_torque.abs()/self.robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        self.samples+=active
        self.saturated+=active&(ratio>=.999)
        self.leg_released+=active&self.c.motion_ready
        self.minimum=torch.where(active,torch.minimum(self.minimum,self.c.geometry_clearance),self.minimum)
        self.maximum_torque=torch.where(active,torch.maximum(self.maximum_torque,ratio),self.maximum_torque)
        self.minimum_foot_force=torch.where(active,torch.minimum(self.minimum_foot_force,force[:,:,2].amin(1)),self.minimum_foot_force)
        self.maximum_vz=torch.where(active,torch.maximum(self.maximum_vz,self.robot.data.root_lin_vel_w[:,2].abs()),self.maximum_vz)
        magnitude=torch.linalg.vector_norm(force,dim=-1).amax(1)
        self.maximum_foot_force=torch.where(active,torch.maximum(self.maximum_foot_force,magnitude),self.maximum_foot_force)
        calm=(self.robot.data.root_lin_vel_w.norm(dim=1)<.025)&(self.robot.data.root_ang_vel_w.norm(dim=1)<.1)
        calm&=(self.robot.data.projected_gravity_b[:,2]<-.96)&(force[:,:,2]>8.).all(1)
        calm&=(self.c.geometry_clearance>=.035)&(ratio<.999)&~self.c.motion_ready
        self.stable_age=torch.where(active,torch.where(calm,self.stable_age+self.env.step_dt,0.),self.stable_age)
        for i in torch.where(active)[0].tolist():
            self.last_states[str(i)]=dict(time_s=float(self.env.episode_length_buf[i]*self.env.step_dt),
                root_position=(self.robot.data.root_pos_w[i]-self.env.scene.env_origins[i]).cpu().tolist(),
                root_quaternion=self.robot.data.root_quat_w[i].cpu().tolist(),
                root_velocity=self.robot.data.root_lin_vel_w[i].cpu().tolist(),
                root_angular_velocity=self.robot.data.root_ang_vel_w[i].cpu().tolist(),
                joint_position=self.robot.data.joint_pos[i].cpu().tolist(),
                joint_velocity=self.robot.data.joint_vel[i].cpu().tolist(),
                foot_position=(self.robot.data.body_pos_w[i,self.foot_ids]-self.env.scene.env_origins[i]).cpu().tolist(),
                foot_force=force[i].cpu().tolist(),reference=self.c.reference[i].cpu().tolist())
        return result

    def summary(self):
        values=dict(first_pause_s=self.first_pause,control_samples=self.samples,saturated_samples=self.saturated,
            leg_released_samples=self.leg_released,final_continuous_stable_s=self.stable_age,
            minimum_geometry_m=self.minimum,maximum_torque_ratio=self.maximum_torque,
            minimum_foot_vertical_force_N=self.minimum_foot_force,peak_abs_vz_m_s=self.maximum_vz,
            peak_foot_resultant_N=self.maximum_foot_force)
        result={k:v.cpu().tolist() for k,v in values.items()}
        for key in ('minimum_geometry_m','minimum_foot_vertical_force_N'):
            result[key]=[None if result['control_samples'][i]==0 else x for i,x in enumerate(result[key])]
        return dict(scope='Preparation hold after actual waypoint13 settling; original task metrics unchanged. Stage-only, not completed PUSH.',
            helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            hold_waypoint=self.hold_waypoint.cpu().tolist(),original_waypoint14=self.original_next.cpu().tolist(),
            override='Waypoint14 repeats13; paused indices restart at13 before apply. Safe-path phase remains active, original leg hold and all physical terminations remain enabled.',
            sample_scope='Controller calls after pause, not physics substeps. Original report still contains initialization telemetry.',
            joint_names=list(self.robot.joint_names),last_states=self.last_states,**result)
