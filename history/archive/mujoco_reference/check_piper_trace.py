"""Regression tests for trace provenance, time alignment and divergence metrics."""

from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from compare_piper_control_traces import compare
from trace_piper_push_hold import foot_forces, reported_root_state


class PiperTraceChecks(unittest.TestCase):
    def test_foot_forces_collect_all_four_ground_contacts(self):
        names = ("floor", "FL", "FR", "RL", "RR", "box")
        model = SimpleNamespace(geom=lambda index: SimpleNamespace(name=names[index]))
        contacts = [SimpleNamespace(geom1=0, geom2=index, frame=np.eye(3).reshape(-1), dist=-0.01) for index in range(1, 5)]
        contacts.append(SimpleNamespace(geom1=5, geom2=1, frame=np.eye(3).reshape(-1), dist=-0.01))
        data = SimpleNamespace(contact=contacts)

        def contact_force(model, data, index, wrench):
            wrench[0] = index + 1

        with patch("trace_piper_push_hold.mujoco.mj_contactForce", side_effect=contact_force):
            forces, details, forces_world = foot_forces(model, data)
        self.assertEqual(forces, {"FL": 1.0, "FR": 2.0, "RL": 3.0, "RR": 4.0})
        self.assertEqual([item["geom2"] for item in details], ["FL", "FR", "RL", "RR"])
        self.assertEqual([forces_world[name] for name in ("FL", "FR", "RL", "RR")],
                         [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0]])

    def test_foot_world_force_reverses_when_floor_is_second_geom(self):
        names = ("FL", "floor")
        model = SimpleNamespace(geom=lambda index: SimpleNamespace(name=names[index]))
        frame = np.array([[0.0, 0.0, -1.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])
        data = SimpleNamespace(contact=[SimpleNamespace(geom1=0, geom2=1, frame=frame.reshape(-1), dist=-0.01)])

        def contact_force(model, data, index, wrench):
            wrench[:3] = (5.0, 2.0, 3.0)

        with patch("trace_piper_push_hold.mujoco.mj_contactForce", side_effect=contact_force):
            forces, _, forces_world = foot_forces(model, data)
        self.assertEqual(forces["FL"], 5.0)
        np.testing.assert_allclose(forces_world["FL"], [-2.0, 3.0, 5.0])

    def test_fixed_root_uses_anchor_instead_of_joint_coordinates(self):
        data = SimpleNamespace(qpos=np.arange(18.0), qvel=np.arange(18.0))
        anchor = np.array([0.1, 0.2, 0.3, 1.0, 0.0, 0.0, 0.0])
        self.assertEqual(reported_root_state(data, anchor, True), (anchor.tolist(), [0.0] * 6))
        self.assertEqual(reported_root_state(data, anchor, False), (data.qpos[:7].tolist(), data.qvel[:6].tolist()))

    def setUp(self):
        initial = {"root_pose": [0.0, 0.0, 0.33, 1.0, 0.0, 0.0, 0.0]}
        row = {"physics_step": 0, "time": 0.005, "root_pose": initial["root_pose"],
               "target": [0.0] * 18, "torque": [0.0] * 18}
        self.local = {"joint_names": [f"joint{index}" for index in range(18)],
                      "initial_state": initial, "physics_dt": 0.005,
                      "steps": [{**row, "limited_positions": [0.0] * 18, "limited_velocities": [0.0] * 18}]}
        self.native = {"joint_names": self.local["joint_names"], "initial_state": deepcopy(initial),
                       "measured_initial_state": deepcopy(initial), "physics_dt": 0.005, "trace_sha256": "targets",
                       "steps": [{**deepcopy(row), "solver_positions": [0.0] * 18, "solver_velocities": [0.0] * 18}]}

    def test_identical_records_have_no_divergence(self):
        result = compare(self.local, self.native, "targets")
        self.assertTrue(all(value is None for value in result["first_divergence"].values()))

    def test_torque_threshold_reports_first_physics_step(self):
        self.native["steps"][0]["torque"][3] = 1.1
        result = compare(self.local, self.native, "targets")
        self.assertEqual(result["first_divergence"]["torque_nm"]["physics_step"], 0)
        self.assertAlmostEqual(result["first_divergence"]["torque_nm"]["error"], 1.1)

    def test_rejects_wrong_source(self):
        with self.assertRaisesRegex(ValueError, "target trace"):
            compare(self.local, self.native, "different-targets")

    def test_rejects_wrong_time(self):
        self.native["steps"][0]["time"] = 0.01
        with self.assertRaisesRegex(ValueError, "timestamps"):
            compare(self.local, self.native, "targets")

    def test_rejects_wrong_measured_initial_state(self):
        self.native["measured_initial_state"]["root_pose"][2] = 0.34
        with self.assertRaisesRegex(ValueError, "Measured initial-state"):
            compare(self.local, self.native, "targets")

    def test_rejects_wrong_target_sequence(self):
        self.native["steps"][0]["target"][1] = 0.1
        with self.assertRaisesRegex(ValueError, "target mismatch"):
            compare(self.local, self.native, "targets")


if __name__ == "__main__":
    unittest.main()