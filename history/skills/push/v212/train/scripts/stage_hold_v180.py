"""Validate measured-pose scenario initialization; not replay or original-start acceptance."""
from pathlib import Path
import hashlib,json,os
import torch
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
from isaaclab.managers import SceneEntityCfg
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
        env.scene.write_data_to_sim()
    def apply(self,actions):
        out=self.old_apply(actions);r=self.robot;c=self.c;dt=self.env.step_dt;active=self.quota.active
        force=self.env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids];fz=force[:,:,2]
        ratio=(r.data.applied_torque.abs()/r.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        # Same native geometry shield on the actual command; fixed source PD targets.
        grav=r.root_physx_view.get_gravity_compensation_forces();columns=c.joint_ids if grav.shape[1]==r.num_joints else c.jacobian_columns
        requested=self.target[:,c.joint_ids]-grav[:,columns]/c.stiffness
        bounds=r.data.soft_joint_pos_limits[:,c.joint_ids].clone();bounds[:,3,0]=bounds[:,3,0].clamp_min(.8)
        projected,clear,blocked=c.geometry_shield.project(r.data.joint_pos[:,c.joint_ids].cpu().numpy(),r.data.joint_vel[:,c.joint_ids].cpu().numpy(),requested.cpu().numpy(),bounds[...,0].cpu().numpy(),bounds[...,1].cpu().numpy(),active.cpu().numpy())
        ref=torch.as_tensor(projected,device=self.env.device,dtype=requested.dtype);clear=torch.as_tensor(clear,device=self.env.device,dtype=requested.dtype)
        correction=(ref-requested).abs().amax(1);self.halted|=active&(correction>1e-6)
        physical=self.target.clone();physical[:,c.joint_ids]=ref+grav[:,columns]/c.stiffness
        out[:]=(physical[:,self.ids]-r.data.default_joint_pos[:,self.ids])/c.scale
        c.reference=ref;c.geometry_clearance=clear;c.geometry_blocked=torch.as_tensor(blocked,device=self.env.device);c.debug_reference_post_geometry=ref.clone()
        contact=box_push.hand_contact(self.env,self.hand);handforce=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2)).norm(dim=1)
        body_error=(r.data.root_pos_w-self.origin).norm(dim=1);calm=(r.data.root_lin_vel_w.norm(dim=1)<.025)&(r.data.root_ang_vel_w.norm(dim=1)<.1)&(r.data.projected_gravity_b[:,2]<-.96)
        healthy=active&(fz>8.).all(1)&calm&(ratio<.98)&(clear>=.055)&(body_error<.01)&(handforce<=1.)&~contact&~self.halted
        self.age=torch.where(active,torch.where(healthy,self.age+dt,0.),self.age);self.count+=active;self.three+=active&((fz>8.).sum(1)>=3);self.air+=active&(fz<=2).all(1)
        self.min_clear=torch.where(active,torch.minimum(self.min_clear,clear),self.min_clear);self.max_ratio=torch.maximum(self.max_ratio,torch.where(active,ratio,0.));self.max_vz=torch.maximum(self.max_vz,torch.where(active,r.data.root_lin_vel_w[:,2].abs(),0.));self.max_force=torch.maximum(self.max_force,torch.where(active,force.norm(dim=2).amax(1),0.));self.max_sumforce=torch.maximum(self.max_sumforce,torch.where(active,force.sum(1).norm(dim=1),0.));self.max_drift=torch.maximum(self.max_drift,torch.where(active,body_error,0.))
        for i in torch.where(active)[0].tolist():self.trace.append(dict(env_id=i,time_s=float(self.env.episode_length_buf[i]*dt),healthy_s=float(self.age[i]),foot_force_z_N=fz[i].cpu().tolist(),geometry_m=float(clear[i]),torque_ratio=float(ratio[i]),body_error_m=float(body_error[i]),hand_force_N=float(handforce[i]),legal_contact=bool(contact[i]),shield_correction_rad=float(correction[i])))
        return out
    def summary(self):
        (Path(os.environ['STAGE_BANK']).parent/'stage-trace.json').write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(control_samples=self.count,three_support_samples=self.three,airborne_samples=self.air,final_healthy_hold_s=self.age,maximum_torque_ratio=self.max_ratio,minimum_geometry_m=self.min_clear,maximum_abs_vz_m_s=self.max_vz,maximum_foot_resultant_N=self.max_force,maximum_total_foot_vector_norm_N=self.max_sumforce,maximum_body_drift_m=self.max_drift,halted=self.halted)
        return dict(scope='6s measured-pose stage-start validation only. Native PD/delay/collision/safety retained. Physics contact solver and observation history freshly initialized; NOT exact state replay or original-start acceptance. No motion_ready/contact/support flag forced true. Physical settling remeasured.',helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),bank_sha256=self.bank_hash,**{k:v.cpu().tolist() for k,v in fields.items()})
