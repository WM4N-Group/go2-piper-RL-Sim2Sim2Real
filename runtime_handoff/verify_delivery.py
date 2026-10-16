"""Verify the repository payload and frozen runtime inputs without importing Isaac."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify():
    checked = 0
    errors = []
    for line in (REPO / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        path = REPO / name
        if not path.is_file() or sha(path) != digest:
            errors.append(name)
        checked += 1
    for name, key in [('PUSH-v212', 'source_hashes'), ('CLIMB-iy', 'source_sha256')]:
        root = ROOT / name
        plan = json.loads((root / 'plan.json').read_text())
        for rel, digest in plan[key].items():
            p = root / 'train' / rel
            if not p.is_file() or sha(p) != digest:
                errors.append(str(p.relative_to(REPO)))
    for plan_path in (ROOT / 'development').glob('*/plan.json'):
        for rel, digest in json.loads(plan_path.read_text())['files'].items():
            p = plan_path.parent / rel
            if not p.is_file() or sha(p) != digest:
                errors.append(str(p.relative_to(REPO)))
    expected = {
        'PUSH-v212/model_255.pt': '4d1a4616928b4d06002285e870a1d6dd114e27b8cafcdd9a41dbdae1aceed419',
        'PUSH-v212/model_199.pt': 'b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721',
        'CLIMB-iy/stand_actor304.pt': 'd9673b2b49f5dce08d844a1de81a3a37e7f90e85d20b86489a5751b8aa2b1dee',
    }
    for rel, digest in expected.items():
        p = ROOT / rel
        if not p.is_file() or sha(p) != digest:
            errors.append(rel)
    nav = REPO / 'sim2real/go2-piper-low-level-policy-handoff/policies/nav/policy.pt'
    if sha(nav) != '72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8':
        errors.append('NAV policy')
    bank = ROOT / 'CLIMB-iy/stage-bank.json'
    if sha(bank) != json.loads((bank.parent / 'plan.json').read_text())['stage_bank_sha256']:
        errors.append('CLIMB bank')
    return {'ok': not errors, 'checked_repository_files': checked, 'errors': sorted(set(errors)),
            'scope': 'File integrity and frozen runtime contract only; no new physics or acceptance claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', action='store_true', help='Also report installed distribution versions')
    args = parser.parse_args()
    result = verify()
    if args.environment:
        versions = {}
        for name in ['isaacsim', 'isaaclab', 'isaaclab-rl', 'isaaclab-tasks', 'rsl-rl-lib',
                     'torch', 'numpy', 'scipy', 'gymnasium', 'mujoco', 'Pillow', 'imageio',
                     'imageio-ffmpeg', 'PyYAML']:
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = None
        result['installed_distributions'] = versions
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
