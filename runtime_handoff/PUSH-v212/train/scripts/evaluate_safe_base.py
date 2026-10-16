"""Evaluate a SAFE_BASE checkpoint over a fixed, failure-free hold interval."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", type=Path, required=True)
parser.add_argument("--output-json", type=Path, required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--num-envs", type=int, default=32)
parser.add_argument("--duration-s", type=float, default=12.0)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.num_envs < 1 or not math.isfinite(args.duration_s) or args.duration_s <= 0:
    parser.error("Evaluation size and duration must be positive and finite")
if not args.checkpoint.is_file() or args.output_json.exists():
    parser.error("Checkpoint must exist and output must not exist")
launcher = AppLauncher(args)

import gymnasium as gym
import torch

import isaaclab_tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import LeggedManip_Lab.tasks


def main():
    task = "GO2-PIPER-Box-Push-Safe-Base-Play"
    config = load_cfg_from_registry(task, "env_cfg_entry_point")
    config.scene.num_envs = args.num_envs
    config.seed = args.seed
    config.sim.device = args.device
    config.episode_length_s = args.duration_s
    config.observations.policy.enable_corruption = False
    agent_config = load_cfg_from_registry(task, "rsl_rl_cfg_entry_point")
    agent_config.device = args.device
    agent_config.seed = args.seed
    env = RslRlVecEnvWrapper(gym.make(task, cfg=config), clip_actions=agent_config.clip_actions)
    base = env.unwrapped
    robot = base.scene["robot"]
    checkpoint = torch.load(args.checkpoint, map_location=args.device, weights_only=False)
    load_actor = runpy.run_path(str(Path(__file__).resolve().parent / "rsl_rl/initialization.py"))["actor_from_state_dict"]
    policy = load_actor(checkpoint["actor_state_dict"], device=args.device)
    observation = env.get_observations()
    groups = agent_config.obs_groups["actor"]
    active = torch.ones(args.num_envs, dtype=torch.bool, device=args.device)
    min_height = torch.full((args.num_envs,), torch.inf, device=args.device)
    max_tilt = torch.zeros(args.num_envs, device=args.device)
    max_speed = torch.zeros(args.num_envs, device=args.device)
    max_angular_speed = torch.zeros(args.num_envs, device=args.device)
    windows = ((0.0, 2.0), (2.0, max(2.0, args.duration_s - 2.0)), (max(2.0, args.duration_s - 2.0), args.duration_s))
    window_speed_max = torch.zeros((len(windows), args.num_envs), device=args.device)
    window_angular_max = torch.zeros_like(window_speed_max)
    window_speed_squares = torch.zeros_like(window_speed_max)
    window_angular_squares = torch.zeros_like(window_speed_max)
    window_samples = torch.zeros_like(window_speed_max)
    min_clearance = torch.full((args.num_envs,), torch.inf, device=args.device)
    reasons = {name: 0 for name in base.termination_manager.active_terms}
    terminal = []
    arm_ids = robot.find_bodies("link[2-6]|end_effector")[0]
    protected_ids = robot.find_bodies("base|.*_(hip|thigh|calf|foot)")[0]
    if not arm_ids or not protected_ids:
        raise ValueError("SAFE_BASE clearance bodies are missing")
    steps = math.ceil(args.duration_s / base.step_dt) + 2
    with torch.inference_mode():
        for step in range(steps):
            position = robot.data.root_pos_w - base.scene.env_origins
            tilt = torch.acos((-robot.data.projected_gravity_b[:, 2]).clamp(-1.0, 1.0))
            speed = torch.linalg.vector_norm(robot.data.root_lin_vel_w, dim=1)
            angular_speed = torch.linalg.vector_norm(robot.data.root_ang_vel_w, dim=1)
            clearance = torch.cdist(robot.data.body_pos_w[:, arm_ids], robot.data.body_pos_w[:, protected_ids]).amin(dim=(1, 2))
            min_height[active] = torch.minimum(min_height[active], position[active, 2])
            max_tilt[active] = torch.maximum(max_tilt[active], tilt[active])
            max_speed[active] = torch.maximum(max_speed[active], speed[active])
            max_angular_speed[active] = torch.maximum(max_angular_speed[active], angular_speed[active])
            for index, (start, end) in enumerate(windows):
                if start <= step * base.step_dt < end:
                    window_speed_max[index, active] = torch.maximum(window_speed_max[index, active], speed[active])
                    window_angular_max[index, active] = torch.maximum(window_angular_max[index, active], angular_speed[active])
                    window_speed_squares[index, active] += speed[active].square()
                    window_angular_squares[index, active] += angular_speed[active].square()
                    window_samples[index, active] += 1
            min_clearance[active] = torch.minimum(min_clearance[active], clearance[active])
            actions = policy(torch.cat([observation[name] for name in groups], dim=-1))
            observation, _rewards, dones, _extras = env.step(actions)
            finished = active & dones.bool()
            if finished.any():
                flags = {name: base.termination_manager.get_term(name) for name in reasons}
                for name, flag in flags.items():
                    reasons[name] += int((finished & flag).sum().item())
                for env_id in finished.nonzero(as_tuple=False).flatten().tolist():
                    failed = [name for name, flag in flags.items() if name != "time_out" and bool(flag[env_id])]
                    terminal.append({"env_id": env_id, "elapsed_seconds": (step + 1) * base.step_dt,
                                     "time_out": bool(flags["time_out"][env_id]), "failures": failed})
                active[finished] = False
            if not active.any():
                break
    result = {
        "task": task, "seed": args.seed, "num_envs": args.num_envs, "duration_s": args.duration_s,
        "step_dt": base.step_dt, "executed_steps": step + 1,
        "completed": len(terminal), "passed": sum(item["time_out"] and not item["failures"] for item in terminal),
        "termination_reasons": reasons, "terminal": sorted(terminal, key=lambda item: item["env_id"]),
        "min_base_height_m": min_height.tolist(), "max_tilt_rad": max_tilt.tolist(),
        "max_base_speed_m_s": max_speed.tolist(), "max_base_angular_speed_rad_s": max_angular_speed.tolist(),
        "velocity_windows": [
            {"start_s": start, "end_s": end, "samples_per_env": window_samples[index].tolist(),
             "max_base_speed_m_s": window_speed_max[index].tolist(),
             "rms_base_speed_m_s": (window_speed_squares[index] / window_samples[index].clamp_min(1)).sqrt().tolist(),
             "max_base_angular_speed_rad_s": window_angular_max[index].tolist(),
             "rms_base_angular_speed_rad_s": (window_angular_squares[index] / window_samples[index].clamp_min(1)).sqrt().tolist()}
            for index, (start, end) in enumerate(windows) if start < end
        ],
        "min_arm_body_center_distance_m": min_clearance.tolist(), "arm_body_threshold_m": 0.08,
        "checkpoint": str(args.checkpoint), "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
        "evaluation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "config_episode_length_s": config.episode_length_s,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print("SAFE_BASE_EVALUATION=" + json.dumps({key: result[key] for key in ("seed", "completed", "passed", "termination_reasons")}), flush=True)
    env.close()


if __name__ == "__main__":
    main()
    launcher.app.close()