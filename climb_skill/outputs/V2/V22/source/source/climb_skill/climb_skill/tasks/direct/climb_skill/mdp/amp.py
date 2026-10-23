"""从物理真值提取AMP特征；不使用有噪声/裁剪的actor观测。"""
import torch
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
    gate = body_plane_gate(pos, env.heights, env.task) * movement_gain(env)
    return features, gate.detach().clone()
