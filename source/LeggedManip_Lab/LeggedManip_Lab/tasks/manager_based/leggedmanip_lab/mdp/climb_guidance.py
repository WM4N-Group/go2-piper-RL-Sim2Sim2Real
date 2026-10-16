"""Opt-in edge diagnostic: support transfer and bounded leg IK, not acceptance."""
import torch
from .climb_leg_kinematics import LegKinematics, rotate_vector


def triangle_margin(point, triangle):
    edge = triangle.roll(-1, 1) - triangle
    sign = (edge[:, 0, 0]*edge[:, 1, 1]-edge[:, 0, 1]*edge[:, 1, 0]).sign()
    normal = torch.stack((-edge[..., 1], edge[..., 0]), -1)
    normal = normal * sign[:, None, None] / edge.norm(dim=-1).clamp_min(1e-8)[..., None]
    return ((point[:, None]-triangle)*normal).sum(-1), normal


def inset_support_target(point, triangle, reserve=.035):
    target = point.clone()
    for _ in range(12):
        for i in range(3):
            margin, normal = triangle_margin(target, triangle)
            target += (reserve-margin[:, i]).clamp_min(0)[:, None]*normal[:, i]
    return target


def loaded_leg_reference(previous, nominal, bias, residual, bounds, valid, engaged, selected, progress):
    fraction = (progress/.25).clamp(0,1)
    fraction = fraction**3*(10-15*fraction+6*fraction**2)
    load = bias.clone()
    load[torch.arange(len(selected),device=selected.device),selected] *= (1-fraction)[:,None]
    proposed = nominal+load+residual
    valid = valid & engaged[:,None] & ((proposed >= bounds[...,0]) & (proposed <= bounds[...,1])).all(2)
    return torch.where(valid[...,None],proposed,previous), valid


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


def unloaded_support_ready(forces, selected, margin, velocity, angular_velocity):
    chosen = torch.nn.functional.one_hot(selected, 4).bool()
    return (((forces > 2.) | chosen).all(1)
            & ((forces*chosen).sum(1) <= 5.) & (margin >= .015)
            & (velocity.norm(dim=1) < .04) & (angular_velocity.norm(dim=1) < .15))


def feedback_unload(current, prepared, selected_contact, swing, dt):
    """Unload only feasible support; restore load only onto a measured contact."""
    delta = torch.where(prepared, dt/1.5, torch.where(selected_contact, -dt/1.5, 0.))
    return torch.where(swing, torch.ones_like(current), (current+delta).clamp(0, 1))


def front_followup_trim_scope(local_feet, contacts, leg, start, landing):
    """Front step on the platform while both rear feet still support on ground."""
    front_top = ((local_feet[:, :2, 0] > .79) & (local_feet[:, :2, 0] < 1.91)
        & (local_feet[:, :2, 1].abs() < .56)
        & (local_feet[:, :2, 2] > .19) & (local_feet[:, :2, 2] < .26)).all(1)
    rear_ground = ((local_feet[:, 2:, 0] < .75) & (local_feet[:, 2:, 2] < .10)).all(1)
    chosen = torch.nn.functional.one_hot(leg, 4).bool()
    return (front_top & rear_ground & (contacts | chosen).all(1) & (leg < 2)
        & (start[:, 0] > .79) & (start[:, 2] > .19)
        & (landing[:, 0]-start[:, 0] > .02)
        & ((landing[:, 2]-start[:, 2]).abs() < .02))


def front_stall_trim_limit(feet, leg, start, landing, stall_age, force_n):
    """Permit10N only for a long-stalled front ascent from below the box.

    Keep the higher bound through measured unload dwell and smooth lift fade.
    Runtime retains all support, motion, pose, command and force-release gates.
    """
    foot = feet[torch.arange(len(feet), device=feet.device), leg]
    ascent = ((leg < 2) & (foot[:, 0] < .75) & (foot[:, 2] < .10)
        & (landing[:, 2]-start[:, 2] > .10))
    recovered = (stall_age >= 10.) | (force_n > 8.)
    return torch.where(ascent & recovered, 10., 8.)


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
        self.stall_age[mask] = 0.
        self.force_n[mask] = 0.
        self.applied_n[mask] = 0.

    def update(self, selected_force, eligible, progress, dt, max_force=8.):
        waiting = progress == 0
        stalled = eligible & waiting & (selected_force > 5.)
        self.stall_age[:] = torch.where(stalled, self.stall_age+dt, 0.)
        integrating = eligible & waiting & ((self.stall_age >= .5) | (self.force_n > 0.))
        # Target3N leaves room below the unchanged5N measured release condition.
        rate = (selected_force-3.).clamp(0., 2.)
        self.force_n[:] = torch.where(integrating,
            (self.force_n+rate*dt).clamp(max=max_force), self.force_n)
        self.force_n[:] = torch.where(waiting & ~eligible,
            (self.force_n-2.*dt).clamp_min(0.), self.force_n)
        t = (progress/.25).clamp(0., 1.)
        smooth = t**3*(10.-15.*t+6.*t*t)
        self.applied_n[:] = self.force_n*(1.-smooth)
        return self.applied_n


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


def mixed_support_body_height(feet, clearance):
    """Diagnostic: keep ground-leg clearance while feet straddle a20cm step."""
    height = feet[:, :, 2]
    lower = height.amin(1)
    surface = torch.where(height.amax(1)-lower > .1, lower, height.mean(1))
    return surface + clearance


def single_front_support_scope(local_feet, contacts, leg):
    """Only the planted one-front-up transfer before the other front foot lifts."""
    top = ((local_feet[..., 0] > .79) & (local_feet[..., 0] < 1.91)
           & (local_feet[..., 1].abs() < .56) & (local_feet[..., 2] > .19))
    ground = (local_feet[..., 0] < .75) & (local_feet[..., 2] < .10)
    selected = torch.nn.functional.one_hot(leg, 4).bool()
    return (contacts.all(1) & (top[:, :2].sum(1) == 1) & ground[:, 2:].all(1)
            & (leg < 2) & (selected & ground).any(1))


def support_plane_pose(feet, root, quaternion, clearance, fraction=1.):
    """Bounded pitch and vertical clearance over the front/rear support plane."""
    w, x, y, z = quaternion.unbind(-1)
    yaw = torch.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    forward = torch.stack((yaw.cos(), yaw.sin()), -1)
    front, rear = feet[:, :2].mean(1), feet[:, 2:].mean(1)
    span = ((front-rear)[:, :2]*forward).sum(1).clamp_min(.15)
    slope = ((front[:, 2]-rear[:, 2])/span).clamp(-.35, .35)
    height = rear[:, 2] + slope*((root-rear)[:, :2]*forward).sum(1) + clearance
    pitch = -torch.atan(slope)
    if fraction != 1.:
        height = torch.lerp(mixed_support_body_height(feet, clearance), height, fraction)
        pitch = pitch*fraction
    cy, sy, cp, sp = (yaw/2).cos(), (yaw/2).sin(), (pitch/2).cos(), (pitch/2).sin()
    orientation = torch.stack((cy*cp, -sy*sp, cy*sp, sy*cp), -1)
    # Equivalent quaternions must interpolate along the short arc.
    orientation *= torch.where((orientation*quaternion).sum(1) < 0, -1., 1.)[:, None]
    return height, orientation


def tripod_support_clearance(feet, selected, positions):
    """Match LowPosture's lowest supported foot surface after selected-foot unload."""
    chosen = torch.nn.functional.one_hot(selected, 4).bool()
    surface = torch.where(chosen, torch.full_like(feet[..., 2], torch.inf), feet[..., 2]-.0225).amin(1)
    return positions[..., 2]-surface[:, None]


def front_support_height(model, feet, positions, rotations):
    """Minimum vertical front hip-to-foot span, including body pitch and roll."""
    offsets=model.origins[:2].expand(*positions.shape[:-1],2,3)
    hips=positions[...,None,:]+rotate_vector(rotations[...,None,:],offsets)
    return (hips[...,2]-feet[:,None,:2,2]).amin(-1)


def front_raise_candidate_ready(model, feet, origin, positions, rotations, preview):
    if 'front_raise_target' not in preview:
        return torch.ones(positions.shape[:2],dtype=torch.bool,device=positions.device)
    current=preview['front_raise_current'][:,None]
    target=preview['front_raise_target'][:,None]
    # Progress in bounded four-foot transfers until the requested extension is
    # reached; later transfers must preserve it. Lift uses measured height.
    required=torch.minimum(target,current+.01)
    return front_support_height(model,feet,positions,rotations)>=required


def predicted_support_com(origin, positions, rotations, preview):
    """Move the measured COM offset with the proposed body pose.

    Limb mass redistribution is still approximate; measured support gates remain
    authoritative. Without an orientation, preserve the original translation.
    """
    # Preserve the original arithmetic order outside the targeted stage.
    translated=preview['com'][:,None]+positions-origin[:,None]
    if 'orientation' not in preview:
        return translated
    local=rotate_vector(preview['orientation'],preview['com']-origin,True)
    rotated=positions+rotate_vector(rotations,local[:,None].expand_as(positions))
    active=preview.get('rotation_active',torch.ones(len(origin),dtype=torch.bool,device=origin.device))
    return torch.where(active[:,None,None],rotated,translated)


def last_rear_com_scope(local_feet, contacts, leg, start, landing):
    top=(local_feet[...,0]>.79)&(local_feet[...,2]>.19)&contacts
    ground=local_feet[torch.arange(len(leg),device=leg.device),leg,2]<.10
    return (top.sum(1)==3)&ground&(leg>=2)&(landing[:,2]-start[:,2]>.1)&contacts.all(1)


def four_support_path_loads(feet, origin, quaternion, positions, rotations, preview):
    """Frozen COM load estimate while all feet stay planted during transfer.

    Full tripod load checks alone intentionally bypass partial transfers. Those
    still need positive loads on every planted foot and a balanced resultant.
    This is a planning estimate; measured contact gates remain authoritative.
    """
    return four_support_path_checks(feet, origin, quaternion, positions, rotations, preview)[:2]


def four_support_path_checks(feet, origin, quaternion, positions, rotations, preview):
    """Also identify paths that restore an initially weak but planted support.

    Weak feet may not lose any predicted load along the sampled path; every
    other foot retains8N, and the endpoint must restore8N on all four feet.
    """
    n, count = positions.shape[:2]
    minimum = positions.new_full((n, count), float('inf'))
    residual_peak = positions.new_zeros((n, count))
    expanded_feet = feet[:, None].expand(-1, count, -1, -1).reshape(-1, 4, 3)
    weight = preview['weight'][:, None].expand(-1, count).reshape(-1)
    leg = preview['leg'][:, None].expand(-1, count).reshape(-1)
    recovery = torch.ones((n*count,), device=feet.device, dtype=torch.bool)
    previous = None
    for fraction in torch.linspace(0., 1., 21, device=feet.device, dtype=feet.dtype):
        pose = torch.lerp(origin[:, None], positions, fraction)
        turn = torch.lerp(quaternion[:, None], rotations, fraction)
        turn = turn/turn.norm(dim=-1, keepdim=True)
        com = predicted_support_com(origin, pose, turn, preview)
        loads, residual = balanced_vertical_loads(expanded_feet, com.reshape(-1, 3),
            weight, leg, torch.zeros_like(weight))
        if previous is None:
            weak = loads < 8.
            floor = loads.clamp(max=8.)
            recovery &= loads.amin(-1) >= 2.
        else:
            recovery &= ((loads >= previous-1e-4) | ~weak).all(-1)
        recovery &= (loads >= floor-1e-4).all(-1)
        previous = loads
        minimum = torch.minimum(minimum, loads.amin(-1).reshape(n, count))
        residual_peak = torch.maximum(residual_peak, residual.norm(dim=-1).reshape(n, count))
    recovery &= loads.amin(-1) >= 8.
    return minimum, residual_peak, recovery.reshape(n, count)


def support_load_preview(model, feet, origin, positions, rotations, joints, bounds, preview):
    """Estimate settled tripod commands using candidate leg lever arms.

    Current gravity compensation and the predicted measured COM are estimates;
    this adds a planning check without replacing measured load/limit gates.
    """
    count, candidates = positions.shape[:2]
    com = predicted_support_com(origin,positions,rotations,preview)
    expanded_feet = feet[:, None].expand(-1, candidates, -1, -1)
    selected = preview["leg"][:, None].expand(-1, candidates).reshape(-1)
    loads, _ = balanced_vertical_loads(expanded_feet.reshape(-1,4,3), com.reshape(-1,3),
        preview["weight"][:,None].expand(-1,candidates).reshape(-1), selected,
        torch.ones_like(selected, dtype=feet.dtype))
    loads = loads.reshape(count, candidates, 4)
    jacobian = model.jacobian(joints)
    up = torch.zeros_like(positions);up[...,2] = 1.
    local_up = rotate_vector(rotations, up, inverse=True)
    vertical_jacobian = (jacobian*local_up[...,None,:,None]).sum(-2)
    torque = preview["gravity"][:,None]-vertical_jacobian*loads[...,None]
    cap = .75*preview["effort"][:,None]
    torque_margin = ((cap-torque.abs())/30.).amin((-1,-2))
    torque = torch.maximum(torch.minimum(torque, cap), -cap)
    command = joints+torque/30.
    margin = torch.minimum(command-bounds[:,None,...,0], bounds[:,None,...,1]-command).amin((-1,-2))
    margin = torch.minimum(margin, torque_margin)
    # Partial transfers outside the tripod still keep four supports. Preview
    # full unloading only after the predicted COM can meet the existing gate.
    indices = torch.tensor([[j for j in range(4) if j != i] for i in range(4)], device=feet.device)
    triangle = expanded_feet.reshape(-1,4,3).gather(1,
        indices[selected,:,None].expand(-1,-1,3))[...,:2]
    support_margin = triangle_margin(com.reshape(-1,3)[:,:2], triangle)[0].amin(1).reshape(count,candidates)
    # Preserve the original.18m LowPosture gate, with1cm planning reserve.
    height_ready = tripod_support_clearance(feet, preview["leg"], positions) >= .19
    margin = torch.where(height_ready, margin, torch.full_like(margin, -1.))
    result = torch.where(support_margin >= .025, margin, torch.full_like(margin, 1e3))
    # A partial lateral transfer must not undo height already gained for the
    # last ground foot. Measured COM can differ from the translated estimate.
    raised = tripod_support_clearance(feet, preview["leg"], origin[:, None]) >= .19
    result = torch.where(raised & ~height_ready, torch.full_like(result, -1.), result)
    return torch.where(front_raise_candidate_ready(model,feet,origin,positions,rotations,preview),
                       result,torch.full_like(result,-1.))


