"""Compose frozen single-step controllers: FL then FR, one episode per environment."""
from pathlib import Path
import hashlib
import os
import torch
from support_transfer_v135 import SupportTransfer as SingleStep
from leg_kinematics_v135 import rotate_vector

class GateQuota:
    def __init__(self, quota, gate):
        self.quota, self.gate = quota, gate
    @property
    def active(self):
        return self.quota.active & self.gate()

class SecondEntry:
    def __init__(self, entry, owner):
        self.entry, self.owner = entry, owner
    @property
    def paused(self):
        return self.entry.paused & self.owner.handed_over
    @property
    def stable_age(self):
        # The transition gate below has already required2s loaded stability.
        return torch.where(self.owner.handed_over, 2., 0.)

class SupportTransfer:
    def __init__(self, env, quota, entry_hold):
        self.env, self.quota = env, quota
        self.handed_over = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        self.handover_time = torch.full((env.num_envs,), -1., device=env.device)
        self.reference_jump = torch.zeros(env.num_envs, device=env.device)
        self.velocity_jump = torch.zeros_like(self.reference_jump)
        self.first = SingleStep(env, GateQuota(quota, lambda: ~self.handed_over), entry_hold)
        self.second = SingleStep(env, GateQuota(quota, lambda: self.handed_over), SecondEntry(entry_hold, self))
        # Reorder complete measured physical legs; do not mirror geometry/actions.
        self.permutation = [3,4,5,0,1,2,6,7,8,9,10,11]
        for name in ('ids', 'slots'):
            values = getattr(self.second, name)
            setattr(self.second, name, [values[i] for i in self.permutation])
        for name in ('feet', 'sensor_ids'):
            values = getattr(self.second, name)
            setattr(self.second, name, [values[i] for i in (1,0,2,3)])
        self.second.kin = self.second.kin.reordered(('FR','FL','RL','RR'))
        robot = self.second.robot
        fk = rotate_vector(robot.data.root_quat_w[:,None], self.second.kin.forward(
            robot.data.joint_pos[:,self.second.ids].reshape(-1,4,3))) + robot.data.root_pos_w[:,None]
        self.reordered_fk_error = float((fk-robot.data.body_pos_w[:,self.second.feet]).norm(dim=-1).max())
        assert self.reordered_fk_error < 1e-4
        self.old_apply = self.second.c.apply
        self.second.c.apply = self.apply

    def apply(self, actions):
        robot = self.first.robot
        forces = self.env.scene['contact_forces'].data.net_forces_w[:,self.first.sensor_ids,2]
        calm = (robot.data.root_lin_vel_w.norm(dim=1)<.025) & (robot.data.root_ang_vel_w.norm(dim=1)<.1)
        calm &= robot.data.projected_gravity_b[:,2] < -.96
        ratio = (robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        begin = (self.quota.active & ~self.handed_over & (self.first.step_loaded_age>=2.)
            & (forces>8.).all(1) & calm & self.first.valid & (ratio<.98)
            & (self.first.c.geometry_clearance>=.055))
        old_reference = self.first.reference[:,self.permutation].clone()
        old_velocity = self.first.velocity[:,self.permutation].clone()
        self.handed_over |= begin
        self.handover_time = torch.where(begin, self.env.episode_length_buf*self.env.step_dt, self.handover_time)
        result = self.old_apply(actions)
        self.reference_jump = torch.where(begin, (self.second.reference-old_reference).abs().amax(1), self.reference_jump)
        self.velocity_jump = torch.where(begin, ((self.second.velocity-old_velocity)/self.env.step_dt).abs().amax(1), self.velocity_jump)
        return result

    def summary(self):
        original_path = os.environ['SUPPORT_TRACE_PATH']
        base = Path(original_path).parent
        try:
            os.environ['SUPPORT_TRACE_PATH'] = str(base/'first-FL-trace.json')
            first = self.first.summary()
            os.environ['SUPPORT_TRACE_PATH'] = str(base/'second-FR-trace.json')
            second = self.second.summary()
        finally:
            os.environ['SUPPORT_TRACE_PATH'] = original_path
        first.update(physical_leg='FL', leg_order=['FL','FR','RL','RR'])
        second.update(physical_leg='FR', leg_order=['FR','FL','RL','RR'])
        return dict(scope='Original-start60s two-front-foot preparation diagnostic. Frozen v135 single-step control composed FL then FR. No box pushing or full PUSH acceptance.',
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            reordered_FR_kinematics_error_m=self.reordered_fk_error,
            handover_time_s=self.handover_time.cpu().tolist(),
            handover_reference_step_rad=self.reference_jump.cpu().tolist(),
            handover_reference_acceleration_rad_s2=self.velocity_jump.cpu().tolist(),
            first_FL=first, second_FR=second)
