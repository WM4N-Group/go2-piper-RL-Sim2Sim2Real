"""在主仓库内保存与恢复 CLIMB 源码；模型、录像与其他项目文件不参与切换。"""
import argparse
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BUNDLE = ROOT / 'versions/source-history.bundle'
SCOPE = ['climb_skill', ':(exclude)climb_skill/outputs']
# These publication tools must remain usable after restoring historical training code.
PERSISTENT = {'scripts/manage.py', 'scripts/env.sh', '.gitignore', '.gitattributes',
              'README.md', 'versions/source-history.bundle', 'versions/publication.json'}


def git(*args, capture=True):
    return subprocess.run(['git', '-C', str(REPO), *args], check=True,
                          text=True, capture_output=capture).stdout


def running_processes():
    result = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            cwd = (proc / 'cwd').resolve()
            for arg in (proc / 'cmdline').read_bytes().split(b'\0'):
                value = arg.decode(errors='replace')
                if not value.endswith('.py'):
                    continue
                p = Path(value)
                p = p if p.is_absolute() else cwd / p
                if p.resolve() in [ROOT / 'scripts' / (n + '.py') for n in
                                   ('train', 'play', 'export_policy', 'migrate_curriculum')]:
                    result.append(proc.name)
        except OSError:
            continue
    return sorted(set(result))


def ensure_history():
    git('fetch', '--no-tags', str(BUNDLE), 'refs/tags/*:refs/climb-history/*')


def resolve(version):
    git('check-ref-format', 'refs/tags/climb/' + version)
    saved = 'refs/tags/climb/' + version
    if subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--verify', '--quiet', saved],
                      stdout=subprocess.DEVNULL).returncode == 0:
        return saved, 'climb_skill/'
    ensure_history()
    ref = 'refs/climb-history/' + version
    git('rev-parse', '--verify', ref)
    return ref, ''


def source_status():
    return git('status', '--porcelain', '--', *SCOPE)


def keep(name):
    return name in PERSISTENT or name.startswith(('outputs/', 'data/'))


def switch(version):
    if source_status().strip():
        raise SystemExit('Climb 源码有未保存修改。请先 save；不会覆盖现有修改。')
    pids = running_processes()
    if pids:
        raise SystemExit('训练/回放仍在运行，不能切换：PID ' + ', '.join(pids))
    ref, prefix = resolve(version)
    args = ['git', '-C', str(REPO), 'archive', ref]
    if prefix:
        args.append(prefix)
    raw = subprocess.check_output(args)
    payload = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for member in archive.getmembers():
            name = member.name[len(prefix):] if prefix else member.name
            if not name or member.isdir() or keep(name):
                continue
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or not member.isfile():
                raise SystemExit('不支持的历史路径：' + name)
            payload[name] = archive.extractfile(member).read()
    tracked = {p[len('climb_skill/'):] for p in
               git('ls-files', '--', 'climb_skill').splitlines()}
    # Never overwrite an untracked user source file.
    for name in payload:
        if (ROOT / name).exists() and name not in tracked:
            raise SystemExit('未跟踪文件与历史版本冲突：' + name)
    for name in tracked:
        if not keep(name) and name not in payload:
            (ROOT / name).unlink(missing_ok=True)
    for name, data in payload.items():
        p = ROOT / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    print('已恢复 ' + version + ' 的训练源码与配置；outputs 保持不变。')
    print('这是主仓库中的源码修改；确认后用 save 保存，再进行下一次切换。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('list')
    sub.add_parser('status')
    sw = sub.add_parser('switch')
    sw.add_argument('version')
    save = sub.add_parser('save')
    save.add_argument('name')
    save.add_argument('--message', required=True)
    args = parser.parse_args()
    if args.action == 'switch':
        switch(args.version)
    elif args.action == 'save':
        tag = 'climb/' + args.name
        git('check-ref-format', 'refs/tags/' + tag)
        if args.name in ('V1','V2','V21','V22','V3') or subprocess.run(
                ['git', '-C', str(REPO), 'show-ref', '--verify', '--quiet',
                 'refs/tags/' + tag]).returncode == 0:
            raise SystemExit('版本名已存在，请使用新名字。')
        if git('diff', '--cached', '--name-only').strip():
            raise SystemExit('主仓库暂存区非空，请先处理，防止误提交其他改动。')
        paths = [p for p in git('ls-files', '-co', '--exclude-standard', '--', 'climb_skill').splitlines()
                 if not p.startswith('climb_skill/outputs/')]
        if paths:
            git('add', '-A', '--', *sorted(set(paths)), capture=False)
        if git('diff', '--cached', '--name-only').strip():
            git('commit', '-m', args.message, capture=False)
        git('tag', '-a', tag, '-m', args.message, capture=False)
        print('已保存 ' + tag + '；没有提交 outputs 的变化。')
    elif args.action == 'list':
        print('内置历史版本：V1 V2 V21 V22 V3（随 source-history.bundle 一起交付）')
        print(git('tag', '--list', 'climb/*'), end='')
    else:
        print('生效配置：', json.loads((ROOT / 'VERSION.json').read_text()))
        print(git('status', '--short', '--branch', '--', *SCOPE), end='')


if __name__ == '__main__':
    main()
