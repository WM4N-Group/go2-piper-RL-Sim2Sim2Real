from config_cases import load_case
import unittest
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    load_config, configuration, require_implementation, STRONG_HEADING_REVISION, PPOConfig,
)
from climb_skill.tasks.direct.climb_skill.mdp.flat_stability import flat_surface_gate
from climb_skill.utils.checkpoint_video import checkpoint_due


class StrongHeading(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
        self.cfg,self.ppo=load_case('legacy_heading_strong')

    def test_no_edge_distance_gate_on_ground_or_top(self):
        feet=torch.tensor([[[.70,.15,.02],[.70,-.15,.02],[.2,.15,.02],[.2,-.15,.02]]])
        f=torch.zeros_like(feet);f[...,2]=30.;h=torch.tensor([.2])
        self.assertEqual(float(flat_surface_gate(feet,f,h,self.cfg)),1.)
        # Four feet near side edges on top still receive the constraints.
        feet[...,0]+=.8;feet[...,1]*=3.8;feet[...,2]+=.2
        self.assertEqual(float(flat_surface_gate(feet,f,h,self.cfg)),1.)
        # Mixed-height step and flight retain freedom.
        feet[:,2,0]=.5;feet[:,2,2]=.02
        self.assertEqual(float(flat_surface_gate(feet,f,h,self.cfg)),0.)
        self.assertEqual(float(flat_surface_gate(feet,f*0,h,self.cfg)),0.)

    def test_weights_revision_and_100_video_cadence(self):
        old,_=load_case('legacy_forward_quality')
        self.assertEqual(self.cfg.rewards['feet_edge'],0.)
        self.assertEqual(self.cfg.forward_heading_weight,2*old.forward_heading_weight)
        self.assertAlmostEqual(self.cfg.target_curvature_weight,3*old.target_curvature_weight)
        self.assertAlmostEqual(self.cfg.contact_slip_weight,3*old.contact_slip_weight)
        self.assertEqual(self.ppo.save_interval,100)
        self.assertEqual(PPOConfig().save_interval,100)
        self.assertEqual([i for i in range(251) if checkpoint_due(i,250,100)],[100,200,250])
        c=configuration(self.cfg,self.ppo);require_implementation(c)
        self.assertEqual(c['implementation_revision'],STRONG_HEADING_REVISION)
