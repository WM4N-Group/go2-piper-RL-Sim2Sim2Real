"""CLIMB 本地版本管理：源码进 Git，训练产物独立保留。"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ('V1', 'V2', 'V21', 'V22', 'V3')


def git(*args, capture=True):
    return subprocess.run(['git', '-C', str(ROOT), *args], check=True,
                          text=True, capture_output=capture).stdout


def running_processes():
    """切换不会改变已导入的代码，但录像子进程可能读到新版本，因此运行中拒绝切换。"""
    result = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = (proc / 'cmdline').read_bytes().split(b'\0')
            cwd = (proc / 'cwd').resolve()
            for arg in args:
                value = arg.decode(errors='replace')
                if value.endswith('.py'):
                    candidate = Path(value)
                    candidate = candidate if candidate.is_absolute() else cwd / candidate
                    if candidate.resolve() in [ROOT / 'scripts' / f'{name}.py'
                                               for name in ('train', 'play', 'export_policy', 'migrate_curriculum')]:
                        result.append(proc.name)
        except (OSError, PermissionError):
            continue
    return result


def switch(version):
    git('check-ref-format', f'refs/tags/{version}')
    if git('status', '--porcelain').strip():
        raise SystemExit('有尚未保存的源码修改。先运行 save 保存，再切换；不会覆盖你的修改。')
    pids = running_processes()
    if pids:
        raise SystemExit('训练或回放仍在运行，暂不切换：PID ' + ', '.join(pids))
    git('rev-parse', '--verify', f'refs/tags/{version}')
    # 不使用强制覆盖，Git 自身也会拒绝覆盖未跟踪的同名文件。
    branch = f'codex/{version}-{datetime.now():%Y%m%d-%H%M%S-%f}'
    git('switch', '-c', branch, f'refs/tags/{version}', capture=False)
    print(f'已切换到 {version}；权重和录像保持在 outputs/。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    sub.add_parser('status')
    sw = sub.add_parser('switch'); sw.add_argument('version', help='V1 / V2 / V21 / V22 / V3 或已保存的标签')
    save = sub.add_parser('save')
    save.add_argument('name', help='新的不可覆盖版本名，例如 V3-before-reward-change')
    save.add_argument('--message', required=True, help='说明这次改动和验证结果')
    args = parser.parse_args()
    if args.action == 'switch':
        switch(args.version)
    elif args.action == 'save':
        git('check-ref-format', f'refs/tags/{args.name}')
        exists = subprocess.run(['git', '-C', str(ROOT), 'show-ref', '--verify', '--quiet',
                                 f'refs/tags/{args.name}']).returncode == 0
        if exists:
            raise SystemExit('该版本名已存在，不允许覆盖。请用新的名字。')
        git('add', '-A', capture=False)
        if git('diff', '--cached', '--name-only').strip():
            git('commit', '-m', args.message, capture=False)
        git('tag', '-a', args.name, '-m', args.message, capture=False)
        print('已保存源码版本：' + args.name + '；outputs 不进入 Git。')
    elif args.action == 'list':
        print(git('tag', '--list', 'V*', '--sort=version:refname'), end='')
    else:
        print('生效配置：', json.loads((ROOT/'VERSION.json').read_text()))
        print(git('status', '--short', '--branch'), end='')


if __name__ == '__main__':
    main()