def swing_transfer_options(feet, origin, positions, preview, swing_ready, rotations=None):
    """Allow improving four-foot transfers; never use partial progress as lift permission."""
    indices = torch.tensor([[j for j in range(4) if j != i] for i in range(4)], device=feet.device)
    triangle = feet.gather(1, indices[preview['leg'], :, None].expand(-1, -1, 3))[..., :2]
    n, count = positions.shape[:2]
    predicted = predicted_support_com(origin,positions,rotations,preview)[...,:2]
    margin = triangle_margin(predicted.reshape(-1, 2),
        triangle[:, None].expand(-1, count, -1, -1).reshape(-1, 3, 2))[0].amin(1).reshape(n, count)
    current = triangle_margin(preview['com'][:, :2], triangle)[0].amin(1)
    partial = (margin < .025) & (margin > current[:, None]+.002)
    return swing_ready | partial, partial


def swing_preview_ready(margin, error, gap, preview):
    """The same complete-path gate for planning and runtime lift permission."""
    required_gap = preview.get('minimum_gap', torch.full_like(margin[:, 0], .005))
    return (margin >= .03) & (error < .001) & (gap >= required_gap[:, None])


def swing_path_preview(model, feet, positions, rotations, bounds, preview, primitives, box_bounds):
    """Sample the planned swing before unloading; frozen pose/gravity estimate."""
    from .climb_body_clearance import leg_link_poses, primitive_box_gap
    n, count = positions.shape[:2]
    phase = torch.linspace(0., 1., 41, device=feet.device, dtype=feet.dtype)
    reference = edge_lift_reference(preview['start'][:, None].expand(-1, 41, -1).reshape(-1, 3),
        preview['landing'][:, None].expand(-1, 41, -1).reshape(-1, 3), phase.repeat(n),
        preview['origins'][:, None].expand(-1, 41, -1).reshape(-1, 3), preview['clearance'], preview['inset'][:, None].expand(-1, 41).reshape(-1)).reshape(n, 41, 3)
    if 'landing_probe_depth' in preview:
        # Include the existing bounded contact search below the nominal landing.
        # These are virtual joint-reference targets, not changed terrain geometry.
        probe = preview['landing'][:, None].expand(-1, 5, -1).clone()
        probe[..., 2] -= preview['landing_probe_depth'][:, None]*torch.linspace(
            .2, 1., 5, device=feet.device, dtype=feet.dtype)[None]
        reference = torch.cat((reference, probe), 1)
    world = feet[:, None, None].expand(-1, count, reference.shape[1], -1, -1).clone()
    chosen = torch.nn.functional.one_hot(preview['leg'], 4).bool()
    world = torch.where(chosen[:, None, None, :, None], reference[:, None, :, None], world)
    local = rotate_vector(rotations[:, :, None, None], world-positions[:, :, None, None], True)
    joints = model.inverse(local)
    command = joints+preview['gravity'][:, None, None]/30.
    nominal = torch.minimum(joints-bounds[:, None, None, :, :, 0],
                            bounds[:, None, None, :, :, 1]-joints).amin(-1)-.01
    loaded = torch.minimum(command-bounds[:, None, None, :, :, 0],
                           bounds[:, None, None, :, :, 1]-command).amin(-1)
    margin = torch.where(chosen[:, None, None], torch.minimum(nominal, loaded),
                         torch.full_like(nominal, 1e6)).amin((-1, -2))
    error = (model.forward(joints)-local).norm(dim=-1).amax((-1, -2))
    links, turns = leg_link_poses(model, joints, positions[:, :, None], rotations[:, :, None])
    gap = primitive_box_gap(links, turns, primitives, box_bounds[:, None, None, None, None]).amin((-1, -2, -3))
    if 'landing_com' in preview:
        # Preview full reloading at the new foothold, before committing to lift.
        # Actual contact/force/calm dwell remains the runtime authority.
        final_feet = world[:, :, 40]
        com = preview['landing_com'][:, None]+positions-preview['landing_origin'][:, None]
        if 'landing_orientation' in preview:
            com = predicted_support_com(preview['landing_origin'], positions, rotations,
                dict(com=preview['landing_com'], orientation=preview['landing_orientation'],
                     rotation_active=preview['landing_rotation_active']))
        leg = preview['leg'][:, None].expand(-1, count).reshape(-1)
        loads, _ = balanced_vertical_loads(final_feet.reshape(-1, 4, 3), com.reshape(-1, 3),
            preview['landing_weight'][:, None].expand(-1, count).reshape(-1), leg,
            torch.zeros_like(leg, dtype=feet.dtype))
        up = torch.zeros_like(positions);up[..., 2] = 1.
        vertical = (model.jacobian(joints[:, :, 40])*rotate_vector(rotations, up, True)[..., None, :, None]).sum(-2)
        torque = preview['gravity'][:, None]-vertical*loads.reshape(n, count, 4, 1)
        cap = .75*preview['landing_effort'][:, None]
        command = joints[:, :, 40]+torque/30.
        reload_margin = torch.minimum(command-bounds[:, None, ..., 0], bounds[:, None, ..., 1]-command).amin((-1, -2))
        reload_margin = torch.minimum(reload_margin, ((cap-torque.abs())/30.).amin((-1, -2)))
        margin = torch.minimum(margin, torch.where(preview['landing_probe_depth'][:, None] > 0,
            reload_margin, torch.full_like(reload_margin, 1e6)))
    return margin, error, gap


def support_endpoint_leg_gap(model, feet, positions, rotations, primitives, box_bounds):
    from .climb_body_clearance import leg_link_poses, primitive_box_gap
    local = rotate_vector(rotations[:, :, None], feet[:, None]-positions[:, :, None], inverse=True)
    joints = model.inverse(local)
    links, turns = leg_link_poses(model, joints, positions, rotations)
    return primitive_box_gap(links, turns, primitives, box_bounds[:, None, None, None]).amin((-1, -2))


def front_ascent_pose(model, feet, target, target_rotation, origin, quaternion, bias,
                      bounds, clearance, body_bounds, box_bounds, link_bounds, load, swing):
    """Prefer a complete guarded swing pose only when the current swing is unsafe.

    The caller must be in an existing four-contact capture, before unloading.
    Failed searches preserve the old plan; this preference is not a new lift gate.
    """
    sm, se, sg = swing_path_preview(model, feet, target[:, None], target_rotation[:, None],
                                   bounds, swing, link_bounds, box_bounds)
    retry = (sm[:, 0] < .03) | (se[:, 0] >= .001) | (sg[:, 0] < .005)
    pose, rotation = target.clone(), target_rotation.clone()
    margin = torch.zeros_like(sm[:, 0])
    accepted = torch.zeros_like(retry)
    if retry.any():
        result = feasible_support_pose(model, feet[retry], target[retry], origin[retry],
            quaternion[retry], bias[retry], bounds[retry], clearance, body_bounds,
            box_bounds[retry], True, link_bounds,
            {k:v[retry] for k,v in load.items()},
            {k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},
            height_samples=65, full_load_reserve=.03)
        accepted[retry] = result[3]
        ids = torch.where(retry)[0][result[3]]
        pose[ids], rotation[ids], margin[ids] = (v[result[3]] for v in result[:3])
    return pose, rotation, margin, retry, accepted


def predicted_tripod_margin(feet, origin, positions, rotations, preview):
    indices = torch.tensor([[j for j in range(4) if j != i] for i in range(4)], device=feet.device)
    triangle = feet.gather(1, indices[preview['leg'], :, None].expand(-1, -1, 3))[..., :2]
    n, count = positions.shape[:2]
    com = predicted_support_com(origin, positions, rotations, preview)[..., :2]
    return triangle_margin(com.reshape(-1, 2), triangle[:, None].expand(-1, count, -1, -1)
                           .reshape(-1, 3, 2))[0].amin(1).reshape(n, count)


def feasible_support_pose(model, feet, target, origin, quaternion, bias, bounds, clearance,
                          body_bounds=None, box_bounds=None, independent_height=False, link_bounds=None, load_preview=None, swing_preview=None, height_samples=17, endpoint_leg_reserve=0., endpoint_body_reserve=0., full_load_reserve=0.):
    """Select a joint-feasible endpoint using measured load bias as an estimate.

    This is a geometric endpoint check, not a dynamics or trajectory certificate.
    The runtime still applies reference limits and measured support gates.
    """
    if endpoint_leg_reserve and (endpoint_leg_reserve < .005 or not isinstance(link_bounds, dict)):
        raise ValueError("Endpoint reserve requires primitive geometry and at least the original5mm gap")
    if endpoint_body_reserve and (endpoint_body_reserve < .010 or body_bounds is None):
        raise ValueError("Body endpoint reserve requires geometry and at least the original10mm gap")
    if full_load_reserve and (full_load_reserve < .03 or load_preview is None):
        raise ValueError("Full-load reserve requires load preview and at least the original30mrad margin")
    if load_preview is not None and len(feet) > 2:
        # Bound temporary candidate/shape tensors on the shared simulation GPU.
        results = []
        for start in range(0, len(feet), 2):
            part = slice(start, start+2)
            results.append(feasible_support_pose(model, feet[part], target[part], origin[part],
                quaternion[part], bias[part], bounds[part], clearance, body_bounds,
                box_bounds[part], independent_height, link_bounds,
                {name: value[part] for name, value in load_preview.items()},
                None if swing_preview is None else {name: value[part] if torch.is_tensor(value) else value
                    for name, value in swing_preview.items()}, height_samples, endpoint_leg_reserve, endpoint_body_reserve, full_load_reserve))
        return tuple(torch.cat([result[i] for result in results]) for i in range(4))
    heights, orientations = [], []
    for fraction in (0., .25, .5, .75, 1.):
        height, orientation = support_plane_pose(feet, target, quaternion, clearance, fraction)
        for offset in (-.02, 0., .02):
            heights.append(height+offset)
            orientations.append(orientation)
    primary_count = len(heights)
    if independent_height:
        if body_bounds is None:
            raise ValueError("Independent height search requires the body path guard")
        # Preserve the existing choice whenever it is feasible. Only on failure,
        # decouple height from pitch; retain the measured orientation as an option.
        extra_rotations = [support_plane_pose(feet, target, quaternion, clearance, f)[1]
                           for f in (0., .25, .5, .75, 1.)] + [quaternion]
        for rotation in extra_rotations:
            for offset in torch.linspace(-.08, .08, height_samples, device=feet.device, dtype=feet.dtype):
                heights.append(origin[:, 2]+offset)
                orientations.append(rotation)
    positions = target[:, None].expand(-1, len(heights), -1).clone()
    positions[:, :, 2] = torch.stack(heights, 1)
    rotations = torch.stack(orientations, 1)
    if load_preview is not None:
        # Move the body further between its planted feet when loaded front knees
        # need bending. Preserve the existing per-transfer8cm displacement cap.
        offset = positions.new_tensor([0., .04, .08])[None,:,None]
        expanded = positions[:,None].expand(-1,3,-1,-1).clone()
        expanded[...,0] += offset
        delta = expanded[...,:2]-origin[:,None,None,:2]
        delta *= (.08/delta.norm(dim=-1).clamp_min(.08))[...,None]
        expanded[...,:2] = origin[:,None,None,:2]+delta
        positions = expanded.flatten(1,2)
        rotations = rotations[:,None].expand(-1,3,-1,-1).flatten(1,2)
    full_count = positions.shape[1]
    if link_bounds is not None:
        if body_bounds is None:
            raise ValueError("Leg path clearance requires base path clearance")
        # A full lateral/forward shift can be impossible with fixed support feet.
        # Try shorter transfers before holding; the measured support gate still
        # forbids lift until the complete weight transfer is actually achieved.
        fractions = positions.new_tensor([1., .5, .25])[None, :, None, None]
        expanded = positions[:, None].expand(-1, 3, -1, -1).clone()
        expanded[..., :2] = origin[:, None, None, :2] + fractions*(expanded[..., :2]-origin[:, None, None, :2])
        positions = expanded.flatten(1, 2)
        rotations = rotations[:, None].expand(-1, 3, -1, -1).flatten(1, 2)
    local = rotate_vector(rotations[:, :, None], feet[:, None]-positions[:, :, None], inverse=True)
    joints = model.inverse(local)
    command = joints+bias[:, None]
    nominal_margin = torch.minimum(joints-bounds[:, None, :, :, 0],
                                   bounds[:, None, :, :, 1]-joints).amin(dim=(-1, -2))-.01
    loaded_margin = torch.minimum(command-bounds[:, None, :, :, 0],
                                  bounds[:, None, :, :, 1]-command).amin(dim=(-1, -2))
    margin = torch.minimum(nominal_margin, loaded_margin)
    if load_preview is not None:
        load_margin = support_load_preview(model, feet, origin,
            positions, rotations, joints, bounds, load_preview)
        margin = torch.minimum(margin, load_margin)
    error = (model.forward(joints)-local).norm(dim=-1).amax(-1)
    angle = 2*torch.acos((rotations*quaternion[:, None]).sum(-1).abs().clamp(max=1.))
    valid = ((error < .001) & (margin >= .03)
             & ((positions[:, :, 2]-origin[:, None, 2]).abs() <= .08) & (angle <= .35))
    if full_load_reserve:
        # Partial transfers intentionally bypass full unloading in the original
        # planner. They must not masquerade as a reserved tripod pose here.
        valid &= (load_margin >= full_load_reserve)
        valid &= predicted_tripod_margin(feet, origin, positions, rotations, load_preview) >= .025
    if load_preview is not None and 'platform_front_first' in load_preview:
        # Expand the front footholds before requesting forward body/COM travel.
        # Lateral/backward weight transfer and all existing lift gates remain.
        before_front_steps = load_preview['platform_front_first'][:, None]
        com = predicted_support_com(origin, positions, rotations, load_preview)
        forward = ((positions[..., 0] > origin[:, None, 0]+1e-6)
                   | (com[..., 0] > load_preview['com'][:, None, 0]+1e-6))
        valid &= ~(before_front_steps & forward)
    if load_preview is not None and 'four_support_path' in load_preview:
        selected = load_preview['four_support_path']
        if selected.any():
            minimum, residual, recovery = four_support_path_checks(feet[selected], origin[selected],
                quaternion[selected], positions[selected], rotations[selected],
                {k:v[selected] for k,v in load_preview.items()})
            ready = minimum >= 8.
            if 'four_support_recovery' in load_preview:
                ready |= load_preview['four_support_recovery'][selected, None] & recovery
            valid[selected] &= ready & (residual < .1)
    if body_bounds is not None:
        from .climb_body_clearance import support_path_geometry
        gap, path_margin, path_error = support_path_geometry(model, feet, origin, quaternion,
            positions, rotations, bias, bounds, body_bounds, box_bounds)
        valid &= (gap >= .01) & (path_margin >= 0.) & (path_error < .001)
    if link_bounds is not None:
        from .climb_body_clearance import leg_path_gap
        valid &= leg_path_gap(model, feet, origin, quaternion, positions, rotations,
                              link_bounds, box_bounds) >= .005
    if endpoint_leg_reserve:
        valid &= support_endpoint_leg_gap(model, feet, positions, rotations,
                                          link_bounds, box_bounds) >= endpoint_leg_reserve
    if endpoint_body_reserve:
        from .climb_body_clearance import base_box_gap
        valid &= base_box_gap(positions, rotations, body_bounds, box_bounds[:, None]) >= endpoint_body_reserve
    if swing_preview is not None:
        swing_margin, swing_error, swing_gap = swing_path_preview(model, feet, positions,
            rotations, bounds, swing_preview, link_bounds, box_bounds)
        active = swing_preview['active'][:, None]
        swing_ready = swing_preview_ready(swing_margin, swing_error, swing_gap, swing_preview)
        allowed = swing_ready
        enforce_swing = active
        if swing_preview.get('allow_partial_transfer', False):
            allowed, partial = swing_transfer_options(feet, origin, positions, load_preview, swing_ready, rotations)
            enforce_swing = active & (~partial | swing_ready)
        valid &= ~active | allowed
        margin = torch.where(enforce_swing, torch.minimum(margin, swing_margin), margin)
    if independent_height:
        valid[:, primary_count:full_count] &= ~valid[:, :primary_count].any(1)[:, None]
    if link_bounds is not None:
        for begin in (full_count, 2*full_count):
            valid[:, begin:begin+full_count] &= ~valid[:, :begin].any(1)[:, None]
    # Prefer clearance from limits, mildly penalizing unnecessary body motion.
    score = margin-.1*(positions[:, :, 2]-origin[:, None, 2]).abs()-.02*angle
    index = torch.where(valid, score, torch.full_like(score, -1e6)).argmax(1)
    rows = torch.arange(len(feet), device=feet.device)
    feasible = valid.any(1)
    return (torch.where(feasible[:, None], positions[rows, index], origin),
            torch.where(feasible[:, None], rotations[rows, index], quaternion),
            margin[rows, index], feasible)


