"""New experimental contract: 12 leg actions and 6 bounded arm IK residuals."""
import torch
from .box_push_actions import BoxPushLegAction

ARM_RESIDUAL_RAD = 0.20

class ResidualPushAction(BoxPushLegAction):
    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        self._raw = torch.zeros((env.num_envs, 19), device=env.device)
        env.box_push_arm_residual = torch.zeros((env.num_envs, 6), device=env.device)

    @property
    def action_dim(self):
        return 19

    def process_actions(self, actions):
        if actions.shape != self._raw.shape or not torch.isfinite(actions).all():
            raise ValueError('Expected finite 19-action residual PUSH output')
        self._raw[:] = actions
        c = self.controller
        c.env.box_push_arm_residual[:] = ARM_RESIDUAL_RAD * torch.tanh(actions[:, 12:18])
        c.env.box_push_arm_speed_scale = torch.sigmoid(actions[:, 18])
        combined = torch.zeros_like(self.joint_commands)
        combined[:, c.leg_slots] = actions[:, :12]
        self.joint_commands[:] = c.apply(combined)
        self.delegate.process_actions(self.joint_commands)
        if getattr(c.env.cfg, 'record_push_policy_activity', False):
            c.env.extras['push_policy_action_active'] = (~c.goal_hold_active & ~c.locked).detach().clone()

    def reset(self, env_ids=None):
        super().reset(env_ids)
        if hasattr(self.controller.env, 'box_push_arm_residual'):
            self.controller.env.box_push_arm_residual[slice(None) if env_ids is None else env_ids] = 0.0

        # v196: initialize targets at the randomized reset pose, after native reset.
        # Do not change joint state, base pose, PD, sampled delays, or non-reset envs.
        r=self.controller.robot
        selected=slice(None) if env_ids is None else env_ids
        position=r.data.joint_pos[selected].clone()
        r.set_joint_position_target(position,env_ids=env_ids)
        r.set_joint_velocity_target(torch.zeros_like(position),env_ids=env_ids)
        r.set_joint_effort_target(torch.zeros_like(position),env_ids=env_ids)
