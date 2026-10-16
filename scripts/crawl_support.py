"""Experimental single-foot support transfer; no learned policy or climb claim."""

import math
import torch
from crawl_leg_kinematics import LegKinematics, rotate_vector


def triangle_margin(point, triangle):
    """Signed XY distance to the nearest edge; positive inside either winding."""
    edges = triangle.roll(-1, dims=1) - triangle
    relative = point[:, None] - triangle
    area = (edges[:, 0, 0] * edges[:, 1, 1] - edges[:, 0, 1] * edges[:, 1, 0])
    cross = edges[..., 0] * relative[..., 1] - edges[..., 1] * relative[..., 0]
    margin = (cross * area.sign()[:, None] / edges.norm(dim=-1).clamp_min(1e-6)).amin(dim=1)
    return torch.where(area.abs() > 1e-6, margin, -torch.ones_like(margin))


def damped_leg_delta(jacobian, error, damping=.025):
    transpose = jacobian.transpose(-1, -2)
    regularizer = damping**2 * torch.eye(3, device=jacobian.device, dtype=jacobian.dtype)
    return (transpose @ torch.linalg.solve(jacobian @ transpose + regularizer, error[..., None])).squeeze(-1)


def smooth_fraction(value):
    value = value.clamp(0, 1)
    return value**3 * (10 - 15 * value + 6 * value**2)


def flat_swing_arc(fraction, distance=.08):
    """Forward step, 5cm clearance; zero velocity/acceleration at both ends."""
    u = fraction.clamp(0, 1)
    return torch.stack((distance * smooth_fraction(u), torch.zeros_like(u),
                        .05 * 64 * u**3 * (1 - u)**3), dim=-1)


def level_orientation(quaternion, fraction):
    """Smoothly remove roll/pitch while preserving the captured heading."""
    w, x, y, z = quaternion.unbind(dim=-1)
    yaw = torch.atan2(2 * (w * z + x * y), 1 - 2 * (y.square() + z.square()))
    target = torch.stack(((yaw / 2).cos(), torch.zeros_like(yaw), torch.zeros_like(yaw), (yaw / 2).sin()), dim=-1)
    target = torch.where(((quaternion * target).sum(dim=-1) < 0)[:, None], -target, target)
    result = torch.lerp(quaternion, target, smooth_fraction(fraction)[:, None])
    return result / result.norm(dim=-1, keepdim=True).clamp_min(1e-8)


def support_shift(point, triangle, desired_margin=.03, max_distance=.10):
    """Shortest shift along the centroid ray reaching the requested margin.

    An unreachable margin returns the bounded endpoint; the measured support
    gate must still decide whether lifting is allowed.
    """
    delta = triangle.mean(dim=1) - point
    delta *= (max_distance / delta.norm(dim=1).clamp_min(max_distance))[:, None]
    low, high = torch.zeros_like(point[:, 0]), torch.ones_like(point[:, 0])
    for _ in range(16):
        middle = (low + high) / 2
        sufficient = triangle_margin(point + middle[:, None] * delta, triangle) >= desired_margin
        high = torch.where(sufficient, middle, high)
        low = torch.where(sufficient, low, middle)
    scale = torch.where(triangle_margin(point, triangle) >= desired_margin, 0., high)
    return delta * scale[:, None]


def support_vertical_forces(feet_xy, com_xy, weight, unloading):
    """Quasi-static vertical support allocation; caller must keep COM in support."""
    relative = feet_xy - com_xy[:, None]
    matrix = torch.cat((torch.ones_like(relative[..., :1]), relative), dim=2).transpose(1, 2)
    rhs = torch.stack((weight, torch.zeros_like(weight), torch.zeros_like(weight)), dim=1)

    def distribute(a):
        regularizer = 1e-7 * torch.eye(3, device=a.device, dtype=a.dtype)
        force = (a.transpose(1, 2) @ torch.linalg.solve(a @ a.transpose(1, 2) + regularizer, rhs[..., None])).squeeze(-1)
        force = force.clamp_min(0)
        return force * (weight / force.sum(dim=1).clamp_min(1e-6))[:, None]

    four = distribute(matrix)
    three = torch.cat((torch.zeros_like(weight[:, None]), distribute(matrix[:, :, 1:])), dim=1)
    return torch.lerp(four, three, unloading[:, None])


def integrate_swing_bias(bias, error, enabled, dt, gain, limit=.03):
    candidate = (bias + dt * gain * error).clamp(-limit, limit)
    return torch.where(enabled[:, None], candidate, bias)


def filter_load_reference(previous, requested, dt, time_constant):
    if time_constant <= 0:
        return requested
    return torch.lerp(previous, requested, -math.expm1(-dt / time_constant))


def loaded_hold_target(position, velocity, torque, stiffness=30., damping=.6):
    return position + (torque + damping * velocity) / stiffness


def landing_feedback(phase, body_error, swing_error, swing_weight):
    """Only blend after landing; a just-advanced lift must retain swing control.

    The trajectory weight is calculated before advancing the phase. At the
    shift-to-lift boundary it is still zero, even though phase is already 2.
    """
    original = torch.where((phase >= 2)[:, None], swing_error, body_error)
    blended = torch.lerp(body_error, swing_error, swing_weight[:, None])
    return torch.where((phase >= 5)[:, None], blended, original)


def settled_stance(contact, velocity, angular_velocity, acceleration, angular_acceleration, gravity_z):
    """Reject low-speed turning points and incomplete support before transfer."""
    return (contact.all(dim=1) & (velocity.norm(dim=1) < .025)
            & (angular_velocity.norm(dim=1) < .1) & (acceleration.norm(dim=1) < .5)
            & (angular_acceleration.norm(dim=1) < 1.) & (gravity_z < -.98))


def support_acceleration_forces(feet, com, weight, unloading, acceleration_xy):
    """Flat-ground COM acceleration with matched horizontal force and pitch/roll moment.

    Moving the pressure center alone would tip the body. The horizontal force
    and its vertical lever arm must also be included. Clamped normal loads may
    make the requested wrench infeasible; the caller records the residual.
    """
    height = (com[:, 2] - feet[:, :, 2].mean(dim=1)).clamp_min(.05)
    pressure_center = com[:, :2] - height[:, None] * acceleration_xy / 9.81
    vertical = support_vertical_forces(feet[:, :, :2], pressure_center, weight, unloading)
    horizontal = vertical[..., None] * acceleration_xy[:, None] / 9.81
    return torch.cat((horizontal, vertical[..., None]), dim=2)


class HoldQuality:
    """Accumulate the entire hold, without resetting drift when motion settles."""

    def __init__(self, count, device, dt, foot_count=4):
        self.dt = dt
        self.count = torch.zeros(count, dtype=torch.long, device=device)
        self.start_position = torch.zeros((count, 3), device=device)
        self.start_feet = torch.zeros((count, foot_count, 3), device=device)
        self.max_base_displacement = torch.zeros(count, device=device)
        self.max_base_target_error = torch.zeros(count, device=device)
        self.max_foot_displacement = torch.zeros((count, foot_count), device=device)
        self.max_foot_target_error = torch.zeros((count, foot_count), device=device)
        self.max_speed = torch.zeros(count, device=device)
        self.max_angular_speed = torch.zeros(count, device=device)
        self.min_margin = torch.full((count,), float('inf'), device=device)
        self.missing_contact_count = torch.zeros_like(self.count)

    def sample(self, mask, position, target, feet, foot_target, velocity, angular, contact, margin):
        start = mask & (self.count == 0)
        self.start_position[start] = position[start]
        self.start_feet[start] = feet[start]
        self.count += mask
        for storage, value in (
            (self.max_base_displacement, (position - self.start_position).norm(dim=1)),
            (self.max_base_target_error, (position - target).norm(dim=1)),
            (self.max_foot_displacement, (feet - self.start_feet).norm(dim=2)),
            (self.max_foot_target_error, (feet - foot_target).norm(dim=2)),
            (self.max_speed, velocity.norm(dim=1)),
            (self.max_angular_speed, angular.norm(dim=1)),
        ):
            storage[mask] = torch.maximum(storage[mask], value[mask])
        self.min_margin[mask] = torch.minimum(self.min_margin[mask], margin[mask])
        self.missing_contact_count += mask & ~contact.all(dim=1)

    def report(self):
        result = []
        for i, count in enumerate(self.count.tolist()):
            fields = {name: getattr(self, name)[i].tolist() if count else None for name in (
                'max_base_displacement', 'max_base_target_error', 'max_foot_displacement',
                'max_foot_target_error', 'max_speed', 'max_angular_speed', 'min_margin')}
            result.append(dict(env_id=i, samples=count, duration_s=count * self.dt,
                               missing_contact_s=int(self.missing_contact_count[i]) * self.dt, **fields))
        return result


class SwingQuality:
    """Measure actual airborne foot tracking, including lateral oscillation."""

    def __init__(self, count, device):
        self.samples = torch.zeros(count, dtype=torch.long, device=device)
        self.min_error = torch.full((count, 3), float('inf'), device=device)
        self.max_error = torch.full((count, 3), -float('inf'), device=device)
        self.max_speed = torch.zeros(count, device=device)
        self.max_tracking_error = torch.zeros_like(self.max_speed)
        self.actual_path = torch.zeros_like(self.max_speed)
        self.target_path = torch.zeros_like(self.max_speed)
        self.error_path = torch.zeros_like(self.max_speed)
        self.previous_actual = torch.zeros((count, 3), device=device)
        self.previous_target = torch.zeros_like(self.previous_actual)
        self.previous_mask = torch.zeros(count, dtype=torch.bool, device=device)

    def sample(self, mask, actual, target, velocity):
        error = actual - target
        self.samples += mask
        self.min_error[mask] = torch.minimum(self.min_error[mask], error[mask])
        self.max_error[mask] = torch.maximum(self.max_error[mask], error[mask])
        self.max_speed[mask] = torch.maximum(self.max_speed[mask], velocity.norm(dim=1)[mask])
        self.max_tracking_error[mask] = torch.maximum(self.max_tracking_error[mask], error.norm(dim=1)[mask])
        consecutive = mask & self.previous_mask
        actual_delta, target_delta = actual - self.previous_actual, target - self.previous_target
        for storage, delta in ((self.actual_path, actual_delta), (self.target_path, target_delta),
                               (self.error_path, actual_delta - target_delta)):
            storage[consecutive] += delta.norm(dim=1)[consecutive]
        self.previous_actual[:] = actual
        self.previous_target[:] = target
        self.previous_mask[:] = mask

    def report(self):
        return [dict(env_id=i, samples=count,
                     error_range_xyz_m=(self.max_error[i] - self.min_error[i]).tolist() if count else None,
                     max_speed_m_s=float(self.max_speed[i]), max_tracking_error_m=float(self.max_tracking_error[i]),
                     actual_path_m=float(self.actual_path[i]), target_path_m=float(self.target_path[i]),
                     error_path_m=float(self.error_path[i])) for i, count in enumerate(self.samples.tolist())]


