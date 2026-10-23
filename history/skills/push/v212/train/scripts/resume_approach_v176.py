from pathlib import Path
import hashlib,json,os
import torch
from isaaclab.managers import SceneEntityCfg
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
from final_body_v176 import SupportTransfer as Preparation
from support_math_v128 import triangle_margin

class SupportTransfer:
    def __init__(self,env,quota,entry_hold):
        self.env,self.quota,self.entry=env,quota,entry_hold
        self.preparation=Preparation(env,quota,entry_hold)
        self.hold=self.preparation.hold;self.robot=self.hold.robot
        self.hand=SceneEntityCfg('robot',body_names='end_effector');self.hand.resolve(env.scene)
        n=env.num_envs;d=env.device
        self.count=torch.zeros(n,dtype=torch.long,device=d)
        self.first_legal=torch.full((n,),-1.,device=d)
        self.healthy_age=torch.zeros(n,device=d);self.max_healthy=self.healthy_age.clone()
        self.max_ratio=self.healthy_age.clone();self.max_hand_force=self.healthy_age.clone()
        self.minimum_geometry=torch.full((n,),float('inf'),device=d)
        self.saturation=torch.zeros((n,self.robot.num_joints),device=d)
        self.three_support=self.count.clone();self.airborne=self.count.clone()
        self.max_vz=self.healthy_age.clone();self.max_foot_force=self.healthy_age.clone()
        self.trace=[]
        self.old_apply=self.hold.c.apply;self.hold.c.apply=self.apply
    def apply(self,actions):
        robot=self.robot;dt=self.env.step_dt
        forces=self.env.scene['contact_forces'].data.net_forces_w[:,self.hold.sensor_ids]
        fz=forces[:,:,2]
        ratio_by_joint=robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)
        ratio=ratio_by_joint.amax(1)
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)&(robot.data.projected_gravity_b[:,2]<-.96)
        if not self.entry.released:
            ready=self.quota.active&self.preparation.holding&(self.hold.ready_age>=2.)&(fz>8.).all(1)&calm&(ratio<.98)&(self.hold.c.geometry_clearance>=.055)
            ready &= self.env.episode_length_buf*self.env.step_dt>=100.
            if ready.all() and self.entry.prepared_pose_matches():self.entry.release_original_path()
        result=self.old_apply(actions)
        if not self.entry.released:return result
        active=self.quota.active
        legal=box_push.hand_contact(self.env,self.hand)
        hand_force=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2))
        hand_norm=hand_force.norm(dim=1)
        feet=robot.data.body_pos_w[:,self.hold.feet]
        com=(robot.data.body_com_pos_w*self.hold.mass[:,:,None]).sum(1)/self.hold.mass.sum(1)[:,None]
        margin=triangle_margin(com[:,:2],feet[:,[0,1,3,2],:2])[0].amin(1)
        body_error=(robot.data.root_pos_w-self.hold.body_goal).norm(dim=1)
        healthy=active&legal&(fz>8.).all(1)&calm&(ratio<.98)&(self.hold.c.geometry_clearance>=.055)&(margin>=.025)&(body_error<.01)
        self.first_legal=torch.where(active&legal&(self.first_legal<0),self.env.episode_length_buf*dt,self.first_legal)
        self.healthy_age=torch.where(active,torch.where(healthy,self.healthy_age+dt,0.),self.healthy_age)
        self.max_healthy=torch.maximum(self.max_healthy,self.healthy_age)
        self.count+=active;self.three_support+=active&((fz>8.).sum(1)>=3);self.airborne+=active&(fz<=2.).all(1)
        self.max_ratio=torch.where(active,torch.maximum(self.max_ratio,ratio),self.max_ratio)
        self.minimum_geometry=torch.where(active,torch.minimum(self.minimum_geometry,self.hold.c.geometry_clearance),self.minimum_geometry)
        self.max_hand_force=torch.where(active,torch.maximum(self.max_hand_force,hand_norm),self.max_hand_force)
        self.max_vz=torch.where(active,torch.maximum(self.max_vz,robot.data.root_lin_vel_w[:,2].abs()),self.max_vz)
        self.max_foot_force=torch.where(active,torch.maximum(self.max_foot_force,forces.norm(dim=-1).amax(1)),self.max_foot_force)
        self.saturation+=(active[:,None]&(ratio_by_joint>=.98))*dt
        for i in torch.where(active)[0].tolist():
            self.trace.append(dict(env_id=i,time_s=float(self.env.episode_length_buf[i]*dt),legal_hand_contact=bool(legal[i]),healthy_contact=bool(healthy[i]),healthy_contact_s=float(self.healthy_age[i]),hand_force_world_N=hand_force[i].cpu().tolist(),foot_forces_world_N=forces[i].cpu().tolist(),root_position=(robot.data.root_pos_w[i]-self.env.scene.env_origins[i]).cpu().tolist(),root_velocity=robot.data.root_lin_vel_w[i].cpu().tolist(),root_angular_velocity=robot.data.root_ang_vel_w[i].cpu().tolist(),body_goal_error_m=float(body_error[i]),full_support_margin_m=float(margin[i]),geometry_clearance_m=float(self.hold.c.geometry_clearance[i]),torque_ratio=float(ratio[i]),safe_waypoint_index=int(self.hold.c.safe_approach_index[i]),native_motion_ready=bool(self.hold.c.motion_ready[i]),box_position=(self.env.scene['box'].data.root_pos_w[i]-self.env.scene.env_origins[i]).cpu().tolist()))
        return result
    def summary(self):
        path=Path(os.environ['SUPPORT_TRACE_PATH']).parent/'resumed-approach-trace.json';path.write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(control_samples=self.count,first_legal_contact_s=self.first_legal,final_healthy_contact_s=self.healthy_age,maximum_healthy_contact_s=self.max_healthy,post_release_maximum_torque_ratio=self.max_ratio,post_release_peak_hand_force_N=self.max_hand_force,post_release_minimum_recorded_geometry_m=self.minimum_geometry,post_release_joint_saturation_seconds=self.saturation,three_support_samples=self.three_support,airborne_samples=self.airborne,post_release_max_abs_vz_m_s=self.max_vz,post_release_peak_foot_resultant_N=self.max_foot_force)
        values={k:v.cpu().tolist() for k,v in fields.items()}
        values['post_release_minimum_recorded_geometry_m']=[x if values['control_samples'][i] else None for i,x in enumerate(values['post_release_minimum_recorded_geometry_m'])]
        return dict(scope='120s native-contact-lock isolation diagnostic: global batch barrier after v151 preparation, run per-environment audited arm paths then native approach and observe native legal contact while legs remain held. Original press logic may move box. Not full PUSH acceptance.',wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),new_path_released=self.entry.released,release_time_s=self.entry.release_times.cpu().tolist() if self.entry.release_times is not None else None,preparation=self.preparation.summary(),**values)