def platform_support_scope(local_feet, contacts):
    """Require all four planted feet inside the original platform support bounds."""
    return (((local_feet[..., 0] > .79) & (local_feet[..., 0] < 1.91)
             & (local_feet[..., 1].abs() < .56) & (local_feet[..., 2] > .19)
             & contacts).all(1))


class PlatformHoldTracking:
    """Bounded proportional correction for a calm, loaded preextension hold.

    This changes neither the held pose nor the arrival/lift gates. The extra
    feedback ramps over seconds and fades when a normal support transfer starts.
    """
    def __init__(self, count, device, max_extra=.5):
        if not 0. < max_extra <= .75:
            raise ValueError('Platform hold tracking extra gain must be in (0, .75]')
        self.max_extra = max_extra
        self.extra = torch.zeros(count, device=device)
        self.stable = torch.zeros_like(self.extra)
        self.latched = torch.zeros(count, dtype=torch.bool, device=device)

    def reset(self, mask):
        self.extra[mask] = 0.
        self.stable[mask] = 0.
        self.latched[mask] = False

    def update(self, supported_hold, reference_age, position_error, angle_error, dt, minimum_age=10.):
        bounded = supported_hold & (position_error < .02) & (angle_error < .05)
        stalled = bounded & (reference_age >= minimum_age) & ((position_error >= .01) | (angle_error >= .025))
        self.stable[:] = torch.where(stalled, self.stable+dt, 0.)
        self.latched[:] = bounded & (self.latched | (self.stable >= 1.))
        goal = self.latched.to(self.extra.dtype)*self.max_extra
        self.extra[:] += (goal-self.extra).clamp(-.1*dt, .1*dt)
        return self.extra


def platform_level_needed(gravity_z, completed=None, front_first=False):
    """Defer extra leveling until both front steps; retain the original lift tilt gate."""
    needed = gravity_z > -.985
    if front_first:
        needed = torch.where(completed < 2, gravity_z >= -.94, needed)
    return needed


def feasible_hold_level_pose(model, feet, origin, quaternion, bias, bounds,
                             body_bounds, box_bounds, primitives, preview):
    """Small four-foot leveling step; frozen loads and geometry are only preflight."""
    from .climb_body_clearance import support_path_geometry, leg_path_gap
    _, level = support_plane_pose(feet, origin, quaternion, .28)
    angle = 2*torch.acos((level*quaternion).sum(-1).abs().clamp(max=1.))
    fraction = (.025/angle.clamp_min(.025)).clamp(max=1.)
    rotation = torch.lerp(quaternion, level, fraction[:, None])
    rotation /= rotation.norm(dim=-1, keepdim=True)
    positions = origin[:, None].expand(-1, 3, -1).clone()
    positions[..., 2] += origin.new_tensor([0., .0025, .005])[None]
    rotations = rotation[:, None].expand(-1, 3, -1)
    local = rotate_vector(rotations[:, :, None], feet[:, None]-positions[:, :, None], True)
    joints = model.inverse(local)
    nominal = torch.minimum(joints-bounds[:, None, ..., 0], bounds[:, None, ..., 1]-joints).amin((-1,-2))-.01
    command = joints+bias[:, None]
    margin = torch.minimum(nominal, torch.minimum(command-bounds[:, None, ..., 0], bounds[:, None, ..., 1]-command).amin((-1,-2)))
    com = predicted_support_com(origin, positions, rotations, dict(preview, orientation=quaternion))
    count = len(feet)
    loads, residual = balanced_vertical_loads(feet[:, None].expand(-1, 3, -1, -1).reshape(-1,4,3),
        com.reshape(-1,3), preview['weight'][:,None].expand(-1,3).reshape(-1),
        torch.zeros(count*3,device=feet.device,dtype=torch.long),torch.zeros(count*3,device=feet.device))
    loads=loads.reshape(count,3,4)
    up=torch.zeros_like(positions);up[...,2]=1.
    vertical=(model.jacobian(joints)*rotate_vector(rotations,up,True)[...,None,:,None]).sum(-2)
    torque=preview['gravity'][:,None]-vertical*loads[...,None]
    command=joints+torque/30.
    margin=torch.minimum(margin,torch.minimum(command-bounds[:,None,...,0],bounds[:,None,...,1]-command).amin((-1,-2)))
    margin=torch.minimum(margin,((.75*preview['effort'][:,None]-torque.abs())/30.).amin((-1,-2)))
    gap,path_margin,path_error=support_path_geometry(model,feet,origin,quaternion,
        positions,rotations,bias,bounds,body_bounds,box_bounds)
    leg_gap=leg_path_gap(model,feet,origin,quaternion,positions,rotations,primitives,box_bounds)
    error=(model.forward(joints)-local).norm(dim=-1).amax(-1)
    valid=((margin>=.03)&(error<.001)&(gap>=.01)&(path_margin>=0.)&(path_error<.001)
           &(leg_gap>=.005)&(loads.amin(-1)>=8.)
           &(residual.reshape(count,3,3).norm(dim=-1)<.1))
    index=torch.where(valid,margin,torch.full_like(margin,-1e6)).argmax(1)
    rows=torch.arange(count,device=feet.device);feasible=valid.any(1)
    return (torch.where(feasible[:,None],positions[rows,index],origin),
            torch.where(feasible[:,None],rotations[rows,index],quaternion),
            margin[rows,index],feasible)


def feasible_platform_final_step(model, feet, origin, quaternion, bias, bounds,
                                 body_bounds, box_bounds, primitives, preview, goal, rise_limit=None):
    """Default1cm forward/up; optional checked rise up to1.5cm, all feet planted.

    Gravity and limb COM are frozen estimates. Check loads, actuator commands and
    geometry along the entire path; runtime still waits for measured settling.
    """
    from .climb_body_clearance import support_path_geometry, leg_path_gap
    delta = (goal-origin).clamp(min=0., max=.01)
    if rise_limit is not None:
        rise_limit = torch.as_tensor(rise_limit, device=origin.device, dtype=origin.dtype)
        if not torch.isfinite(rise_limit).all() or ((rise_limit < .01) | (rise_limit > .015)).any():
            raise ValueError("Final platform rise limit must be in [.01, .015] meters")
        delta[:, 2] = torch.minimum((goal-origin)[:, 2].clamp(min=0.), rise_limit)
    delta[:, 1] = 0.
    positions = origin[:, None]+delta[:, None]*origin.new_tensor([1., .5, .25])[None, :, None]
    rotations = quaternion[:, None].expand(-1, 3, -1)
    path_preview = dict(preview, orientation=quaternion)
    n = len(feet)
    margin = origin.new_full((n, 3), float('inf'))
    load_min = margin.clone()
    residual_max = torch.zeros_like(margin)
    error_max = torch.zeros_like(margin)
    for fraction in torch.linspace(0., 1., 21, device=origin.device, dtype=origin.dtype):
        pose = torch.lerp(origin[:, None], positions, fraction)
        local = rotate_vector(rotations[:, :, None], feet[:, None]-pose[:, :, None], True)
        joints = model.inverse(local)
        nominal = torch.minimum(joints-bounds[:, None, ..., 0],
                                bounds[:, None, ..., 1]-joints).amin((-1, -2))-.01
        com = predicted_support_com(origin, pose, rotations, path_preview)
        loads, residual = balanced_vertical_loads(
            feet[:, None].expand(-1, 3, -1, -1).reshape(-1, 4, 3), com.reshape(-1, 3),
            preview['weight'][:, None].expand(-1, 3).reshape(-1),
            torch.zeros(n*3, device=origin.device, dtype=torch.long), origin.new_zeros(n*3))
        loads = loads.reshape(n, 3, 4)
        up = torch.zeros_like(pose); up[..., 2] = 1.
        vertical = (model.jacobian(joints)*rotate_vector(rotations, up, True)[..., None, :, None]).sum(-2)
        torque = preview['gravity'][:, None]-vertical*loads[..., None]
        command = joints+torque/30.
        command_margin = torch.minimum(command-bounds[:, None, ..., 0],
                                      bounds[:, None, ..., 1]-command).amin((-1, -2))
        effort_margin = ((.75*preview['effort'][:, None]-torque.abs())/30.).amin((-1, -2))
        margin = torch.minimum(margin, torch.minimum(nominal, torch.minimum(command_margin, effort_margin)))
        load_min = torch.minimum(load_min, loads.amin(-1))
        residual_max = torch.maximum(residual_max, residual.reshape(n, 3, 3).norm(dim=-1))
        error_max = torch.maximum(error_max, (model.forward(joints)-local).norm(dim=-1).amax(-1))
    gap, path_margin, path_error = support_path_geometry(model, feet, origin, quaternion,
        positions, rotations, bias, bounds, body_bounds, box_bounds)
    leg_gap = leg_path_gap(model, feet, origin, quaternion, positions, rotations, primitives, box_bounds)
    valid = ((margin >= .03) & (load_min >= 8.) & (residual_max < .1) & (error_max < .001)
        & (gap >= .01) & (path_margin >= 0.) & (path_error < .001) & (leg_gap >= .005)
        & (delta.norm(dim=1)[:, None] > .002))
    # Largest safe increment; an infeasible segment retains the existing hold.
    index = valid.to(torch.int64).argmax(1)
    rows = torch.arange(n, device=origin.device)
    feasible = valid.any(1)
    return (torch.where(feasible[:, None], positions[rows, index], origin),
            quaternion, margin[rows, index], feasible)


def platform_hold_ready(local_feet, contacts, progress, lifted, landing_ready, stable, settle):
    """Finish the loaded landing before latching a separate platform-hold diagnostic."""
    return (platform_support_scope(local_feet, contacts) & (progress >= 1.)
            & lifted & landing_ready & (stable >= settle))


def expanded_pose_scope(local_feet, contacts, leg, prepared_rear=False):
    """Keep fallback limited to rear ascent after platform support is established."""
    on_top = (local_feet[..., 0] > .79) & (local_feet[..., 2] > .19) & contacts
    scope = on_top.sum(1) == 3
    if prepared_rear:
        scope |= (on_top[:, :2].all(1) & (local_feet[:, 2:, 0].amin(1) >= .68)
                  & (local_feet[:, 2:, 2].amax(1) < .10) & contacts.all(1))
    return scope & (leg >= 2)


def expanded_support_pose(model, feet, origin, quaternion, bias, bounds,
                          body_bounds, box_bounds, link_bounds, load_preview, swing_preview, angle_span=.5):
    """Rear-ascent fallback geometry search; measured support gates still control lift.

    Each environment is independent. Fixed Sobol samples expand XY, roll and pitch
    coverage within the original per-transfer limits; no nominal gate is relaxed.
    """
    from .climb_body_clearance import support_path_geometry, leg_path_gap
    outputs = []
    samples = torch.quasirandom.SobolEngine(5, scramble=True, seed=913).draw(32768).to(origin)
    for row in range(len(feet)):
        take = slice(row, row+1)
        f, o, q, b, limits, box = feet[take], origin[take], quaternion[take], bias[take], bounds[take], box_bounds[take]
        load = {k: v[take] for k, v in load_preview.items()}
        swing = {k: v[take] if torch.is_tensor(v) else v for k, v in swing_preview.items()}
        positions = o[:, None]+(samples[None, :, :3]-.5)*.16
        w, x, y, z = q[0]
        roll = torch.atan2(2*(w*x+y*z), 1-2*(x*x+y*y))+(samples[:, 3]-.5)*angle_span
        pitch = torch.asin((2*(w*y-z*x)).clamp(-1., 1.))+(samples[:, 4]-.5)*angle_span
        yaw = torch.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
        cr, sr, cp, sp, cy, sy = (roll/2).cos(), (roll/2).sin(), (pitch/2).cos(), (pitch/2).sin(), (yaw/2).cos(), (yaw/2).sin()
        rotations = torch.stack((cr*cp*cy+sr*sp*sy, sr*cp*cy-cr*sp*sy,
                                 cr*sp*cy+sr*cp*sy, cr*cp*sy-sr*sp*cy), -1)[None]
        local = rotate_vector(rotations[:, :, None], f[:, None]-positions[:, :, None], True)
        joints = model.inverse(local)
        command = joints+b[:, None]
        margin = torch.minimum(
            torch.minimum(joints-limits[:, None, ..., 0], limits[:, None, ..., 1]-joints).amin((-1, -2))-.01,
            torch.minimum(command-limits[:, None, ..., 0], limits[:, None, ..., 1]-command).amin((-1, -2)))
        margin = torch.minimum(margin, support_load_preview(model, f, o, positions, rotations, joints, limits, load))
        error = (model.forward(joints)-local).norm(dim=-1).amax(-1)
        angle = 2*torch.acos((rotations*q[:, None]).sum(-1).abs().clamp(max=1.))
        support_ids = torch.tensor([[j for j in range(4) if j != i] for i in range(4)], device=f.device)
        triangle = f[:, support_ids[load['leg'][0]], :2]
        predicted_com = predicted_support_com(o,positions,rotations,load)[...,:2]
        tripod = triangle_margin(predicted_com.reshape(-1, 2), triangle.expand(len(samples), -1, -1))[0].amin(1)[None]
        valid = ((margin >= .03) & (error < .001) & (angle <= .35)
                 & ((positions[..., :2]-o[:, None, :2]).norm(dim=-1) <= .08)
                 & ((positions[..., 2]-o[:, None, 2]).abs() <= .08) & (tripod >= .025))
        indices = torch.where(valid[0])[0]
        best_score = -float('inf')
        best = (o[0], q[0], o.new_tensor(0.), torch.tensor(False, device=o.device))
        for begin in range(0, len(indices), 64):
            ids = indices[begin:begin+64]
            p, rotation = positions[:, ids], rotations[:, ids]
            gap, path_margin, path_error = support_path_geometry(model, f, o, q, p, rotation, b, limits, body_bounds, box)
            legs_gap = leg_path_gap(model, f, o, q, p, rotation, link_bounds, box)
            path_valid = (gap >= .01) & (path_margin >= 0.) & (path_error < .001) & (legs_gap >= .005)
            sm, se, sg = swing_path_preview(model, f, p, rotation, limits, swing, link_bounds, box)
            ready = path_valid & (sm >= .03) & (se < .001) & (sg >= .005)
            combined = torch.minimum(margin[:, ids], sm)
            score = combined-.1*(p[..., 2]-o[:, None, 2]).abs()-.02*angle[:, ids]
            score = torch.where(ready, score, torch.full_like(score, -float('inf')))
            index = score[0].argmax()
            if score[0, index].item() > best_score:
                best_score = score[0, index].item()
                best = (p[0, index], rotation[0, index], combined[0, index], ready[0, index])
        outputs.append(best)
    return tuple(torch.stack([v[i] for v in outputs]) for i in range(4))


