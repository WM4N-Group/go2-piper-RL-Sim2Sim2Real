"""18轴动作与机械臂初态保持。"""

import torch
from isaaclab.utils.math import euler_xyz_from_quat, quat_from_euler_xyz
from ..task_parameters import FOOT_NAMES, HISTORY, JOINT_NAMES, PROPRIO
from .geometry import box_scan, constrained_actions, stable_timer, top_support


def pre_physics_step(env, actions):
    if not torch.isfinite(actions).all():
        raise FloatingPointError("Nonfinite policy action")
    if env.task.approach_quality_enabled:
        from .amp import snapshot
        env.approach_quality.before, env.approach_quality.before_gate = snapshot(env)
        if env.task.crossing_quality_enabled:
            _, _, feet, forces, *_ = env._kinematics()
            env.approach_quality.capture(feet, forces)
    env.previous_actions.copy_(env.actions)
    env.previous_previous_targets.copy_(env.previous_targets)
    env.previous_targets.copy_(env.targets)
    # 网络原始高斯动作先清臂残差，再裁到±(1.2/0.25)=±4.8；随后乘起步渐放系数。
    env.actions = constrained_actions(actions).clamp(
        -env.task.max_position_offset / env.task.action_scale,
        env.task.max_position_offset / env.task.action_scale)
    if env.task.startup_stand_seconds > 0:
        from .startup import movement_gain
        env.actions *= movement_gain(env)[:, None]
    # 腿目标=本回合参考角+0.25×残差；不是上一时刻目标累加，因而不会积分漂移。
    env.targets = env.reference + env.task.action_scale * env.actions
    limits = env.robot.data.soft_joint_pos_limits[:, env.joint_ids]
    # 腿进一步裁到USD软限位；观测里的env.actions是裁软限位之前的残差，不等于最终目标角。
    env.targets[:, :12] = env.targets[:, :12].clamp(limits[:, :12, 0], limits[:, :12, 1])
    if env.task.rear_workspace_enabled:
        from .joint_workspace import rear_target_workspace
        env.targets = rear_target_workspace(env.targets, env.task)
    env.targets[:, 12:] = env.reference[:, 12:]

