"""Tensor geometry shared by the environment and CPU contract tests."""

import torch


def constrained_actions(actions):
    """An 18-axis interface with exactly zero arm residual, including during exploration."""
    if actions.shape[-1] != 18:
        raise ValueError("CLIMB requires 18 actions in declared joint order")
    return torch.cat((actions[..., :12], torch.zeros_like(actions[..., 12:])), dim=-1)


def top_support(feet, forces, heights, cfg):
    """Require safe XY, actual foot height AND positive vertical support, not just proximity."""
    inside = ((feet[..., 0] >= cfg.box_front + cfg.top_margin)
              & (feet[..., 0] <= cfg.box_front + cfg.box_length - cfg.top_margin)
              & (feet[..., 1].abs() <= cfg.box_width / 2 - cfg.top_margin))
    at_height = (feet[..., 2] - cfg.foot_radius - heights[:, None]).abs() <= cfg.foot_height_tolerance
    loaded = forces[..., 2] >= cfg.support_force
    return inside & at_height & loaded


def box_scan(points_xy, heights, cfg):
    """Exact privileged height query for this task's ONLY geometry: plane plus axis-aligned box."""
    inside = ((points_xy[..., 0] >= cfg.box_front)
              & (points_xy[..., 0] <= cfg.box_front + cfg.box_length)
              & (points_xy[..., 1].abs() <= cfg.box_width / 2))
    return inside.to(points_xy.dtype) * heights[:, None]


def stable_timer(previous, stable, dt):
    """A failed frame resets the timer; intermittent stability cannot accumulate into success."""
    return torch.where(stable, previous + dt, torch.zeros_like(previous))


def forward_tracking_rewards(forward, command, heading):
    """Reward forward travel and alignment while moving; resting earns neither term."""
    ratio = forward / command.clamp_min(1e-6)
    velocity = ratio.clamp_max(1.)
    alignment = torch.exp(-heading.abs()) * ratio.clamp(0., 1.)
    return velocity, alignment


def update_top_contact_age(previous, support, dt):
    """Time since each foot last carried load on the top; infinity means never loaded."""
    return torch.where(support, torch.zeros_like(previous), previous + dt)


def platform_ascent_geometry(feet, ages, root_x, cfg, heights):
    """Check sustained ascent evidence independently of the current gait phase.

    Every foot must have actually loaded the top recently and still be above its
    safe footprint. Swing feet may be above the contact-height band. This alone
    is not a success signal: current support and health are checked at commit.
    """
    inside = ((feet[..., 0] >= cfg.box_front + cfg.top_margin)
              & (feet[..., 0] <= cfg.box_front + cfg.box_length - cfg.top_margin)
              & (feet[..., 1].abs() <= cfg.box_width / 2 - cfg.top_margin))
    above_top = feet[..., 2] - cfg.foot_radius >= heights[:, None] - cfg.foot_height_tolerance
    recent_load = ages <= cfg.top_contact_memory
    stance = ((feet[..., 0].amax(-1) - feet[..., 0].amin(-1) >= cfg.minimum_stance_length)
              & (feet[..., 1].amax(-1) - feet[..., 1].amin(-1) >= cfg.minimum_stance_width))
    return (inside & above_top & recent_load).all(-1) & (root_x >= cfg.finish_x) & stance


def ascent_confirmation(previous_hold, geometry_ready, support, tilt, arm_error, failure, cfg, dt):
    """Confirm residence on the platform without demanding an uninterrupted gait phase.

    Geometry and recent actual loading of all four feet must persist throughout
    the confirmation window. At completion, require real current support,
    upright posture and the configured arm tracking accuracy. Instantaneous
    walking speed and angular speed do not redefine whether ascent occurred.
    """
    hold = stable_timer(previous_hold, geometry_ready & ~failure, dt)
    success = ((hold >= cfg.traversal_seconds) & (support.sum(-1) >= 2)
               & (tilt < cfg.traversal_max_tilt) & (arm_error < cfg.traversal_arm_error)
               & ~failure)
    return hold, success

