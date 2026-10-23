"""本目录独立的运行入口；默认准备计划，--execute 才运行物理。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent

def push_variables(train):
    bundle = ROOT / 'v212'
    return {'PIPER_HANDOFF_ROOT': str(bundle),
            'PIPER_GEOMETRY_ROOT': str(bundle / 'geometry/mujoco'),
            'PIPER_LEG_CHECKPOINT': str(bundle / 'model_199.pt'),
            'PIPER_PUSH_CHECKPOINT': str(bundle / 'model_255.pt'),
            'PIPER_SOURCE_ROOT': str(train)}

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
    bundle = ROOT / 'v212'
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isaac-python', type=Path, default=Path(sys.executable), help='默认使用当前Conda环境的Python')
    parser.add_argument('--output-dir', type=Path, required=True, help='新的输出目录，不能覆盖已有结果')
    parser.add_argument('--gpu', type=int, default=0)
    # 本技能使用原冻结批次的seed，不提供替换参数。
    parser.add_argument('--num-envs', type=int, default=8, help='并行数；单个演示可用1，结果不得与原8环境批次混用')
    parser.add_argument('--video-fps', type=int, choices=[5, 10, 25], default=10, help='录像渲染频率；物理和控制频率不变')
    parser.add_argument('--no-video', action='store_true', help='不启用摄像头，用于较快物理验证')
    parser.add_argument('--start-backoff', type=float, default=0.08, help='承重初始化起点后移米数；默认8cm给原关节入场路径留空间')
    parser.add_argument('--startup-only', action='store_true', help='仅验证初始化落稳，不运行推箱')
    parser.add_argument('--original-start', action='store_true', help='关闭启动落稳适配，运行原版初始化')
    parser.add_argument('--execute', action='store_true', help='实际运行；省略时只准备并校验计划')
    args = parser.parse_args()
    python = args.isaac_python.expanduser().resolve()
    if not python.is_file() or not os.access(python, os.X_OK):
        parser.error('--isaac-python must name an executable file')
    if not 0.0 <= args.start_backoff <= 0.15:
        parser.error('--start-backoff must be in [0, 0.15] metres')
    if args.startup_only and args.original_start:
        parser.error('--startup-only requires startup adapter')
    if args.num_envs < 1:
        parser.error('--num-envs must be positive')
    if args.gpu < 0:
        parser.error('--gpu must be nonnegative')
    output = args.output_dir.expanduser().resolve()
    if output.exists():
        parser.error('--output-dir must be new; previous outputs are never overwritten')
    # 仅校验本目录的文件；不依赖另一个技能的校验器或根目录清单。
    subprocess.run([sys.executable, str(ROOT / 'verify.py')], check=True)
    output.mkdir(parents=True)
    train, command, variables, scope = prepare(output, python, None)
    replace_flag(command, '--num_envs', args.num_envs)
    from startup import patch_evaluator, patch_geometry
    shutil.copy2(ROOT / 'startup.py', train / 'scripts/startup.py')
    patch_geometry(train)
    patch_evaluator(train / 'scripts/evaluate_residual_push.py', args.video_fps, not args.original_start, args.startup_only, args.start_backoff)
    if args.no_video or args.startup_only:
        index = command.index('--video-path')
        del command[index:index+2]
        command.remove('--enable_cameras')
    env = os.environ.copy()
    env.update(variables)
    env['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(train / 'source/LeggedManip_Lab'),
                          variables.get('PIPER_GEOMETRY_ROOT'), env.get('PYTHONPATH')]))
    env['PYTHONUNBUFFERED'] = '1'
    plan = {'skill': 'push', 'cwd': str(train), 'command': command, 'scope': scope,
            'variables': {k: env[k] for k in [*variables, 'CUDA_VISIBLE_DEVICES', 'PYTHONPATH']},
            'executed': args.execute, 'startup_settling': not args.original_start, 'video_fps': None if args.no_video else args.video_fps, 'candidate': True, 'entry': 'original_joint_waypoints', 'start_backoff_m': 0.0 if args.original_start else args.start_backoff, 'num_envs': args.num_envs, 'bundle_checksum_sha256': sha256(ROOT / 'SHA256SUMS')}
    (output / 'run-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(json.dumps({'run_plan': str(output / 'run-plan.json'), 'command': command}, indent=2), flush=True)
    if args.execute:
        began = time.perf_counter()
        with (output / 'run.log').open('x') as log:
            result = subprocess.run(command, cwd=train, env=env, stdout=log, stderr=subprocess.STDOUT)
        (output / 'exit-status.json').write_text(json.dumps({'returncode': result.returncode, 'wall_seconds': time.perf_counter() - began}) + '\n')
        return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
