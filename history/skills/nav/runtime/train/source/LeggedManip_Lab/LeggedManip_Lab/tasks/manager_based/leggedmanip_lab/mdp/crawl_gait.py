"""Tensor-only contact-gated crawl scheduling and joint reference limits."""

import torch


class CrawlClock:
    """FL, RR, FR, RL; advance only after the chosen foot lifted and landed."""

    def __init__(self, count, device, transfer=.10, swing=.60, settle=.15):
        self.transfer, self.swing, self.settle = transfer, swing, settle
        self.order = torch.tensor([0, 3, 1, 2], device=device)
        self.index = torch.zeros(count, dtype=torch.long, device=device)
        self.elapsed = torch.zeros(count, device=device)
        self.stable = torch.zeros(count, device=device)
        self.lifted = torch.zeros(count, dtype=torch.bool, device=device)

    @property
    def leg(self):
        return self.order[self.index]

    @property
    def progress(self):
        value = ((self.elapsed - self.transfer) / self.swing).clamp(0, 1)
        return torch.where(self.elapsed >= self.transfer + self.swing - 1e-6, 1., value)

    def reset(self, ids=None):
        ids = slice(None) if ids is None else ids
        self.index[ids] = 0
        self.elapsed[ids] = 0
        self.stable[ids] = 0
        self.lifted[ids] = False

    def update(self, contacts, active, dt, *, lift_ready=None, traverse_ready=None, settle_ready=None):
        chosen = torch.nn.functional.one_hot(self.leg, 4).bool()
        other_support = (contacts | chosen).all(dim=1)
        selected_contact = (contacts & chosen).any(dim=1)
        self.lifted |= active & (self.elapsed >= self.transfer) & ~selected_contact
        self.stable = torch.where(active & contacts.all(dim=1), self.stable + dt, 0.)
        can_move = other_support & ((self.elapsed >= self.transfer) | contacts.all(dim=1))
        next_elapsed = (self.elapsed + dt).clamp(max=self.transfer + self.swing)
        # Keep the raised reference until the real foot catches up; a policy must
        # not skip the lift merely by waiting for a time-driven trajectory to end.
        for fraction, ready in ((.25, lift_ready), (.75, traverse_ready)):
            if ready is not None:
                boundary = self.transfer + fraction * self.swing
                waiting = (self.elapsed <= boundary + 1e-6) & ~ready
                next_elapsed = torch.where(waiting, next_elapsed.clamp(max=boundary), next_elapsed)
        self.elapsed = torch.where(active & can_move, next_elapsed, self.elapsed)
        advance = active & self.lifted & (self.elapsed >= self.transfer + self.swing - 1e-6) & (self.stable >= self.settle)
        if settle_ready is not None:
            advance &= settle_ready
        self.index[advance] = (self.index[advance] + 1) % 4
        self.elapsed[advance] = 0
        self.stable[advance] = 0
        self.lifted[advance] = False
        return advance


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
    return next_position, next_velocity


def swing_reference(start, landing, progress, clearance=.07):
    """Lift, translate, lower, with zero endpoint velocity at each segment."""
    def smooth(t):
        t = t.clamp(0, 1)
        return t**3 * (10 - 15 * t + 6 * t**2)
    high = torch.maximum(start[:, 2], landing[:, 2]) + clearance
    result = start + smooth((progress - .25) / .5)[:, None] * (landing - start)
    up = start[:, 2] + smooth(progress / .25) * (high - start[:, 2])
    down = high + smooth((progress - .75) / .25) * (landing[:, 2] - high)
    result[:, 2] = torch.where(progress < .25, up, torch.where(progress > .75, down, high))
    return result


class PlatformFrontExtension:
    """Two front steps after a verified four-foot landing, then permanent hold.

    This schedules references only. The caller retains support, swing feasibility,
    touchdown and load-confirmation gates before moving or completing a foot.
    """
    def __init__(self, count, device, distance):
        if not 0. < distance <= .08:
            raise ValueError('Platform front extension must be in (0, .08] meters')
        self.distance = distance
        self.completed = torch.zeros(count, dtype=torch.long, device=device)
        self.moving = torch.zeros(count, dtype=torch.bool, device=device)
        self.started = torch.zeros_like(self.moving)
        self.stable = torch.zeros(count, device=device)
        self.goals = torch.zeros(count, 2, 3, device=device)

    def reset(self, ids):
        self.completed[ids] = 0
        self.moving[ids] = False
        self.started[ids] = False
        self.stable[ids] = 0.
        self.goals[ids] = 0.

    def landed(self, verified_landing):
        completed = verified_landing & self.moving
        self.completed[completed] += 1
        self.moving[completed] = False
        self.stable[verified_landing] = 0.

    def release(self, hold, ready, feet, env_origins, dt):
        eligible = hold & ready & ~self.moving & (self.completed < 2)
        # Never leave the original platform footprint or turn a tiny boundary
        # remainder into an endless sequence of additional footsteps.
        goals = feet[:, :2].clone()
        goals[..., 0] += self.distance
        inside = ((goals[..., 0]-env_origins[:, None, 0] < 1.91)
                  & ((goals[..., 1]-env_origins[:, None, 1]).abs() < .56)).all(1)
        eligible &= self.started | inside
        self.stable[:] = torch.where(eligible, self.stable+dt, 0.)
        release = eligible & (self.stable >= 1.)
        first = release & ~self.started
        self.goals[first] = goals[first]
        self.started[release] = True
        self.moving[release] = True
        self.stable[release] = 0.
        return release
