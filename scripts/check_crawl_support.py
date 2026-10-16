"""Geometry and sign checks for the experimental support-transfer controller."""
import importlib.util
from pathlib import Path
import unittest
import torch

path = Path(__file__).resolve().with_name("crawl_support.py")
spec = importlib.util.spec_from_file_location("crawl_support", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupportChecks(unittest.TestCase):
    def test_joint_body_plan_is_translation_invariant_and_rejects_unreachable_stride(self):
        from crawl_approach import plan_ground_approach
        from crawl_leg_kinematics import LegKinematics,rotate_vector
        k=LegKinematics(dict(hip_origins=[[.1934,.0465,0],[.1934,-.0465,0],[-.1934,.0465,0],[-.1934,-.0465,0]],
            hip_lateral_offsets=[.0955,-.0955,.0955,-.0955],link_lengths=[[.213,.213]]*4),dtype=torch.float64)
        q=torch.tensor([[[.1,.6,-1.8],[-.1,.6,-1.8],[.1,.9,-1.8],[-.1,.9,-1.8]]],dtype=torch.float64).expand(3,-1,-1)
        b=torch.tensor([[0.,0.,.27],[6.,-4.,.27],[-9.,3.,.27]],dtype=torch.float64)
        f=k.forward(q)+b[:,None];quat=torch.tensor([[1.,0.,0.,0.]],dtype=torch.float64).expand(3,-1)
        com=b+torch.tensor([[.02,0.,.06]],dtype=torch.float64)
        lo=torch.tensor([[[-.94,-1.31,-2.62]]*4],dtype=torch.float64).expand(3,-1,-1)
        hi=torch.tensor([[[.94,3.2,-.932]]*4],dtype=torch.float64).expand(3,-1,-1)
        leg=torch.zeros(3,dtype=torch.long)
        r=plan_ground_approach(k,b,quat,com,f,q,lo,hi,leg,.16,2.8,True,support_search=True)
        self.assertTrue(r['feasible'].all())
        for key in ('advance','delta','joint_margin','joint_speed','joint_acceleration'):
            torch.testing.assert_close(r[key],r[key][:1].expand_as(r[key]),rtol=1e-7,atol=1e-7)
        # Dense independent replay checks between the planner's65 samples.
        u=torch.linspace(0,1,1001,dtype=torch.float64)
        body=(b+r['delta'])[:,None].expand(-1,len(u),-1).clone()
        body[:,:,0]+=r['advance'][:,None]*module.smooth_fraction(u)[None]
        feet=f[:,None].expand(-1,len(u),-1,-1).clone();feet[:,:,0]+=module.flat_swing_arc(u,.16)[None]
        local=rotate_vector(quat[:,None,None],feet-body[:,:,None],inverse=True);j=k.inverse(local)
        anchor=k.inverse(rotate_vector(quat[:,None],f-(b+r['delta'])[:,None],inverse=True))
        self.assertLess((j-anchor[:,None]).abs().max().item(),.675)
        self.assertTrue(((j>=lo[:,None]+.025)&(j<=hi[:,None]-.025)).all())
        self.assertLess((k.forward(j)-local).abs().max().item(),1e-8)
        invalid=plan_ground_approach(k,b,quat,com,f,q,lo,hi,leg,.6,2.8,True,support_search=True)
        self.assertFalse(invalid['feasible'].any())
        self.assertEqual(invalid['advance'].abs().sum().item(),0.)
        self.assertEqual(invalid['delta'].abs().sum().item(),0.)

    def test_approach_arc_bounds_and_ground_edge_clearance(self):
        for distance, duration in ((.16,3.),(.24,4.1)):
            u=torch.linspace(0.,1.,2001,dtype=torch.float64,requires_grad=True)
            arc=module.flat_swing_arc(u,distance)
            v=torch.stack([torch.autograd.grad(arc[:,i].sum(),u,create_graph=True,retain_graph=True)[0] for i in range(3)],dim=1)
            acc=torch.stack([torch.autograd.grad(v[:,i].sum(),u,retain_graph=True)[0] for i in range(3)],dim=1)
            self.assertLess((v/duration).norm(dim=1).max().item(),.12)
            self.assertLess((acc/duration**2).norm(dim=1).max().item(),.4)
            torch.testing.assert_close(v[[0,-1]],torch.zeros(2,3,dtype=torch.float64))
            torch.testing.assert_close(acc[[0,-1]],torch.zeros(2,3,dtype=torch.float64))
            torch.testing.assert_close(arc[[0,-1]],torch.tensor([[0.,0.,0.],[distance,0.,0.]],dtype=torch.float64))
        from types import SimpleNamespace
        owner=SimpleNamespace(approach_stride_m=.16,
            env=SimpleNamespace(scene=SimpleNamespace(env_origins=torch.tensor([[0.,0.,0.],[6.,0.,0.],[12.,0.,0.]])),
                cfg=SimpleNamespace(scene=SimpleNamespace(terrain=SimpleNamespace(terrain_generator=SimpleNamespace(
                    sub_terrains={'box':SimpleNamespace(approach_distance=.75)}))))))
        start=torch.tensor([[.5,0.,.02],[6.55,0.,.02],[12.5,0.,.02]])
        safe=module.SingleStepController.approach_foothold_clear(owner,start,.16)
        self.assertEqual(safe.tolist(),[True,False,True])

    def test_level_duration_bounds_actual_normalized_quaternion_reference(self):
        from crawl_cycle import level_transfer_duration
        for angle in (.05,.2,.5,1.):
            q=torch.tensor([[torch.cos(torch.tensor(angle/2)).item(),torch.sin(torch.tensor(angle/2)).item(),0.,0.]],dtype=torch.float64)
            q=q/q.norm(dim=1,keepdim=True)
            duration=level_transfer_duration(torch.tensor([.03],dtype=torch.float64),q).item()
            fraction=torch.linspace(0.,1.,1001,dtype=torch.float64,requires_grad=True)
            path=module.level_orientation(q.expand(1001,-1),fraction)
            derivative=torch.stack([torch.autograd.grad(path[:,i].sum(),fraction,create_graph=True,retain_graph=True)[0] for i in range(4)],dim=1)/duration
            second=torch.stack([torch.autograd.grad(derivative[:,i].sum(),fraction,retain_graph=True)[0] for i in range(4)],dim=1)/duration
            angular_acceleration=2*(path[:,:1]*second[:,1:]-second[:,:1]*path[:,1:]-torch.cross(path[:,1:],second[:,1:],dim=1))
            self.assertLessEqual(2*derivative.norm(dim=1).max().item(),.2+1e-8)
            self.assertLessEqual(angular_acceleration.norm(dim=1).max().item(),.5+1e-8)
            self.assertLessEqual(1.875*.03/duration,.075+1e-8)
            self.assertLessEqual(5.774*.03/duration**2,.133+1e-8)

    def test_bounded_swing_timing_preserves_end_rest_and_reference_envelope(self):
        fraction=torch.linspace(0.,1.,10001,dtype=torch.float64,requires_grad=True)
        arc=module.flat_swing_arc(fraction)
        first=torch.stack([torch.autograd.grad(arc[:,i].sum(),fraction,create_graph=True,retain_graph=True)[0] for i in range(3)],dim=1)
        second=torch.stack([torch.autograd.grad(first[:,i].sum(),fraction,retain_graph=True)[0] for i in range(3)],dim=1)
        for duration in (1.8,2.1,3.):
            self.assertLess((first/duration).norm(dim=1).max().item(),.12)
            self.assertLess((second/duration**2).norm(dim=1).max().item(),.4)
            torch.testing.assert_close(first[[0,-1]],torch.zeros(2,3,dtype=torch.float64))
            torch.testing.assert_close(second[[0,-1]],torch.zeros(2,3,dtype=torch.float64))
        torch.testing.assert_close(arc[[0,-1]],torch.tensor([[0.,0.,0.],[.08,0.,0.]],dtype=torch.float64))
        self.assertAlmostEqual(arc[:,2].max().item(),.05)

    def test_preparation_anticipates_next_triangle_without_crossing_current_corridor(self):
        from crawl_cycle import next_support_preparation
        feet=torch.tensor([[[.25,.2],[.25,-.2],[-.25,.2],[-.25,-.2]]],dtype=torch.float64)
        triangle=feet[:,[1,3,2]]; future=feet.clone();future[:,0,0]+=.08
        point=torch.tensor([[-.06,-.06]],dtype=torch.float64);advance=torch.tensor([[.025,0.]],dtype=torch.float64)
        delta=next_support_preparation(point,triangle,advance,future[:,[0,1,2]])
        for u in torch.linspace(0,1,41):
            self.assertGreaterEqual(module.triangle_margin(point+delta+u*advance,triangle).item(),.03-1e-7)
        before=module.triangle_margin(point+advance,future[:,[0,1,2]])
        after=module.triangle_margin(point+delta+advance,future[:,[0,1,2]])
        self.assertGreater(after.item(),before.item())
        torch.testing.assert_close(delta,next_support_preparation(point,triangle.flip(1),advance,future[:,[0,1,2]]))
        # No unnecessary travel along the common diagonal: the minimum move
        # to its inward boundary is normal to that diagonal.
        edge = feet[:,2]-feet[:,1]
        self.assertLess((edge*delta).sum(-1).abs().item(),1e-10)
        offset=torch.tensor([[18.,-24.]],dtype=torch.float64)
        torch.testing.assert_close(delta,next_support_preparation(point+offset,triangle+offset[:,None],advance,future[:,[0,1,2]]+offset[:,None]))

    def test_cycle_shift_covers_entire_body_advance_in_both_windings(self):
        from crawl_cycle import path_support_shift
        triangle = torch.tensor([[[-.25,-.2],[.25,.2],[-.25,.2]]], dtype=torch.float64)
        point = torch.tensor([[.025,0.]], dtype=torch.float64)
        advance = torch.tensor([[.025,0.]], dtype=torch.float64)
        for shape in (triangle, triangle.flip(1)):
            delta = path_support_shift(point, shape, advance)
            self.assertLessEqual(delta.norm().item(), .14)
            for fraction in torch.linspace(0,1,31):
                self.assertGreaterEqual(module.triangle_margin(point+delta+fraction*advance,shape).item(), .03-1e-8)
            # A second call from the already feasible position must not move it.
            torch.testing.assert_close(path_support_shift(point+delta,shape,advance),torch.zeros_like(delta))

    def test_cycle_shift_bound_does_not_claim_unreachable_margin(self):
        from crawl_cycle import path_support_shift
        triangle = torch.tensor([[[-.25,-.2],[.25,.2],[-.25,.2]]], dtype=torch.float64)
        point = torch.tensor([[.4,-.2]], dtype=torch.float64)
        advance = torch.tensor([[.025,0.]], dtype=torch.float64)
        delta = path_support_shift(point,triangle,advance)
        self.assertLessEqual(delta.norm().item(),.14+1e-12)
        self.assertLess(module.triangle_margin(point+delta,triangle).item(),.015)

    def test_cycle_repeated_rest_cannot_count_a_future_or_unstarted_step(self):
        from crawl_cycle import new_step_completion
        ready=torch.tensor([True]);started=torch.full((1,3),-1.);completed=started.clone()
        index=torch.tensor([0])
        self.assertFalse(new_step_completion(ready,started,completed,index).item())
        started[0,0]=4.
        self.assertTrue(new_step_completion(ready,started,completed,index).item())
        completed[0,0]=8.
        # Rest is lost then recovered before the next physical swing starts.
        for value in (False,True,True):
            self.assertFalse(new_step_completion(torch.tensor([value]),started,completed,index).item())
        self.assertFalse(new_step_completion(ready,started,completed,torch.tensor([1])).item())

    def test_cycle_transfer_duration_bounds_quintic_speed_and_acceleration(self):
        from crawl_cycle import transfer_duration
        distance = torch.linspace(0., .14, 1000, dtype=torch.float64)
        duration = transfer_duration(distance)
        self.assertTrue((1.875*distance/duration <= .075+1e-12).all())
        self.assertTrue(((10/torch.sqrt(torch.tensor(3.)))*distance/duration.square() <= .133+1e-8).all())
        self.assertTrue((duration >= 1.).all())

    def test_cycle_force_reordering_unloads_each_actual_selected_leg(self):
        feet = torch.tensor([[[.2,.2,0.],[.2,-.2,0.],[-.2,.2,0.],[-.2,-.2,0.]]], dtype=torch.float64)
        for leg in range(4):
            order = [leg]+[i for i in range(4) if i != leg]
            inverse = torch.tensor(order).argsort()
            com = feet[:,order[1:]].mean(dim=1);com[:,2]=.3
            acceleration=torch.tensor([[.02,-.01]],dtype=torch.float64)
            force=module.support_acceleration_forces(feet[:,order],com,torch.tensor([200.],dtype=torch.float64),torch.ones(1,dtype=torch.float64),acceleration)[:,inverse]
            self.assertAlmostEqual(force[0,leg,2].item(),0.,places=6)
            self.assertTrue((force[:,:,2]>=0.).all())
            torch.testing.assert_close(force.sum(dim=1),torch.cat((200*acceleration/9.81,torch.tensor([[200.]],dtype=torch.float64)),dim=1))
            self.assertLess(torch.cross(feet-com[:,None],force,dim=2).sum(dim=1).norm().item(),1e-4)

    def test_leg_reordering_preserves_physical_forward_inverse_geometry(self):
        model = module.LegKinematics(dict(hip_origins=[[.19,.047,0.],[.19,-.047,0.],[-.19,.047,0.],[-.19,-.047,0.]],
                                        hip_lateral_offsets=[.0955,-.0955,.0955,-.0955],
                                        link_lengths=[[.213,.213]]*4), dtype=torch.float64)
        q = torch.tensor([[[.2,.7,-1.5],[-.2,.9,-1.8],[.1,1.,-1.7],[-.1,.8,-1.6]]], dtype=torch.float64)
        order = [1,0,3,2]
        swapped = model.reordered(('FR','FL','RR','RL'))
        torch.testing.assert_close(swapped.forward(q[:,order]), model.forward(q)[:,order])
        torch.testing.assert_close(swapped.inverse(model.forward(q)[:,order]), q[:,order])
        restored = swapped.reordered(('FL','FR','RL','RR'))
        torch.testing.assert_close(restored.forward(q), model.forward(q))
        self.assertEqual(model.legs, ('FL','FR','RL','RR'))
        with self.assertRaises(ValueError): model.reordered(('FR','FR','RL','RR'))

    def test_rear_step_requires_release_and_never_reloads_an_airborne_foot(self):
        rear = module.RearStep(1, 'cpu')
        active = torch.ones(1, dtype=torch.bool)
        release = torch.zeros_like(active)
        feet = torch.zeros(1, 4, 3)
        anchor = feet[:, 3].clone()
        contacts = torch.ones(1, 4, dtype=torch.bool)
        forces = torch.ones(1, 4) * 50
        zero = torch.zeros(1, 3)
        def tick():
            rear.update(active, release, anchor, feet, contacts, forces, torch.ones(1)*.03,
                        zero, zero, zero, zero, -torch.ones(1), torch.ones(1), .02)
        for _ in range(10): tick()
        self.assertEqual(rear.stage.item(), 0)
        release[:] = True
        tick()
        release[:] = False
        contacts[:, 3] = False
        forces[:, 3] = 0
        for _ in range(220):
            feet[:, 3] = rear.target()
            tick()
        self.assertTrue(rear.clearance_seen.item() and rear.midpoint_seen.item())
        self.assertEqual(rear.stage.item(), 2)
        self.assertEqual(rear.reload.item(), 0.)
        self.assertFalse(rear.verified.item())
        # A single spurious light touch cannot restore load.
        forces[:, 3] = 1.
        tick()
        self.assertEqual(rear.reload.item(), 0.)
        forces[:, 3] = 0.
        tick()
        self.assertEqual(rear.touch_stable.item(), 0.)
        # Sustained real contact and a full ramp precede the 1s rest gate.
        contacts[:, 3] = True
        forces[:, 3] = 50.
        for _ in range(30):
            feet[:, 3] = rear.target()
            tick()
        self.assertEqual(rear.stage.item(), 3)
        self.assertFalse(rear.verified.item())
        for _ in range(50): tick()
        self.assertTrue(rear.verified.item())

    def test_rear_step_missing_support_freezes_swing_without_loading_rr(self):
        rear = module.RearStep(1, 'cpu')
        active = torch.ones(1, dtype=torch.bool)
        feet = torch.zeros(1, 4, 3)
        contact = torch.ones(1, 4, dtype=torch.bool)
        force = torch.ones(1, 4)
        zero = torch.zeros(1, 3)
        def tick(release):
            rear.update(active, torch.tensor([release]), feet[:, 3], feet, contact, force,
                        torch.ones(1)*.03, zero, zero, zero, zero, -torch.ones(1), torch.ones(1), .02)
        tick(True)
        for _ in range(30): tick(False)
        previous = rear.target().clone()
        contact[:, 0] = False
        for _ in range(40): tick(False)
        torch.testing.assert_close(rear.target(), previous)
        self.assertEqual(rear.reload.item(), 0.)
        self.assertFalse(rear.verified.item())

    def test_flat_arc_has_smooth_endpoints_and_bounded_three_second_speed(self):
        u = torch.linspace(0., 1., 1001, dtype=torch.float64, requires_grad=True)
        point = module.flat_swing_arc(u)
        torch.testing.assert_close(point[[0, 500, 1000]], torch.tensor(
            [[0., 0., 0.], [.04, 0., .05], [.08, 0., 0.]], dtype=u.dtype))
        velocity = []
        for axis in (0, 2):
            first = torch.autograd.grad(point[:, axis].sum(), u, create_graph=True, retain_graph=True)[0]
            second = torch.autograd.grad(first.sum(), u, retain_graph=True)[0]
            torch.testing.assert_close(first[[0, -1]], torch.zeros(2, dtype=u.dtype), atol=1e-12, rtol=0.)
            torch.testing.assert_close(second[[0, -1]], torch.zeros(2, dtype=u.dtype), atol=1e-12, rtol=0.)
            velocity.append(first / 3.)
        self.assertLess(torch.stack(velocity, dim=1).norm(dim=1).max().item(), .067)
        self.assertTrue((point[:, 2] >= 0.).all())

    def test_level_orientation_preserves_heading_and_handles_quaternion_sign(self):
        # A90-degree heading combined with30-degree roll.
        q = torch.tensor([[.6830127, .1830127, .1830127, .6830127]])
        q = q / q.norm(dim=1, keepdim=True)
        torch.testing.assert_close(module.level_orientation(q, torch.zeros(1)), q)
        for sign in (1., -1.):
            level = module.level_orientation(sign * q, torch.ones(1))
            axes = torch.eye(3)[None]
            rotated = module.rotate_vector(level[:, None], axes)
            torch.testing.assert_close(rotated[0, 2], torch.tensor([0., 0., 1.]), atol=1e-6, rtol=0.)
            torch.testing.assert_close(rotated[0, 0], torch.tensor([0., 1., 0.]), atol=1e-6, rtol=0.)
            self.assertAlmostEqual(module.level_orientation(sign * q, torch.full((1,), .5)).norm().item(), 1., places=6)

    def test_start_rejects_turning_point_and_missing_foot(self):
        contact = torch.ones(3, 4, dtype=torch.bool)
        contact[2, 0] = False
        zero = torch.zeros(3, 3)
        acceleration = zero.clone()
        acceleration[1, 0] = .8
        result = module.settled_stance(contact, zero, zero, acceleration, zero, -torch.ones(3))
        self.assertEqual(result.tolist(), [True, False, False])

    def leg_model(self):
        return module.LegKinematics(dict(hip_origins=[[0.,0.,0.]]*4,
                                        hip_lateral_offsets=[.0955,-.0955,.0955,-.0955],
                                        link_lengths=[[.213,.213]]*4), dtype=torch.float64)

    def test_leg_forward_matches_independent_right_angle_geometry(self):
        model = self.leg_model()
        q = torch.zeros(1,4,3,dtype=torch.float64)
        expected = torch.stack((torch.zeros(4,dtype=torch.float64),model.lateral,torch.full((4,),-.426,dtype=torch.float64)),dim=1)
        torch.testing.assert_close(model.forward(q)[0],expected)
        q[:,:,0] = torch.pi/2
        expected[:,1] = .426; expected[:,2] = model.lateral
        torch.testing.assert_close(model.forward(q)[0],expected)

    def test_inverse_preserves_bent_knee_branch_and_exposes_unreachable_target(self):
        model = self.leg_model()
        q = torch.tensor([[[.2,.7,-1.5],[-.2,.9,-1.8],[.1,1.,-1.7],[-.1,.8,-1.6]]],dtype=torch.float64)
        torch.testing.assert_close(model.inverse(model.forward(q)),q)
        far = torch.full((1,4,3),2.,dtype=torch.float64)
        candidate = model.inverse(far)
        self.assertTrue(torch.isfinite(candidate).all())
        self.assertGreater((model.forward(candidate)-far).norm(dim=-1).min().item(),1.)

    def test_landing_feedback_preserves_swing_at_just_advanced_lift(self):
        phase = torch.tensor([1, 2, 4, 5, 5, 6])
        weight = torch.tensor([0., 0., 1., 1., .5, 0.])
        body = torch.ones(6, 3)
        swing = torch.full((6, 3), 3.)
        result = module.landing_feedback(phase, body, swing, weight)
        torch.testing.assert_close(result[:, 0], torch.tensor([1., 3., 3., 3., 2., 1.]))

    def test_acceleration_support_matches_force_and_zero_moment(self):
        feet = torch.tensor([[[.2,.2,0.],[.2,-.2,0.],[-.2,.2,0.],[-.2,-.2,0.]]], dtype=torch.float64)
        com = torch.tensor([[-.06,-.06,.3]], dtype=torch.float64)
        acceleration = torch.tensor([[.3,-.2]], dtype=torch.float64)
        weight = torch.tensor([200.], dtype=torch.float64)
        for unload in (0., .5, 1.):
            force = module.support_acceleration_forces(feet, com, weight, torch.tensor([unload], dtype=torch.float64), acceleration)
            torch.testing.assert_close(force.sum(dim=1), torch.cat((weight[:, None] * acceleration / 9.81, weight[:, None]), dim=1))
            self.assertLess(torch.cross(feet-com[:,None], force, dim=2).sum(dim=1).norm().item(), 1e-4)
            self.assertTrue((force[:,:,2] >= 0).all())

    def test_hold_metrics_preserve_excursion_after_return_and_mask_inactive(self):
        q = module.HoldQuality(2, 'cpu', .02)
        origin = torch.zeros(2,3); feet = torch.zeros(2,4,3)
        contact = torch.ones(2,4,dtype=torch.bool)
        for x in (0., .14, 0.):
            position = origin.clone(); position[:,0] = x
            q.sample(torch.tensor([True,False]), position, origin, feet, feet, origin, origin, contact, torch.ones(2)*.02)
        self.assertAlmostEqual(q.max_base_displacement[0].item(), .14)
        self.assertEqual(q.report()[0]['samples'], 3)
        self.assertIsNone(q.report()[1]['max_base_displacement'])

    def test_loaded_hold_target_preserves_pd_torque_at_capture_state(self):
        q = torch.tensor([[.1, .8, -1.5]])
        velocity = torch.tensor([[.04, -.1, .15]])
        torque = torch.tensor([[1.5, 6., -12.]])
        target = module.loaded_hold_target(q, velocity, torque)
        torch.testing.assert_close(30. * (target - q) - .6 * velocity, torque)

    def test_load_filter_is_monotone_bounded_and_can_be_disabled(self):
        old, target = torch.tensor([[-2., 3.]]), torch.tensor([[4., -5.]])
        for dt in (.005, .02, .5):
            result = module.filter_load_reference(old, target, dt, .1)
            self.assertTrue((result >= torch.minimum(old, target)).all())
            self.assertTrue((result <= torch.maximum(old, target)).all())
            self.assertLess((target - result).norm().item(), (target - old).norm().item())
        torch.testing.assert_close(module.filter_load_reference(old, target, .02, 0.), target)
        value = old
        for _ in range(50):
            value = module.filter_load_reference(value, target, .02, .1)
        torch.testing.assert_close(value, target, atol=.001, rtol=0.)

    def test_swing_bias_freezes_at_gate_and_has_bounded_reversible_windup(self):
        bias = torch.tensor([[.029, -.029, 0.], [.01, -.01, .02]])
        error = torch.tensor([[1., -1., 0.], [1., -1., 1.]])
        mask = torch.tensor([True, False])
        result = module.integrate_swing_bias(bias, error, mask, .02, .5)
        torch.testing.assert_close(result, torch.tensor([[.03, -.03, 0.], [.01, -.01, .02]]))
        restored = module.integrate_swing_bias(result, -error, mask, .02, .5)
        torch.testing.assert_close(restored[0], torch.tensor([.02, -.02, 0.]))

    def test_shift_reaches_margin_without_unnecessary_centroid_travel(self):
        triangle = torch.tensor([[[.2, -.2], [-.2, -.2], [-.2, .2]]], dtype=torch.float64)
        point = torch.tensor([[0., 0.]], dtype=torch.float64)
        delta = module.support_shift(point, triangle, .03)
        self.assertGreaterEqual(module.triangle_margin(point + delta, triangle).item(), .03)
        self.assertLess(delta.norm().item(), .03001)
        torch.testing.assert_close(module.support_shift(point + 2 * delta, triangle, .03), torch.zeros_like(delta))
        outside = torch.tensor([[1., 1.]], dtype=torch.float64)
        self.assertLessEqual(module.support_shift(outside, triangle, .03).norm().item(), .100001)
        torch.testing.assert_close(delta, module.support_shift(point, triangle.flip(1), .03))

    def test_support_forces_preserve_weight_and_moment_inside_tripod(self):
        feet = torch.tensor([[[.2, .2], [.2, -.2], [-.2, .2], [-.2, -.2]]], dtype=torch.float64)
        com = torch.tensor([[-.06, -.06]], dtype=torch.float64)
        for unload in (0., .5, 1.):
            force = module.support_vertical_forces(feet, com, torch.tensor([200.], dtype=torch.float64), torch.tensor([unload], dtype=torch.float64))
            self.assertTrue((force >= 0).all())
            self.assertAlmostEqual(force.sum().item(), 200., places=8)
            self.assertLess(((feet - com[:, None]) * force[..., None]).sum(dim=1).norm().item(), 1e-4)
            if unload == 1.:
                self.assertEqual(force[0, 0].item(), 0.)

    def test_support_margin_is_winding_independent_and_rejects_degenerate_triangle(self):
        triangle = torch.tensor([[[0., 0.], [1., 0.], [0., 1.]]])
        inside, outside = torch.tensor([[.2, .2]]), torch.tensor([[.8, .8]])
        self.assertGreater(module.triangle_margin(inside, triangle).item(), .19)
        self.assertLess(module.triangle_margin(outside, triangle).item(), 0)
        torch.testing.assert_close(module.triangle_margin(inside, triangle), module.triangle_margin(inside, triangle.flip(1)))
        self.assertLess(module.triangle_margin(inside, torch.zeros_like(triangle)).item(), 0)

    def test_damped_joint_step_reduces_local_cartesian_error(self):
        torch.manual_seed(2)
        jacobian = torch.randn(32, 3, 3)
        error = torch.randn(32, 3) * .01
        delta = module.damped_leg_delta(jacobian, error)
        remaining = error - (jacobian @ delta[..., None]).squeeze(-1)
        self.assertTrue((remaining.norm(dim=1) <= error.norm(dim=1)).all())
        self.assertTrue(torch.isfinite(module.damped_leg_delta(torch.zeros_like(jacobian), error)).all())


if __name__ == "__main__":
    unittest.main()
