"""One additional bounded four-contact transfer when the original RR transfer clips."""
from pathlib import Path
import hashlib,os
import torch
from four_feet_v137 import SupportTransfer as OriginalFourFeet
from support_transfer_v135 import SupportTransfer as SingleStep
from support_math_v135 import triangle_margin
from leg_kinematics_v135 import rotate_vector

class MaskQuota:
    def __init__(self,quota,gate):self.quota,self.gate=quota,gate
    @property
    def active(self):return self.quota.active&self.gate()

class ReplanEntry:
    def __init__(self,entry,owner):self.entry,self.owner=entry,owner
    @property
    def paused(self):return self.entry.paused&self.owner.replanned
    @property
    def stable_age(self):return torch.where(self.owner.replanned,2.,0.)

class SupportTransfer:
    def __init__(self,env,quota,entry_hold):
        self.env,self.quota=env,quota
        self.replanned=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
        self.stable=torch.zeros(env.num_envs,device=env.device)
        self.replan_time=torch.full_like(self.stable,-1.)
        self.reference_jump=torch.zeros_like(self.stable);self.acceleration_jump=torch.zeros_like(self.stable)
        self.original=OriginalFourFeet(env,MaskQuota(quota,lambda:~self.replanned),entry_hold)
        self.extra=SingleStep(env,MaskQuota(quota,lambda:self.replanned),ReplanEntry(entry_hold,self))
        order=[3,0,1,2];permutation=[3*i+j for i in order for j in range(3)]
        for name in ('ids','slots'):
            old=getattr(self.extra,name);setattr(self.extra,name,[old[i] for i in permutation])
        for name in ('feet','sensor_ids'):
            old=getattr(self.extra,name);setattr(self.extra,name,[old[i] for i in order])
        self.extra.kin=self.extra.kin.reordered(('RR','FL','FR','RL'))
        assert self.extra.ids==self.original.controllers[3].ids
        assert self.extra.feet==self.original.controllers[3].feet
        robot=self.extra.robot
        fk=rotate_vector(robot.data.root_quat_w[:,None],self.extra.kin.forward(robot.data.joint_pos[:,self.extra.ids].reshape(-1,4,3)))+robot.data.root_pos_w[:,None]
        self.fk_error=float((fk-robot.data.body_pos_w[:,self.extra.feet]).norm(dim=-1).max());assert self.fk_error<1e-4
        self.old_apply=self.extra.c.apply;self.extra.c.apply=self.apply

    def apply(self,actions):
        previous=self.original.controllers[3];robot=previous.robot
        feet=robot.data.body_pos_w[:,previous.feet]
        forces=self.env.scene['contact_forces'].data.net_forces_w[:,previous.sensor_ids,2]
        com=(robot.data.body_com_pos_w*previous.mass[:,:,None]).sum(1)/previous.mass.sum(1)[:,None]
        margin=triangle_margin(com[:,:2],feet[:,1:,:2])[0].amin(1)
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)&(robot.data.projected_gravity_b[:,2]<-.96)
        ratio=(robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        at_goal=(previous.body_ref[:,:2]-previous.body_goal[:,:2]).norm(dim=1)<.001
        tracked=(robot.data.root_pos_w[:,:2]-previous.body_ref[:,:2]).norm(dim=1)<.015
        clipped=(previous.body_goal[:,:2]-previous.origin[:,:2]).abs().amax(1)>=.0799
        eligible=(self.quota.active&~self.replanned&(self.original.phase==3)&previous.active
            &~previous.swing_started&~previous.unload_armed&(previous.age>=2.)&at_goal&tracked&clipped
            &(margin<.025)&(forces>8.).all(1)&calm&previous.valid&(ratio<.98)&(previous.c.geometry_clearance>=.055))
        self.stable=torch.where(eligible,self.stable+self.env.step_dt,0.)
        begin=eligible&(self.stable>=2.)
        old_reference=previous.reference.clone();old_velocity=previous.velocity.clone()
        self.replanned|=begin
        self.replan_time=torch.where(begin,self.env.episode_length_buf*self.env.step_dt,self.replan_time)
        result=self.old_apply(actions)
        self.reference_jump=torch.where(begin,(self.extra.reference-old_reference).abs().amax(1),self.reference_jump)
        self.acceleration_jump=torch.where(begin,((self.extra.velocity-old_velocity)/self.env.step_dt).abs().amax(1),self.acceleration_jump)
        return result

    def summary(self):
        original_path=os.environ['SUPPORT_TRACE_PATH'];base=Path(original_path).parent
        old=self.original.summary()
        try:
            os.environ['SUPPORT_TRACE_PATH']=str(base/'extra-RR-trace.json');extra=self.extra.summary()
        finally:os.environ['SUPPORT_TRACE_PATH']=original_path
        extra.update(physical_leg='RR',leg_order=['RR','FL','FR','RL'],trace_file='extra-RR-trace.json')
        return dict(scope='Original-start90s four-foot preparation; retain v137 until stable clipped RR transfer, then one additional bounded four-contact transfer. Original25mm unload gate unchanged.',
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reordered_fk_error_m=self.fk_error,
            replan_time_s=self.replan_time.cpu().tolist(),replan_reference_step_rad=self.reference_jump.cpu().tolist(),
            replan_reference_acceleration_rad_s2=self.acceleration_jump.cpu().tolist(),original_four_foot=old,extra_RR=extra)
