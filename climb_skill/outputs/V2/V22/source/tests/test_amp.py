"""AMP关键契约：奖励门控、独立优化、数据身份及完整断点恢复。"""
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import torch
from climb_skill.learning.amp import AMP, AMPConfig
from climb_skill.learning.ppo import PPO
from climb_skill.learning.actor_critic import ClimbActorCritic
from climb_skill.tasks.direct.climb_skill.task_parameters import LEG_NAMES, TaskConfig, PPOConfig, configuration, load_config

torch.set_num_threads(1)

class AMPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'data.json'
        # 合成数据仅测试数值与接口，不作为训练示范。
        self.path.write_text(json.dumps(dict(format='climb_amp_pairs_v1',dt=.02,
            joint_order=list(LEG_NAMES), feature_order=['joint_position_12','body_linear_velocity_3',
                'body_angular_velocity_3','joint_velocity_12'], pairs=torch.randn(64,60).tolist())))
        self.cfg = AMPConfig(dataset=str(self.path),batch_size=16,updates=2,replay_capacity=32)
        self.amp = AMP(self.cfg,'cpu')

    def test_gate_and_done_never_insert_reset(self):
        before,after = torch.randn(4,30),torch.randn(4,30)
        reward,eligible = self.amp.transition(before,after,torch.tensor([1.,0.,1.,1.]),
            torch.tensor([1.,1.,0.,1.]),torch.tensor([False,False,False,True]),.02)
        self.assertEqual(self.amp.size,1)
        torch.testing.assert_close(self.amp.replay[0],torch.cat((before[0],after[0])))
        self.assertEqual(reward[1:].sum().item(),0)
        self.assertTrue(0<=reward[0]<=.01)
        self.assertFalse(reward.requires_grad)
        self.assertEqual(eligible.item(),.25)

    def test_optimizer_and_roundtrip(self):
        self.amp.insert(torch.randn(70,60))
        old = [p.clone() for p in self.amp.discriminator.parameters()]
        logs=self.amp.update()
        self.assertTrue(logs['amp_discriminator_loss']>0)
        self.assertTrue(any(not torch.equal(x,y) for x,y in zip(old,self.amp.discriminator.parameters())))
        other=AMP(self.cfg,'cpu');other.load_state_dict(self.amp.state_dict())
        torch.testing.assert_close(other.replay,self.amp.replay)
        probe=torch.randn(4,60)
        torch.testing.assert_close(other.discriminator(other.normalize(probe)),self.amp.discriminator(self.amp.normalize(probe)))
        bad=self.amp.state_dict();bad['dataset_sha256']='changed'
        with self.assertRaisesRegex(ValueError,'dataset changed'):other.load_state_dict(bad)

    def test_ppo_save_load_and_nonamp_rejection(self):
        cfg=PPOConfig();model=ClimbActorCritic()
        algo=PPO(model,cfg,amp=self.amp)
        self.amp.insert(torch.randn(7,60));self.amp.update()
        path=Path(self.temp.name)/'model.pt'
        algo.save(path,configuration(TaskConfig(),cfg))
        clone=PPO(ClimbActorCritic(),cfg,amp=AMP(self.cfg,'cpu'));clone.load(path)
        self.assertEqual(clone.amp.size,7)
        with self.assertRaisesRegex(ValueError,'AMP checkpoint'):PPO(ClimbActorCritic(),cfg).load(path)

    def test_collect_uses_terminal_pair_and_separates_task_reward(self):
        from types import SimpleNamespace
        cfg=PPOConfig(steps_per_env=1)
        amp=self.amp
        algo=PPO(ClimbActorCritic(),cfg,amp=amp)
        class Env:
            num_envs=2
            device='cpu'
            task = TaskConfig(startup_stand_seconds=0.)
            step_dt=.02
            def step(self,actions):
                assert torch.count_nonzero(actions[:,12:])==0
                return ({'policy':torch.zeros(2,923)},torch.ones(2),torch.zeros(2,dtype=torch.bool),
                    torch.zeros(2,dtype=torch.bool),dict(amp_terminal_state=torch.full((2,30),2.),
                    amp_terminal_gate=torch.ones(2), amp_terminal_forward_speed=torch.full((2,),.4), terminal_observations=torch.zeros(2,923)))
        with patch('climb_skill.tasks.direct.climb_skill.mdp.amp.snapshot',return_value=(torch.ones(2,30),torch.ones(2))):
            algo.collect(Env(),torch.zeros(2,923))
        torch.testing.assert_close(amp.replay[:2,30:],torch.full((2,30),2.))
        self.assertEqual(algo.rollout_diagnostics['task_step_reward'],1.)

    def test_config_keeps_task_removes_gait_costs(self):
        path=Path(__file__).resolve().parents[1]/'configs/climb30.json'
        task,ppo=load_config(path)
        self.assertEqual(ppo.save_interval,100)
        self.assertGreater(task.rewards['progress'],0)
        self.assertGreater(task.forward_heading_weight,0)

if __name__=='__main__':unittest.main()
