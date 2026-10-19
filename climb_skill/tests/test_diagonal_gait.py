from config_cases import load_case
import copy
from pathlib import Path
import unittest
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, load_config, configuration, require_implementation, DIAGONAL_GAIT_REVISION,
)
from climb_skill.tasks.direct.climb_skill.mdp.diagonal_gait import (
    diagonal_gait_costs, diagonal_walking_mask,
)


class DiagonalGait(unittest.TestCase):
    def setUp(self):
        self.cfg = TaskConfig()

    def costs(self, air, stance, mask=1.):
        return diagonal_gait_costs(torch.tensor([mask]), torch.tensor([air]),
                                   torch.tensor([stance]), self.cfg)

    def test_both_diagonal_phases_and_short_transfer_are_free(self):
        patterns = [([.2,0.,0.,.2], [0.,.2,.2,0.]),
                    ([0.,.2,.2,0.], [.2,0.,0.,.2]),
                    ([0.,0.,0.,0.], [.04,.24,.24,.04]),
                    ([0.,0.,0.,.2], [.03,.2,.2,0.])]
        for air, stance in patterns:
            for cost in self.costs(air, stance).values():
                self.assertEqual(float(cost), 0.)

    def test_front_rear_flight_and_pace_rejected_symmetrically(self):
        for air, stance in [([.2,.2,0.,0.],[0.,0.,.2,.2]),
                            ([0.,0.,.2,.2],[.2,.2,0.,0.]),
                            ([.2,.2,.2,.2],[0.,0.,0.,0.])]:
            self.assertEqual(float(self.costs(air, stance)['diagonal_pair']),1.)
        c=self.costs([.2,0.,.2,0.],[0.,.2,0.,.2])
        self.assertEqual(float(c['diagonal_sync']),1.)

    def test_standing_or_holding_same_diagonal_is_not_an_escape(self):
        for air, stance in [([0.,0.,0.,0.],[1.,1.,1.,1.]),
                            ([1.,0.,0.,1.],[0.,1.,1.,0.])]:
            self.assertGreater(float(self.costs(air, stance)['diagonal_duration']),0.)
        # Changing phase inside the generous limits is free.
        for air, stance in [([.25,0.,0.,.25],[0.,.25,.25,0.]),
                            ([0.,.25,.25,0.],[.25,0.,0.,.25])]:
            self.assertEqual(float(self.costs(air,stance)['diagonal_duration']),0.)

    def test_short_loss_of_contact_has_grace_and_costs_are_bounded(self):
        for cost in self.costs([.02,.02,0.,0.],[0.,0.,.2,.2]).values():
            self.assertEqual(float(cost),0.)
        for cost in self.costs([100.,100.,100.,100.],[0.,0.,0.,0.]).values():
            self.assertTrue(0 <= float(cost) <= 1)

    def test_step_jump_and_unlanded_top_exempt_but_flat_flight_not(self):
        cfg=self.cfg; heights=torch.full((4,),.2)
        pos=torch.tensor([[0.,0.,.5],[.75,0.,.5],[1.8,0.,.7],[1.8,0.,.7]])
        feet=torch.tensor([[[.25,.15,.3],[.25,-.15,.3],[-.25,.15,.3],[-.25,-.15,.3]]]).repeat(4,1,1)
        feet[1,:,0]+=.5; feet[2:,:,0]+=1.8; feet[2:,:,2]+=.2
        landed=torch.ones(4,4,dtype=torch.bool);landed[2,2:]=False
        mask=diagonal_walking_mask(pos,feet,heights,landed,cfg)
        torch.testing.assert_close(mask,torch.tensor([1.,0.,0.,1.]))
        costs=diagonal_gait_costs(mask,torch.full((4,4),.2),torch.zeros(4,4),cfg)
        torch.testing.assert_close(costs['diagonal_pair'],mask)

    def test_old_contract_unchanged_and_new_config_only_adds_gait(self):
        root=Path(__file__).resolve().parents[1]
        cfg,ppo=load_case('legacy_diagonal_gait')
        base,oldppo=load_case('legacy_forward_recovery')
        c=configuration(cfg,ppo);require_implementation(c)
        self.assertEqual(c['implementation_revision'],DIAGONAL_GAIT_REVISION)
        self.assertEqual(c['observation_dimensions']['total'],923)
        self.assertEqual(c['action_dimension'],18)
        self.assertEqual(ppo,oldppo);self.assertEqual(ppo.save_interval,100)
        a=copy.deepcopy(vars(cfg));b=vars(base)
        for key in a:
            if not key.startswith('diagonal_'):self.assertEqual(a[key],b[key],key)
        self.assertFalse(base.diagonal_gait_enabled)
        self.assertEqual(cfg.rewards['feet_edge'],0.)
        c['implementation_revision']=configuration(base,oldppo)['implementation_revision']
        with self.assertRaises(ValueError):require_implementation(c)

    def test_invalid_parameters_and_low_course_recording(self):
        for key,value in [('diagonal_pair_weight',-1.),('diagonal_transfer_seconds',0.),
                          ('diagonal_max_stance_seconds',.02),('diagonal_max_swing_seconds',float('nan'))]:
            cfg=TaskConfig();setattr(cfg,key,value)
            with self.assertRaises(ValueError):cfg.validate()
        cfg=TaskConfig(diagonal_gait_enabled=True)
        with self.assertRaises(ValueError):cfg.validate()
        cfg.flat_walking_enabled=True;cfg.flat_walk_start_height=.15
        cfg.box_height=.05;cfg.validate()


if __name__ == '__main__':unittest.main()
