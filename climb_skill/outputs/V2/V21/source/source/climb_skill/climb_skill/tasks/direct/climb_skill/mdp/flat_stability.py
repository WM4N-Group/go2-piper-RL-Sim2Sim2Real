"""Optional posture and soft speed costs, sharing a flat-surface gate."""
import math
from .geometry import box_scan


def flat_surface_gate(feet, forces, heights, cfg, root_xy=None):
    terrain = box_scan(feet[..., :2], heights, cfg)
    on_top = terrain > 0.
    same_plane = on_top.all(-1) | (~on_top).all(-1)
    at_surface = (feet[..., 2] - cfg.foot_radius - terrain).abs() <= cfg.foot_height_tolerance
    loaded = (forces[..., 2] >= cfg.support_force) & at_surface
    above_plane = (feet[..., 2] - cfg.foot_radius >= terrain - cfg.foot_height_tolerance).all(-1)
    return (same_plane & above_plane & (loaded.sum(-1) >= 2)).to(feet.dtype)


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
