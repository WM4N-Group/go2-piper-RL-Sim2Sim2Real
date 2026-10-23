"""Stage selection and edge targets; no local physics execution."""
from pathlib import Path
import importlib.util
import unittest
import torch
p=Path(__file__).resolve().parents[1]/'source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/climb_stage_math.py'
spec=importlib.util.spec_from_file_location('stage_math',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class StageChecks(unittest.TestCase):
    def test_rear_edge_preparation_precedes_either_ascent_and_does_not_loop(self):
        feet=torch.tensor([[[1.11,.18,.224],[1.11,-.18,.224],[.66,.2,.024],[.65,-.2,.024]]]).repeat(6,1,1)
        contacts=torch.ones(6,4,dtype=torch.bool);leg=torch.tensor([3,2,2,3,0,2])
        feet[1,2,0]=.69 # Prepared foot proceeds to ascent.
        feet[2,3]=torch.tensor([.84,-.2,.224]) # Never add ground step after other rear ascends.
        contacts[3,0]=False
        next_x=torch.tensor([.87,.91,.88,.87,1.3,.69])
        torch.testing.assert_close(m.prepare_rear_edge_x(next_x,feet,contacts,leg),
            torch.tensor([.69,.91,.88,.87,1.3,.69]))


    def test_rear_ascent_cap_preserves_ground_front_and_platform_steps(self):
        feet=torch.tensor([[[1.16,.18,.224],[1.16,-.18,.224],[.65,.2,.024],[.65,-.2,.024]]]).repeat(7,1,1)
        legs=torch.tensor([2,3,2,0,2,2,2]);contacts=torch.ones(7,4,dtype=torch.bool)
        feet[4,2]=torch.tensor([.84,.2,.224]) # Already landed: resume ordinary steps.
        contacts[5,0]=False # Do not change a target without front support.
        feet[6,2,0]=.85 # Never retreat to enforce the cap.
        target=m.limit_rear_ascent_x(torch.tensor([.87,.87,.69,1.38,1.06,.87,1.07]),feet,contacts,legs,.83)
        torch.testing.assert_close(target,torch.tensor([.83,.83,.69,1.38,1.06,.87,.85]))
        feet[0,2]=torch.tensor([.83,.2,.224])
        chosen=m.choose_stage_leg(feet[:1],contacts[:1],torch.tensor([False]),torch.tensor([0]),True,1.16)
        self.assertEqual(chosen.item(),3) # Last rear foot must still follow.


    def test_shorter_second_front_advance_keeps_ascent_and_returns_to_rear_steps(self):
        feet=torch.tensor([[[1.06,.18,.224],[1.06,-.18,.224],[.65,.20,.024],[.65,-.20,.024]]]).repeat(5,1,1)
        feet[1,2:,0]=.4  # First follow-up keeps its original stride.
        feet[2,0,2]=.024  # Initial ascent keeps its original target.
        feet[3,0,0]=1.25  # Never command backward to enforce a cap.
        contacts=torch.ones(5,4,dtype=torch.bool);legs=torch.tensor([0,0,0,0,3])
        next_x=torch.tensor([1.28,1.28,1.28,1.47,.87])
        capped=m.limit_front_followup_x(next_x,feet,contacts,legs,1.16)
        torch.testing.assert_close(capped,torch.tensor([1.16,1.28,1.28,1.25,.87]))
        platform=feet[:1].clone();platform[:,:,2]=.224;platform[:,2:,0]=.9
        # Once all four feet are on top, normal forward stepping must resume.
        torch.testing.assert_close(m.limit_front_followup_x(torch.tensor([1.28]),platform,
            contacts[:1],torch.tensor([0]),1.16),torch.tensor([1.28]))
        original=feet[:1].clone();pending=torch.zeros(1,dtype=torch.bool);fallback=torch.tensor([3])
        chosen=m.choose_stage_leg(original,contacts[:1],pending,fallback,True,1.16)
        self.assertEqual(chosen.item(),0)
        original[0,0,0]=1.16
        self.assertEqual(m.choose_stage_leg(original,contacts[:1],pending,fallback,True,1.16).item(),1)
        original[0,1,0]=1.16
        self.assertEqual(m.choose_stage_leg(original,contacts[:1],pending,fallback,True,1.16).item(),2)
        # Original target remains active without the diagnostic override.
        self.assertEqual(m.choose_stage_leg(original,contacts[:1],pending,fallback,True).item(),0)

    def test_front_anchors_follow_rear_progress_without_skipping_ascent(self):
        feet=torch.tensor([[[.84,.17,.224],[.84,-.17,.224],[.3,.17,.024],[.3,-.17,.024]]]).repeat(6,1,1)
        feet[1:,2:,0]=.4
        feet[2:,0,0]=1.06
        feet[3:,1,0]=1.06
        feet[4:,2:,0]=.6
        feet[5,0,2]=.024
        contacts=torch.ones(6,4,dtype=torch.bool);pending=torch.zeros(6,dtype=torch.bool)
        chosen=m.choose_stage_leg(feet,contacts,pending,torch.full((6,),3),True)
        self.assertEqual(chosen.tolist(),[2,0,1,2,0,0])
        feet[:,:,:2]=torch.tensor([1.4,0.]);feet[:,:,2]=.224
        self.assertEqual(m.choose_stage_leg(feet,contacts,pending,torch.full((6,),3),True).tolist(),[3]*6)

    def test_reach_bound_rejects_retreat_and_is_translation_invariant(self):
        hip=torch.tensor([[0.,0.,0.]])
        thigh=torch.tensor([[0.,.0955,0.]])
        calf=thigh+torch.tensor([[0.,0.,-.213]])
        foot=calf+torch.tensor([[0.,0.,-.213]])
        target=torch.tensor([[.3,.0955,0.]])
        margin=m.outer_reach_margin(hip,thigh,calf,foot,target)
        self.assertGreater(margin.item(),0.)
        retreat=torch.tensor([[-.2,0.,0.]])
        self.assertLess(m.outer_reach_margin(hip+retreat,thigh+retreat,calf+retreat,foot+retreat,target).item(),0.)
        shift=torch.tensor([[12.,-8.,3.]])
        torch.testing.assert_close(m.outer_reach_margin(hip+shift,thigh+shift,calf+shift,foot+shift,target+shift),margin)

    def test_unload_has_dense_signal_but_flight_and_missing_support_get_no_credit(self):
        force=torch.tensor([[50.,50.,50.,50.],[10.,70.,60.,60.],[0.,70.,60.,70.],
                            [0.,0.,0.,0.],[0.,0.,100.,100.]])
        scores=m.supported_lift_scores(force,torch.zeros(5,dtype=torch.long),
            torch.full((5,),.15),torch.full((5,),.025),torch.full((5,),.275),torch.ones(5,dtype=torch.bool))
        torch.testing.assert_close(scores[0],torch.tensor([0.,.8,1.,0.,0.]))
        torch.testing.assert_close(scores[1],torch.tensor([0.,0.,.5,0.,0.]))
        torch.testing.assert_close(scores[2],torch.tensor([0.,0.,1.,0.,0.]))

    def test_inactive_and_loaded_foot_do_not_get_lift_credit(self):
        force=torch.tensor([[0.,70.,60.,70.],[5.,70.,60.,65.]])
        unload,height,contact=m.supported_lift_scores(force,torch.zeros(2,dtype=torch.long),
            torch.ones(2),torch.zeros(2),torch.ones(2),torch.tensor([False,True]))
        self.assertEqual(height.tolist(),[0.,0.])
        self.assertEqual(contact.tolist(),[0.,0.])
        self.assertEqual(unload[0],0.)

    def test_loaded_pose_uses_explicit_pd_and_rejects_zero_simulator_stiffness(self):
        q=torch.tensor([[.1,-1.8]]);torque=torch.tensor([[3.,-100.]])
        effort=torch.tensor([[23.7,45.43]]);gain=torch.tensor([[30.,30.]])
        expected=q+torch.tensor([[.1,-.75*45.43/30]])
        torch.testing.assert_close(m.loaded_position_reference(q,torque,effort,gain),expected)
        with self.assertRaises(ValueError):m.loaded_position_reference(q,torque,effort,torch.zeros_like(gain))

    def test_reset_without_sensor_history_uses_geometry_not_false_missing_front_contact(self):
        feet=torch.tensor([[[.9,.16,.2245],[.9,-.16,.2245],[.85,.16,.2245],[.69,-.16,.024]]])
        chosen=m.choose_stage_leg(feet,torch.zeros(1,4,dtype=torch.bool),torch.ones(1,dtype=torch.bool),torch.tensor([0]))
        self.assertEqual(chosen.item(),3)

    def test_front_ascent_precedes_rear_following_and_all_top_uses_cycle(self):
        feet=torch.tensor([[[.69,.16,.024],[.69,-.16,.024],[.3,.16,.024],[.3,-.16,.024]]]).repeat(4,1,1)
        feet[1:,0,[0,2]]=torch.tensor([.9,.2245])
        feet[2:,1,[0,2]]=torch.tensor([.9,.2245])
        feet[3,2:,[0,2]]=torch.tensor([[.9,.2245],[.9,.2245]])
        chosen=m.choose_stage_leg(feet,torch.ones(4,4,dtype=torch.bool),torch.zeros(4,dtype=torch.bool),torch.tensor([3,3,3,3]))
        self.assertEqual(chosen.tolist(),[0,1,2,3])

    def test_landing_centers_never_target_the_vertical_box_face(self):
        x=torch.linspace(.1,1.6,10000);target=m.next_stage_foothold_x(x,.22)
        self.assertFalse(((target>.690001)&(target<.829999)).any())
        self.assertTrue((target>=x).all())
        self.assertLessEqual(target.max(),1.75)


if __name__=='__main__':unittest.main()
