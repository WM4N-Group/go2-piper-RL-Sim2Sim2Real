from config_cases import load_case
import unittest
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    load_config, configuration, require_implementation, FORWARD_RECOVERY_REVISION,
)
from climb_skill.tasks.direct.climb_skill.mdp.flat_walking import walking_quality_curriculum, path_deviation_cost
from climb_skill.tasks.direct.climb_skill.mdp.geometry import forward_tracking_rewards


class ForwardRecovery(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]
        self.cfg,self.ppo=load_case('legacy_forward_recovery')
        self.base,_=load_case('legacy_heading_strong')

    def test_original_forward_reward_and_heading_contract_restored(self):
        self.assertFalse(self.cfg.flat_walk_velocity_tracking)
        self.assertFalse(self.cfg.straight_tracking_enabled)
        self.assertEqual(self.cfg.rewards,self.base.rewards)
        self.assertEqual(self.cfg.forward_heading_weight,self.base.forward_heading_weight)
        speed=torch.tensor([.0,.05,.2,.4])
        reward,_=forward_tracking_rewards(speed,torch.full_like(speed,.4),torch.zeros_like(speed))
        torch.testing.assert_close(reward,torch.tensor([0.,.125,.5,1.]))

    def test_quality_only_after_height_promotion_and_only_flat(self):
        heights=torch.tensor([.05,.125,.15,.2,.2])
        mask=torch.tensor([1.,1.,1.,1.,0.])
        torch.testing.assert_close(walking_quality_curriculum(mask,heights,self.cfg),
                                   torch.tensor([0.,0.,1.,1.,0.]))
        self.assertEqual(self.cfg.flat_walk_flight_weight,.5)
        self.assertEqual(self.cfg.flat_walk_vertical_weight,0.)
        self.assertEqual(self.cfg.flat_walk_mirror_weight,0.)
        self.assertEqual(self.cfg.flat_walk_air_variance_weight,0.)

    def test_heading_and_path_are_not_conflicting_rate_constraints(self):
        pos=torch.tensor([[0.,0.,.3],[1.,.03,.3],[1.,.23,.3]])
        torch.testing.assert_close(path_deviation_cost(pos),torch.tensor([0.,0.,1.]))
        self.assertEqual(self.ppo.save_interval,100)
        c=configuration(self.cfg,self.ppo);require_implementation(c)
        self.assertEqual(c['implementation_revision'],FORWARD_RECOVERY_REVISION)
        c['implementation_revision']='climb_skill_v3_flat_walk_straight_candidate'
        with self.assertRaises(ValueError):require_implementation(c)

    def test_current_low_course_video_stays_valid(self):
        self.cfg.box_height=.05
        self.cfg.curriculum_min_height=.05
        self.cfg.validate()
        torch.testing.assert_close(walking_quality_curriculum(torch.ones(1),torch.tensor([.05]),self.cfg),
                                   torch.zeros(1))
