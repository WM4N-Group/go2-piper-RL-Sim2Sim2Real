import torch
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import rotate_vector, support_load_preview, predicted_support_com, triangle_margin, swing_path_preview, four_support_path_loads
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import edge_lift_reference, balanced_vertical_loads

def selected_swing_path_preview(model, feet, positions, rotations, bounds, preview, primitives, box_bounds):
    """Sample the planned swing before unloading; frozen pose/gravity estimate."""
    from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_body_clearance import leg_link_poses, primitive_box_gap
    n, count = positions.shape[:2]
    phase = torch.linspace(0.0, 1.0, 41, device=feet.device, dtype=feet.dtype)
    reference = edge_lift_reference(preview['start'][:, None].expand(-1, 41, -1).reshape(-1, 3), preview['landing'][:, None].expand(-1, 41, -1).reshape(-1, 3), phase.repeat(n), preview['origins'][:, None].expand(-1, 41, -1).reshape(-1, 3), preview['clearance'], preview['inset'][:, None].expand(-1, 41).reshape(-1)).reshape(n, 41, 3)
    if 'landing_probe_depth' in preview:
        probe = preview['landing'][:, None].expand(-1, 5, -1).clone()
        probe[..., 2] -= preview['landing_probe_depth'][:, None] * torch.linspace(0.2, 1.0, 5, device=feet.device, dtype=feet.dtype)[None]
        reference = torch.cat((reference, probe), 1)
    world = feet[:, None, None].expand(-1, count, reference.shape[1], -1, -1).clone()
    chosen = torch.nn.functional.one_hot(preview['leg'], 4).bool()
    world = torch.where(chosen[:, None, None, :, None], reference[:, None, :, None], world)
    local = rotate_vector(rotations[:, :, None, None], world - positions[:, :, None, None], True)
    joints = model.inverse(local)
    command = joints + preview['gravity'][:, None, None] / 30.0
    nominal = torch.minimum(joints - bounds[:, None, None, :, :, 0], bounds[:, None, None, :, :, 1] - joints).amin(-1) - 0.01
    loaded = torch.minimum(command - bounds[:, None, None, :, :, 0], bounds[:, None, None, :, :, 1] - command).amin(-1)
    margin = torch.where(chosen[:, None, None], torch.minimum(nominal, loaded), torch.full_like(nominal, 1000000.0)).amin((-1, -2))
    error = (model.forward(joints) - local).norm(dim=-1).amax((-1, -2))
    links, turns = leg_link_poses(model, joints, positions[:, :, None], rotations[:, :, None])
    primitive_gap = primitive_box_gap(links, turns, primitives, box_bounds[:, None, None, None, None])
    gap = torch.where(chosen[:, None, None, :, None], primitive_gap, torch.full_like(primitive_gap, float('inf'))).amin((-1, -2, -3))
    if 'landing_com' in preview:
        final_feet = world[:, :, 40]
        com = preview['landing_com'][:, None] + positions - preview['landing_origin'][:, None]
        if 'landing_orientation' in preview:
            com = predicted_support_com(preview['landing_origin'], positions, rotations, dict(com=preview['landing_com'], orientation=preview['landing_orientation'], rotation_active=preview['landing_rotation_active']))
        leg = preview['leg'][:, None].expand(-1, count).reshape(-1)
        loads, _ = balanced_vertical_loads(final_feet.reshape(-1, 4, 3), com.reshape(-1, 3), preview['landing_weight'][:, None].expand(-1, count).reshape(-1), leg, torch.zeros_like(leg, dtype=feet.dtype))
        up = torch.zeros_like(positions)
        up[..., 2] = 1.0
        vertical = (model.jacobian(joints[:, :, 40]) * rotate_vector(rotations, up, True)[..., None, :, None]).sum(-2)
        torque = preview['gravity'][:, None] - vertical * loads.reshape(n, count, 4, 1)
        cap = 0.75 * preview['landing_effort'][:, None]
        command = joints[:, :, 40] + torque / 30.0
        reload_margin = torch.minimum(command - bounds[:, None, ..., 0], bounds[:, None, ..., 1] - command).amin((-1, -2))
        reload_margin = torch.minimum(reload_margin, ((cap - torque.abs()) / 30.0).amin((-1, -2)))
        margin = torch.minimum(margin, torch.where(preview['landing_probe_depth'][:, None] > 0, reload_margin, torch.full_like(reload_margin, 1000000.0)))
    return (margin, error, gap)

