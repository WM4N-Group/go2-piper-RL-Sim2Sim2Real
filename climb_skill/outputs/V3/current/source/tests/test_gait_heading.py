import math
import unittest
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, PPOConfig, configuration, require_implementation, GAIT_HEADING_REVISION, load_config,
)
from climb_skill.tasks.direct.climb_skill.mdp.gait_quality import (
    target_curvature, forward_pose_ready, contact_slip,
)
from climb_skill.tasks.direct.climb_skill.mdp.flat_stability import flat_surface_gate
from climb_skill.tasks.direct.climb_skill.mdp.geometry import stable_timer


class GaitHeading(unittest.TestCase):
    def test_constant_and_linear_targets_free_but_reversal_costs(self):
        a=torch.zeros(1,18);b=a.clone();b[:,:12]=.1;c=b*2
        self.assertEqual(float(target_curvature(c,b,a)),0.)
        torch.testing.assert_close(target_curvature(a,b,a),torch.tensor([4.]))

    def test_heading_wrap_lateral_corridor_and_default_compatibility(self):
        cfg=TaskConfig(traversal_heading_tolerance=math.radians(10))
        pos=torch.tensor([[2.4,0.,.4],[2.4,0.,.4],[2.4,.3,.4],[2.4,0.,.4]])
        yaw=torch.tensor([0.,math.pi/4,0.,2*math.pi])
        self.assertEqual(forward_pose_ready(pos,yaw,cfg).tolist(),[True,False,False,True])
        self.assertTrue(forward_pose_ready(pos,yaw,TaskConfig()).all())
        hold=stable_timer(torch.full((4,),.29),forward_pose_ready(pos,yaw,cfg),.02)
        self.assertEqual((hold>=.3).tolist(),[True,False,False,True])

    def test_body_gate_covers_wide_top_stance_but_excludes_crossing(self):
        cfg=TaskConfig(flat_use_body_gate=True)
        feet=torch.tensor([[[2.2,.45,.22],[2.2,-.45,.22],[1.6,.45,.22],[1.6,-.45,.22]]])
        forces=torch.zeros_like(feet);forces[...,2]=30.;h=torch.tensor([.2]);root=torch.tensor([[1.9,0.]])
        self.assertEqual(float(flat_surface_gate(feet,forces,h,cfg,root)),1.)
        cfg.flat_use_body_gate=False
        self.assertEqual(float(flat_surface_gate(feet,forces,h,cfg,root)),0.)
        cfg.flat_use_body_gate=True
        # A rear foot still below top height is an active crossing, not a flat top.
        feet[:,2,2]=.05
        self.assertEqual(float(flat_surface_gate(feet,forces,h,cfg,root)),0.)
        feet[:,2,2]=.22;feet[:,2,0]=.6
        self.assertEqual(float(flat_surface_gate(feet,forces,h,cfg,root)),0.)
        feet[:,2,0]=1.6
        self.assertEqual(float(flat_surface_gate(feet,forces,h,cfg,torch.tensor([[1.9,.45]]))),0.)
        feet[...,2]=.02;feet[...,0]=torch.tensor([.7,.7,.2,.2])
        self.assertEqual(float(flat_surface_gate(feet,forces,h,cfg,torch.tensor([[.4,0.]]))),0.)

    def test_contact_slip_counts_loaded_feet_only_across_mixed_surfaces(self):
        cfg=TaskConfig();h=torch.tensor([.2])
        feet=torch.tensor([[[1.,.2,.22],[1.,-.2,.22],[.5,.2,.02],[.5,-.2,.12]]])
        f=torch.zeros_like(feet);f[:,:3,2]=30.
        v=torch.zeros_like(feet);v[:,2,0]=.33;v[:,3,0]=100.
        torch.testing.assert_close(contact_slip(feet,f,v,h,cfg),torch.tensor([1/3]))
        torch.testing.assert_close(contact_slip(feet,f*0,v,h,cfg),torch.zeros(1))

    def test_new_profile_has_explicit_revision_and_preserves_video_cadence(self):
        root=Path(__file__).resolve().parents[1]
        task,ppo=load_config(root/'configs/rtx4090-forward-quality.json')
        c=configuration(task,ppo);require_implementation(c)
        self.assertEqual(c['implementation_revision'],GAIT_HEADING_REVISION)
        self.assertEqual(ppo.save_interval,500)
        self.assertAlmostEqual(task.finish_x,2.3)
        self.assertEqual(c['action_dimension'],18)
        c['implementation_revision']='climb_skill_v3_standing_start_candidate'
        with self.assertRaises(ValueError):require_implementation(c)
