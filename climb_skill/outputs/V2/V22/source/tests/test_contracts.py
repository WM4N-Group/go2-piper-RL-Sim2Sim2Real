"""CPU tests of failure-sensitive contracts; no Isaac Sim startup required."""

import tempfile
from pathlib import Path
import unittest

import torch

from climb_skill.tasks.direct.climb_skill.task_parameters import OBSERVATIONS, PROPRIO, SCAN, EXPLICIT, TaskConfig, PPOConfig, configuration
from climb_skill.tasks.direct.climb_skill.mdp.geometry import box_scan, constrained_actions, stable_timer, top_support
from climb_skill.learning.actor_critic import ClimbActorCritic
from climb_skill.learning.ppo import PPO, gae

torch.set_num_threads(1)


class Contracts(unittest.TestCase):
    def setUp(self):
        self.cfg = TaskConfig()

    def test_support_requires_height_load_and_edge_clearance(self):
        feet = torch.tensor([[[0.9, 0.15, 0.22], [0.9, -0.15, 0.22],
                              [1.3, 0.15, 0.22], [1.3, -0.15, 0.22]]])
        forces = torch.zeros(1, 4, 3)
        forces[..., 2] = 20.
        h = torch.tensor([0.2])
        self.assertTrue(top_support(feet, forces, h, self.cfg).all())
        for invalid in ("ground", "floating", "edge", "horizontal_force"):
            f, w = feet.clone(), forces.clone()
            if invalid == "ground": f[0, 0, 2] = 0.02
            if invalid == "floating": w[0, 0, 2] = 0.
            if invalid == "edge": f[0, 0, 0] = 0.76
            if invalid == "horizontal_force": w[0, 0] = torch.tensor([100., 0., 0.])
            self.assertFalse(top_support(f, w, h, self.cfg).all(), invalid)

    def test_stability_must_be_continuous(self):
        hold = torch.tensor([0.9, 0.9])
        hold = stable_timer(hold, torch.tensor([True, False]), 0.02)
        torch.testing.assert_close(hold, torch.tensor([0.92, 0.]))

    def test_height_scan_and_arm_mask(self):
        points = torch.tensor([[[0.5, 0.], [0.8, 0.], [1., 0.7], [self.cfg.box_front + self.cfg.box_length + .1, 0.]]])
        torch.testing.assert_close(box_scan(points, torch.tensor([0.2]), self.cfg), torch.tensor([[0., 0.2, 0., 0.]]))
        actions = torch.randn(7, 18)
        filtered = constrained_actions(actions)
        torch.testing.assert_close(filtered[:, :12], actions[:, :12])
        self.assertEqual(torch.count_nonzero(filtered[:, 12:]), 0)
        self.assertEqual(torch.count_nonzero(actions[:, 12:]), 42)

    def test_gae_terminal_and_timeout_do_not_cross_reset(self):
        # t=0 is a timeout with terminal V=5 already included; V(reset)=100 must be ignored.
        rewards = torch.tensor([[1. + 0.99 * 5.], [2.]])
        values = torch.tensor([[3.], [100.]])
        advantages, returns = gae(rewards, values, torch.tensor([[True], [True]]), torch.tensor([999.]), .99, .95)
        torch.testing.assert_close(returns, rewards)
        torch.testing.assert_close(advantages, rewards - values)

    def test_actor_uses_history_not_privileged_truth_at_inference(self):
        torch.manual_seed(3)
        model = ClimbActorCritic()
        obs = torch.randn(3, OBSERVATIONS)
        altered = obs.clone()
        altered[:, PROPRIO + SCAN:PROPRIO + SCAN + EXPLICIT + 29] = 100.
        torch.testing.assert_close(model(obs), model(altered))
        self.assertEqual(model(obs).shape, (3, 18))
        self.assertEqual(torch.count_nonzero(model(obs)[:, 12:]), 0)
        self.assertEqual(model.distribution(obs, True).sample().shape, (3, 12))
        traced = torch.jit.trace(model.eval(), torch.zeros(1, OBSERVATIONS))
        torch.testing.assert_close(traced(obs), model(obs))

    def test_ppo_updates_and_resume_preserves_optimizer_iteration(self):
        torch.manual_seed(9)
        cfg = PPOConfig(epochs=1, minibatches=2)
        model = ClimbActorCritic()
        algorithm = PPO(model, cfg)
        obs = torch.randn(8, OBSERVATIONS)
        with torch.no_grad():
            dist = model.distribution(obs, True)
            actions = dist.sample()
            batch = {"obs": obs, "actions": actions, "logp": dist.log_prob(actions).sum(-1),
                     "values": model.value(obs), "mu": dist.mean, "std": dist.stddev,
                     "advantages": torch.randn(8), "returns": torch.randn(8), "policy_active": torch.ones(8,dtype=torch.bool)}
        before = model.actor[-1].weight.detach().clone()
        logs = algorithm.update(batch, True)
        self.assertTrue(all(torch.isfinite(torch.tensor(v)) for v in logs.values()))
        self.assertFalse(torch.equal(before, model.actor[-1].weight))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.pt"
            algorithm.save(path, configuration(self.cfg, cfg), [2, 3])
            restored = PPO(ClimbActorCritic(), cfg)
            payload = restored.load(path)
            self.assertEqual(restored.iteration, 1)
            self.assertEqual(payload["curriculum_levels"], [2, 3])
            torch.testing.assert_close(restored.model(obs), model(obs))
            self.assertEqual(len(restored.history_optimizer.state), len(algorithm.history_optimizer.state))


if __name__ == "__main__":
    unittest.main()
