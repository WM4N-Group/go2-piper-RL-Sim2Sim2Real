"""Prepare or execute a versioned Isaac skill replay in a new output directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
NAV = REPO / 'sim2real/go2-piper-low-level-policy-handoff/policies/nav/policy.pt'
NAV_SHA = '72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path, expected):
    if not path.is_file() or sha256(path) != expected:
        raise ValueError(f'Missing or mismatched file: {path}')


def replace_flag(command, flag, value):
    command[command.index(flag) + 1] = str(value)


def verify_sources(folder, plan, key):
    for relative, expected in plan[key].items():
        require_hash(folder / relative, expected)


def copy_train(bundle, output):
    plan = json.loads((bundle / 'plan.json').read_text())
    key = 'source_hashes' if bundle.name == 'PUSH-v212' else 'source_sha256'
    verify_sources(bundle / 'train', plan, key)
    train = output / 'train'
    shutil.copytree(bundle / 'train', train,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs', 'logs'))
    return train, plan


def push_variables(train):
    bundle = ROOT / 'PUSH-v212'
    return {'PIPER_HANDOFF_ROOT': str(bundle),
            'PIPER_GEOMETRY_ROOT': str(bundle / 'geometry/mujoco'),
            'PIPER_LEG_CHECKPOINT': str(bundle / 'model_199.pt'),
            'PIPER_PUSH_CHECKPOINT': str(bundle / 'model_255.pt'),
            'PIPER_SOURCE_ROOT': str(train)}


def prepare_push(output, python):
    bundle = ROOT / 'PUSH-v212'
    train, plan = copy_train(bundle, output)
    require_hash(bundle / 'model_255.pt', plan['variants'][0]['checkpoint_sha256'])
    require_hash(bundle / 'model_199.pt',
                 'b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721')
    video_plan = json.loads((bundle / 'video-development-seed3701-8env-48s-plan.json').read_text())
    command = list(video_plan['command'])
    command[:2] = [str(python), str(train / 'scripts/evaluate_residual_push.py')]
    for flag, path in [('--checkpoint', bundle / 'model_255.pt'),
                       ('--push-geometry-root', bundle / 'geometry/mujoco'),
                       ('--output-json', output / 'report.json'),
                       ('--video-path', output / 'video.mp4')]:
        replace_flag(command, flag, path)
    if '--enable_cameras' not in command:
        command.append('--enable_cameras')
    return train, command, push_variables(train), video_plan['scope']


def prepare_climb(output, python):
    bundle = ROOT / 'CLIMB-iy'
    train, plan = copy_train(bundle, output)
    require_hash(bundle / 'stage-bank.json', plan['stage_bank_sha256'])
    require_hash(bundle / 'stand_actor304.pt', plan['actor_sha256'])
    job, = json.loads((bundle / 'jobs.json').read_text())
    original = list(job['command'])
    script_index = original.index('scripts/evaluate_box_skills.py')
    command = [str(python), str(train / original[script_index]), *original[script_index + 1:]]
    for flag, path in [('--climb-stage-bank', bundle / 'stage-bank.json'),
                       ('--actor-policy', bundle / 'stand_actor304.pt'),
                       ('--output-json', output / 'report.json'),
                       ('--video-path', output / 'video.mp4')]:
        replace_flag(command, flag, path)
    command.append('--enable_cameras')
    return train, command, {'PIPER_SOURCE_ROOT': str(train)}, plan['scope']


def prepare_development(skill, output, python, seed):
    require_hash(NAV, NAV_SHA)
    name = {'nav': 'nav-native-entry-video-v038',
            'nav-climb-nav': 'transition-nav-climb-v067',
            'nav-push-nav': 'transition-arm-entry-v317'}[skill]
    controller = ROOT / 'development' / name
    control_plan = json.loads((controller / 'plan.json').read_text())
    verify_sources(controller, control_plan, 'files')
    bundle = ROOT / ('PUSH-v212' if skill == 'nav-push-nav' else 'CLIMB-iy')
    train, plan = copy_train(bundle, output)
    # CLIMB configuration extraction reads the matching plan/jobs beside train.
    for f in ['plan.json', 'jobs.json']:
        if (bundle / f).exists():
            shutil.copy2(bundle / f, output / f)
    command = [str(python), str(controller / 'probe.py'), '--source', str(train),
               '--policy' if skill == 'nav' else '--nav-actor', str(NAV),
               '--output', str(output / 'result'), '--seed', str(seed), '--headless',
               '--device', 'cuda:0']
    variables = {'PIPER_SOURCE_ROOT': str(train)}
    if skill == 'nav':
        command += ['--ee-x', '.45', '--ee-z', '.45', '--speed', '.25',
                    '--support-min-s', '3', '--body-damping', '5', '--blend-s', '1',
                    '--posture-template', str(controller / 'nav-posture-template.json'),
                    '--seconds', '60', '--enable_cameras']
        scope = 'Independent current-limit NAV entry and 10 s exact native18 walking; not goal or chain acceptance.'
    elif skill == 'nav-climb-nav':
        command += ['--seconds', '420']
        scope = 'Preserved v067 development baseline. Altered NAV contract and wrist failure remain; not a stable SDK.'
    else:
        command += ['--seconds', '96']
        variables.update(push_variables(train))
        require_hash(bundle / 'model_255.pt', plan['variants'][0]['checkpoint_sha256'])
        scope = 'Preserved v317 continuous development baseline; not held-out, sim2sim or hardware acceptance.'
    return train, command, variables, scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill', choices=['nav', 'push', 'climb', 'nav-climb-nav', 'nav-push-nav'])
    parser.add_argument('--isaac-python', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--seed', type=int, default=None,
                        help='Development NAV/chain seed; standalone PUSH/CLIMB keep their recorded batch seeds.')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    python = args.isaac_python.expanduser().resolve()
    if not python.is_file() or not os.access(python, os.X_OK):
        parser.error('--isaac-python must name an executable file')
    if args.gpu < 0:
        parser.error('--gpu must be nonnegative')
    if args.seed is not None and args.skill in ['push', 'climb']:
        parser.error('Standalone PUSH/CLIMB use the recorded batch seeds; --seed is only for NAV/development chains')
    output = args.output_dir.expanduser().resolve()
    if output.exists():
        parser.error('--output-dir must be new; previous outputs are never overwritten')
    # Verify the delivered files before producing a runnable copy.
    subprocess.run([sys.executable, str(ROOT / 'verify_delivery.py')], check=True)
    output.mkdir(parents=True)
    if args.skill == 'push':
        train, command, variables, scope = prepare_push(output, python)
    elif args.skill == 'climb':
        train, command, variables, scope = prepare_climb(output, python)
    else:
        seed = args.seed if args.seed is not None else (3703 if args.skill == 'nav' else 3701)
        train, command, variables, scope = prepare_development(args.skill, output, python, seed)
    env = os.environ.copy()
    env.update(variables)
    env['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(train / 'source/LeggedManip_Lab'),
                            variables.get('PIPER_GEOMETRY_ROOT'), env.get('PYTHONPATH')]))
    env['PYTHONUNBUFFERED'] = '1'
    plan = {'skill': args.skill, 'cwd': str(train), 'command': command, 'scope': scope,
            'variables': {k: env[k] for k in [*variables, 'CUDA_VISIBLE_DEVICES', 'PYTHONPATH']},
            'executed': args.execute, 'bundle_checksum_sha256': sha256(ROOT / 'SHA256SUMS')}
    (output / 'run-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(json.dumps({'run_plan': str(output / 'run-plan.json'), 'command': command}, indent=2), flush=True)
    if args.execute:
        with (output / 'run.log').open('x') as log:
            result = subprocess.run(command, cwd=train, env=env, stdout=log, stderr=subprocess.STDOUT)
        (output / 'exit-status.json').write_text(json.dumps({'returncode': result.returncode}) + '\n')
        return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
