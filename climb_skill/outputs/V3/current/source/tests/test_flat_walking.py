import math
from pathlib import Path
import unittest
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, load_config, configuration, require_implementation, FLAT_WALK_REVISION,
)
from climb_skill.tasks.direct.climb_skill.mdp.flat_walking import (
    flat_walking_mask, flat_walking_costs, flat_velocity_tracking, straight_tracking_costs,
)


class FlatWalking(unittest.TestCase):
    def test_flat_flight_cannot_disable_its_own_cost_but_step_jump_is_free(self):
        cfg=TaskConfig();h=torch.tensor([.2])
        pos=torch.tensor([[0.,0.,.5],[.75,0.,.5],[1.8,0.,.7]])
        feet=torch.tensor([[[.25,.15,.30],[.25,-.15,.30],[-.25,.15,.30],[-.25,-.15,.30]]]).repeat(3,1,1)
        feet[1,:,0]+=.5;feet[2,:,0]+=1.8;feet[2,:,2]+=.2
        mask=flat_walking_mask(pos,feet,h.repeat(3),cfg)
        torch.testing.assert_close(mask,torch.tensor([1.,0.,1.]))
        costs=flat_walking_costs(mask,torch.zeros(3,4,3),torch.ones(3),torch.zeros(3,18),
                                torch.zeros(3,4),torch.zeros(3,4),torch.zeros(3,4))
        torch.testing.assert_close(costs['flat_walk_flight'],mask)
        torch.testing.assert_close(costs['flat_walk_vertical'],mask)

    def test_diagonal_support_allowed_and_mirror_is_a_soft_cost(self):
        forces=torch.zeros(1,4,3);forces[:,[0,3],2]=30.
        q=torch.zeros(1,18);q[:,[0,9]]=1.
        c=flat_walking_costs(torch.ones(1),forces,torch.zeros(1),q,
            torch.zeros(1,4),torch.zeros(1,4),torch.zeros(1,4))
        self.assertEqual(float(c['flat_walk_flight']),0.)
        self.assertEqual(float(c['flat_walk_mirror']),0.)
        q[:,9]=0.
        self.assertGreater(float(flat_walking_costs(torch.ones(1),forces,torch.zeros(1),q,
            torch.zeros(1,4),torch.zeros(1,4),torch.zeros(1,4))['flat_walk_mirror']),0.)

    def test_velocity_tracking_has_no_rest_income_or_sprint_advantage(self):
        velocity=torch.tensor([[0.,0.],[.4,0.],[1.2,0.],[.4,.4]])
        r=flat_velocity_tracking(velocity,torch.full((4,),.4))
        self.assertEqual(float(r[0]),0.);self.assertEqual(float(r[1]),1.)
        self.assertLess(float(r[2]),float(r[1]));self.assertLess(float(r[3]),float(r[1]))

    def test_heading_position_and_corrective_motion_are_distinct(self):
        pos=torch.tensor([[0.,0.,.3],[0.,.1,.3]])
        yaw=torch.tensor([math.radians(10),0.])
        costs=straight_tracking_costs(pos,yaw,torch.tensor([0.,-.1]),torch.tensor([-1.5*math.radians(10),0.]))
        torch.testing.assert_close(costs['straight_heading'],torch.tensor([1.,0.]))
        self.assertGreater(float(costs['straight_path'][1]),0.)
        torch.testing.assert_close(costs['straight_lateral_velocity'],torch.zeros(2))
        torch.testing.assert_close(costs['straight_yaw_rate'],torch.zeros(2))

    def test_candidate_revision_and_video_contract(self):
        root=Path(__file__).resolve().parents[1]
        cfg,ppo=load_config(root/'configs/rtx4090-flat-walk.json')
        c=configuration(cfg,ppo);require_implementation(c)
        self.assertEqual(c['implementation_revision'],FLAT_WALK_REVISION)
        self.assertEqual(ppo.save_interval,100);self.assertEqual(c['observation_dimensions']['total'],923)
        self.assertEqual(c['action_dimension'],18);self.assertTrue(cfg.flat_ignore_edge_distance)
        self.assertEqual(cfg.rewards['feet_edge'],0.)
        c['implementation_revision']='climb_skill_v3_heading_strong_no_edge_candidate'
        with self.assertRaises(ValueError):require_implementation(c)


if __name__=='__main__':unittest.main()
