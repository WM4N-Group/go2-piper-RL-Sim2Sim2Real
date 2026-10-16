"""Geometry and support checks only; physical tests run on the remote Isaac host."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
import torch

root = Path(__file__).resolve().parents[1]/'source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp'
package = types.ModuleType('_guidance_math')
package.__path__ = [str(root)]
sys.modules[package.__name__] = package
from _guidance_math.climb_guidance import inset_support_target, triangle_margin, loaded_leg_reference, edge_lift_reference, balanced_vertical_loads, balanced_acceleration_loads, unloaded_support_ready, LandingContact, mixed_support_body_height
from _guidance_math.climb_leg_kinematics import LegKinematics
from _guidance_math.climb_guidance import feedback_unload, support_plane_pose, feasible_support_pose
from crawl_leg_kinematics import LegKinematics as AuditedKinematics


class GuidanceChecks(unittest.TestCase):
    def test_front_stall_trim_scope_retains_platform_and_early_limits(self):
        from _guidance_math.climb_guidance import front_stall_trim_limit, UnloadForceTrim
        feet=torch.tensor([[[.5,.1,.02],[.5,-.1,.02],[.1,.1,.02],[.1,-.1,.02]]]).repeat(6,1,1)
        leg=torch.tensor([1,1,1,2,1,1]);start=torch.tensor([[.5,-.1,.02]]).repeat(6,1);landing=start.clone();landing[:,0]=.85;landing[:,2]=.224
        age=torch.tensor([9.99,10.,0.,20.,20.,20.]);force=torch.tensor([8.,8.,9.,8.,8.,8.])
        feet[4,1,2]=.22;start[4,2]=.22;landing[5,2]=.02
        torch.testing.assert_close(front_stall_trim_limit(feet,leg,start,landing,age,force),torch.tensor([8.,10.,10.,8.,8.,8.]))
        trim=UnloadForceTrim(1,'cpu');trim.force_n[:]=8.;trim.stall_age[:]=10.;previous=8.
        for _ in range(100):
            limit=front_stall_trim_limit(feet[:1],leg[:1],start[:1],landing[:1],trim.stall_age,trim.force_n)
            trim.update(torch.tensor([6.65]),torch.tensor([True]),torch.zeros(1),.02,max_force=limit)
            self.assertLessEqual(trim.force_n.item()-previous,.040001);previous=trim.force_n.item()
        self.assertAlmostEqual(trim.force_n.item(),10.)
        # Real unload confirmation must not abruptly lose the added correction.
        for _ in range(11):
            limit=front_stall_trim_limit(feet[:1],leg[:1],start[:1],landing[:1],trim.stall_age,trim.force_n)
            trim.update(torch.tensor([4.9]),torch.tensor([True]),torch.zeros(1),.02,max_force=limit)
        self.assertAlmostEqual(trim.force_n.item(),10.)
        trim.update(torch.tensor([4.9]),torch.tensor([False]),torch.zeros(1),.02,max_force=10.)
        self.assertAlmostEqual(trim.force_n.item(),9.96,places=5)
        trim.force_n[:]=10.;previous=10.
        for progress in [.05,.1,.2,.25]:
            applied=trim.update(torch.zeros(1),torch.tensor([False]),torch.tensor([progress]),.02,max_force=8.).item()
            self.assertLess(applied,previous);previous=applied
        self.assertEqual(previous,0.)

    def test_exact_front_stall_trim_keeps_actuator_and_joint_headroom(self):
        import json
        from _guidance_math.climb_guidance import rotate_vector, unloaded_support_ready
        f=json.loads((Path(__file__).parent/'fixtures/climb_front_stall_trim.json').read_text());r=f['trace'];ts=lambda k:torch.tensor([r[k]])
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(usd)
        q=ts('joint_position')[:,torch.tensor([[0,4,9],[1,5,10],[2,6,11],[3,7,12]])]
        up=rotate_vector(ts('robot_quaternion'),torch.tensor([[0.,0.,1.]]),True);jz=(model.jacobian(q)*up[:,None,:,None]).sum(-2)
        bounds=torch.tensor(f['capture']['bounds']);effort=torch.tensor(f['capture']['load']['effort'])
        tau=ts('guidance_load_torque').clone();tau[:,1]+=2.*jz[:,1];command=ts('guidance_nominal_joints')+tau/30.
        self.assertGreater(torch.minimum(command-bounds[...,0],bounds[...,1]-command).min().item(),.12)
        self.assertGreater((.75*effort-tau.abs()).min().item(),1.)
        forces=ts('foot_contact_force_z');zero=torch.zeros(1,3)
        self.assertFalse(unloaded_support_ready(forces,torch.tensor([1]),ts('guidance_support_margin'),zero,zero).item())
        forces[:,1]=4.9
        self.assertTrue(unloaded_support_ready(forces,torch.tensor([1]),ts('guidance_support_margin'),zero,zero).item())

    def test_settled_recovery_requires_age_and_quiet_dwell_after_both_front_steps(self):
        import json,copy
        from _guidance_math.climb_guidance import StageGuidance,PlatformHoldTracking
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_final_tracking.json').read_text());r=f['terminal_trace'];ts=lambda k:torch.tensor([r[k]]);ns=types.SimpleNamespace
        class Scene(dict):pass
        forces=torch.zeros(1,4,3);forces[:,:,2]=ts('foot_contact_force_z')
        scene=Scene(contact_forces=ns(data=ns(net_forces_w=forces)));scene.env_origins=torch.zeros(1,3)
        robot=ns(root_pos_w=ts('robot_position'),root_quat_w=ts('robot_quaternion'),projected_gravity_b=ts('robot_gravity'),root_lin_vel_w=ts('robot_velocity'),root_ang_vel_w=ts('robot_angular_velocity'))
        a=ns(cfg=ns(guidance_platform_extension_tracking=True,guidance_platform_settled_recovery=True),_asset=ns(data=robot),_env=ns(scene=scene,step_dt=.02),rows=torch.arange(1),sensor_ids=list(range(4)),clock=ns(leg=torch.tensor([1]),progress=torch.ones(1)),start=ts('crawl_foot_reference'),landing=ts('crawl_landing_position'),extension=ns(moving=torch.tensor([False]),completed=torch.tensor([2])),platform_hold=torch.tensor([True]),feet_positions=lambda:ts('feet_position'),contacts=lambda:torch.ones(1,4,dtype=torch.bool))
        h=StageGuidance.__new__(StageGuidance);h.a=a;h.hold_tracking=PlatformHoldTracking(1,'cpu',.75);h.age=torch.tensor([2.99]);h.target=ts('guidance_body_target');h.target_orientation=ts('guidance_target_orientation');h.engaged=torch.tensor([True]);h.margin=ts('guidance_support_margin');h.unload_fraction=torch.zeros(1);h.pose_feasible=torch.tensor([True]);h.swing_path_ready=torch.tensor([True]);h.valid_legs=torch.ones(1,4,dtype=torch.bool);h.command_limit_excess=torch.zeros(1,4);h.load_replan=torch.tensor([False])
        for _ in range(70):h.update_platform_hold_tracking()
        self.assertEqual(h.hold_tracking.extra.item(),0.)
        h.age[:]=3.;robot.root_lin_vel_w[:,0]=.002
        for _ in range(70):h.update_platform_hold_tracking()
        self.assertEqual(h.hold_tracking.extra.item(),0.)
        robot.root_lin_vel_w[:]=ts('robot_velocity');baseline=copy.deepcopy(h)
        for _ in range(49):h.update_platform_hold_tracking()
        self.assertEqual(h.hold_tracking.extra.item(),0.)
        for _ in range(52):h.update_platform_hold_tracking()
        self.assertGreater(h.hold_tracking.extra.item(),0.)
        self.assertEqual(a.extension.completed.item(),2);self.assertFalse(a.extension.moving.item())
        # Once corrective motion starts, retain the original calm bounds instead
        # of repeatedly toggling feedback at the stricter start threshold.
        robot.root_lin_vel_w[:,0]=.004;before=h.hold_tracking.extra.clone();h.update_platform_hold_tracking()
        self.assertGreater(h.hold_tracking.extra.item(),before.item())
        robot.root_lin_vel_w[:,0]=.03;before=h.hold_tracking.extra.clone();h.update_platform_hold_tracking()
        torch.testing.assert_close(h.hold_tracking.extra,before-.002)
        for case in ['disabled','weak_load','moving','contact','angle_speed','no_residual','bad_command']:
            j=copy.deepcopy(baseline)
            if case=='disabled':j.a.cfg.guidance_platform_settled_recovery=False
            elif case=='weak_load':j.a._env.scene['contact_forces'].data.net_forces_w[0,2,2]=7.9
            elif case=='moving':j.a.extension.moving[:]=True
            elif case=='contact':j.a.contacts=lambda:torch.tensor([[True,True,False,True]])
            elif case=='angle_speed':j.a._asset.data.root_ang_vel_w[:,0]=.011
            elif case=='no_residual':j.target[:]=j.a._asset.data.root_pos_w;j.target_orientation[:]=j.a._asset.data.root_quat_w
            elif case=='bad_command':j.command_limit_excess[:,0]=.001
            for _ in range(70):j.update_platform_hold_tracking()
            self.assertEqual(j.hold_tracking.extra.item(),0.,case)

    def test_exact_final_tracking_gain_preserves_joint_headroom(self):
        self._check_hold_gain_fixture('climb_platform_final_tracking.json',[.5,.75,1.,1.25],.5,min_command_margin=.1)

    def test_platform_extension_tracking_corrects_residual_before_original_unload_scope(self):
        import json,copy
        from _guidance_math.climb_guidance import StageGuidance,PlatformHoldTracking
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_extension_tracking.json').read_text());r=f['terminal_trace']
        ts=lambda k:torch.tensor([r[k]]);ns=types.SimpleNamespace
        class Scene(dict):pass
        forces=torch.zeros(1,4,3);forces[:,:,2]=ts('foot_contact_force_z')
        scene=Scene(contact_forces=ns(data=ns(net_forces_w=forces)));scene.env_origins=torch.zeros(1,3)
        robot=ns(root_pos_w=ts('robot_position'),root_quat_w=ts('robot_quaternion'),projected_gravity_b=ts('robot_gravity'),root_lin_vel_w=ts('robot_velocity'),root_ang_vel_w=ts('robot_angular_velocity'))
        a=ns(cfg=ns(guidance_platform_extension_tracking=True,guidance_platform_settled_recovery=False),_asset=ns(data=robot),_env=ns(scene=scene,step_dt=.02),rows=torch.arange(1),sensor_ids=list(range(4)),
            clock=ns(leg=torch.tensor([1]),progress=torch.zeros(1)),start=ts('crawl_foot_reference'),landing=ts('crawl_landing_position'),
            extension=ns(moving=torch.tensor([True]),completed=torch.tensor([1])),platform_hold=torch.tensor([False]),
            feet_positions=lambda:ts('feet_position'),contacts=lambda:torch.ones(1,4,dtype=torch.bool))
        h=StageGuidance.__new__(StageGuidance);h.a=a;h.hold_tracking=PlatformHoldTracking(1,'cpu',.75);h.age=ts('guidance_reference_age');h.target=ts('guidance_body_target');h.target_orientation=ts('guidance_target_orientation');h.engaged=torch.tensor([True]);h.margin=ts('guidance_support_margin');h.unload_fraction=torch.ones(1);h.pose_feasible=torch.tensor([True]);h.swing_path_ready=torch.tensor([True]);h.valid_legs=torch.ones(1,4,dtype=torch.bool);h.command_limit_excess=torch.zeros(1,4);h.load_replan=torch.tensor([False])
        # Actual10.6mm residual still fails the original1cm trim scope.
        self.assertFalse(h.platform_extension_trim_scope(a.feet_positions(),a.contacts()).item())
        for _ in range(49):h.update_platform_hold_tracking()
        self.assertEqual(h.hold_tracking.extra.item(),0.)
        for _ in range(80):h.update_platform_hold_tracking()
        self.assertGreater(h.hold_tracking.extra.item(),0.)
        baseline=copy.deepcopy(h)
        # Feedback stays latched during the original measured-unload dwell.
        robot.root_pos_w[:]=h.target;forces[0,1,2]=4.9;before=h.hold_tracking.extra.clone()
        for _ in range(12):h.update_platform_hold_tracking()
        self.assertGreaterEqual(h.hold_tracking.extra.item(),before.item())
        self.assertTrue(h.platform_extension_trim_scope(a.feet_positions(),a.contacts()).item())
        a.clock.progress[:]=.005;before=h.hold_tracking.extra.clone();h.update_platform_hold_tracking()
        torch.testing.assert_close(h.hold_tracking.extra,before-.002)
        for case in ['disabled','support_load','contact','swing','unloaded','position','tilt','speed','angle_speed','pose','swing_preview','command','replan','margin','age']:
            j=copy.deepcopy(baseline);aa=j.a;j.hold_tracking.reset(torch.tensor([True]))
            if case=='disabled':aa.cfg.guidance_platform_extension_tracking=False
            elif case=='support_load':aa._env.scene['contact_forces'].data.net_forces_w[0,2,2]=7.9
            elif case=='contact':aa.contacts=lambda:torch.tensor([[True,True,False,True]])
            elif case=='swing':aa.clock.progress[:]=.01
            elif case=='unloaded':aa._env.scene['contact_forces'].data.net_forces_w[0,1,2]=4.9
            elif case=='position':j.target[:,0]+=.03
            elif case=='tilt':aa._asset.data.projected_gravity_b[:,2]=-.93
            elif case=='speed':aa._asset.data.root_lin_vel_w[:,0]=.03
            elif case=='angle_speed':aa._asset.data.root_ang_vel_w[:,0]=.11
            elif case=='pose':j.pose_feasible[:]=False
            elif case=='swing_preview':j.swing_path_ready[:]=False
            elif case=='command':j.command_limit_excess[:,0]=.001
            elif case=='replan':j.load_replan[:]=True
            elif case=='margin':j.margin[:]=.024
            elif case=='age':j.age[:]=9.99
            for _ in range(70):j.update_platform_hold_tracking()
            self.assertEqual(j.hold_tracking.extra.item(),0.,case)

    def test_exact_extension_tracking_gain_preserves_joint_headroom(self):
        self._check_hold_gain_fixture('climb_platform_extension_tracking.json',[.5,.75,1.,1.25],.5,min_command_margin=.1)

    def test_platform_extension_trim_only_after_settled_full_ascent(self):
        import json,copy
        from _guidance_math.climb_guidance import StageGuidance
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_extension_unload.json').read_text())
        r=f['trace'];ts=lambda k:torch.tensor([r[k]]);ns=types.SimpleNamespace
        robot=ns(root_pos_w=ts('robot_position'),root_quat_w=ts('robot_quaternion'))
        a=ns(_asset=ns(data=robot),_env=ns(scene=ns(env_origins=torch.zeros(1,3))),
            clock=ns(leg=torch.tensor([0])),start=ts('crawl_foot_reference'),landing=ts('crawl_landing_position'),
            extension=ns(moving=torch.tensor([True]),completed=torch.tensor([0])),platform_hold=torch.tensor([False]))
        h=StageGuidance.__new__(StageGuidance);h.a=a;h.age=ts('guidance_reference_age');h.target=ts('guidance_body_target');h.target_orientation=ts('guidance_target_orientation')
        feet=ts('feet_position');contacts=torch.ones(1,4,dtype=torch.bool)
        self.assertTrue(h.platform_extension_trim_scope(feet,contacts).item())
        contacts[0,0]=False  # Selected foot may unload; the three supports may not.
        self.assertTrue(h.platform_extension_trim_scope(feet,contacts).item())
        contacts[:]=True
        for case in ['rear_ground','support_lost','rear_leg','not_moving','finished','hold','too_early','position','angle','backward','height','outside']:
            j=copy.deepcopy(h);ff=feet.clone();cc=contacts.clone()
            if case=='rear_ground':ff[:,2:,2]=.023
            elif case=='support_lost':cc[0,1]=False
            elif case=='rear_leg':j.a.clock.leg[:]=3
            elif case=='not_moving':j.a.extension.moving[:]=False
            elif case=='finished':j.a.extension.completed[:]=2
            elif case=='hold':j.a.platform_hold[:]=True
            elif case=='too_early':j.age[:]=9.99
            elif case=='position':j.target[:,0]+=.02
            elif case=='angle':j.target_orientation[:]=torch.tensor([[.99,.14106736,0.,0.]])
            elif case=='backward':j.a.landing[:,0]=j.a.start[:,0]-.04
            elif case=='height':j.a.landing[:,2]+=.2
            elif case=='outside':ff[:,1,1]=.57
            self.assertFalse(j.platform_extension_trim_scope(ff,cc).item(),case)

    def test_exact_platform_unload_trim_keeps_joint_and_effort_headroom(self):
        import json
        from _guidance_math.climb_leg_kinematics import rotate_vector
        from _guidance_math.climb_guidance import UnloadForceTrim
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_extension_unload.json').read_text());r=f['trace']
        ts=lambda k:torch.tensor([r[k]]);model=LegKinematics.from_usd(root.parents[3]/'assets/go2_piper/go2_piper.usd')
        slots=torch.tensor([[0,4,9],[1,5,10],[2,6,11],[3,7,12]])
        q=ts('joint_position')[:,slots];bounds=torch.tensor(f['capture']['bounds']);effort=torch.tensor(f['capture']['preview']['effort'])
        z=rotate_vector(ts('robot_quaternion'),torch.tensor([[0.,0.,1.]]),True)
        jz=(model.jacobian(q)*z[:,None,:,None]).sum(-2)
        original=ts('guidance_load_torque');nominal=ts('guidance_nominal_joints')
        for force in [0.,2.,4.,8.]:
            torque=original.clone();torque[:,0]+=jz[:,0]*force
            command=nominal+torque/30.
            self.assertTrue((torque.abs()<.75*effort).all())
            self.assertGreater(torch.minimum(command-bounds[...,0],bounds[...,1]-command).min().item(),.03)
            torch.testing.assert_close(torque[:,1:],original[:,1:])
        trim=UnloadForceTrim(1,'cpu');forces=ts('foot_contact_force_z');zero=torch.zeros(1,3)
        for _ in range(300):
            old=trim.applied_n.clone();trim.update(forces[:,0],torch.tensor([True]),torch.zeros(1),.02)
            self.assertLessEqual((trim.applied_n-old).abs().max().item(),.040001)
        # Extra force alone cannot satisfy the measured unload gate.
        self.assertFalse(unloaded_support_ready(forces,torch.tensor([0]),ts('guidance_support_margin'),zero,zero).item())
        forces[:,0]=4.9
        self.assertTrue(unloaded_support_ready(forces,torch.tensor([0]),ts('guidance_support_margin'),zero,zero).item())

    def test_hold_tracking_explicit_bound_keeps_default_and_rate(self):
        from _guidance_math.climb_guidance import PlatformHoldTracking
        default=PlatformHoldTracking(1,'cpu');explicit=PlatformHoldTracking(1,'cpu',.5);larger=PlatformHoldTracking(1,'cpu',.75)
        args=(torch.tensor([True]),torch.tensor([20.]),torch.tensor([.01064]),torch.tensor([.02954]),.02)
        for _ in range(500):
            before=larger.extra.clone()
            for h in [default,explicit,larger]:h.update(*args)
            self.assertTrue(torch.equal(default.extra,explicit.extra))
            self.assertLessEqual((larger.extra-before).abs().max().item(),.002001)
        self.assertEqual(default.extra.item(),.5);self.assertEqual(larger.extra.item(),.75)
        for invalid in [0.,-.1,.751,float('nan')]:
            with self.assertRaises(ValueError):PlatformHoldTracking(1,'cpu',invalid)

    def test_loaded_hold_tracking_waits_and_fades_without_relaxing_arrival(self):
        from _guidance_math.climb_guidance import PlatformHoldTracking
        h=PlatformHoldTracking(5,'cpu');supported=torch.tensor([True,True,False,True,True])
        age=torch.tensor([10.,9.,20.,20.,20.]);pos=torch.tensor([.01064,.01064,.01064,.021,.01064]);angle=torch.tensor([.02954]*4+[.051])
        for _ in range(49):h.update(supported,age,pos,angle,.02)
        self.assertTrue((h.extra==0).all())
        for _ in range(302):
            before=h.extra.clone();h.update(supported,age,pos,angle,.02)
            self.assertLessEqual((h.extra-before).abs().max().item(),.002001)
        torch.testing.assert_close(h.extra,torch.tensor([.5,0.,0.,0.,0.]))
        # Matching the unchanged1cm/.025rad gates must not remove the feedback
        # just before the one-second arrival dwell completes.
        pos[0]=.009;angle[0]=.023
        for _ in range(55):h.update(supported,age,pos,angle,.02)
        self.assertEqual(h.extra[0].item(),.5)
        supported[0]=False;before=h.extra.clone();h.update(supported,age,pos,angle,.02)
        self.assertAlmostEqual(h.extra[0].item(),.498,places=6)
        for _ in range(260):h.update(supported,age,pos,angle,.02)
        self.assertTrue((h.extra==0).all())
        h.extra[0]=.5;h.reset(torch.tensor([True,False,False,False,False]));self.assertEqual(h.extra[0].item(),0.)

    def test_hold_tracking_runtime_requires_measured_support_and_calm(self):
        import json
        from _guidance_math.climb_guidance import StageGuidance,PlatformHoldTracking
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_hold_tracking.json').read_text())['capture']
        ns=types.SimpleNamespace;ts=lambda k:torch.tensor(f[k]);forces=torch.zeros(1,4,3);forces[:,:,2]=ts('measured_foot_force_z')
        class Scene(dict):pass
        scene=Scene(contact_forces=ns(data=ns(net_forces_w=forces)));scene.env_origins=ts('env_origin')
        robot=ns(root_pos_w=ts('origin'),root_quat_w=ts('quaternion'),root_lin_vel_w=torch.zeros(1,3),root_ang_vel_w=torch.zeros(1,3))
        a=ns(cfg=ns(guidance_platform_extension_tracking=False,guidance_platform_settled_recovery=False),_asset=ns(data=robot),_env=ns(scene=scene,step_dt=.02),sensor_ids=list(range(4)),feet_positions=lambda:ts('feet'),contacts=lambda:torch.ones(1,4,dtype=torch.bool),platform_hold=torch.tensor([True]),extension=ns(moving=torch.tensor([False]),completed=torch.tensor([0])))
        h=StageGuidance.__new__(StageGuidance);h.a=a;h.hold_tracking=PlatformHoldTracking(1,'cpu');h.age=torch.tensor([20.]);h.target=ts('previous_target');h.target_orientation=ts('previous_quaternion');h.pose_feasible=torch.tensor([True]);h.valid_legs=torch.ones(1,4,dtype=torch.bool);h.command_limit_excess=torch.zeros(1,4)
        for _ in range(70):h.update_platform_hold_tracking()
        self.assertGreater(h.hold_tracking.extra.item(),0.)
        for blocked in ['load','motion','finished','command','contact']:
            h.hold_tracking.reset(torch.tensor([True]));forces[:,:,2]=ts('measured_foot_force_z');robot.root_lin_vel_w.zero_();a.extension.completed[:]=0;h.command_limit_excess.zero_();a.platform_hold[:]=True
            if blocked=='load':forces[0,3,2]=7.9
            if blocked=='motion':robot.root_lin_vel_w[0,0]=.03
            if blocked=='finished':a.extension.completed[:]=2
            if blocked=='command':h.command_limit_excess[0,0]=.001
            if blocked=='contact':a.platform_hold[:]=False
            for _ in range(70):h.update_platform_hold_tracking()
            self.assertEqual(h.hold_tracking.extra.item(),0.,blocked)

    def test_exact_loaded_hold_gain_preserves_joint_headroom(self):
        self._check_hold_gain_fixture('climb_platform_hold_tracking.json',[.5,.6,.75,1.],.5)
        self._check_hold_gain_fixture('climb_platform_hold_tracking_hc.json',[1.,1.1,1.25],1.)

    def _check_hold_gain_fixture(self, filename, gains, baseline_gain, min_command_margin=.38):
        import json
        from _guidance_math.climb_guidance import rotate_vector
        from _guidance_math.climb_body_clearance import leg_collision_primitives,leg_link_poses,primitive_box_gap
        f=json.loads((Path(__file__).parent/'fixtures'/filename).read_text());r=f['terminal_trace'];ts=lambda k:torch.tensor([r[k]])
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(usd);links=leg_collision_primitives(usd)
        quat=ts('robot_quaternion');pos=ts('robot_position');anchors=ts('guidance_anchors');target=ts('guidance_body_target');turn=ts('guidance_target_orientation');bounds=torch.tensor(f['capture']['bounds'])
        nominal=rotate_vector(turn[:,None],anchors-target[:,None],True);actual=rotate_vector(quat[:,None],anchors-pos[:,None],True)
        velocity=rotate_vector(quat,ts('robot_velocity'),True)[:,None]+torch.cross(rotate_vector(quat,ts('robot_angular_velocity'),True)[:,None].expand_as(nominal),nominal,dim=-1)
        for gain in gains:
            correction=gain*(nominal-actual)+.08*velocity;correction*= (.05/correction.norm(dim=-1).clamp_min(.05))[...,None]
            desired=nominal+correction;joints=model.inverse(desired);command=joints+ts('guidance_load_torque')/30.
            self.assertLess((model.forward(joints)-desired).norm(dim=-1).max().item(),.001)
            self.assertGreater(torch.minimum(joints-bounds[...,0],bounds[...,1]-joints).min().item(),.22)
            self.assertGreater(torch.minimum(command-bounds[...,0],bounds[...,1]-command).min().item(),min_command_margin)
            lp,lq=leg_link_poses(model,joints,pos,quat)
            self.assertGreater(primitive_box_gap(lp,lq,links,torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])[:,None,None]).min().item(),.005)
            if gain==baseline_gain:torch.testing.assert_close(joints,ts('guidance_nominal_joints'),atol=5e-5,rtol=0.)

    def test_followup_complete_swing_reserve_and_partial_transfer(self):
        import json
        from _guidance_math.climb_guidance import swing_path_preview, swing_preview_ready, predicted_tripod_margin
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        data=json.loads((Path(__file__).parent/'fixtures/climb_front_followup_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        for name,f in data.items():
            with self.subTest(name=name):
                ts=lambda k:torch.tensor(f[k])
                load={k:torch.tensor(v) for k,v in f['load'].items()}
                load.update(orientation=ts('quaternion'),rotation_active=torch.tensor([True]),
                            four_support_path=torch.tensor([True]))
                swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing_request'].items()}
                swing.update(gravity=load['gravity'],landing_probe_depth=torch.tensor([.015]),
                    landing_com=load['com'],landing_origin=ts('origin'),landing_weight=load['weight'],
                    landing_effort=load['effort'],minimum_gap=torch.tensor([.010]),
                    landing_orientation=ts('quaternion'),landing_rotation_active=torch.tensor([True]),
                    allow_partial_transfer=True)
                args=(model,ts('feet'),ts('target'),ts('origin'),ts('quaternion'),ts('bias'),
                    ts('bounds'),f['clearance'],body,ts('box_bounds'),True,links,load,swing)
                pose,turn,margin,valid=feasible_support_pose(*args)
                sm,se,sg=swing_path_preview(model,ts('feet'),pose[:,None],turn[:,None],ts('bounds'),swing,links,ts('box_bounds'))
                ready=valid[:,None]&swing_preview_ready(sm,se,sg,swing)
                if name=='2:0':
                    self.assertTrue(ready.item())
                    self.assertGreater(pose[0,2]-torch.tensor(f['result']['position'])[0,2],.015)
                    self.assertGreater(sg.item(),.010)
                elif name=='2:1':
                    # This recorded start already has a clearance deficit; no
                    # denser search can repair a path that includes that start.
                    self.assertFalse(valid.item())
                    self.assertFalse(feasible_support_pose(*args,height_samples=65)[3].item())
                elif name=='11:1':
                    # A safe four-contact intermediate transfer may be useful,
                    # but its unchecked/blocked swing must remain unreleased.
                    self.assertTrue(valid.item())
                    self.assertFalse(ready.item())
                    self.assertLess(predicted_tripod_margin(ts('feet'),ts('origin'),pose[:,None],turn[:,None],load).item(),.025)
                else:
                    self.assertTrue(ready.item())
                    torch.testing.assert_close(pose,torch.tensor(f['result']['position']),atol=1e-6,rtol=0.)

    def test_followup_reserve_does_not_change_original_swing_gate(self):
        from _guidance_math.climb_guidance import swing_preview_ready
        margin=torch.tensor([[.04,.04,.04],[.04,.029,.04]])
        error=torch.tensor([[0.,0.,0.],[0.,0.,.0011]])
        gap=torch.tensor([[.0049,.007,.011],[.011,.011,.011]])
        self.assertEqual(swing_preview_ready(margin,error,gap,{}).tolist(),
            [[False,True,True],[True,False,False]])
        self.assertEqual(swing_preview_ready(margin,error,gap,{'minimum_gap':torch.tensor([.010,.005])}).tolist(),
            [[False,False,True],[True,False,False]])

    def test_front_followup_trim_requires_mixed_support_and_forward_front_step(self):
        from _guidance_math.climb_guidance import front_followup_trim_scope
        # Observed env2: both front feet on the20cm box, both rear feet on ground.
        feet=torch.tensor([[[.85153,.17124,.22365],[.85008,-.18215,.22381],
            [.41141,.18533,.02297],[.40166,-.19008,.02305]]]).repeat(9,1,1)
        contacts=torch.ones(9,4,dtype=torch.bool);leg=torch.zeros(9,dtype=torch.long)
        start=feet[:,0].clone();landing=start.clone();landing[:,0]+=.22
        # Selected foot may lose contact during successful unloading. The other
        # three feet must remain planted; initial ascent and final expansion differ.
        contacts[1,0]=False
        contacts[2,3]=False
        feet[3,1,2]=.024
        feet[4,2:,0]=.85;feet[4,2:,2]=.224
        leg[5]=3
        landing[6,0]=start[6,0]
        landing[7,2]+=.20
        feet[8,0,1]=.60
        self.assertEqual(front_followup_trim_scope(feet,contacts,leg,start,landing).tolist(),
            [True,True,False,False,False,False,False,False,False])

    def test_front_followup_trim_keeps_measured_five_newton_release_gate(self):
        from _guidance_math.climb_guidance import UnloadForceTrim
        trim=UnloadForceTrim(1,'cpu')
        forces=torch.tensor([[5.358878,124.179962,81.322258,26.236456]])
        leg=torch.zeros(1,dtype=torch.long);zero=torch.zeros(1,3)
        for _ in range(200):
            trim.update(forces[:,0],torch.tensor([True]),torch.zeros(1),.02)
        self.assertGreater(trim.applied_n.item(),0.)
        self.assertLessEqual(trim.applied_n.item(),8.)
        self.assertFalse(unloaded_support_ready(forces,leg,torch.tensor([.0287]),zero,zero).item())
        forces[:,0]=4.9
        self.assertTrue(unloaded_support_ready(forces,leg,torch.tensor([.0287]),zero,zero).item())

    def test_final_adjustment_waits_for_both_loaded_steps_and_keeps_fixed_goal(self):
        import json
        from _guidance_math.climb_guidance import StageGuidance
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_final_pose.json').read_text())['31']
        ts=lambda k:torch.tensor(f[k]);ns=types.SimpleNamespace
        class Scene(dict):
            pass
        scene=Scene();forces=torch.zeros(1,4,3);forces[:,:,2]=ts('measured_foot_force_z')
        scene['contact_forces']=ns(data=ns(net_forces_w=forces))
        data=ns(root_pos_w=ts('origin'),root_quat_w=ts('quaternion'),
            root_lin_vel_w=torch.zeros(1,3),root_ang_vel_w=torch.zeros(1,3),
            projected_gravity_b=torch.tensor([[0.,0.,-1.]]),joint_pos=ts('joint_position').reshape(1,12),
            soft_joint_pos_limits=ts('bounds').reshape(1,12,2),
            joint_effort_limits=torch.tensor(f['preview']['effort']).reshape(1,12))
        a=ns(_asset=ns(data=data,num_joints=12,root_physx_view=ns(
                get_gravity_compensation_forces=lambda:torch.tensor(f['preview']['gravity']).reshape(1,12))),
            _env=ns(step_dt=.02,device='cpu',scene=scene),_joint_ids=list(range(12)),sensor_ids=list(range(4)),
            cfg=ns(guidance_body_clearance=.28,guidance_pose_fixtures=False,guidance_platform_final_recovery_rise=False),
            extension=ns(completed=torch.tensor([1]),moving=torch.tensor([False])),
            platform_hold=torch.tensor([True]),contacts=lambda:torch.ones(1,4,dtype=torch.bool),
            feet_positions=lambda:ts('feet'),center_of_mass=lambda:torch.tensor(f['preview']['com']),
            mass=torch.tensor(f['preview']['weight'])[:,None]/9.81,reference=ts('reference').reshape(1,12))
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        h=ns(a=a,age=torch.tensor([3.]),valid_legs=torch.ones(1,4,dtype=torch.bool),
            command_limit_excess=torch.zeros(1,4),target=ts('origin'),target_orientation=ts('quaternion'),
            platform_final_retry_age=torch.tensor([2.]),platform_final_stable=torch.zeros(1),
            platform_final_started=torch.tensor([False]),platform_final_goal=ts('origin'),
            platform_final_segments=torch.zeros(1,dtype=torch.long),platform_final_rejections=torch.zeros(1,dtype=torch.long),
            slots=torch.arange(12).reshape(4,3),model=LegKinematics.from_usd(usd),
            body_bounds=base_collision_bounds(usd),box_bounds=ts('box_bounds'),link_bounds=leg_collision_primitives(usd))
        h.capture_hold=lambda mask:h.age.__setitem__(mask,0.)
        h.hold_tracking=ns(latched=torch.tensor([False]))
        StageGuidance.adjust_platform_final_pose(h)
        self.assertFalse(h.platform_final_started.item())
        a.extension.completed[:]=2;forces[0,0,2]=0.
        StageGuidance.adjust_platform_final_pose(h)
        self.assertFalse(h.platform_final_started.item())
        forces[:,:,2]=ts('measured_foot_force_z')
        StageGuidance.adjust_platform_final_pose(h)
        self.assertFalse(h.platform_final_started.item())
        h.platform_final_stable[:]=.5
        StageGuidance.adjust_platform_final_pose(h)
        self.assertEqual(h.platform_final_segments.item(),1)
        fixed=h.platform_final_goal.clone()
        torch.testing.assert_close(data.root_pos_w,ts('origin'))
        a.cfg.guidance_platform_final_recovery_rise=True
        data.root_pos_w=h.target.clone();h.age[:]=3.;h.platform_final_stable[:]=.5;h.platform_final_retry_age[:]=2.
        StageGuidance.adjust_platform_final_pose(h)
        self.assertEqual(h.platform_final_segments.item(),2)
        self.assertAlmostEqual(float((h.target-data.root_pos_w)[0,2]),.01,places=6)
        torch.testing.assert_close(h.platform_final_goal,fixed)
        h.hold_tracking.latched[:]=True
        data.root_pos_w=h.target.clone();h.age[:]=3.;h.platform_final_stable[:]=.5;h.platform_final_retry_age[:]=2.
        StageGuidance.adjust_platform_final_pose(h)
        self.assertEqual(h.platform_final_segments.item(),3)
        self.assertAlmostEqual(float((h.target-data.root_pos_w)[0,2]),.015,places=6)
        torch.testing.assert_close(h.platform_final_goal,fixed)
        # gw7/29 remain about2.5mm below an already commanded fixed height.
        # This must preserve the hold instead of resetting anchors every2.5s.
        h.target=fixed.clone();data.root_pos_w=fixed.clone();data.root_pos_w[:,2]-=.0026
        h.age[:]=5.;h.platform_final_stable[:]=.5;h.platform_final_retry_age[:]=2.
        def unexpected_capture(mask):
            self.fail('An already commanded final goal must not recapture support feet')
        h.capture_hold=unexpected_capture
        for _ in range(10):
            StageGuidance.adjust_platform_final_pose(h)
        self.assertEqual(h.platform_final_segments.item(),3)
        self.assertEqual(h.age.item(),5.)
        torch.testing.assert_close(h.target,fixed)
        torch.testing.assert_close(h.platform_final_goal,fixed)

    def test_final_recovery_rise_checks_recorded_loaded_paths_and_bounds(self):
        import json
        from _guidance_math.climb_guidance import feasible_platform_final_step
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        records=json.loads((Path(__file__).parent/'fixtures/climb_platform_final_recovery_rise.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(usd)
        for f in records:
            ts=lambda k:torch.tensor(f[k]);origin=ts('origin');preview={k:torch.tensor(v) for k,v in f['preview'].items()}
            args=(model,ts('feet'),origin,ts('quaternion'),ts('bias'),ts('bounds'),base_collision_bounds(usd),ts('box_bounds'),leg_collision_primitives(usd),preview,ts('goal'))
            old=feasible_platform_final_step(*args)
            unchanged=feasible_platform_final_step(*args,rise_limit=torch.tensor([.01]))
            for x,y in zip(old,unchanged):torch.testing.assert_close(x,y,rtol=0,atol=0)
            pose,quat,margin,valid=feasible_platform_final_step(*args,rise_limit=torch.tensor([.015]))
            self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
            self.assertAlmostEqual(float((pose-origin)[0,2]),.015,places=6)
            self.assertLessEqual(float((pose-origin)[0,0]),.010001)
            self.assertTrue((pose<=torch.maximum(origin,ts('goal'))+1e-6).all())
            weak=dict(preview,effort=torch.ones_like(preview['effort']))
            self.assertFalse(feasible_platform_final_step(*args[:-2],weak,args[-1],rise_limit=.015)[3].item())
            for limit in [.009,.016,float('nan')]:
                with self.assertRaises(ValueError):feasible_platform_final_step(*args,rise_limit=limit)

    def test_final_platform_step_keeps_all_loaded_paths_and_bounded_motion(self):
        import json
        from _guidance_math.climb_guidance import feasible_platform_final_step
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixtures=json.loads((Path(__file__).parent/'fixtures/climb_platform_final_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        for f in fixtures.values():
            ts=lambda k:torch.tensor(f[k]);origin=ts('origin')
            preview={k:torch.tensor(v) for k,v in f['preview'].items()}
            goal=origin.clone();goal[:,0]+=.04;goal[:,2]=ts('feet')[:,:,2].mean(1)+.28
            args=(model,ts('feet'),origin,ts('quaternion'),ts('bias'),ts('bounds'),body,ts('box_bounds'),links,preview)
            pose,quat,margin,valid=feasible_platform_final_step(*args,goal)
            self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
            torch.testing.assert_close(pose-origin,torch.tensor([[.01,0.,.01]]),rtol=0,atol=1e-6)
            torch.testing.assert_close(quat,ts('quaternion'))
            # Reaching the fixed goal must not manufacture more motion.
            held=feasible_platform_final_step(*args,origin)
            self.assertFalse(held[3].item());torch.testing.assert_close(held[0],origin)
            # Insufficient motor headroom cannot be bypassed by shorter steps.
            weak=dict(preview,effort=torch.ones_like(preview['effort']))
            self.assertFalse(feasible_platform_final_step(*args[:-1],weak,goal)[3].item())

    def test_final_platform_step_rejects_unbalanced_four_foot_support(self):
        import json
        from _guidance_math.climb_guidance import feasible_platform_final_step
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_final_pose.json').read_text())['31']
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);ts=lambda k:torch.tensor(f[k]);origin=ts('origin');goal=origin.clone();goal[:,0]+=.04
        preview={k:torch.tensor(v) for k,v in f['preview'].items()};preview['com'][:,0]+=.4
        result=feasible_platform_final_step(model,ts('feet'),origin,ts('quaternion'),ts('bias'),ts('bounds'),
            base_collision_bounds(usd),ts('box_bounds'),leg_collision_primitives(usd),preview,goal)
        self.assertFalse(result[3].item());torch.testing.assert_close(result[0],origin)

    def test_front_first_keeps_required_tilt_preparation_and_defers_extra_leveling(self):
        from _guidance_math.climb_guidance import platform_level_needed
        gravity=torch.tensor([-.897,-.94,-.95,-.95,-.99])
        completed=torch.tensor([0,0,0,2,2])
        self.assertEqual(platform_level_needed(gravity,completed,True).tolist(),[True,True,False,True,False])
        torch.testing.assert_close(platform_level_needed(gravity,completed,False),gravity>-.985)

    def test_front_first_avoids_forward_body_and_com_before_front_steps(self):
        import json
        from _guidance_math.climb_guidance import predicted_support_com
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_four_support.json').read_text())['4']
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        ts=lambda k:torch.tensor(f[k])
        load={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['load'].items()}
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing'].items()}
        args=(model,ts('feet'),ts('target'),ts('origin'),ts('quaternion'),ts('bias'),ts('bounds'),f['clearance'],body,ts('box_bounds'),True,links,load,swing)
        old=feasible_support_pose(*args)
        self.assertTrue(old[3].item());self.assertGreater(old[0][0,0],ts('origin')[0,0])
        load['platform_front_first']=torch.tensor([True])
        new=feasible_support_pose(*args);self.assertTrue(new[3].item())
        com=predicted_support_com(ts('origin'),new[0][:,None],new[1][:,None],load)
        self.assertLessEqual(new[0][0,0],ts('origin')[0,0]+1e-6)
        self.assertLessEqual(com[0,0,0],load['com'][0,0]+1e-6)
        load['platform_front_first'][:]=False
        restored=feasible_support_pose(*args)
        for a,b in zip(old,restored):torch.testing.assert_close(a,b,rtol=0,atol=0)

    def test_platform_weak_support_recovery_requires_restored_load(self):
        import json
        from _guidance_math.climb_guidance import four_support_path_checks
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixtures=json.loads((Path(__file__).parent/'fixtures/climb_platform_support_recovery.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        for key,f in fixtures.items():
            ts=lambda k:torch.tensor(f[k])
            load={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['load'].items()}
            swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing'].items()}
            args=(model,ts('feet'),ts('target'),ts('origin'),ts('quaternion'),ts('bias'),ts('bounds'),f['clearance'],body,ts('box_bounds'),True,links,load,swing)
            old=feasible_support_pose(*args)
            if key!='4':self.assertFalse(old[3].item())
            load['four_support_recovery']=torch.tensor([True])
            new=feasible_support_pose(*args);self.assertTrue(new[3].item())
            minimum,residual,ready=four_support_path_checks(ts('feet'),ts('origin'),ts('quaternion'),new[0][:,None],new[1][:,None],load)
            self.assertTrue(ready.item());self.assertLess(residual.item(),.1)
            if key=='4':
                for a,b in zip(old,new):torch.testing.assert_close(a,b,rtol=0,atol=0)
            else:
                self.assertGreater(minimum.item(),2.);self.assertLess(minimum.item(),8.)
                # Holding the weak initial pose fails the endpoint recovery
                # requirement; the original unsafe forward shift also fails.
                held=four_support_path_checks(ts('feet'),ts('origin'),ts('quaternion'),ts('origin')[:,None],ts('quaternion')[:,None],load)
                self.assertFalse(held[2].item())
                unguarded=dict(load);unguarded.pop('four_support_path');unguarded.pop('four_support_recovery')
                unsafe=feasible_support_pose(*args[:12],unguarded,swing)
                check=four_support_path_checks(ts('feet'),ts('origin'),ts('quaternion'),unsafe[0][:,None],unsafe[1][:,None],load)
                self.assertFalse(check[2].item())

    def test_platform_partial_transfer_retains_four_loaded_supports(self):
        import json
        from _guidance_math.climb_guidance import four_support_path_loads
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixtures=json.loads((Path(__file__).parent/'fixtures/climb_platform_four_support.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        for key,f in fixtures.items():
            ts=lambda k:torch.tensor(f[k])
            load={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['load'].items()}
            swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing'].items()}
            args=(model,ts('feet'),ts('target'),ts('origin'),ts('quaternion'),ts('bias'),ts('bounds'),f['clearance'],body,ts('box_bounds'),True,links,load,swing)
            old=feasible_support_pose(*args)
            self.assertTrue(old[3].item())
            minimum,residual=four_support_path_loads(ts('feet'),ts('origin'),ts('quaternion'),old[0][:,None],old[1][:,None],load)
            if key=='4':
                self.assertLess(minimum.item(),8.);self.assertGreater(residual.item(),.1)
            load['four_support_path']=torch.tensor([True])
            new=feasible_support_pose(*args)
            self.assertTrue(new[3].item())
            minimum,residual=four_support_path_loads(ts('feet'),ts('origin'),ts('quaternion'),new[0][:,None],new[1][:,None],load)
            self.assertGreaterEqual(minimum.item(),8.);self.assertLess(residual.item(),.1)
            if key=='12':
                for a,b in zip(old,new):torch.testing.assert_close(a,b,rtol=0,atol=0)
            load['four_support_path'][:]=False
            disabled=feasible_support_pose(*args)
            for a,b in zip(old,disabled):torch.testing.assert_close(a,b,rtol=0,atol=0)

    def test_front_ascent_candidate_keeps_full_guards_and_ignores_airborne_capture(self):
        import json
        from _guidance_math.climb_guidance import front_ascent_pose, StageGuidance, predicted_tripod_margin, swing_path_preview
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives, support_path_geometry, leg_path_gap
        f=json.loads((Path(__file__).parent/'fixtures/climb_front_ascent_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        feet,target,target_q,origin,quat,bias,bounds,box=[torch.tensor(f[k]) for k in
            ('feet','target','target_quaternion','origin','quaternion','bias','bounds','box_bounds')]
        load={k:torch.tensor(v) for k,v in f['load'].items()}
        load.update(orientation=quat,rotation_active=torch.tensor([True]))
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing'].items()}
        swing.update(landing_probe_depth=torch.tensor([.015]),landing_com=load['com'],
            landing_origin=origin,landing_weight=load['weight'],landing_effort=load['effort'])
        def solve(t=target,tq=target_q,limits=bounds):
            return front_ascent_pose(model,feet,t,tq,origin,quat,bias,limits,
                f['clearance'],body,box,links,load,swing)
        pose,rot,margin,retry,accepted=solve()
        self.assertTrue(retry.item());self.assertTrue(accepted.item());self.assertGreaterEqual(margin.item(),.03)
        self.assertGreaterEqual(predicted_tripod_margin(feet,origin,pose[:,None],rot[:,None],load).item(),.025)
        gap,pm,err=support_path_geometry(model,feet,origin,quat,pose[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(pm.item(),0.);self.assertLess(err.item(),.001)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pose[:,None],rot[:,None],links,box).item(),.005)
        sm,se,sg=swing_path_preview(model,feet,pose[:,None],rot[:,None],bounds,swing,links,box)
        self.assertGreaterEqual(sm.item(),.03);self.assertLess(se.item(),.001);self.assertGreaterEqual(sg.item(),.005)
        self.assertLessEqual((pose-origin)[:,:2].norm().item(),.080001)
        self.assertLessEqual(abs(pose[0,2]-origin[0,2]).item(),.080001)
        self.assertLessEqual((2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1))).item(),.350001)
        # A safe plan stays bit-identical; impossible alternatives also keep the
        # original plan instead of applying the infeasible fallback pose.
        safe=solve(pose,rot);self.assertFalse(safe[3].item());self.assertFalse(safe[4].item())
        torch.testing.assert_close(safe[0],pose,rtol=0,atol=0);torch.testing.assert_close(safe[1],rot,rtol=0,atol=0)
        impossible=bounds.clone();impossible[...,0]=-.001;impossible[...,1]=.001
        rejected=solve(limits=impossible);self.assertFalse(rejected[4].item())
        torch.testing.assert_close(rejected[0],target,rtol=0,atol=0)
        torch.testing.assert_close(swing['landing'],torch.tensor(f['swing']['landing']),rtol=0,atol=0)
        # This exact fixture has three contacts and must never invoke the runtime
        # capture adjustment even though a mathematical candidate exists.
        fake=types.SimpleNamespace(a=types.SimpleNamespace(_asset=None,
            feet_positions=lambda:feet,contacts=lambda:torch.tensor(f['contacts']),
            _env=types.SimpleNamespace(scene=types.SimpleNamespace(env_origins=torch.tensor(f['swing']['origins']))),
            clock=types.SimpleNamespace(leg=load['leg'],progress=torch.zeros(1)),
            start=swing['start'],landing=swing['landing']),pose_feasible=torch.tensor([True]))
        StageGuidance.reserve_front_ascent_pose(fake,torch.tensor([True]))

    def test_platform_load_reserve_replays_exact_accepted_inputs(self):
        import json
        from _guidance_math.climb_guidance import support_load_preview, predicted_tripod_margin
        from _guidance_math.climb_leg_kinematics import rotate_vector
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives, leg_path_gap, support_path_geometry
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_load_reserve.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        feet,target,origin,quat,bias,bounds,box=[torch.tensor(f[k]) for k in
            ('feet','target','origin','quaternion','bias','bounds','box_bounds')]
        load={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['load'].items()}
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing'].items()}
        args=(model,feet,target,origin,quat,bias,bounds,f['clearance'],body,box,True,links,load,swing)
        old=feasible_support_pose(*args)
        self.assertTrue(old[3].item())
        for value,key in zip(old[:3],['position','quaternion','margin']):
            self.assertTrue(torch.allclose(value,torch.tensor(f['result'][key]),atol=1e-6,rtol=0))
        self.assertLess(old[2].item(),.08)
        pos,rot,margin,valid=feasible_support_pose(*args,height_samples=65,full_load_reserve=.08)
        self.assertTrue(valid.item())
        joints=model.inverse(rotate_vector(rot[:,None,None],feet[:,None]-pos[:,None,None],True))
        self.assertGreaterEqual(support_load_preview(model,feet,origin,pos[:,None],rot[:,None],joints,bounds,load).item(),.08)
        self.assertGreaterEqual(predicted_tripod_margin(feet,origin,pos[:,None],rot[:,None],load).item(),.025)
        gap,pm,err=support_path_geometry(model,feet,origin,quat,pos[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(pm.item(),0.);self.assertLess(err.item(),.001)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pos[:,None],rot[:,None],links,box).item(),.005)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.080001)
        self.assertLessEqual(abs(pos[0,2]-origin[0,2]).item(),.080001)
        # Stricter infeasible reserve cannot escape via the1000-valued partial-transfer bypass.
        self.assertFalse(feasible_support_pose(*args,height_samples=65,full_load_reserve=.10)[3].item())
        with self.assertRaises(ValueError):feasible_support_pose(*args,full_load_reserve=.02)

    def test_body_endpoint_reserve_keeps_path_and_leg_reserves(self):
        import json
        from _guidance_math.climb_guidance import support_endpoint_leg_gap
        from _guidance_math.climb_body_clearance import base_box_gap, base_collision_bounds, leg_collision_primitives, leg_path_gap, support_path_geometry
        f=json.loads((Path(__file__).parent/'fixtures/climb_endpoint_body_reserve.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        feet,target,origin,quat,bias,bounds,box=[torch.tensor(f[k]) for k in
            ('feet','target','origin','quaternion','bias','bounds','box_bounds')]
        self.assertLess(base_box_gap(torch.tensor(f['original_target']),torch.tensor(f['original_rotation']),body,box).item(),.015)
        args=(model,feet,target,origin,quat,bias,bounds,f['clearance'],body,box,True,links,None,None)
        # Recorded geometry only: exact loaded planning is evaluated remotely.
        pos,rot,margin,valid=feasible_support_pose(*args,height_samples=65,
            endpoint_leg_reserve=.010,endpoint_body_reserve=.015)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        self.assertGreaterEqual(base_box_gap(pos,rot,body,box).item(),.015)
        self.assertGreaterEqual(support_endpoint_leg_gap(model,feet,pos[:,None],rot[:,None],links,box).item(),.010)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pos[:,None],rot[:,None],links,box).item(),.005)
        gap,pm,err=support_path_geometry(model,feet,origin,quat,pos[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.010);self.assertGreaterEqual(pm.item(),0.);self.assertLess(err.item(),.001)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.080001)
        self.assertLessEqual(abs(pos[0,2]-origin[0,2]).item(),.080001)
        self.assertLessEqual((2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))).item(),.35)
        with self.assertRaises(ValueError):feasible_support_pose(*args,endpoint_body_reserve=.009)

    def test_endpoint_reserve_with_recorded_geometry_keeps_original_path_guard(self):
        import json
        from _guidance_math.climb_guidance import support_endpoint_leg_gap
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives, leg_path_gap, support_path_geometry
        f=json.loads((Path(__file__).parent/'fixtures/climb_endpoint_leg_reserve.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        feet,target,origin,quat,bias,bounds,box=[torch.tensor(f[k]) for k in
            ('feet','target','origin','quaternion','bias','bounds','box_bounds')]
        original_pos=torch.tensor(f['original_target'])[:,None]
        original_rot=torch.tensor(f['original_rotation'])[:,None]
        self.assertLess(support_endpoint_leg_gap(model,feet,original_pos,original_rot,links,box).item(),.010)
        args=(model,feet,target,origin,quat,bias,bounds,f['clearance'],body,box,True,links,None,None)
        # This fixture contains geometry and measured bias, not exact load-preview
        # inputs. The test proves geometric availability, not loaded feasibility.
        pos,rot,margin,valid=feasible_support_pose(*args,height_samples=65,endpoint_leg_reserve=.010)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        self.assertGreaterEqual(support_endpoint_leg_gap(model,feet,pos[:,None],rot[:,None],links,box).item(),.010)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pos[:,None],rot[:,None],links,box).item(),.005)
        gap,pm,err=support_path_geometry(model,feet,origin,quat,pos[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(pm.item(),0.);self.assertLess(err.item(),.001)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.080001)
        self.assertLessEqual(abs(pos[0,2]-origin[0,2]).item(),.080001)
        self.assertLessEqual((2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))).item(),.35)
        with self.assertRaises(ValueError):feasible_support_pose(*args,endpoint_leg_reserve=.004)

    def test_finer_height_recovers_recorded_pose_without_relaxing_gates(self):
        import json
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives, support_path_geometry, leg_path_gap
        f=json.loads((Path(__file__).parent/'fixtures/climb_support_height_grid.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(usd);body=base_collision_bounds(usd);links=leg_collision_primitives(usd)
        feet,target,origin,quat,bias,bounds,box=[torch.tensor(f[k]) for k in
            ('feet','target','origin','quaternion','bias','bounds','box_bounds')]
        load={k:torch.tensor(v) for k,v in f['load'].items()}
        args=(model,feet,target,origin,quat,bias,bounds,f['clearance'],body,box,True,links,load,None)
        self.assertFalse(feasible_support_pose(*args)[3].item())
        pos,rot,margin,valid=feasible_support_pose(*args,height_samples=65)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        gap,path_margin,error=support_path_geometry(model,feet,origin,quat,pos[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(path_margin.item(),0.)
        self.assertLess(error.item(),.001)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pos[:,None],rot[:,None],links,box).item(),.005)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.080001)
        self.assertLessEqual(abs(pos[0,2]-origin[0,2]).item(),.080001)
        self.assertLessEqual((2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))).item(),.35)

    def test_rejected_replan_preserves_valid_reference_without_unlocking_lift(self):
        from _guidance_math.climb_guidance import StageGuidance
        guide=StageGuidance.__new__(StageGuidance)
        shapes={'anchors':(4,4,3),'origin':(4,3),'target':(4,3),'orientation':(4,4),
                'target_orientation':(4,4),'load_bias':(4,4,3),'age':(4,)}
        initial={name:torch.arange(torch.tensor(shape).prod()).reshape(shape).float()+10
                 for name,shape in shapes.items()}
        for name,value in initial.items():setattr(guide,name,value.clone())
        guide.valid_legs=torch.ones(4,4,dtype=torch.bool);guide.valid_legs[3,0]=False
        guide.command_limit_excess=torch.zeros(4,4)
        guide.pose_feasible=torch.ones(4,dtype=torch.bool)
        guide.replan_reference_retained=torch.zeros(4,dtype=torch.bool)
        guide.replan_rejections=torch.zeros(4,dtype=torch.long)
        guide.replan_retry_age=torch.full((4,),3.)
        def capture(mask):
            for name in shapes:getattr(guide,name)[mask]-=.02
            guide.pose_feasible[mask]=False;guide.pose_feasible[1]=True
            guide.replan_reference_retained[mask]=False
            guide.replan_retry_age[mask]=0.
        guide.capture=capture;mask=torch.tensor([True,True,False,True])
        for _ in range(3):guide.replan_preserving_reference(mask)
        for name,value in initial.items():
            torch.testing.assert_close(getattr(guide,name)[0],value[0])
            torch.testing.assert_close(getattr(guide,name)[2],value[2])
            torch.testing.assert_close(getattr(guide,name)[1],value[1]-.06)
            torch.testing.assert_close(getattr(guide,name)[3],value[3]-.06)
        self.assertEqual(guide.pose_feasible.tolist(),[False,True,True,False])
        self.assertEqual(guide.replan_reference_retained.tolist(),[True,False,False,False])
        self.assertEqual(guide.replan_rejections.tolist(),[3,0,0,0])
        self.assertEqual(guide.replan_retry_age.tolist(),[0.,0.,3.,0.])

    def test_single_front_scope_preserves_other_climb_stages(self):
        from _guidance_math.climb_guidance import single_front_support_scope
        feet=torch.tensor([[[.83,.17,.224],[.60,-.17,.024],[.16,.17,.024],[.16,-.17,.024]]])
        contacts=torch.ones((1,4),dtype=torch.bool)
        self.assertTrue(single_front_support_scope(feet,contacts,torch.tensor([1])).item())
        mirrored=feet[:,[1,0,3,2]].clone();mirrored[...,1]*=-1
        self.assertTrue(single_front_support_scope(mirrored,contacts,torch.tensor([0])).item())
        self.assertFalse(single_front_support_scope(feet,contacts,torch.tensor([0])).item())
        self.assertFalse(single_front_support_scope(feet,contacts,torch.tensor([2])).item())
        contacts[0,0]=False
        self.assertFalse(single_front_support_scope(feet,contacts,torch.tensor([1])).item())
        contacts[:]=True
        ground=feet.clone();ground[0,0]=torch.tensor([.60,.17,.024])
        self.assertFalse(single_front_support_scope(ground,contacts,torch.tensor([1])).item())
        both=feet.clone();both[0,1]=torch.tensor([.83,-.17,.224])
        self.assertFalse(single_front_support_scope(both,contacts,torch.tensor([1])).item())
        outside=feet.clone();outside[0,0,1]=.57
        self.assertFalse(single_front_support_scope(outside,contacts,torch.tensor([1])).item())

    def test_unload_trim_waits_for_stall_and_preserves_measured_release_gate(self):
        from _guidance_math.climb_guidance import UnloadForceTrim
        trim=UnloadForceTrim(3,'cpu');force=torch.tensor([7.6,7.6,4.9])
        eligible=torch.tensor([True,False,True]);phase=torch.zeros(3)
        for _ in range(24):
            self.assertTrue((trim.update(force,eligible,phase,.02)==0).all())
        trim.update(force,eligible,phase,.03)
        self.assertGreater(trim.applied_n[0],0.)
        self.assertEqual(trim.applied_n[1:].tolist(),[0.,0.])
        for _ in range(1000):trim.update(force,eligible,phase,.02)
        self.assertEqual(trim.force_n.tolist(),[8.,0.,0.])
        forces=torch.tensor([[7.6,60.,70.,70.]])
        self.assertFalse(unloaded_support_ready(forces,torch.tensor([0]),torch.tensor([.035]),torch.zeros(1,3),torch.zeros(1,3)).item())
        forces[0,0]=4.9
        self.assertTrue(unloaded_support_ready(forces,torch.tensor([0]),torch.tensor([.035]),torch.zeros(1,3),torch.zeros(1,3)).item())

    def test_unload_trim_rolls_back_on_guard_loss_and_fades_during_lift(self):
        from _guidance_math.climb_guidance import UnloadForceTrim
        trim=UnloadForceTrim(2,'cpu');trim.force_n[:]=4.
        value=trim.update(torch.tensor([7.,7.]),torch.tensor([False,False]),torch.tensor([0.,.125]),.02)
        torch.testing.assert_close(value,torch.tensor([3.96,2.]))
        self.assertEqual(trim.force_n[1],4.)
        self.assertEqual(trim.update(torch.tensor([7.,7.]),torch.tensor([False,False]),torch.tensor([0.,.25]),.02)[1],0.)
        trim.reset(torch.tensor([1]));self.assertEqual(trim.force_n[1],0.)
        self.assertGreater(trim.force_n[0],0.)

    def test_unload_trim_jacobian_transpose_has_upward_virtual_work(self):
        from _guidance_math.climb_leg_kinematics import rotate_vector
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        q=torch.tensor([[[.05,.8,-1.7],[-.05,.8,-1.7],[.05,.8,-1.7],[-.05,.8,-1.7]]])
        # Zero root rotation matches worldZ; a positive trim must pull up,
        # rather than increase the measured downward contact preload.
        jac=model.jacobian(q);jz=jac[...,2,:];tau=jz*4.
        dq=tau*1e-4
        dz=(model.forward(q+dq)-model.forward(q))[...,2]
        self.assertTrue((dz>0).all())
        torch.testing.assert_close((tau*dq).sum(-1),4.*(jz*dq).sum(-1))

    def test_front_extension_requires_hold_and_dwell_and_finishes_only_loaded_steps(self):
        from _guidance_math.crawl_gait import PlatformFrontExtension
        extension = PlatformFrontExtension(3, 'cpu', .04)
        feet = torch.tensor([[[1.12,.18,.224],[1.12,-.18,.224],[.84,.2,.224],[.84,-.2,.224]]]).repeat(3,1,1)
        origins = torch.zeros(3,3)
        ready = torch.ones(3,dtype=torch.bool)
        hold = torch.tensor([True,False,True])
        feet[2,:2,0] = 1.90  # A new landing would leave the original footprint.
        for _ in range(49):
            self.assertFalse(extension.release(hold,ready,feet,origins,.02).any())
        release = extension.release(hold,ready,feet,origins,.021)
        self.assertEqual(release.tolist(),[True,False,False])
        torch.testing.assert_close(extension.goals[0,:,:2],torch.tensor([[1.16,.18],[1.16,-.18]]))
        saved = extension.goals.clone()
        extension.landed(torch.zeros(3,dtype=torch.bool))
        self.assertEqual(extension.completed.tolist(),[0,0,0])
        self.assertTrue(extension.moving[0])
        extension.landed(torch.tensor([True,False,False]))
        self.assertEqual(extension.completed.tolist(),[1,0,0])
        # Noise/drift in later measurements must not extend the goal again.
        feet[0,:2,0] += .01
        release = extension.release(hold,ready,feet,origins,1.01)
        self.assertTrue(release[0]);self.assertTrue(torch.equal(extension.goals,saved))
        extension.landed(torch.tensor([True,False,False]))
        self.assertEqual(extension.completed.tolist(),[2,0,0])
        self.assertFalse(extension.release(hold,ready,feet,origins,10.).any())
        extension.reset(torch.tensor([0]))
        self.assertFalse(extension.started[0]);self.assertEqual(extension.completed[0],0)
        self.assertTrue((extension.goals[0]==0).all())

    def test_front_extension_dwell_resets_on_lost_stability(self):
        from _guidance_math.crawl_gait import PlatformFrontExtension
        extension = PlatformFrontExtension(1,'cpu',.04)
        feet=torch.tensor([[[1.12,.18,.224],[1.12,-.18,.224],[.84,.2,.224],[.84,-.2,.224]]])
        yes=torch.tensor([True]);no=~yes;origins=torch.zeros(1,3)
        self.assertFalse(extension.release(yes,yes,feet,origins,.8).item())
        self.assertFalse(extension.release(yes,no,feet,origins,.1).item())
        self.assertFalse(extension.release(yes,yes,feet,origins,.8).item())
        self.assertTrue(extension.release(yes,yes,feet,origins,.21).item())

    def test_settled_fv_front_step_keeps_swing_probe_and_reload_margins(self):
        import json
        from _guidance_math.climb_guidance import swing_path_preview
        from _guidance_math.climb_body_clearance import base_collision_bounds,leg_collision_primitives
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_front_extension.json').read_text())
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        feet,origin,quat,bias,bounds=[torch.tensor(f[k]) for k in ('feet','origin','quaternion','bias','bounds')]
        load={k:torch.tensor(v) for k,v in f['load'].items()};load['leg']=torch.tensor([0])
        triangle=feet[:,[1,2,3],:2]
        shift=inset_support_target(load['com'][:,:2],triangle)-load['com'][:,:2]
        shift*=.08/shift.norm(dim=-1).clamp_min(.08)[:,None]
        target=origin.clone();target[:,:2]+=shift
        start=feet[:,0].clone();landing=start.clone();landing[:,0]+=.04
        swing=dict(start=start,landing=landing,origins=torch.zeros(1,3),leg=load['leg'],
            gravity=load['gravity'],clearance=.03,active=torch.tensor([True]),inset=torch.zeros(1),
            allow_partial_transfer=True,landing_probe_depth=torch.full((1,),.015),
            landing_com=load['com'],landing_origin=origin,landing_weight=load['weight'],landing_effort=load['effort'])
        body=base_collision_bounds(asset);links=leg_collision_primitives(asset)
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        pos,rot,margin,valid=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box,True,links,load,swing)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        sm,se,sg=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,swing,links,box)
        self.assertGreaterEqual(sm.item(),.03);self.assertLess(se.item(),.001);self.assertGreaterEqual(sg.item(),.005)
        self.assertLessEqual((pos[:,:2]-origin[:,:2]).norm().item(),.080001)
        # A landing overload must still be rejected, even with a short front step.
        swing['landing_effort']=load['effort']*.0001
        rejected=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,swing,links,box)
        self.assertLess(rejected[0].item(),.03)

    def test_fu_level_step_keeps_anchors_bounds_and_rejects_overload(self):
        import json
        from _guidance_math.climb_guidance import feasible_hold_level_pose
        from _guidance_math.climb_body_clearance import base_collision_bounds,leg_collision_primitives,support_path_geometry,leg_path_gap
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_hold_level.json').read_text())
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        feet,origin,quat,bias,bounds=[torch.tensor(f[k]) for k in ('feet','origin','quaternion','bias','bounds')]
        preview={k:torch.tensor(v) for k,v in f['load'].items()}
        body=base_collision_bounds(asset);links=leg_collision_primitives(asset)
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        pos,rot,margin,valid=feasible_hold_level_pose(model,feet,origin,quat,bias,bounds,body,box,links,preview)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        self.assertTrue(torch.equal(pos[:,:2],origin[:,:2]))
        self.assertGreaterEqual((pos[:,2]-origin[:,2]).item(),0.)
        self.assertLessEqual((pos[:,2]-origin[:,2]).item(),.005001)
        angle=2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))
        self.assertLessEqual(angle.item(),.0251)
        self.assertLess(rot[:,1:3].square().sum().item(),quat[:,1:3].square().sum().item())
        gap,path_margin,error=support_path_geometry(model,feet,origin,quat,pos[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(path_margin.item(),0.)
        self.assertLess(error.item(),.001)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pos[:,None],rot[:,None],links,box).item(),.005)
        preview['effort']*=.0001
        rejected=feasible_hold_level_pose(model,feet,origin,quat,bias,bounds,body,box,links,preview)
        self.assertFalse(rejected[3].item())
        self.assertTrue(torch.equal(rejected[0],origin));self.assertTrue(torch.equal(rejected[1],quat))

    def test_platform_hold_waits_for_complete_loaded_landing_and_stops_clock(self):
        from _guidance_math.climb_guidance import platform_hold_ready
        from _guidance_math.crawl_gait import CrawlClock
        feet=torch.tensor([[[1.1,.18,.2245],[1.1,-.18,.2245],[.83,.2,.2245],[.83,-.2,.2245]]]).repeat(5,1,1)
        contacts=torch.ones(5,4,dtype=torch.bool)
        feet[1,3,2]=.0245
        progress=torch.tensor([1.,1.,.9,1.,1.]);loaded=torch.tensor([True,True,True,False,True])
        stable=torch.tensor([.2,.2,.2,.2,.1]);lifted=torch.ones(5,dtype=torch.bool)
        ready=platform_hold_ready(feet,contacts,progress,lifted,loaded,stable,.15)
        self.assertEqual(ready.tolist(),[True,False,False,False,False])
        clock=CrawlClock(1,'cpu');clock.index[:]=1;clock.elapsed[:]=clock.transfer+clock.swing
        clock.lifted[:]=True;clock.stable[:]=.2
        advance=clock.update(contacts[:1],~ready[:1],.02,settle_ready=loaded[:1])
        self.assertFalse(advance.item());self.assertEqual(clock.leg.item(),3)
        self.assertEqual(clock.progress.item(),1.)

    def test_platform_hold_capture_preserves_reference_and_other_environments(self):
        from types import SimpleNamespace as NS
        from _guidance_math.climb_guidance import StageGuidance
        guide=StageGuidance.__new__(StageGuidance)
        q=torch.arange(24,dtype=torch.float32).reshape(2,12)/100
        feet=torch.arange(24,dtype=torch.float32).reshape(2,4,3)/50
        root_pos=torch.tensor([[1.,.02,.4],[1.1,.03,.41]])
        quat=torch.tensor([[1.,0.,0.,0.],[1.,0.,0.,0.]])
        action=NS(feet_positions=lambda:feet,_asset=NS(data=NS(root_pos_w=root_pos,root_quat_w=quat,joint_pos=q)),
            _joint_ids=list(range(12)),reference=q+.07,center_of_mass=lambda:root_pos+.01)
        guide.a=action;guide.slots=torch.arange(12).reshape(4,3)
        guide.anchors=torch.full_like(feet,-1.);guide.origin=torch.full_like(root_pos,-1.)
        guide.target=guide.origin.clone();guide.orientation=torch.zeros_like(quat)
        guide.target_orientation=guide.orientation.clone();guide.load_bias=torch.zeros(2,4,3)
        guide.age=torch.ones(2);guide.feedback_unloading=torch.ones(2)
        guide.load_replan=torch.ones(2,dtype=torch.bool)
        guide.replan_reference_retained=torch.ones(2,dtype=torch.bool)
        guide.pose_requested_target=guide.origin.clone();guide.pose_capture_com=guide.origin.clone()
        guide.capture_hold(torch.tensor([True,False]))
        torch.testing.assert_close(guide.anchors[0],feet[0])
        torch.testing.assert_close(guide.target[0],root_pos[0])
        torch.testing.assert_close(q[0].reshape(4,3)+guide.load_bias[0],action.reference[0].reshape(4,3))
        self.assertEqual(guide.age.tolist(),[0.,1.]);self.assertEqual(guide.feedback_unloading.tolist(),[0.,1.])
        self.assertTrue((guide.anchors[1]==-1.).all().item())
        self.assertEqual(guide.load_replan.tolist(),[False,True])

    def test_platform_pose_scope_requires_four_planted_inside_feet(self):
        from _guidance_math.climb_guidance import platform_support_scope
        feet=torch.tensor([[[1.1,.18,.2245],[1.1,-.18,.2245],[.83,.2,.2245],[.83,-.2,.2245]]]).repeat(5,1,1)
        contacts=torch.ones(5,4,dtype=torch.bool)
        feet[1,3,2]=.0245  # Last rear still on the ground.
        contacts[2,3]=False  # Swing or unloaded foot is not platform support.
        feet[3,3,0]=.78  # Preserve the original edge reserve.
        feet[4,3,1]=.57
        self.assertEqual(platform_support_scope(feet,contacts).tolist(),[True,False,False,False,False])

    def test_fr_platform_pose_rejects_overextended_front_and_finds_guarded_geometry(self):
        import json
        from _guidance_math.climb_leg_kinematics import rotate_vector
        from _guidance_math.climb_body_clearance import base_collision_bounds,leg_collision_primitives,support_path_geometry,leg_path_gap
        f=json.loads((Path(__file__).parent/'fixtures/climb_all_platform_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(str(usd))
        feet,origin,quat,bias,bounds,target=[torch.tensor(f[k]) for k in ('feet','origin','quaternion','bias','bounds','target')]
        old=torch.tensor([f['old_target']])
        joints=model.inverse(rotate_vector(torch.tensor([f['old_quaternion']])[:,None],feet-old[:,None],inverse=True))
        self.assertLess(torch.minimum(joints-bounds[...,0],bounds[...,1]-joints).amin().item(),0.)
        body=base_collision_bounds(str(usd));links=leg_collision_primitives(str(usd))
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        pos,rot,margin,valid=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box,True,links)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        gap,path_margin,error=support_path_geometry(model,feet,origin,quat,pos[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(path_margin.item(),0.)
        self.assertLess(error.item(),.001)
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,pos[:,None],rot[:,None],links,box).item(),.005)
        self.assertLessEqual((pos[:,:2]-origin[:,:2]).norm().item(),.080001)
        self.assertLessEqual((pos[:,2]-origin[:,2]).abs().item(),.080001)

    def test_com_rotation_is_limited_to_last_ground_rear_and_preserves_old_arithmetic(self):
        from _guidance_math.climb_guidance import last_rear_com_scope, predicted_support_com
        feet=torch.tensor([[[1.1,.18,.2245],[1.1,-.18,.2245],[.83,.2,.2245],[.7,-.2,.024]]]).repeat(5,1,1)
        contacts=torch.ones(5,4,dtype=torch.bool)
        leg=torch.tensor([3,3,1,3,3])
        start=feet[torch.arange(5),leg].clone();landing=start.clone();landing[:,2]=.2245
        feet[1,2,2]=.024;contacts[3,2]=False;landing[4,2]=.024
        self.assertEqual(last_rear_com_scope(feet,contacts,leg,start,landing).tolist(),[True,False,False,False,False])
        origin=torch.tensor([[100.125,-32.7,.391]])
        positions=torch.tensor([[[100.16,-32.72,.4],[100.09,-32.68,.395]]])
        com=torch.tensor([[100.09,-32.71,.44]])
        rot=torch.tensor([[[.98,0.,-.1989975,0.]]]).expand(1,2,4)
        preview={'com':com,'orientation':torch.tensor([[1.,0.,0.,0.]]),'rotation_active':torch.tensor([False])}
        expected=com[:,None]+positions-origin[:,None]
        self.assertTrue(torch.equal(predicted_support_com(origin,positions,rot,preview),expected))
        del preview['orientation']
        self.assertTrue(torch.equal(predicted_support_com(origin,positions,rot,preview),expected))

    def test_support_com_rotates_measured_offset_and_preserves_translation(self):
        from _guidance_math.climb_guidance import predicted_support_com
        origin=torch.tensor([[1.,2.,.4]])
        position=origin[:,None].clone()
        rotation=torch.tensor([[[.70710678,0.,0.,.70710678]]])
        preview={'com':torch.tensor([[1.1,2.,.5]])}
        torch.testing.assert_close(predicted_support_com(origin,position,rotation,preview),preview['com'][:,None])
        preview['orientation']=torch.tensor([[1.,0.,0.,0.]])
        torch.testing.assert_close(predicted_support_com(origin,position,rotation,preview),torch.tensor([[[1.,2.1,.5]]]))
        shift=torch.tensor([[2.,-3.,.7]])
        shifted=dict(preview,com=preview['com']+shift)
        torch.testing.assert_close(predicted_support_com(origin+shift,position+shift[:,None],rotation,shifted),
            predicted_support_com(origin,position,rotation,preview)+shift[:,None])

    def test_rotated_com_recovers_front_raised_last_rear_pose(self):
        import json
        from _guidance_math.climb_guidance import expanded_support_pose, predicted_support_com, front_support_height, tripod_support_clearance
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixture=json.loads((Path(__file__).parent/'fixtures/climb_front_raised_last_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(str(usd))
        feet,origin,quat,bias,bounds=[torch.tensor(fixture[k]) for k in ('feet','origin','quaternion','bias','bounds')]
        load={k:torch.tensor(v) for k,v in fixture['load'].items()}
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in fixture['swing'].items()}
        args=(model,feet,origin,quat,bias,bounds,base_collision_bounds(str(usd)),
              torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]]),leg_collision_primitives(str(usd)),load,swing)
        self.assertFalse(expanded_support_pose(*args,angle_span=.6)[3].item())
        load['orientation']=quat
        pos,rot,margin,valid=expanded_support_pose(*args,angle_span=.6)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        self.assertGreaterEqual(front_support_height(model,feet,pos[:,None],rot[:,None]).item(),.24)
        self.assertGreaterEqual(tripod_support_clearance(feet,load['leg'],pos[:,None]).item(),.19)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.08)
        self.assertLessEqual((2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))).item(),.35)
        com=predicted_support_com(origin,pos[:,None],rot[:,None],load)[:,0]
        self.assertGreaterEqual(triangle_margin(com[:,:2],feet[:,[0,1,2],:2])[0].amin().item(),.025)

    def test_front_raise_measures_pitch_and_preserves_extension(self):
        from _guidance_math.climb_guidance import front_support_height, front_raise_candidate_ready
        from _guidance_math.climb_leg_kinematics import rotate_vector
        model=LegKinematics.from_usd(str(root.parents[3]/'assets/go2_piper/go2_piper.usd'))
        feet=torch.tensor([[[1.1,.18,.2245],[1.1,-.18,.2245],[.69,.20,.024],[.69,-.20,.024]]])
        origin=torch.tensor([[.95,0.,.35]])
        positions=origin[:,None].expand(-1,3,-1).clone()
        positions[0,:,2]=torch.tensor([.35,.39,.47])
        turns=torch.tensor([[[1.,0.,0.,0.]]]).expand(1,3,4)
        height=front_support_height(model,feet,positions,turns)
        torch.testing.assert_close(height,positions[...,2]-.2245)
        preview={'front_raise_target':torch.tensor([.24]),'front_raise_current':torch.tensor([.23])}
        accepted=front_raise_candidate_ready(model,feet,origin,positions,turns,preview)
        self.assertEqual(accepted.tolist(),[[False,False,True]])
        preview['front_raise_current'][:]=.12
        self.assertEqual(front_raise_candidate_ready(model,feet,origin,positions,turns,preview).tolist(),[[False,True,True]])
        # Raising the front by pitch counts; a root-height-only metric misses it.
        tilted=torch.tensor([[[.98480775,0.,-.17364818,0.]]])
        actual=front_support_height(model,feet,positions[:,:1],tilted)
        self.assertGreater(actual.item(),height[0,0].item()+.06)
        shift=torch.tensor([[[2.,-3.,.5]]])
        torch.testing.assert_close(front_support_height(model,feet+shift,positions+shift,turns),height)


    def test_last_rear_inset_scope_and_frozen_height_pose(self):
        import json
        from _guidance_math.climb_guidance import stage_swing_inset, expanded_support_pose, tripod_support_clearance
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixture=json.loads((Path(__file__).parent/'fixtures/climb_last_right_height_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(str(usd))
        feet,origin,quat,bias,bounds=[torch.tensor(fixture[k]) for k in ('feet','origin','quaternion','bias','bounds')]
        load={k:torch.tensor(v) for k,v in fixture['load'].items()}
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in fixture['swing'].items()}
        contacts=torch.ones((1,4),dtype=torch.bool)
        params=(swing['start'],swing['landing'],load['leg'],swing['origins'])
        torch.testing.assert_close(stage_swing_inset(*params,feet,contacts),torch.tensor([.06]))
        torch.testing.assert_close(stage_swing_inset(*params,feet,contacts,.02),torch.tensor([.02]))
        contacts[:,2]=False
        torch.testing.assert_close(stage_swing_inset(*params,feet,contacts,.02),torch.tensor([.06]))
        args=(model,feet,origin,quat,bias,bounds,base_collision_bounds(str(usd)),
              torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]]),leg_collision_primitives(str(usd)),load,swing)
        self.assertFalse(expanded_support_pose(*args,angle_span=.6)[3].item())
        swing['inset'][:]=.02
        pos,rot,margin,valid=expanded_support_pose(*args,angle_span=.6)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        self.assertGreaterEqual(tripod_support_clearance(feet,load['leg'],pos[:,None]).item(),.19)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.08)
        self.assertLessEqual((2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))).item(),.35)
        predicted=load['com']+pos-origin
        self.assertGreaterEqual(triangle_margin(predicted[:,:2],feet[:,[0,1,2],:2])[0].amin().item(),.025)

    def test_partial_last_foot_transfer_preserves_acquired_unload_height(self):
        import json
        from _guidance_math.climb_leg_kinematics import rotate_vector
        from _guidance_math.climb_guidance import support_load_preview
        fixture=json.loads((Path(__file__).parent/'fixtures/climb_last_right_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(str(usd))
        feet,origin,quat,bounds=[torch.tensor(fixture[k]) for k in ('feet','origin','quaternion','bounds')]
        preview={k:torch.tensor(v) for k,v in fixture['load'].items()}
        # fl raised the body to.3911m, then a partial transfer requested.3611m.
        # The three remaining feet stand on the.20m platform. Even outside the
        # estimated tripod, that descent loses the existing unload clearance.
        preview['com'][:, :2]=torch.tensor([[.5,0.]])
        origin[:,2]=.3911
        positions=origin[:,None].clone();positions[...,2]=.3611
        joints=model.inverse(rotate_vector(quat[:,None,None],feet[:,None]-positions[:,:,None],True))
        rejected=support_load_preview(model,feet,origin,positions,quat[:,None],joints,bounds,preview)
        self.assertLess(rejected.item(),.03)
        # Before height is acquired, four-foot intermediate transfers remain
        # available; the measured unload gate still requires the full height.
        origin[:,2]=.3293
        allowed=support_load_preview(model,feet,origin,positions,quat[:,None],joints,bounds,preview)
        self.assertGreaterEqual(allowed.item(),.03)

    def test_angle_coverage_finds_last_right_pose_without_relaxing_total_angle(self):
        import json
        from _guidance_math.climb_guidance import expanded_support_pose, tripod_support_clearance
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixture=json.loads((Path(__file__).parent/'fixtures/climb_last_right_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(str(usd))
        feet,origin,quat,bias,bounds=[torch.tensor(fixture[k]) for k in ('feet','origin','quaternion','bias','bounds')]
        load={k:torch.tensor(v) for k,v in fixture['load'].items()}
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in fixture['swing'].items()}
        args=(model,feet,origin,quat,bias,bounds,base_collision_bounds(str(usd)),
              torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]]),leg_collision_primitives(str(usd)),load,swing)
        self.assertFalse(expanded_support_pose(*args)[3].item())
        pos,rot,margin,valid=expanded_support_pose(*args,angle_span=.6)
        self.assertTrue(valid.item())
        self.assertGreaterEqual(margin.item(),.03)
        angle=2*torch.acos((rot*quat).sum(-1).abs().clamp(max=1.))
        self.assertLessEqual(angle.item(),.35)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.08)
        self.assertGreaterEqual(tripod_support_clearance(feet,load['leg'],pos[:,None]).item(),.19)
        com=load['com']+pos-origin
        self.assertGreaterEqual(triangle_margin(com[:,:2],feet[:,[0,1,2],:2])[0].amin().item(),.025)


    def test_expanded_scope_requires_both_prepared_rear_feet_and_platform_support(self):
        from _guidance_math.climb_guidance import expanded_pose_scope
        feet=torch.tensor([[[1.11,.18,.224],[1.11,-.18,.224],[.69,.2,.024],[.69,-.2,.024]]]).repeat(6,1,1)
        contacts=torch.ones(6,4,dtype=torch.bool);legs=torch.tensor([2,2,2,2,0,2])
        feet[1,3,0]=.65 # Earlier rear ground following is unchanged.
        contacts[2,0]=False
        feet[3,3]=torch.tensor([.84,-.2,.224]) # Original last-rear fallback remains.
        contacts[5,2]=False # First rear transfer requires settled four-foot contact.
        self.assertEqual(expanded_pose_scope(feet,contacts,legs).tolist(),[False,False,False,True,False,False])
        self.assertEqual(expanded_pose_scope(feet,contacts,legs,True).tolist(),[True,False,False,True,False,False])


    def test_expanded_last_rear_pose_keeps_support_and_effort_gates(self):
        import json
        from _guidance_math.climb_guidance import expanded_support_pose
        from _guidance_math.climb_body_clearance import base_collision_bounds, leg_collision_primitives
        fixture=json.loads((Path(__file__).parent/'fixtures/climb_last_rear_pose.json').read_text())
        usd=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(str(usd))
        body=base_collision_bounds(str(usd));links=leg_collision_primitives(str(usd))
        feet,origin,quat,bias,bounds=[torch.tensor(fixture[k]) for k in ('feet','origin','quaternion','bias','bounds')]
        load={k:torch.tensor(v) for k,v in fixture['load'].items()}
        swing={k:torch.tensor(v) if isinstance(v,list) else v for k,v in fixture['swing'].items()}
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        args=(model,feet,origin,quat,bias,bounds,body,box,links,load,swing)
        # The former geometric candidate fails the existing unload-height gate.
        held,_,_,valid=expanded_support_pose(*args)
        self.assertFalse(valid.item())
        torch.testing.assert_close(held,origin)
        # A synthetic earlier ground placement gives a feasible higher body pose.
        feet[:,2,0]=.69;swing['start'][:,0]=.69
        pos,rot,margin,valid=expanded_support_pose(*args)
        self.assertTrue(valid.item())
        from _guidance_math.climb_guidance import tripod_support_clearance
        self.assertGreaterEqual(tripod_support_clearance(feet,load['leg'],pos[:,None]).item(),.19)
        self.assertGreaterEqual(margin.item(),.03)
        self.assertLessEqual((pos-origin)[:,:2].norm().item(),.08)
        support=triangle_margin((load['com']+pos-origin)[:,:2],feet[:,[0,1,3],:2])[0].amin()
        self.assertGreaterEqual(support.item(),.025)
        # A feasible swing alone cannot override the actuator compensation cap.
        load['effort']=torch.full_like(load['effort'],.001)
        held,rotation,_,valid=expanded_support_pose(*args)
        self.assertFalse(valid.item())
        torch.testing.assert_close(held,origin)
        torch.testing.assert_close(rotation,quat)


    def test_incomplete_swing_allows_only_improving_four_foot_transfer(self):
        from _guidance_math.climb_guidance import swing_transfer_options
        feet=torch.tensor([[[1.,1.,0.],[1.,-1.,0.],[-1.,1.,0.],[-1.,-1.,0.]]])
        origin=torch.zeros(1,3)
        positions=torch.tensor([[[.04,.04,0.],[-.04,-.04,0.],[.25,.25,0.],[.25,.25,0.],[0.,0.,0.]]])
        preview=dict(com=torch.tensor([[-.2,-.2,.3]]),leg=torch.tensor([3]))
        ready=torch.tensor([[False,False,False,True,False]])
        allowed,partial=swing_transfer_options(feet,origin,positions,preview,ready)
        self.assertEqual(allowed.tolist(),[[True,False,False,True,False]])
        self.assertEqual(partial.tolist(),[[True,False,False,False,False]])
        self.assertFalse(ready[0,0])  # A permissible intermediate move does not authorize lift.

    def test_measured_support_does_not_release_unchecked_swing(self):
        from types import SimpleNamespace as NS
        from _guidance_math.climb_guidance import StageGuidance
        feet=torch.tensor([[[1.,1.,0.],[1.,-1.,0.],[-1.,1.,0.],[-1.,-1.,0.]]])
        forces=torch.zeros(1,4,3);forces[0,:3,2]=70.
        sensor=NS(data=NS(net_forces_w=forces))
        action=NS(feet_positions=lambda:feet,center_of_mass=lambda:torch.tensor([[.2,.2,.3]]),
            clock=NS(leg=torch.tensor([3])),sensor_ids=torch.arange(4),
            cfg=NS(guidance_preunload=True,guidance_feasible_pose=True,guidance_swing_preview=True,guidance_load_preview=True,guidance_pose_fixtures=False,front_raise_height=None),
            _asset=NS(data=NS(root_lin_vel_w=torch.zeros(1,3),root_ang_vel_w=torch.zeros(1,3),root_pos_w=torch.tensor([[0.,0.,.3]]))),
            _env=NS(scene={'contact_forces':sensor},step_dt=.02))
        guide=StageGuidance.__new__(StageGuidance);guide.a=action
        guide.support_indices=torch.tensor([[j for j in range(4) if j!=i] for i in range(4)])
        guide.margin=torch.zeros(1);guide.age=torch.tensor([4.]);guide.engaged=torch.tensor([True])
        guide.pose_feasible=torch.tensor([True]);guide.swing_path_ready=torch.tensor([False])
        guide.unload_stable=torch.zeros(1)
        for _ in range(20):self.assertFalse(guide.support_ready().item())
        guide.swing_path_ready[:]=True
        for _ in range(11):ready=guide.support_ready()
        self.assertTrue(ready.item())
        # Even a clear swing and unloaded rear foot wait for front-body rise.
        action.cfg.front_raise_height=.24
        guide.front_raise_active=lambda:torch.tensor([True])
        guide.front_raise_measured_height=lambda:torch.tensor([.23])
        self.assertFalse(guide.support_ready().item())
        guide.front_raise_measured_height=lambda:torch.tensor([.245])
        for _ in range(11):ready=guide.support_ready()
        self.assertTrue(ready.item())
        action._asset.data.root_pos_w[:,2]=.1
        self.assertFalse(guide.support_ready().item())

    def test_platform_contact_search_catches_fs_front_knee_limit(self):
        import json
        from _guidance_math.climb_guidance import swing_path_preview
        from _guidance_math.climb_body_clearance import leg_collision_primitives
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_contact_search.json').read_text())
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        feet,pos,rot,bounds=[torch.tensor(f[k]) for k in ('feet','origin','quaternion','bounds')]
        preview={k:torch.tensor(v) if isinstance(v,list) else v for k,v in f['swing'].items()}
        links=leg_collision_primitives(asset);box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        checked=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,preview,links,box)
        self.assertLess(checked[0].item(),-.10)
        preview['landing_probe_depth'].zero_()
        zero=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,preview,links,box)
        del preview['landing_probe_depth']
        original=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,preview,links,box)
        self.assertGreater(original[0].item(),checked[0].item()+.05)
        for x,y in zip(original,zero):self.assertTrue(torch.equal(x,y))

    def test_platform_reload_preview_preserves_inactive_row_and_rejects_effort_excess(self):
        import json
        from _guidance_math.climb_guidance import swing_path_preview
        from _guidance_math.climb_body_clearance import leg_collision_primitives
        f=json.loads((Path(__file__).parent/'fixtures/climb_platform_contact_search.json').read_text())
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        feet,pos,rot,bounds=[torch.tensor(f[k]).repeat(2,*([1]*(torch.tensor(f[k]).ndim-1))) for k in ('feet','origin','quaternion','bounds')]
        preview={k:torch.tensor(v).repeat(2,*([1]*(torch.tensor(v).ndim-1))) if isinstance(v,list) else v for k,v in f['swing'].items()}
        links=leg_collision_primitives(asset);box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]]).repeat(2,1,1)
        preview['landing_probe_depth'][:]=0
        old=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,preview,links,box)
        preview.update(landing_com=feet.mean(1),landing_origin=pos,landing_weight=torch.full((2,),10000.),landing_effort=torch.ones(2,4,3)*.001)
        preview['landing_probe_depth'][1]=.015
        new=swing_path_preview(model,feet,pos[:,None],rot[:,None],bounds,preview,links,box)
        for x,y in zip(old,new):self.assertTrue(torch.equal(x[0],y[0]))
        self.assertLess(new[0][1].item(),-1.)

    def test_rear_swing_preview_rejects_hip_limit_and_accepts_inward_arc(self):
        from _guidance_math.climb_guidance import swing_path_preview
        from _guidance_math.climb_body_clearance import leg_collision_primitives
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        feet=torch.tensor([[[1.297123,.191440,.223998],[1.296028,-.185289,.223819],
                            [.664482,.202002,.022440],[.645182,-.201756,.023]]])
        pos=torch.tensor([[[1.003156,.048992,.361552]]])
        rot=torch.tensor([[[.9884703,.0008334,-.1513147,.0054444]]])
        rot=rot/rot.norm(dim=-1,keepdim=True)
        bounds=torch.tensor([[-.94248,.94248],[-1.31772,3.237],[-2.62845,-.93226]]).expand(1,4,3,2)
        gravity=torch.zeros(1,4,3);gravity[:,3]=torch.tensor([-.718904,.362042,-.124215])
        preview=dict(start=feet[:,3],landing=torch.tensor([[.865182,-.201756,.2245]]),
            origins=torch.zeros(1,3),leg=torch.tensor([3]),gravity=gravity,clearance=.03,
            active=torch.tensor([True]),inset=torch.tensor([0.]))
        links=leg_collision_primitives(asset);box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        bad,err,gap=swing_path_preview(model,feet,pos,rot,bounds,preview,links,box)
        self.assertLess(bad.item(),-.10);self.assertLess(err.item(),.001)
        preview['inset']=torch.tensor([.06])
        good,err,gap=swing_path_preview(model,feet,pos,rot,bounds,preview,links,box)
        self.assertGreater(good.item(),.03);self.assertLess(err.item(),.001);self.assertGreater(gap.item(),.005)
        shift=torch.tensor([9.,-7.,.6]);moved={**preview,'start':preview['start']+shift,
            'landing':preview['landing']+shift,'origins':preview['origins']+shift}
        translated=swing_path_preview(model,feet+shift,pos+shift,rot,bounds,moved,links,box+shift)
        for x,y in zip((good,err,gap),translated):torch.testing.assert_close(x,y,atol=4e-6,rtol=1e-4)

    def test_rear_inward_arc_keeps_endpoints_and_smooth_phase_joins(self):
        from _guidance_math.climb_guidance import rear_swing_inset
        start=torch.tensor([[.65,.20,.024],[.65,-.20,.024],[.65,-.20,.024],[.65,-.20,.2245]])
        landing=start.clone();landing[:,0]=.87;landing[:,2]=.2245
        origins=torch.zeros_like(start);legs=torch.tensor([2,3,1,3])
        inset=rear_swing_inset(start,landing,legs,origins)
        torch.testing.assert_close(inset,torch.tensor([-.06,.06,0.,0.]))
        for progress,expected in ((0.,start),(1.,landing)):
            torch.testing.assert_close(edge_lift_reference(start,landing,torch.full((4,),progress),origins,.03,inset),expected)
        traverse=edge_lift_reference(start,landing,torch.full((4,),.75),origins,.03,inset)
        torch.testing.assert_close(traverse[:,0],landing[:,0])
        torch.testing.assert_close(traverse[:,1],landing[:,1]+inset)
        # The traverse gate must use the raised inset waypoint; descent restores width.
        self.assertGreater((traverse[0,:2]-landing[0,:2]).norm().item(),.05)
        for phase in (.25,.75):
            mid=edge_lift_reference(start,landing,torch.full((4,),phase),origins,.03,inset)
            for epsilon in (-.0001,.0001):
                near=edge_lift_reference(start,landing,torch.full((4,),phase+epsilon),origins,.03,inset)
                self.assertLess((near-mid).abs().max().item(),1e-6)

    def test_collision_bounds_reject_observed_low_body_and_allow_clear_pose(self):
        from _guidance_math.climb_body_clearance import base_collision_bounds, base_box_gap
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        body=base_collision_bounds(asset)
        torch.testing.assert_close(body, torch.tensor([[-.1279979,-.09722298,-.09683901],
                                                      [.331958,.09677697,.08883398]]))
        pos=torch.tensor([[.4506637,.0327311,.2832591], [.4506637,.0327311,.34]])
        quat=torch.tensor([[.9999974,0.,0.,.0022813], [1.,0.,0.,0.]])
        box=torch.tensor([[.75,-.6,0.],[1.95,.6,.2]])
        gap=base_box_gap(pos,quat,body,box)
        self.assertLess(gap[0],0.)
        self.assertGreater(gap[1],.01)
        shift=torch.tensor([9.,-7.,.6])
        torch.testing.assert_close(base_box_gap(pos+shift,quat,body,box+shift),gap,atol=1e-6,rtol=1e-5)
        # Front-up bounds clear the edge even when their world AABB overlaps.
        tilt=torch.tensor([[.9887711,0.,-.1494381,0.]])
        self.assertGreater(base_box_gap(torch.tensor([[.5,0.,.30]]),tilt,body,box).item(),.01)

    def test_sampled_path_rejects_crossing_with_clear_endpoints(self):
        from _guidance_math.climb_body_clearance import base_box_gap, support_path_geometry
        geometry={'hip_origins':[[.1934,.0465,0],[.1934,-.0465,0],[-.1934,.0465,0],[-.1934,-.0465,0]],
                  'hip_lateral_offsets':[.0955,-.0955,.0955,-.0955], 'link_lengths':[[.213,.213]]*4}
        model=LegKinematics(geometry)
        body=torch.tensor([[-.128,-.097,-.097],[.332,.097,.089]])
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        origin=torch.tensor([[.35,0.,.25]]);pos=torch.tensor([[[2.2,0.,.25]]])
        quat=torch.tensor([[1.,0.,0.,0.]])
        self.assertGreater(base_box_gap(origin,quat,body,box).item(),.01)
        self.assertGreater(base_box_gap(pos[:,0],quat,body,box).item(),.01)
        q=torch.tensor([[[0.,.8,-1.6]]*4]);feet=model.forward(q)+origin[:,None]
        bounds=torch.tensor([[-.94,.94],[-1.32,3.24],[-2.63,-.932]]).expand(1,4,3,2)
        gap,margin,error=support_path_geometry(model,feet,origin,quat,pos,quat[:,None],
            torch.zeros_like(q),bounds,body,box)
        self.assertLess(gap.item(),0.)
        # Stationary valid support must pass; unreachable transfer must not.
        gap,margin,error=support_path_geometry(model,feet,origin,quat,origin[:,None],quat[:,None],
            torch.zeros_like(q),bounds,body,box)
        self.assertGreater(gap.item(),.01);self.assertGreater(margin.item(),0.)
        self.assertLess(error.item(),.001)

    def test_leg_jacobian_matches_finite_difference(self):
        model=LegKinematics.from_usd(root.parents[3]/'assets/go2_piper/go2_piper.usd',dtype=torch.float64)
        q=torch.tensor([[[.2,.7,-1.8],[-.1,.9,-1.5],[.1,1.,-1.7],[-.2,.5,-2.]]],dtype=torch.float64)
        finite=[]
        for joint in range(3):
            delta=torch.zeros_like(q);delta[...,joint]=1e-6
            finite.append((model.forward(q+delta)-model.forward(q-delta))/2e-6)
        torch.testing.assert_close(model.jacobian(q),torch.stack(finite,-1),atol=1e-9,rtol=1e-8)

    def test_tripod_load_preview_rejects_stalled_pose_and_finds_bounded_transfer(self):
        from _guidance_math.climb_guidance import support_load_preview
        from _guidance_math.climb_body_clearance import base_collision_bounds,leg_collision_primitives
        from _guidance_math.climb_leg_kinematics import rotate_vector
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        feet=torch.tensor([[[1.063105,.186058,.223971],[.841235,-.171647,.223952],
                            [.400631,.186453,.023401],[.392631,-.190943,.023362]]])
        origin=torch.tensor([[.591422,-.002328,.355840]])
        quat=torch.tensor([[.99188513,.00039590,-.12713566,.00027591]])
        target=torch.tensor([[.591247,-.002092,.320557]])
        bias=torch.tensor([[[-.132750,.337974,.254599],[.076222,.070542,.187466],
                            [-.270638,.020035,.319635],[.324504,-.000181,.369083]]])
        bounds=torch.tensor([[-.94248,.94248],[-1.31772,3.237],[-2.62845,-.93226]]).expand(1,4,3,2)
        preview=dict(com=torch.tensor([[.572860,-.001243,.396936]]),leg=torch.tensor([1]),
            weight=torch.tensor([213.51466]),effort=torch.tensor([23.7,23.7,45.43]).expand(1,4,3),
            gravity=torch.tensor([[[1.167985,-.493575,-.253521],[-1.095958,.293701,-.252550],
                                  [1.118937,.377729,-.185871],[-1.116326,.396265,-.181115]]]))
        joints=model.inverse(rotate_vector(quat[:,None],feet-origin[:,None],True))
        bad=support_load_preview(model,feet,origin,origin[:,None],quat[:,None],joints[:,None],bounds,preview)
        self.assertLess(bad.item(),0.)
        body=base_collision_bounds(asset);links=leg_collision_primitives(asset)
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        result=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box,True,links,preview)
        self.assertTrue(result[3].item());self.assertGreaterEqual(result[2].item(),.03)
        self.assertLessEqual((result[0][:,:2]-origin[:,:2]).norm().item(),.080001)
        self.assertGreater(result[0][0,0],origin[0,0]+.02)
        # More than two environments exercises the bounded-memory path.
        expand=lambda x:x.expand(3,*x.shape[1:]).clone()
        batched=feasible_support_pose(model,expand(feet),expand(target),expand(origin),expand(quat),
            expand(bias),expand(bounds),.28,body,expand(box),True,links,{k:expand(v) for k,v in preview.items()})
        for actual,expected in zip(batched,result):torch.testing.assert_close(actual,expand(expected))

    def test_cylinder_support_separates_empty_box_corners_and_rejects_intersection(self):
        from _guidance_math.climb_body_clearance import primitive_box_gap
        primitive=dict(center=torch.zeros(1,1,3),rotation=torch.tensor([[[1.,0.,0.,0.]]]),
                       half=torch.tensor([[[1.,1.,.5]]]),cylinder=torch.ones(1,1,dtype=torch.bool))
        position=torch.zeros(2,1,1,3);rotation=torch.tensor([1.,0.,0.,0.]).expand(2,1,1,4)
        boxes=torch.tensor([[[.8,.8,-.2],[2.,2.,.2]],[[.6,.6,-.2],[2.,2.,.2]]])[:,None,None]
        gap=primitive_box_gap(position,rotation,primitive,boxes).flatten()
        self.assertAlmostEqual(gap[0].item(),2**.5*.8-1.,places=6)
        self.assertLess(gap[1].item(),0.)

    def test_usd_primitives_resolve_observed_false_leg_overlap(self):
        from _guidance_math.climb_body_clearance import leg_collision_primitives,leg_collision_bounds,leg_link_poses,primitive_box_gap,base_box_gap
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd';model=LegKinematics.from_usd(asset)
        primitives=leg_collision_primitives(asset);bounds=leg_collision_bounds(asset)
        joints=torch.tensor([[[.33818349,-.19162969,-1.32474494],[.00532844,-.23453097,-1.44540584],
                              [.16401762,.82127941,-1.32931161],[-.02484578,.84723508,-1.40906787]]])
        origin=torch.tensor([[.36931843,-.02157021,.36058202]])
        quat=torch.tensor([[.99870878,-.01083701,-.04837872,-.01108436]])
        p,q=leg_link_poses(model,joints,origin,quat)
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])[:,None,None]
        self.assertLess(base_box_gap(p,q,bounds,box).amin().item(),.005)
        self.assertGreater(primitive_box_gap(p,q,primitives,box).amin().item(),.005)
        self.assertAlmostEqual(primitives['half'][1,2,0].item(),.013,places=6)
        self.assertAlmostEqual(primitives['half'][1,1,0].item(),.1065,places=6)

    def test_leg_link_frames_and_primitive_dimensions_match_chain(self):
        from _guidance_math.climb_body_clearance import leg_collision_bounds, leg_link_poses
        from _guidance_math.climb_leg_kinematics import rotate_vector
        asset=root.parents[3]/'assets/go2_piper/go2_piper.usd'
        model=LegKinematics.from_usd(asset);bounds=leg_collision_bounds(asset)
        # The cube's authored extent already includes scale. Use size+transform
        # once, otherwise the thigh would shrink and miss genuine collisions.
        self.assertAlmostEqual(float(bounds[0,1,1,2]-bounds[0,1,0,2]),.213,places=6)
        joints=torch.tensor([[[.13,.72,-1.84],[-.13,.72,-1.84],[.12,.98,-1.89],[-.12,.98,-1.89]]])
        origin=torch.tensor([[.64,-.04,.36]]);quat=torch.tensor([[.9887711,0.,-.1494381,0.]])
        p,q=leg_link_poses(model,joints,origin,quat)
        down=torch.zeros_like(joints);down[...,2]=-model.lengths[:,1]
        feet=p[:,:,2]+rotate_vector(q[:,:,2],down)
        torch.testing.assert_close(feet,origin[:,None]+rotate_vector(quat[:,None],model.forward(joints)),atol=1e-6,rtol=1e-6)
        torch.testing.assert_close(q.norm(dim=-1),torch.ones_like(q[...,0]))

    def test_independent_height_recovers_stalled_mixed_support_without_relaxing_gates(self):
        from _guidance_math.climb_body_clearance import support_path_geometry
        geometry={'hip_origins':[[.1934,.0465,0],[.1934,-.0465,0],[-.1934,.0465,0],[-.1934,-.0465,0]],
                  'hip_lateral_offsets':[.0955,-.0955,.0955,-.0955], 'link_lengths':[[.213,.213]]*4}
        model=LegKinematics(geometry)
        # Rounded ew env6 terminal geometry after both front anchors advanced.
        feet=torch.tensor([[[1.068396,.176947,.223960],[1.062380,-.194460,.223987],
                            [.399746,.189236,.023065],[.399945,-.191567,.023122]]])
        origin=torch.tensor([[.642225,-.022316,.366093]])
        target=torch.tensor([[.6792,-.0894,.366093]])
        quat=torch.tensor([[.9887411,-.0251161,-.1475012,-.00190225]])
        quat=quat/quat.norm(dim=1,keepdim=True)
        bias=torch.tensor([[[-.114757,.245443,.211106],[.127277,.307376,.274148],
                            [-.311999,-.080409,.236463],[.254238,-.115978,.283176]]])
        bounds=torch.tensor([[-.94248,.94248],[-1.31772,3.237],[-2.62845,-.93226]]).expand(1,4,3,2)
        body=torch.tensor([[-.1279979,-.09722298,-.09683901],[.331958,.09677697,.08883398]])
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        old=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box)
        self.assertFalse(old[3].item())
        pose,rot,margin,valid=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box,True)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        gap,path_margin,error=support_path_geometry(model,feet,origin,quat,pose[:,None],rot[:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(path_margin.item(),0.)
        self.assertLess(error.item(),.001);self.assertLessEqual(abs(pose[0,2]-origin[0,2]),.08)
        from _guidance_math.climb_body_clearance import leg_collision_bounds, leg_path_gap, leg_link_poses
        links=leg_collision_bounds(root.parents[3]/'assets/go2_piper/go2_piper.usd')
        self.assertLess(leg_path_gap(model,feet,origin,quat,pose[:,None],rot[:,None],links,box).item(),0.)
        guarded=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box,True,links)
        self.assertTrue(guarded[3].item())
        self.assertGreaterEqual(leg_path_gap(model,feet,origin,quat,guarded[0][:,None],guarded[1][:,None],links,box).item(),.005)
        self.assertLess((guarded[0][:,:2]-origin[:,:2]).norm(),(target[:,:2]-origin[:,:2]).norm())
        gap,pm,err=support_path_geometry(model,feet,origin,quat,guarded[0][:,None],guarded[1][:,None],bias,bounds,body,box)
        self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(pm.item(),0.)
        self.assertLess(err.item(),.001)
        # A case with an already feasible original choice keeps that exact pose.
        target=origin.clone()
        old=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box)
        self.assertTrue(old[3].item())
        extended=feasible_support_pose(model,feet,target,origin,quat,bias,bounds,.28,body,box,True)
        for actual,expected in zip(extended,old):torch.testing.assert_close(actual,expected)

    def test_pose_selection_checks_all_legs_and_holds_when_no_endpoint_is_feasible(self):
        geometry={'hip_origins':[[.1934,.0465,0],[.1934,-.0465,0],[-.1934,.0465,0],[-.1934,-.0465,0]],
                  'hip_lateral_offsets':[.0955,-.0955,.0955,-.0955], 'link_lengths':[[.213,.213]]*4}
        model=LegKinematics(geometry)
        feet=torch.tensor([[[.845,.171,.224],[.842,-.177,.224],[.401,.186,.023],[.398,-.192,.023]]])
        origin=torch.tensor([[.64,-.046,.326]]);quat=torch.tensor([[1.,0.,0.,0.]])
        bias=torch.tensor([[[-.21,.04,.25],[.15,.036,.46],[-.197,-.036,.134],[.175,-.087,.27]]])
        bounds=torch.tensor([[-.94248,.94248],[-1.31772,3.237],[-2.62845,-.932]]).expand(1,4,3,2)
        pose,rotation,margin,valid=feasible_support_pose(model,feet,origin,origin,quat,bias,bounds,.28)
        self.assertTrue(valid.item());self.assertGreaterEqual(margin.item(),.03)
        from _guidance_math.climb_leg_kinematics import rotate_vector
        joints=model.inverse(rotate_vector(rotation[:,None],feet-pose[:,None],inverse=True))
        self.assertTrue(((joints>bounds[...,0])&(joints<bounds[...,1])).all())
        self.assertTrue(((joints+bias>bounds[...,0])&(joints+bias<bounds[...,1])).all())
        from _guidance_math.climb_body_clearance import support_path_geometry
        body=torch.tensor([[-.128,-.097,-.097],[.332,.097,.089]])
        box=torch.tensor([[[.75,-.6,0.],[1.95,.6,.2]]])
        p,r,_,safe=feasible_support_pose(model,feet,origin,origin,quat,bias,bounds,.28,body,box)
        if safe.item():
            gap,pm,err=support_path_geometry(model,feet,origin,quat,p[:,None],r[:,None],bias,bounds,body,box)
            self.assertGreaterEqual(gap.item(),.01);self.assertGreaterEqual(pm.item(),0.)
            self.assertLess(err.item(),.001)
        else:
            torch.testing.assert_close(p,origin)
        # Even joint-feasible endpoints must be rejected when inside the obstacle.
        enclosing=torch.tensor([[[-2.,-2.,-2.],[2.,2.,2.]]])
        p,r,_,safe=feasible_support_pose(model,feet,origin,origin,quat,bias,bounds,.28,body,enclosing)
        self.assertFalse(safe.item());torch.testing.assert_close(p,origin);torch.testing.assert_close(r,quat)
        p,q,_,valid=feasible_support_pose(model,feet+3,origin,origin,quat,bias,bounds,.28)
        self.assertFalse(valid.item());torch.testing.assert_close(p,origin);torch.testing.assert_close(q,quat)

    def test_support_plane_pitch_sign_clearance_and_world_invariance(self):
        feet=torch.tensor([[[.83,.17,.224],[.83,-.17,.224],[.15,.17,.024],[.15,-.17,.024]]])
        root=torch.tensor([[.49,0.,.3]]);q=torch.tensor([[1.,0.,0.,0.]])
        height,orientation=support_plane_pose(feet,root,q,.28)
        torch.testing.assert_close(height,torch.tensor([.404]))
        self.assertLess(orientation[0,2],0.)
        torch.testing.assert_close(orientation.norm(dim=1),torch.ones(1))
        from _guidance_math.climb_leg_kinematics import rotate_vector
        front=rotate_vector(orientation,torch.tensor([[.2,0.,0.]]))
        self.assertGreater(front[0,2],0.)
        shift=torch.tensor([4.,-7.,.6]);rot=torch.tensor([[.70710678,0.,0.,.70710678]])
        moved=rotate_vector(rot[:,None],feet)+shift
        h2,q2=support_plane_pose(moved,rotate_vector(rot,root)+shift,rot,.28)
        torch.testing.assert_close(h2,height+.6)
        torch.testing.assert_close(rotate_vector(q2,torch.tensor([[.2,0.,0.]])),rotate_vector(rot,front))
        _,neg=support_plane_pose(feet,root,-q,.28)
        torch.testing.assert_close(neg,-orientation)
        low,level=support_plane_pose(feet,root,q,.28,0.)
        torch.testing.assert_close(low,torch.tensor([.304]))
        torch.testing.assert_close(level,q)
        quarter,tilt=support_plane_pose(feet,root,q,.28,.25)
        torch.testing.assert_close(quarter,torch.tensor([.329]))
        torch.testing.assert_close(torch.atan2(tilt[:,2],tilt[:,0]),
                                  .25*torch.atan2(orientation[:,2],orientation[:,0]))

    def test_feedback_unloading_waits_recovers_and_never_loads_swing(self):
        current=torch.tensor([0.,.5,.5,.5,.5])
        prepared=torch.tensor([False,True,False,False,False])
        contact=torch.tensor([True,True,True,False,False])
        swing=torch.tensor([False,False,False,False,True])
        out=feedback_unload(current,prepared,contact,swing,.15)
        torch.testing.assert_close(out,torch.tensor([0.,.6,.4,.5,1.]))
        for _ in range(100):out=feedback_unload(out,prepared,contact,swing,.15)
        torch.testing.assert_close(out,torch.tensor([0.,1.,0.,.5,1.]))

    def test_mixed_support_keeps_ground_clearance_and_preserves_flat_reference(self):
        feet=torch.zeros(3,4,3);feet[:,:,2]=.024
        feet[1,0,2]=.224;feet[2,:,2]=.224
        torch.testing.assert_close(mixed_support_body_height(feet,.28),torch.tensor([.304,.304,.504]))
        shift=torch.tensor([12.,-7.,.4])
        torch.testing.assert_close(mixed_support_body_height(feet+shift,.28),mixed_support_body_height(feet,.28)+.4)

    def test_landing_waits_for_touch_load_and_drops_airborne_allocation(self):
        state=LandingContact(1,'cpu');yes=torch.tensor([True]);no=~yes
        for _ in range(250):
            ready=state.update(yes,no,yes,torch.zeros(1),yes,.02)
        self.assertFalse(ready.item());self.assertEqual(state.reload.item(),0.)
        self.assertAlmostEqual(state.depth.item(),.015,places=6)
        for _ in range(100):
            ready=state.update(yes,yes,yes,torch.tensor([3.]),yes,.02)
        self.assertEqual(state.reload.item(),1.);self.assertFalse(ready.item())
        for _ in range(11):ready=state.update(yes,yes,yes,torch.tensor([20.]),yes,.02)
        self.assertTrue(ready.item())
        ready=state.update(yes,no,yes,torch.zeros(1),yes,.02)
        self.assertFalse(ready.item());self.assertEqual(state.reload.item(),0.)
        state.reset(yes);self.assertEqual(state.depth.item(),0.)

    def test_no_probe_or_reload_before_landing_or_without_support(self):
        state=LandingContact(2,'cpu');active=torch.tensor([False,True]);touch=torch.tensor([False,True])
        supported=torch.tensor([True,False]);calm=torch.ones(2,dtype=torch.bool)
        for _ in range(100):state.update(active,touch,supported,torch.full((2,),20.),calm,.02)
        self.assertEqual(state.depth.sum().item(),0.);self.assertEqual(state.reload.sum().item(),0.)

    def test_unload_gate_rejects_missing_support_load_motion_and_margin(self):
        forces=torch.tensor([[0.,70.,70.,70.],[24.,70.,70.,70.],[0.,70.,70.,0.],
                             [0.,70.,70.,70.],[0.,70.,70.,70.],[0.,70.,70.,70.]])
        selected=torch.zeros(6,dtype=torch.long);margin=torch.full((6,),.035);margin[3]=-.01
        velocity=torch.zeros(6,3);velocity[4,0]=.05
        angular=torch.zeros(6,3);angular[5,1]=.2
        self.assertEqual(unloaded_support_ready(forces,selected,margin,velocity,angular).tolist(),[True,False,False,False,False,False])
        for leg in range(4):
            f=torch.full((1,4),70.);f[0,leg]=1.
            self.assertTrue(unloaded_support_ready(f,torch.tensor([leg]),torch.tensor([.035]),torch.zeros(1,3),torch.zeros(1,3)).item())

    def test_acceleration_force_and_moments_at_mixed_heights(self):
        feet=torch.tensor([[[.2,.15,.2],[.2,-.15,.2],[-.2,.15,0],[-.2,-.15,0]]],dtype=torch.float64)
        com=torch.tensor([[-.06,-.04,.38]],dtype=torch.float64);weight=torch.tensor([200.],dtype=torch.float64);leg=torch.tensor([0]);u=torch.ones(1,dtype=torch.float64)
        acceleration=torch.tensor([[.2,-.1]],dtype=torch.float64)
        forces,residual=balanced_acceleration_loads(feet,com,weight,leg,u,acceleration)
        self.assertLess(residual.abs().max(),.001)
        torch.testing.assert_close(forces.sum(1)[:,:2],weight[:,None]*acceleration/9.81)
        self.assertLess(torch.cross(feet-com[:,None],forces,dim=-1).sum(1).abs().max(),.001)
        self.assertEqual(forces[:,0].abs().sum(),0.)
        vertical,_=balanced_vertical_loads(feet,com,weight,leg,u)
        zero,_=balanced_acceleration_loads(feet,com,weight,leg,u,torch.zeros_like(acceleration))
        torch.testing.assert_close(zero[:,:,2],vertical);self.assertEqual(zero[:,:,:2].abs().sum(),0.)
        shift=torch.tensor([4.,-7.,.4],dtype=torch.float64)
        translated,_=balanced_acceleration_loads(feet+shift,com+shift,weight,leg,u,acceleration)
        torch.testing.assert_close(translated,forces)

    def test_force_allocation_respects_selected_foot_and_reports_infeasibility(self):
        feet=torch.tensor([[[.2,.15,0],[.2,-.15,0],[-.2,.15,0],[-.2,-.15,0]]],dtype=torch.float64).repeat(4,1,1)
        selected=torch.arange(4)
        support=torch.tensor([[j for j in range(4) if j!=i] for i in range(4)])
        com=feet.gather(1,support[:,:,None].expand(-1,-1,3)).mean(1);com[:,2]=.32
        weight=torch.full((4,),200.,dtype=torch.float64)
        force,residual=balanced_vertical_loads(feet,com,weight,selected,torch.ones(4,dtype=torch.float64))
        self.assertLess(residual.abs().max(),.001)
        torch.testing.assert_close(force.sum(1),weight)
        torch.testing.assert_close(force[torch.arange(4),selected],torch.zeros(4,dtype=torch.float64))
        self.assertGreaterEqual(force.min(),0)
        moved,res2=balanced_vertical_loads(feet+torch.tensor([4.,-6.,.2]),com+torch.tensor([4.,-6.,.2]),weight,selected,torch.ones(4,dtype=torch.float64))
        torch.testing.assert_close(moved,force);torch.testing.assert_close(res2,residual)
        bad=balanced_vertical_loads(feet,com+torch.tensor([2.,0.,0.]),weight,selected,torch.ones(4,dtype=torch.float64))
        self.assertGreater(bad[1][:,1:].abs().max(),100.)

    def test_four_to_three_load_transfer_is_continuous(self):
        feet=torch.tensor([[[.2,.15,0],[.2,-.15,0],[-.2,.15,0],[-.2,-.15,0]]],dtype=torch.float64)
        com=torch.tensor([[-.06,-.04,.32]],dtype=torch.float64);weight=torch.tensor([200.],dtype=torch.float64);leg=torch.tensor([0])
        f0,_=balanced_vertical_loads(feet,com,weight,leg,torch.zeros(1,dtype=torch.float64))
        f1,_=balanced_vertical_loads(feet,com,weight,leg,torch.ones(1,dtype=torch.float64))
        fm,_=balanced_vertical_loads(feet,com,weight,leg,torch.full((1,),.5,dtype=torch.float64))
        torch.testing.assert_close(fm,(f0+f1)/2)
        self.assertGreater(f0[0,0],0);self.assertEqual(f1[0,0],0)

    def test_forward_lift_stays_before_face_until_foot_clears_top(self):
        phase=torch.linspace(0,1,1001);start=torch.tensor([[.60,.17,.024]]).repeat(len(phase),1)
        landing=torch.tensor([[.83,.17,.2245]]).repeat(len(phase),1)
        trajectory=edge_lift_reference(start,landing,phase,torch.zeros_like(start),.03)
        torch.testing.assert_close(trajectory[0],start[0]);torch.testing.assert_close(trajectory[-1],landing[-1])
        self.assertLessEqual(trajectory[phase<=.25,0].max(),.700001)
        self.assertGreaterEqual(trajectory[(phase>=.25)&(phase<=.75),2].min(),.25449)
        shift=torch.tensor([[12.,-7.,.1]])
        torch.testing.assert_close(edge_lift_reference(start+shift,landing+shift,phase,torch.zeros_like(start)+shift,.03)-shift,trajectory,atol=2e-6,rtol=1e-6)

    def test_loaded_reference_continuity_and_swing_rejection_preserve_support(self):
        actual=torch.full((1,4,3),.4);bias=torch.full_like(actual,.1)
        previous=actual+bias;bounds=torch.stack((-torch.ones_like(actual),torch.ones_like(actual)),dim=-1)
        valid=torch.ones((1,4),dtype=torch.bool);selected=torch.tensor([0]);engaged=torch.tensor([True])
        out,_=loaded_leg_reference(previous,actual,bias,torch.zeros_like(actual),bounds,valid,engaged,selected,torch.zeros(1))
        torch.testing.assert_close(out,previous)
        moved=actual+.05;valid[0,0]=False
        out,accepted=loaded_leg_reference(previous,moved,bias,torch.zeros_like(actual),bounds,valid,engaged,selected,torch.tensor([.25]))
        torch.testing.assert_close(out[:,0],previous[:,0])
        torch.testing.assert_close(out[:,1:],moved[:,1:]+bias[:,1:])
        self.assertEqual(accepted.tolist(),[[False,True,True,True]])

    def test_loaded_command_limit_and_only_swing_unloads(self):
        q=torch.full((1,4,3),.4);bias=torch.full_like(q,.2)
        bounds=torch.stack((-torch.ones_like(q),torch.ones_like(q)),dim=-1)
        valid=torch.ones((1,4),dtype=torch.bool)
        out,_=loaded_leg_reference(q,q,bias,torch.zeros_like(q),bounds,valid,torch.tensor([True]),torch.tensor([2]),torch.tensor([.25]))
        torch.testing.assert_close(out[:,2],q[:,2]);torch.testing.assert_close(out[:,0],q[:,0]+bias[:,0])
        q[:,1]=.95
        out,accepted=loaded_leg_reference(torch.zeros_like(q),q,bias,torch.zeros_like(q),bounds,valid,torch.tensor([True]),torch.tensor([2]),torch.tensor([.25]))
        self.assertFalse(accepted[0,1]);self.assertTrue((out[:,1]==0).all())

    def test_inset_is_inside_for_both_windings_and_translations(self):
        triangle = torch.tensor([[[.2,-.15],[-.2,.15],[-.2,-.15]]])
        point = torch.tensor([[.03,.01]])
        target = inset_support_target(point,triangle)
        self.assertGreaterEqual(triangle_margin(target,triangle)[0].min().item(),.03499)
        torch.testing.assert_close(inset_support_target(point,triangle.flip(1)), target, atol=1e-6,rtol=1e-6)
        shift = torch.tensor([[12.,-7.]])
        torch.testing.assert_close(inset_support_target(point+shift,triangle+shift[:,None])-shift,target,atol=2e-6,rtol=1e-6)

    def test_inside_point_stays_fixed(self):
        triangle=torch.tensor([[[1.,0.],[-1.,1.],[-1.,-1.]]])
        point=torch.zeros(1,2)
        torch.testing.assert_close(inset_support_target(point,triangle),point)

    def test_runtime_ik_matches_audited_model_and_reports_unreachable(self):
        geometry={'hip_origins':[[.1934,.0465,0],[.1934,-.0465,0],[-.1934,.0465,0],[-.1934,-.0465,0]],
                  'hip_lateral_offsets':[.0955,-.0955,.0955,-.0955], 'link_lengths':[[.213,.213]]*4}
        model=LegKinematics(geometry,dtype=torch.float64)
        audited=AuditedKinematics(geometry,dtype=torch.float64)
        gen=torch.Generator().manual_seed(20261002)
        q=torch.rand((100,4,3),generator=gen,dtype=torch.float64)*torch.tensor([.6,1.3,1.2])+torch.tensor([-.3,.2,-2.4])
        feet=model.forward(q)
        torch.testing.assert_close(feet,audited.forward(q))
        torch.testing.assert_close(model.forward(model.inverse(feet)),feet,atol=1e-12,rtol=1e-12)
        far=feet+torch.tensor([2.,0,0])
        self.assertGreater((model.forward(model.inverse(far))-far).norm(dim=-1).min(),1.)


if __name__=='__main__':unittest.main()
