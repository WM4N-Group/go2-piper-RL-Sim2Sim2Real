"""回归腾空绕开限速、课程迟启用、短成对腾空与摆脚高度带。"""
import copy
from pathlib import Path
import unittest
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, configuration, load_config, require_implementation, WALKING_REFINEMENT_REVISION,
)
from climb_skill.tasks.direct.climb_skill.mdp.walking_refinement import (
    settled_flat_mask, early_gait_gain, swing_clearance_cost,
)
from climb_skill.tasks.direct.climb_skill.mdp.diagonal_gait import diagonal_gait_costs, diagonal_walking_mask
from climb_skill.tasks.direct.climb_skill.mdp.flat_stability import flat_surface_gate, flat_speed_terms


class WalkingRefinement(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.cfg, self.ppo = load_config(root/'configs/rtx4090-walking-refinement.json')

    def geometry(self):
        pos = torch.tensor([[0.,0.,.5], [.75,0.,.5], [1.8,0.,.7], [1.8,0.,.7]])
        feet = torch.tensor([[[.25,.15,.1],[.25,-.15,.1],[-.25,.15,.1],[-.25,-.15,.1]]]).repeat(4,1,1)
        feet[1,:,0] += .75
        feet[2:,:,0] += 1.8
        feet[2:,:,2] += .2
        landed = torch.ones(4,4,dtype=torch.bool); landed[2,2:] = False
        return pos, feet, torch.full((4,),.2), landed

    def test_airborne_speed_cost_stays_on_but_crossing_and_unlanded_top_exempt(self):
        pos,feet,h,landed = self.geometry(); cfg = self.cfg
        forces = torch.zeros_like(feet)  # 全部离地，无当前承重。
        old = flat_surface_gate(feet,forces,h,cfg,pos[:,:2])
        torch.testing.assert_close(old,torch.zeros(4))
        gate = settled_flat_mask(pos,feet,h,landed,cfg)
        torch.testing.assert_close(gate,torch.tensor([1.,0.,0.,1.]))
        cost,progress = flat_speed_terms(torch.ones(4),torch.ones(4),gate,cfg)
        self.assertTrue((cost[[0,3]] > 0).all()); self.assertTrue((cost[[1,2]] == 0).all())
        torch.testing.assert_close(progress,torch.tensor([.45,1.,1.,.45]))
        # 实际接触与否不能成为新限速gate的开关。
        feet[...,2] += .15
        torch.testing.assert_close(settled_flat_mask(pos,feet,h,landed,cfg),gate)

    def test_low_curriculum_is_gradual_and_old_branch_unchanged(self):
        cfg = self.cfg
        heights = torch.tensor([.05,.10,.15,.20])
        torch.testing.assert_close(early_gait_gain(heights,cfg),torch.tensor([.25,.625,1.,1.]))
        pos,feet,_,landed = self.geometry(); pos[:]=pos[0].clone(); feet[:]=feet[0].clone()
        torch.testing.assert_close(diagonal_walking_mask(pos,feet,heights,landed,cfg),early_gait_gain(heights,cfg))
        old = copy.deepcopy(cfg); old.walking_refinement_enabled = False
        torch.testing.assert_close(diagonal_walking_mask(pos,feet,heights,landed,old),torch.tensor([0.,0.,1.,1.]))
        cfg.flat_walk_start_height = cfg.curriculum_min_height
        torch.testing.assert_close(early_gait_gain(heights,cfg),torch.ones(4))

    def test_short_rear_and_front_hops_penalized_diagonal_transfer_allowed(self):
        cfg = self.cfg
        air = torch.tensor([[0.,0.,.03,.03],[.03,.03,0.,0.],[.1,0.,0.,.1]])
        stance = torch.where(air>0.,0.,.2)
        costs = diagonal_gait_costs(torch.ones(3),air,stance,cfg)
        torch.testing.assert_close(costs['diagonal_pair'],torch.tensor([.5,.5,0.]))
        self.assertEqual(float(costs['diagonal_sync'][2]),0.)
        old=copy.deepcopy(cfg); old.walking_refinement_enabled=False
        self.assertTrue((diagonal_gait_costs(torch.ones(3),air,stance,old)['diagonal_pair']==0).all())
        for c in diagonal_gait_costs(torch.ones(3),air*100,stance,cfg).values():
            self.assertTrue(((c>=0)&(c<=1)).all())

    def test_clearance_stance_toeoff_band_drag_and_high_swing(self):
        cfg=self.cfg; mask=torch.ones(5);h=torch.full((5,),.2)
        feet=torch.zeros(5,4,3);feet[...,2]=cfg.foot_radius
        feet[2,:,2]+=.04; feet[3,:,2]+=.18
        air=torch.full((5,4),.2);air[0]=0.;air[1]=.03
        c=swing_clearance_cost(mask,feet,h,air,cfg)
        torch.testing.assert_close(c[:3],torch.zeros(3))
        self.assertGreater(float(c[3]),float(c[4]));self.assertGreater(float(c[4]),0.)
        self.assertTrue(((c>=0)&(c<=1)).all())
        torch.testing.assert_close(swing_clearance_cost(mask*0,feet,h,air,cfg),torch.zeros(5))
        # 相同摆脚高度在箱顶不应因绝对z更高而增加成本。
        feet[:,:,0]=1.8;feet[:,:,2]+=.2
        torch.testing.assert_close(swing_clearance_cost(mask,feet,h,air,cfg),c)

    def test_contract_and_old_configuration_preserved(self):
        root=Path(__file__).resolve().parents[1];cfg,ppo=self.cfg,self.ppo
        old,oldppo=load_config(root/'configs/rtx4090-diagonal-gait.json')
        self.assertEqual(ppo,oldppo);self.assertEqual(ppo.save_interval,100)
        for k,v in vars(cfg).items():
            if not k.startswith('walking_'):self.assertEqual(v,vars(old)[k],k)
        c=configuration(cfg,ppo);require_implementation(c)
        self.assertEqual(c['implementation_revision'],WALKING_REFINEMENT_REVISION)
        self.assertEqual(c['action_dimension'],18);self.assertEqual(c['observation_dimensions']['total'],923)
        c['implementation_revision']=configuration(old,oldppo)['implementation_revision']
        with self.assertRaises(ValueError):require_implementation(c)
        for key,value in [('walking_early_gain',0.),('walking_pair_grace_seconds',float('nan')),
                          ('walking_pair_ramp_seconds',0.),('walking_clearance_weight',-1.),
                          ('walking_clearance_max',.01),('diagonal_gait_enabled',False)]:
            bad=copy.deepcopy(cfg);setattr(bad,key,value)
            with self.assertRaises(ValueError):bad.validate()


if __name__=='__main__':unittest.main()
