"""无需启动Isaac：核对速度采样/课程、12→18维动作、AMP和PPO超时bootstrap。"""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source/nav_skill2'))
import torch
from nav_skill2.tasks.direct.nav_skill2.parameters import TaskConfig,PPOConfig,ACTOR_OBS,CRITIC_OBS,LEG_NAMES
from nav_skill2.tasks.direct.nav_skill2.commands import sample_commands,smooth_commands,tracking_quality,motion_terms,command_modes,startup_action_gain
from nav_skill2.learning.ppo import ActorCritic,PPO
from nav_skill2.learning.amp import AMP

class Contracts(unittest.TestCase):
    def setUp(self):torch.set_num_threads(2)
    def test_startup_handover_and_legacy_contract(self):
        elapsed=torch.tensor([0.,.02,.5,1.,1.5,2.,3.])
        gain=startup_action_gain(elapsed,2.)
        self.assertEqual(float(gain[0]),0.)
        self.assertEqual(float(gain[-1]),1.)
        self.assertAlmostEqual(float(gain[3]),.5)
        self.assertTrue(bool((gain[1:]>=gain[:-1]).all()))
        torch.testing.assert_close(startup_action_gain(elapsed,0.),torch.ones_like(elapsed))
        self.assertLess(float(gain[1]),.00002)
        old=TaskConfig();self.assertEqual(old.reset_settle_seconds,0.)
        self.assertEqual(old.startup_action_ramp_seconds,0.)
        for name in ('reset_settle_seconds','startup_action_ramp_seconds'):
            cfg=TaskConfig();setattr(cfg,name,float('nan'))
            with self.assertRaises(ValueError):cfg.validate()

    def test_velocity_commands_and_smoothing(self):
        cfg=TaskConfig();cfg.validate();torch.manual_seed(12)
        levels=torch.zeros(20000,dtype=torch.long)
        commands=sample_commands(levels,cfg)
        self.assertEqual(commands.shape,(20000,3));self.assertTrue(bool((commands[:,1].abs()>.1).any()))
        self.assertTrue(bool((commands[:,0]<-.1).any()));self.assertLessEqual(float(commands[:,0].max()),cfg.speed_limits[0])
        stand=commands.abs().sum(-1)==0
        self.assertAlmostEqual(float(stand.float().mean()),.15,delta=.02)
        self.assertAlmostEqual(float((commands[:,2]>0).float().mean()),float((commands[:,2]<0).float().mean()),delta=.02)
        current=torch.tensor([[.001,0.,.001],[0.,0.,0.]])
        desired=torch.tensor([[0.,0.,0.],[.45,0.,.7]])
        result=smooth_commands(current,desired,torch.full((2,),.02),cfg)
        torch.testing.assert_close(result,torch.tensor([[0.,0.,0.],[.01,0.,.02]]))

    def test_curriculum_cannot_reward_standing_or_no_motion(self):
        cfg=TaskConfig()
        count=torch.full((4,),200.);motion=torch.tensor([0.,4.,4.,4.]);failed=torch.tensor([False,False,False,True])
        # 第一例纯站立，第二例站着忽略0.1m/s指令，第三例跟踪好，第四例跌倒。
        response=torch.zeros(4,7);response[:,1]=torch.tensor([0.,0.,100.,100.])
        counts=torch.zeros(4,7);counts[:,1]=torch.tensor([0.,200.,200.,200.])
        qualified,eligible,_,_=tracking_quality(torch.tensor([0.,2.,.02,.02]),torch.zeros(4),count,motion,failed,cfg,torch.tensor([0.,2.,2.,2.]),response,counts,torch.tensor([0.,0.,150.,150.]),torch.zeros(4),torch.zeros(4))
        self.assertEqual(qualified.tolist(),[False,False,True,False]);self.assertEqual(eligible.tolist(),[False,True,True,True])
        self.assertEqual(ACTOR_OBS,315);self.assertEqual(CRITIC_OBS,324)

    def test_actor18_and_arm_excluded_from_probability(self):
        model=ActorCritic();obs=torch.randn(7,ACTOR_OBS);a=model.actor(obs)
        self.assertEqual(a.shape,(7,18));self.assertEqual(int(torch.count_nonzero(a[:,12:])),0)
        self.assertEqual(model.distribution(obs).mean.shape,(7,12))
        self.assertEqual(model.actor.network[-1].out_features,12)
        a.sum().backward();self.assertTrue(bool(torch.isfinite(model.actor.network[-1].weight.grad).all()))
        jit=torch.jit.script(model.actor);self.assertEqual(int(torch.count_nonzero(jit(obs)[:,12:])),0)
    def test_real_motion_rewards_and_modes(self):
        command=torch.tensor([[.25,0.,0.],[-.25,0.,0.],[0.,.2,0.],[0.,-.2,0.],[0.,0.,.35],[0.,0.,-.35]])
        zero=torch.zeros(6,3)
        terms,response,good=motion_terms(command,zero,zero)
        self.assertEqual(float(terms['velocity'].sum()+terms['yaw_velocity'].sum()),0.)
        self.assertFalse(bool(good.any()))
        velocity=command.clone();velocity[:,2]=0.
        omega=zero.clone();omega[:,2]=command[:,2]
        _,response,good=motion_terms(command,velocity,omega)
        torch.testing.assert_close(response,torch.ones(6));self.assertTrue(bool(good.all()))
        _,wrong,_=motion_terms(command,-velocity,-omega)
        self.assertTrue(bool((wrong<0).all()))
        fast,_,_=motion_terms(command,velocity*4,omega*4)
        self.assertLessEqual(float(fast['velocity'].max()),1.);self.assertTrue(bool((fast['overspeed']>0).all()))
        self.assertEqual(command_modes(command).tolist(),[1,2,3,4,5,6])

    def test_amp_reset_stop_mode_change_and_stationary_cheat(self):
        cfg=PPOConfig(amp_batch_size=16,amp_updates=1)
        amp=AMP(cfg,Path(__file__).resolve().parents[1]/'data/amp_pairs.json','cpu')
        pairs=amp.expert[:3];before,after=pairs[:,:30],pairs[:,30:]
        gate=torch.tensor([[1.,1.,1.]]).expand(3,-1).clone()
        for terminal,other in [(True,gate),(False,torch.zeros_like(gate)),(False,gate+torch.tensor([0.,0.,1.]))]:
            r=amp.transition(before,after,gate,other,torch.full((3,),terminal),.02)
            self.assertEqual(float(r.abs().sum()),0.);self.assertEqual(amp.size,0)
        stationary=before.clone();stationary[:,18:]=0.
        no_response=gate.clone();no_response[:,1]=0.
        r=amp.transition(stationary,stationary,no_response,no_response,torch.zeros(3,dtype=torch.bool),.02)
        self.assertEqual(amp.logs['amp_reward'],0.);self.assertGreater(amp.logs['amp_reference_cost'],0.)
        self.assertTrue(bool((r<0).all()))
        r=amp.transition(before,after,gate,gate,torch.zeros(3,dtype=torch.bool),.02)
        self.assertEqual(amp.size,6);self.assertTrue(torch.isfinite(r).all());self.assertTrue(torch.isfinite(torch.tensor(amp.update()['amp_loss'])))
        for mode,reference in amp.references.items():
            example=amp.expert[amp.groups[mode][:2]]
            self.assertLess(float(reference.cost(example)[0].max()),1e-4)
        examples=torch.cat([amp.expert[group[:1]] for group in amp.groups.values()])
        modes=torch.arange(1,7,dtype=torch.float32)
        gates=torch.stack((torch.ones(6),torch.ones(6),modes),-1)
        amp.transition(examples[:,:30],examples[:,30:],gates,gates,torch.zeros(6,dtype=torch.bool),.02)
        self.assertEqual(set(amp.replay_modes[:amp.size].tolist()),set(range(1,7)))
        self.assertTrue(torch.isfinite(torch.tensor(amp.update()['amp_loss'])))
        saved=amp.state_dict();other=AMP(cfg,Path(__file__).resolve().parents[1]/'data/amp_pairs.json','cpu');other.load_state_dict(saved)
        torch.testing.assert_close(other.replay_modes[:other.size],amp.replay_modes[:amp.size])
    def test_export_is_portable_cpu_actor18(self):
        import tempfile
        from types import SimpleNamespace
        from nav_skill2.tasks.direct.nav_skill2.parameters import configuration
        model=ActorCritic();cfg=PPOConfig(amp_enabled=False);algo=PPO(model,cfg)
        fake=SimpleNamespace(levels=torch.zeros(2,dtype=torch.long),wins=torch.zeros(2,dtype=torch.long),losses=torch.zeros(2,dtype=torch.long))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'model_0.pt'
            algo.save(path,configuration(TaskConfig(num_envs=2),cfg),fake)
            actor=torch.jit.load(str(path.with_name('actor_0.pt')))
            self.assertEqual(next(actor.parameters()).device.type,'cpu')
            result=actor(torch.randn(2,ACTOR_OBS))
            self.assertEqual(result.shape,(2,18));self.assertEqual(int(torch.count_nonzero(result[:,12:])),0)

    def test_timeout_bootstraps_terminal_not_reset(self):
        # 终态critic全1、reset后critic全100；值函数只取第1维。
        class Dummy:
            step_dt=.02
            def amp_snapshot(self):return None,None
            def step(self,action):return {'policy':torch.zeros(2,ACTOR_OBS),'critic':torch.ones(2,CRITIC_OBS)*100},torch.ones(2),torch.tensor([False,True]),torch.tensor([True,False]),{'terminal_critic':torch.ones(2,CRITIC_OBS),'episode_records':[]}
        model=ActorCritic();model.value=lambda x:x[:,0]
        algo=PPO(model,PPOConfig(steps_per_env=1),None)
        obs={'policy':torch.zeros(2,ACTOR_OBS),'critic':torch.zeros(2,CRITIC_OBS)}
        _,data,_,_=algo.collect(Dummy(),obs)
        torch.testing.assert_close(data['returns'],torch.tensor([1.99,1.]))

if __name__=='__main__':unittest.main()
