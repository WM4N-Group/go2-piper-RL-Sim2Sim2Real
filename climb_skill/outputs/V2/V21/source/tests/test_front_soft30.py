"""恢复向前登箱后的30cm课程和宽松前腿软约束。"""
from pathlib import Path
from types import SimpleNamespace
import unittest,math
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import load_config,configuration,require_implementation
from climb_skill.tasks.direct.climb_skill.mdp.front_safety import front_soft_cost
from climb_skill.tasks.direct.climb_skill.mdp.joint_workspace import rear_target_workspace
from climb_skill.tasks.direct.climb_skill.mdp.startup import movement_gain
from climb_skill.tasks.direct.climb_skill.mdp.amp import snapshot

class FrontSoft30Tests(unittest.TestCase):
 def setUp(self):
  self.cfg,self.ppo=load_config(Path(__file__).resolve().parents[1]/'configs/climb30.json')

 def test_curriculum_and_contract(self):
  c=self.cfg;heights=torch.linspace(c.curriculum_min_height,c.box_height,c.curriculum_levels)
  self.assertEqual(len(heights),11);self.assertAlmostEqual(float(heights[-1]),.3,6)
  torch.testing.assert_close(heights[1:]-heights[:-1],torch.full((10,),.025))
  self.assertEqual(self.ppo.save_interval,100)
  conf=configuration(c,self.ppo);require_implementation(conf)
  self.assertEqual(conf['implementation_revision'],'climb_skill_v6_forward_baseline_front_soft30')
  with self.assertRaises(ValueError):require_implementation({**conf,'implementation_revision':'climb_skill_v5_ascent_stop'})

 def test_free_start_is_retained(self):
  c=self.cfg;self.assertEqual(c.startup_stand_seconds,0.)
  env=SimpleNamespace(task=c,num_envs=2,device='cpu')
  torch.testing.assert_close(movement_gain(env),torch.ones(2))

 def test_front_range_is_wider_and_penalty_does_not_clip(self):
  c=self.cfg
  self.assertGreater(c.front_thigh_max,c.rear_thigh_max)
  self.assertLess(c.front_calf_min,c.rear_calf_min)
  self.assertGreater(c.front_calf_max,c.rear_calf_max)
  q=torch.zeros(3,18);q[:,[1,4]]=1.85;q[:,[2,5]]=-1.
  q[1,1]=c.front_thigh_max+.1;q[2,1]=c.front_thigh_max+.2
  original=q.clone();g=torch.tensor([[0.,0.,-1.]]).expand(3,-1)
  costs=front_soft_cost(q,q,g,torch.ones(3),c)['front_joint_soft']
  self.assertEqual(costs[0].item(),0.)
  self.assertGreater(costs[1].item(),0.)
  self.assertAlmostEqual(float(costs[2]/costs[1]),4.,places=4)
  torch.testing.assert_close(q,original)
  # 后腿工作范围裁剪绝不能顺带裁前腿。
  targets=rear_target_workspace(q,c)
  torch.testing.assert_close(targets[:,:6],q[:,:6])

 def test_front_pitch_is_soft_and_nose_up_only(self):
  c=self.cfg;angles=torch.tensor([.5,.6,.7,-.7])
  g=torch.stack((-angles.sin(),torch.zeros(4),-angles.cos()),-1)
  q=torch.zeros(4,18);q[:,[1,4]]=.8;q[:,[2,5]]=-1.5
  cost=front_soft_cost(q,q,g,torch.ones(4),c)['front_pitch_soft']
  self.assertEqual(cost[0].item(),0.);self.assertAlmostEqual(cost[1].item(),0.,places=6)
  self.assertGreater(cost[2].item(),0.);self.assertEqual(cost[3].item(),0.)

 def test_amp_not_switched_off_by_top_ascent(self):
  c=self.cfg
  env=SimpleNamespace(task=c,num_envs=1,device='cpu',robot=SimpleNamespace(data=SimpleNamespace(
      joint_pos=torch.zeros(1,18),joint_vel=torch.zeros(1,18),root_lin_vel_b=torch.zeros(1,3),root_ang_vel_b=torch.zeros(1,3))),
      joint_ids=list(range(18)),heights=torch.tensor([.3]),
      _kinematics=lambda:(torch.tensor([[c.finish_x,0.,.6]]),None,torch.zeros(1,4,3)))
  _,gate=snapshot(env);self.assertEqual(gate.item(),1.)

if __name__=='__main__':unittest.main()
