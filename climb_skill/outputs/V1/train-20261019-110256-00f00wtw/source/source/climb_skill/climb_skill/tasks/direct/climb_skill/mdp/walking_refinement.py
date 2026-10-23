"""平面行走候选：不因腾空关闭限速，低课程渐入，摆脚高度软约束。

所有量都由当前几何/传感器计时计算，不维护隐藏步态时钟，不强制换脚。
不用于旧checkpoint；仅walking_refinement_enabled开启时调用。
"""
import torch
from .flat_walking import flat_walking_mask
from .geometry import box_scan


def settled_flat_mask(pos, feet, heights, ever_top_support, cfg):
    """同一平面且箱顶已完成四足初次承重；不查询当前接触数。

    箱顶初次攀上阶段不约束；之后即使全身腾空也保持约束。
    只判同平面，不使用到箱沿距离的奖励或距离阈值。
    """
    mask = flat_walking_mask(pos, feet, heights, cfg)
    root_top = box_scan(pos[:, None, :2], heights, cfg).squeeze(-1) > 0.
    feet_top = box_scan(feet[..., :2], heights, cfg) > 0.
    same_as_root = (feet_top == root_top[:, None]).all(-1)
    landed = ~root_top | ever_top_support.all(-1)
    return mask * same_as_root * landed


def early_gait_gain(heights, cfg):
    """最低箱高即启用25%成本，随本环境课程高度线性增加，15cm达全量。

    播放低高度或关闭课程时仍按实际箱高计算；不依赖训练轮数。
    """
    span = cfg.flat_walk_start_height - cfg.curriculum_min_height
    if span <= 0:
        return torch.ones_like(heights)
    fraction = ((heights - cfg.curriculum_min_height) / span).clamp(0., 1.)
    return cfg.walking_early_gain + (1. - cfg.walking_early_gain) * fraction


def swing_clearance_cost(mask, feet, heights, air_time, cfg):
    """成熟摆动中的脚底高度带：过低易拖、过高易甩腿/蹬跳。

    落地air_time归零，成本归零；起摆60ms内不要求瞬间达到高度。
    再用60ms渐入；逐足平均且封顶，避免一项新成本压倒前进目标。
    这是高度带软成本，并不保证指定的足端轨迹。
    """
    terrain = box_scan(feet[..., :2], heights, cfg)
    clearance = feet[..., 2] - cfg.foot_radius - terrain
    low = (cfg.walking_clearance_min - clearance).clamp_min(0.)
    high = (clearance - cfg.walking_clearance_max).clamp_min(0.)
    error = ((low + high) / cfg.walking_clearance_scale).square().clamp_max(1.)
    mature = ((air_time - cfg.diagonal_transfer_seconds) / cfg.diagonal_transfer_seconds).clamp(0., 1.)
    return mask * (mature * error).mean(-1)
