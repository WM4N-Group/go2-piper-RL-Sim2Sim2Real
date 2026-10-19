from config_cases import load_case
import unittest
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import load_config, configuration
from climb_skill.tasks.direct.climb_skill.mdp.crossing_quality import CrossingQuality
from climb_skill.learning.motion_reference import MotionReference

class CrossingTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.cfg, self.ppo = load_case('legacy_crossing_quality')
        self.q = CrossingQuality(2, 'cpu', self.cfg)
        self.h = torch.full((2,), .2)
        self.feet = torch.zeros(2,4,3)
        self.feet[...,0] = self.cfg.box_front - .12
        self.feet[...,2] = self.cfg.foot_radius
        self.force = torch.zeros_like(self.feet); self.force[...,2] = 20
        self.support = torch.zeros(2,4,dtype=torch.bool)
        self.q.capture(self.feet,self.force)

    def step(self, feet, force=None, support=None, dt=.02):
        self.q.track(feet, self.force if force is None else force,
                     self.support if support is None else support,self.h,dt)
        self.q.capture(feet,self.force if force is None else force)

    def fill_gait(self):
        for phase in (0,1):
            self.q.accumulate(torch.full((2,),.1),torch.full((2,4),.1),
                torch.full((2,),phase),torch.ones(2,dtype=torch.bool),torch.full((2,),.4),1.)

    def test_last_approach_and_normal_swing_checked(self):
        ground,top,mask=self.q.masks(self.feet,self.h)
        self.assertTrue(ground.all());self.assertTrue(mask.all());self.assertFalse(top.any())
        swing=self.feet.clone();swing[:,0,2]+=.04
        force=self.force.clone();force[:,0]=0
        self.step(swing,force);self.step(self.feet)
        self.assertFalse(self.q.failed.any());self.assertFalse(self.q.active.any())
        self.assertTrue(self.q.flat_gate(self.feet,self.h).all())

    def test_only_actual_climbing_leg_exempt(self):
        lifted=self.feet.clone();lifted[:,0,2]+=.15;lifted[:,0,0]+=.06
        force=self.force.clone();force[:,0]=0
        self.step(lifted,force)
        ground,top,mask=self.q.masks(lifted,self.h)
        self.assertFalse(ground.any());self.assertFalse(top.any())
        self.assertEqual(mask[0].tolist(),[False,True,True,True])

    def test_low_crossing_failure_persists_after_safe_recovery(self):
        low=self.feet.clone();low[:,:,0]=self.cfg.box_front+.08;low[:,:,2]+=.1
        self.step(low,torch.zeros_like(self.force))
        self.assertTrue(self.q.failed.all())
        self.assertTrue(self.q.new_failure.all())
        safe=low.clone();safe[:,:,2]=self.cfg.foot_radius+.2
        for _ in range(5):self.step(safe,support=torch.ones_like(self.support))
        self.fill_gait()
        self.assertTrue(self.q.confirmed.all());self.assertFalse(self.q.passed().any())
        self.assertFalse(self.q.new_failure.any())

    def test_clean_cross_and_loaded_landing_all_four(self):
        lifted=self.feet.clone();lifted[:,:,2]+=.25
        self.step(lifted,torch.zeros_like(self.force))
        over=lifted.clone();over[:,:,0]=self.cfg.box_front+.1
        self.step(over,torch.zeros_like(self.force))
        safe=over.clone();safe[:,:,2]=self.cfg.foot_radius+.2
        for _ in range(3):self.step(safe,support=torch.ones_like(self.support))
        self.assertFalse(self.q.confirmed.any())
        self.step(safe,support=torch.ones_like(self.support))
        self.fill_gait()
        self.assertTrue(self.q.passed().all())
        self.q.confirmed[1,3]=False
        self.assertEqual(self.q.passed().tolist(),[True,False])
        self.q.reset(torch.tensor([0]))
        self.assertFalse(self.q.crossed[0].any());self.assertTrue(self.q.crossed[1].all())

    def test_return_wall_unsafe_and_timeout(self):
        lifted=self.feet.clone();lifted[:,:,2]+=.15;lifted[:,:,0]+=.06
        self.step(lifted,torch.zeros_like(self.force))
        for _ in range(3):self.step(self.feet)
        self.assertTrue(self.q.reason_flags[:,:,1].all())
        self.q.reset(torch.arange(2));self.q.capture(self.feet,self.force)
        wall=self.feet.clone();wall[:,:,0]=self.cfg.box_front-.01;wall[:,:,2]+=.1
        force=torch.zeros_like(self.force);force[:,:,0]=20
        for _ in range(4):self.step(wall,force)
        self.assertTrue(self.q.reason_flags[:,:,2].all())
        self.q.reset(torch.arange(2));self.q.capture(self.feet,self.force)
        self.step(lifted,torch.zeros_like(self.force),dt=1.6)
        self.assertTrue(self.q.reason_flags[:,:,4].all())
        self.q.reset(torch.arange(2));self.q.capture(self.feet,self.force)
        edge=self.feet.clone();edge[:,:,0]=self.cfg.box_front+.01;edge[:,:,2]+=.2
        self.step(edge)
        self.assertTrue(self.q.reason_flags[:,:,3].all())

    def test_masked_reference_shared_phase_and_no_empty_mask(self):
        expert=torch.zeros(2,60);expert[1,:12]=1;expert[1,30:42]=1
        ref=MotionReference(expert)
        pairs=expert[:1].clone();pairs[:,6:12]=50;pairs[:,36:42]=50
        c,l=ref.cost(pairs,torch.tensor([[True,True,False,False]]))
        self.assertLess(c.item(),1e-6);self.assertEqual(l[:,2:].sum(),0)
        pairs[:,3:6]=1;pairs[:,33:36]=1
        c,_=ref.cost(pairs,torch.tensor([[True,True,False,False]]))
        self.assertGreater(c.item(),.1)
        with self.assertRaises(ValueError):ref.cost(pairs,torch.zeros(1,4,dtype=torch.bool))

    def test_bad_mixed_gait_blocks_and_config_versioned(self):
        self.fill_gait();self.q.crossed[:]=True;self.q.confirmed[:]=True
        self.q.mixed_seconds[:]=1;self.q.mixed_good_seconds[:]=.5
        self.assertFalse(self.q.passed().any())
        self.assertEqual(self.ppo.save_interval,100)
        self.assertEqual(configuration(self.cfg,self.ppo)['implementation_revision'],'climb_skill_v3_foot_crossing_quality_v2')
        self.cfg.crossing_takeoff_max=.01
        with self.assertRaises(ValueError):self.cfg.validate()

if __name__=='__main__':unittest.main()
