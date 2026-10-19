from config_cases import load_case
"""Optional flat posture refinement must leave ascent and the restored baseline intact."""
import unittest
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, PPOConfig, configuration, require_implementation,
    IMPLEMENTATION_REVISION, FLAT_STABILITY_REVISION, FLAT_SPEED_REVISION, load_config,
)
from climb_skill.tasks.direct.climb_skill.mdp.flat_stability import flat_posture_cost, flat_surface_gate, flat_speed_terms
from climb_skill.utils.checkpoint_video import checkpoint_due


class FlatRefinement(unittest.TestCase):
    def setUp(self):
        self.cfg=TaskConfig(flat_stability_weight=1.)
        self.feet=torch.tensor([[[.25,.15,.02],[.25,-.15,.02],[-.25,.15,.02],[-.25,-.15,.02]]])
        self.forces=torch.zeros_like(self.feet);self.forces[...,2]=30.
        self.gravity=torch.tensor([[.25,0.,-(1.-.25**2)**.5]])
        self.heights=torch.tensor([.2])

    def cost(self, feet=None, forces=None, gravity=None):
        return flat_posture_cost(self.feet if feet is None else feet,
            self.forces if forces is None else forces,self.gravity if gravity is None else gravity,self.heights,self.cfg)

    def test_ground_and_top_cost_but_upright_is_free(self):
        cost,gate=self.cost();self.assertGreater(float(cost),0.);self.assertEqual(float(gate),1.)
        feet=self.feet.clone();feet[...,0]+=1.5;feet[...,2]+=.2
        top,gate=self.cost(feet);torch.testing.assert_close(top,cost);self.assertEqual(float(gate),1.)
        cost,_=self.cost(gravity=torch.tensor([[0.,0.,-1.]]));self.assertEqual(float(cost),0.)

    def test_edge_approach_and_mixed_height_have_no_extra_cost(self):
        for dx in [.35,.5,.75]:
            feet=self.feet.clone();feet[...,0]+=dx
            cost,gate=self.cost(feet)
            self.assertEqual(float(cost),0.);self.assertEqual(float(gate),0.)
        # Exit edge and side edge on the platform are also excluded.
        feet=self.feet.clone();feet[...,0]+=2.8;feet[...,2]+=.2
        self.assertEqual(float(self.cost(feet)[1]),0.)
        feet=self.feet.clone();feet[...,0]+=1.5;feet[...,1]+=.3;feet[...,2]+=.2
        self.assertEqual(float(self.cost(feet)[1]),0.)

    def test_two_real_contacts_allowed_but_airborne_and_wrong_height_rejected(self):
        force=self.forces.clone();force[:,[1,2]]=0.
        self.assertEqual(float(self.cost(forces=force)[1]),1.)
        self.assertEqual(float(self.cost(forces=force*0.)[1]),0.)
        feet=self.feet.clone();feet[...,2]+=.2
        self.assertEqual(float(self.cost(feet)[1]),0.)

    def test_baseline_default_and_candidate_contract_cannot_be_mislabeled(self):
        base=configuration(TaskConfig(),PPOConfig())
        self.assertEqual(base['implementation_revision'],IMPLEMENTATION_REVISION)
        require_implementation(base)
        # Actual old v3 checkpoints did not contain the optional parameters.
        for k in list(base['task']):
            if k.startswith('flat_stability_'): del base['task'][k]
        require_implementation(base)
        candidate=configuration(self.cfg,PPOConfig())
        self.assertEqual(candidate['implementation_revision'],FLAT_STABILITY_REVISION)
        require_implementation(candidate)
        candidate['implementation_revision']=IMPLEMENTATION_REVISION
        with self.assertRaises(ValueError):require_implementation(candidate)
        for revision in ['climb_skill_v4_terrain_stability','climb_skill_v5_learning_stability']:
            with self.assertRaises(ValueError):require_implementation({'implementation_revision':revision})

    def test_speed_cost_and_progress_limit_only_on_safe_flat_surface(self):
        speed=torch.tensor([.2,.6,.9,.9])
        progress=torch.tensor([.2,.6,1.,1.])
        gate=torch.tensor([1.,1.,1.,0.])
        cost,adjusted=flat_speed_terms(speed,progress,gate,self.cfg)
        torch.testing.assert_close(cost,torch.tensor([0.,0.,.25,0.]))
        torch.testing.assert_close(adjusted,torch.tensor([.2,.6,.6,1.]))
        # Near the edge, mixed heights or airborne must preserve the entire old progress value.
        for dx in [.35,.5,.75]:
            feet=self.feet.clone();feet[...,0]+=dx
            edge_gate=flat_surface_gate(feet,self.forces,self.heights,self.cfg)
            cost,adjusted=flat_speed_terms(torch.tensor([2.]),torch.tensor([1.]),edge_gate,self.cfg)
            self.assertEqual(float(cost),0.);self.assertEqual(float(adjusted),1.)
        cost,adjusted=flat_speed_terms(torch.tensor([.9]),torch.tensor([1.]),torch.tensor([.5]),self.cfg)
        torch.testing.assert_close(cost,torch.tensor([.125]))
        torch.testing.assert_close(adjusted,torch.tensor([.8]))
        _,reverse=flat_speed_terms(torch.tensor([.9]),torch.tensor([-.4]),torch.ones(1),self.cfg)
        torch.testing.assert_close(reverse,torch.tensor([-.4]))

    def test_speed_reward_revision_is_distinct_and_old_models_still_load(self):
        self.cfg.flat_speed_weight=1.
        candidate=configuration(self.cfg,PPOConfig())
        self.assertEqual(candidate['implementation_revision'],FLAT_SPEED_REVISION)
        require_implementation(candidate)
        candidate['implementation_revision']=FLAT_STABILITY_REVISION
        with self.assertRaises(ValueError):require_implementation(candidate)
        for kwargs in [dict(flat_speed_weight=-1.),dict(flat_speed_limit=0.)]:
            with self.assertRaises(ValueError):TaskConfig(**kwargs).validate()

    def test_500_cadence_final_save_and_optional_configuration(self):
        root=Path(__file__).resolve().parents[1]
        baseline,ppo=load_case('legacy')
        candidate,cppo=load_case('legacy_flat_posture')
        self.assertEqual(ppo,cppo);self.assertEqual(ppo.save_interval,500)
        differences=[k for k in vars(baseline) if getattr(baseline,k)!=getattr(candidate,k)]
        self.assertEqual(set(differences),{'flat_stability_weight','flat_speed_weight'})
        self.assertEqual([i for i in range(1251) if checkpoint_due(i,1250,500)],[500,1000,1250])

if __name__=='__main__':unittest.main()
