"""Check PIPER self-contact monitoring against the compiled collision model."""

import unittest
from unittest.mock import patch

import mujoco
import numpy as np
import torch

from reconfigurable_navigation.piper_box_runtime import make_episode


class PiperBoxCollisionTests(unittest.TestCase):
    def make_runtime(self, skill="climb", substeps=1, push_height_offset=0.0):
        with patch("reconfigurable_navigation.climb_runtime.torch.jit.load", return_value=torch.nn.Identity()):
            return make_episode(
                skill, "unused.pt", 503, native_collisions=True, constraint_substeps=substeps,
                push_height_offset=push_height_offset,
            )

    def test_nominal_pose_has_no_self_contact(self):
        for skill in ("push", "climb"):
            with self.subTest(skill=skill):
                runtime = self.make_runtime(skill)
                runtime.on_safety_step()
                self.assertIsNone(runtime.self_collision)

    def test_push_approach_state_uses_configured_height_offset(self):
        runtime = self.make_runtime("push", push_height_offset=0.03)
        arm = runtime.arm
        center = runtime.data.geom_xpos[arm.box_geom].copy()
        rotation = arm.box_rotation()

        def world_position(local):
            return center + rotation @ np.asarray(local)

        with patch.object(
            arm,
            "hand_position",
            side_effect=(
                world_position((-0.65, 0.0, 0.03)),
                world_position((-0.60, 0.0, 0.085)),
            ),
        ):
            arm.hand_target()
            self.assertTrue(arm.approached)
            arm.hand_target()
            self.assertTrue(arm.approached)

    def test_monitor_runs_for_every_solver_substep(self):
        runtime = self.make_runtime(substeps=2)
        runtime._simulate_target(runtime.default_qpos)
        self.assertEqual(runtime.collision_checks, runtime.decimation * 2)

    def test_arm_is_visible_with_default_renderer_options(self):
        runtime = self.make_runtime()
        options = mujoco.MjvOption()
        for name in ("Piper", "link1", "link2", "link3", "link4", "link5", "link6"):
            body = runtime.model.body(name).id
            geoms = np.flatnonzero(runtime.model.geom_bodyid == body)
            self.assertTrue(any(options.geomgroup[runtime.model.geom_group[index]] for index in geoms), name)

    def test_safe_partial_arm_step_is_not_discarded(self):
        runtime = self.make_runtime("push")
        arm = runtime.arm
        target = runtime.data.qpos[arm.arm_qpos].copy()
        target[0] += 0.01

        def partial_target(desired):
            arm.collision_blocked = True
            return target.copy()

        with patch.object(arm, "_collision_safe_target", side_effect=partial_target):
            arm.apply(np.zeros(12))
        np.testing.assert_allclose(arm.reference, target, atol=1.0e-10)

    def test_locked_reference_cannot_override_safe_projection(self):
        runtime = self.make_runtime("push")
        arm = runtime.arm
        target = runtime.data.qpos[arm.arm_qpos].copy()
        target[0] += 0.01
        arm.locked = True
        arm.motion_ready = True
        arm.locked_reference = target + 0.2

        def partial_target(desired):
            arm.collision_blocked = True
            return target.copy()

        with patch.object(arm, "_collision_safe_target", side_effect=partial_target):
            actions = arm.apply(np.ones(12))
        self.assertFalse(arm.locked)
        self.assertFalse(arm.motion_ready)
        np.testing.assert_allclose(arm.reference, target, atol=1.0e-10)
        np.testing.assert_array_equal(actions[:12], np.zeros(12))

    def test_arm_collision_is_latched_after_leaving_contact(self):
        runtime = self.make_runtime()
        model, data = runtime.model, runtime.data
        initial = data.qpos.copy()
        arm_positions = runtime.joint_qpos_adr[12:]
        joints = model.dof_jntid[runtime.joint_dof_adr[12:]]
        limits = model.jnt_range[joints]
        generator = np.random.default_rng(7)
        for candidate in generator.uniform(limits[:, 0], limits[:, 1], size=(64, 6)):
            data.qpos[arm_positions] = candidate
            mujoco.mj_forward(model, data)
            runtime.on_safety_step()
            if runtime.self_collision is not None:
                break
        self.assertIsNotNone(runtime.self_collision)
        first = runtime.self_collision.copy()
        data.qpos[:] = initial
        mujoco.mj_forward(model, data)
        runtime.on_safety_step()
        self.assertEqual(runtime.self_collision, first)


if __name__ == "__main__":
    torch.set_num_threads(1)
    unittest.main()