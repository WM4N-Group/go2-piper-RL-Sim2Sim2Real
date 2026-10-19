"""从物理真值提取AMP特征；不使用有噪声/裁剪的actor观测。"""
import torch
from .walking_refinement import settled_flat_mask
from .startup import movement_gain


def body_plane_gate(pos, heights, cfg):
    """只看名义机身四角投影：跨台阶关闭；脚折到身后不会关闭平地风格。

    0.45m前后覆盖给登箱留出过渡空间；不奖励离边沿的距离、不查接触数。
    """
    from .geometry import box_scan
    footprint = pos[:, None, :2] + pos.new_tensor(
        [[.45, .20], [.45, -.20], [-.45, .20], [-.45, -.20]])
    planes = box_scan(footprint, heights, cfg) > 0.
    return (planes.all(-1) | (~planes).all(-1)).to(pos.dtype)


def snapshot(env):
    data = env.robot.data
    joints = env.joint_ids[:12]
    features = torch.cat((data.joint_pos[:, joints], data.root_lin_vel_b,
                          data.root_ang_vel_b, data.joint_vel[:, joints]), -1).detach().clone()
    pos, _, feet, *_ = env._kinematics()
    if env.task.crossing_quality_enabled:
        gate = env.approach_quality.flat_gate(feet, env.heights) * movement_gain(env)
        return features, gate.detach().clone()
    if env.task.amp_body_gate:
        # 起步渐放过程中也渐入学习信号，而不是等机器人已冲到箱沿才开始。
        gate = body_plane_gate(pos, env.heights, env.task) * movement_gain(env)
        return features, gate.detach().clone()
    gate = settled_flat_mask(pos, feet, env.heights, env.ever_top_support, env.task)
    gate *= (movement_gain(env) >= 1.).float()
    # 防止站着靠正的风格奖励拖延回合；向世界+X实际移动才获得风格奖励。
    gate *= (data.root_lin_vel_w[:, 0] / env.task.approach_speed).clamp(0, 1)
    return features, gate.detach().clone()
