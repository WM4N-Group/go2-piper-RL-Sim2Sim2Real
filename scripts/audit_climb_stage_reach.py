"""Offline FK check of measured CLIMB terminal poses and swing clearance targets."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from crawl_leg_kinematics import LegKinematics, rotate_vector


def audit(geometry_report, evaluation):
    source = json.loads(geometry_report.read_text())
    report = json.loads(evaluation.read_text())
    terminal = report['terminal_states']
    names = report['joint_names']
    model = LegKinematics(source['leg_geometry'], dtype=torch.float64)
    legs = ('FL', 'FR', 'RL', 'RR')
    slots = [[names.index(leg+'_'+part+'_joint') for part in ('hip', 'thigh', 'calf')] for leg in legs]
    feet = torch.tensor([[t['robot_body_position'][report['body_names'].index(leg+'_foot')]
                          for leg in legs] for t in terminal], dtype=torch.float64)
    position = torch.tensor([t['robot_position'] for t in terminal], dtype=torch.float64)
    quaternion = torch.tensor([t['robot_quaternion'] for t in terminal], dtype=torch.float64)
    measured = torch.tensor([t['robot_joint_position'] for t in terminal], dtype=torch.float64)[:, slots]
    measured_body = rotate_vector(quaternion[:, None], feet-position[:, None], inverse=True)
    error = (model.forward(measured)-measured_body).norm(dim=-1)
    if error.max() >= 1e-5:
        raise ValueError('Geometry does not reproduce the measured foot poses')
    rows = torch.arange(len(terminal))
    selected = torch.tensor([t['crawl_leg_index'] for t in terminal])
    target = feet.clone()
    target[rows, selected] = torch.tensor([t['crawl_landing_position'] for t in terminal], dtype=torch.float64)
    # These box-edge reports use an upward first step. Reject other geometry
    # rather than assuming the landing height is the swing apex for a descent.
    if (target[rows, selected, 2] < .19).any():
        raise ValueError('This audit requires upward20cm box-edge landing targets')
    clearance = report['actual_physics']['crawl_contract']['foot_clearance']
    target[rows, selected, 2] += clearance
    target_body = rotate_vector(quaternion[:, None], target-position[:, None], inverse=True)
    joints = model.inverse(target_body)
    residual = (model.forward(joints)-target_body).norm(dim=-1)[rows, selected]
    result = {
        'scope': 'Measured terminal posture geometry only; no dynamics, joint-limit or collision certification',
        'evaluation_sha256': hashlib.sha256(evaluation.read_bytes()).hexdigest(),
        'geometry_report_sha256': hashlib.sha256(geometry_report.read_bytes()).hexdigest(),
        'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'kinematics_sha256': hashlib.sha256(Path(__file__).with_name('crawl_leg_kinematics.py').read_bytes()).hexdigest(),
        'max_measured_fk_error_m': error.max().item(),
        'terminal_goal_unreachable_count': int((residual > .001).sum()),
        'terminal_goal_fk_residual_m_max': residual.max().item(),
        'per_environment': [dict(env_id=t['env_id'], phase=t['crawl_phase'],
            lifted=t['crawl_lifted'], root_position=t['robot_position'],
            target_clearance=target[i, selected[i]].tolist(), target_fk_residual_m=residual[i].item())
            for i, t in enumerate(terminal)],
    }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry-report', type=Path, required=True)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.geometry_report, args.evaluation)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print({k:v for k,v in result.items() if k != 'per_environment'})
