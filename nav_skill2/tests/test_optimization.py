"""V4实质合同：镜像轴/历史、非对称速度范围、软限速、探索退火和速度条件AMP。"""
import sys,unittest,tempfile
from pathlib import Path
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source/nav_skill2'))
from nav_skill2.tasks.direct.nav_skill2.parameters import load_config,TaskConfig,ACTOR_OBS
from nav_skill2.tasks.direct.nav_skill2.commands import sample_commands,motion_terms,smooth_commands
from nav_skill2.learning.ppo import ActorCritic,PPO
from nav_skill2.learning.symmetry import mirror_legs,mirror_observations,mirror_loss,exploration_schedule
from nav_skill2.learning.amp import AMP
from nav_skill2.utils.runtime import dataset_path
ROOT=Path(__file__).resolve().parents[1]

class Optimization(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2);torch.manual_seed(6)
        self.task,self.cfg=load_config(ROOT/'configs/nav.json')

    def test_mirror_axes_joint_order_and_history(self):
        x=torch.randn(4,ACTOR_OBS)
        torch.testing.assert_close(mirror_observations(mirror_observations(x)),x)
        obs=torch.arange(63,dtype=torch.float32).repeat(5).unsqueeze(0)
        f=mirror_observations(obs).reshape(5,63)
        torch.testing.assert_close(f[0,:6],torch.tensor([0.,1.,-2.,3.,-4.,5.]))
        torch.testing.assert_close(f[0,60:],torch.tensor([60.,-61.,-62.]))
        torch.testing.assert_close(f[0,18:24],torch.tensor([-18.,19.,20.,-21.,22.,-23.]))
        torch.testing.assert_close(mirror_legs(torch.arange(12.)),torch.tensor([-3.,4.,5.,0.,1.,2.,-9.,10.,11.,-6.,7.,8.]))
        self.assertEqual(f.shape,(5,63));torch.testing.assert_close(f[0],f[-1])

    def test_mirror_loss_has_actor_gradient_and_can_be_disabled(self):
        model=ActorCritic();obs=torch.randn(32,ACTOR_OBS)
        loss=mirror_loss(model.actor,obs);loss.backward()
        self.assertGreater(sum(float(p.grad.abs().sum()) for p in model.actor.parameters()),0.)
        self.assertIsNone(model.log_std.grad) # 不对随机噪声做镜像监督
        self.assertEqual(int(model.actor(obs)[:,12:].count_nonzero()),0)
        self.assertGreater(self.cfg.symmetry_weight,0.)

    def test_v4_pure_commands_have_independent_limits(self):
        levels=torch.arange(5).repeat(5000);c=sample_commands(levels,self.task)
        f=(c[:,0]>0)&(c[:,1]==0)&(c[:,2]==0);b=(c[:,0]<0)&(c[:,1]==0)&(c[:,2]==0)
        side=(c[:,0]==0)&(c[:,1]!=0)&(c[:,2]==0);turn=(c[:,:2].abs().sum(-1)==0)&(c[:,2]!=0)
        self.assertGreaterEqual(float(c[f,0].min()),.3)
        self.assertGreaterEqual(float(c[b,0].abs().min()),.15)
        self.assertGreaterEqual(float(c[side,1].abs().min()),.15)
        self.assertGreaterEqual(float(c[turn,2].abs().min()),.2)
        self.assertAlmostEqual(float(turn.float().mean()),.30,delta=.02)
        self.assertAlmostEqual(float((c[turn,2]>0).float().mean()),.5,delta=.03)
        limit=torch.tensor(self.task.speed_limits)[levels];back=torch.tensor(self.task.backward_speed_limits)[levels]
        self.assertTrue(bool((c[:,0]<=limit+1e-6).all()));self.assertTrue(bool((c[:,0]>=-back-1e-6).all()))
        self.assertTrue(bool((c[:,:2].norm(dim=-1)<=limit+1e-6).all()))
        # 起停不硬跳到最低采样速度。
        x=smooth_commands(torch.zeros(1,3),torch.tensor([[.3,0.,.2]]),torch.tensor([.02]),self.task)
        self.assertLess(float(x[0,0]),.3);self.assertGreater(float(x[0,0]),0.)

    def test_relative_soft_overspeed_and_legacy(self):
        c=torch.tensor([[0.,0.,.2]]);v=torch.zeros(1,3);w=torch.tensor([[0.,0.,.4]])
        old=motion_terms(c,v,w)[0]['overspeed'];new=motion_terms(c,v,w,self.task)[0]['overspeed']
        self.assertEqual(float(old),0.);self.assertGreater(float(new),0.)
        near=motion_terms(c,v,torch.tensor([[0.,0.,.24]]),self.task)[0]['overspeed']
        self.assertEqual(float(near),0.)

    def test_exploration_schedule_and_resumed_iteration(self):
        self.assertEqual(exploration_schedule(self.cfg,0),(.6,.005))
        self.assertEqual(exploration_schedule(self.cfg,500),(.6,.005))
        cap,entropy=exploration_schedule(self.cfg,4000)
        self.assertAlmostEqual(cap,.25);self.assertAlmostEqual(entropy,.001)
        cap,_=exploration_schedule(self.cfg,2000);self.assertGreater(cap,.25);self.assertLess(cap,.6)
        algo=PPO(ActorCritic(.6),self.cfg);algo.iteration=2000
        self.assertEqual(exploration_schedule(algo.cfg,algo.iteration),exploration_schedule(self.cfg,2000))

    def test_amp_matches_direction_and_speed_and_restores(self):
        self.cfg.amp_batch_size=16;self.cfg.amp_updates=1
        amp=AMP(self.cfg,dataset_path(self.cfg),'cpu')
        modes=torch.tensor([1,1,5,6]);speeds=torch.tensor([.3,.9,.2,.6])
        groups=amp.select_groups(modes,speeds)
        torch.testing.assert_close(amp.group_modes[groups],modes)
        torch.testing.assert_close(amp.group_speeds[groups],torch.tensor([.4,.8,.2,.5]))
        examples=torch.cat([amp.expert[amp.groups[int(g)][:1]] for g in groups])
        gates=torch.stack((torch.ones(4),torch.ones(4),modes.float(),speeds),-1)
        result=amp.transition(examples[:,:30],examples[:,30:],gates,gates,torch.zeros(4,dtype=torch.bool),.02)
        self.assertTrue(bool(torch.isfinite(result).all()));self.assertEqual(amp.size,4)
        torch.testing.assert_close(amp.replay_groups[:4],groups)
        self.assertTrue(torch.isfinite(torch.tensor(amp.update()['amp_loss'])))
        clone=AMP(self.cfg,dataset_path(self.cfg),'cpu');clone.load_state_dict(amp.state_dict())
        torch.testing.assert_close(clone.replay_groups[:4],groups)
        # 切换参考速度组时不拼接跨组转换。
        changed=gates.clone();changed[0,3]=.9
        before=amp.size;amp.transition(examples[:1,:30],examples[:1,30:],gates[:1],changed[:1],torch.zeros(1,dtype=torch.bool),.02)
        self.assertEqual(before,amp.size)

if __name__=='__main__':unittest.main()