class RearStep:
    """Optional second flat step after measured RR unloading; no climb claim.

    Stage 0 waits for release, 1 follows the arc, 2 searches/reloads, 3 holds.
    A lost support pauses the arc. Reloading requires sustained measured touch.
    """

    def __init__(self, count, device, duration=3., probe_m=.003, touch_n=.5):
        self.duration, self.probe_m, self.touch_n = duration, probe_m, touch_n
        self.stage = torch.zeros(count, device=device, dtype=torch.long)
        self.elapsed = torch.zeros(count, device=device)
        self.origin = torch.zeros((count, 3), device=device)
        self.started_at = torch.full_like(self.elapsed, -1.)
        self.probe = torch.zeros_like(self.elapsed)
        self.touch_stable = torch.zeros_like(self.elapsed)
        self.reload = torch.zeros_like(self.elapsed)
        self.end_stable = torch.zeros_like(self.elapsed)
        self.hold_stable = torch.zeros_like(self.elapsed)
        self.max_height = torch.zeros_like(self.elapsed)
        self.clearance_seen = torch.zeros(count, device=device, dtype=torch.bool)
        self.midpoint_seen = torch.zeros_like(self.clearance_seen)
        self.verified = torch.zeros_like(self.clearance_seen)

    def target(self):
        target = self.origin + flat_swing_arc(self.elapsed / self.duration)
        target[:, 2] -= self.probe_m * smooth_fraction(self.probe)
        return target

    def update(self, active, release, anchor, feet, contact, force, margin,
               velocity, angular_velocity, acceleration, angular_acceleration, gravity_z, now, dt):
        begin = active & release & (self.stage == 0)
        self.origin[begin] = anchor[begin]
        self.started_at[begin] = now[begin]
        self.stage[begin] = 1
        supported = contact[:, :3].all(dim=1) & (margin >= .015)
        swing = active & (self.stage == 1)
        progressing = swing & supported & ~begin
        self.elapsed[progressing] = (self.elapsed[progressing] + dt).clamp(max=self.duration)
        height = feet[:, 3, 2] - self.origin[:, 2]
        self.max_height[swing] = torch.maximum(self.max_height[swing], height[swing])
        self.clearance_seen |= swing & ~contact[:, 3] & (height >= .035)
        self.midpoint_seen |= (swing & ~contact[:, 3] & (height >= .03)
                              & (feet[:, 3, 0] - self.origin[:, 0] >= .03))
        end_ready = (swing & supported & (self.elapsed >= self.duration) & self.clearance_seen
                     & self.midpoint_seen & ((feet[:, 3] - self.target()).norm(dim=1) < .025))
        self.end_stable[:] = torch.where(swing, torch.where(end_ready, self.end_stable + dt, 0.), self.end_stable)
        land = end_ready & (self.end_stable >= .2)
        self.stage[land] = 2
        # Do not count the last arc observation twice as the first landing one.
        landing = active & (self.stage >= 2) & ~land
        probe = landing & supported & ~contact[:, 3]
        self.probe[probe] = (self.probe[probe] + dt).clamp(max=1.)
        touch = landing & supported & (force[:, 3] > self.touch_n)
        self.touch_stable[:] = torch.where(landing, torch.where(touch, self.touch_stable + dt, 0.), self.touch_stable)
        load_ready = touch & (self.touch_stable >= .06)
        self.reload[:] = torch.where(landing, (self.reload + torch.where(load_ready, dt, -dt)).clamp(0., .5), self.reload)
        fully_loaded = landing & (self.reload >= .5) & contact.all(dim=1)
        self.stage[fully_loaded] = 3
        self.stage[landing & ~fully_loaded] = 2
        quiet = (fully_loaded & ((feet[:, 3] - self.target()).norm(dim=1) < .025)
                 & settled_stance(contact, velocity, angular_velocity, acceleration, angular_acceleration, gravity_z))
        self.hold_stable[:] = torch.where(active, torch.where(quiet, self.hold_stable + dt, 0.), self.hold_stable)
        self.verified |= quiet & (self.hold_stable >= 1.)

    def state(self):
        return dict(rr_stage=self.stage, rr_swing_elapsed_s=self.elapsed, rr_started_at_s=self.started_at,
                    rr_probe_elapsed_s=self.probe, rr_touch_stable_s=self.touch_stable,
                    rr_reload_elapsed_s=self.reload, rr_arc_end_stable_s=self.end_stable,
                    rr_hold_stable_s=self.hold_stable, rr_max_height_m=self.max_height,
                    rr_clearance_seen=self.clearance_seen, rr_midpoint_seen=self.midpoint_seen,
                    rr_step_verified_1s=self.verified)


