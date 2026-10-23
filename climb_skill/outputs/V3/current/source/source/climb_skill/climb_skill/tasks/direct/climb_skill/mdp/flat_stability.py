"""Optional posture and soft speed costs, sharing a flat-surface gate."""
import math
import torch
from .geometry import box_scan


def flat_surface_gate(feet, forces, heights, cfg, root_xy=None):
    terrain = box_scan(feet[..., :2], heights, cfg)
    on_top = terrain > 0.
    same_plane = on_top.all(-1) | (~on_top).all(-1)
    if cfg.flat_ignore_edge_distance:
        # No edge-distance reward or gate. Preserve pitch freedom during ascent.
        at_surface = (feet[..., 2] - cfg.foot_radius - terrain).abs() <= cfg.foot_height_tolerance
        loaded = (forces[..., 2] >= cfg.support_force) & at_surface
        above_plane = (feet[..., 2] - cfg.foot_radius >= terrain - cfg.foot_height_tolerance).all(-1)
        return (same_plane & above_plane & (loaded.sum(-1) >= 2)).to(feet.dtype)
    x, y = feet[..., 0], feet[..., 1]
    dx = torch.maximum((cfg.box_front - x).clamp_min(0.),
                       (x - cfg.box_front - cfg.box_length).clamp_min(0.))
    dy = (y.abs() - cfg.box_width / 2).clamp_min(0.)
    outside_distance = torch.sqrt(dx.square() + dy.square())
    inside_distance = torch.minimum(torch.minimum(x - cfg.box_front,
        cfg.box_front + cfg.box_length - x), cfg.box_width / 2 - y.abs())
    clearance = torch.where(on_top, inside_distance, outside_distance).amin(-1)
    if cfg.flat_use_body_gate:
        if root_xy is None:
            raise ValueError("Body gate requires actual root XY")
        rx, ry = root_xy[:, 0], root_xy[:, 1]
        root_top = box_scan(root_xy[:, None], heights, cfg)[:, 0] > 0.
        root_inside = torch.minimum(torch.minimum(rx - cfg.box_front,
            cfg.box_front + cfg.box_length - rx), cfg.box_width / 2 - ry.abs())
        # Preserve the original foot-based approach margin on the ground.
        # On top, one wide-placed foot must not disable all torso stabilization.
        clearance = torch.where(root_top, root_inside, clearance)
        # The torso and all feet must query the same plane. Mixed-height ascent stays free.
        same_plane = same_plane & (on_top == root_top[:, None]).all(-1)
        same_plane &= (feet[..., 2] - cfg.foot_radius >= terrain - cfg.foot_height_tolerance).all(-1)
    gate = ((clearance - cfg.flat_stability_margin) / cfg.flat_stability_blend_width).clamp(0., 1.)
    # Real support on the queried surface; normal swing feet are allowed.
    at_surface = (feet[..., 2] - cfg.foot_radius - terrain).abs() <= cfg.foot_height_tolerance
    loaded = (forces[..., 2] >= cfg.support_force) & at_surface
    return gate * same_plane * (loaded.sum(-1) >= 2)


def flat_posture_cost(feet, forces, gravity, heights, cfg, root_xy=None):
    gate = flat_surface_gate(feet, forces, heights, cfg, root_xy)
    excess = (gravity[:, :2].abs() - math.sin(cfg.flat_stability_tolerance)).clamp_min(0.)
    return gate * excess.square().sum(-1), gate


def flat_speed_terms(planar_speed, progress, gate, cfg):
    """Soft overspeed cost and progress cap ONLY where the shared gate is active.

    Does not clamp robot velocity, actions, or the original step-crossing rewards.
    """
    excess = (planar_speed / cfg.flat_speed_limit - 1.).clamp_min(0.)
    overspeed = gate * excess.square()
    # Without this local cap the original progress term still rewards sprinting.
    local_progress = progress.clamp_max(cfg.flat_speed_limit)
    gated_progress = progress + gate * (local_progress - progress)
    return overspeed, gated_progress


def flat_motion_costs(feet, forces, foot_velocities, angular_velocity, heights, gate, cfg):
    """Damp roll/pitch oscillation and loaded-foot slip on safe flat surfaces.

    No yaw, swing-foot, contact-count reward, or gait phase constraint. Velocities
    are world-frame foot link velocities against the static floor/platform.
    """
    angular = gate * (angular_velocity[:, :2].abs()
        - cfg.flat_angular_velocity_tolerance).clamp_min(0.).square().sum(-1)
    terrain = box_scan(feet[..., :2], heights, cfg)
    at_surface = (feet[..., 2] - cfg.foot_radius - terrain).abs() <= cfg.foot_height_tolerance
    loaded = (forces[..., 2] >= cfg.support_force) & at_surface
    slip_speed = foot_velocities[..., :2].norm(dim=-1)
    excess = ((slip_speed - cfg.flat_slip_tolerance).clamp_min(0.) / cfg.flat_slip_scale).square()
    slip = gate * (excess * loaded).sum(-1) / loaded.sum(-1).clamp_min(1)
    return angular, slip
