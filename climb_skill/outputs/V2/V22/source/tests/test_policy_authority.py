"""起步无控制权时不得驱动策略/探索，探索压力不能突破标准差上限。"""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import torch
from climb_skill.learning.actor_critic import ClimbActorCritic
from climb_skill.learning.ppo import PPO
from climb_skill.tasks.direct.climb_skill.task_parameters import PPOConfig

torch.set_num_threads(1)

class AuthorityTests(unittest.TestCase):
    def make_batch(self, model, active):
        obs=torch.randn(len(active),923)
        with torch.no_grad():
            d=model.distribution(obs,True)
            actions=d.sample()
            return dict(obs=obs,actions=actions,logp=d.log_prob(actions).sum(-1),
                values=model.value(obs),mu=d.mean,std=d.stddev,
                advantages=torch.randn(len(active)),returns=torch.randn(len(active)),
                policy_active=torch.tensor(active,dtype=torch.bool))

    def test_forced_standing_does_not_update_actor_or_exploration(self):
        model=ClimbActorCritic(.6)
        algo=PPO(model,PPOConfig(epochs=1,minibatches=1,initial_std=.6,entropy_coefficient=1.))
        batch=self.make_batch(model,[False]*8)
        actor=copy.deepcopy(model.actor.state_dict()); std=model.log_std.detach().clone()
        logs=algo.update(batch,False)
        for k,v in actor.items():torch.testing.assert_close(model.actor.state_dict()[k],v,rtol=0,atol=0)
        torch.testing.assert_close(model.log_std,std,rtol=0,atol=0)
        self.assertEqual(logs['entropy'],0.);self.assertEqual(logs['kl'],0.)
        self.assertEqual(logs['learning_rate'],algo.cfg.learning_rate)
        self.assertGreater(logs['value_loss'],0.)  # critic仍学习真实的站立阶段回报

    def test_inactive_samples_do_not_change_policy_gradient_or_kl(self):
        torch.manual_seed(1)
        a=ClimbActorCritic();b=copy.deepcopy(a)
        ca=PPO(a,PPOConfig(epochs=1,minibatches=1));cb=PPO(b,PPOConfig(epochs=1,minibatches=1))
        batch=self.make_batch(a,[True]*4+[False]*4);other={k:v.clone() for k,v in batch.items()}
        other['actions'][4:]+=3.;other['advantages'][4:]=1000.;other['mu'][4:]+=100.
        torch.manual_seed(7);la=ca.update(batch,False)
        torch.manual_seed(7);lb=cb.update(other,False)
        for k,v in a.actor.state_dict().items():torch.testing.assert_close(v,b.actor.state_dict()[k],rtol=0,atol=0)
        self.assertEqual(la['kl'],lb['kl']);self.assertEqual(la['policy_loss'],lb['policy_loss'])

    def test_entropy_pressure_and_kl_adaptation_stay_bounded(self):
        model=ClimbActorCritic();cfg=PPOConfig(epochs=1,minibatches=1,entropy_coefficient=1.)
        algo=PPO(model,cfg)
        for _ in range(12):
            batch=self.make_batch(model,[True]*8)
            batch['advantages'].zero_();batch['std']=batch['std']*1.01
            logs=algo.update(batch,False)
            self.assertLessEqual(logs['policy/std_max'],cfg.maximum_std)
            self.assertLessEqual(logs['learning_rate'],cfg.maximum_learning_rate)

    def test_collect_records_authority_before_auto_reset(self):
        cfg=PPOConfig(steps_per_env=1);algo=PPO(ClimbActorCritic(),cfg)
        class Env:
            step_dt=.02
            def step(self,actions):
                # 模拟自动reset导致权限变动；rollout必须保存step之前的权限。
                self.gain=torch.ones(2)
                return ({'policy':torch.zeros(2,923)},torch.ones(2),torch.zeros(2,dtype=torch.bool),
                        torch.zeros(2,dtype=torch.bool),{})
        env=Env();env.gain=torch.tensor([0.,1.])
        with patch('climb_skill.tasks.direct.climb_skill.mdp.startup.movement_gain',side_effect=lambda e:e.gain):
            _,batch,*_=algo.collect(env,torch.zeros(2,923))
        self.assertEqual(batch['policy_active'].tolist(),[False,True])
        self.assertEqual(batch['advantages'][0].item(),0.)

if __name__=='__main__':unittest.main()
