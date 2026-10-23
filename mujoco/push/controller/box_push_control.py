"""Contact-aware locomotion commands for physical pushing."""

import torch


def latch_goal_pose(eligible, active, stored_position, stored_quaternion, position, quaternion, *, release_axis=None, release_distance=0.0):
    """Hold the measured world pose on entry; release if the goal condition ends."""
    if not 0.0 <= release_distance <= 0.02 or (release_distance and release_axis is None):
        raise ValueError("Goal contact release requires distance in [0, .02] and a forward axis")
    target_position = position if release_distance == 0.0 else position - release_distance * release_axis
    entering = eligible & ~active
    return (
        eligible.clone(),
        torch.where(entering[:, None], target_position, stored_position),
        torch.where(entering[:, None], quaternion, stored_quaternion),
    )


def latch_leg_contact(ready, safe_approach_complete, valid_contact):
    """Latch real legal contact only after safe approach; callers reset per episode."""
    return safe_approach_complete & (ready | valid_contact)


def pose_task_scale(reference, *, orientation_weight, height_weight=1.0):
    """Scale world-frame pose residuals; height weighting does not change limits."""
    if not 0.0 < orientation_weight <= 1.0 or not 1.0 <= height_weight <= 3.0:
        raise ValueError("Pose weights require orientation in (0, 1] and height in [1, 3]")
    return reference.new_tensor([1.0, 1.0, height_weight, orientation_weight, orientation_weight, orientation_weight])


def weighted_pose_delta(jacobian, position_error, rotation_error, *, orientation_weight, damping=0.1):
    """Damped pose IK with a reduced rotation residual scale (metres/radian)."""
    if not 0.0 < orientation_weight <= 1.0 or not 0.0 < damping < float("inf"):
        raise ValueError("Pose IK requires orientation weight in (0, 1] and positive finite damping")
    scale = pose_task_scale(jacobian, orientation_weight=orientation_weight)
    weighted_jacobian = jacobian * scale[None, :, None]
    error = torch.cat((position_error, rotation_error), dim=-1) * scale
    transpose = weighted_jacobian.transpose(-1, -2)
    regularizer = damping**2 * torch.eye(6, device=jacobian.device, dtype=jacobian.dtype)
    return (transpose @ torch.linalg.solve(weighted_jacobian @ transpose + regularizer, error.unsqueeze(-1))).squeeze(-1)


def bounded_pose_delta(jacobian, error, lower, upper, *, damping=0.1, iterations=32):
    """Improve clipped DLS within the joint limits using projected descent.

    The Frobenius bound on the Hessian gives a conservative step size. Each
    iteration decreases the regularized linearized pose objective; this is a
    finite local solve, not a global kinematic or collision guarantee.
    """
    if not 0.0 < damping < float("inf") or iterations < 1:
        raise ValueError("Bounded pose IK requires positive damping and iterations")
    transpose = jacobian.transpose(-1, -2)
    identity = torch.eye(jacobian.shape[-1], device=jacobian.device, dtype=jacobian.dtype)
    hessian = transpose @ jacobian + damping**2 * identity
    rhs = (transpose @ error.unsqueeze(-1)).squeeze(-1)
    delta = torch.linalg.solve(hessian, rhs.unsqueeze(-1)).squeeze(-1).clamp(min=lower, max=upper)
    step_denominator = jacobian.square().sum(dim=(-1, -2)) + damping**2
    for _ in range(iterations):
        gradient = (hessian @ delta.unsqueeze(-1)).squeeze(-1) - rhs
        delta = (delta - gradient / step_denominator[:, None]).clamp(min=lower, max=upper)
    return delta


def bounded_push_target(target, base_position, forward_axis, *, maximum):
    """Limit forward reach in the base yaw frame without moving the target upward."""
    if not 0.43 <= maximum <= 0.65:
        raise ValueError("PUSH target reach must be in [0.43, 0.65] metres")
    reach = ((target - base_position) * forward_axis).sum(dim=1, keepdim=True)
    return target - (reach - maximum).clamp_min(0.0) * forward_axis


def coordinated_joint_target(reference, desired, max_delta):
    delta = desired - reference
    scale = torch.clamp(max_delta / delta.abs().amax(dim=1, keepdim=True).clamp_min(1.0e-9), max=1.0)
    return reference + scale * delta


