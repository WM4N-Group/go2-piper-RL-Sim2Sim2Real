"""Adversarial evidence checks for continuous skill-chain audit."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit_piper_transition import audit, FINAL_GATES, METRICS, SUCCESS


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'controller.py').write_text('# fixed candidate\n')
        digest = hashlib.sha256((self.root / 'controller.py').read_bytes()).hexdigest()
        (self.root / 'plan.json').write_text(json.dumps({'files': {'controller.py': digest}}))
        self.run = self.root / 'seed1-native-entry'
        self.run.mkdir()
        self.rows = [dict(step=i, time_s=i * .02,
                          return_nav=dict(arrival_brake=True, goal_error_m=.03,
                                          heading_error_rad=.02, travel_m=.22),
                          exit_stable_gates=dict.fromkeys(FINAL_GATES, True),
                          retracted_ready=True) for i in range(26)]
        for row in self.rows:
            row.update(root_velocity=[0., 0., 0.], root_angular_velocity=[0., 0., 0.],
                       dq=[0.]*18, foot_forces=[[0., 0., 12.]]*4,
                       root_quaternion=[1., 0., 0., 0.], clearance_m=.05, torque_ratio=.6)
        self.rows[0]['retracted_ready'] = False
        self.report = dict(seed=1, outcome=SUCCESS, control_dt=.02, samples=26,
                           physical_resets_after_initial=0, terminal={},
                           return_nav_final_state=self.rows[-1], **dict.fromkeys(METRICS, 0))

    def result(self):
        (self.run / 'report.json').write_text(json.dumps(self.report))
        (self.run / 'control.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in self.rows))
        return audit(self.root, [1])['runs'][0]['status']

    def test_continuous_final_state(self):
        self.assertEqual(self.result(), 'success')

    def test_one_failed_sample_breaks_stable_window(self):
        self.rows[12]['exit_stable_gates']['four_loaded_feet'] = False
        self.assertEqual(self.result(), 'invalid_evidence')

    def test_gate_bits_do_not_override_measured_load_or_speed(self):
        self.rows[-1]['foot_forces'] = [[0., 0., 0.]]*4
        self.assertEqual(self.result(), 'invalid_evidence')
        self.rows[-1]['foot_forces'] = [[0., 0., 12.]]*4
        self.rows[-1]['root_velocity'] = [.1, 0., 0.]
        self.assertEqual(self.result(), 'invalid_evidence')

    def test_truncated_or_reset_clock_cannot_pass(self):
        self.rows[12]['time_s'] = 0.
        self.assertEqual(self.result(), 'invalid_evidence')

    def test_native_failure_cannot_be_labelled_success(self):
        self.report['terminal'] = {'invalid_hand_contact': True}
        self.assertEqual(self.result(), 'invalid_evidence')

    def test_runtime_error_is_failure_even_with_complete_log(self):
        self.report['outcome'] = 'runtime_error'
        self.assertEqual(self.result(), 'failure')

    def test_missing_started_and_unrun_are_distinct(self):
        result = audit(self.root, [1, 2])
        self.assertEqual(result['counts']['missing_terminal'], 1)
        self.assertEqual(result['counts']['not_run'], 1)

    def test_modified_candidate_rejected(self):
        (self.root / 'controller.py').write_text('# changed candidate\n')
        with self.assertRaises(ValueError): audit(self.root, [1])

    def test_duplicate_start_rejected(self):
        with self.assertRaises(ValueError): audit(self.root, [1, 1])

    def test_final_state_must_match_full_log(self):
        self.report['return_nav_final_state'] = {'step': 25}
        self.assertEqual(self.result(), 'invalid_evidence')


if __name__ == '__main__': unittest.main()
