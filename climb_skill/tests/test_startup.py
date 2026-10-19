import unittest
from types import SimpleNamespace
import torch
from climb_skill.tasks.direct.climb_skill.mdp.startup import movement_gain, standing_transition
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, PPOConfig, configuration, require_implementation, STARTUP_REVISION,
)


class Startup(unittest.TestCase):
    def test_waits_for_minimum_time_and_continuous_stability_then_ramps(self):
        cfg = TaskConfig(startup_stand_seconds=1.)
        elapsed = torch.zeros(2); hold = elapsed.clone()
        ready = torch.zeros(2,dtype=torch.bool); release = torch.full((2,),float('inf'))
        for _ in range(9):
            elapsed,hold,ready,release,failed = standing_transition(
                elapsed,hold,ready,release,torch.tensor([True,False]),cfg,.1)
        self.assertFalse(ready.any())
        elapsed,hold,ready,release,failed = standing_transition(
            elapsed,hold,ready,release,torch.tensor([True,False]),cfg,.1)
        self.assertEqual(ready.tolist(),[True,False])
        env = SimpleNamespace(task=cfg,num_envs=2,device='cpu',startup_elapsed=elapsed,
                              startup_release_time=release,startup_ready=ready)
        torch.testing.assert_close(movement_gain(env),torch.zeros(2))
        env.startup_elapsed = elapsed + .4
        torch.testing.assert_close(movement_gain(env),torch.tensor([.5,0.]))
        env.startup_elapsed = elapsed + 2.
        torch.testing.assert_close(movement_gain(env),torch.tensor([1.,0.]))

    def test_unstable_window_resets_and_timeout_fails(self):
        cfg = TaskConfig(startup_stand_seconds=1.)
        elapsed,hold,ready,release,failed = standing_transition(
            torch.tensor([1.,3.]),torch.tensor([.2,.2]),torch.tensor([False,False]),
            torch.full((2,),float('inf')),torch.tensor([False,False]),cfg,.02)
        self.assertEqual(hold.tolist(),[0.,0.]);self.assertEqual(failed.tolist(),[False,True])

    def test_old_task_unchanged_and_revision_distinct(self):
        env=SimpleNamespace(task=TaskConfig(),num_envs=2,device='cpu')
        torch.testing.assert_close(movement_gain(env),torch.ones(2))
        c=configuration(TaskConfig(startup_stand_seconds=1.),PPOConfig())
        self.assertEqual(c['implementation_revision'],STARTUP_REVISION);require_implementation(c)
        c['task'].pop('startup_stand_seconds')
        with self.assertRaises(ValueError):require_implementation(c)
        for kw in [dict(startup_stand_seconds=-1),dict(startup_stand_seconds=1,startup_timeout=.5),
                   dict(startup_stand_seconds=1,startup_ramp_seconds=0)]:
            with self.assertRaises(ValueError):TaskConfig(**kw).validate()
