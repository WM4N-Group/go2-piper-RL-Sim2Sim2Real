"""Audit one candidate's continuous NAV/PUSH/NAV evidence, without simulation.

An audit distinguishes success, failure, missing evidence and unrun starts.
It does not establish physical safety between logged samples or release a skill.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

SUCCESS = 'nav_push_stow_nav_target_stable'
FINAL_GATES = ('transfer_complete', 'position', 'orientation', 'velocity',
               'four_loaded_feet', 'joint_speed', 'soft_limits', 'clearance',
               'effort', 'hand_unloaded', 'box_still_settled')
METRICS = ('minimum_clearance_m', 'max_torque_ratio', 'max_substep_arm_torque_ratio',
           'effort_over_098_samples', 'airborne_samples', 'under_three_support_samples',
           'max_abs_vz_m_s', 'max_single_foot_N', 'max_sum_foot_force_norm_N')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def measured_stop(row):
    """Corroborate logged gate bits with measured physical stop quantities."""
    try:
        velocity, omega = row['root_velocity'], row['root_angular_velocity']
        dq, feet = row['dq'], row['foot_forces']
        quat = row['root_quaternion']
        flat = [*velocity, *omega, *dq, *quat, *(v for f in feet for v in f),
                row['clearance_m'], row['torque_ratio']]
        if (len(velocity) != 3 or len(omega) != 3 or len(dq) != 18
                or len(quat) != 4 or len(feet) != 4 or any(len(f) != 3 for f in feet)
                or not all(math.isfinite(v) for v in flat)):
            return False
        return (sum(v*v for v in velocity) < .025**2
                and sum(v*v for v in omega) < .1**2
                and min(f[2] for f in feet) >= 8.
                and max(abs(v) for v in dq[:12]) < .35
                and max(abs(v) for v in dq[12:]) < .2
                and abs(sum(v*v for v in quat)-1.) < 1e-4
                and -(1.-2.*(quat[1]**2+quat[2]**2)) < -.98
                and row['clearance_m'] >= .035 and 0 <= row['torque_ratio'] < .98)
    except (KeyError, TypeError, ValueError):
        return False


def final_ready(row):
    nav = row.get('return_nav', {})
    gates = row.get('exit_stable_gates', {})
    return (measured_stop(row)
            and nav.get('arrival_brake') is True
            and 0 <= nav.get('goal_error_m', math.inf) < .05
            and 0 <= nav.get('heading_error_rad', math.inf) < .12
            and nav.get('travel_m', -math.inf) >= .20
            and row.get('retracted_ready') is True
            and all(gates.get(key) is True for key in FINAL_GATES))


def audit_run(directory, seed):
    path = directory / f'seed{seed}-native-entry'
    report_path = path / 'report.json'
    if not report_path.exists():
        started = path.exists() or (directory / f'launch-seed{seed}.json').exists()
        return dict(seed=seed, status='missing_terminal' if started else 'not_run')
    try:
        report = json.loads(report_path.read_text())
        if report['seed'] != seed:
            raise ValueError('Report seed differs from requested start')
        result = dict(seed=seed, outcome=report['outcome'],
                      report_sha256=sha(report_path),
                      metrics={key: report[key] for key in METRICS})
        dt = report['control_dt']
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('Invalid sample period')
        previous = last = None
        count = 0
        stable = 0.
        control = path / 'control.jsonl'
        with control.open() as stream:
            for line in stream:
                row = json.loads(line)
                if not math.isfinite(row['time_s']):
                    raise ValueError('Nonfinite physical clock')
                if previous is None:
                    if row['step'] != 0 or row['time_s'] != 0:
                        raise ValueError('Initialization sample missing')
                elif (row['step'] != previous['step'] + 1
                      or abs(row['time_s'] - previous['time_s'] - dt) > 1e-7):
                    raise ValueError('Noncontinuous physical clock or missing sample')
                if abs(row['time_s'] - row['step'] * dt) > 1e-7:
                    raise ValueError('Step and clock disagree')
                stable = stable + dt if final_ready(row) else 0.
                previous = last = row
                count += 1
        if count != report['samples'] or last is None:
            raise ValueError('Report sample count differs from control evidence')
        result.update(samples=count, end_time_s=last['time_s'],
                      control_sha256=sha(control), final_ready_seconds=stable)
        if report['physical_resets_after_initial'] != 0:
            raise ValueError('Physical reset during continuous chain')
        if report['outcome'] == SUCCESS:
            if report.get('error') or any(report['terminal'].values()):
                raise ValueError('Success conflicts with runtime/native failure')
            if stable + 1e-8 < .5:
                raise ValueError('Final gates did not hold continuously for 0.5 seconds')
            if report.get('return_nav_final_state') != last:
                raise ValueError('Final report state differs from last control sample')
            result['status'] = 'success'
        else:
            result['status'] = 'failure'
        return result
    except (ValueError, KeyError, TypeError, OSError) as error:
        # No deployment paths or traceback are needed in the portable summary.
        return dict(seed=seed, status='invalid_evidence', error=type(error).__name__)


def audit(directory, seeds):
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('Expected starts must be explicit and unique')
    plan_path = directory / 'plan.json'
    plan = json.loads(plan_path.read_text())
    for name, expected in plan['files'].items():
        path = directory / name
        if Path(name).is_absolute() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError('Candidate inventory escapes its directory')
        if sha(path) != expected:
            raise ValueError(f'Candidate inventory mismatch: {name}')
    runs = [audit_run(directory, seed) for seed in seeds]
    return dict(scope='One candidate, logged full-chain development evidence; no release decision',
                candidate=directory.name, plan_sha256=sha(plan_path), expected_starts=seeds,
                counts={status: sum(run['status'] == status for run in runs)
                        for status in ('success', 'failure', 'missing_terminal', 'not_run', 'invalid_evidence')},
                runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--expected-seeds', nargs='+', type=int, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.candidate, args.expected_seeds)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(text)
    print(json.dumps(result['counts']))
    return int(bool(result['counts']['missing_terminal'] or result['counts']['invalid_evidence']))


if __name__ == '__main__':
    raise SystemExit(main())
