"""Verify joint-speed projection preserves unconstrained generalized momentum."""

import unittest

import mujoco
import numpy as np

from reconfigurable_navigation.velocity_projection import project_joint_velocities


class VelocityProjectionChecks(unittest.TestCase):
    def setUp(self):
        self.model = mujoco.MjModel.from_xml_string('<mujoco><worldbody><body><freejoint/><geom type="sphere" size="0.1" mass="2"/><body pos="0.3 0 0"><joint name="arm" axis="0 1 0"/><geom type="capsule" fromto="0 0 0 0.4 0 0" size="0.04" mass="1"/></body></body></worldbody></mujoco>')
        self.data = mujoco.MjData(self.model)
        mujoco.mj_forward(self.model, self.data)
        self.addresses = np.array([6])
        self.limits = np.array([3.0])

    def test_no_limit_violation_leaves_state_unchanged(self):
        self.data.qvel[6] = 2.0
        before_position, before_velocity = self.data.qpos.copy(), self.data.qvel.copy()
        project_joint_velocities(self.model, self.data, self.addresses, self.limits, 0.005)
        np.testing.assert_array_equal(self.data.qpos, before_position)
        np.testing.assert_array_equal(self.data.qvel, before_velocity)

    def test_positive_limit_preserves_free_base_momentum(self):
        self.check_momentum(5.0)

    def test_negative_limit_preserves_free_base_momentum(self):
        self.check_momentum(-5.0)

    def test_position_boundary_preserves_free_base_momentum(self):
        self.model.jnt_limited[1] = True
        self.model.jnt_range[1] = [-0.2, 0.2]
        self.data.qpos[7] = 0.202
        self.data.qvel[6] = 2.0
        before_velocity = self.data.qvel.copy()
        mass = np.zeros((self.model.nv, self.model.nv))
        mujoco.mj_fullM(self.model, self.data, mass)
        project_joint_velocities(self.model, self.data, self.addresses, self.limits, 0.005, position_limits=True)
        self.assertAlmostEqual(self.data.qpos[7], 0.2)
        self.assertAlmostEqual(self.data.qvel[6], 1.6)
        np.testing.assert_allclose((mass @ (self.data.qvel - before_velocity))[:6], 0.0, atol=1e-12)

    def test_infeasible_one_step_recovery_uses_speed_limit(self):
        self.model.jnt_limited[1] = True
        self.model.jnt_range[1] = [-0.2, 0.2]
        self.data.qpos[7] = 0.23
        self.data.qvel[6] = 2.0
        project_joint_velocities(self.model, self.data, self.addresses, self.limits, 0.005, position_limits=True)
        self.assertAlmostEqual(self.data.qvel[6], -3.0)
        self.assertLess(self.data.qpos[7], 0.23)

    def check_momentum(self, velocity):
        self.data.qvel[6] = velocity
        before_velocity = self.data.qvel.copy()
        mass = np.zeros((self.model.nv, self.model.nv))
        mujoco.mj_fullM(self.model, self.data, mass)
        project_joint_velocities(self.model, self.data, self.addresses, self.limits, 0.005)
        self.assertAlmostEqual(self.data.qvel[6], np.sign(velocity) * 3.0)
        impulse = mass @ (self.data.qvel - before_velocity)
        np.testing.assert_allclose(impulse[:6], 0.0, atol=1e-12)
        self.assertGreater(np.linalg.norm(self.data.qvel[:6]), 0.1)

if __name__ == "__main__":
    unittest.main()