"""Regression tests for trace provenance, time alignment and divergence metrics."""

from copy import deepcopy
import unittest

from compare_piper_control_traces import compare


class PiperTraceChecks(unittest.TestCase):
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