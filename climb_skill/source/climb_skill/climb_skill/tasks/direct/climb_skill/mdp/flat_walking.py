"""Adapt LeggedManip_Lab walking costs to flat phases of the climbing task.

No clock, contact-triggered foot-switch gate, or three-foot support requirement.
The geometry mask deliberately stays active during flight over a flat surface.
"""
import math
import torch
from .geometry import box_scan


def flat_walking_mask(pos, feet, heights, cfg):
    footprint = pos[:, None, :2] + pos.new_tensor(
        [[.35,.20],[.35,-.20],[-.35,.20],[-.35,-.20]])
    probes = box_scan(footprint, heights, cfg) > 0.
    foot_plane = box_scan(feet[..., :2], heights, cfg) > 0.
    all_planes = torch.cat((probes, foot_plane), dim=-1)
    return (all_planes.all(-1) | (~all_planes).all(-1)).to(pos.dtype)


def walking_quality_curriculum(mask, heights, cfg):
    """Quality costs start only after successful ascent promoted this environment."""
    return mask * (heights >= cfg.flat_walk_start_height)


def path_deviation_cost(pos):
    return ((pos[:,1].abs()-.03).clamp_min(0.)/.20).square()


def flat_walking_costs(mask, forces, vertical_speed, joint_deviation,
                       last_air_time, last_contact_time, current_air_time):
    flight = (forces[..., 2] <= 2.).all(-1).float()
    # Same capped timing variance as LeggedManip_Lab. Alone this cannot reject hopping.
    variance = last_air_time.clamp_max(.5).var(-1) + last_contact_time.clamp_max(.5).var(-1)
    long_air = (current_air_time - .5).clamp_min(0.).square().sum(-1)
    q = joint_deviation[:, :12].reshape(-1, 4, 3)  # FL, FR, RL, RR
    mirror = ((q[:,0]-q[:,3]).square().sum(-1) + (q[:,1]-q[:,2]).square().sum(-1)) / 2
    return {"flat_walk_flight": mask*flight,
            "flat_walk_vertical": mask*vertical_speed.square(),
            "flat_walk_air_variance": mask*variance,
            "flat_walk_long_air": mask*long_air,
            "flat_walk_mirror": mask*mirror}


def flat_velocity_tracking(velocity_xy, command):
    # NAV-style exponential tracking, with a movement factor to avoid standing income.
    error = (velocity_xy[:,0]-command).square() + velocity_xy[:,1].square()
    moving = (velocity_xy[:,0] / command.clamp_min(1e-6)).clamp(0.,1.)
    return torch.exp(-error/.25) * moving


def straight_tracking_costs(pos, yaw, velocity_y, yaw_rate):
    error = torch.atan2(yaw.sin(), yaw.cos())
    # Normalize heading by 10 degrees: the old 1-cos cost was tiny near zero.
    heading = (1.-error.cos()) / (1.-math.cos(math.radians(10)))
    path = path_deviation_cost(pos)
    # Permit corrective sideways motion and turning, rather than opposing recovery.
    desired_y_velocity = (-pos[:,1]).clamp(-.2,.2)
    desired_yaw_rate = (-1.5*error).clamp(-.6,.6)
    return {"straight_heading": heading, "straight_path": path,
            "straight_lateral_velocity": (velocity_y-desired_y_velocity).square(),
            "straight_yaw_rate": (yaw_rate-desired_yaw_rate).square()}
