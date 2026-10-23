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
REPO = ROOT.parents[1]

NAV = REPO / 'skills/nav/policy.pt'
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
    key = 'source_hashes' if 'source_hashes' in plan else 'source_sha256'
    verify_sources(bundle / 'train', plan, key)
    train = output / 'train'
    shutil.copytree(bundle / 'train', train,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs', 'logs'))
    return train, plan

def prepare(output, python, seed):
    require_hash(NAV, NAV_SHA)
    controller = ROOT / 'v067'
    verify_sources(controller, json.loads((controller / 'plan.json').read_text()), 'files')
    bundle = REPO / 'skills/climb/iy'
    train, plan = copy_train(bundle, output)
    for name in ['plan.json', 'jobs.json']:
        if (bundle / name).exists():
            shutil.copy2(bundle / name, output / name)
    command = [str(python), str(controller / 'probe.py'), '--source', str(train),
               '--nav-actor', str(NAV), '--output', str(output / 'result'), '--seed', str(seed),
               '--headless', '--device', 'cuda:0', '--seconds', '420']
    variables = {'PIPER_SOURCE_ROOT': str(train)}
    return train, command, variables, 'Preserved v067 development baseline. Altered NAV contract and wrist failure remain; not a stable SDK.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isaac-python', type=Path, default=Path(sys.executable), help='默认使用当前Conda环境的Python')
    parser.add_argument('--output-dir', type=Path, required=True, help='新的输出目录，不能覆盖已有结果')
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--seed', type=int, default=3701)
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
    train, command, variables, scope = prepare(output, python, args.seed)
    env = os.environ.copy()
    env.update(variables)
    env['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(train / 'source/LeggedManip_Lab'),
                          variables.get('PIPER_GEOMETRY_ROOT'), env.get('PYTHONPATH')]))
    env['PYTHONUNBUFFERED'] = '1'
    plan = {'skill': 'nav-climb-nav', 'cwd': str(train), 'command': command, 'scope': scope,
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
