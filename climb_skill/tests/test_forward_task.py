"""Regression tests for genuine ascent without requiring a four-foot standing gait."""

from types import SimpleNamespace
import unittest

import torch

from climb_skill.tasks.direct.climb_skill.mdp.geometry import (
    ascent_confirmation, forward_tracking_rewards, platform_ascent_geometry,
    platform_traversal_ready, top_support,
    update_top_contact_age,
)


class ForwardTask(unittest.TestCase):
    def setUp(self):
        self.cfg = SimpleNamespace(box_front=.75, box_length=2.4, box_width=1.2,
            top_margin=.06, foot_radius=.02, foot_height_tolerance=.035,
            support_force=8., top_contact_memory=.75, finish_x=1.95,
            minimum_stance_length=.30, minimum_stance_width=.16,
            traversal_seconds=.3, traversal_max_tilt=.3, traversal_arm_error=.08)
        self.heights = torch.tensor([.2])
        # FL/RR support; FR/RL swing. All four previously loaded the platform.
        self.feet = torch.tensor([[[2.2, .2, .22], [2.2, -.2, .30],
                                   [1.75, .2, .30], [1.75, -.2, .22]]])
        self.forces = torch.zeros(1, 4, 3)
        self.forces[:, [0, 3], 2] = 25.
        self.support = top_support(self.feet, self.forces, self.heights, self.cfg)
        self.ages = torch.tensor([[0., .2, .2, 0.]])
        self.root_x = torch.tensor([2.])

    def ready(self, feet=None, support=None, ages=None, root_x=None):
        return platform_traversal_ready(
            self.feet if feet is None else feet,
            self.support if support is None else support,
            self.ages if ages is None else ages,
            self.root_x if root_x is None else root_x, self.cfg, self.heights)

    def test_rest_and_reverse_cannot_collect_heading_income(self):
        forward = torch.tensor([0., -.2, .2, .4, .8])
        velocity, heading = forward_tracking_rewards(
            forward, torch.full_like(forward, .4), torch.zeros_like(forward))
        torch.testing.assert_close(velocity, torch.tensor([0., -.5, .5, 1., 1.]))
        torch.testing.assert_close(heading, torch.tensor([0., 0., .5, 1., 1.]))
        _, angled = forward_tracking_rewards(torch.tensor([.4]), torch.tensor([.4]), torch.tensor([1.]))
        torch.testing.assert_close(angled, torch.exp(torch.tensor([-1.])))

    def test_diagonal_walking_support_is_valid(self):
        self.assertEqual(self.support.sum().item(), 2)
        self.assertTrue(self.ready().item())

    def test_front_legs_only_and_old_near_lip_goal_are_invalid(self):
        feet = self.feet.clone()
        feet[:, 2:, 0] = .65
        feet[:, 2:, 2] = .02
        self.assertFalse(self.ready(feet=feet).item())
        # The completion line independently requires travelling further onto the box.
        self.assertFalse(self.ready(root_x=torch.tensor([1.17])).item())

    def test_airborne_or_single_contact_is_not_success(self):
        self.assertFalse(self.ready(support=torch.zeros_like(self.support)).item())
        one = torch.zeros_like(self.support)
        one[:, 0] = True
        self.assertFalse(self.ready(support=one).item())

    def test_never_loaded_or_stale_rear_foot_cannot_pass(self):
        for age in (float("inf"), .76):
            ages = self.ages.clone()
            ages[:, 2] = age
            self.assertFalse(self.ready(ages=ages).item())

    def test_ground_height_side_bypass_and_far_edge_are_invalid(self):
        for axis, value in ((2, .02), (1, .7), (0, 3.14)):
            feet = self.feet.clone()
            feet[:, 2, axis] = value
            self.assertFalse(self.ready(feet=feet).item(), (axis, value))

    def test_contact_memory_expires_and_reset_does_not_leak(self):
        never_loaded = torch.full((1, 4), float("inf"))
        ages = update_top_contact_age(never_loaded, self.support, .02)
        self.assertTrue(torch.isinf(ages[:, [1, 2]]).all().item())
        torch.testing.assert_close(ages[:, [0, 3]], torch.zeros(1, 2))
        self.assertFalse(self.ready(ages=ages).item())
        ages = update_top_contact_age(torch.full((1, 4), .74), torch.zeros_like(self.support), .02)
        self.assertFalse(self.ready(ages=ages).item())
        ages = update_top_contact_age(ages, torch.ones_like(self.support), .02)
        torch.testing.assert_close(ages, torch.zeros_like(ages))
        self.assertTrue(self.ready(ages=ages).item())

    def confirm(self, hold, support=None, geometry=None, tilt=.1, arm_error=.04, failure=False, dt=.1):
        if geometry is None:
            geometry = platform_ascent_geometry(self.feet, self.ages, self.root_x, self.cfg, self.heights)
        return ascent_confirmation(hold, geometry,
            self.support if support is None else support,
            torch.tensor([tilt]), torch.tensor([arm_error]), torch.tensor([failure]), self.cfg, dt)

    def test_confirmation_survives_gait_switch_but_commits_only_with_support(self):
        hold, success = self.confirm(torch.zeros(1))
        self.assertFalse(success.item())
        one = torch.zeros_like(self.support)
        one[:, 0] = True
        hold, success = self.confirm(hold, support=one)
        torch.testing.assert_close(hold, torch.tensor([.2]))
        hold, success = self.confirm(hold, support=torch.zeros_like(self.support))
        self.assertFalse(success.item())
        self.assertGreaterEqual(hold.item(), .3)
        hold, success = self.confirm(hold)
        self.assertTrue(success.item())
        # No speed input is needed: stopping or a momentary zero velocity cannot veto ascent.

    def test_stale_hind_foot_resets_confirmation(self):
        ages = self.ages.clone()
        ages[:, 2] = 1.
        geometry = platform_ascent_geometry(self.feet, ages, self.root_x, self.cfg, self.heights)
        hold, success = self.confirm(torch.tensor([.29]), geometry=geometry)
        torch.testing.assert_close(hold, torch.zeros(1))
        self.assertFalse(success.item())

    def test_posture_arm_precision_and_failure_remain_required_at_commit(self):
        for arguments in ({"tilt": .31}, {"arm_error": .09}, {"arm_error": .36}, {"failure": True}):
            hold, success = self.confirm(torch.tensor([.4]), **arguments)
            self.assertFalse(success.item(), arguments)
            if arguments.get("failure"):
                torch.testing.assert_close(hold, torch.zeros(1))

    def test_confirmation_cannot_bridge_missing_geometry_or_episode_reset(self):
        hold, _ = self.confirm(torch.tensor([.2]), geometry=torch.tensor([False]))
        torch.testing.assert_close(hold, torch.zeros(1))
        hold, success = self.confirm(hold)
        self.assertFalse(success.item())
        # A reset supplies zero hold even if the previous episode completed its window.
        hold, success = self.confirm(torch.zeros(1))
        torch.testing.assert_close(hold, torch.tensor([.1]))
        self.assertFalse(success.item())


if __name__ == "__main__":
    unittest.main()
