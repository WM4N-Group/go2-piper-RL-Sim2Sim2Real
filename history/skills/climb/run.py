"""本目录独立的运行入口；默认准备计划，--execute 才运行物理。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent



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
    key = 'source_hashes' if 'source_hashes' in plan else 'source_sha256'
    verify_sources(bundle / 'train', plan, key)
    train = output / 'train'
    shutil.copytree(bundle / 'train', train,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs', 'logs'))
    return train, plan

def prepare(output, python, seed):
    bundle = ROOT / 'iy'
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isaac-python', type=Path, default=Path(sys.executable), help='默认使用当前Conda环境的Python')
    parser.add_argument('--output-dir', type=Path, required=True, help='新的输出目录，不能覆盖已有结果')
    parser.add_argument('--gpu', type=int, default=0)
    # 本技能使用原冻结批次的seed，不提供替换参数。
    parser.add_argument('--execute', action='store_true', help='实际运行；省略时只准备并校验计划')
    args = parser.parse_args()
    python = args.isaac_python.expanduser().resolve()
    if not python.is_file() or not os.access(python, os.X_OK):
        parser.error('--isaac-python must name an executable file')
    if args.gpu < 0:
        parser.error('--gpu must be nonnegative')
    output = args.output_dir.expanduser().resolve()
    if output.exists():
        parser.error('--output-dir must be new; previous outputs are never overwritten')
    # 仅校验本目录的文件；不依赖另一个技能的校验器或根目录清单。
    subprocess.run([sys.executable, str(ROOT / 'verify.py')], check=True)
    output.mkdir(parents=True)
    train, command, variables, scope = prepare(output, python, None)
    env = os.environ.copy()
    env.update(variables)
    env['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(train / 'source/LeggedManip_Lab'),
                          variables.get('PIPER_GEOMETRY_ROOT'), env.get('PYTHONPATH')]))
    env['PYTHONUNBUFFERED'] = '1'
    plan = {'skill': 'climb', 'cwd': str(train), 'command': command, 'scope': scope,
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