def rear_swing_inset(start, landing, leg, origins):
    ascending = (leg >= 2) & (landing[:, 2]-start[:, 2] > .1)
    return torch.where(ascending, -.06*torch.sign(start[:, 1]-origins[:, 1]), 0.)



def stage_swing_inset(start, landing, leg, origins, feet, contacts, last_rear_inset=None):
    inset = rear_swing_inset(start, landing, leg, origins)
    if last_rear_inset is not None:
        local = feet-origins[:, None]
        top = (local[..., 0] > .79) & (local[..., 2] > .19) & contacts
        selected_ground = local[torch.arange(len(leg), device=leg.device), leg, 2] < .10
        last = (top.sum(1) == 3) & selected_ground & (leg >= 2) & (landing[:, 2]-start[:, 2] > .1)
        inset = torch.where(last, -last_rear_inset*torch.sign(start[:, 1]-origins[:, 1]), inset)
    return inset


def edge_lift_reference(start, landing, progress, origins, clearance, lateral_inset=None):
    """Move forward while lifting, but clear the20cm face before crossing it."""
    def smooth(value):
        value=value.clamp(0,1)
        return value**3*(10-15*value+6*value**2)
    apex=start.clone()
    apex[:,0]=torch.maximum(start[:,0],torch.minimum(start[:,0]+.10,origins[:,0]+.70))
    apex[:,2]=torch.maximum(start[:,2],landing[:,2])+clearance
    end=landing.clone();end[:,2]=apex[:,2]
    if lateral_inset is not None:
        # Draw the airborne rear foot inward smoothly, then restore landing width.
        apex[:,1] += lateral_inset
        end[:,1] += lateral_inset
    up=torch.lerp(start,apex,smooth(progress/.25)[:,None])
    across=torch.lerp(apex,end,smooth((progress-.25)/.5)[:,None])
    down=torch.lerp(end,landing,smooth((progress-.75)/.25)[:,None])
    return torch.where((progress<.25)[:,None],up,torch.where((progress>.75)[:,None],down,across))