def expanded_front_landing_reserve(model, feet, origin, quaternion, bias, bounds, body_bounds, box_bounds, link_bounds, load_preview, swing_preview, angle_span=0.5):
    """Smallest checked preparation after the original front search fails.

    Existing path/load/swing gates are unchanged. Actual lift and reload still
    require the original measured gates. This helper never changes foot targets.
    """
    from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_body_clearance import support_path_geometry, leg_path_gap
    outputs = []
    samples = torch.quasirandom.SobolEngine(5, scramble=True, seed=913).draw(32768).to(origin)
    for row in range(len(feet)):
        take = slice(row, row + 1)
        f, o, q, b, limits, box = (feet[take], origin[take], quaternion[take], bias[take], bounds[take], box_bounds[take])
        load = {k: v[take] for k, v in load_preview.items()}
        load['orientation'] = q
        load['rotation_active'] = torch.ones(1, dtype=torch.bool, device=o.device)
        swing = {k: v[take] if torch.is_tensor(v) else v for k, v in swing_preview.items()}
        swing['landing_orientation'] = q
        swing['landing_rotation_active'] = load['rotation_active']
        positions = o[:, None] + (samples[None, :, :3] - 0.5) * 0.16
        w, x, y, z = q[0]
        roll = torch.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)) + (samples[:, 3] - 0.5) * angle_span
        pitch = torch.asin((2 * (w * y - z * x)).clamp(-1.0, 1.0)) + (samples[:, 4] - 0.5) * angle_span
        yaw = torch.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        cr, sr, cp, sp, cy, sy = ((roll / 2).cos(), (roll / 2).sin(), (pitch / 2).cos(), (pitch / 2).sin(), (yaw / 2).cos(), (yaw / 2).sin())
        rotations = torch.stack((cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy), -1)[None]
        local = rotate_vector(rotations[:, :, None], f[:, None] - positions[:, :, None], True)
        joints = model.inverse(local)
        command = joints + b[:, None]
        margin = torch.minimum(torch.minimum(joints - limits[:, None, ..., 0], limits[:, None, ..., 1] - joints).amin((-1, -2)) - 0.01, torch.minimum(command - limits[:, None, ..., 0], limits[:, None, ..., 1] - command).amin((-1, -2)))
        margin = torch.minimum(margin, support_load_preview(model, f, o, positions, rotations, joints, limits, load))
        error = (model.forward(joints) - local).norm(dim=-1).amax(-1)
        angle = 2 * torch.acos((rotations * q[:, None]).sum(-1).abs().clamp(max=1.0))
        support_ids = torch.tensor([[j for j in range(4) if j != i] for i in range(4)], device=f.device)
        triangle = f[:, support_ids[load['leg'][0]], :2]
        predicted_com = predicted_support_com(o, positions, rotations, load)[..., :2]
        tripod = triangle_margin(predicted_com.reshape(-1, 2), triangle.expand(len(samples), -1, -1))[0].amin(1)[None]
        valid = (margin >= 0.03) & (error < 0.001) & (angle <= 0.35) & ((positions[..., :2] - o[:, None, :2]).norm(dim=-1) <= 0.08) & ((positions[..., 2] - o[:, None, 2]).abs() <= 0.08) & (tripod >= 0.025)
        indices = torch.where(valid[0])[0]
        best_score = -float('inf')
        best = (o[0], q[0], o.new_tensor(0.0), torch.tensor(False, device=o.device))
        for begin in range(0, len(indices), 64):
            ids = indices[begin:begin + 64]
            p, rotation = (positions[:, ids], rotations[:, ids])
            gap, path_margin, path_error = support_path_geometry(model, f, o, q, p, rotation, b, limits, body_bounds, box)
            legs_gap = leg_path_gap(model, f, o, q, p, rotation, link_bounds, box)
            path_valid = (gap >= 0.01) & (path_margin >= 0.0) & (path_error < 0.001) & (legs_gap >= 0.005)
            sm, se, sg = swing_path_preview(model, f, p, rotation, limits, swing, link_bounds, box)
            _, _, selected_gap = selected_swing_path_preview(model, f, p, rotation, limits, swing, link_bounds, box)
            minimum, residual = four_support_path_loads(f, o, q, p, rotation, load)
            ready = path_valid & (sm >= 0.03) & (se < 0.001) & (sg >= 0.005) & (selected_gap >= 0.012)
            ready &= (minimum >= 8.0) & (residual < 0.1)
            combined = torch.minimum(margin[:, ids], sm)
            score = -(p - o[:, None]).norm(dim=-1) - 0.05 * angle[:, ids] + 0.01 * combined
            score = torch.where(ready, score, torch.full_like(score, -float('inf')))
            index = score[0].argmax()
            if score[0, index].item() > best_score:
                best_score = score[0, index].item()
                best = (p[0, index], rotation[0, index], combined[0, index], ready[0, index])
        outputs.append(best)
    return tuple((torch.stack([v[i] for v in outputs]) for i in range(4)))