def project_clearance_target(candidate, position, gradient, distance, lower, upper, *, minimum, iterations=24):
    """Project a bounded joint reference onto local body-center distance constraints.

    This is a finite-iteration kinematic diagnostic, not a collision certificate.
    Return the worst remaining linearized violation in metres, including infeasible
    constraints. Bounds combine joint limits with the reference slew-rate limit.
    """
    if not 0.0 < minimum < float("inf") or iterations < 1:
        raise ValueError("Clearance projection requires positive distance and iterations")
    target = torch.clamp(candidate, min=lower, max=upper)
    batch = torch.arange(target.shape[0], device=target.device)
    best = target.clone()
    best_violation = torch.full_like(distance[:, 0], torch.inf)
    for _ in range(iterations):
        predicted = distance + torch.einsum("npj,nj->np", gradient, target - position)
        violation, index = (minimum - predicted).clamp_min(0.0).max(dim=1)
        improved = violation < best_violation
        best = torch.where(improved[:, None], target, best)
        best_violation = torch.minimum(best_violation, violation)
        normal = gradient[batch, index]
        correction = violation / normal.square().sum(dim=1).clamp_min(1.0e-12)
        target = torch.clamp(target + correction[:, None] * normal, min=lower, max=upper)
    residual = (minimum - distance - torch.einsum("npj,nj->np", gradient, target - position)).clamp_min(0.0).amax(dim=1)
    improved = residual < best_violation
    return torch.where(improved[:, None], target, best), torch.minimum(best_violation, residual)


def advance_leg_blend(blend, release, legal_contact, *, dt, ramp_time, contact_ramp_time):
    """Keep gentle approach blending, increasing its rate only during legal contact."""
    if not 0.0 < dt < float("inf") or not 0.0 < contact_ramp_time <= ramp_time < float("inf"):
        raise ValueError("Leg blending requires positive dt and contact ramp <= approach ramp")
    rate = torch.where(legal_contact, 1.0 / contact_ramp_time, 1.0 / ramp_time)
    return torch.where(release, (blend + dt * rate).clamp(max=1.0), 0.0)


def contact_action_blend(duration, *, hold_time, ramp_time):
    if not 0.0 <= hold_time < float("inf") or not 0.0 < ramp_time < float("inf"):
        raise ValueError("Contact action blending requires finite nonnegative hold and positive ramp time")
    return ((duration - hold_time) / ramp_time).clamp(min=0.0, max=1.0)


def force_limited_contact_advance(advance, normal_force, active, *, dt, target_force, gain, speed_limit, travel_limit):
    values = (dt, target_force, gain, speed_limit, travel_limit)
    if not all(0.0 < value < float("inf") for value in values):
        raise ValueError("Contact servo parameters must be finite and positive")
    speed = torch.clamp(gain * (target_force - normal_force), -speed_limit, speed_limit)
    speed = torch.where(normal_force < 1.0, torch.full_like(speed, speed_limit), speed)
    return torch.clamp(advance + active.float() * dt * speed, min=0.0, max=travel_limit)


def confirmed_push_contact(contact, precontact_ready, at_goal, duration, *, dt, hold_time):
    if not 0.0 < dt < float("inf") or not 0.0 < hold_time < float("inf"):
        raise ValueError("Contact confirmation requires finite positive time steps and hold time")
    active = contact & precontact_ready & ~at_goal
    duration = torch.where(active, duration + dt, torch.zeros_like(duration))
    return duration, active & (duration >= hold_time - 1.0e-7)


def stabilized_ik_target(position, velocity, desired, *, gain, velocity_feedback_time):
    if not 0.0 < gain <= 1.0 or not 0.0 <= velocity_feedback_time < float("inf"):
        raise ValueError("IK gain must be in (0, 1] and velocity feedback must be finite and nonnegative")
    return position + gain * (desired - position) - velocity_feedback_time * velocity


def side_approach_ready(hand_local, box_half_length, approach_distance, height_tolerance=0.035, target_height=0.0):
    return (
        (hand_local[:, 0] >= -box_half_length - approach_distance - 0.06)
        & (hand_local[:, 0] <= -box_half_length - 0.03)
        & (hand_local[:, 1].abs() < 0.10)
        & ((hand_local[:, 2] - target_height).abs() < height_tolerance)
    )


def retained_push_contact(contact, near_face, remaining, *, dt, memory_s):
    """Bridge brief force-sampling gaps only after contact and while near the face."""
    if not 0.0 < dt < float("inf") or not 0.0 < memory_s <= 0.2:
        raise ValueError("Contact memory requires positive dt and memory in (0, 0.2]")
    remaining = torch.where(contact & near_face, memory_s, (remaining - dt).clamp_min(0.0))
    remaining = torch.where(near_face, remaining, 0.0)
    return remaining, remaining > 1.0e-7


def valid_front_contact(force, box_axis, contact_local, near_tip, box_size, height_margin=0.01):
    strength = torch.linalg.vector_norm(force, dim=1)
    resisting_force = -torch.sum(force * box_axis, dim=1)
    return (
        near_tip & torch.isfinite(contact_local).all(dim=1)
        & (resisting_force > 1.0) & (resisting_force > 0.8 * strength)
        & ((contact_local[:, 0] + box_size[0] / 2.0).abs() < 0.02)
        & (contact_local[:, 1].abs() < box_size[1] / 2.0)
        & (contact_local[:, 2].abs() <= box_size[2] / 2.0 - height_margin + 1.0e-4)
    )


