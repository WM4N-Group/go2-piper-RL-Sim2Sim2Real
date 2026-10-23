"""Validate equal weighting of successes, failures and incomplete trials."""

import unittest

import torch

from box_evaluation_metrics import EpisodeHistory, EpisodeQuota, JointMotionTelemetry


class EvaluationChecks(unittest.TestCase):
    def test_history_wraps_per_environment_and_copies_mutable_state(self):
        history = EpisodeHistory(2, 3, "cpu")
        for step in range(6):
            value = torch.tensor([[step, step + 10], [100 + step, 200 + step]], dtype=torch.float32)
            history.append(torch.tensor([True, step % 2 == 0]),
                           position=value, ready=torch.tensor([True, False]),
                           elapsed_seconds=torch.full((2,), step * .02))
            value.fill_(-999)  # Simulator buffers are reused in place.
        a, b = history.snapshot(0), history.snapshot(1)
        self.assertEqual([s["position"][0] for s in a], [3, 4, 5])
        self.assertEqual([s["position"][0] for s in b], [100, 102, 104])
        self.assertTrue(all(s["ready"] for s in a))
        self.assertFalse(any(s["ready"] for s in b))
        self.assertEqual(history.fields["position"].shape, (3, 2, 2))

    def test_failure_history_matches_quota_and_survives_resets(self):
        quota = EpisodeQuota(3, 2, "cpu")
        history = EpisodeHistory(3, 4, "cpu")
        names = ["time_out", "box_settled", "invalid_hand_contact"]
        history.append(quota.active, value=torch.tensor([10, 20, 30]))
        # A goal flag overlapping safety failure remains a failed episode.
        flags = torch.tensor([[True, True, False], [False, True, True], [True, False, False]])
        states = quota.terminal_snapshot(torch.arange(3), termination_flags=flags)
        failed = history.finish(states, names, first_terminal_index=17)
        self.assertEqual([(s["env_id"], s["terminal_state_index"]) for s in failed], [(1, 18), (2, 19)])
        self.assertTrue(all(s["episode"] == 1 for s in failed))
        quota.record(torch.ones(3, dtype=torch.bool), torch.tensor([True, False, False]))
        self.assertTrue(all(history.snapshot(i) == [] for i in range(3)))
        history.append(quota.active, value=torch.tensor([40, 50, 60]))
        next_states = quota.terminal_snapshot(torch.tensor([1]), termination_flags=flags)
        next_failed = history.finish(next_states, names, first_terminal_index=20)
        self.assertEqual(next_failed[0]["episode"], 2)
        self.assertEqual(next_failed[0]["pre_step_samples"], [{"value": 50}])
        self.assertEqual(failed[0]["pre_step_samples"], [{"value": 20}])
        self.assertEqual(history.snapshot(0), [{"value": 40}])
        quota.record(torch.tensor([False, True, False]), torch.zeros(3, dtype=torch.bool))
        # Finished env1 does not acquire history from later automatic resets.
        history.append(quota.active, value=torch.tensor([70, 80, 90]))
        self.assertEqual(history.snapshot(1), [])
        self.assertEqual(quota.terminal_snapshot(torch.tensor([1]), termination_flags=flags), [])

    def test_history_rejects_schema_changes_without_partial_writes(self):
        for dimensions in [(0, 3), (2, 0)]:
            with self.assertRaises(ValueError):
                EpisodeHistory(*dimensions, "cpu")
        history = EpisodeHistory(2, 2, "cpu")
        active = torch.ones(2, dtype=torch.bool)
        history.append(active, scalar=torch.tensor([1., 2.]))
        before = history.snapshot(0)
        for fields in [{}, {"other": torch.ones(2)}, {"scalar": torch.ones(2, 2)}, {"scalar": torch.ones(2, dtype=torch.long)}]:
            with self.assertRaises(ValueError):
                history.append(active, **fields)
            self.assertEqual(history.snapshot(0), before)
        with self.assertRaises(ValueError):
            history.append(torch.ones(2), scalar=torch.ones(2))

    def test_fast_failures_do_not_outweigh_slow_success(self):
        quota = EpisodeQuota(2, 1, "cpu")
        for _ in range(5):
            quota.record(torch.tensor([True, False]), torch.tensor([False, False]))
        quota.record(torch.tensor([True, True]), torch.tensor([False, True]))
        torch.testing.assert_close(quota.completed, torch.tensor([1, 1]))
        torch.testing.assert_close(quota.successful, torch.tensor([0, 1]))
        self.assertFalse(quota.active.any())

    def test_incomplete_trials_remain_distinct(self):
        quota = EpisodeQuota(2, 2, "cpu")
        quota.record(torch.tensor([True, False]), torch.tensor([True, True]))
        torch.testing.assert_close(quota.completed, torch.tensor([1, 0]))
        torch.testing.assert_close(quota.successful, torch.tensor([1, 0]))
        self.assertTrue(quota.active.all())

    def test_terminal_snapshot_survives_reset_and_ignores_finished_envs(self):
        quota = EpisodeQuota(2, 1, "cpu")
        quota.record(torch.tensor([True, False]), torch.tensor([True, False]))
        position = torch.tensor([[0.0, 0.0], [1.6, 0.1]])
        snapshot = quota.terminal_snapshot(torch.tensor([0, 1]), box_position=position)
        position.zero_()
        quota.record(torch.tensor([True, True]), torch.tensor([True, True]))
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]["env_id"], 1)
        self.assertEqual(snapshot[0]["episode"], 1)
        torch.testing.assert_close(torch.tensor(snapshot[0]["box_position"]), torch.tensor([1.6, 0.1]))
        self.assertEqual(quota.terminal_snapshot(torch.tensor([0, 1]), box_position=position), [])

    def test_motion_metrics_follow_active_environments_and_reset_targets(self):
        motion = JointMotionTelemetry(torch.tensor([[0.2, -0.1], [0.0, 0.0]]), step_dt=0.02)
        motion.sample(
            torch.tensor([True, False]),
            torch.tensor([[0.2, -0.1], [9.0, 9.0]]),
            torch.tensor([[2.0, -3.0], [99.0, 99.0]]),
            torch.tensor([[4.0, -5.0], [99.0, 99.0]]),
            torch.tensor([[9.8, -2.0], [99.0, 99.0]]),
            torch.tensor([[10.0, 10.0], [10.0, 10.0]]),
            torch.tensor([[3.0, 4.0, 0.0], [99.0, 99.0, 0.0]]),
        )
        motion.reset_reference(torch.tensor([True, False]), torch.tensor([[1.0, 1.0], [0.0, 0.0]]))
        motion.sample(
            torch.tensor([True, False]),
            torch.tensor([[1.1, 1.0], [9.0, 9.0]]),
            torch.zeros(2, 2), torch.zeros(2, 2), torch.zeros(2, 2),
            torch.ones(2, 2), torch.zeros(2, 3),
        )
        summary = motion.summary()
        torch.testing.assert_close(torch.tensor(summary["max_abs_joint_target_step"]), torch.tensor([0.1, 0.0]))
        torch.testing.assert_close(torch.tensor(summary["max_abs_joint_velocity"]), torch.tensor([2.0, 3.0]))
        torch.testing.assert_close(torch.tensor(summary["max_abs_joint_acceleration"]), torch.tensor([4.0, 5.0]))
        torch.testing.assert_close(torch.tensor(summary["max_abs_joint_mechanical_power"]), torch.tensor([19.6, 6.0]))
        torch.testing.assert_close(torch.tensor(summary["torque_saturation_seconds_per_env_joint"]), torch.tensor([[0.02, 0.0], [0.0, 0.0]]))
        torch.testing.assert_close(torch.tensor(summary["max_base_angular_speed_xy_per_env"]), torch.tensor([5.0, 0.0]))


if __name__ == "__main__":
    unittest.main()
