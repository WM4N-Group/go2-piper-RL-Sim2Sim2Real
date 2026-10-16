"""Check activity sampling, terminal snapshots and no-update rollouts on CPU."""
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

import torch

module = runpy.run_path(str(Path(__file__).parent / "rsl_rl/push_action_sampling.py"))


class Storage:
    def __init__(self):
        self.training_type, self.device = "rl", "cpu"
        self.num_envs, self.num_transitions_per_env, self.step = 4, 2, 0
        self.observations = torch.arange(8.).reshape(2, 4, 1)
        self.actions = self.observations + 10
        self.values = torch.zeros_like(self.observations)
        self.returns = self.observations + 1
        self.actions_log_prob = self.observations + 20
        self.distribution_params = (self.observations + 30, self.observations + 40)
        self.advantages = torch.ones_like(self.values) * 999

    def clear(self):
        self.step = 0

    def mini_batch_generator(self, *args, **kwargs):
        yield {k: getattr(self, k).flatten(0, 1) for k in ("observations", "actions", "values", "returns", "advantages", "actions_log_prob")}


class Algorithm:
    def __init__(self):
        self.actor = self.critic = SimpleNamespace(is_recurrent=False)
        self.symmetry = self.rnd = None
        self.is_multi_gpu = self.normalize_advantage_per_mini_batch = False
        self.num_mini_batches = 2
        self.storage = Storage()
        self.updates = 0

    def process_env_step(self, obs, rewards, dones, extras):
        self.storage.step += 1
        # Emulate readiness being cleared at an automatic terminal reset.
        extras["push_policy_action_active"].zero_()

    def update(self):
        self.updates += 1
        self.batch = next(self.storage.mini_batch_generator(2, 1))
        self.storage.clear()
        return {"value": 1., "surrogate": 2., "entropy": 3.}


def collect(algorithm, masks):
    for mask in masks:
        algorithm.process_env_step(None, None, torch.ones(4, dtype=torch.bool),
                                   {"push_policy_action_active": torch.tensor(mask)})


class SamplingChecks(unittest.TestCase):
    def test_active_view_excludes_inactive_values_and_keeps_field_alignment(self):
        storage = Storage()
        mask = torch.tensor([[True, False, True, False], [False, True, False, True]])
        storage.returns[~mask] = 1e9
        before = storage.returns.clone()
        view = module["active_storage_view"](storage, mask)
        ids = torch.tensor([0., 2., 5., 7.]).reshape(1, 4, 1)
        for name, offset in (("observations", 0), ("actions", 10), ("actions_log_prob", 20)):
            torch.testing.assert_close(getattr(view, name), ids + offset)
        torch.testing.assert_close(view.distribution_params[1], ids + 40)
        expected = (ids - ids.mean()) / ids.std()
        torch.testing.assert_close(view.advantages, expected)
        torch.testing.assert_close(storage.returns, before)

    def test_terminal_activity_is_copied_before_reset_and_update_is_filtered(self):
        algorithm = Algorithm()
        module["install_push_action_sampling"](algorithm, active_only=True)
        collect(algorithm, [[True, False, True, False], [False, True, False, True]])
        result = algorithm.update()
        torch.testing.assert_close(algorithm.batch["observations"].flatten(), torch.tensor([0., 2., 5., 7.]))
        self.assertEqual(result["push_active_fraction"], .5)
        self.assertEqual(algorithm.storage.mini_batch_generator.__self__, algorithm.storage)

    def test_fully_inactive_rollout_does_not_call_optimizer_update(self):
        algorithm = Algorithm()
        module["install_push_action_sampling"](algorithm, active_only=True)
        collect(algorithm, [[False] * 4] * 2)
        result = algorithm.update()
        self.assertEqual(algorithm.updates, 0)
        self.assertEqual(algorithm.storage.step, 0)
        self.assertEqual(result["push_skipped_update"], 1.)

    def test_control_arm_preserves_full_original_batch(self):
        algorithm = Algorithm()
        module["install_push_action_sampling"](algorithm, active_only=False)
        collect(algorithm, [[False] * 4] * 2)
        algorithm.update()
        torch.testing.assert_close(algorithm.batch["observations"].flatten(), torch.arange(8.))
        torch.testing.assert_close(algorithm.batch["advantages"], torch.ones(8, 1) * 999)

    def test_missing_mask_and_unsupported_algorithm_fail_closed(self):
        algorithm = Algorithm()
        module["install_push_action_sampling"](algorithm, active_only=True)
        with self.assertRaises(KeyError):
            algorithm.process_env_step(None, None, None, {})
        algorithm = Algorithm()
        algorithm.is_multi_gpu = True
        with self.assertRaises(ValueError):
            module["install_push_action_sampling"](algorithm, active_only=True)


if __name__ == "__main__":
    unittest.main()
