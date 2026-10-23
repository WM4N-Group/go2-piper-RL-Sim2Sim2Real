import copy
import importlib.util
from pathlib import Path
import unittest
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import load_config, configuration, require_implementation
from climb_skill.tasks.direct.climb_skill.mdp.crossing_quality import CrossingQuality

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('migrate_curriculum',ROOT/'scripts/migrate_curriculum.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class MigrationTests(unittest.TestCase):
 def setUp(self):
  self.old,self.ppo=load_config(ROOT/'configs/rtx4090-crossing-quality.json')
  self.new,self.newppo=load_config(ROOT/'configs/rtx4090-model800-curriculum.json')
  self.state={k:object() for k in ('model','optimizer','estimator_optimizer','history_optimizer','amp','torch_rng','python_rng','numpy_rng','learning_rate','iteration','curriculum_levels')}
  self.state['configuration']=configuration(self.old,self.newppo)
 def test_learning_state_untouched_and_versioned(self):
  result,changes=module.migrate(self.state,self.new,self.newppo)
  self.assertEqual(set(changes),{'curriculum_only_enabled','quality_window_enabled'})
  for k in self.state:
   if k!='configuration':self.assertIs(result[k],self.state[k])
  require_implementation(result['configuration'])
  self.assertEqual(result['configuration']['implementation_revision'],'climb_skill_v3_model800_curriculum_v4')
 def test_reward_and_ppo_changes_rejected(self):
  cfg=copy.deepcopy(self.new);cfg.front_landing_bonus+=1
  with self.assertRaisesRegex(ValueError,'Non-curriculum'):module.migrate(self.state,cfg,self.newppo)
  ppo=copy.deepcopy(self.newppo);ppo.learning_rate*=.5
  with self.assertRaisesRegex(ValueError,'PPO/AMP'):module.migrate(self.state,self.new,ppo)
 def test_old_crossing_rewards_and_masks_identical(self):
  old=CrossingQuality(2,'cpu',self.old);new=CrossingQuality(2,'cpu',self.new)
  h=torch.tensor([.05,.2]);force=torch.zeros(2,4,3);force[:,:,2]=20
  foot=torch.zeros(2,4,3);foot[:,:,0]=self.old.box_front-.06;foot[:,:,2]=self.old.foot_radius
  for q in (old,new):q.active[:]=True;q.capture(foot,force)
  for step in range(12):
   if step==4:foot[:,:,0]=self.old.box_front+.01;foot[:,:,2]=self.old.foot_radius+h[:,None]
   if step==8:foot[:,:,0]=self.old.box_front+.1
   support=torch.full((2,4),step>=8,dtype=torch.bool)
   for q in (old,new):q.track(foot,force,support,h,.02)
   for name in ('clearance','guidance','new_failure','new_landing','failed','active','confirmed','crossed'):
    torch.testing.assert_close(getattr(old,name),getattr(new,name))
   torch.testing.assert_close(old.flat_gate(foot,h),new.flat_gate(foot,h))
   for q in (old,new):q.capture(foot,force)
 def test_quality_changes_do_not_require_mixed_flat_style(self):
  q=CrossingQuality(1,'cpu',self.new)
  for phase in (0,1):
   for speed in (.1,.7):q.accumulate(torch.tensor([.1]),torch.full((1,4),.1),torch.tensor([phase]),torch.tensor([True]),torch.tensor([speed]),.5)
  q.confirmed[:]=True;q.crossed[:]=True;q.mixed_seconds[:]=1
  self.assertTrue(q.passed().item())
  q.failed[:,0]=True;self.assertFalse(q.passed().item())

if __name__=='__main__':unittest.main()
