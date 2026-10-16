import torch

def triangle_margin(point, triangle):
    edge = triangle.roll(-1, 1) - triangle
    sign = (edge[:, 0, 0] * edge[:, 1, 1] - edge[:, 0, 1] * edge[:, 1, 0]).sign()
    normal = torch.stack((-edge[..., 1], edge[..., 0]), -1)
    normal = normal * sign[:, None, None] / edge.norm(dim=-1).clamp_min(1e-08)[..., None]
    return (((point[:, None] - triangle) * normal).sum(-1), normal)

def inset_support_target(point, triangle, reserve=0.035):
    target = point.clone()
    for _ in range(12):
        for i in range(3):
            margin, normal = triangle_margin(target, triangle)
            target += (reserve - margin[:, i]).clamp_min(0)[:, None] * normal[:, i]
    return target

def balanced_vertical_loads(feet, com, weight, selected, unloading):
    """Quasi-static loads; report the residual after unilateral-force clipping."""
    relative = feet[:, :, :2] - com[:, None, :2]
    matrix = torch.cat((torch.ones_like(relative[..., :1]), relative), -1).transpose(1, 2)
    rhs = torch.stack((weight, torch.zeros_like(weight), torch.zeros_like(weight)), -1)
    availability = torch.ones_like(feet[:, :, 0])
    availability.scatter_(1, selected[:, None], 0.0)

    def solve(weights):
        weighted = matrix * weights[:, None]
        regularizer = 1e-07 * torch.eye(3, device=feet.device, dtype=feet.dtype)
        loads = (weighted.transpose(1, 2) @ torch.linalg.solve(weighted @ weighted.transpose(1, 2) + regularizer, rhs[:, :, None])).squeeze(-1)
        loads = loads.clamp_min(0) * weights
        return loads * (weight / loads.sum(1).clamp_min(1e-06))[:, None]
    loads = torch.lerp(solve(torch.ones_like(availability)), solve(availability), unloading[:, None])
    residual = (matrix @ loads[:, :, None]).squeeze(-1) - rhs
    return (loads, residual)

def balanced_acceleration_loads(feet, com, weight, selected, unloading, acceleration):
    """Match horizontal acceleration and roll/pitch moments at mixed foot heights.

    Each horizontal force is proportional to its normal load. Moving the XY
    lever arms by dz*a/g reduces moment balance to the vertical allocation.
    Nonnegative clipping can invalidate that balance; return the actual residual.
    """
    adjusted = feet.clone()
    adjusted[:, :, :2] -= (feet[:, :, 2] - com[:, None, 2])[:, :, None] * acceleration[:, None] / 9.81
    normal, _ = balanced_vertical_loads(adjusted, com, weight, selected, unloading)
    forces = torch.cat((normal[:, :, None] * acceleration[:, None] / 9.81, normal[:, :, None]), -1)
    target = torch.cat((weight[:, None] * acceleration / 9.81, weight[:, None]), -1)
    residual = torch.cat((forces.sum(1) - target, torch.cross(feet - com[:, None], forces, dim=-1).sum(1)), -1)
    return (forces, residual)

def feedback_unload(current, prepared, selected_contact, swing, dt):
    """Unload only feasible support; restore load only onto a measured contact."""
    delta = torch.where(prepared, dt / 1.5, torch.where(selected_contact, -dt / 1.5, 0.0))
    return torch.where(swing, torch.ones_like(current), (current + delta).clamp(0, 1))

class UnloadForceTrim:
    """Bounded measured-force correction after nominal unloading has stalled.

    A positive vertical Jacobian-transpose term pulls the selected foot upward.
    This never changes the actual-force release gate or advances the foot clock.
    """

    def __init__(self, count, device):
        self.stall_age = torch.zeros(count, device=device)
        self.force_n = torch.zeros_like(self.stall_age)
        self.applied_n = torch.zeros_like(self.stall_age)

    def reset(self, mask):
        self.stall_age[mask] = 0.0
        self.force_n[mask] = 0.0
        self.applied_n[mask] = 0.0

    def update(self, selected_force, eligible, progress, dt, max_force=8.0):
        waiting = progress == 0
        stalled = eligible & waiting & (selected_force > 5.0)
        self.stall_age[:] = torch.where(stalled, self.stall_age + dt, 0.0)
        integrating = eligible & waiting & ((self.stall_age >= 0.5) | (self.force_n > 0.0))
        rate = (selected_force - 3.0).clamp(0.0, 2.0)
        self.force_n[:] = torch.where(integrating, (self.force_n + rate * dt).clamp(max=max_force), self.force_n)
        self.force_n[:] = torch.where(waiting & ~eligible, (self.force_n - 2.0 * dt).clamp_min(0.0), self.force_n)
        t = (progress / 0.25).clamp(0.0, 1.0)
        smooth = t ** 3 * (10.0 - 15.0 * t + 6.0 * t * t)
        self.applied_n[:] = self.force_n * (1.0 - smooth)
        return self.applied_n

def limit_reference(position, velocity, target, lower, upper, max_velocity, max_acceleration, dt):
    """Bound target rate/acceleration, with braking envelopes near joint limits."""
    target = torch.maximum(torch.minimum(target, upper), lower)
    desired = ((target - position) / dt).clamp(-max_velocity, max_velocity)
    next_velocity = torch.maximum(torch.minimum(desired, velocity + max_acceleration * dt), velocity - max_acceleration * dt)
    step_braking = max_acceleration * dt
    positive = torch.sqrt(2 * max_acceleration * (upper - position).clamp_min(0) + step_braking.square()) - step_braking
    negative = torch.sqrt(2 * max_acceleration * (position - lower).clamp_min(0) + step_braking.square()) - step_braking
    next_velocity = torch.maximum(torch.minimum(next_velocity, positive), -negative)
    next_position = torch.maximum(torch.minimum(position + dt * next_velocity, upper), lower)
    return (next_position, next_velocity)


class LandingContact:
    """Bounded contact search, then measured load confirmation before switching."""
    def __init__(self, count, device):
        self.depth = torch.zeros(count, device=device)
        self.touch_age = torch.zeros_like(self.depth)
        self.reload = torch.zeros_like(self.depth)
        self.loaded_age = torch.zeros_like(self.depth)

    def reset(self, mask):
        for state in (self.depth, self.touch_age, self.reload, self.loaded_age):
            state[mask] = 0.

    def update(self, at_end, touch, supported, selected_force, calm, dt):
        probing = at_end & supported & calm & ~touch
        self.depth[:] = (self.depth + probing*.004*dt).clamp(max=.015)
        contact = at_end & touch & supported
        self.touch_age[:] = torch.where(contact, self.touch_age+dt, 0.)
        # Never assign support load to a foot that has lost measured contact.
        self.reload[:] = torch.where(contact & (self.touch_age >= .1),
                                     (self.reload+dt/.6).clamp(max=1.), 0.)
        loaded = contact & (self.reload >= 1.) & (selected_force >= 8.) & calm
        self.loaded_age[:] = torch.where(loaded, self.loaded_age+dt, 0.)
        return self.loaded_age >= .2
