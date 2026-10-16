"""Check contact drive, separation limits and goal stopping."""

from pathlib import Path
import ast
import runpy
from types import SimpleNamespace
import unittest

import torch


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/box_push_control.py"
helpers = runpy.run_path(str(MODULE))
command = helpers["contact_push_velocity"]
low_board_command = helpers["low_board_push_velocity"]


class PushControlChecks(unittest.TestCase):
    def test_gap_cap_is_continuous_and_never_increases_forward_motion(self):
        gap = torch.linspace(.40, .60, 201, dtype=torch.float64)
        commands = torch.tensor([.5, -.07, .2], dtype=torch.float64).repeat(len(gap), 1)
        enabled = torch.ones_like(gap, dtype=torch.bool)
        out = helpers["contact_gap_speed_cap"](commands, gap, enabled, enabled, slowdown_start=.52, maximum_speed=.5)
        self.assertTrue((out[:, 0] <= commands[:, 0]).all())
        self.assertTrue((out[:, 0] >= 0).all())
        self.assertTrue((torch.diff(out[:, 0]) >= -1e-12).all())
        self.assertLess(torch.diff(out[:, 0]).abs().max().item(), .006)
        self.assertTrue((out[gap <= .43, 0] == 0).all())
        torch.testing.assert_close(out[gap >= .52], commands[gap >= .52])
        torch.testing.assert_close(out[:, 1:], commands[:, 1:])
        torch.testing.assert_close(commands[:, 0], torch.full_like(gap, .5))

    def test_gap_cap_preserves_goal_stop_reverse_and_contact_gates(self):
        commands = torch.tensor([[0., .1, -.2], [-.1, .1, -.2], [.5, .1, -.2], [.5, .1, -.2]])
        legal = torch.tensor([True, True, False, True])
        safe = torch.tensor([True, True, True, False])
        out = helpers["contact_gap_speed_cap"](commands, torch.full((4,), .44), legal, safe, slowdown_start=.52, maximum_speed=.5)
        torch.testing.assert_close(out, commands)
        for start, speed, minimum in [(.43, .5, .43), (.7, .5, .43), (float("nan"), .5, .43), (.52, .51, .43), (.52, .5, .42)]:
            with self.assertRaises(ValueError):
                helpers["contact_gap_speed_cap"](commands, torch.ones(4), legal, safe, slowdown_start=start, maximum_speed=speed, min_gap=minimum)

    def test_gap_cap_integration_uses_current_contact_after_feedback(self):
        # Load the real wrapper without importing Isaac; stub sensor/robot I/O.
        source = ast.parse((MODULE.parent / "box_push.py").read_text())
        function = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "push_velocity_commands")
        command_value = torch.tensor([[.5, .02, -.03]])
        contact = torch.tensor([True])
        robot = SimpleNamespace(data=SimpleNamespace(root_quat_w=torch.ones(1, 4), root_pos_w=torch.zeros(1, 3), root_lin_vel_w=torch.zeros(1, 3)))
        env = SimpleNamespace(scene={"robot": robot}, cfg=SimpleNamespace(push_contact_gap_slowdown_start=.52, push_forward_command_gain=2.), box_push_safe_approach_complete=torch.tensor([True]), box_push_drive_contact=torch.tensor([True]))
        namespace = dict(torch=torch, SceneEntityCfg=lambda *a, **kw: None,
                         nominal_push_velocity_commands=lambda *a: torch.zeros(1, 3),
                         yaw_quat=lambda x: x, quat_apply_inverse=lambda q, x: x,
                         front_face=lambda e: torch.tensor([[.475, 0., 0.]]),
                         feedback_push_velocity=lambda *a, **kw: command_value.clone(),
                         hand_contact=lambda *a: contact,
                         forbidden_box_contact=lambda e: torch.tensor([False]),
                         contact_gap_speed_cap=helpers["contact_gap_speed_cap"])
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(MODULE.parent / "box_push.py"), "exec"), namespace)
        out = namespace["push_velocity_commands"](env)
        self.assertAlmostEqual(out[0, 0].item(), .25, places=6)
        torch.testing.assert_close(out[:, 1:], command_value[:, 1:])
        contact[:] = False  # A true contact-memory latch must not activate the cap.
        torch.testing.assert_close(namespace["push_velocity_commands"](env), command_value)
        contact[:] = True
        env.cfg.push_contact_gap_slowdown_start = 0.
        torch.testing.assert_close(namespace["push_velocity_commands"](env), command_value)

    def test_height_weight_trades_reach_for_height_within_original_joint_limit(self):
        # One joint raises both x and z, but requested x and z conflict.
        jacobian = torch.zeros((1, 6, 1), dtype=torch.float64)
        jacobian[:, 0, 0] = 1.0
        jacobian[:, 2, 0] = 1.0
        error = torch.tensor([[1., 0., -1., 0., 0., 0.]], dtype=torch.float64)
        low, high = torch.tensor([[-.5]]), torch.tensor([[.5]])
        results = []
        for height in (1., 2., 3.):
            scale = helpers["pose_task_scale"](jacobian, orientation_weight=.5, height_weight=height)
            delta = helpers["bounded_pose_delta"](jacobian * scale[None, :, None], error * scale, low, high)
            optimum = max(-.5, min(.5, (1. - height**2) / (1. + height**2 + .01)))
            self.assertAlmostEqual(delta.item(), optimum, places=7)
            self.assertTrue(((delta >= low) & (delta <= high)).all())
            results.append(abs(delta.item() + 1.))
        self.assertLess(results[1], results[0])
        torch.testing.assert_close(helpers["pose_task_scale"](jacobian, orientation_weight=1.), torch.ones(6, dtype=torch.float64))
        for height in (.9, 3.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                helpers["pose_task_scale"](jacobian, orientation_weight=.5, height_weight=height)

    def test_contact_acceleration_preserves_initial_blend_and_release_gate(self):
        advance = helpers["advance_leg_blend"]
        release = torch.tensor([True, True, False])
        blend = torch.zeros(3)
        for _ in range(5):
            blend = advance(blend, release, torch.zeros(3, dtype=torch.bool), dt=.02, ramp_time=.5, contact_ramp_time=.2)
        torch.testing.assert_close(blend, torch.tensor([.2, .2, 0.]))
        blend = advance(blend, release, torch.tensor([False, True, True]), dt=.02, ramp_time=.5, contact_ramp_time=.2)
        torch.testing.assert_close(blend, torch.tensor([.24, .3, 0.]))
        # Losing contact returns to the slow rate without resetting or jumping the blend.
        blend = advance(blend, release, torch.zeros(3, dtype=torch.bool), dt=.02, ramp_time=.5, contact_ramp_time=.2)
        torch.testing.assert_close(blend, torch.tensor([.28, .34, 0.]))
        for _ in range(25):
            blend = advance(blend, release, torch.ones(3, dtype=torch.bool), dt=.02, ramp_time=.5, contact_ramp_time=.2)
        torch.testing.assert_close(blend, torch.tensor([1., 1., 0.]))
        blend[1] = 0.  # per-environment episode reset
        blend = advance(blend, torch.ones(3, dtype=torch.bool), torch.zeros(3, dtype=torch.bool), dt=.02, ramp_time=.5, contact_ramp_time=.2)
        torch.testing.assert_close(blend, torch.tensor([1., .04, .04]))
        for fast in (0., .6, float("nan")):
            with self.assertRaises(ValueError):
                advance(blend, release, release, dt=.02, ramp_time=.5, contact_ramp_time=fast)

    def test_goal_release_is_outward_once_and_preserves_measured_orientation(self):
        latch = helpers["latch_goal_pose"]
        p = torch.tensor([[.5, .2, .13], [.6, .3, .12]])
        q = torch.tensor([[1., 0., 0., 0.], [0., 0., 0., 1.]])
        axis = torch.tensor([[1., 0., 0.], [0., 1., 0.]])
        active, saved_p, saved_q = latch(torch.ones(2, dtype=torch.bool), torch.zeros(2, dtype=torch.bool), torch.zeros_like(p), torch.zeros_like(q), p, q, release_axis=axis, release_distance=.01)
        torch.testing.assert_close(saved_p, torch.tensor([[.49, .2, .13], [.6, .29, .12]]))
        torch.testing.assert_close(saved_q, q)
        _, held_p, held_q = latch(active, active, saved_p, saved_q, p + .2, q.flip(0), release_axis=-axis, release_distance=.01)
        torch.testing.assert_close(held_p, saved_p)
        torch.testing.assert_close(held_q, saved_q)
        for invalid in (-.001, .021, float("nan")):
            with self.assertRaises(ValueError):
                latch(active, active, p, q, p, q, release_axis=axis, release_distance=invalid)

    def test_goal_braking_only_opposes_forward_motion_at_goal_and_is_bounded(self):
        brake = helpers["goal_brake_velocity"]
        cmd = torch.tensor([[.4, .02, .1], [0., .01, 0.], [0., 0., 0.], [0., 0., 0.]])
        velocity = torch.tensor([[.4, 0., 0.], [.05, 0., 0.], [1., 0., 0.], [-.1, 0., 0.]])
        at_goal = torch.tensor([False, True, True, True])
        result = brake(cmd, velocity, at_goal, gain=.5)
        torch.testing.assert_close(result[:, 0], torch.tensor([.4, -.025, -.1, 0.]))
        torch.testing.assert_close(result[:, 1:], cmd[:, 1:])
        torch.testing.assert_close(brake(cmd, velocity, at_goal, gain=0.), cmd)
        self.assertGreater(cmd[0, 0], 0.)  # input remains unchanged
        for invalid in (-.1, 2.1, float("nan")):
            with self.assertRaises(ValueError):
                brake(cmd, velocity, at_goal, gain=invalid)

    def test_leg_release_needs_real_contact_after_safe_approach(self):
        latch = helpers["latch_leg_contact"]
        ready = latch(torch.zeros(3, dtype=torch.bool), torch.tensor([False, True, True]), torch.tensor([True, False, True]))
        torch.testing.assert_close(ready, torch.tensor([False, False, True]))
        ready = latch(ready, torch.ones(3, dtype=torch.bool), torch.zeros(3, dtype=torch.bool))
        torch.testing.assert_close(ready, torch.tensor([False, False, True]))
        ready[2] = False
        torch.testing.assert_close(latch(ready, torch.ones(3, dtype=torch.bool), torch.zeros(3, dtype=torch.bool)), torch.zeros(3, dtype=torch.bool))

    def test_control_stop_distance_only_changes_goal_braking(self):
        face = torch.tensor([[.60, 0., 0.]]).repeat(3, 1)
        remaining = torch.tensor([.109, .111, .20])
        contact = torch.ones(3, dtype=torch.bool)
        original = command(face, torch.zeros_like(face), remaining, contact)
        early = command(face, torch.zeros_like(face), remaining, contact, stop_distance=.11)
        torch.testing.assert_close(early[0], torch.zeros(3))
        self.assertGreater(original[0, 0], 0.)
        torch.testing.assert_close(early[1:], original[1:])
        for invalid in (.12, .04, float("nan")):
            with self.assertRaises(ValueError):
                command(face, torch.zeros_like(face), remaining, contact, stop_distance=invalid)

    def test_goal_pose_holds_world_pose_and_reenters_after_reset_or_recoil(self):
        latch = helpers["latch_goal_pose"]
        position = torch.tensor([[.5, .1, .13], [.6, -.1, .14]])
        quaternion = torch.tensor([[1., 0., 0., 0.], [.8, 0., .6, 0.]])
        active, saved_p, saved_q = latch(torch.tensor([True, False]), torch.zeros(2, dtype=torch.bool), torch.zeros_like(position), torch.zeros_like(quaternion), position, quaternion)
        # Motion of the robot/box after entry must not drag the held world target.
        active, saved_p, saved_q = latch(torch.tensor([True, True]), active, saved_p, saved_q, position + .2, quaternion.flip(0))
        torch.testing.assert_close(saved_p, torch.stack((position[0], position[1] + .2)))
        torch.testing.assert_close(saved_q[0], quaternion[0])
        active, saved_p, saved_q = latch(torch.tensor([False, True]), active, saved_p, saved_q, position + .3, quaternion)
        self.assertFalse(active[0])
        self.assertTrue(active[1])
        # A per-environment reset only clears that environment's latch.
        active[1] = False
        active, saved_p, saved_q = latch(torch.ones(2, dtype=torch.bool), active, saved_p, saved_q, position + .4, quaternion)
        torch.testing.assert_close(saved_p, position + .4)
        torch.testing.assert_close(saved_q, quaternion)

    def test_bounded_pose_reassigns_motion_when_one_joint_saturates(self):
        jacobian = torch.tensor([[[1., 1.], [0., 1.]]], dtype=torch.float64)
        error = torch.tensor([[1., 0.]], dtype=torch.float64)
        lower, upper = torch.tensor([[-1., -1.]]), torch.tensor([[0., 1.]])
        result = helpers["bounded_pose_delta"](jacobian, error, lower, upper)
        # At q0=0, optimum q1 is 1/(2+lambda^2), not its near-zero clipped DLS value.
        torch.testing.assert_close(result, torch.tensor([[0., 1. / 2.01]], dtype=torch.float64))

    def test_bounded_pose_preserves_feasibility_and_reduces_clipped_objective(self):
        generator = torch.Generator().manual_seed(72)
        jacobian = torch.randn((16, 6, 6), generator=generator, dtype=torch.float64)
        error = torch.randn((16, 6), generator=generator, dtype=torch.float64)
        lower = -torch.rand((16, 6), generator=generator, dtype=torch.float64) * .15
        upper = torch.rand((16, 6), generator=generator, dtype=torch.float64) * .15
        hessian = jacobian.transpose(-1, -2) @ jacobian + .01 * torch.eye(6)
        rhs = jacobian.transpose(-1, -2) @ error.unsqueeze(-1)
        clipped = torch.linalg.solve(hessian, rhs).squeeze(-1).clamp(min=lower, max=upper)
        result = helpers["bounded_pose_delta"](jacobian, error, lower, upper)
        self.assertTrue(((result >= lower) & (result <= upper)).all())
        objective = lambda q: ((jacobian @ q.unsqueeze(-1)).squeeze(-1) - error).square().sum(-1) + .01*q.square().sum(-1)
        self.assertTrue((objective(result) <= objective(clipped) + 1e-10).all())
        self.assertTrue((objective(result) < objective(clipped) - .01).any())
        unconstrained = torch.linalg.solve(hessian, rhs).squeeze(-1)
        wide = helpers["bounded_pose_delta"](jacobian, error, -torch.ones_like(lower)*100, torch.ones_like(upper)*100)
        torch.testing.assert_close(wide, unconstrained)

    def test_pose_weight_reduces_position_error_for_conflicting_tasks(self):
        # One joint affects both x and pitch: the two requested errors conflict.
        jacobian = torch.zeros((1, 6, 1), dtype=torch.float64)
        jacobian[:, 0, 0] = 1.0
        jacobian[:, 4, 0] = 1.0
        position = torch.tensor([[1.0, 0.0, 0.0]], dtype=torch.float64)
        rotation = torch.tensor([[0.0, -1.0, 0.0]], dtype=torch.float64)
        full = helpers["weighted_pose_delta"](jacobian, position, rotation, orientation_weight=1.0)
        reduced = helpers["weighted_pose_delta"](jacobian, position, rotation, orientation_weight=0.25)
        self.assertLess(abs(1.0 - reduced.item()), abs(1.0 - full.item()))
        # Analytic minimizer of (q-1)^2 + .25^2*(q+1)^2 + .1^2*q^2.
        self.assertAlmostEqual(reduced.item(), (1.0 - .25**2) / (1.0 + .25**2 + .1**2), places=10)

    def test_pose_weight_matches_augmented_least_squares(self):
        generator = torch.Generator().manual_seed(71)
        jacobian = torch.randn((4, 6, 6), generator=generator, dtype=torch.float64)
        error = torch.randn((4, 6), generator=generator, dtype=torch.float64)
        for weight in (1.0, 0.25):
            scale = torch.tensor([1., 1., 1., weight, weight, weight], dtype=torch.float64)
            augmented = torch.cat((jacobian * scale[None, :, None], .1 * torch.eye(6).expand(4, 6, 6)), dim=1)
            rhs = torch.cat((error * scale, torch.zeros_like(error)), dim=1)
            expected = torch.linalg.lstsq(augmented, rhs.unsqueeze(-1)).solution.squeeze(-1)
            actual = helpers["weighted_pose_delta"](jacobian, error[:, :3], error[:, 3:], orientation_weight=weight)
            torch.testing.assert_close(actual, expected)
        for invalid in (0.0, -1.0, float("nan"), 1.1):
            with self.assertRaises(ValueError):
                helpers["weighted_pose_delta"](jacobian, error[:, :3], error[:, 3:], orientation_weight=invalid)

    def test_reach_limit_preserves_height_lateral_position_and_near_targets(self):
        target = torch.tensor([[1.8, 2.1, .13], [1.1, 2.8, .13], [1.4, 2.1, .13]])
        original = target.clone()
        base = torch.tensor([[1., 2., .28]]).repeat(3, 1)
        forward = torch.tensor([[1., 0., 0.], [0., 1., 0.], [1., 0., 0.]])
        result = helpers["bounded_push_target"](target, base, forward, maximum=.54)
        torch.testing.assert_close(result, torch.tensor([[1.54, 2.1, .13], [1.1, 2.54, .13], [1.4, 2.1, .13]]))
        torch.testing.assert_close(target, original)
        for invalid in (float("nan"), .42, .66):
            with self.assertRaises(ValueError):
                helpers["bounded_push_target"](target, base, forward, maximum=invalid)

    def test_velocity_feedback_drives_stall_brakes_overspeed_and_obeys_gap(self):
        command = torch.tensor([[0.2, 0.0, 0.1], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.2, 0.0, 0.1]])
        velocity = torch.tensor([[0.0, 0.0, 0.0], [0.4, -0.1, 0.0], [-0.1, 0.0, 0.0], [0.2, 0.0, 0.0]])
        original = command.clone()
        result = helpers["feedback_push_velocity"](command, velocity, torch.tensor([0.5, 0.5, 0.42, 0.5]), gain=2.0)
        torch.testing.assert_close(result, torch.tensor([[0.5, 0.0, 0.1], [-0.5, 0.2, 0.0], [0.0, 0.0, 0.0], [0.2, 0.0, 0.1]]))
        torch.testing.assert_close(command, original)
        torch.testing.assert_close(helpers["feedback_push_velocity"](command, velocity, torch.ones(4), gain=0.0), command)

    def test_forward_gain_preserves_separation_goal_and_reverse_commands(self):
        face = torch.tensor([[0.50, 0., 0.], [0.43, 0., 0.], [0.60, 0., 0.], [0.45, 0., 0.]])
        result = command(face, torch.zeros_like(face), torch.tensor([1., 1., 0.05, 1.]), torch.tensor([True, True, True, False]), forward_gain=2.0)
        torch.testing.assert_close(result[:, 0], torch.tensor([0.36, 0.0, 0.0, -0.04]))
        with self.assertRaises(ValueError):
            command(face, torch.zeros_like(face), torch.ones(4), torch.ones(4, dtype=torch.bool), forward_gain=2.1)

    def test_contact_memory_requires_contact_expires_and_revokes_on_separation(self):
        update = helpers["retained_push_contact"]
        near = torch.tensor([True, True, False])
        remaining, drive = update(
            torch.tensor([True, False, True]), near, torch.zeros(3), dt=0.02, memory_s=0.10,
        )
        torch.testing.assert_close(drive, torch.tensor([True, False, False]))
        for _ in range(4):
            remaining, drive = update(torch.zeros(3, dtype=torch.bool), near, remaining, dt=0.02, memory_s=0.10)
            self.assertTrue(drive[0])
        remaining, drive = update(torch.zeros(3, dtype=torch.bool), near, remaining, dt=0.02, memory_s=0.10)
        self.assertFalse(drive.any())
        remaining, drive = update(torch.zeros(3, dtype=torch.bool), torch.zeros(3, dtype=torch.bool), torch.ones(3) * 0.1, dt=0.02, memory_s=0.10)
        self.assertFalse(drive.any())
        torch.testing.assert_close(remaining, torch.zeros(3))

    def test_clearance_projection_keeps_feasible_command_and_separates_near_pair(self):
        candidate = torch.tensor([[-0.02, 0.01], [-0.02, 0.01]])
        position = torch.zeros_like(candidate)
        gradient = torch.tensor([[[1.0, 0.0]], [[1.0, 0.0]]])
        result, residual = helpers["project_clearance_target"](
            candidate, position, gradient, torch.tensor([[0.15], [0.09]]),
            position - 0.02, position + 0.02, minimum=0.10,
        )
        torch.testing.assert_close(result, torch.tensor([[-0.02, 0.01], [0.01, 0.01]]))
        torch.testing.assert_close(residual, torch.zeros(2))
        torch.testing.assert_close(candidate, torch.tensor([[-0.02, 0.01], [-0.02, 0.01]]))

    def test_clearance_projection_reports_infeasible_rate_bound_and_zero_gradient(self):
        position = torch.zeros((2, 2))
        gradient = torch.tensor([[[1.0, 0.0]], [[0.0, 0.0]]])
        result, residual = helpers["project_clearance_target"](
            position, position, gradient, torch.tensor([[0.07], [0.07]]),
            position - 0.02, position + 0.02, minimum=0.10,
        )
        self.assertTrue(torch.isfinite(result).all())
        self.assertTrue((result.abs() <= 0.02).all())
        torch.testing.assert_close(residual, torch.tensor([0.01, 0.03]))

    def test_clearance_projection_handles_multiple_pairs_and_joint_limit(self):
        position = torch.zeros((1, 2))
        gradient = torch.tensor([[[1.0, 0.0], [0.0, 1.0]]])
        result, residual = helpers["project_clearance_target"](
            torch.tensor([[-0.02, -0.02]]), position, gradient, torch.tensor([[0.09, 0.09]]),
            position - 0.02, torch.tensor([[0.01, 0.02]]), minimum=0.10,
        )
        torch.testing.assert_close(result, torch.tensor([[0.01, 0.01]]))
        torch.testing.assert_close(residual, torch.zeros(1), atol=1.0e-7, rtol=0.0)

    def test_contact_action_blend_starts_at_zero_and_reaches_one(self):
        duration = torch.tensor([0.0, 0.10, 0.35, 0.60, 3.0])
        blend = helpers["contact_action_blend"](duration, hold_time=0.10, ramp_time=0.50)
        torch.testing.assert_close(blend, torch.tensor([0.0, 0.0, 0.5, 1.0, 1.0]))

    def test_contact_servo_advances_below_target_retracts_above_and_holds_inactive(self):
        advance = torch.full((5,), 0.04)
        force = torch.tensor([0.0, 4.0, 8.0, 18.0, 0.0])
        active = torch.tensor([True, True, True, True, False])
        actual = helpers["force_limited_contact_advance"](
            advance, force, active, dt=0.02, target_force=8.0, gain=0.001, speed_limit=0.025, travel_limit=0.10,
        )
        torch.testing.assert_close(actual, torch.tensor([0.0405, 0.04008, 0.04, 0.0398, 0.04]))
        torch.testing.assert_close(advance, torch.full((5,), 0.04))

    def test_contact_confirmation_requires_continuity_and_revokes_on_loss(self):
        duration = torch.zeros(3)
        ready = torch.tensor([True, False, True])
        at_goal = torch.tensor([False, False, True])
        for index in range(5):
            duration, released = helpers["confirmed_push_contact"](
                torch.ones(3, dtype=torch.bool), ready, at_goal, duration, dt=0.02, hold_time=0.10,
            )
            torch.testing.assert_close(released, torch.tensor([index == 4, False, False]))
        duration, released = helpers["confirmed_push_contact"](
            torch.zeros(3, dtype=torch.bool), ready, at_goal, duration, dt=0.02, hold_time=0.10,
        )
        torch.testing.assert_close(duration, torch.zeros(3))
        self.assertFalse(released.any())
        _, released = helpers["confirmed_push_contact"](
            torch.ones(3, dtype=torch.bool), ready, at_goal, duration, dt=0.02, hold_time=0.10,
        )
        self.assertFalse(released.any())

    def test_ik_feedback_reduces_step_and_brakes_joint_motion(self):
        position = torch.tensor([[1.0, -1.0], [0.0, 0.0]])
        velocity = torch.tensor([[1.0, -2.0], [0.5, -0.5]])
        desired = torch.tensor([[2.0, -1.0], [0.0, 0.0]])
        original = position.clone()
        actual = helpers["stabilized_ik_target"](position, velocity, desired, gain=0.25, velocity_feedback_time=0.05)
        torch.testing.assert_close(actual, torch.tensor([[1.2, -0.9], [-0.025, 0.025]]))
        torch.testing.assert_close(position, original)

    def test_ik_feedback_rejects_invalid_gains(self):
        state = torch.zeros((1, 6))
        for gain, feedback in ((0.0, 0.0), (2.0, 0.0), (0.2, -0.1), (0.2, float("inf"))):
            with self.subTest(gain=gain, feedback=feedback), self.assertRaises(ValueError):
                helpers["stabilized_ik_target"](state, state, state, gain=gain, velocity_feedback_time=feedback)

    def test_joint_rate_limit_preserves_coordinated_direction(self):
        reference = torch.zeros((2, 2))
        desired = torch.tensor([[1.0, 0.1], [0.05, -0.02]])
        actual = helpers["coordinated_joint_target"](reference, desired, 0.1)
        torch.testing.assert_close(actual, torch.tensor([[0.1, 0.01], [0.05, -0.02]]))
        torch.testing.assert_close(reference, torch.zeros_like(reference))

    def test_approach_must_be_outside_face_at_contact_height(self):
        hands = torch.tensor([[-0.7, 0.0, 0.0], [-0.7, 0.0, 0.15], [-0.5, 0.0, 0.0], [-0.7, 0.2, 0.0], [-1.0, 0.0, 0.0]])
        ready = helpers["side_approach_ready"](hands, 0.6, 0.10)
        torch.testing.assert_close(ready, torch.tensor([True, False, False, False, False]))

    def test_approach_height_tracks_configured_contact_offset(self):
        hands = torch.tensor([[-0.7, 0.0, 0.03], [-0.7, 0.0, 0.07]])
        ready = helpers["side_approach_ready"](hands, 0.6, 0.10, target_height=0.03)
        torch.testing.assert_close(ready, torch.tensor([True, False]))

    def test_top_rear_and_wrist_contacts_are_not_push_contacts(self):
        forces = torch.tensor([[-10.0, 0.0, 0.0], [0.0, 0.0, 10.0], [10.0, 0.0, 0.0], [-10.0, 0.0, 0.0], [-10.0, 0.0, 0.0]])
        points = torch.tensor([[-0.6, 0.0, 0.0]]).expand(5, -1).clone()
        points[4, 2] = 0.125
        axes = torch.tensor([[1.0, 0.0, 0.0]]).expand(5, -1)
        contact = helpers["valid_front_contact"](forces, axes, points, torch.tensor([True, True, True, False, True]), (1.2, 1.2, 0.25))
        torch.testing.assert_close(contact, torch.tensor([True, False, False, False, False]))

    def test_low_board_front_edge_requires_zero_height_margin(self):
        force = torch.tensor([[-10.0, 0.0, 0.0]])
        axis = torch.tensor([[1.0, 0.0, 0.0]])
        point = torch.tensor([[-0.55, 0.0, 0.0400002]])
        near_tip = torch.tensor([True])
        accepted = helpers["valid_front_contact"](force, axis, point, near_tip, (1.10, 0.48, 0.08), 0.0)
        rejected = helpers["valid_front_contact"](force, axis, point, near_tip, (1.10, 0.48, 0.08), 0.01)
        torch.testing.assert_close(accepted, torch.tensor([True]))
        torch.testing.assert_close(rejected, torch.tensor([False]))

    def test_heading_feedback_turns_toward_push_direction_before_driving(self):
        faces = torch.tensor([[0.5, 0.0, 0.0]]).expand(3, -1)
        velocity = command(faces, torch.zeros_like(faces), torch.ones(3), torch.ones(3, dtype=torch.bool), torch.tensor([0.6, -0.6, 0.1]))
        torch.testing.assert_close(velocity[:, 2], torch.tensor([0.4, -0.4, 0.15]))
        torch.testing.assert_close(velocity[:, 0], torch.tensor([0.0, 0.0, 0.18]))

    def test_static_box_receives_drive_only_after_aligned_contact(self):
        faces = torch.tensor([[0.5, 0.0, 0.0], [0.5, 0.0, 0.0], [0.5, 0.2, 0.0]])
        velocity = command(faces, torch.zeros_like(faces), torch.ones(3), torch.tensor([False, True, True]))
        torch.testing.assert_close(velocity[:, 0], torch.tensor([0.0, 0.18, 0.0]))

    def test_approach_exceeds_policy_deadzone_without_forcing_small_errors(self):
        faces = torch.tensor([[0.55, 0.0, 0.0], [0.51, 0.0, 0.0]])
        velocity = command(faces, torch.zeros_like(faces), torch.ones(2), torch.zeros(2, dtype=torch.bool))
        torch.testing.assert_close(velocity[:, 0], torch.tensor([0.15, 0.008]))

    def test_contact_drive_never_overrides_separation_or_goal_stop(self):
        faces = torch.tensor([[0.40, 0.0, 0.0], [0.43, 0.0, 0.0], [0.5, 0.0, 0.0]])
        boxes = torch.tensor([[0.2, 0.0, 0.0]]).expand(3, -1)
        velocity = command(faces, boxes, torch.tensor([1.0, 1.0, 0.05]), torch.ones(3, dtype=torch.bool))
        torch.testing.assert_close(velocity, torch.zeros_like(faces))

    def test_far_approach_stays_bounded_and_input_is_not_mutated(self):
        face = torch.tensor([[1.4, -0.5, 0.0]])
        original = face.clone()
        velocity = command(face, torch.zeros_like(face), torch.ones(1), torch.zeros(1, dtype=torch.bool))
        torch.testing.assert_close(velocity, torch.tensor([[0.25, -0.12, 0.0]]))
        torch.testing.assert_close(face, original)

    def test_crossed_goal_stops_despite_lateral_error_and_box_motion(self):
        face = torch.tensor([[0.6, 0.2, 0.0]])
        velocity = command(face, torch.tensor([[0.5, 0.0, 0.0]]), torch.tensor([-0.05]), torch.tensor([True]), torch.tensor([2.0]))
        torch.testing.assert_close(velocity, torch.zeros_like(face))

    def test_low_board_approach_targets_precontact_gap(self):
        faces = torch.tensor([[0.36, 0.0, 0.0], [0.46, 0.0, 0.0], [0.30, 0.0, 0.0]])
        velocity = low_board_command(
            faces, torch.zeros_like(faces), torch.ones(3), torch.zeros(3, dtype=torch.bool),
            min_gap=0.32, approach_gap=0.36,
        )
        torch.testing.assert_close(velocity[:, 0], torch.tensor([0.0, 0.08, -0.048]))

    def test_low_board_contact_uses_slow_drive_and_respects_minimum_gap(self):
        faces = torch.tensor([[0.36, 0.0, 0.0], [0.31, 0.0, 0.0], [0.36, 0.2, 0.0]])
        velocity = low_board_command(
            faces, torch.zeros_like(faces), torch.ones(3), torch.ones(3, dtype=torch.bool),
            min_gap=0.32, approach_gap=0.36,
        )
        torch.testing.assert_close(velocity[:, 0], torch.tensor([0.12, 0.0, 0.0]))


if __name__ == "__main__":
    unittest.main()
