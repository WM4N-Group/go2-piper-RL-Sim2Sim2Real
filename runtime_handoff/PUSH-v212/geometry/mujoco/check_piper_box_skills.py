"""Evaluate PIPER PUSH/CLIMB candidates with explicit physical provenance."""

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import torch
import mujoco
import scipy

from check_box_push_policy import run_episode as run_push_episode
from check_piper_startup import sha256
from reconfigurable_navigation.locomotion_runtime import projected_gravity
from reconfigurable_navigation.piper_box_runtime import DEPLOY, ROOT, make_episode
from reconfigurable_navigation.piper_robot_profile import COLLISION_PROFILE_PATH, PROFILE_PATH


def run_climb(runtime, seed, height):
    model, data = runtime.model, runtime.data
    feet = [model.geom(name).id for name in ("FL", "FR", "RL", "RR")]
    floor = model.geom("floor").id
    box = model.geom("support_box").id
    goal = data.geom_xpos[box, :2].copy()
    stable_steps = low_steps = max_supported = 0
    reason = "timeout"
    trace = []
    for step in range(round(12 / runtime.control_dt)):
        position = data.xpos[runtime.base_id]
        rotation = data.xmat[runtime.base_id].reshape(3, 3)
        yaw = np.arctan2(rotation[1, 0], rotation[0, 0])
        delta = goal - position[:2]
        relative = np.array([[np.cos(yaw), np.sin(yaw)], [-np.sin(yaw), np.cos(yaw)]]) @ delta
        velocity = np.array([np.clip(0.8*relative[0], -0.15, 0.3), np.clip(0.8*relative[1], -0.12, 0.12), 0])
        if np.linalg.norm(delta) < 0.1:
            velocity.fill(0)
        runtime.step(velocity)
        support = runtime.support_contacts(feet, {box})
        surfaces = runtime.support_contacts(feet, {box, floor})
        max_supported = max(max_supported, len(support))
        position = data.xpos[runtime.base_id]
        gravity = projected_gravity(data.qpos[3:7])
        clearance = position[2] - min(surfaces.values(), default=0)
        low_steps = low_steps+1 if data.time >= 0.4 and clearance < 0.18 else 0
        if step % 25 == 0:
            trace.append({"time": float(data.time), "position": position.tolist(), "supported_feet": len(support)})
        if runtime.base_contacts_terrain():
            reason = "base_contact"
        elif gravity[2] > -np.cos(0.9):
            reason = "bad_orientation"
        elif low_steps * runtime.control_dt >= 0.2:
            reason = "low_posture"
        else:
            feet_positions = data.geom_xpos[feet]
            on_top = np.all(np.abs(feet_positions[:, :2] - goal) < 0.56) and np.all(np.abs(feet_positions[:, 2] - (height + 0.022)) < 0.04)
            stable = len(support) == 4 and on_top and np.linalg.norm(position[:2] - goal) < 0.2 and np.linalg.norm(data.qvel[:3]) < 0.15 and np.linalg.norm(data.qvel[3:6]) < 0.4 and gravity[2] < -0.94
            stable_steps = stable_steps+1 if stable else 0
            if stable_steps * runtime.control_dt >= 1.0:
                reason = "box_settled"
        if reason != "timeout":
            break
    return {"seed": seed, "succeeded": reason == "box_settled", "reason": reason, "elapsed": float(data.time), "max_supported_feet": max_supported, "trace": trace}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=("push", "climb"), required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--height", type=float, default=0.2)
    parser.add_argument("--push-ik-mode", choices=("position", "pose"), default="position")
    parser.add_argument("--native-collisions", action="store_true")
    parser.add_argument("--velocity-mode", choices=("legacy", "coupled", "coupled-bounds"), default="legacy")
    parser.add_argument("--constraint-substeps", type=int, choices=(1, 2), default=1)
    parser.add_argument("--contact-time-constant", type=float)
    parser.add_argument("--contact-damping-ratio", type=float)
    parser.add_argument("--contact-impedance", type=float)
    parser.add_argument("--contact-width", type=float)
    parser.add_argument("--contact-margin", type=float, default=0.0)
    parser.add_argument("--push-height-offset", type=float, default=0.0)
    parser.add_argument("--push-hand-pitch", type=float, default=0.8)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.seed_offset < 0 or args.output_json.exists():
        parser.error("Require positive seeds, nonnegative offset and a new output")
    if args.contact_time_constant is not None and (not np.isfinite(args.contact_time_constant) or args.contact_time_constant < 0.01):
        parser.error("Contact time constant must be finite and at least 0.01 s")
    if args.contact_damping_ratio is not None and (not np.isfinite(args.contact_damping_ratio) or args.contact_damping_ratio <= 0.0):
        parser.error("Contact damping ratio must be positive and finite")
    if args.contact_impedance is not None and (not np.isfinite(args.contact_impedance) or not 0.0 < args.contact_impedance < 0.95):
        parser.error("Contact impedance must be between 0 and 0.95")
    if args.contact_width is not None and (not np.isfinite(args.contact_width) or not 0.0 < args.contact_width <= 0.05):
        parser.error("Contact width must be between 0 and 0.05 m")
    if not np.isfinite(args.contact_margin) or not 0.0 <= args.contact_margin <= 0.01:
        parser.error("Contact margin must be between 0 and 0.01 m")
    if not np.isfinite(args.push_height_offset) or not -0.03 <= args.push_height_offset <= 0.03:
        parser.error("PUSH height offset must be between -0.03 and 0.03 m")
    if not np.isfinite(args.push_hand_pitch) or not 0.0 <= args.push_hand_pitch <= 1.2:
        parser.error("PUSH hand pitch must be between 0 and 1.2 rad")
    torch.set_num_threads(1)
    results = []
    for seed in range(args.seed_offset, args.seed_offset+args.seeds):
        runtime = make_episode(args.skill, args.policy, seed, args.height, push_ik_mode=args.push_ik_mode, native_collisions=args.native_collisions, velocity_mode=args.velocity_mode, constraint_substeps=args.constraint_substeps, contact_time_constant=args.contact_time_constant, contact_damping_ratio=args.contact_damping_ratio, contact_impedance=args.contact_impedance, contact_width=args.contact_width, contact_margin=args.contact_margin, push_height_offset=args.push_height_offset, push_hand_pitch=args.push_hand_pitch)
        result = run_push_episode(args.policy, seed, runtime=runtime) if args.skill == "push" else run_climb(runtime, seed, args.height)
        result["physical_initializations"] = 1
        results.append(result)
        print(f"{args.skill} seed={seed} succeeded={result['succeeded']} reason={result['reason']}", flush=True)
    paths = [Path(__file__), PROFILE_PATH, DEPLOY / "config.yaml", ROOT / "check_box_push_policy.py"]
    if args.native_collisions:
        paths.append(COLLISION_PROFILE_PATH)
    paths.extend(ROOT / "reconfigurable_navigation" / name for name in ("piper_box_runtime.py", "piper_robot_profile.py", "velocity_projection.py", "box_push_runtime.py", "box_climb_runtime.py", "climb_runtime.py"))
    paths.extend(path for path in (ROOT / "robots/go2_piper").rglob("*") if path.is_file())
    report = {"schema_version": 1, "robot": "go2_piper", "skill": args.skill, "height": args.height,
              "push_ik_mode": args.push_ik_mode if args.skill == "push" else None,
              "native_collisions": args.native_collisions,
              "velocity_mode": args.velocity_mode, "constraint_substeps": args.constraint_substeps, "contact_time_constant": args.contact_time_constant, "contact_damping_ratio": args.contact_damping_ratio, "contact_impedance": args.contact_impedance, "contact_width": args.contact_width, "contact_margin": args.contact_margin,
              "push_height_offset": args.push_height_offset,
              "push_hand_pitch": args.push_hand_pitch,
              "backend": {"mujoco": mujoco.__version__, "torch": torch.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
                          "cpu_capability": torch.backends.cpu.get_cpu_capability(), "torch_threads": torch.get_num_threads()},
              "successful_episodes": sum(result["succeeded"] for result in results), "evaluated_episodes": len(results),
              "failures": dict(Counter(result["reason"] for result in results if not result["succeeded"])),
              "policy_sha256": sha256(args.policy), "source_assets_sha256": {str(path): sha256(path) for path in paths},
              "actuator_delay_steps": runtime.actuator_delay_steps.tolist(), "velocity_limits": runtime.joint_velocity_limits.tolist(),
              "kp": runtime.kp.tolist(), "kd": runtime.kd.tolist(), "results": results}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x") as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
    print(json.dumps({key: report[key] for key in ("successful_episodes", "evaluated_episodes", "failures")}, indent=2))
    return 0 if all(result["succeeded"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())