from config_cases import load_case
"""Protect swing freedom, terrain gating and checkpoint reward provenance."""
import unittest
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, PPOConfig, configuration, require_implementation, load_config,
    FLAT_DAMPING_REVISION, FLAT_SPEED_REVISION,
)
from climb_skill.tasks.direct.climb_skill.mdp.flat_stability import flat_surface_gate, flat_motion_costs


class FlatMotion(unittest.TestCase):
    def setUp(self):
        self.cfg = TaskConfig(flat_angular_velocity_weight=.3, flat_slip_weight=.5)
        self.feet = torch.tensor([[[.25,.15,.02],[.25,-.15,.02],[-.25,.15,.02],[-.25,-.15,.02]]])
        self.forces = torch.zeros_like(self.feet); self.forces[...,2] = 30.
        self.heights = torch.tensor([.2])

    def costs(self, velocities, angular, feet=None, forces=None):
        feet = self.feet if feet is None else feet
        forces = self.forces if forces is None else forces
        gate = flat_surface_gate(feet, forces, self.heights, self.cfg)
        return flat_motion_costs(feet, forces, velocities, angular, self.heights, gate, self.cfg)

    def test_yaw_and_small_motion_free_but_roll_pitch_damped(self):
        v = torch.full_like(self.feet, .01)
        a,s = self.costs(v, torch.tensor([[.3,-.4,10.]]))
        self.assertEqual(float(a+s), 0.)
        a,s = self.costs(v, torch.tensor([[1.4,-1.4,0.]]))
        torch.testing.assert_close(a, torch.tensor([2.]))

    def test_loaded_slip_numeric_and_unloaded_swing_free(self):
        v = torch.zeros_like(self.feet); v[:,0,0] = .33
        _,s = self.costs(v, torch.zeros(1,3))
        torch.testing.assert_close(s, torch.tensor([.25]))
        f = self.forces.clone(); f[:,0] = 0.
        _,s = self.costs(v*100, torch.zeros(1,3), forces=f)
        self.assertEqual(float(s),0.)
        feet = self.feet.clone(); feet[:,0,2] += .1
        _,s = self.costs(v*100, torch.zeros(1,3), feet=feet)
        self.assertEqual(float(s),0.)

    def test_edge_mixed_height_and_flight_disable_both_costs(self):
        for dx in [.35,.5,.75]:
            feet = self.feet.clone(); feet[...,0] += dx
            a,s = self.costs(torch.ones_like(feet), torch.ones(1,3)*3, feet=feet)
            self.assertEqual(float(a+s),0.)
        a,s = self.costs(torch.ones_like(self.feet), torch.ones(1,3)*3, forces=self.forces*0)
        self.assertEqual(float(a+s),0.)

    def test_new_profile_and_old_checkpoint_contracts(self):
        root = Path(__file__).resolve().parents[1]
        old,ppo = load_case('legacy_flat_posture')
        new,nppo = load_case('legacy_stable')
        self.assertEqual(ppo,nppo); self.assertEqual(nppo.save_interval,500)
        before = configuration(old,ppo)
        for key in list(before['task']):
            if key.startswith(('flat_angular_', 'flat_slip_')): del before['task'][key]
        self.assertEqual(before['implementation_revision'],FLAT_SPEED_REVISION)
        require_implementation(before)
        after = configuration(new,nppo)
        self.assertEqual(after['implementation_revision'],FLAT_DAMPING_REVISION)
        require_implementation(after)
        after['implementation_revision'] = FLAT_SPEED_REVISION
        with self.assertRaises(ValueError): require_implementation(after)
        for kwargs in [dict(flat_slip_weight=-1),dict(flat_slip_scale=0),
                       dict(flat_angular_velocity_tolerance=float('nan'))]:
            with self.assertRaises(ValueError): TaskConfig(**kwargs).validate()


if __name__ == '__main__': unittest.main()
