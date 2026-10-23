"""校验本目录文件；不导入Isaac，不运行物理。"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def verify():
    errors = []
    checked = 0
    for line in (ROOT / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        path = ROOT / name
        h = hashlib.sha256()
        if not path.is_file():
            errors.append(name)
            continue
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
        if h.hexdigest() != digest:
            errors.append(name)
        checked += 1
    return {'ok': not errors, 'checked_files': checked, 'errors': errors,
            'scope': 'Local file integrity only; no physics or deployment acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', action='store_true')
    args = parser.parse_args()
    result = verify()
    if args.environment:
        result['installed_distributions'] = {}
        for name in ['isaacsim', 'isaaclab', 'isaaclab-rl', 'rsl-rl-lib', 'torch', 'numpy', 'mujoco']:
            try:
                result['installed_distributions'][name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                result['installed_distributions'][name] = None
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
