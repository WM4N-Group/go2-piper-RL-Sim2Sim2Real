"""恢复已知向前登箱判定：连续几何确认、近期承重；允许行走接触交替。"""
import unittest
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import TaskConfig
from climb_skill.tasks.direct.climb_skill.mdp.geometry import platform_ascent_geometry,ascent_confirmation
from climb_skill.tasks.direct.climb_skill.mdp.gait_quality import forward_pose_ready

class AscentTests(unittest.TestCase):
 def setUp(self):self.c=TaskConfig()
 def geometry(self,x=2.4):
  c=self.c;feet=torch.tensor([[[x+.25,.15,.32],[x+.25,-.15,.32],[x-.25,.15,.32],[x-.25,-.15,.32]]])
  ages=torch.full((1,4),.1)
  return feet,ages,platform_ascent_geometry(feet,ages,torch.tensor([x]),c,torch.tensor([.3]))
 def confirm(self,g,support,**kwargs):
  z=torch.zeros(1);h=z.clone();tilt=kwargs.get('tilt',z);bad=kwargs.get('failure',torch.tensor([False]))
  for _ in range(16):h,ok=ascent_confirmation(h,g,support,tilt,z,bad,self.c,.02)
  return h,ok
 def test_walk_on_top_can_finish_without_standing(self):
  feet,ages,g=self.geometry()
  self.assertTrue(g.item())
  _,ok=self.confirm(g,torch.tensor([[True,False,False,True]]))
  self.assertTrue(ok.item())
 def test_original_completion_line_and_heading_are_restored(self):
  self.assertFalse(self.geometry(2.15)[2].item())
  self.assertTrue(self.geometry(2.4)[2].item())
  self.assertFalse(forward_pose_ready(torch.tensor([[2.4,0.,.6]]),torch.tensor([.3]),self.c).item())
 def test_missing_or_stale_top_foot_cannot_finish(self):
  for variant in ['ground','outside','never_loaded']:
   feet,ages,_=self.geometry()
   if variant=='ground':feet[:,2,2]=.02
   if variant=='outside':feet[:,2,0]=.7
   if variant=='never_loaded':ages[:,2]=float('inf')
   g=platform_ascent_geometry(feet,ages,torch.tensor([2.4]),self.c,torch.tensor([.3]))
   _,ok=self.confirm(g,torch.ones(1,4,dtype=torch.bool));self.assertFalse(ok.item(),variant)
 def test_continuity_health_and_current_support(self):
  g=self.geometry()[2]
  for support,extra in [(torch.zeros(1,4,dtype=torch.bool),{}),
   (torch.ones(1,4,dtype=torch.bool),{'tilt':torch.tensor([.5])}),
   (torch.ones(1,4,dtype=torch.bool),{'failure':torch.tensor([True])})]:
   _,ok=self.confirm(g,support,**extra);self.assertFalse(ok.item())
  h,_=self.confirm(g,torch.ones(1,4,dtype=torch.bool))
  h,ok=ascent_confirmation(h,torch.tensor([False]),torch.ones(1,4,dtype=torch.bool),torch.zeros(1),torch.zeros(1),torch.tensor([False]),self.c,.02)
  self.assertEqual(h.item(),0.);self.assertFalse(ok.item())
if __name__=='__main__':unittest.main()
