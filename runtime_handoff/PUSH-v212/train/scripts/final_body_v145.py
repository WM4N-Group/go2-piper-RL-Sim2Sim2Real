from pathlib import Path
import hashlib,os
import torch
from rr_replan_v138 import SupportTransfer as Preparation
from final_hold_v145 import SupportTransfer as FinalHold

class MaskQuota:
    def __init__(self,quota,gate):self.quota,self.gate=quota,gate
    @property
    def active(self):return self.quota.active&self.gate()
class HoldEntry:
    def __init__(self,entry,owner):self.entry,self.owner=entry,owner
    @property
    def paused(self):return self.entry.paused&self.owner.holding
    @property
    def stable_age(self):return torch.where(self.owner.holding,2.,0.)

class SupportTransfer:
    def __init__(self,env,quota,entry_hold):
        self.env,self.quota=env,quota
        self.holding=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
        self.start_time=torch.full((env.num_envs,),-1.,device=env.device)
        self.jump=torch.zeros(env.num_envs,device=env.device);self.acceleration_jump=torch.zeros_like(self.jump)
        self.preparation=Preparation(env,MaskQuota(quota,lambda:~self.holding),entry_hold)
        self.hold=FinalHold(env,MaskQuota(quota,lambda:self.holding),HoldEntry(entry_hold,self))
        self.old_apply=self.hold.c.apply;self.hold.c.apply=self.apply
    def apply(self,actions):
        previous=self.preparation.extra;robot=previous.robot
        forces=self.env.scene['contact_forces'].data.net_forces_w[:,previous.sensor_ids,2]
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)&(robot.data.projected_gravity_b[:,2]<-.96)
        ratio=(robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        begin=self.quota.active&~self.holding&(previous.step_loaded_age>=2.)&(forces>8.).all(1)&calm&previous.valid&(ratio<.98)&(previous.c.geometry_clearance>=.055)
        permutation=[previous.ids.index(j) for j in self.hold.ids]
        reference=previous.reference[:,permutation].clone();velocity=previous.velocity[:,permutation].clone()
        self.holding|=begin;self.start_time=torch.where(begin,self.env.episode_length_buf*self.env.step_dt,self.start_time)
        result=self.old_apply(actions)
        self.jump=torch.where(begin,(self.hold.reference-reference).abs().amax(1),self.jump)
        self.acceleration_jump=torch.where(begin,((self.hold.velocity-velocity)/self.env.step_dt).abs().amax(1),self.acceleration_jump)
        return result
    def summary(self):
        original=os.environ['SUPPORT_TRACE_PATH'];preparation=self.preparation.summary()
        try:
            os.environ['SUPPORT_TRACE_PATH']=str(Path(original).parent/'final-body-trace.json');hold=self.hold.summary()
        finally:os.environ['SUPPORT_TRACE_PATH']=original
        return dict(scope='Original-start100s preparation plus final body no forward shift/lower4cm diagnostic, not full PUSH acceptance.',wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),final_body_start_s=self.start_time.cpu().tolist(),handover_reference_step_rad=self.jump.cpu().tolist(),handover_reference_acceleration_rad_s2=self.acceleration_jump.cpu().tolist(),preparation=preparation,final_body=hold)