class StageGuidance:
    def __init__(self, action):
        self.a = action
        robot = action._asset
        self.model = LegKinematics.from_usd(robot.cfg.spawn.usd_path, action._env.device)
        names = [robot.joint_names[i] for i in action._joint_ids]
        self.slots = torch.tensor([[names.index(leg+'_'+part+'_joint')
            for part in ('hip', 'thigh', 'calf')] for leg in self.model.legs], device=action._env.device)
        self.support_indices = torch.tensor([[j for j in range(4) if j != i] for i in range(4)], device=action._env.device)
        self.anchors = action.feet_positions().clone()
        self.origin = robot.data.root_pos_w.clone()
        self.target = self.origin.clone()
        self.orientation = robot.data.root_quat_w.clone()
        self.age = torch.zeros_like(action.clock.progress)
        self.margin = self.age.clone()
        self.ik_error = self.age.clone()
        self.limit_excess = self.age.clone()
        self.engaged = torch.zeros_like(action.pending)
        self.stable = self.age.clone()
        self.load_bias = torch.zeros_like(action.reference[:, self.slots])
        self.valid_legs = torch.zeros_like(action.contacts())
        self.support_loads = torch.zeros_like(self.anchors[:, :, 0])
        self.load_residual = torch.zeros_like(self.origin)
        self.load_torque = torch.zeros_like(self.load_bias)
        self.support_vectors = torch.zeros_like(self.anchors)
        self.wrench_residual = torch.zeros((len(self.age), 6), device=action._env.device)
        self.unload_fraction = torch.zeros_like(self.age)
        self.unload_stable = torch.zeros_like(self.age)
        self.landing_contact = LandingContact(len(self.age), action._env.device)
        self.nominal_joints = torch.zeros_like(self.load_bias)
        self.command_limit_excess = torch.zeros_like(self.support_loads)
        self.feedback_unloading = torch.zeros_like(self.age)
        self.target_orientation = self.orientation.clone()
        self.pose_feasible = torch.ones_like(self.engaged)
        self.pose_margin = torch.zeros_like(self.age)
        self.pose_path_gap = torch.zeros_like(self.age)
        self.pose_path_margin = torch.zeros_like(self.age)
        self.pose_requested_target = self.origin.clone()
        self.pose_capture_com = self.origin.clone()
        self.pose_leg_path_gap = torch.zeros_like(self.age)
        self.swing_path_ready = torch.ones_like(self.engaged)
        self.swing_path_margin = torch.zeros_like(self.age)
        self.swing_path_gap = torch.zeros_like(self.age)
        self.load_replan = torch.zeros_like(self.engaged)
        self.expanded_search_origin = self.origin.clone()
        self.expanded_search_quat = self.orientation.clone()
        self.expanded_searches = torch.zeros_like(action.clock.leg)
        self.expanded_pose = torch.zeros_like(self.engaged)
        self.platform_level_segments = torch.zeros_like(action.clock.leg)
        self.platform_final_segments = torch.zeros_like(action.clock.leg)
        self.platform_final_rejections = torch.zeros_like(action.clock.leg)
        self.platform_final_started = torch.zeros_like(self.engaged)
        self.platform_final_goal = self.origin.clone()
        self.platform_final_stable = torch.zeros_like(self.age)
        self.platform_final_retry_age = torch.zeros_like(self.age)
        self.height_refinements = torch.zeros_like(action.clock.leg)
        self.endpoint_reserve_attempts = torch.zeros_like(action.clock.leg)
        self.endpoint_reserve_applied = torch.zeros_like(action.clock.leg)
        self.body_reserve_attempts = torch.zeros_like(action.clock.leg)
        self.body_reserve_applied = torch.zeros_like(action.clock.leg)
        self.platform_load_attempts = torch.zeros_like(action.clock.leg)
        self.platform_load_applied = torch.zeros_like(action.clock.leg)
        self.failed_pose_inputs = {}
        self.platform_pose_inputs = {}
        self.platform_level_inputs = {}
        self.hold_tracking = PlatformHoldTracking(len(action.clock.leg), action._env.device,
            action.cfg.guidance_platform_hold_tracking_max_extra)
        self.platform_final_inputs = {}
        self.platform_preextension_inputs = {}
        self.platform_final_plan_inputs = {}
        self.front_swing_inputs = {}
        self.front_followup_pose_inputs = {}
        self.front_ascent_inputs = {}
        self.front_ascent_attempts = torch.zeros_like(action.clock.leg)
        self.front_ascent_applied = torch.zeros_like(action.clock.leg)
        self.replan_retry_age = torch.zeros_like(self.age)
        self.replan_reference_retained = torch.zeros_like(self.engaged)
        self.replan_rejections = torch.zeros_like(action.clock.leg)
        self.force_trim = UnloadForceTrim(len(action.clock.leg), action._env.device)
        self.com_rotation_active = torch.zeros_like(self.engaged)
        self.link_bounds = None
        if action.cfg.guidance_leg_collision:
            from .climb_body_clearance import leg_collision_bounds, leg_collision_primitives
            loader = leg_collision_primitives if action.cfg.guidance_primitive_collision else leg_collision_bounds
            self.link_bounds = loader(robot.cfg.spawn.usd_path, action._env.device)
            self.link_body_ids = robot.find_bodies([leg+"_"+part for leg in self.model.legs
                for part in ("hip", "thigh", "calf")], preserve_order=True)[0]
        self.body_bounds = None
        if action.cfg.guidance_body_collision:
            from .climb_body_clearance import base_collision_bounds
            self.body_bounds = base_collision_bounds(robot.cfg.spawn.usd_path, action._env.device)
            # Fixed geometry is checked by CrawlJointAction before guidance construction.
            self.box_bounds = torch.tensor([[.75, -.6, 0.], [1.95, .6, .2]],
                device=action._env.device)[None] + action._env.scene.env_origins[:, None]
        if action.cfg.guidance_force_balance:
            stiffness = robot.actuators['base_legs'].stiffness
            if not torch.allclose(stiffness, torch.full_like(stiffness, 30.)):
                raise ValueError('Force balance requires the unchanged leg PD stiffness30')
        self.checked = False

    def reset(self, mask):
        self.hold_tracking.reset(mask)
        self.height_refinements[mask] = 0
        self.endpoint_reserve_attempts[mask] = 0
        self.endpoint_reserve_applied[mask] = 0
        self.body_reserve_attempts[mask] = 0
        self.body_reserve_applied[mask] = 0
        self.platform_load_attempts[mask] = 0
        self.platform_load_applied[mask] = 0
        self.front_ascent_attempts[mask] = 0
        self.front_ascent_applied[mask] = 0
        self.replan_retry_age[mask] = 0.
        self.replan_reference_retained[mask] = False
        self.replan_rejections[mask] = 0
        self.force_trim.reset(mask)
        self.expanded_searches[mask] = 0
        self.platform_level_segments[mask] = 0
        self.platform_final_segments[mask] = 0
        self.platform_final_rejections[mask] = 0
        self.platform_final_started[mask] = False
        self.platform_final_stable[mask] = 0.
        self.platform_final_retry_age[mask] = 0.
        self.platform_final_goal[mask] = self.a._asset.data.root_pos_w[mask]
        self.expanded_pose[mask] = False
        self.com_rotation_active[mask] = False
        self.engaged[mask] = False
        self.stable[mask] = 0.
        self.age[mask] = 0.
        self.load_bias[mask] = 0.
        self.valid_legs[mask] = False
        self.support_loads[mask] = 0.
        self.load_residual[mask] = 0.
        self.load_torque[mask] = 0.
        self.support_vectors[mask] = 0.
        self.wrench_residual[mask] = 0.
        self.unload_fraction[mask] = 0.
        self.unload_stable[mask] = 0.
        self.landing_contact.reset(mask)
        self.nominal_joints[mask] = 0.
        self.command_limit_excess[mask] = 0.
        self.feedback_unloading[mask] = 0.
        self.pose_feasible[mask] = True
        self.pose_margin[mask] = 0.
        self.pose_path_gap[mask] = 0.
        self.pose_path_margin[mask] = 0.
        self.pose_leg_path_gap[mask] = 0.
        self.swing_path_ready[mask] = True
        self.swing_path_margin[mask] = 0.
        self.swing_path_gap[mask] = 0.
        self.load_replan[mask] = False
        if not self.a.cfg.guidance_loaded_start:
            self.capture(mask)

    def capture(self, mask):
        self.replan_retry_age[mask] = 0.
        self.replan_reference_retained[mask] = False
        self.force_trim.reset(mask)
        a = self.a
        feet = a.feet_positions()
        q = a._asset.data.joint_pos[:, a._joint_ids][:, self.slots]
        body_feet = rotate_vector(a._asset.data.root_quat_w[:, None],
            feet-a._asset.data.root_pos_w[:, None], inverse=True)
        if not self.checked:
            error = (self.model.forward(q)-body_feet).norm(dim=-1).max().item()
            if error > 5e-5:
                raise ValueError(f'Guidance geometry disagrees with runtime feet: {error}')
            if self.link_bounds is not None:
                from .climb_body_clearance import leg_link_poses
                positions, _ = leg_link_poses(self.model, q, a._asset.data.root_pos_w,
                                              a._asset.data.root_quat_w)
                actual = a._asset.data.body_pos_w[:, self.link_body_ids].reshape_as(positions)
                if (positions-actual).norm(dim=-1).max().item() > 5e-5:
                    raise ValueError("Leg collision reference frames disagree with runtime links")
            self.checked = True
        triangle = feet.gather(1, self.support_indices[a.clock.leg, :, None].expand(-1,-1,3))[:, :, :2]
        com = a.center_of_mass()[:, :2]
        shift = inset_support_target(com, triangle)-com
        # A large requested transfer is diagnosed, never made instantaneously.
        shift *= (.08 / shift.norm(dim=1).clamp_min(.08))[:, None]
        self.expanded_pose[mask] = False
        self.com_rotation_active[mask] = False
        self.anchors[mask] = feet[mask]
        self.origin[mask] = a._asset.data.root_pos_w[mask]
        self.target[mask] = self.origin[mask]
        self.target[mask, :2] += shift[mask]
        self.target[mask, 2] = feet[mask, :, 2].mean(1) + a.cfg.guidance_body_clearance
        if a.cfg.guidance_mixed_height:
            self.target[mask, 2] = mixed_support_body_height(feet, a.cfg.guidance_body_clearance)[mask]
        self.orientation[mask] = a._asset.data.root_quat_w[mask]
        self.target_orientation[mask] = self.orientation[mask]
        self.pose_feasible[mask] = True
        self.pose_margin[mask] = 0.
        self.pose_path_gap[mask] = 0.
        self.pose_path_margin[mask] = 0.
        self.pose_leg_path_gap[mask] = 0.
        self.swing_path_ready[mask] = True
        self.swing_path_margin[mask] = 0.
        self.swing_path_gap[mask] = 0.
        if a.cfg.guidance_support_plane:
            local = feet-a._env.scene.env_origins[:, None]
            mixed = (((local[:, :2, 0] > .79) & (local[:, :2, 2] > .19)
                      & a.contacts()[:, :2]).all(1) & (local[:, 2:, 2].amin(1) < .10))
            # After the last rear landing, the robot may still be outside the
            # original goal radius. Keep validating its next support transfer;
            # jumping to the nominal height with the old pitch can extend a
            # front knee beyond its soft limit.
            platform = platform_support_scope(local, a.contacts())
            if a.cfg.guidance_platform_pose:
                mixed = mixed | platform
            if a.extension is not None:
                mixed = mixed | (platform & a.extension.moving)
            if a.cfg.guidance_single_front_pose:
                # A single raised front support also needs the complete loaded
                # pose/path preview before unloading the other front foot.
                mixed |= single_front_support_scope(local, a.contacts(), a.clock.leg)
            selected = mask & mixed
            height, orientation = support_plane_pose(feet, self.target,
                self.orientation, a.cfg.guidance_body_clearance, a.cfg.guidance_plane_fraction)
            self.target[selected, 2] = height[selected]
            self.target_orientation[selected] = orientation[selected]
            if a.cfg.guidance_feasible_pose and selected.any():
                bounds = a._asset.data.soft_joint_pos_limits[:, a._joint_ids][:, self.slots]
                bias = a._asset.data.applied_torque[:, a._joint_ids][:, self.slots]/30.
                self.pose_requested_target[selected] = self.target[selected]
                self.pose_capture_com[selected] = a.center_of_mass()[selected]
                followup_step = torch.zeros_like(a.clock.leg[selected], dtype=torch.bool)
                if a.cfg.guidance_front_followup_preview:
                    origins = a._env.scene.env_origins
                    followup_step = front_followup_trim_scope(local[selected], a.contacts()[selected],
                        a.clock.leg[selected], (a.start-origins)[selected], (a.landing-origins)[selected])
                preview = None
                if a.cfg.guidance_load_preview:
                    gravity = a._asset.root_physx_view.get_gravity_compensation_forces()
                    offset = 0 if gravity.shape[1] == a._asset.num_joints else 6
                    ids = torch.tensor(a._joint_ids, device=a._env.device)[self.slots]
                    preview = dict(com=a.center_of_mass()[selected], leg=a.clock.leg[selected],
                        weight=a.mass.sum(1)[selected]*9.81,
                        gravity=gravity[:,ids+offset][selected],
                        effort=a._asset.data.joint_effort_limits[:,ids][selected])
                    if a.cfg.guidance_rotate_com:
                        preview['orientation']=self.orientation[selected]
                        preview['rotation_active']=last_rear_com_scope(local[selected],a.contacts()[selected],
                            a.clock.leg[selected],a.start[selected],a.landing[selected])
                        if a.extension is not None:
                            preview['rotation_active'] |= a.extension.moving[selected]
                        if a.cfg.guidance_front_followup_preview:
                            preview['rotation_active'] |= followup_step
                        self.com_rotation_active[selected]=preview['rotation_active']
                    if a.cfg.guidance_platform_support_path and a.extension is not None:
                        preview['four_support_path'] = platform[selected] & a.extension.moving[selected]
                        if a.cfg.guidance_platform_support_recovery:
                            preview['four_support_recovery'] = preview['four_support_path'].clone()
                    if a.cfg.guidance_front_followup_preview:
                        preview['four_support_path'] = (preview.get('four_support_path',
                            torch.zeros_like(followup_step)) | followup_step)
                    if a.cfg.platform_front_first and a.extension is not None:
                        preview['platform_front_first'] = (platform[selected]
                            & a.extension.moving[selected] & (a.extension.completed[selected] < 2))
                    if a.cfg.front_raise_height is not None:
                        active=self.front_raise_active()[selected]
                        preview['front_raise_current']=front_support_height(self.model,feet[selected],
                            self.origin[selected,None],self.orientation[selected,None])[:,0]
                        preview['front_raise_target']=torch.where(active,
                            torch.full_like(preview['front_raise_current'],a.cfg.front_raise_height),
                            torch.full_like(preview['front_raise_current'],-1.))
                swing_preview = None
                if a.cfg.guidance_swing_preview:
                    rear_ascent = (a.clock.leg[selected] >= 2) & (a.landing[selected, 2]-a.start[selected, 2] > .1)
                    platform_step = (platform_support_scope(local[selected], a.contacts()[selected])
                        if a.cfg.guidance_platform_swing else torch.zeros_like(rear_ascent))
                    if a.extension is not None:
                        platform_step |= platform[selected] & a.extension.moving[selected]
                    if (rear_ascent | platform_step | followup_step).any():
                        swing_preview = dict(start=a.start[selected], landing=a.landing[selected],
                            origins=a._env.scene.env_origins[selected], leg=a.clock.leg[selected],
                            gravity=preview['gravity'], clearance=a.cfg.foot_clearance, active=rear_ascent | platform_step | followup_step,
                            allow_partial_transfer=a.cfg.guidance_swing_transfer,
                            inset=a.swing_inset[selected])
                        if (platform_step | followup_step).any():
                            swing_preview.update(landing_probe_depth=.015*(platform_step | followup_step),
                                landing_com=preview['com'], landing_origin=self.origin[selected],
                                landing_weight=preview['weight'], landing_effort=preview['effort'])
                        if followup_step.any():
                            # A10mm nominal reserve accounts for observed loaded
                            # sag; original body/support path guards still apply.
                            # Partial four-foot transfer never authorizes lift.
                            swing_preview.update(minimum_gap=torch.where(followup_step,
                                torch.full_like(a.swing_inset[selected], .010),
                                torch.full_like(a.swing_inset[selected], .005)),
                                landing_orientation=self.orientation[selected],
                                landing_rotation_active=followup_step)
                pose, rotation, margin, feasible = feasible_support_pose(self.model,
                    feet[selected], self.target[selected], self.origin[selected],
                    self.orientation[selected], bias[selected], bounds[selected],
                    a.cfg.guidance_body_clearance, self.body_bounds,
                    self.box_bounds[selected] if self.body_bounds is not None else None,
                    a.cfg.guidance_independent_height, self.link_bounds, preview, swing_preview)
                if a.cfg.guidance_last_pose_search and swing_preview is not None:
                    scope = expanded_pose_scope(local, a.contacts(), a.clock.leg,
                                                a.cfg.guidance_edge_pose_search)
                    changed = ((self.origin-self.expanded_search_origin).norm(dim=-1) > .01)
                    turned = 2*torch.acos((self.orientation*self.expanded_search_quat).sum(-1).abs().clamp(max=1.)) > .05
                    eligible = (~feasible & swing_preview['active'] & scope[selected]
                                & ((self.expanded_searches[selected] == 0) | changed[selected] | turned[selected]))
                    if eligible.any():
                        ids = torch.where(selected)[0][eligible]
                        self.expanded_searches[ids] += 1
                        self.expanded_search_origin[ids] = self.origin[ids]
                        self.expanded_search_quat[ids] = self.orientation[ids]
                        extra = expanded_support_pose(self.model, feet[ids], self.origin[ids],
                            self.orientation[ids], bias[ids], bounds[ids], self.body_bounds,
                            self.box_bounds[ids], self.link_bounds,
                            {k: v[eligible] for k, v in preview.items()},
                            {k: v[eligible] if torch.is_tensor(v) else v for k, v in swing_preview.items()})
                        if a.cfg.guidance_pose_angle_coverage and not extra[3].all():
                            # Preserve every original feasible choice. Broaden sampling,
                            # while retaining the original.35rad total-rotation gate.
                            missing = ~extra[3]
                            retry_ids = ids[missing]
                            chosen_rows = torch.where(eligible)[0][missing]
                            wider = expanded_support_pose(self.model, feet[retry_ids], self.origin[retry_ids],
                                self.orientation[retry_ids], bias[retry_ids], bounds[retry_ids], self.body_bounds,
                                self.box_bounds[retry_ids], self.link_bounds,
                                {k: v[chosen_rows] for k, v in preview.items()},
                                {k: v[chosen_rows] if torch.is_tensor(v) else v for k, v in swing_preview.items()},
                                angle_span=.6)
                            for destination, value in zip(extra, wider):
                                destination[missing] = value
                        pose[eligible], rotation[eligible], margin[eligible], feasible[eligible] = extra
                        self.expanded_pose[ids] = extra[3]
                if a.cfg.guidance_refine_height and (~feasible).any():
                    from .climb_body_clearance import base_box_gap, leg_path_gap
                    initial_body = base_box_gap(self.origin[selected], self.orientation[selected],
                        self.body_bounds, self.box_bounds[selected])
                    initial_leg = leg_path_gap(self.model, feet[selected], self.origin[selected],
                        self.orientation[selected], self.origin[selected, None],
                        self.orientation[selected, None], self.link_bounds, self.box_bounds[selected])[:, 0]
                    # Every path includes its initial state. Denser heights cannot
                    # repair a pre-existing clearance deficit; never relax it.
                    retry = ~feasible & (initial_body >= .01) & (initial_leg >= .005)
                    if retry.any():
                        ids = torch.where(selected)[0][retry]
                        self.height_refinements[ids] += 1
                        refined = feasible_support_pose(self.model, feet[ids], self.target[ids],
                            self.origin[ids], self.orientation[ids], bias[ids], bounds[ids],
                            a.cfg.guidance_body_clearance, self.body_bounds, self.box_bounds[ids],
                            a.cfg.guidance_independent_height, self.link_bounds,
                            {k:v[retry] for k,v in preview.items()},
                            None if swing_preview is None else {k:v[retry] if torch.is_tensor(v) else v
                                for k,v in swing_preview.items()}, height_samples=65)
                        pose[retry], rotation[retry], margin[retry], feasible[retry] = refined
                if a.cfg.guidance_endpoint_leg_reserve and feasible.any():
                    # A narrow nominal endpoint can lose its remaining clearance
                    # under load. Prefer a larger endpoint reserve before rear
                    # ground-foot transfer; leave the original5mm path guard intact.
                    endpoint_gap = support_endpoint_leg_gap(self.model, feet[selected],
                        pose[:, None], rotation[:, None], self.link_bounds, self.box_bounds[selected])[:, 0]
                    rear_ground = ((a.clock.leg[selected] >= 2)
                        & (local[selected][torch.arange(len(pose), device=pose.device), a.clock.leg[selected], 2] < .10)
                        & a.contacts()[selected].all(1))
                    retry = feasible & rear_ground & (endpoint_gap < .010)
                    if retry.any():
                        ids = torch.where(selected)[0][retry]
                        self.endpoint_reserve_attempts[ids] += 1
                        reserved = feasible_support_pose(self.model, feet[ids], self.target[ids],
                            self.origin[ids], self.orientation[ids], bias[ids], bounds[ids],
                            a.cfg.guidance_body_clearance, self.body_bounds, self.box_bounds[ids],
                            a.cfg.guidance_independent_height, self.link_bounds,
                            {k:v[retry] for k,v in preview.items()},
                            None if swing_preview is None else {k:v[retry] if torch.is_tensor(v) else v
                                for k,v in swing_preview.items()}, height_samples=65, endpoint_leg_reserve=.010)
                        accepted = reserved[3]
                        rows = torch.where(retry)[0][accepted]
                        pose[rows], rotation[rows], margin[rows] = (x[accepted] for x in reserved[:3])
                        self.endpoint_reserve_applied[ids[accepted]] += 1
                        # If the stricter preference has no solution, keep the
                        # already feasible original choice and its original gates.
                if a.cfg.guidance_endpoint_body_reserve and feasible.any():
                    from .climb_body_clearance import base_box_gap
                    endpoint_gap = base_box_gap(pose, rotation, self.body_bounds, self.box_bounds[selected])
                    rear_ground = ((a.clock.leg[selected] >= 2)
                        & (local[selected][torch.arange(len(pose), device=pose.device), a.clock.leg[selected], 2] < .10)
                        & a.contacts()[selected].all(1))
                    retry = feasible & rear_ground & (endpoint_gap < .015)
                    if retry.any():
                        ids = torch.where(selected)[0][retry]
                        self.body_reserve_attempts[ids] += 1
                        reserved = feasible_support_pose(self.model, feet[ids], self.target[ids],
                            self.origin[ids], self.orientation[ids], bias[ids], bounds[ids],
                            a.cfg.guidance_body_clearance, self.body_bounds, self.box_bounds[ids],
                            a.cfg.guidance_independent_height, self.link_bounds,
                            {k:v[retry] for k,v in preview.items()},
                            None if swing_preview is None else {k:v[retry] if torch.is_tensor(v) else v
                                for k,v in swing_preview.items()}, height_samples=65,
                            endpoint_leg_reserve=.010 if a.cfg.guidance_endpoint_leg_reserve else 0.,
                            endpoint_body_reserve=.015)
                        accepted = reserved[3]
                        rows = torch.where(retry)[0][accepted]
                        pose[rows], rotation[rows], margin[rows] = (x[accepted] for x in reserved[:3])
                        self.body_reserve_applied[ids[accepted]] += 1
                if a.cfg.guidance_platform_load_reserve and a.extension is not None and feasible.any():
                    local_pose = rotate_vector(rotation[:, None], feet[selected]-pose[:, None], inverse=True)
                    load_margin = support_load_preview(self.model, feet[selected], self.origin[selected],
                        pose[:, None], rotation[:, None], self.model.inverse(local_pose)[:, None],
                        bounds[selected], preview)[:, 0]
                    retry = (feasible & platform[selected] & a.extension.moving[selected]
                             & (load_margin < .08))
                    if retry.any():
                        ids = torch.where(selected)[0][retry]
                        self.platform_load_attempts[ids] += 1
                        reserved = feasible_support_pose(self.model, feet[ids], self.target[ids],
                            self.origin[ids], self.orientation[ids], bias[ids], bounds[ids],
                            a.cfg.guidance_body_clearance, self.body_bounds, self.box_bounds[ids],
                            a.cfg.guidance_independent_height, self.link_bounds,
                            {k:v[retry] for k,v in preview.items()},
                            None if swing_preview is None else {k:v[retry] if torch.is_tensor(v) else v
                                for k,v in swing_preview.items()}, height_samples=65, full_load_reserve=.08)
                        accepted = reserved[3]
                        rows = torch.where(retry)[0][accepted]
                        pose[rows], rotation[rows], margin[rows] = (x[accepted] for x in reserved[:3])
                        self.platform_load_applied[ids[accepted]] += 1
                if swing_preview is not None:
                    sm, se, sg = swing_path_preview(self.model, feet[selected], pose[:, None],
                        rotation[:, None], bounds[selected], swing_preview, self.link_bounds, self.box_bounds[selected])
                    self.swing_path_ready[selected] = (~swing_preview['active'] | (
                        feasible & swing_preview_ready(sm, se, sg, swing_preview)[:, 0]))
                    self.swing_path_margin[selected] = sm[:, 0]
                    self.swing_path_gap[selected] = sg[:, 0]
                if self.body_bounds is not None:
                    from .climb_body_clearance import support_path_geometry
                    gap, path_margin, _ = support_path_geometry(self.model, feet[selected],
                        self.origin[selected], self.orientation[selected], pose[:, None],
                        rotation[:, None], bias[selected], bounds[selected], self.body_bounds,
                        self.box_bounds[selected])
                    self.pose_path_gap[selected] = gap[:, 0]
                    self.pose_path_margin[selected] = path_margin[:, 0]
                if self.link_bounds is not None:
                    from .climb_body_clearance import leg_path_gap
                    self.pose_leg_path_gap[selected] = leg_path_gap(self.model, feet[selected],
                        self.origin[selected], self.orientation[selected], pose[:, None],
                        rotation[:, None], self.link_bounds, self.box_bounds[selected])[:, 0]
                if a.cfg.guidance_pose_fixtures:
                    # Read-only first-failure inputs for reproducing the search.
                    # Keep world coordinates and a batch dimension exactly as used.
                    ids = torch.where(selected)[0]
                    def pose_input(row):
                        env_id = int(ids[row])
                        def item(value):
                            return value[row:row+1].detach().cpu().tolist() if torch.is_tensor(value) else value
                        return dict(
                            env_id=env_id, elapsed_s=float(a._env.episode_length_buf[env_id]*a._env.step_dt),
                            leg=int(a.clock.leg[env_id]),
                            feet=item(feet[selected]), target=item(self.target[selected]),
                            origin=item(self.origin[selected]), quaternion=item(self.orientation[selected]),
                            bias=item(bias[selected]), bounds=item(bounds[selected]),
                            box_bounds=item(self.box_bounds[selected]),
                            clearance=a.cfg.guidance_body_clearance,
                            independent_height=a.cfg.guidance_independent_height,
                            load={key:item(value) for key,value in preview.items()} if preview is not None else None,
                            swing={key:item(value) for key,value in swing_preview.items()} if swing_preview is not None else None,
                            result=dict(position=item(pose), quaternion=item(rotation), margin=item(margin), feasible=bool(feasible[row])),
                            expanded_searches=int(self.expanded_searches[env_id]))
                    for row in torch.where(~feasible)[0].tolist():
                        env_id = int(ids[row])
                        if env_id not in self.failed_pose_inputs:
                            self.failed_pose_inputs[env_id] = pose_input(row)
                    # Exact mixed-height front followup inputs before unloading.
                    # Diagnostic only: preserve the planner's original load/bias,
                    # and record the swing that this capture currently omits.
                    followup = front_followup_trim_scope(local[selected], a.contacts()[selected],
                        a.clock.leg[selected], (a.start-a._env.scene.env_origins)[selected],
                        (a.landing-a._env.scene.env_origins)[selected])
                    for row in torch.where(followup)[0].tolist():
                        env_id = int(ids[row])
                        records = self.front_followup_pose_inputs.setdefault(env_id, [])
                        if len(records) < 16:
                            record = pose_input(row)
                            def followup_item(value):
                                return value[env_id:env_id+1].detach().cpu().tolist()
                            record['swing_request'] = dict(start=followup_item(a.start),
                                landing=followup_item(a.landing), origins=followup_item(a._env.scene.env_origins),
                                leg=followup_item(a.clock.leg), clearance=a.cfg.foot_clearance,
                                inset=followup_item(a.swing_inset), active=[True], allow_partial_transfer=False)
                            record['contacts'] = followup_item(a.contacts())
                            record['reference_bias'] = followup_item(a.reference[:, self.slots]-q)
                            record['measured_foot_force_z'] = followup_item(
                                a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2])
                            records.append(record)
                    if a.extension is not None:
                        # Include accepted plans before platform steps, so a
                        # later loaded failure can be replayed without guessing
                        # its original gravity/COM inputs. Diagnostic reads only.
                        for row in torch.where(a.extension.moving[selected] & platform[selected])[0].tolist():
                            env_id = int(ids[row])
                            records = self.platform_pose_inputs.setdefault(env_id, [])
                            if len(records) < 64:
                                record = pose_input(row)
                                record['extension_completed'] = int(a.extension.completed[env_id])
                                records.append(record)
                self.target[selected] = pose
                self.target_orientation[selected] = rotation
                self.pose_margin[selected] = margin
                self.pose_feasible[selected] = feasible
        if a.cfg.guidance_front_ascent_pose:
            self.reserve_front_ascent_pose(mask)
        self.load_replan[mask] = False
        self.age[mask] = 0.
        self.unload_stable[mask] = 0.
        self.landing_contact.reset(mask)
        self.feedback_unloading[mask] = 0.
        self.engaged[mask] = True
        if a.cfg.guidance_loaded_start:
            self.load_bias[mask] = (a.reference[:, self.slots]-q)[mask]

    def reserve_front_ascent_pose(self, mask):
        """Adjust only a normal planted capture; never recapture a lifted foot."""
        a = self.a
        robot = a._asset
        feet = a.feet_positions()
        local = feet-a._env.scene.env_origins[:, None]
        selected = (mask & single_front_support_scope(local, a.contacts(), a.clock.leg)
                    & (a.clock.progress == 0) & self.pose_feasible
                    & (a.landing[:, 2]-a.start[:, 2] > .1))
        if not selected.any():
            return
        slots = torch.tensor(a._joint_ids, device=a._env.device)[self.slots]
        gravity = robot.root_physx_view.get_gravity_compensation_forces()
        offset = 0 if gravity.shape[1] == robot.num_joints else 6
        bounds = robot.data.soft_joint_pos_limits[:, slots][selected]
        bias = robot.data.applied_torque[:, slots][selected]/30.
        load = dict(com=a.center_of_mass()[selected], leg=a.clock.leg[selected],
            weight=a.mass.sum(1)[selected]*9.81, gravity=gravity[:, slots+offset][selected],
            effort=robot.data.joint_effort_limits[:, slots][selected],
            orientation=self.orientation[selected], rotation_active=torch.ones_like(a.clock.leg[selected], dtype=torch.bool))
        swing = dict(start=a.start[selected], landing=a.landing[selected],
            origins=a._env.scene.env_origins[selected], leg=a.clock.leg[selected],
            gravity=load['gravity'], clearance=a.cfg.foot_clearance,
            inset=a.swing_inset[selected], active=torch.ones_like(load['leg'], dtype=torch.bool),
            allow_partial_transfer=False, landing_probe_depth=torch.full_like(load['weight'], .015),
            landing_com=load['com'], landing_origin=self.origin[selected],
            landing_weight=load['weight'], landing_effort=load['effort'])
        pose, rotation, margin, retry, accepted = front_ascent_pose(self.model,
            feet[selected], self.target[selected], self.target_orientation[selected],
            self.origin[selected], self.orientation[selected], bias, bounds,
            a.cfg.guidance_body_clearance, self.body_bounds, self.box_bounds[selected],
            self.link_bounds, load, swing)
        ids = torch.where(selected)[0]
        self.front_ascent_attempts[ids[retry]] += 1
        self.front_ascent_applied[ids[accepted]] += 1
        if a.cfg.guidance_pose_fixtures:
            for row, env_id in enumerate(ids.tolist()):
                if env_id in self.front_ascent_inputs:
                    continue
                def item(value):
                    return value[row:row+1].detach().cpu().tolist() if torch.is_tensor(value) else value
                self.front_ascent_inputs[env_id] = dict(
                    env_id=env_id, elapsed_s=float(a._env.episode_length_buf[env_id]*a._env.step_dt),
                    leg=int(a.clock.leg[env_id]), feet=item(feet[selected]),
                    target=item(self.target[selected]), target_quaternion=item(self.target_orientation[selected]),
                    origin=item(self.origin[selected]), quaternion=item(self.orientation[selected]),
                    bias=item(bias), bounds=item(bounds), box_bounds=item(self.box_bounds[selected]),
                    clearance=a.cfg.guidance_body_clearance,
                    contacts=item(a.contacts()[selected]),
                    load={k:item(v) for k,v in load.items()}, swing={k:item(v) for k,v in swing.items()},
                    result=dict(position=item(pose), quaternion=item(rotation), margin=item(margin),
                        attempted=bool(retry[row]), accepted=bool(accepted[row])))
        changed = ids[accepted]
        if accepted.any():
            from .climb_body_clearance import support_path_geometry, leg_path_gap
            sm, se, sg = swing_path_preview(self.model, feet[changed], pose[accepted, None],
                rotation[accepted, None], bounds[accepted],
                {k:v[accepted] if torch.is_tensor(v) else v for k,v in swing.items()},
                self.link_bounds, self.box_bounds[changed])
            gap, pm, _ = support_path_geometry(self.model, feet[changed], self.origin[changed],
                self.orientation[changed], pose[accepted, None], rotation[accepted, None],
                bias[accepted], bounds[accepted], self.body_bounds, self.box_bounds[changed])
            self.pose_path_gap[changed], self.pose_path_margin[changed] = gap[:, 0], pm[:, 0]
            self.pose_leg_path_gap[changed] = leg_path_gap(self.model, feet[changed],
                self.origin[changed], self.orientation[changed], pose[accepted, None],
                rotation[accepted, None], self.link_bounds, self.box_bounds[changed])[:, 0]
            self.swing_path_margin[changed], self.swing_path_gap[changed] = sm[:, 0], sg[:, 0]
            self.swing_path_ready[changed] = (sm[:, 0] >= .03) & (se[:, 0] < .001) & (sg[:, 0] >= .005)
            self.pose_requested_target[changed] = self.target[changed]
            self.pose_capture_com[changed] = load['com'][accepted]
            self.com_rotation_active[changed] = True
        self.target[changed] = pose[accepted]
        self.target_orientation[changed] = rotation[accepted]
        self.pose_margin[changed] = margin[accepted]
        # The enclosing capture already blends from the measured pose and old
        # joint reference, and resets unloading while all four feet contact.
        # Leave every existing measured unload/landing/limit gate in authority.

    def replan_preserving_reference(self, mask):
        """Reject infeasible recapture without moving an already valid support reference.

        Called only for calm four-contact replans at phase zero and zero unload.
        Keep failed planning diagnostics, so lifting remains blocked; retry timing
        is independent of the restored reference interpolation age.
        """
        stable_reference = self.valid_legs.all(1) & (self.command_limit_excess.amax(1) < 1e-6)
        names = ('anchors', 'origin', 'target', 'orientation', 'target_orientation', 'load_bias', 'age')
        saved = {name: getattr(self, name)[mask].clone() for name in names}
        self.capture(mask)
        rejected = ~self.pose_feasible[mask] & stable_reference[mask]
        ids = torch.where(mask)[0][rejected]
        for name, value in saved.items():
            getattr(self, name)[ids] = value[rejected]
        self.replan_reference_retained[ids] = True
        self.replan_rejections[ids] += 1

    def capture_hold(self, mask):
        """Hold measured landed anchors continuously, without another support shift."""
        a = self.a
        self.replan_reference_retained[mask] = False
        if hasattr(self, "force_trim"):
            self.force_trim.reset(mask)
        self.anchors[mask] = a.feet_positions()[mask]
        self.origin[mask] = a._asset.data.root_pos_w[mask]
        self.target[mask] = self.origin[mask]
        self.orientation[mask] = a._asset.data.root_quat_w[mask]
        self.target_orientation[mask] = self.orientation[mask]
        q = a._asset.data.joint_pos[:, a._joint_ids][:, self.slots]
        self.load_bias[mask] = (a.reference[:, self.slots]-q)[mask]
        self.age[mask] = 0.
        self.feedback_unloading[mask] = 0.
        self.load_replan[mask] = False
        self.pose_requested_target[mask] = self.target[mask]
        self.pose_capture_com[mask] = a.center_of_mass()[mask]

    def record_platform_final_inputs(self, before_extension=False):
        """Read-only loaded states after both front steps, for final-pose planning."""
        a = self.a
        if a.extension is None:
            return
        robot = a._asset
        records_by_env = self.platform_preextension_inputs if before_extension else self.platform_final_inputs
        stage = (a.extension.completed < 2) if before_extension else (a.extension.completed == 2)
        ready = (a.platform_hold & stage & ~a.extension.moving
            & (self.age >= 3.) & a.contacts().all(1) & self.valid_legs.all(1)
            & (robot.data.root_lin_vel_w.norm(dim=1) < .025)
            & (robot.data.root_ang_vel_w.norm(dim=1) < .1)
            & (self.command_limit_excess.amax(1) < 1e-6))
        ids = []
        for env_id in torch.where(ready)[0].tolist():
            count = len(records_by_env.get(env_id, []))
            if count < 3 and float(self.age[env_id]) >= (3., 10., 20.)[count]:
                ids.append(env_id)
        if not ids:
            return
        slots = torch.tensor(a._joint_ids, device=a._env.device)[self.slots]
        gravity = robot.root_physx_view.get_gravity_compensation_forces()
        offset = 0 if gravity.shape[1] == robot.num_joints else 6
        feet = a.feet_positions()
        com = a.center_of_mass()
        q = robot.data.joint_pos[:, slots]
        bias = a.reference[:, self.slots]-q
        forces = a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
        for env_id in ids:
            def item(value):
                return value[env_id:env_id+1].detach().cpu().tolist()
            records = records_by_env.setdefault(env_id, [])
            records.append(dict(env_id=env_id,
                elapsed_s=float(a._env.episode_length_buf[env_id]*a._env.step_dt),
                reference_age_s=float(self.age[env_id]),
                extension_completed=int(a.extension.completed[env_id]),
                feet=item(feet), origin=item(robot.data.root_pos_w),
                quaternion=item(robot.data.root_quat_w), bias=item(bias),
                bounds=item(robot.data.soft_joint_pos_limits[:, slots]),
                box_bounds=item(self.box_bounds), env_origin=item(a._env.scene.env_origins),
                contacts=item(a.contacts()), measured_foot_force_z=item(forces),
                joint_position=item(q), reference=item(a.reference[:, self.slots]),
                command_limit_excess=item(self.command_limit_excess),
                previous_target=item(self.target), previous_quaternion=item(self.target_orientation),
                linear_velocity=item(robot.data.root_lin_vel_w), angular_velocity=item(robot.data.root_ang_vel_w),
                preview=dict(com=item(com), weight=item(a.mass.sum(1)*9.81),
                    gravity=item(gravity[:, slots+offset]), effort=item(robot.data.joint_effort_limits[:, slots]))))
            if before_extension:
                records[-1].update(level_segments=int(self.platform_level_segments[env_id]),
                    position_error_m=float((self.target[env_id]-robot.data.root_pos_w[env_id]).norm()),
                    orientation_error_rad=float(2*torch.acos((self.target_orientation[env_id]*robot.data.root_quat_w[env_id]).sum().abs().clamp(max=1.))),
                    projected_gravity=item(robot.data.projected_gravity_b))

    def update_platform_hold_tracking(self):
        a = self.a; robot = a._asset.data
        minimum_age = 3. if a.cfg.guidance_platform_settled_recovery else 10.
        feet = a.feet_positions()-a._env.scene.env_origins[:, None]
        forces = a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
        supported = (a.platform_hold & ~a.extension.moving & (a.extension.completed < 2)
            & platform_support_scope(feet, a.contacts()) & (forces >= 8.).all(1)
            & self.pose_feasible & self.valid_legs.all(1)
            & (self.command_limit_excess.amax(1) < 1e-6)
            & (robot.root_lin_vel_w.norm(dim=1) < .025)
            & (robot.root_ang_vel_w.norm(dim=1) < .1))
        if a.cfg.guidance_platform_extension_tracking:
            chosen = torch.nn.functional.one_hot(a.clock.leg, 4).bool()
            # Correct a small loaded pose residual before the unchanged arrival
            # and measured-unload gates. Keep the feedback through unload dwell.
            transferring = self.platform_extension_trim_scope(feet, a.contacts(), .02, .05,
                minimum_age=minimum_age)
            supported |= (transferring & (a.clock.progress == 0) & self.engaged
                & a.contacts().all(1) & ((forces > 8.) | chosen).all(1)
                & ((forces[a.rows, a.clock.leg] > 5.) | self.hold_tracking.latched)
                & (self.margin >= .025) & (self.unload_fraction >= .999)
                & self.pose_feasible & self.swing_path_ready & self.valid_legs.all(1)
                & (self.command_limit_excess.amax(1) < 1e-6) & ~self.load_replan
                & (robot.projected_gravity_b[:, 2] < -.94)
                & (robot.root_lin_vel_w.norm(dim=1) < .025)
                & (robot.root_ang_vel_w.norm(dim=1) < .1))
        if a.cfg.guidance_platform_settled_recovery:
            # The loaded residual can also block final adjustment after both
            # front steps. This supplies feedback, never a new phase release.
            supported |= (a.platform_hold & ~a.extension.moving & (a.extension.completed == 2)
                & platform_support_scope(feet, a.contacts()) & (forces >= 8.).all(1)
                & self.pose_feasible & self.valid_legs.all(1)
                & (self.command_limit_excess.amax(1) < 1e-6)
                & (robot.root_lin_vel_w.norm(dim=1) < .025)
                & (robot.root_ang_vel_w.norm(dim=1) < .1))
            settled = ((robot.root_lin_vel_w.norm(dim=1) < .001)
                & (robot.root_ang_vel_w.norm(dim=1) < .01))
            supported &= self.hold_tracking.latched | settled
        position_error = (self.target-robot.root_pos_w).norm(dim=1)
        angle_error = 2*torch.acos((self.target_orientation*robot.root_quat_w).sum(-1).abs().clamp(max=1.))
        return self.hold_tracking.update(supported, self.age, position_error, angle_error, a._env.step_dt,
            minimum_age=minimum_age)

    def level_hold(self):
        a=self.a;robot=a._asset
        settled=((self.target-robot.data.root_pos_w).norm(dim=1)<.01)
        turn_error=2*torch.acos((self.target_orientation*robot.data.root_quat_w).sum(-1).abs().clamp(max=1.))
        ready=(a.platform_hold & (self.age>=2.) & settled & (turn_error<.025)
            & a.contacts().all(1) & self.valid_legs.all(1)
            & (robot.data.root_lin_vel_w.norm(dim=1)<.025)
            & (robot.data.root_ang_vel_w.norm(dim=1)<.1)
            & platform_level_needed(robot.data.projected_gravity_b[:,2],
                None if a.extension is None else a.extension.completed, a.cfg.platform_front_first))
        if not ready.any():
            return
        ids=torch.tensor(a._joint_ids,device=a._env.device)[self.slots]
        gravity=robot.root_physx_view.get_gravity_compensation_forces()
        offset=0 if gravity.shape[1]==robot.num_joints else 6
        q=robot.data.joint_pos[:,a._joint_ids][:,self.slots]
        bias=a.reference[:,self.slots]-q
        preview=dict(com=a.center_of_mass()[ready],weight=a.mass.sum(1)[ready]*9.81,
            gravity=gravity[:,ids+offset][ready],effort=robot.data.joint_effort_limits[:,ids][ready])
        pose,rotation,margin,valid=feasible_hold_level_pose(self.model,a.feet_positions()[ready],
            robot.data.root_pos_w[ready],robot.data.root_quat_w[ready],bias[ready],
            robot.data.soft_joint_pos_limits[:,a._joint_ids][:,self.slots][ready],
            self.body_bounds,self.box_bounds[ready],self.link_bounds,preview)
        if a.cfg.guidance_pose_fixtures:
            self.record_platform_level_inputs(ready, bias, preview, pose, rotation, margin, valid)
        self.pose_feasible[ready]=valid;self.pose_margin[ready]=margin
        accepted=torch.zeros_like(ready);accepted[ready]=valid
        if accepted.any():
            self.capture_hold(accepted)
            self.target[accepted]=pose[valid]
            self.target_orientation[accepted]=rotation[valid]
            self.platform_level_segments[accepted]+=1

    def adjust_platform_final_pose(self):
        a = self.a; robot = a._asset
        self.platform_final_retry_age += a._env.step_dt
        forces = a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
        turn_error = 2*torch.acos((self.target_orientation*robot.data.root_quat_w).sum(-1).abs().clamp(max=1.))
        ready = (a.platform_hold & (a.extension.completed == 2) & ~a.extension.moving
            & (self.age >= 2.) & a.contacts().all(1) & (forces >= 8.).all(1)
            & self.valid_legs.all(1) & (self.command_limit_excess.amax(1) < 1e-6)
            & ((self.target-robot.data.root_pos_w).norm(dim=1) < .01) & (turn_error < .025)
            & (robot.data.projected_gravity_b[:, 2] < -.985)
            & (robot.data.root_lin_vel_w.norm(dim=1) < .025)
            & (robot.data.root_ang_vel_w.norm(dim=1) < .1))
        self.platform_final_stable[:] = torch.where(ready, self.platform_final_stable+a._env.step_dt, 0.)
        attempt = ready & (self.platform_final_stable >= .5) & (self.platform_final_retry_age >= 1.5)
        if not attempt.any():
            return
        feet = a.feet_positions()
        first = attempt & ~self.platform_final_started
        self.platform_final_goal[first] = robot.data.root_pos_w[first]
        self.platform_final_goal[first, 0] += .04
        self.platform_final_goal[first, 2] = torch.maximum(robot.data.root_pos_w[first, 2],
            feet[first, :, 2].mean(1)+a.cfg.guidance_body_clearance)
        self.platform_final_started[first] = True
        remaining = (self.platform_final_goal-robot.data.root_pos_w).clamp(min=0.)
        remaining[:, 1] = 0.
        attempt &= remaining.norm(dim=1) > .002
        # Once the fixed goal is commanded, retain its anchors and interpolation
        # age. Loaded tracking error is not a new segment: recapturing the same
        # goal repeatedly rebases the feet and can slowly move the held stance.
        reference_remaining = (self.platform_final_goal-self.target).clamp(min=0.)
        reference_remaining[:, 1] = 0.
        attempt &= (self.platform_final_segments == 0) | (reference_remaining.norm(dim=1) > 1e-6)
        if not attempt.any():
            return
        slots = torch.tensor(a._joint_ids, device=a._env.device)[self.slots]
        gravity = robot.root_physx_view.get_gravity_compensation_forces()
        offset = 0 if gravity.shape[1] == robot.num_joints else 6
        bias = a.reference[:, self.slots]-robot.data.joint_pos[:, slots]
        preview = dict(com=a.center_of_mass()[attempt], weight=a.mass.sum(1)[attempt]*9.81,
            gravity=gravity[:, slots+offset][attempt], effort=robot.data.joint_effort_limits[:, slots][attempt])
        planner_options = {}
        if a.cfg.guidance_platform_final_recovery_rise:
            # Only a final hold already requiring residual recovery uses the
            # taller checked segment; forward advance stays capped at1cm.
            planner_options["rise_limit"] = torch.where(self.hold_tracking.latched[attempt], .015, .01)
        pose, rotation, margin, valid = feasible_platform_final_step(self.model, feet[attempt],
            robot.data.root_pos_w[attempt], robot.data.root_quat_w[attempt], bias[attempt],
            robot.data.soft_joint_pos_limits[:, slots][attempt], self.body_bounds,
            self.box_bounds[attempt], self.link_bounds, preview, self.platform_final_goal[attempt], **planner_options)
        if a.cfg.guidance_pose_fixtures:
            self.record_platform_level_inputs(attempt, bias, preview, pose, rotation, margin, valid, final=True)
        self.platform_final_retry_age[attempt] = 0.
        ids = torch.where(attempt)[0]
        self.platform_final_rejections[ids[~valid]] += 1
        accepted = torch.zeros_like(attempt); accepted[ids[valid]] = True
        if accepted.any():
            self.capture_hold(accepted)
            self.target[accepted] = pose[valid]
            self.target_orientation[accepted] = rotation[valid]
            self.platform_final_segments[accepted] += 1
            self.platform_final_stable[accepted] = 0.

    def record_platform_level_inputs(self, mask, bias, preview, pose, rotation, margin, valid, final=False):
        """Read-only exact inputs before a four-foot leveling segment is adopted."""
        a=self.a;robot=a._asset
        for row, env_id in enumerate(torch.where(mask)[0].tolist()):
            records=(self.platform_final_plan_inputs if final else self.platform_level_inputs).setdefault(env_id, [])
            if len(records)>=64:
                continue
            def item(value):
                return value[row:row+1].detach().cpu().tolist()
            records.append(dict(env_id=env_id,
                elapsed_s=float(a._env.episode_length_buf[env_id]*a._env.step_dt),
                segment=int((self.platform_final_segments if final else self.platform_level_segments)[env_id]),
                feet=item(a.feet_positions()[mask]), origin=item(robot.data.root_pos_w[mask]),
                quaternion=item(robot.data.root_quat_w[mask]), bias=item(bias[mask]),
                bounds=item(robot.data.soft_joint_pos_limits[:,a._joint_ids][:,self.slots][mask]),
                box_bounds=item(self.box_bounds[mask]),
                contacts=item(a.contacts()[mask]),
                measured_foot_force_z=item(a._env.scene['contact_forces'].data.net_forces_w[:,a.sensor_ids,2][mask]),
                previous_target=item(self.target[mask]), previous_quaternion=item(self.target_orientation[mask]),
                preview={k:item(v) for k,v in preview.items()},
                result=dict(position=item(pose),quaternion=item(rotation),margin=item(margin),valid=bool(valid[row]))))
            if final:
                records[-1]['goal'] = item(self.platform_final_goal[mask])

    def front_raise_active(self):
        a=self.a
        local=a.feet_positions()-a._env.scene.env_origins[:,None]
        front_top=((local[:,:2,0]>.79)&(local[:,:2,2]>.19)&a.contacts()[:,:2]).all(1)
        return front_top & (a.clock.leg>=2) & (a.landing[:,2]-a.start[:,2]>.1)

    def front_raise_measured_height(self):
        a=self.a
        return front_support_height(self.model,a.feet_positions(),
            a._asset.data.root_pos_w[:,None],a._asset.data.root_quat_w[:,None])[:,0]

    def front_raise_ready(self):
        a=self.a
        if a.cfg.front_raise_height is None:
            return torch.ones_like(self.engaged)
        return ~self.front_raise_active() | (self.front_raise_measured_height()>=a.cfg.front_raise_height)

    def support_ready(self):
        a = self.a
        feet = a.feet_positions()
        triangle = feet.gather(1, self.support_indices[a.clock.leg, :, None].expand(-1,-1,3))[:, :, :2]
        self.margin[:] = triangle_margin(a.center_of_mass()[:, :2], triangle)[0].amin(1)
        if a.cfg.guidance_preunload:
            forces = a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
            ready = (self.engaged & (self.age >= 3.) & unloaded_support_ready(
                forces, a.clock.leg, self.margin, a._asset.data.root_lin_vel_w,
                a._asset.data.root_ang_vel_w))
            if a.cfg.guidance_load_preview:
                ready &= tripod_support_clearance(feet, a.clock.leg, a._asset.data.root_pos_w[:, None])[:, 0] >= .18
            if a.cfg.guidance_feasible_pose:
                ready &= self.pose_feasible
            if a.cfg.guidance_swing_preview:
                ready &= self.swing_path_ready
            ready &= self.front_raise_ready()
            self.unload_stable[:] = torch.where(ready, self.unload_stable+a._env.step_dt, 0.)
            if a.cfg.guidance_pose_fixtures:
                self.record_front_swing_inputs(self.unload_stable >= .2)
            return self.unload_stable >= .2
        return self.engaged & (self.age >= 1.5) & (self.margin >= .015)

    def record_front_swing_inputs(self, ready):
        """Read-only inputs before initial ascent and mixed-height front followup.

        Record actual pose and the existing reference separately at release;
        neither is changed by this collector.
        One episode per environment is required by the diagnostic evaluator.
        """
        a = self.a
        origins = a._env.scene.env_origins
        followup = front_followup_trim_scope(a.feet_positions()-origins[:, None],
            a.contacts(), a.clock.leg, a.start-origins, a.landing-origins)
        ascent = ((a.start[:, 2]-origins[:, 2] < .1)
            & (a.landing[:, 2]-a.start[:, 2] > .1))
        mask = (ready & ~a.pending & (a.clock.progress == 0) & (a.clock.leg < 2)
                & (ascent | followup))
        def record_key(i):
            return f'{i}:{int(a.clock.leg[i])}' + (':followup' if bool(followup[i]) else '')
        ids = [i for i in torch.where(mask)[0].tolist()
               if record_key(i) not in self.front_swing_inputs]
        if not ids:
            return
        robot = a._asset
        slots = torch.tensor(a._joint_ids, device=a._env.device)[self.slots]
        gravity = robot.root_physx_view.get_gravity_compensation_forces()
        offset = 0 if gravity.shape[1] == robot.num_joints else 6
        feet = a.feet_positions()
        com = a.center_of_mass()
        for env_id in ids:
            def item(value):
                return value[env_id:env_id+1].detach().cpu().tolist() if torch.is_tensor(value) else value
            leg = int(a.clock.leg[env_id])
            self.front_swing_inputs[record_key(env_id)] = dict(
                env_id=env_id, leg=leg,
                elapsed_s=float(a._env.episode_length_buf[env_id]*a._env.step_dt),
                feet=item(feet), origin=item(robot.data.root_pos_w),
                quaternion=item(robot.data.root_quat_w),
                target=item(self.target), target_quaternion=item(self.target_orientation),
                reference_origin=item(self.origin), reference_quaternion=item(self.orientation),
                reference_anchors=item(self.anchors), reference_age=item(self.age),
                bias=item(robot.data.applied_torque[:, a._joint_ids][:, self.slots]/30.),
                bounds=item(robot.data.soft_joint_pos_limits[:, a._joint_ids][:, self.slots]),
                box_bounds=item(self.box_bounds), clearance=a.cfg.guidance_body_clearance,
                load=dict(com=item(com), leg=item(a.clock.leg), weight=item(a.mass.sum(1)*9.81),
                    gravity=item(gravity[:, slots+offset]),
                    effort=item(robot.data.joint_effort_limits[:, slots])),
                swing=dict(start=item(a.start), landing=item(a.landing),
                    origins=item(a._env.scene.env_origins), leg=item(a.clock.leg),
                    gravity=item(gravity[:, slots+offset]), clearance=a.cfg.foot_clearance,
                    inset=item(a.swing_inset), active=[True], allow_partial_transfer=False),
                contacts=item(a.contacts()), support_margin=item(self.margin),
                unload_fraction=item(self.feedback_unloading))

    def landing_ready(self):
        a = self.a
        selected = torch.nn.functional.one_hot(a.clock.leg, 4).bool()
        supported = (a.contacts() | selected).all(1)
        forces = a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
        force = forces[a.rows, a.clock.leg]
        feet = a.feet_positions()[a.rows, a.clock.leg]
        near = ((feet[:, :2]-a.landing[:, :2]).norm(dim=1) < .03) & ((feet[:, 2]-a.landing[:, 2]).abs() < .02)
        touch = (force > 2.) & near
        calm = (a._asset.data.root_lin_vel_w.norm(dim=1) < .05) & (a._asset.data.root_ang_vel_w.norm(dim=1) < .2)
        return self.landing_contact.update(self.engaged & (a.clock.progress >= 1.),
            touch, supported, force, calm, a._env.step_dt)

    def balanced_load_bias(self):
        a = self.a
        robot = a._asset
        u = (a.clock.progress / .25).clamp(0, 1)
        if a.cfg.guidance_preunload:
            # Complete weight transfer at the original foot position, before lift.
            u = ((self.age-1.5)/1.5).clamp(0, 1)
        u = u**3 * (10 - 15*u + 6*u*u)
        if a.cfg.guidance_support_feedback:
            chosen = torch.nn.functional.one_hot(a.clock.leg, 4).bool()
            contacts = a.contacts()
            calm = ((robot.data.root_lin_vel_w.norm(dim=1) < .05)
                    & (robot.data.root_ang_vel_w.norm(dim=1) < .2))
            prepared = (self.engaged & (self.age >= 1.5) & (self.margin >= .025)
                        & (contacts | chosen).all(1) & calm & self.valid_legs.all(1)
                        & (self.command_limit_excess.amax(1) < 1e-6))
            if a.cfg.guidance_load_preview:
                blocked = (~self.valid_legs.all(1) | (self.command_limit_excess.amax(1) > 1e-6))
                self.load_replan |= self.engaged & (a.clock.progress == 0) & (self.feedback_unloading > 0) & blocked
                prepared &= ~self.load_replan
                prepared &= tripod_support_clearance(a.feet_positions(), a.clock.leg, robot.data.root_pos_w[:, None])[:, 0] >= .18
            if a.cfg.guidance_feasible_pose:
                prepared &= self.pose_feasible
            if a.cfg.guidance_swing_preview:
                prepared &= self.swing_path_ready
            prepared &= self.front_raise_ready()
            self.feedback_unloading[:] = feedback_unload(self.feedback_unloading, prepared,
                (contacts & chosen).any(1), a.clock.progress > 0, a._env.step_dt)
            u = self.feedback_unloading
        if a.cfg.guidance_landing_contact:
            u = u*(1.-self.landing_contact.reload)
        if a.cfg.guidance_platform_hold:
            u = torch.where(a.platform_hold, 0., u)
        self.unload_fraction[:] = u
        self.support_loads[:], self.load_residual[:] = balanced_vertical_loads(
            a.feet_positions(), a.center_of_mass(), a.mass.sum(1)*9.81, a.clock.leg, u)
        if a.cfg.guidance_horizontal_balance:
            fraction = (self.age/1.5).clamp(0, 1)
            velocity = (self.target-self.origin)[:, :2]*(30*fraction.square()*(1-fraction).square()/1.5)[:, None]
            acceleration = 4.*(velocity-robot.data.root_lin_vel_w[:, :2])
            acceleration *= (.4/acceleration.norm(dim=1).clamp_min(.4))[:, None]
            self.support_vectors[:], self.wrench_residual[:] = balanced_acceleration_loads(
                a.feet_positions(), a.center_of_mass(), a.mass.sum(1)*9.81, a.clock.leg, u, acceleration)
            self.support_loads[:] = self.support_vectors[:, :, 2]
        if a.cfg.guidance_front_force_trim:
            forces = a._env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
            chosen = torch.nn.functional.one_hot(a.clock.leg, 4).bool()
            local = a.feet_positions()-a._env.scene.env_origins[:, None]
            foot = local[a.rows, a.clock.leg]
            trim_scope = ((a.clock.leg < 2) & (foot[:, 0] < .75) & (foot[:, 2] < .10)
                & (a.landing[:, 2]-a.start[:, 2] > .10))
            if a.cfg.guidance_front_followup_force_trim:
                origins = a._env.scene.env_origins
                trim_scope |= front_followup_trim_scope(local, a.contacts(), a.clock.leg,
                    a.start-origins, a.landing-origins) & ~a.platform_hold
            if a.cfg.guidance_platform_extension_force_trim:
                platform_trim = self.platform_extension_trim_scope(local, a.contacts(),
                    minimum_age=3. if a.cfg.guidance_platform_settled_recovery else 10.)
                if a.cfg.guidance_platform_settled_recovery:
                    settled = ((robot.data.root_lin_vel_w.norm(dim=1) < .001)
                        & (robot.data.root_ang_vel_w.norm(dim=1) < .01))
                    platform_trim &= (self.force_trim.force_n > 0.) | settled
                trim_scope |= platform_trim
            eligible = (self.engaged & (self.age >= 3.) & (u >= .999)
                & trim_scope
                & (self.margin >= .025) & ((forces > 8.) | chosen).all(1)
                & (robot.data.root_lin_vel_w.norm(dim=1) < .025)
                & (robot.data.root_ang_vel_w.norm(dim=1) < .1)
                & self.pose_feasible & self.swing_path_ready & self.valid_legs.all(1)
                & (self.command_limit_excess.amax(1) < 1e-6) & ~self.load_replan)
            trim_options = {}
            if a.cfg.guidance_front_stall_trim:
                trim_options["max_force"] = front_stall_trim_limit(local, a.clock.leg,
                    a.start, a.landing, self.force_trim.stall_age, self.force_trim.force_n)
            self.force_trim.update(forces[a.rows, a.clock.leg], eligible, a.clock.progress, a._env.step_dt,
                **trim_options)
        jacobians = robot.root_physx_view.get_jacobians()
        gravity = robot.root_physx_view.get_gravity_compensation_forces()
        offset = 0 if robot.is_fixed_base else 6
        for leg, slots in enumerate(self.slots.tolist()):
            ids = [a._joint_ids[slot] for slot in slots]
            body = a.feet_ids[leg] - (1 if robot.is_fixed_base else 0)
            jacobian = jacobians[:, body, :3][:, :, [i+offset for i in ids]]
            gravity_ids = ids if gravity.shape[1] == robot.num_joints else [i+offset for i in ids]
            if a.cfg.guidance_horizontal_balance:
                contact_torque = (jacobian.transpose(1, 2) @ self.support_vectors[:, leg, :, None]).squeeze(-1)
            else:
                contact_torque = jacobian[:, 2]*self.support_loads[:, leg, None]
            torque = gravity[:, gravity_ids] - contact_torque
            if a.cfg.guidance_front_force_trim:
                # Positive J_z^T force supplies upward virtual work. It is an
                # explicit small force-feedback correction, not a negative
                # support load or a replacement for measured contact checks.
                trim = self.force_trim.applied_n*(a.clock.leg == leg)
                torque = torque+jacobian[:, 2]*trim[:, None]
            cap = .75*robot.data.joint_effort_limits[:, ids]
            self.load_torque[:, leg] = torch.maximum(torch.minimum(torque, cap), -cap)
        blend = (self.age / 1.5).clamp(0, 1)
        blend = blend**3*(10 - 15*blend + 6*blend*blend)
        return torch.lerp(self.load_bias, self.load_torque/30., blend[:, None, None])

    def platform_extension_trim_scope(self, local_feet, contacts, position_tolerance=.01, angle_tolerance=.025, minimum_age=10.):
        """Only a settled, stalled front extension after all feet reached the box.

        The caller retains measured support, load, speed, command and swing gates.
        This scope cannot release a foot or authorize the final body adjustment.
        """
        a = self.a; robot = a._asset.data
        selected = torch.nn.functional.one_hot(a.clock.leg, 4).bool()
        start = a.start-a._env.scene.env_origins
        landing = a.landing-a._env.scene.env_origins
        angle = 2*torch.acos((self.target_orientation*robot.root_quat_w).sum(-1).abs().clamp(max=1.))
        return (a.extension.moving & (a.extension.completed < 2) & ~a.platform_hold
            & (a.clock.leg < 2) & (self.age >= minimum_age)
            & platform_support_scope(local_feet, contacts | selected)
            & (local_feet[..., 2] < .26).all(1)
            & (start[:, 0] > .79) & (start[:, 2] > .19)
            & (landing[:, 0]-start[:, 0] > .02)
            & (landing[:, 0]-start[:, 0] <= .080001)
            & ((landing[:, 2]-start[:, 2]).abs() < .02)
            & ((self.target-robot.root_pos_w).norm(dim=1) < position_tolerance) & (angle < angle_tolerance))

    def requested(self, actor_request):
        a = self.a
        if a.cfg.guidance_retain_infeasible_reference:
            self.replan_retry_age += a._env.step_dt
        if a.cfg.guidance_loaded_start:
            ready = (a.contacts().all(1) & (a._asset.data.root_lin_vel_w.norm(dim=1) < .025)
                     & (a._asset.data.root_ang_vel_w.norm(dim=1) < .1)
                     & (a._asset.data.projected_gravity_b[:,2] < -.98)
                     & (a._env.episode_length_buf*a._env.step_dt >= .5))
            self.stable[:] = torch.where(ready & ~self.engaged, self.stable+a._env.step_dt, 0.)
            capture = ~self.engaged & (self.stable >= .25)
            if capture.any():
                self.capture(capture)
        if a.cfg.guidance_platform_level:
            if a.cfg.guidance_pose_fixtures:
                self.record_platform_final_inputs()
                self.record_platform_final_inputs(before_extension=True)
            self.level_hold()
        if a.cfg.platform_final_adjust:
            self.adjust_platform_final_pose()
        if a.cfg.guidance_support_feedback:
            # The8cm bound is per smooth transfer, not a permanent COM destination.
            # Continue with another bounded segment while all feet still support.
            settled = ((self.target[:, :2]-a._asset.data.root_pos_w[:, :2]).norm(dim=1) < .01)
            calm = ((a._asset.data.root_lin_vel_w.norm(dim=1) < .025)
                    & (a._asset.data.root_ang_vel_w.norm(dim=1) < .1))
            needs_pose = (self.margin < .025) | ~self.front_raise_ready()
            if a.cfg.guidance_feasible_pose:
                needs_pose = needs_pose | ~self.valid_legs.all(1) | ~self.pose_feasible
            if a.cfg.guidance_swing_preview:
                needs_pose |= ~self.swing_path_ready
            if a.cfg.guidance_load_preview:
                needs_pose |= self.load_replan
                # XY support and a clear swing alone cannot release the last
                # ground foot while the remaining support plane is too high.
                needs_pose |= tripod_support_clearance(a.feet_positions(), a.clock.leg,
                    a._asset.data.root_pos_w[:, None])[:, 0] < .18
            replan = (self.engaged & (self.age >= 1.5) & (a.clock.progress == 0)
                      & needs_pose & settled & calm & a.contacts().all(1)
                      & (self.feedback_unloading == 0))
            if a.cfg.guidance_platform_hold:
                replan &= ~a.platform_hold
            if a.cfg.guidance_retain_infeasible_reference:
                replan &= ~self.replan_reference_retained | (self.replan_retry_age >= 1.5)
            if replan.any():
                if a.cfg.guidance_retain_infeasible_reference:
                    self.replan_preserving_reference(replan)
                else:
                    self.capture(replan)
        self.age += a._env.step_dt*self.engaged
        t = (self.age/1.5).clamp(0,1)
        t = t**3*(10-15*t+6*t*t)
        body = self.origin+t[:,None]*(self.target-self.origin)
        orientation = self.orientation
        if a.cfg.guidance_support_plane:
            orientation = torch.lerp(self.orientation, self.target_orientation, t[:, None])
            orientation = orientation/ orientation.norm(dim=1, keepdim=True).clamp_min(1e-8)
        desired = rotate_vector(orientation[:,None], self.anchors-body[:,None], inverse=True)
        # Loaded position control does not realize the nominal body pose exactly.
        # Correct support-leg geometry using measured root pose and velocity;
        # cap the Cartesian correction before IK and the existing joint limiter.
        actual = rotate_vector(a._asset.data.root_quat_w[:,None],
            self.anchors-a._asset.data.root_pos_w[:,None], inverse=True)
        velocity = a._asset.data.root_lin_vel_b[:,None] + torch.cross(
            a._asset.data.root_ang_vel_b[:,None].expand_as(desired), desired, dim=-1)
        correction = a.cfg.guidance_body_gain*(desired-actual)+a.cfg.guidance_body_damping*velocity
        if a.cfg.guidance_platform_hold_tracking:
            extra = self.update_platform_hold_tracking()
            correction += extra[:, None, None]*(desired-actual)
        correction *= (.05/correction.norm(dim=-1).clamp_min(.05))[...,None]
        desired += correction
        # The swinging foot tracks its world reference using the measured base;
        # supporting feet use the continuous nominal body shift above.
        swing = a.clock.progress > 0
        if a.cfg.guidance_platform_hold:
            swing &= ~a.platform_hold
        measured_target = rotate_vector(a._asset.data.root_quat_w,
            a.foot_reference-a._asset.data.root_pos_w, inverse=True)
        desired[a.rows[swing], a.clock.leg[swing]] = measured_target[swing]
        q = self.model.inverse(desired)
        self.nominal_joints[:] = q
        self.ik_error[:] = (self.model.forward(q)-desired).norm(dim=-1).amax(1)
        bounds = a._asset.data.soft_joint_pos_limits[:, a._joint_ids][:, self.slots]
        limit_error = torch.maximum(bounds[...,0]+.01-q, q-bounds[...,1]+.01).clamp_min(0).amax(2)
        self.limit_excess[:] = limit_error.amax(1)
        self.valid_legs[:] = ((self.model.forward(q)-desired).norm(dim=-1) < .001) & (limit_error < 1e-6)
        valid = self.valid_legs.all(1)
        request = actor_request.clone()
        nominal = a.reference[:, self.slots].clone()
        residual = a.cfg.guidance_residual_scale*(actor_request-a.stage_offset)[:,self.slots]
        if a.cfg.guidance_loaded_start:
            # A rejected swing goal must not freeze the other supporting legs.
            bias = self.balanced_load_bias() if a.cfg.guidance_force_balance else self.load_bias
            # Allocation already unloads the swing foot; retain its own gravity compensation.
            progress = torch.zeros_like(a.clock.progress) if a.cfg.guidance_force_balance else a.clock.progress
            if a.cfg.guidance_mixed_height:
                combined = q+bias+residual
                self.command_limit_excess[:] = torch.maximum(
                    bounds[..., 0]-combined, combined-bounds[..., 1]).clamp_min(0).amax(2)
            nominal, valid_legs = loaded_leg_reference(nominal,q,bias,residual,bounds,
                self.valid_legs,self.engaged,a.clock.leg,progress)
            self.valid_legs[:] = valid_legs
            request[:,self.slots] = nominal
            request[~self.engaged] = a.stage_offset[~self.engaged]
        else:
            nominal[valid] = q[valid]
            request[:, self.slots] = nominal + torch.where(valid[:,None,None], residual, 0.)
        return request
