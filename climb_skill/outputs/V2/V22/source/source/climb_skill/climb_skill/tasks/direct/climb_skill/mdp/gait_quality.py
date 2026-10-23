"""Soft motion quality costs and forward traversal, without prescribed foot timing."""
import torch
from .geometry import box_scan


def forward_pose_ready(pos, yaw, cfg):
    error = torch.atan2(yaw.sin(), yaw.cos()).abs()
    return (error <= cfg.traversal_heading_tolerance) & (pos[:,1].abs() <= cfg.traversal_lateral_tolerance)


def target_curvature(targets, previous, previous_previous):
    # Actual clipped position targets in rad; 0.1 rad is the normalization scale.
    return ((targets[:, :12] - 2*previous[:, :12] + previous_previous[:, :12]) / .1).square().mean(-1)


def contact_slip(feet, forces, velocities, heights, cfg):
    terrain = box_scan(feet[..., :2], heights, cfg)
    loaded = (forces[..., 2] >= cfg.support_force) & (
        (feet[..., 2] - cfg.foot_radius - terrain).abs() <= cfg.foot_height_tolerance)
    excess = ((velocities[..., :2].norm(dim=-1) - cfg.flat_slip_tolerance).clamp_min(0.)
              / cfg.flat_slip_scale).square()
    return (excess * loaded).sum(-1) / loaded.sum(-1).clamp_min(1)


def path_deviation_cost(pos):
    """离开中心线3cm后才增加横向平方成本，归一化尺度20cm。"""
    return ((pos[:,1].abs()-.03).clamp_min(0.)/.20).square()
