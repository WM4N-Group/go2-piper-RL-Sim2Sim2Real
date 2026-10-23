"""Physical regression checks for joint limits at supporting contacts."""

import unittest

import mujoco
import numpy as np

from reconfigurable_navigation.velocity_projection import project_joint_velocities


class ContactVelocityProjectionTests(unittest.TestCase):
    def make_state(self, height):
        model = mujoco.MjModel.from_xml_string(f"""
        <mujoco>
          <option timestep="0.005" gravity="0 0 0"/>
          <worldbody>
            <geom name="floor" type="plane" size="2 2 .1" condim="1"/>
            <body name="base" pos="0 0 {height}">
              <freejoint/>
              <geom type="sphere" size=".05" mass="1"/>
              <body name="foot" pos="0 0 -.3">
                <joint name="extension" type="slide" axis="0 0 1"/>
                <geom name="foot_geom" type="sphere" size=".2" mass="1" condim="1" margin=".001"/>
              </body>
            </body>
          </worldbody>
        </mujoco>
        """)
        data = mujoco.MjData(model)
        address = int(model.jnt_dofadr[model.joint("extension").id])
        data.qvel[2] = -2.0
        data.qvel[address] = 2.0
        mujoco.mj_forward(model, data)
        return model, data, np.array([address])

    def foot_vertical_velocity(self, model, data):
        jacobian = np.zeros((3, model.nv))
        mujoco.mj_jacBody(model, data, jacobian, None, model.body("foot").id)
        return float(jacobian[2] @ data.qvel)

    def test_joint_limit_preserves_support_contact(self):
        model, data, addresses = self.make_state(0.5)
        self.assertEqual(data.ncon, 1)
        self.assertAlmostEqual(self.foot_vertical_velocity(model, data), 0.0)
        project_joint_velocities(model, data, addresses, np.array([1.0]), model.opt.timestep)
        self.assertLessEqual(abs(data.qvel[addresses[0]]), 1.0 + 1.0e-9)
        self.assertGreaterEqual(self.foot_vertical_velocity(model, data), -1.0e-9)

    def test_airborne_limit_retains_mass_coupling(self):
        model, data, addresses = self.make_state(0.8)
        self.assertEqual(data.ncon, 0)
        project_joint_velocities(model, data, addresses, np.array([1.0]), model.opt.timestep)
        self.assertAlmostEqual(data.qvel[2], -1.5)
        self.assertAlmostEqual(data.qvel[addresses[0]], 1.0)

    def test_explicit_legacy_mode_reproduces_contact_regression(self):
      model, data, addresses = self.make_state(0.5)
      project_joint_velocities(model, data, addresses, np.array([1.0]), model.opt.timestep, preserve_contacts=False)
      self.assertAlmostEqual(self.foot_vertical_velocity(model, data), -0.5)


if __name__ == "__main__":
    unittest.main()