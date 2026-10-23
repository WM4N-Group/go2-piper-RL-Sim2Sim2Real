"""Tensor-only foot selection and edge clearance for the isolated climb curriculum."""
import torch


def outer_reach_margin(hip, thigh, calf, foot, target, reserve=.03):
    """GO2 geometric outer bound only; it does not certify joint/collision feasibility."""
    lateral = (thigh - hip).norm(dim=-1)
    links = (calf - thigh).norm(dim=-1) + (foot - calf).norm(dim=-1)
    radius = (lateral.square() + links.square()).sqrt()
    return radius - reserve - (target - hip).norm(dim=-1)


def supported_lift_scores(foot_force_z, leg, actual_z, start_z, target_z, active):
    """Give no unload/lift credit when another stance foot loses support."""
    rows = torch.arange(len(leg), device=leg.device)
    selected = torch.nn.functional.one_hot(leg, 4).bool()
    contacts = foot_force_z > 2.
    tripod = (contacts | selected).all(dim=1)
    force = foot_force_z.clamp_min(0)
    # Normalize against the measured total load so floating has no advantage.
    share = force[rows, leg] / force.sum(1).clamp_min(1.)
    unload = (1. - share / .25).clamp(0., 1.)
    height = ((actual_z - start_z) / (target_z - start_z).clamp_min(.02)).clamp(0., 1.)
    valid = active & tripod
    # Height credit is for the unloaded foot, not a loaded contact on an edge.
    return unload * valid, height * valid * ~contacts[rows, leg], (~contacts[rows, leg] & valid).float()


def loaded_position_reference(position,torque,effort,stiffness):
    if not torch.isfinite(stiffness).all() or (stiffness<=0).any():
        raise ValueError('Use actual positive actuator PD stiffness')
    return position+torque.clamp(-.75*effort,.75*effort)/stiffness


def choose_stage_leg(local_feet, contacts, pending, fallback_leg, front_followup=False, front_followup_target=None):
    on_top=(local_feet[:,:,0]>.79)&(local_feet[:,:,2]>.19)&(contacts|pending[:,None])
    front_missing=~on_top[:,:2]
    front=torch.where(front_missing[:,0],0,1)
    rear=torch.where(local_feet[:,2,0]<=local_feet[:,3,0],2,3)
    rear=torch.where(on_top[:,2]&~on_top[:,3],3,rear)
    rear=torch.where(on_top[:,3]&~on_top[:,2],2,rear)
    chosen = torch.where(on_top.all(1),fallback_leg,torch.where(front_missing.any(1),front,rear))
    if front_followup:
        # Once the rear feet catch up, advance the front support anchors on top.
        # Otherwise the growing rear support triangle cannot carry the body forward.
        rear_x = local_feet[:, 2:, 0].amin(1)
        target = torch.where(rear_x >= .55,
            1.23 if front_followup_target is None else front_followup_target-.02, 1.03)
        behind = local_feet[:, :2, 0] < target[:, None]
        front_next = torch.where(behind[:, 0], 0, 1)
        move_front = (on_top[:, :2].all(1) & ~on_top.all(1)
                      & (rear_x >= .35) & behind.any(1))
        chosen = torch.where(move_front, front_next, chosen)
    return chosen


def next_stage_foothold_x(local_x, stride):
    next_x=local_x+stride
    edge=(next_x>.69)&(next_x<.83)
    return torch.where(edge,torch.where(local_x<.58,.69,.83),next_x).clamp(max=1.75)


def limit_front_followup_x(next_x, local_feet, contacts, leg, target):
    """Bound only the second platform front advance; preserve ascent and rear steps."""
    on_top = (local_feet[:, :2, 0] > .79) & (local_feet[:, :2, 2] > .19) & contacts[:, :2]
    all_top = ((local_feet[:, :, 0] > .79) & (local_feet[:, :, 2] > .19) & contacts).all(1)
    second = on_top.all(1) & ~all_top & (local_feet[:, 2:, 0].amin(1) >= .55) & (leg < 2)
    current = local_feet[torch.arange(len(leg), device=leg.device), leg, 0]
    return torch.where(second, torch.maximum(current, next_x.clamp(max=target)), next_x)


def limit_rear_ascent_x(next_x, local_feet, contacts, leg, target):
    """Shorten only the first rear landing on top; retain the existing edge reserve."""
    rows = torch.arange(len(leg), device=leg.device)
    selected = local_feet[rows, leg]
    front_supported = ((local_feet[:, :2, 0] > .79)
                       & (local_feet[:, :2, 2] > .19) & contacts[:, :2]).all(1)
    ascending = (leg >= 2) & (selected[:, 2] < .10) & (next_x >= .83) & front_supported
    return torch.where(ascending, torch.maximum(selected[:, 0], next_x.clamp(max=target)), next_x)


def prepare_rear_edge_x(next_x, local_feet, contacts, leg):
    """Move both rear feet to the existing.69m ground anchor before either ascends."""
    selected = local_feet[torch.arange(len(leg), device=leg.device), leg]
    on_top = (local_feet[..., 0] > .79) & (local_feet[..., 2] > .19) & contacts
    prepare = ((leg >= 2) & (on_top[:, :2].all(1)) & (local_feet[:, 2:, 2].amax(1) < .10) & (selected[:, 2] < .10)
               & (selected[:, 0] < .68) & (next_x >= .83))
    return torch.where(prepare, torch.full_like(next_x, .69), next_x)
