"""Retain the measured, loaded FR foothold across the additional RR transfer."""
from pathlib import Path
import hashlib
import torch
from rr_replan_v138 import SupportTransfer as OriginalReplan

class SupportTransfer:
    def __init__(self,env,quota,entry_hold):
        self.env,self.quota=env,quota
        self.base=OriginalReplan(env,quota,entry_hold)
        self.plant_xy=torch.zeros((env.num_envs,2),device=env.device)
        self.captured=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
        self.attempted=torch.zeros_like(self.captured);self.applied=torch.zeros_like(self.captured)
        self.capture_time=torch.full((env.num_envs,),-1.,device=env.device)
        self.update_time=torch.full_like(self.capture_time,-1.)
        self.shift=torch.zeros_like(self.plant_xy)
        self.fr_body=self.base.original.controllers[0].feet[1]
        self.fr_slot=self.base.extra.feet.index(self.fr_body)
        assert self.fr_slot==2
        self.old_apply=self.base.extra.c.apply;self.base.extra.c.apply=self.apply

    def apply(self,actions):
        previous_phase=self.base.original.phase.clone()
        result=self.old_apply(actions)
        # The original transition already checked2s loaded hold and current
        # four-foot contact/calm/geometry/effort gates. Capture measured XY once.
        landed=self.quota.active&(previous_phase==1)&(self.base.original.phase==2)&~self.captured
        foot=self.base.extra.robot.data.body_pos_w[:,self.fr_body,:2]
        self.plant_xy[landed]=foot[landed];self.captured|=landed
        self.capture_time=torch.where(landed,self.env.episode_length_buf*self.env.step_dt,self.capture_time)
        begin=self.quota.active&self.base.replanned&~self.attempted
        shift=self.plant_xy-self.base.extra.anchors[:,self.fr_slot,:2]
        allowed=begin&self.captured&(shift.norm(dim=1)<=.008)
        # At this capture call the frozen helper has published its old target
        # with zero handover blend. The retained anchor enters its existing2s
        # quintic blend on later calls, still behind its original IK/force gates.
        self.base.extra.anchors[allowed,self.fr_slot,:2]=self.plant_xy[allowed]
        self.shift=torch.where(begin[:,None],shift,self.shift)
        self.attempted|=begin;self.applied|=allowed
        self.update_time=torch.where(allowed,self.env.episode_length_buf*self.env.step_dt,self.update_time)
        return result

    def summary(self):
        return dict(scope='Original-start90s four-foot preparation diagnostic. Retain measured loaded FR XY anchor during extra RR transfer; Z, robot state, release and physical gates unchanged.',
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            FR_loaded_capture_time_s=self.capture_time.cpu().tolist(),FR_anchor_update_time_s=self.update_time.cpu().tolist(),
            FR_anchor_shift_xy_m=self.shift.cpu().tolist(),FR_anchor_update_applied=self.applied.cpu().tolist(),
            anchor_change_cap_m=.008,base_result=self.base.summary())
