"""下载固定版本公开GO2动作，生成20ms AMP相邻帧；不需要Isaac或MuJoCo。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import urllib.request
import numpy as np

COMMIT = '65cf1afd13e4792bce7b9def6f44372ecbb3cdf0'
SOURCE = 'datasets/go2_motion/go2_forward_0.4mps.txt'
SHA256 = '48818298b24a808554ce546f24e61c2b106171e433a96f3450d4d240c0eb9b5f'
URL = 'https://api.github.com/repos/haozhang04/wmp_go1/git/blobs/646eb37b48887e1e8de07369b2dbb9412ce9993c'


def convert(raw):
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError('Reference file checksum mismatch')
    motion = json.loads(raw)
    frames = np.asarray(motion['Frames'], dtype=np.float64)
    if frames.ndim != 2 or frames.shape[1] != 61 or not np.isfinite(frames).all():
        raise ValueError('Expected finite 61-column WMP motion')
    if abs(motion['FrameDuration'] - .02) > 1e-9:
        raise ValueError('Expected 20ms references; no implicit speed rescaling')
    # WMP原生Isaac顺序FL,FR,RL,RR；脚的局部xy正负额外验证，防止左右/前后互换。
    toes = frames[:, 19:31].reshape(-1, 4, 3)
    if not np.all(np.sign(toes[:, :, :2].mean(0)) == [[1,1],[1,-1],[-1,1],[-1,-1]]):
        raise ValueError('Foot-order check failed')
    state = np.concatenate((frames[:, 7:19], frames[:, 31:49]), axis=1)
    # 排除启动、停止和明显偏离前进的帧；必须原片中连续两帧都合格，不跨缺口/循环端点拼接。
    moving = (frames[:,31] >= .2) & (frames[:,31] <= .65) & (np.abs(frames[:,32]) < .15)
    keep = moving[:-1] & moving[1:]
    pairs = np.concatenate((state[:-1], state[1:]), axis=1)[keep]
    if len(pairs) < 32:
        raise ValueError('Insufficient forward references')
    return dict(format='climb_amp_pairs_v1', dt=.02,
        joint_order=[f'{leg}_{joint}_joint' for leg in ('FL','FR','RL','RR') for joint in ('hip','thigh','calf')],
        feature_order=['joint_position_12','body_linear_velocity_3','body_angular_velocity_3','joint_velocity_12'],
        source_url=f'https://github.com/haozhang04/wmp_go1/blob/{COMMIT}/{SOURCE}',
        source_sha256=SHA256, source_commit=COMMIT, original_frames=len(frames),
        retained_transition_indices=np.flatnonzero(keep).tolist(),
        limitations='Public bare-GO2 named clip; not GO2-PIPER demonstration; no contact-force labels; source recording pipeline not fully specified.',
        pairs=pairs.tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New external data directory')
    parser.add_argument('--source-file', type=Path, help='Optional already downloaded source, same SHA required')
    args = parser.parse_args()
    raw = args.source_file.read_bytes() if args.source_file else base64.b64decode(
        json.load(urllib.request.urlopen(URL, timeout=30))['content'])
    dataset = convert(raw)
    license_url = f'https://raw.githubusercontent.com/haozhang04/wmp_go1/{COMMIT}/LICENSE.txt'
    license_text = urllib.request.urlopen(license_url, timeout=30).read()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / Path(SOURCE).name).write_bytes(raw)
    (args.output / 'LICENSE.upstream.txt').write_bytes(license_text)
    path = args.output / 'amp_pairs.json'
    path.write_text(json.dumps(dataset, indent=2, allow_nan=False)+'\n')
    print(f'{path}\nTransitions: {len(dataset["pairs"])}\nSHA256: {hashlib.sha256(path.read_bytes()).hexdigest()}')

if __name__ == '__main__':
    main()
