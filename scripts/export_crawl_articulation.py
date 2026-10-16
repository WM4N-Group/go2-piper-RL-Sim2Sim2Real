"""Remote Isaac initialized-model snapshot, without executing a skill episode."""
import argparse
import hashlib
import json
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--num-envs', type=int, default=32)
parser.add_argument('--seed', type=int, default=513)
parser.add_argument('--output', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output.exists() or args.num_envs < 1:
    parser.error('Require a new output path and positive environment count')
launcher = AppLauncher(args)

import gymnasium as gym
import LeggedManip_Lab.tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab.utils.io import dump_yaml

try:
    cfg = load_cfg_from_registry('GO2-PIPER-Box-Climb-Crawl-Play', 'env_cfg_entry_point')
    cfg.scene.num_envs = args.num_envs
    cfg.seed = args.seed
    cfg.sim.device = args.device
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dump_yaml(str(args.output.with_suffix('.env.yaml')), cfg)
    env = gym.make('GO2-PIPER-Box-Climb-Crawl-Play', cfg=cfg)
    try:
        env.reset()
        base = env.unwrapped; robot = base.scene['robot']
        origin = base.scene.env_origins
        usd_path = Path(cfg.scene.robot.spawn.usd_path)
        result = dict(scope='Initialized model snapshot, zero skill steps, NOT an episode evaluation',
            seed=args.seed, num_envs=args.num_envs, joint_names=robot.joint_names,
            body_names=robot.body_names, usd_path=str(usd_path),
            usd_sha256=hashlib.sha256(usd_path.read_bytes()).hexdigest(),
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            actual_masses=robot.root_physx_view.get_masses().tolist(),
            default_masses=robot.data.default_mass.tolist(),
            local_com_transforms_xyzw=robot.root_physx_view.get_coms().tolist(),
            joint_position=robot.data.joint_pos.tolist(),
            joint_effort_limits=robot.data.joint_effort_limits.tolist(),
            root_position=(robot.data.root_pos_w-origin).tolist(),
            root_quaternion_wxyz=robot.data.root_quat_w.tolist(),
            body_position=(robot.data.body_pos_w-origin[:,None]).tolist(),
            body_quaternion_wxyz=robot.data.body_quat_w.tolist(),
            body_com_position=(robot.data.body_com_pos_w-origin[:,None]).tolist())
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        print('MODEL_SNAPSHOT', args.output, 'bodies', len(robot.body_names), flush=True)
    finally:
        env.close()
finally:
    launcher.app.close()
