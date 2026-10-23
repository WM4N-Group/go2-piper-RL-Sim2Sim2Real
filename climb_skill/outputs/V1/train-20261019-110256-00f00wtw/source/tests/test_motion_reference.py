from config_cases import load_case
"""左右反射符号、四腿共享相位、单腿不动/过折仍有成本，以及阶段门控。"""
import json
from pathlib import Path
import tempfile
import unittest
import torch
from climb_skill.learning.motion_reference import mirror_transitions, MotionReference
from climb_skill.learning.amp import AMP, AMPConfig
from climb_skill.tasks.direct.climb_skill.task_parameters import LEG_NAMES, TaskConfig, load_config
from climb_skill.tasks.direct.climb_skill.mdp.amp import body_plane_gate, snapshot
from types import SimpleNamespace

torch.set_num_threads(1)

class ReferenceTests(unittest.TestCase):
    def test_reflection_involution_and_vector_signs(self):
        x=torch.arange(60.).reshape(1,60)
        m=mirror_transitions(x)
        torch.testing.assert_close(mirror_transitions(m),x)
        torch.testing.assert_close(m[0,:3],torch.tensor([-3.,4.,5.]))
        torch.testing.assert_close(m[0,6:9],torch.tensor([-9.,10.,11.]))
        torch.testing.assert_close(m[0,12:18],torch.tensor([12.,-13.,14.,-15.,16.,-17.]))
        torch.testing.assert_close(m[0,18:21],torch.tensor([-21.,22.,23.]))

    def test_good_pose_bad_left_and_inactive_right(self):
        x=torch.zeros(3,60)
        for frame in [0,30]:
            x[:,frame:frame+12]=torch.tensor([.1,.8,-1.8,-.1,.8,-1.8,.1,.9,-1.8,-.1,.9,-1.8])
            x[:,frame+18:frame+30]=torch.tensor([0,1.,-2.,0,-1.,2.,0,-1.,2.,0,1.,-2.])
        ref=MotionReference(x[:1])
        x[1,[6,7,8,36,37,38]]=torch.tensor([.1,2.2,-2.7,.1,2.2,-2.7])
        x[2,[27,28,29,57,58,59]]=0  # 右后关节速度归零，不能用前腿好运动掩盖
        x[2,[11,41]]=-.9
        cost,legs=ref.cost(x)
        self.assertLess(cost[0].item(),1e-5)
        self.assertGreater(cost[1].item(),.1)
        self.assertGreater(cost[2].item(),.1)
        self.assertEqual(legs[1].argmax().item(),2)
        self.assertEqual(legs[2].argmax().item(),3)

    def test_four_legs_cannot_pick_different_reference_phases(self):
        expert=torch.zeros(2,60)
        expert[1,:12]=1;expert[1,30:42]=1
        mixed=expert[:1].clone();mixed[:,6:12]=1;mixed[:,36:42]=1
        cost,_=MotionReference(expert).cost(mixed)
        self.assertGreater(cost.item(),.1)

    def test_body_gate_does_not_depend_on_folded_feet_or_contact(self):
        cfg=TaskConfig(amp_enabled=True,amp_body_gate=True)
        pos=torch.tensor([[0.,0.,.3],[.75,0.,.4],[1.5,0.,.5]])
        heights=torch.full((3,),.2)
        gate=body_plane_gate(pos,heights,cfg)
        torch.testing.assert_close(gate,torch.tensor([1.,0.,1.]))
        env=SimpleNamespace(task=cfg,robot=SimpleNamespace(data=SimpleNamespace(
            joint_pos=torch.zeros(3,18),joint_vel=torch.zeros(3,18),root_lin_vel_b=torch.zeros(3,3),
            root_ang_vel_b=torch.zeros(3,3))),joint_ids=list(range(18)),heights=heights,
            _kinematics=lambda:(pos,None,torch.full((3,4,3),-100.)),startup_elapsed=torch.ones(3),
            startup_release_time=torch.zeros(3),startup_ready=torch.ones(3,dtype=torch.bool))
        cfg.startup_stand_seconds=1.;cfg.startup_ramp_seconds=2.
        _,g=snapshot(env)
        torch.testing.assert_close(g,.5*gate)

    def test_no_style_income_but_reference_cost_when_stopped_and_resume_contract(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'data.json'
            expert=torch.ones(40,60)
            path.write_text(json.dumps(dict(format='climb_amp_pairs_v1',dt=.02,joint_order=list(LEG_NAMES),
                feature_order=['joint_position_12','body_linear_velocity_3','body_angular_velocity_3','joint_velocity_12'],pairs=expert.tolist())))
            cfg=AMPConfig(dataset=str(path),reference_weight=1.,mirror_reference=True,batch_size=8,updates=1)
            amp=AMP(cfg,'cpu')
            reward,_=amp.transition(torch.zeros(2,30),torch.zeros(2,30),torch.ones(2),torch.ones(2),
                torch.tensor([False,True]),.02,movement=torch.zeros(2))
            self.assertLess(reward[0].item(),0)
            self.assertEqual(reward[1].item(),0)
            self.assertEqual(amp.last_diagnostics['amp_style_positive'].item(),0)
            self.assertGreater(amp.update()['amp_discriminator_loss'],0)
            state=amp.state_dict()
            restored=AMP(cfg,'cpu');restored.load_state_dict(state)
            torch.testing.assert_close(restored.replay[:restored.size],amp.replay[:amp.size])
            torch.testing.assert_close(restored.reference.expert,amp.reference.expert)
            changed=AMP(AMPConfig(dataset=str(path),reference_weight=2.,mirror_reference=True),'cpu')
            with self.assertRaisesRegex(ValueError,'configuration changed'): changed.load_state_dict(state)

    def test_new_config_does_not_change_user_previous_config(self):
        root=Path(__file__).resolve().parents[1]
        old,old_ppo=load_case('legacy_amp')
        new,new_ppo=load_case('legacy_amp_reference')
        self.assertFalse(old.amp_body_gate);self.assertTrue(new.amp_body_gate)
        self.assertEqual(new.num_envs,old.num_envs)  # 用户已将并行数改到4096，保留
        self.assertEqual(new_ppo.save_interval,100)
        self.assertGreater(new_ppo.amp['reference_weight'],0)

class WorkspaceTests(unittest.TestCase):
    def test_only_rear_targets_clipped_and_old_behavior_unchanged(self):
        from climb_skill.tasks.direct.climb_skill.mdp.joint_workspace import rear_target_workspace
        x=torch.zeros(2,18);x[:,[7,10]]=2.2;x[0,[8,11]]=-2.7;x[1,[8,11]]=-.93
        x[:,12:]=torch.arange(6.)
        old=TaskConfig()
        self.assertIs(rear_target_workspace(x,old),x)
        cfg=TaskConfig(amp_enabled=True,amp_body_gate=True,rear_workspace_enabled=True,
            walking_refinement_enabled=True,diagonal_gait_enabled=True,flat_walking_enabled=True)
        cfg.validate();y=rear_target_workspace(x,cfg)
        torch.testing.assert_close(y[:,[7,10]],torch.full((2,2),1.8))
        torch.testing.assert_close(y[0,[8,11]],torch.full((2,),-2.5))
        torch.testing.assert_close(y[1,[8,11]],torch.full((2,),-1.05))
        other=[i for i in range(18) if i not in (7,8,10,11)]
        torch.testing.assert_close(y[:,other],x[:,other])
        self.assertEqual(x[0,7].item(),torch.tensor(2.2).item())

if __name__=='__main__':unittest.main()
