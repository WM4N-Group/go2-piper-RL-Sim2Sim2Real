import unittest
from types import SimpleNamespace
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import load_config
from climb_skill.tasks.direct.climb_skill.mdp.crossing_quality import CrossingQuality
from climb_skill.tasks.direct.climb_skill.mdp.quality_window import update_window

class WindowTests(unittest.TestCase):
 def setUp(self):
  self.cfg,_=load_config(Path(__file__).resolve().parents[1]/'configs/rtx4090-quality-window.json')
 def test_speed_separate_and_stopped_blocked(self):
  q=CrossingQuality(2,'cpu',self.cfg)
  for phase in (0,1):
   for speed in (.1,.7):
    q.accumulate(torch.full((2,),.1),torch.full((2,4),.1),torch.full((2,),phase),torch.ones(2,dtype=torch.bool),torch.tensor([speed,0.]),.5)
  q.crossed[:]=True;q.confirmed[:]=True
  self.assertEqual(q.passed().tolist(),[True,False])
  self.assertTrue((q.good_seconds==q.seconds).all())
  self.assertEqual(q.speed_good_seconds.sum(),0)
  q.speed_sum[0]=1.
  self.assertFalse(q.passed().any())
 def test_window_nonconsecutive_and_isolated(self):
  env=SimpleNamespace(task=self.cfg,num_envs=2,device='cpu')
  ids=torch.arange(2);done=torch.ones(2,dtype=torch.bool)
  for k,win in enumerate([True,False,True,False,True]):
   up=update_window(env,ids,done,torch.tensor([win,False]))
   self.assertEqual(up.tolist(),[k==4,False])
  old=env.quality_count.clone()
  update_window(env,ids,torch.zeros_like(done),torch.zeros_like(done))
  torch.testing.assert_close(old,env.quality_count)
 def test_unsafe_contact_needs_duration(self):
  q=CrossingQuality(1,'cpu',self.cfg);h=torch.tensor([.05])
  feet=torch.zeros(1,4,3);feet[:,:,0]=self.cfg.box_front-.1;feet[:,:,2]=self.cfg.foot_radius+.08
  force=torch.zeros_like(feet);support=torch.zeros(1,4,dtype=torch.bool)
  q.capture(feet,force)
  feet[:,:,0]=self.cfg.box_front+.01;feet[:,:,2]=self.cfg.foot_radius+.05;force[:,:,2]=20
  for i in range(4):
   q.track(feet,force,support,h,.02);q.capture(feet,force)
   self.assertEqual(bool(q.reason_flags[:,:,3].all()),i==3)
 def test_ordinary_return_not_failed(self):
  q=CrossingQuality(1,'cpu',self.cfg);h=torch.tensor([.05])
  feet=torch.zeros(1,4,3);feet[:,:,0]=self.cfg.box_front-.06;feet[:,:,2]=self.cfg.foot_radius
  force=torch.zeros_like(feet);force[:,:,2]=20
  q.active[:]=True;q.capture(feet,force)
  for _ in range(3):q.track(feet,force,torch.zeros(1,4,dtype=torch.bool),h,.02)
  self.assertFalse(q.failed.any());self.assertFalse(q.active.any())

if __name__=='__main__':unittest.main()