class SingleStepController:
    """Settle, shift COM, lift FL, move it 8 cm, lower, and hold.

    Uses measured foot Jacobians and a captured loaded standing posture.
    The existing crawl action still applies joint reference limits.
    This is a diagnostic controller, not a deployment controller.
    """

    names = ("settle", "shift", "lift", "translate", "lower", "hold", "complete", "next_RR_support_shift")

    def __init__(self, env, shift=True, gain=1., feedback_mode="anchor_ik", damping_s=.3,
                 body_feedback=.5, swing_feedback=1., force_feedforward=False,
                 shift_target="centroid", desired_margin=.03, body_damping_s=.1,
                 body_feedback_after_shift=False, stance_after_landing=False,
                 swing_integral_gain=0., force_geometry="live", stop_after_shift=False,
                 force_filter_s=0., hold_reference_mode="none", capture_between_steps=False,
                 capture_after_landing_only=False, settled_landing_capture=False, support_wrench="none",
                 pose_reference="linear", idle_only=False, climb_start_s=2., start_stable_s=0., takeover_s=0.,
                 level_stance=False, level_before_step=False, swing_damping_s=.1,
                 unload_before_lift=False, step_body_advance_m=0., reload_on_contact=False,
                 landing_probe_m=0., reload_touch_force_n=2., next_support_only=False,
                 next_shift_max_m=.10, next_unload_only=False, continuous_swing_s=0., reuse_landing_stability=False,
                 next_step=False, prepare_with_shift=False, first_leg="FL", cyclic=False,
                 prepare_for_next_support=False, bounded_cyclic_swing=False, adaptive_preparation=False,
                 early_preparation=False, overlap_landing_waits=False, approach_stride_m=0., plan_approach=False, approach_support_search=False):
        self.env, self.robot = env, env.scene["robot"]
        self.action = env.action_manager.get_term("joint_pos")
        if first_leg not in ("FL", "FR"):
            raise ValueError("Pair diagnostic must start with FL or FR")
        self.leg_order = ("FL", "FR", "RL", "RR") if first_leg == "FL" else ("FR", "FL", "RR", "RL")
        self.first_leg = first_leg
        if not math.isfinite(approach_stride_m) or (approach_stride_m and not .08 <= approach_stride_m <= .24):
            raise ValueError("Approach stride must be zero (legacy) or between.08 and.24m")
        if approach_stride_m and (not cyclic or not prepare_for_next_support or not bounded_cyclic_swing):
            raise ValueError("Approach strides require cyclic support planning and explicit bounded timing")
        if plan_approach and (not approach_stride_m or not adaptive_preparation):
            raise ValueError("Joint/body planning requires an explicit approach stride and adaptive preparation")
        if approach_support_search and not plan_approach:
            raise ValueError("Support placement search requires the joint/body approach planner")
        self.approach_support_search = approach_support_search
        self.plan_approach = plan_approach
        self.approach_stride_m = approach_stride_m
        self.stride_m = approach_stride_m or .08
        if approach_stride_m:
            # Conservative bounds on the unchanged quintic x and degree6 z
            # polynomials. These are reference bounds, not measured limits.
            speed_bound = math.hypot(1.875 * approach_stride_m, .172) / continuous_swing_s if continuous_swing_s > 0 else math.inf
            acceleration_bound = math.hypot(5.774 * approach_stride_m, 1.2) / continuous_swing_s**2 if continuous_swing_s > 0 else math.inf
            if speed_bound > (.18 if plan_approach else .12) or acceleration_bound > .4:
                raise ValueError("Approach arc exceeds its explicit nominal speed or.4m/s2 budget")
        expected_advance = approach_stride_m / 4 if approach_stride_m else .025
        if cyclic and (first_leg != "FL" or not next_support_only or not reuse_landing_stability
                       or not prepare_with_shift or (continuous_swing_s != 3. and not bounded_cyclic_swing) or support_wrench != "damping"
                       or abs(step_body_advance_m - expected_advance) > 1e-8 or landing_probe_m != .003 or reload_touch_force_n != .5
                       or body_feedback != .25 or body_damping_s != .1 or swing_feedback != .5 or takeover_s != .5):
            raise ValueError("Continuous crawl requires the established prepared FL arc and measured landing observations")
        self.cyclic = cyclic
        if bounded_cyclic_swing and not cyclic:
            raise ValueError("Bounded swing timing requires the continuous crawl diagnostic")
        self.bounded_cyclic_swing = bounded_cyclic_swing
        if adaptive_preparation and not cyclic:
            raise ValueError("Adaptive preparation requires the continuous crawl diagnostic")
        self.adaptive_preparation = adaptive_preparation
        if early_preparation and (not cyclic or not level_before_step or takeover_s != .5):
            raise ValueError("Early preparation requires cyclic leveling with the established0.5s takeover")
        self.early_preparation = early_preparation
        if overlap_landing_waits and not cyclic:
            raise ValueError("Overlapping landing observations requires the continuous crawl diagnostic")
        self.overlap_landing_waits = overlap_landing_waits
        if prepare_for_next_support and not cyclic:
            raise ValueError("Next-support preparation requires the continuous FL-first diagnostic")
        self.prepare_for_next_support = prepare_for_next_support
        self.shift, self.gain = shift, gain
        self.feedback_mode, self.damping_s = feedback_mode, damping_s
        self.body_feedback, self.swing_feedback = body_feedback, swing_feedback
        if not math.isfinite(swing_damping_s) or swing_damping_s < 0:
            raise ValueError("Swing velocity feedback must be finite and nonnegative")
        self.swing_damping_s = swing_damping_s
        if unload_before_lift and (not force_feedforward or pose_reference != "analytic" or not shift):
            raise ValueError("Measured unloading requires analytic support feedforward and centroid transfer")
        self.unload_before_lift = unload_before_lift
        self.approach_edge_blocked = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        if (not math.isfinite(step_body_advance_m) or not 0 <= step_body_advance_m <= (.06 if approach_stride_m else .04)
                or (step_body_advance_m and not unload_before_lift)):
            raise ValueError("Body advance exceeds its diagnostic bound or lacks measured unloading")
        self.step_body_advance_m = step_body_advance_m
        if reload_on_contact and not unload_before_lift:
            raise ValueError("Contact-based reloading requires measured unloading")
        self.reload_on_contact = reload_on_contact
        if (not math.isfinite(landing_probe_m) or not 0 <= landing_probe_m <= .005
                or (landing_probe_m and not reload_on_contact)):
            raise ValueError("Landing probe requires contact reloading and a distance in [0,0.005]m")
        self.landing_probe_m = landing_probe_m
        if not math.isfinite(reload_touch_force_n) or not .1 <= reload_touch_force_n <= 2.:
            raise ValueError("Reload touch threshold must be in [0.1,2]N; support contacts remain2N")
        self.reload_touch_force_n = reload_touch_force_n
        if next_support_only and (not reload_on_contact or takeover_s <= 0 or not level_before_step):
            raise ValueError("Next support diagnostic requires prepared stepping, measured reload and smooth takeover")
        self.next_support_only = next_support_only
        if not math.isfinite(next_shift_max_m) or not .10 <= next_shift_max_m <= .14:
            raise ValueError("Next support shift cap must be in [0.10,0.14]m")
        self.next_shift_max_m = next_shift_max_m
        if next_unload_only and (not next_support_only or shift_target != "centroid"):
            raise ValueError("RR unloading requires the centroid next-support diagnostic")
        self.next_unload_only = next_unload_only
        minimum_swing_s = 1.8 if bounded_cyclic_swing else 3.
        if (not math.isfinite(continuous_swing_s) or
                (continuous_swing_s != 0 and (not minimum_swing_s <= continuous_swing_s <= 4.5 or not reload_on_contact))):
            raise ValueError(f"Continuous flat swing requires contact reloading and a duration in [{minimum_swing_s},4.5]s")
        self.continuous_swing_s = continuous_swing_s
        if reuse_landing_stability and not next_support_only:
            raise ValueError("Reusing landing observations requires next-support transfer")
        self.reuse_landing_stability = reuse_landing_stability
        if next_step and (not next_unload_only or not continuous_swing_s or pose_reference != "analytic"
                          or feedback_mode != "anchor_ik" or hold_reference_mode != "none"):
            raise ValueError("RR step requires analytic arc control, measured RR unloading and no reference capture")
        self.next_step = next_step
        if prepare_with_shift and (not level_before_step or not unload_before_lift or not shift
                                   or shift_target != "centroid" or start_stable_s < .5 or takeover_s <= 0):
            raise ValueError("Combined preparation requires leveling, centroid transfer, measured unloading and >=0.5s rest")
        self.prepare_with_shift = prepare_with_shift
        if continuous_swing_s:
            self.names = (*self.names[:2], "continuous_FL_swing", "unused_translate", *self.names[4:])
        if first_leg == "FR":
            self.names = tuple(name.replace("FL", "FR").replace("RR", "RL") for name in self.names)
        self.force_feedforward = force_feedforward
        self.shift_target, self.desired_margin = shift_target, desired_margin
        self.body_damping_s = body_damping_s
        self.body_feedback_after_shift = body_feedback_after_shift
        self.stance_after_landing = stance_after_landing
        self.swing_integral_gain = swing_integral_gain
        if support_wrench not in ("none", "damping"):
            raise ValueError("Expected none/damping support wrench")
        if support_wrench != "none" and (not force_feedforward or force_geometry != "live"):
            raise ValueError("Support wrench requires live force feedforward")
        self.support_wrench = support_wrench
        if pose_reference not in ("linear", "analytic"):
            raise ValueError("Expected linear/analytic pose reference")
        if pose_reference == "analytic" and (not force_feedforward or feedback_mode != "anchor_ik"):
            raise ValueError("Analytic pose reference requires anchored IK and force feedforward")
        self.pose_reference = pose_reference
        earliest = 1. if early_preparation else 2.
        if not math.isfinite(climb_start_s) or climb_start_s < earliest or (idle_only and stop_after_shift):
            raise ValueError(f"Preparation requires at least{earliest}s; idle and shifted hold are distinct diagnostics")
        self.idle_only, self.climb_start_s = idle_only, climb_start_s
        if not math.isfinite(start_stable_s) or start_stable_s < 0:
            raise ValueError("Start stability duration must be finite and nonnegative")
        self.start_stable_s = start_stable_s
        if not math.isfinite(takeover_s) or takeover_s < 0:
            raise ValueError("Takeover duration must be finite and nonnegative")
        self.takeover_s = takeover_s
        if level_stance and (shift or not stop_after_shift or idle_only or pose_reference != "analytic" or takeover_s <= 0):
            raise ValueError("Level stance requires analytic static support, no centroid shift, and smooth takeover")
        self.level_stance = level_stance
        if level_before_step and (level_stance or not shift or stop_after_shift or idle_only
                                  or pose_reference != "analytic" or takeover_s <= 0 or start_stable_s < .5):
            raise ValueError("Prepared step requires analytic support transfer, smooth takeover, and at least0.5s settled gate")
        self.level_before_step = level_before_step
        self.kinematics = LegKinematics.from_usd(env.cfg.scene.robot.spawn.usd_path, env.device)
        if first_leg != "FL":
            self.kinematics = self.kinematics.reordered(self.leg_order)
        if force_geometry not in ("live", "planned"):
            raise ValueError("Expected live/planned force geometry")
        self.force_geometry, self.stop_after_shift = force_geometry, stop_after_shift
        self.force_filter_s = force_filter_s
        if hold_reference_mode not in ("none", "command", "equilibrium") or (hold_reference_mode != "none" and not (stop_after_shift or capture_between_steps)):
            raise ValueError("Reference capture requires static hold or explicit stance phase capture")
        self.hold_reference_mode = hold_reference_mode
        self.capture_between_steps = capture_between_steps
        self.capture_after_landing_only = capture_after_landing_only
        self.settled_landing_capture = settled_landing_capture
        if shift_target not in ("centroid", "margin") or desired_margin <= 0:
            raise ValueError("Expected centroid/margin shift and a positive support margin")
        if feedback_mode not in ("reference_integral", "posture_pd", "anchor_ik"):
            raise ValueError("Unknown support controller feedback mode")
        self.feet_ids = self.robot.find_bodies([f"{leg}_foot" for leg in self.leg_order], preserve_order=True)[0]
        self.sensor_ids = env.scene["contact_forces"].find_bodies([f"{leg}_foot" for leg in self.leg_order], preserve_order=True)[0]
        self.joint_ids = list(self.action._joint_ids)
        offset = 0 if self.robot.is_fixed_base else 6
        self.columns, self.slots = [], []
        for leg in self.leg_order:
            ids = self.robot.find_joints([f"{leg}_{joint}_joint" for joint in ("hip", "thigh", "calf")], preserve_order=True)[0]
            self.columns.append([i + offset for i in ids])
            self.slots.append([self.joint_ids.index(i) for i in ids])
        self.bodies = [i - int(self.robot.is_fixed_base) for i in self.feet_ids]
        self.mass = self.robot.root_physx_view.get_masses().to(env.device)
        count = env.num_envs
        self.rear_step = RearStep(count, env.device, continuous_swing_s or 3., landing_probe_m, reload_touch_force_n)
        self.phase = torch.zeros(count, dtype=torch.long, device=env.device)
        self.timer = torch.zeros(count, device=env.device)
        self.planned_advance = torch.full_like(self.timer, step_body_advance_m)
        self.approach_plan_feasible = torch.ones(count, dtype=torch.bool, device=env.device)
        self.approach_plan_metrics = torch.zeros((count,6), device=env.device)
        self.approach_plan_inputs = torch.zeros((count,59), device=env.device)
        self.preparation_duration = torch.full_like(self.timer, 3.)
        self.early_preparation_stable = torch.zeros_like(self.timer)
        self.early_preparation_gate = torch.zeros((count, 5), device=env.device)
        self.unload_stable_time = torch.zeros_like(self.timer)
        self.lift_elapsed = torch.zeros_like(self.timer)
        self.lift_released = torch.zeros(count, device=env.device, dtype=torch.bool)
        self.lift_released_at = torch.full_like(self.timer, -1.)
        self.lift_release_gate = torch.zeros((count, 8), device=env.device)
        self.landing_contact_stable = torch.zeros_like(self.timer)
        self.reload_elapsed = torch.zeros_like(self.timer)
        self.first_landing_contact_at = torch.full_like(self.timer, -1.)
        self.first_landing_contact_speed = torch.zeros_like(self.timer)
        self.max_airborne_reload_force = torch.zeros_like(self.timer)
        self.landing_probe_elapsed = torch.zeros_like(self.timer)
        self.reload_started_at = torch.full_like(self.timer, -1.)
        self.reload_start_force = torch.zeros_like(self.timer)
        self.next_support_stable = torch.zeros_like(self.timer)
        self.next_support_started_at = torch.full_like(self.timer, -1.)
        self.next_support_gate = torch.zeros((count, 7), device=env.device)
        self.next_ready_time = torch.zeros_like(self.timer)
        self.next_unload_started_at = torch.full_like(self.timer, -1.)
        self.next_unload_elapsed = torch.zeros_like(self.timer)
        self.next_unload_stable = torch.zeros_like(self.timer)
        self.next_unload_verified = torch.zeros(count, device=env.device, dtype=torch.bool)
        self.next_unload_gate = torch.zeros((count, 8), device=env.device)
        self.next_unload_anchor = torch.zeros((count, 3), device=env.device)
        self.arc_clearance_seen = torch.zeros(count, device=env.device, dtype=torch.bool)
        self.arc_midpoint_seen = torch.zeros_like(self.arc_clearance_seen)
        self.arc_max_actual_height = torch.zeros_like(self.timer)
        self.start_stable_time = torch.zeros_like(self.timer)
        self.started_at = torch.full_like(self.timer, -1.)
        self.preparing = torch.zeros(count, dtype=torch.bool, device=env.device)
        self.preparation_started_at = torch.full_like(self.timer, -1.)
        self.preparation_completed_at = torch.full_like(self.timer, -1.)
        self.preparation_start_raw_jump = torch.zeros_like(self.timer)
        self.preparation_start_command_jump = torch.zeros_like(self.timer)
        # duration, speed, angular speed, acceleration, angular acceleration,
        # gravity Z, contact count, elapsed leveling trajectory time at handover.
        self.preparation_gate = torch.zeros((count, 8), device=env.device)
        self.stable = torch.zeros_like(self.timer)
        self.completed = torch.zeros(count, dtype=torch.bool, device=env.device)
        self.anchors = self.robot.data.body_pos_w[:, self.feet_ids].clone()
        self.base_start = self.robot.data.root_pos_w.clone()
        self.base_target = self.base_start.clone()
        self.quat_target = self.robot.data.root_quat_w.clone()
        self.quat_start = self.quat_target.clone()
        self.com_start = self.com().clone()
        self.shift_delta = torch.zeros_like(self.base_start)
        self.foot_target = self.anchors.clone()
        self.margin = torch.zeros_like(self.timer)
        self.load_bias = torch.zeros_like(self.action.reference)
        self.reference_start = self.action.reference.clone()
        self.command_target = self.action.reference.clone()
        self.start_command_jump = torch.zeros(count, device=env.device)
        self.start_raw_jump = torch.zeros(count, device=env.device)
        self.anchor_jacobian = torch.zeros((count, 4, 3, 3), device=env.device)
        self.position_start = self.robot.data.joint_pos[:, self.joint_ids].clone()
        self.nominal_leg_reference = torch.zeros((count, 4, 3), device=env.device)
        self.nominal_foot_error = torch.zeros((count, 4), device=env.device)
        self.max_nominal_foot_error = torch.zeros_like(self.nominal_foot_error)
        self.max_measured_fk_error = torch.zeros_like(self.nominal_foot_error)
        self.nominal_error_by_phase = torch.zeros((count, 7, 4), device=env.device)
        self.support_force = torch.zeros((count, 4), device=env.device)
        self.support_force_vector = torch.zeros((count, 4, 3), device=env.device)
        self.support_moment_residual = torch.zeros_like(self.base_start)
        self.feedforward_torque = torch.zeros_like(self.action.reference)
        self.swing_bias = torch.zeros_like(self.base_start)
        self.landed_at = torch.zeros_like(self.timer)
        self.anchor_gravity = torch.zeros_like(self.action.reference)
        self.hold_reference = torch.zeros_like(self.action.reference)
        self.hold_captured = torch.zeros_like(self.completed)
        self.hold_capture_time = torch.zeros_like(self.timer)
        self.hold_stage = torch.zeros_like(self.phase)
        self.capture_stable_time = torch.zeros_like(self.timer)
        self.previous_linear_velocity = self.robot.data.root_lin_vel_w.clone()
        self.previous_angular_velocity = self.robot.data.root_ang_vel_w.clone()
        self.stiffness = self.robot.actuators["base_legs"].stiffness
        if not torch.allclose(self.stiffness, torch.full_like(self.stiffness, 30.)):
            raise ValueError("This diagnostic expects the unchanged 30 Nm/rad leg stiffness")
        self.cycle = None
        if cyclic:
            from crawl_cycle import CrawlCycle
            self.cycle = CrawlCycle(self)

    def com(self):
        return (self.robot.data.body_com_pos_w * self.mass[..., None]).sum(dim=1) / self.mass.sum(dim=1, keepdim=True)

    def contacts(self):
        return self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids, 2] > 2.

    def state(self):
        origin = self.env.scene.env_origins
        return dict(**(self.cycle.state() if self.cycle else {}), **self.rear_step.state(), phase=self.phase, phase_seconds=self.timer, single_step_completed=self.completed,
                    approach_planned_body_advance_m=self.planned_advance,
                    approach_plan_feasible=self.approach_plan_feasible,
                    approach_plan_metrics=self.approach_plan_metrics,
                    approach_plan_inputs=self.approach_plan_inputs,
                    approach_edge_blocked=self.approach_edge_blocked,
                    box_front_gap_m=(self.env.scene.env_origins[:, 0] + self.env.cfg.scene.terrain.terrain_generator.sub_terrains["box"].approach_distance - self.robot.data.body_pos_w[:, self.feet_ids, 0].amax(dim=1)),
                    preparation_nominal_duration_s=self.preparation_duration,
                    early_preparation_gate=self.early_preparation_gate,
                    unload_stable_time=self.unload_stable_time, lift_elapsed_s=self.lift_elapsed,
                    lift_released=self.lift_released, lift_released_at_s=self.lift_released_at,
                    lift_release_gate=self.lift_release_gate,
                    landing_contact_stable_s=self.landing_contact_stable,
                    reload_elapsed_s=self.reload_elapsed,
                    first_landing_contact_at_s=self.first_landing_contact_at,
                    first_landing_contact_speed_m_s=self.first_landing_contact_speed,
                    max_airborne_reload_force_n=self.max_airborne_reload_force,
                    landing_probe_elapsed_s=self.landing_probe_elapsed,
                    reload_started_at_s=self.reload_started_at, reload_start_force_n=self.reload_start_force,
                    next_support_stable_s=self.next_support_stable, next_support_started_at_s=self.next_support_started_at,
                    next_support_gate=self.next_support_gate,
                    next_unload_started_at_s=self.next_unload_started_at,
                    next_unload_elapsed_s=self.next_unload_elapsed,
                    next_unload_stable_s=self.next_unload_stable,
                    next_unload_verified=self.next_unload_verified, next_unload_gate=self.next_unload_gate,
                    arc_clearance_seen=self.arc_clearance_seen, arc_midpoint_seen=self.arc_midpoint_seen,
                    arc_max_actual_height_m=self.arc_max_actual_height,
                    nominal_error_by_phase_m=self.nominal_error_by_phase,
                    start_stable_time=self.start_stable_time, started_at_s=self.started_at,
                    command_target=self.command_target, start_command_jump_rad=self.start_command_jump,
                    start_raw_jump_rad=self.start_raw_jump,
                    preparing=self.preparing, preparation_started_at_s=self.preparation_started_at,
                    preparation_completed_at_s=self.preparation_completed_at,
                    preparation_start_raw_jump_rad=self.preparation_start_raw_jump,
                    preparation_start_command_jump_rad=self.preparation_start_command_jump,
                    preparation_gate=self.preparation_gate,
                    captured_joint_position=self.position_start,
                    nominal_leg_reference=self.nominal_leg_reference,
                    orientation_target=self.quat_target,
                    com_position=self.com() - origin, support_margin_m=self.margin,
                    base_target=self.base_target - origin, feet_position=self.robot.data.body_pos_w[:, self.feet_ids] - origin[:, None],
                    feet_target=self.foot_target - origin[:, None], contacts=self.contacts(),
                    measured_foot_force_w=self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids],
                    root_linear_velocity=self.robot.data.root_lin_vel_w,
                    root_angular_velocity=self.robot.data.root_ang_vel_w,
                    projected_gravity=self.robot.data.projected_gravity_b,
                    shift_delta=self.shift_delta,
                    swing_bias=self.swing_bias,
                    hold_captured=self.hold_captured, hold_capture_time=self.hold_capture_time, hold_stage=self.hold_stage,
                    capture_stable_time=self.capture_stable_time,
                    support_force_target_n=self.support_force, feedforward_joint_torque=self.feedforward_torque,
                    support_force_vector_n=self.support_force_vector, support_moment_residual_nm=self.support_moment_residual,
                    nominal_foot_error_m=self.nominal_foot_error, max_nominal_foot_error_m=self.max_nominal_foot_error,
                    max_measured_fk_error_m=self.max_measured_fk_error)

    def make_approach_plan(self, base, quat, com, feet, captured, leg, first=False):
        from crawl_approach import plan_ground_approach
        joint_start = torch.stack([captured[:,slots] for slots in self.slots],dim=1)
        bounds = torch.stack([self.robot.data.soft_joint_pos_limits[:,[self.joint_ids[i] for i in slots]]
                              for slots in self.slots],dim=1)
        result = plan_ground_approach(self.kinematics,base,quat,com,feet,joint_start,
                                   bounds[...,0],bounds[...,1],leg,self.stride_m,self.continuous_swing_s,first,self.approach_support_search)
        origin=self.env.scene.env_origins
        result['inputs']=torch.cat((base-origin,quat,com-origin,(feet-origin[:,None]).flatten(1),joint_start.flatten(1),
                                    bounds[...,0].flatten(1),bounds[...,1].flatten(1),leg[:,None]),dim=1)
        return result

    @staticmethod
    def plan_metrics(plan):
        return torch.stack([plan[k] for k in ('joint_margin','joint_speed','joint_acceleration',
                                               'fk_residual','support_margin','feasible_candidates')],dim=1)

    def approach_foothold_clear(self, start, distance):
        if not self.approach_stride_m:
            return torch.ones(start.shape[0], dtype=torch.bool, device=start.device)
        edge = self.env.scene.env_origins[:, 0] + self.env.cfg.scene.terrain.terrain_generator.sub_terrains["box"].approach_distance
        clear = start[:, 0] + distance <= edge - .06
        return clear

    def velocity_audit(self):
        jacobian = self.robot.root_physx_view.get_jacobians()[:, self.bodies, :3]
        velocity = torch.cat((self.robot.data.root_link_lin_vel_w, self.robot.data.root_ang_vel_w,
                              self.robot.data.joint_vel), dim=1)
        predicted = (jacobian @ velocity[:, None, :, None]).squeeze(-1)
        com_velocity = torch.cat((self.robot.data.root_com_lin_vel_w, self.robot.data.root_ang_vel_w,
                                  self.robot.data.joint_vel), dim=1)
        predicted_com = (jacobian @ com_velocity[:, None, :, None]).squeeze(-1)
        measured = self.robot.data.body_link_lin_vel_w[:, self.feet_ids]
        return dict(jacobian_predicted_foot_velocity=predicted, measured_foot_velocity=measured,
                    measured_foot_angular_velocity=self.robot.data.body_ang_vel_w[:, self.feet_ids],
                    measured_foot_quaternion=self.robot.data.body_quat_w[:, self.feet_ids],
                    jacobian_velocity_error=(predicted - measured).norm(dim=2),
                    jacobian_com_velocity_error=(predicted_com - measured).norm(dim=2))

    def compute(self, active):
        dt = self.env.step_dt
        linear_acceleration = (self.robot.data.root_lin_vel_w - self.previous_linear_velocity) / dt
        angular_acceleration = (self.robot.data.root_ang_vel_w - self.previous_angular_velocity) / dt
        self.previous_linear_velocity[:] = self.robot.data.root_lin_vel_w
        self.previous_angular_velocity[:] = self.robot.data.root_ang_vel_w
        feet = self.robot.data.body_pos_w[:, self.feet_ids]
        contact = self.contacts()
        com = self.com()
        self.margin = triangle_margin(com[:, :2], feet[:, [1, 3, 2], :2])
        next_start = torch.zeros_like(active)
        if self.next_support_only:
            observing_phase = ((self.phase >= 4) & (self.phase <= 6)) if self.reuse_landing_stability else (self.phase == 6)
            observing = observing_phase
            if self.reuse_landing_stability:
                # Keep the same continuous measured 1s gate. Include the final
                # loaded landing phases instead of discarding their observations.
                observing = (observing_phase & (self.reload_elapsed >= .5)
                             & ((feet[:, 0] - self.foot_target[:, 0]).norm(dim=1) < .025))
            ready = (active & observing
                     & settled_stance(contact, self.robot.data.root_lin_vel_w, self.robot.data.root_ang_vel_w,
                                      linear_acceleration, angular_acceleration, self.robot.data.projected_gravity_b[:, 2]))
            self.next_support_stable[:] = torch.where(
                active & observing_phase,
                torch.where(ready, self.next_support_stable + dt, 0.),
                self.next_support_stable)
            next_start = ready & (self.phase == 6) & (self.next_support_stable >= 1.) & (not self.cyclic)
            self.next_support_started_at[next_start] = (self.env.episode_length_buf * dt)[next_start]
            gate = torch.stack((self.next_support_stable, contact.sum(dim=1),
                                self.robot.data.root_lin_vel_w.norm(dim=1), self.robot.data.root_ang_vel_w.norm(dim=1),
                                linear_acceleration.norm(dim=1), angular_acceleration.norm(dim=1),
                                self.robot.data.projected_gravity_b[:, 2]), dim=1)
            self.next_support_gate[next_start] = gate[next_start]
            next_margin = triangle_margin(com[:, :2], feet[:, [0, 1, 2], :2])
            self.margin = torch.where((self.phase == 7) | next_start, next_margin, self.margin)
        if self.next_unload_only:
            ready = (active & (self.phase == 7) & (self.timer >= 3.) & contact.all(dim=1)
                     & (self.margin >= .015) & (self.robot.data.root_lin_vel_w.norm(dim=1) < .025)
                     & (self.robot.data.root_ang_vel_w.norm(dim=1) < .1)
                     & (self.robot.data.projected_gravity_b[:, 2] < -.98)
                     & ((self.robot.data.root_pos_w - self.base_target).norm(dim=1) < .015))
            self.next_ready_time[:] = torch.where(ready, self.next_ready_time + dt, 0.)
            begin = ready & (self.next_ready_time >= 1.) & (self.next_unload_started_at < 0)
            self.next_unload_started_at[begin] = (self.env.episode_length_buf * dt)[begin]
            self.next_unload_anchor[begin] = feet[begin, 3]
            unloading_rr = active & (self.next_unload_started_at >= 0)
            # Pause and smoothly restore load if any of the other three feet
            # loses support. No RR lift is commanded in this diagnostic.
            next_support = contact[:, :3].all(dim=1) & (self.margin >= .015)
            self.next_unload_elapsed[:] = torch.where(
                unloading_rr, (self.next_unload_elapsed + torch.where(next_support, dt, -dt)).clamp(0., 1.),
                self.next_unload_elapsed)
            light = self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids[3], 2] <= 5.
            released = (unloading_rr & next_support & (self.next_unload_elapsed >= 1.) & light
                        & (self.robot.data.root_lin_vel_w.norm(dim=1) < .05)
                        & (self.robot.data.root_ang_vel_w.norm(dim=1) < .1))
            self.next_unload_stable[:] = torch.where(released, self.next_unload_stable + dt, 0.)
            verified = released & (self.next_unload_stable >= .1)
            capture = verified & ~self.next_unload_verified
            gate = torch.cat((self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids, 2],
                              self.margin[:, None], self.robot.data.root_lin_vel_w.norm(dim=1)[:, None],
                              self.robot.data.root_ang_vel_w.norm(dim=1)[:, None], self.next_unload_stable[:, None]), dim=1)
            self.next_unload_gate[capture] = gate[capture]
            self.next_unload_verified |= verified
        settled = (active & (not self.idle_only) & (self.phase == 0)
                   & (self.env.episode_length_buf * dt >= self.climb_start_s) & contact.all(dim=1))
        if self.early_preparation:
            ready = (settled & (self.robot.data.root_lin_vel_w.norm(dim=1) < .15)
                     & (self.robot.data.root_ang_vel_w.norm(dim=1) < .5)
                     & (self.robot.data.projected_gravity_b[:, 2] < -.94))
            self.early_preparation_stable[:] = torch.where(
                active & (self.phase == 0), torch.where(ready, self.early_preparation_stable + dt, 0.),
                self.early_preparation_stable)
            settled &= self.early_preparation_stable >= .1
            gate = torch.stack((contact.sum(dim=1), self.robot.data.root_lin_vel_w.norm(dim=1),
                                self.robot.data.root_ang_vel_w.norm(dim=1), self.robot.data.projected_gravity_b[:, 2],
                                self.early_preparation_stable), dim=1)
            self.early_preparation_gate[settled] = gate[settled]
        initial_preparation = settled & self.level_before_step
        if self.start_stable_s > 0 and not self.level_before_step:
            ready = settled & settled_stance(contact, self.robot.data.root_lin_vel_w,
                                             self.robot.data.root_ang_vel_w, linear_acceleration,
                                             angular_acceleration, self.robot.data.projected_gravity_b[:, 2])
            self.start_stable_time[:] = torch.where(
                self.phase == 0, torch.where(ready, self.start_stable_time + dt, 0.), self.start_stable_time)
            settled &= self.start_stable_time >= self.start_stable_s
        if self.level_before_step:
            # Finish the leveling trajectory, then require continuous measured rest.
            # Four-foot static stability alone never authorizes lifting a foot.
            ready = (active & self.preparing & (self.timer >= self.preparation_duration)
                     & settled_stance(contact, self.robot.data.root_lin_vel_w,
                                      self.robot.data.root_ang_vel_w, linear_acceleration,
                                      angular_acceleration, self.robot.data.projected_gravity_b[:, 2]))
            if self.prepare_with_shift:
                ready &= (self.margin >= .015) & ((self.robot.data.root_pos_w - self.base_target).norm(dim=1) < .015)
            self.start_stable_time[:] = torch.where(
                self.preparing, torch.where(ready, self.start_stable_time + dt, 0.), self.start_stable_time)
            transfer = ready & (self.start_stable_time >= self.start_stable_s) & self.approach_plan_feasible
            gate = torch.stack((self.start_stable_time, self.robot.data.root_lin_vel_w.norm(dim=1),
                                self.robot.data.root_ang_vel_w.norm(dim=1), linear_acceleration.norm(dim=1),
                                angular_acceleration.norm(dim=1), self.robot.data.projected_gravity_b[:, 2],
                                contact.sum(dim=1), self.timer), dim=1)
            self.preparation_gate[transfer] = gate[transfer]
            self.preparation_started_at[initial_preparation] = (self.env.episode_length_buf * dt)[initial_preparation]
            self.preparation_completed_at[transfer] = (self.env.episode_length_buf * dt)[transfer]
            self.preparing[initial_preparation] = True
            self.preparing[transfer] = False
            settled |= transfer
        settled |= next_start
        self.started_at[settled] = (self.env.episode_length_buf * dt)[settled]
        self.anchors[settled] = feet[settled]
        self.base_start[settled] = self.robot.data.root_pos_w[settled]
        self.quat_target[settled] = self.robot.data.root_quat_w[settled]
        self.quat_start[settled] = self.quat_target[settled]
        self.com_start[settled] = com[settled]
        self.load_bias[settled] = self.action.reference[settled] - self.robot.data.joint_pos[:, self.joint_ids][settled]
        self.reference_start[settled] = self.action.reference[settled]
        self.position_start[settled] = self.robot.data.joint_pos[:, self.joint_ids][settled]
        jacobians = self.robot.root_physx_view.get_jacobians()
        for leg in range(4):
            self.anchor_jacobian[settled, leg] = jacobians[:, self.bodies[leg], :3][:, :, self.columns[leg]][settled]
        delta = feet[:, [1, 3, 2], :2].mean(dim=1) - com[:, :2]
        delta[next_start] = (feet[:, [0, 1, 2], :2].mean(dim=1) - com[:, :2])[next_start]
        delta *= (.10 / delta.norm(dim=1).clamp_min(.10))[:, None]
        if self.next_shift_max_m != .10:
            next_delta = feet[:, [0, 1, 2], :2].mean(dim=1) - com[:, :2]
            next_delta *= (self.next_shift_max_m / next_delta.norm(dim=1).clamp_min(self.next_shift_max_m))[:, None]
            delta[next_start] = next_delta[next_start]
        if self.shift_target == "margin" and settled.any():
            delta[settled] = support_shift(com[settled, :2], feet[settled][:, [1, 3, 2], :2], self.desired_margin)
        if self.prepare_for_next_support and initial_preparation.any():
            from crawl_cycle import next_support_preparation
            predicted = feet.clone()
            predicted[:, 0, 0] += self.stride_m
            advance = torch.zeros_like(com[:, :2]); advance[:, 0] = self.step_body_advance_m
            planned = next_support_preparation(com[:, :2], feet[:, [1, 3, 2], :2],
                                               advance, predicted[:, [0, 1, 2], :2])
            delta[initial_preparation] = planned[initial_preparation]
        if self.plan_approach and initial_preparation.any():
            plan = self.make_approach_plan(self.base_start,self.quat_start,com,feet,self.position_start,
                                           torch.zeros_like(self.phase),first=True)
            delta[initial_preparation] = plan['delta'][initial_preparation,:2]
            self.planned_advance[initial_preparation] = plan['advance'][initial_preparation]
            self.approach_plan_feasible[initial_preparation] = plan['feasible'][initial_preparation]
            self.approach_plan_metrics[initial_preparation] = self.plan_metrics(plan)[initial_preparation]
            self.approach_plan_inputs[initial_preparation] = plan['inputs'][initial_preparation]
        if self.adaptive_preparation and initial_preparation.any():
            from crawl_cycle import level_transfer_duration
            duration = level_transfer_duration(delta.norm(dim=1), self.quat_start)
            self.preparation_duration[initial_preparation] = duration[initial_preparation]
        self.shift_delta[settled, :2] = delta[settled] if self.shift else 0.
        if self.prepare_with_shift:
            # Four-foot leveling and the first COM shift share one3s trajectory.
            # Recapture only after measured rest and actual tripod margin pass.
            # At recapture the shift is already done; retain the measured pose.
            self.shift_delta[transfer] = 0.
        else:
            self.shift_delta[self.preparing] = 0.
        self.phase[settled] = 1
        if self.prepare_with_shift:
            self.phase[transfer] = 2
        self.phase[next_start] = 7
        self.timer[settled] = 0
        support = contact[:, 1:].all(dim=1)
        support = torch.where(self.phase == 7, contact.all(dim=1), support)
        moving = active & (self.phase >= 1) & ((self.phase <= 5) | (self.phase == 7)) & support
        self.timer[moving] += dt
        self.base_target[:] = self.base_start + self.shift_delta
        shifting = (self.phase == 1) | (self.phase == 7)
        shift_duration = torch.where(self.preparing, self.preparation_duration, 3.)
        leveling = shifting & (self.preparing | self.level_stance)
        if leveling.any():
            self.quat_target[leveling] = level_orientation(self.quat_start[leveling], self.timer[leveling] / shift_duration[leveling])
        self.base_target[shifting] = self.base_start[shifting] + smooth_fraction(self.timer[shifting] / shift_duration[shifting])[:, None] * self.shift_delta[shifting]
        self.foot_target[:] = self.anchors
        rr_unload_weight = smooth_fraction(self.next_unload_elapsed)
        if self.next_unload_only:
            self.foot_target[:, 3] = torch.lerp(self.anchors[:, 3], self.next_unload_anchor, rr_unload_weight[:, None])
        lifting = self.phase == 2
        traversing = self.phase == 3
        lowering = self.phase == 4
        done_moving = (self.phase >= 5) & (self.phase <= 6)
        next_shift = self.phase == 7
        trajectory_phase = self.phase.clone()
        landing_phase = lowering
        if self.continuous_swing_s:
            landing_phase = lowering | (lifting & (self.lift_elapsed >= self.continuous_swing_s / 2))
        landing_contact = active & landing_phase & contact[:, 0]
        first_touch = landing_contact & (self.first_landing_contact_at < 0)
        self.first_landing_contact_at[first_touch] = (self.env.episode_length_buf * dt)[first_touch]
        self.first_landing_contact_speed[first_touch] = self.robot.data.body_link_lin_vel_w[:, self.feet_ids[0]].norm(dim=1)[first_touch]
        if self.reload_on_contact:
            touch_force = self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids[0], 2]
            ready = active & lowering & support & (touch_force > self.reload_touch_force_n)
            self.landing_contact_stable[:] = torch.where(
                active & lowering, torch.where(ready, self.landing_contact_stable + dt, 0.), self.landing_contact_stable)
            # Smoothly reverse the load ramp if support disappears, rather than
            # applying the planned stance load to a foot still in the air.
            load_ready = ready & (self.landing_contact_stable >= .06)
            start_load = load_ready & (self.reload_started_at < 0)
            self.reload_started_at[start_load] = (self.env.episode_length_buf * dt)[start_load]
            self.reload_start_force[start_load] = touch_force[start_load]
            self.reload_elapsed[:] = torch.where(
                active & lowering, (self.reload_elapsed + torch.where(load_ready, dt, -dt)).clamp(0., .5),
                self.reload_elapsed)
        if self.step_body_advance_m:
            advance_fraction = torch.where(traversing, smooth_fraction(self.timer / 1.5), ((self.phase >= 4) & ~next_shift).float())
            self.base_target[:, 0] += self.planned_advance * advance_fraction
        lift_time = self.timer
        if self.unload_before_lift:
            # Hold the ground anchor while shifting load. A force target alone
            # does not establish that the foot is physically unloaded.
            light = (self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids[0], 2] <= 5.)
            ready = (active & lifting & support & (self.timer >= 1.) & light
                     & (self.margin >= .015)
                     & (self.robot.data.root_lin_vel_w.norm(dim=1) < .05)
                     & (self.robot.data.root_ang_vel_w.norm(dim=1) < .1))
            self.unload_stable_time[:] = torch.where(
                lifting & ~self.lift_released, torch.where(ready, self.unload_stable_time + dt, 0.),
                self.unload_stable_time)
            self.lift_elapsed[moving & lifting & self.lift_released] += dt
            clear = self.approach_foothold_clear(self.anchors[:, 0], self.stride_m)
            self.approach_edge_blocked |= active & lifting & ~clear
            release = ready & ~self.lift_released & (self.unload_stable_time >= .1) & clear
            self.lift_released_at[release] = (self.env.episode_length_buf * dt)[release]
            release_gate = torch.cat((self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids, 2],
                                      self.margin[:, None], self.robot.data.root_lin_vel_w.norm(dim=1)[:, None],
                                      self.robot.data.root_ang_vel_w.norm(dim=1)[:, None],
                                      self.unload_stable_time[:, None]), dim=1)
            self.lift_release_gate[release] = release_gate[release]
            self.lift_released |= release
            lift_time = torch.where(lifting, self.lift_elapsed, self.timer)
        if self.continuous_swing_s:
            self.base_target[lifting, 0] += self.planned_advance[lifting] * smooth_fraction(lift_time[lifting] / self.continuous_swing_s)
            swing_active = active & lifting & self.lift_released & support
            height = feet[:, 0, 2] - self.anchors[:, 0, 2]
            self.arc_max_actual_height[swing_active] = torch.maximum(self.arc_max_actual_height[swing_active], height[swing_active])
            self.arc_clearance_seen |= swing_active & ~contact[:, 0] & (height >= .035)
            self.arc_midpoint_seen |= (swing_active & ~contact[:, 0] & (height >= .03)
                                       & (feet[:, 0, 0] - self.anchors[:, 0, 0] >= .03))
        # Capture alongside the foot target, before advancing/resetting the phase timer.
        unloading = torch.where(lifting, smooth_fraction(self.timer / (1. if self.unload_before_lift else 1.5)), (self.phase >= 3).float())
        force_unloading = torch.where(lowering, 1 - smooth_fraction((self.timer - 1.) / .5), unloading)
        force_unloading = torch.where(done_moving | next_shift, 0., force_unloading)
        if self.reload_on_contact:
            force_unloading = torch.where(lowering, 1 - smooth_fraction(self.reload_elapsed / .5), force_unloading)
        self.foot_target[lifting, 0, 2] += .05 * smooth_fraction(lift_time[lifting] / 1.5)
        if self.continuous_swing_s:
            self.foot_target[lifting, 0] = self.anchors[lifting, 0] + flat_swing_arc(lift_time[lifting] / self.continuous_swing_s, self.stride_m)
        self.foot_target[traversing, 0, 2] += .05
        self.foot_target[traversing, 0, 0] += self.stride_m * smooth_fraction(self.timer[traversing] / 1.5)
        self.foot_target[lowering, 0, 0] += self.stride_m
        self.foot_target[lowering, 0, 2] += .05 * (1 - smooth_fraction(self.timer[lowering] / 1.5))
        self.foot_target[done_moving, 0, 0] += self.stride_m
        if self.landing_probe_m:
            searching = lowering & (self.timer >= 1.5)
            if self.overlap_landing_waits:
                searching |= (lifting & self.lift_released & (lift_time >= self.continuous_swing_s)
                              & self.arc_clearance_seen & self.arc_midpoint_seen)
            probe = active & searching & support & ~contact[:, 0]
            self.landing_probe_elapsed[probe] = (self.landing_probe_elapsed[probe] + dt).clamp(max=1.)
            # Retain the measured-contact search depth after landing; removing it
            # at a phase boundary would introduce another reference discontinuity.
            self.foot_target[:, 0, 2] -= self.landing_probe_m * smooth_fraction(self.landing_probe_elapsed) * (~next_shift)
        if self.next_step:
            rr = self.rear_step
            # Use this frame's measured release gate, not the historical latch.
            release_rr = released & (self.next_unload_stable >= .1)
            rr.update(active, release_rr, self.next_unload_anchor, feet, contact,
                      self.env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids, 2],
                      self.margin, self.robot.data.root_lin_vel_w, self.robot.data.root_ang_vel_w,
                      linear_acceleration, angular_acceleration, self.robot.data.projected_gravity_b[:, 2],
                      self.env.episode_length_buf * dt, dt)
            rr_active = rr.stage > 0
            self.foot_target[rr_active, 3] = rr.target()[rr_active]
            self.base_target[rr_active, 0] += self.planned_advance[rr_active] * smooth_fraction(rr.elapsed[rr_active] / rr.duration)
            rr_unload_weight = torch.where(rr_active, 1 - smooth_fraction(rr.reload / .5), rr_unload_weight)
        analytic_reference = None
        if self.pose_reference == "analytic":
            local_feet = rotate_vector(self.quat_target[:, None], self.foot_target - self.base_target[:, None], inverse=True)
            analytic_reference = self.kinematics.inverse(local_feet)
        if self.force_feedforward:
            planned = self.force_geometry == "planned"
            allocation_feet = self.foot_target if planned else feet
            allocation_com = self.com_start + self.base_target - self.base_start if planned else com
            self.support_force[:] = support_vertical_forces(allocation_feet[:, :, :2], allocation_com[:, :2],
                                                            self.mass.sum(dim=1) * 9.81, force_unloading)
            self.support_force_vector.zero_()
            self.support_force_vector[:, :, 2] = self.support_force
            if self.support_wrench != "none":
                fraction = (self.timer / shift_duration).clamp(0, 1)
                target_velocity = self.shift_delta * (30 * fraction**2 * (1 - fraction)**2 / shift_duration)[:, None]
                target_velocity[~shifting] = 0.
                if self.step_body_advance_m:
                    fraction = (self.timer / 1.5).clamp(0, 1)
                    advance_velocity = self.planned_advance * 30 * fraction**2 * (1 - fraction)**2 / 1.5
                    target_velocity[traversing, 0] = advance_velocity[traversing]
                    if self.continuous_swing_s:
                        fraction = (lift_time / self.continuous_swing_s).clamp(0, 1)
                        target_velocity[lifting, 0] = (self.planned_advance * 30 * fraction**2 * (1 - fraction)**2 / self.continuous_swing_s)[lifting]
                    if self.next_step:
                        fraction = (self.rear_step.elapsed / self.rear_step.duration).clamp(0, 1)
                        rr_velocity = self.planned_advance * 30 * fraction**2 * (1 - fraction)**2 / self.rear_step.duration
                        rr_supported = contact[:, :3].all(dim=1) & (self.margin >= .015)
                        target_velocity[self.rear_step.stage > 0, 0] = torch.where(rr_supported, rr_velocity, 0.)[self.rear_step.stage > 0]
                com_velocity = (self.robot.data.body_com_lin_vel_w * self.mass[..., None]).sum(dim=1) / self.mass.sum(dim=1, keepdim=True)
                acceleration = 4. * (target_velocity[:, :2] - com_velocity[:, :2])
                acceleration *= (.4 / acceleration.norm(dim=1).clamp_min(.4))[:, None]
                self.support_force_vector[:] = support_acceleration_forces(
                    feet, com, self.mass.sum(dim=1) * 9.81, force_unloading, acceleration)
                self.support_force[:] = self.support_force_vector[:, :, 2]
            if self.next_unload_only:
                # Reuse the original FL allocator with RR in the swing slot;
                # restore FL/FR/RL/RR order before applying physical torques.
                order, inverse = [3, 0, 1, 2], [1, 2, 3, 0]
                rr_forces = support_acceleration_forces(
                    feet[:, order], com, self.mass.sum(dim=1) * 9.81, rr_unload_weight,
                    acceleration if self.support_wrench != "none" else torch.zeros_like(com[:, :2]))[:, inverse]
                use_rr = self.next_unload_started_at >= 0
                self.support_force_vector[:] = torch.where(use_rr[:, None, None], rr_forces, self.support_force_vector)
                self.support_force[:] = self.support_force_vector[:, :, 2]
            self.support_moment_residual[:] = torch.cross(feet - com[:, None], self.support_force_vector, dim=2).sum(dim=1)
            airborne_lowering = active & lowering & ~contact[:, 0]
            self.max_airborne_reload_force[airborne_lowering] = torch.maximum(
                self.max_airborne_reload_force[airborne_lowering], self.support_force[airborne_lowering, 0])
            gravity = self.robot.root_physx_view.get_gravity_compensation_forces()
            gravity_columns = self.joint_ids if gravity.shape[1] == self.robot.num_joints else [i + 6 for i in self.joint_ids]
            self.anchor_gravity[settled] = gravity[:, gravity_columns][settled]
        swing_weight = torch.where(self.phase >= 5, 1 - smooth_fraction((self.env.episode_length_buf * dt - self.landed_at) / .75),
                                   ((self.phase >= 2) & (self.phase <= 4)).float())
        if self.swing_integral_gain:
            ids = [self.joint_ids[slot] for slot in self.slots[0]]
            torque_ratio = (self.robot.data.applied_torque[:, ids].abs()
                            / self.robot.data.joint_effort_limits[:, ids].clamp_min(1e-6)).amax(dim=1)
            integral_ready = lift_time >= 1.5
            if self.continuous_swing_s:
                integral_ready = torch.where(lifting, lift_time >= self.continuous_swing_s, integral_ready)
            integrate = (active & support & ~contact[:, 0] & integral_ready
                         & (lifting | traversing | lowering) & (torque_ratio < .9))
            self.swing_bias[:] = integrate_swing_bias(self.swing_bias, self.foot_target[:, 0] - feet[:, 0],
                                                      integrate, dt, self.swing_integral_gain)
        speed = self.robot.data.root_lin_vel_w.norm(dim=1)
        shift_ready = (self.margin >= .015) if self.shift else torch.ones_like(active)
        loaded = (self.reload_elapsed >= .5) if self.reload_on_contact else torch.ones_like(active)
        lift_ready = lifting & (lift_time >= 1.5) & ~contact[:, 0] & (feet[:, 0, 2] >= self.anchors[:, 0, 2] + .035)
        if self.continuous_swing_s:
            lift_ready = (lifting & (lift_time >= self.continuous_swing_s) & self.arc_clearance_seen & self.arc_midpoint_seen
                          & ((feet[:, 0] - self.foot_target[:, 0]).norm(dim=1) < .025))
        phase_ready = ((shifting & ~next_shift & ~self.preparing & (not self.stop_after_shift) & (self.timer >= 3.) & shift_ready & (speed < .05) & contact.all(dim=1))
                       | lift_ready
                       | (traversing & (self.timer >= 1.5) & ((feet[:, 0, :2] - self.foot_target[:, 0, :2]).norm(dim=1) < .02) & (feet[:, 0, 2] >= self.anchors[:, 0, 2] + .03))
                       | (lowering & loaded & (self.timer >= 1.5) & contact.all(dim=1) & ((feet[:, 0] - self.foot_target[:, 0]).norm(dim=1) < .025))
                       | ((self.phase == 5) & contact.all(dim=1) & (speed < .05))) & active & support
        self.stable = torch.where(phase_ready, self.stable + dt, 0.)
        advance = phase_ready & (self.stable >= .20)
        self.landed_at[advance & lowering] = (self.env.episode_length_buf * dt)[advance & lowering]
        self.phase[advance] += 1
        self.timer[advance] = 0
        if self.continuous_swing_s:
            # The arc already ended at the landing target. Continue the original
            # contact search/reload, not another nominal lowering trajectory.
            self.phase[advance & lifting] = 4
            self.timer[advance & lifting] = 1.5
        self.stable[advance] = 0
        self.completed |= active & (self.phase == 6)
        # Compute a small world-frame body correction through fixed stance feet.
        base_error = (self.base_target - self.robot.data.root_pos_w).clamp(-.03, .03)
        actual_q, desired_q = self.robot.data.root_quat_w, self.quat_target
        scalar = (actual_q * desired_q).sum(dim=1)
        rotation_error = 2 * scalar.sign()[:, None] * (
            -desired_q[:, :1] * actual_q[:, 1:] + actual_q[:, :1] * desired_q[:, 1:]
            - torch.cross(desired_q[:, 1:], actual_q[:, 1:], dim=1))
        relative = feet - self.robot.data.root_pos_w[:, None]
        error = self.foot_target - feet - base_error[:, None] - torch.cross(rotation_error[:, None].expand_as(relative), relative, dim=2)
        targets = self.action.reference.clone()
        engaged = active & (self.phase >= 1)
        for leg in range(4):
            jacobian = jacobians[:, self.bodies[leg], :3][:, :, self.columns[leg]]
            if self.feedback_mode == "reference_integral":
                increment = (self.gain * damped_leg_delta(jacobian, error[:, leg])).clamp(-.015, .015)
                targets[:, self.slots[leg]] += increment * engaged[:, None]
            elif self.feedback_mode == "posture_pd":
                ids = [self.joint_ids[slot] for slot in self.slots[leg]]
                joint_speed = self.robot.data.joint_vel[:, ids]
                local_speed = (jacobian @ joint_speed[..., None]).squeeze(-1)
                correction = (self.gain * damped_leg_delta(jacobian, error[:, leg] - self.damping_s * local_speed)).clamp(-.15, .15)
                # Re-anchor to measured posture, preserving the static load offset.
                # This avoids integrating position error into an ever-growing target.
                targets[:, self.slots[leg]] = self.robot.data.joint_pos[:, ids] + self.load_bias[:, self.slots[leg]] + correction
            else:
                # Feedforward pose about the verified loaded standing posture.
                # A zero body/foot displacement exactly retains the held reference.
                displacement = self.foot_target[:, leg] - self.anchors[:, leg] - (self.base_target - self.base_start)
                correction = (self.gain * damped_leg_delta(self.anchor_jacobian[:, leg], displacement)).clamp(-.7, .7)
                reference = self.position_start if self.force_feedforward else self.reference_start
                targets[:, self.slots[leg]] = reference[:, self.slots[leg]] + correction
                if analytic_reference is not None:
                    ids = [self.joint_ids[slot] for slot in self.slots[leg]]
                    initial = self.position_start[:, self.slots[leg]]
                    limits = self.robot.data.soft_joint_pos_limits[:, ids]
                    lower = torch.maximum(initial - .7, limits[:, :, 0])
                    upper = torch.minimum(initial + .7, limits[:, :, 1])
                    targets[:, self.slots[leg]] = torch.maximum(torch.minimum(analytic_reference[:, leg], upper), lower)
                self.nominal_leg_reference[:, leg] = targets[:, self.slots[leg]]
                body_error = -(self.base_target - self.robot.data.root_pos_w).clamp(-.10, .10)
                body_error -= torch.cross(rotation_error, relative[:, leg], dim=1)
                body_error += self.body_damping_s * (self.robot.data.root_lin_vel_w + torch.cross(self.robot.data.root_ang_vel_w, relative[:, leg], dim=1))
                feedback_scale = unloading[:, None] if self.body_feedback_after_shift else 1.
                feedback_error = self.body_feedback * feedback_scale * body_error
                if leg == 0:
                    swing_error = (self.foot_target[:, leg] - feet[:, leg]
                                   - self.swing_damping_s * self.robot.data.body_lin_vel_w[:, self.feet_ids[leg]])
                    swing_error = self.swing_feedback * swing_error + self.swing_bias
                    if self.stance_after_landing:
                        feedback_error = landing_feedback(self.phase, feedback_error, swing_error, swing_weight)
                    else:
                        feedback_error = torch.where(((self.phase >= 2) & ~next_shift)[:, None], swing_error, feedback_error)
                if leg == 3 and self.next_unload_only:
                    ground_error = self.swing_feedback * (self.foot_target[:, leg] - feet[:, leg])
                    feedback_error = torch.lerp(feedback_error, ground_error, rr_unload_weight[:, None])
                targets[:, self.slots[leg]] += damped_leg_delta(jacobian, feedback_error.clamp(-.08, .08)).clamp(-.4, .4)
                if self.force_feedforward:
                    ids = [self.joint_ids[slot] for slot in self.slots[leg]]
                    columns = ids if gravity.shape[1] == self.robot.num_joints else self.columns[leg]
                    if self.force_geometry == "planned":
                        torque = self.anchor_gravity[:, self.slots[leg]] - self.anchor_jacobian[:, leg, 2] * self.support_force[:, leg, None]
                    else:
                        if self.support_wrench == "none":
                            torque = gravity[:, columns] - jacobian[:, 2] * self.support_force[:, leg, None]
                        else:
                            torque = gravity[:, columns] - (jacobian.transpose(1, 2) @ self.support_force_vector[:, leg, :, None]).squeeze(-1)
                    limit = .75 * self.robot.data.joint_effort_limits[:, ids]
                    torque = torch.maximum(torch.minimum(torque, limit), -limit)
                    if self.force_filter_s > 0:
                        filtered = filter_load_reference(self.feedforward_torque[:, self.slots[leg]], torque, dt, self.force_filter_s)
                        filtered[settled] = torque[settled]
                        torque = filtered
                    self.feedforward_torque[:, self.slots[leg]] = torque
                    targets[:, self.slots[leg]] += torque / 30.
                elif leg == 0:
                    targets[:, self.slots[leg]] -= self.load_bias[:, self.slots[leg]] * unloading[:, None]
        nominal_feet = rotate_vector(self.quat_target[:, None], self.kinematics.forward(self.nominal_leg_reference)) + self.base_target[:, None]
        self.nominal_foot_error[:] = (nominal_feet - self.foot_target).norm(dim=2)
        nominal_active = engaged if self.cycle is None else engaged & (self.cycle.stage == 0)
        self.max_nominal_foot_error[nominal_active] = torch.maximum(self.max_nominal_foot_error[nominal_active], self.nominal_foot_error[nominal_active])
        for phase_index in range(7):
            phase_mask = nominal_active & (trajectory_phase == phase_index)
            self.nominal_error_by_phase[phase_mask, phase_index] = torch.maximum(
                self.nominal_error_by_phase[phase_mask, phase_index], self.nominal_foot_error[phase_mask])
        measured_joints = torch.stack([self.robot.data.joint_pos[:, self.joint_ids][:, slots] for slots in self.slots], dim=1)
        reconstructed = rotate_vector(self.robot.data.root_quat_w[:, None], self.kinematics.forward(measured_joints)) + self.robot.data.root_pos_w[:, None]
        measured_error = (reconstructed - feet).norm(dim=2)
        self.max_measured_fk_error[active] = torch.maximum(self.max_measured_fk_error[active], measured_error[active])
        if measured_error[active].numel() and measured_error[active].max() > .0005:
            raise RuntimeError("Leg FK differs from active Isaac geometry by more than0.5mm")
        if self.hold_reference_mode != "none":
            hold_stage = torch.where((self.phase == 1) & (not self.capture_after_landing_only), 1,
                                     torch.where((self.phase >= 5) & self.capture_between_steps, 2, 0))
            self.hold_captured &= hold_stage == self.hold_stage
            self.hold_stage[:] = hold_stage
            candidate = self.action.reference.clone()
            if self.hold_reference_mode == "equilibrium":
                candidate = loaded_hold_target(self.robot.data.joint_pos[:, self.joint_ids],
                                               self.robot.data.joint_vel[:, self.joint_ids],
                                               self.robot.data.applied_torque[:, self.joint_ids])
            limits = self.robot.data.soft_joint_pos_limits[:, self.joint_ids]
            within_limits = ((candidate[:, :12] >= limits[:, :12, 0]) & (candidate[:, :12] <= limits[:, :12, 1])).all(dim=1)
            ready = ((hold_stage == 1) & (self.timer >= 3.)) | (
                (hold_stage == 2) & ((feet[:, 0] - self.foot_target[:, 0]).norm(dim=1) < .025))
            capture = (active & ~self.hold_captured & ready & contact.all(dim=1)
                       & (self.margin >= .015) & (speed < .05) & (self.robot.data.root_ang_vel_w.norm(dim=1) < .2)
                       & (self.robot.data.projected_gravity_b[:, 2] < -.98) & within_limits)
            if self.settled_landing_capture:
                stable = (capture & (hold_stage == 2) & (speed < .025)
                          & (self.robot.data.root_ang_vel_w.norm(dim=1) < .1)
                          & (linear_acceleration.norm(dim=1) < .5) & (angular_acceleration.norm(dim=1) < 1.))
                self.capture_stable_time[:] = torch.where(stable, self.capture_stable_time + dt, 0.)
                capture &= (hold_stage != 2) | (self.capture_stable_time >= .5)
            self.hold_reference[capture] = candidate[capture]
            self.hold_capture_time[capture] = (self.env.episode_length_buf * dt)[capture]
            self.hold_captured |= capture
            targets = torch.where(self.hold_captured[:, None], self.hold_reference, targets)
        defaults = self.robot.data.default_joint_pos[:, self.joint_ids]
        self.start_raw_jump[settled] = (targets - self.reference_start).abs().amax(dim=1)[settled]
        if self.takeover_s > 0:
            fraction = smooth_fraction((self.env.episode_length_buf * dt - self.started_at) / self.takeover_s)
            targets = torch.lerp(self.reference_start, targets, fraction[:, None])
        self.start_command_jump[settled] = (targets - self.reference_start).abs().amax(dim=1)[settled]
        self.preparation_start_raw_jump[initial_preparation] = self.start_raw_jump[initial_preparation]
        self.preparation_start_command_jump[initial_preparation] = self.start_command_jump[initial_preparation]
        self.command_target[:] = targets
        normalized = (targets - defaults) / self.action.cfg.scale
        normalized[:, 12:] = 0
        normalized[~engaged] = 0
        if self.cycle is not None:
            cycling, cycle_action = self.cycle.compute(active, linear_acceleration, angular_acceleration)
            normalized = torch.where(cycling[:, None], cycle_action, normalized)
        return normalized
