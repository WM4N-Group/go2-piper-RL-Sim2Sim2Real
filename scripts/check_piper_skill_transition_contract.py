"""Contract regressions: no physical safety claims or simulator dependencies."""
from dataclasses import replace
import unittest
import json
from piper_skill_transition_contract import EntryState, Handoff, Phase, skill_elapsed_seconds, BoundedReference


def state(**updates):
    s = EntryState(100, 2.0, tuple(f'j{i}' for i in range(18)), (0.,)*18,
                   (0.,)*18, (.1,)*18, (1.,)*18, 3, 'v212-with-nav-v1', 'box0',
                   {'loaded': True, 'velocity': True}, .5)
    return replace(s, **updates)


class Checks(unittest.TestCase):
    def pending(self):
        h = Handoff('NAV', 'PUSH', ('loaded', 'velocity'))
        h.begin(state(stable_seconds=0.))
        return h

    def test_clock_starts_at_activation_without_resetting_task(self):
        self.assertEqual(skill_elapsed_seconds(600, 600, .02), 0.)
        self.assertEqual(skill_elapsed_seconds(625, 600, .02), .5)
        self.assertEqual(skill_elapsed_seconds(25, 0, .02), .5)
        with self.assertRaises(ValueError): skill_elapsed_seconds(599, 600, .02)

    def test_no_future_push_stage_required(self):
        h = self.pending(); s = state()
        self.assertTrue(h.offer(s)); h.start(s, authorized=True)
        self.assertEqual([e['event'] for e in h.events],
                         ['transition_started', 'transition_ready', 'skill_started'])
        self.assertEqual(h.phase, Phase.STARTED)

    def test_wait_invalidates_old_readiness(self):
        h = self.pending(); h.offer(state())
        with self.assertRaises(ValueError): h.start(state(step=101, physical_time_s=2.02), authorized=True)
        self.assertFalse(h.offer(state(step=101, physical_time_s=2.02,
                                      gates={'loaded': False, 'velocity': True}, stable_seconds=0.)))
        with self.assertRaises(ValueError): h.start(state(), authorized=True)

    def test_missing_gate_or_history_never_passes(self):
        for s in [state(gates={'loaded': True}), state(history_valid_frames=2),
                  state(stable_seconds=.48), state(gates={'loaded': 1, 'velocity': True})]:
            self.assertFalse(self.pending().offer(s))

    def test_rebinding_and_reset_are_rejected(self):
        for s in [state(step=0), state(physical_time_s=0.), state(source_id='other'),
                  state(object_id='box1'), state(joint_names=tuple(reversed(state().joint_names)))]:
            with self.assertRaises(ValueError): self.pending().offer(s)

    def test_nonfinite_state_is_rejected(self):
        with self.assertRaises(ValueError): self.pending().offer(state(applied_torque=(float('nan'),)*18))

    def test_abstain_is_not_start_or_safe_action(self):
        h = self.pending(); h.offer(state())
        for value in (False, 'abstain', 'false', 1, None):
            with self.assertRaises(ValueError): h.start(state(), authorized=value)
        h.fail(state(), 'NO_VALIDATED_HOLD'); self.assertEqual(h.phase, Phase.FAILED)
        with self.assertRaises(ValueError): h.offer(state())

    def test_ready_snapshot_cannot_be_mutated_by_caller(self):
        gates={'loaded': True, 'velocity': True}
        s=state(gates=gates); h=self.pending(); h.offer(s)
        gates['loaded']=False
        self.assertIs(s.gates['loaded'], True)
        with self.assertRaises(TypeError): s.gates['loaded']=False
        changed=replace(s, gates=gates)
        with self.assertRaises(ValueError): h.start(changed, authorized=True)
        self.assertFalse(h.offer(changed))

    def test_wait_refresh_publishes_measured_state_before_start(self):
        h=self.pending(); h.offer(state())
        newer=state(step=101, physical_time_s=2.02, applied_torque=(1.1,)*18)
        h.offer(newer)
        event=json.loads(json.dumps(h.events[-1]))
        self.assertEqual(event['event'], 'transition_ready_refreshed')
        self.assertEqual(event['contract_version'], 1)
        self.assertEqual(event['entry_state']['applied_torque'], [1.1]*18)
        with self.assertRaises(ValueError): h.start(state(), authorized=True)
        h.start(newer, authorized=True)

    def test_state_arrays_are_snapshots_and_counts_are_validated(self):
        target=[.1]*18; s=state(applied_position_target=target)
        target[0]=99.
        self.assertEqual(s.applied_position_target[0], .1)
        for bad in (state(step=True),state(step=1.5),state(history_valid_frames=float('nan'))):
            with self.assertRaises(ValueError): self.pending().offer(bad)


class ReferenceChecks(unittest.TestCase):
    def test_step_and_reversal_preserve_rate_and_acceleration(self):
        r=BoundedReference((.4,-.2),(0.,0.),(.45,.45),(1.,1.),.02)
        for goal in [(1.,-1.)]*80+[(-1.,1.)]*160+[(0.,0.)]*100:
            q,v=r.position,r.velocity
            r.advance(goal)
            for i in range(2):
                self.assertLessEqual(abs(r.position[i]-q[i]),.45*.02+1e-12)
                self.assertLessEqual(abs(r.velocity[i]-v[i]),1.*.02+1e-12)

    def test_loaded_target_is_preserved_and_not_replaced_by_joint_position(self):
        r=BoundedReference((.4,),(.1,),(.45,),(1.,),.02)
        self.assertEqual(r.position,(.4,))
        self.assertAlmostEqual(r.advance((.8,))[0],.4024)

    def test_invalid_reference_does_not_mutate_state(self):
        r=BoundedReference((.4,),(0.,),(.45,),(1.,),.02)
        with self.assertRaises(ValueError):r.advance((float('nan'),))
        self.assertEqual(r.position,(.4,))


if __name__ == '__main__': unittest.main()
