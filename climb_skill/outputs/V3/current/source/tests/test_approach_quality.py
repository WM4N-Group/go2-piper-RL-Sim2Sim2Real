import unittest
from pathlib import Path
from types import SimpleNamespace
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import load_config, configuration
from climb_skill.tasks.direct.climb_skill.mdp.approach_quality import ApproachQuality, front_clearance

ROOT = Path(__file__).resolve().parents[1]

class ApproachTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.ppo = load_config(ROOT/'configs/rtx4090-approach-quality.json')
        self.q = ApproachQuality(3, 'cpu', self.cfg)

    def fill(self, cost=.1, speed=.4, legs=None):
        for phase, duration in [(0, 1.), (1, .5)]:
            self.q.accumulate(torch.full((3,), cost),
                torch.full((3,4), cost) if legs is None else legs,
                torch.full((3,),phase), torch.ones(3,dtype=torch.bool),
                torch.full((3,),speed), duration)

    def test_both_phases_and_motion_required(self):
        self.q.accumulate(torch.zeros(3),torch.zeros(3,4),torch.zeros(3,dtype=torch.long),
                          torch.ones(3,dtype=torch.bool),torch.full((3,),.4),10.)
        self.assertFalse(self.q.passed().any())
        self.q.reset(torch.arange(3)); self.fill(speed=0.)
        self.assertFalse(self.q.passed().any())
        self.q.reset(torch.arange(3)); self.fill()
        self.assertTrue(self.q.passed().all())

    def test_one_bad_hind_leg_cannot_hide_in_average(self):
        legs=torch.full((3,4),.1);legs[:,3]=.7
        self.fill(legs=legs)
        self.assertFalse(self.q.passed().any())

    def test_subset_reset_preserves_other_episodes(self):
        self.fill();self.q.retries[:]=2
        self.q.reset(torch.tensor([1]))
        self.assertEqual(self.q.passed().tolist(),[True,False,True])
        self.assertEqual(self.q.retries[:,0].tolist(),[2,0,2])

    def test_nonfinite_and_ineligible_samples(self):
        self.fill(cost=float('nan'))
        self.assertFalse(self.q.passed().any())
        self.q.reset(torch.arange(3))
        self.q.accumulate(torch.ones(3),torch.ones(3,4),torch.zeros(3,dtype=torch.long),
                          torch.zeros(3,dtype=torch.bool),torch.ones(3),10.)
        self.assertEqual(self.q.seconds.sum(),0.)

    def test_clearance_only_near_edge_unlanded_front_swing(self):
        feet=torch.zeros(1,4,3);feet[:,:,:]=torch.tensor([self.cfg.box_front,0.,.10])
        forces=torch.zeros_like(feet);height=torch.tensor([.2]);landed=torch.zeros(1,2,dtype=torch.bool)
        self.assertGreater(front_clearance(feet,forces,height,landed,self.cfg).item(),.5)
        forces[:,:,2]=20.
        self.assertEqual(front_clearance(feet,forces,height,landed,self.cfg).item(),0.)
        forces.zero_();feet[:,:,0]-=1.
        self.assertEqual(front_clearance(feet,forces,height,landed,self.cfg).item(),0.)
        feet[:,:,0]+=1.;feet[:,:,2]=.26
        self.assertEqual(front_clearance(feet,forces,height,landed,self.cfg).item(),0.)
        feet[:,:,2]=.1;landed[:]=True
        self.assertEqual(front_clearance(feet,forces,height,landed,self.cfg).item(),0.)

    def test_first_landing_bonus_cannot_repeat(self):
        from unittest.mock import patch
        q = self.q
        q.reference = SimpleNamespace(cost=lambda pairs: (torch.zeros(len(pairs)),torch.zeros(len(pairs),4)))
        q.before_gate[:] = 1
        env = SimpleNamespace(step_dt=.02, heights=torch.full((3,),.2),
            robot=SimpleNamespace(data=SimpleNamespace(root_lin_vel_w=torch.zeros(3,3))))
        pos=torch.tensor([[1.5,0.,.5]]).repeat(3,1)
        feet=torch.zeros(3,4,3);forces=torch.zeros_like(feet)
        support=torch.ones(3,4,dtype=torch.bool)
        with patch('climb_skill.tasks.direct.climb_skill.mdp.amp.snapshot',return_value=(torch.zeros(3,30),torch.ones(3))),              patch('climb_skill.tasks.direct.climb_skill.mdp.startup.movement_gain',return_value=torch.ones(3)):
            paid=torch.zeros(3,2)
            for _ in range(20):
                q.update(env,pos,feet,forces,support);paid+=q.new_landing
            torch.testing.assert_close(paid,torch.ones(3,2))
            support.zero_()
            q.update(env,pos,feet,forces,support)
            support[:]=True
            for _ in range(10):
                q.update(env,pos,feet,forces,support)
                self.assertFalse(q.new_landing.any())

    def test_independent_revision_start_inside_boundary_and_baseline_preserved(self):
        base,p=load_config(ROOT/'configs/rtx4090-amp-reference.json')
        self.assertNotEqual(configuration(base,p)['implementation_revision'],configuration(self.cfg,self.ppo)['implementation_revision'])
        self.assertFalse(base.approach_quality_enabled)
        self.assertEqual(base.box_height,.2)
        self.assertLess(self.cfg.rear_boundary_x,self.cfg.reset_x_range[0])
        self.assertEqual(self.ppo.save_interval,100)
        self.assertEqual(self.cfg.num_envs,4096)
        self.cfg.rear_boundary_x=-.5
        with self.assertRaises(ValueError):self.cfg.validate()

if __name__=='__main__':unittest.main()
