"""Unmodified function copies from repository CLIMB guidance; see provenance."""
import torch

def balanced_vertical_loads(feet, com, weight, selected, unloading):
    """Quasi-static loads; report the residual after unilateral-force clipping."""
    relative = feet[:, :, :2] - com[:, None, :2]
    matrix = torch.cat((torch.ones_like(relative[..., :1]), relative), -1).transpose(1, 2)
    rhs = torch.stack((weight, torch.zeros_like(weight), torch.zeros_like(weight)), -1)
    availability = torch.ones_like(feet[:, :, 0])
    availability.scatter_(1, selected[:, None], 0.)

    def solve(weights):
        weighted = matrix * weights[:, None]
        regularizer = 1e-7 * torch.eye(3, device=feet.device, dtype=feet.dtype)
        loads = (weighted.transpose(1, 2) @ torch.linalg.solve(
            weighted @ weighted.transpose(1, 2) + regularizer, rhs[:, :, None])).squeeze(-1)
        loads = loads.clamp_min(0) * weights
        return loads * (weight / loads.sum(1).clamp_min(1e-6))[:, None]

    loads = torch.lerp(solve(torch.ones_like(availability)), solve(availability), unloading[:, None])
    residual = (matrix @ loads[:, :, None]).squeeze(-1) - rhs
    return loads, residual

def balanced_acceleration_loads(feet, com, weight, selected, unloading, acceleration):
    """Match horizontal acceleration and roll/pitch moments at mixed foot heights.

    Each horizontal force is proportional to its normal load. Moving the XY
    lever arms by dz*a/g reduces moment balance to the vertical allocation.
    Nonnegative clipping can invalidate that balance; return the actual residual.
    """
    adjusted = feet.clone()
    adjusted[:, :, :2] -= (feet[:, :, 2]-com[:, None, 2])[:, :, None]*acceleration[:, None]/9.81
    normal, _ = balanced_vertical_loads(adjusted, com, weight, selected, unloading)
    forces = torch.cat((normal[:, :, None]*acceleration[:, None]/9.81, normal[:, :, None]), -1)
    target = torch.cat((weight[:, None]*acceleration/9.81, weight[:, None]), -1)
    residual = torch.cat((forces.sum(1)-target, torch.cross(feet-com[:, None], forces, dim=-1).sum(1)), -1)
    return forces, residual