def contact_push_velocity(face, box_velocity, target_distance, contact, heading_error=None, drive_speed=0.18, min_gap=0.43, forward_gain=1.0, approach_gap=0.50, stop_distance=0.10, contact_alignment_override=None, override_drive_speed=0.18):
    if not 1.0 <= forward_gain <= 2.0:
        raise ValueError("PUSH forward gain must be in [1, 2]")
    if not 0.05 <= stop_distance <= 0.11:
        raise ValueError("PUSH control stop distance must be in [0.05, 0.11] metres")
    commands = torch.zeros_like(face)
    aligned = face[:, 1].abs() < 0.12
    speed = torch.full_like(face[:, 0], drive_speed)
    if contact_alignment_override is not None:
        if not 0.0 <= override_drive_speed <= drive_speed:
            raise ValueError("Additional contact drive cannot exceed original drive speed")
        speed = torch.where(aligned, speed, torch.full_like(speed, override_drive_speed))
        aligned |= contact_alignment_override & (face[:, 0] > min_gap)
    if heading_error is not None:
        aligned &= heading_error.abs() < 0.25
        commands[:, 2] = torch.clamp(1.5 * heading_error, -0.4, 0.4)
    drive = (contact & aligned).float() * speed
    commands[:, 0] = torch.clamp(box_velocity[:, 0] + 0.8 * (face[:, 0] - approach_gap) + drive, -0.10, 0.25)
    commands[:, 0] = torch.where(commands[:, 0] > 0.01, commands[:, 0].clamp_min(0.15), commands[:, 0])
    commands[:, 0] = torch.where(face[:, 0] <= min_gap, commands[:, 0].clamp_max(0.0), commands[:, 0])
    commands[:, 1] = torch.clamp(0.8 * face[:, 1], -0.12, 0.12)
    commands[target_distance < stop_distance] = 0.0
    commands[:, 0] = torch.where(commands[:, 0] > 0.0, commands[:, 0] * forward_gain, commands[:, 0])
    return commands


def contact_gap_speed_cap(commands, gap, legal_contact, safe_approach_complete, *, slowdown_start, maximum_speed, min_gap=0.43):
    """Reduce forward commands continuously near the existing separation stop."""
    if not 0.43 == min_gap < slowdown_start <= 0.65 or not 0.0 < maximum_speed <= 0.5:
        raise ValueError("Contact gap cap requires the original .43 m stop and bounded forward speed")
    fraction = ((gap - min_gap) / (slowdown_start - min_gap)).clamp(0.0, 1.0)
    capped = torch.minimum(commands[:, 0], maximum_speed * fraction)
    result = commands.clone()
    result[:, 0] = torch.where(legal_contact & safe_approach_complete, capped, commands[:, 0])
    return result


def low_board_push_velocity(
    face, box_velocity, target_distance, contact, heading_error=None,
    drive_speed=0.12, min_gap=0.30, approach_gap=0.34,
):
    commands = torch.zeros_like(face)
    aligned = face[:, 1].abs() < 0.12
    if heading_error is not None:
        aligned &= heading_error.abs() < 0.25
        commands[:, 2] = torch.clamp(1.5 * heading_error, -0.4, 0.4)
    drive = (contact & aligned).float() * drive_speed
    approach_velocity = torch.clamp(box_velocity[:, 0] + 0.8 * (face[:, 0] - approach_gap), -0.10, 0.25)
    commands[:, 0] = torch.where(contact, drive, approach_velocity)
    commands[:, 0] = torch.where(face[:, 0] <= min_gap, commands[:, 0].clamp_max(0.0), commands[:, 0])
    commands[:, 1] = torch.clamp(0.8 * face[:, 1], -0.12, 0.12)
    commands[target_distance < 0.10] = 0.0
    return commands


def goal_brake_velocity(command, measured_velocity, at_goal, *, gain):
    """Oppose residual forward base motion at goal, within the original -0.1 limit."""
    if not 0.0 <= gain <= 2.0:
        raise ValueError("Goal braking gain must be in [0, 2]")
    result = command.clone()
    if gain:
        braking = (-gain * measured_velocity[:, 0].clamp_min(0.0)).clamp(min=-0.10)
        result[:, 0] = torch.where(at_goal, braking, result[:, 0])
    return result


def feedback_push_velocity(command, measured_velocity, face_x, *, gain, integral=None, min_gap=0.43):
    """Correct the locomotion actor's tracking error, including braking at zero target."""
    if not 0.0 <= gain <= 3.0:
        raise ValueError("PUSH velocity feedback gain must be in [0, 3]")
    result = command.clone()
    if gain:
        result[:, :2] += gain * (command[:, :2] - measured_velocity[:, :2])
        if integral is not None:
            result[:, :2] += integral
        result[:, 0].clamp_(-0.50, 0.50)
        result[:, 1].clamp_(-0.20, 0.20)
        result[:, 0] = torch.where(face_x <= min_gap, result[:, 0].clamp_max(0.0), result[:, 0])
    return result
