"""Boundary regressions for the online CLIMB completion contract."""
import copy
import unittest
from piper_climb_completion import ClimbCompletion

S=dict(feet_position=[[1.2,.2,.224],[1.2,-.2,.224],[.9,.2,.224],[.9,-.2,.224]],foot_contact_force_z=[50.]*4,platform_extension_completed=2,platform_extension_moving=False,platform_final_started=True,platform_hold_active=True,platform_final_goal=[1.,0.,.5],guidance_body_target=[1.,0.,.5],robot_position=[1.,0.,.5],guidance_reference_age=4.,robot_velocity=[0.]*3,robot_angular_velocity=[0.]*3,guidance_command_limit_excess=[0.]*4)
class Check(unittest.TestCase):
 def test_continuous_hold(self):
  d=ClimbCompletion()
  for i in range(150):self.assertFalse(d.update(S,time_s=i*.02,safety_ok=True)['complete'])
  self.assertTrue(d.update(S,time_s=3.,safety_ok=True)['complete'])
 def test_failure_dominates_and_latches(self):
  d=ClimbCompletion();d.update(S,time_s=0.,safety_ok=False)
  for i in range(1,200):self.assertFalse(d.update(S,time_s=i*.02,safety_ok=True)['complete'])
 def test_incomplete_and_bad_endpoints(self):
  for key,value in [('platform_extension_completed',1),('platform_extension_moving',True),('platform_final_started',False),('foot_contact_force_z',[7.9]*4),('robot_velocity',[.03,0.,0.]),('guidance_command_limit_excess',[1e-5]*4),('robot_position',[1.02,0.,.5]),('feet_position',[[.7,0.,.224]]*4),('robot_velocity',[float('nan'),0.,0.]),('platform_final_goal',[float('nan'),0.,.5]),('robot_velocity',[])]:
   s=copy.deepcopy(S);s[key]=value;d=ClimbCompletion()
   for i in range(155):self.assertFalse(d.update(s,time_s=i*.02,safety_ok=True)['complete'],key)
  self.assertFalse(ClimbCompletion().update({},time_s=0.,safety_ok=True)['complete'])
 def test_gap_and_interruption_restart_clock(self):
  d=ClimbCompletion();d.update(S,time_s=0.,safety_ok=True)
  self.assertEqual(d.update(S,time_s=5.,safety_ok=True)['stable_s'],0.)
  s=copy.deepcopy(S);s['foot_contact_force_z'][0]=0.;d.update(s,time_s=5.02,safety_ok=True)
  self.assertEqual(d.update(S,time_s=5.04,safety_ok=True)['stable_s'],0.)
 def test_single_swing_foot_is_not_four_feet(self):
  s=copy.deepcopy(S);s['feet_position']=[1.2,.2,.224]
  self.assertFalse(ClimbCompletion().update(s,time_s=0.,safety_ok=True)['complete'])
 def test_repeated_time_rejected(self):
  d=ClimbCompletion();d.update(S,time_s=0.,safety_ok=True)
  with self.assertRaises(ValueError):d.update(S,time_s=0.,safety_ok=True)
if __name__=='__main__':unittest.main()
