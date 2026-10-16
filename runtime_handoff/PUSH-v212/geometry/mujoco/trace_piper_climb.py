"""Record solver output before and after deployment velocity limiting."""

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
import torch

from check_piper_box_skills import run_climb
from check_piper_startup import sha256
from reconfigurable_navigation.piper_box_runtime import DEPLOY, ROOT, make_episode


def trace_episode(policy, seed, velocity_mode="legacy", targets=None, constraint_substeps=1, contact_time_constant=None, contact_damping_ratio=None, contact_impedance=None, contact_width=None, contact_margin=0.0):
    runtime = make_episode("climb", policy, seed, native_collisions=True, velocity_mode=velocity_mode, constraint_substeps=constraint_substeps, contact_time_constant=contact_time_constant, contact_damping_ratio=contact_damping_ratio, contact_impedance=contact_impedance, contact_width=contact_width, contact_margin=contact_margin)
    model, data = runtime.model, runtime.data
    rows = []
    initial_state = {
        "root_pose": data.qpos[:7].tolist(), "root_velocity": data.qvel[:6].tolist(),
        "joint_positions": data.qpos[runtime.joint_qpos_adr].tolist(),
        "joint_velocities": data.qvel[runtime.joint_dof_adr].tolist(),
    }

    def solver_step():
        contacts = []
        for index in range(data.ncon):
            contact = data.contact[index]
            wrench = np.zeros(6)
            mujoco.mj_contactForce(model, data, index, wrench)
            contacts.append({
                "geoms": [model.geom(int(contact.geom1)).name, model.geom(int(contact.geom2)).name],
                "position": contact.pos.tolist(), "distance": float(contact.dist),
                "normal_force": float(wrench[0]),
            })
        rows.append({
            "physics_step": len(rows), "time": float(data.time),
            "root_pose": data.qpos[:7].tolist(), "root_velocity": data.qvel[:6].tolist(),
            "target": runtime.target_history[-1].tolist(),
            "torque": data.ctrl.tolist(),
            "solver_positions": data.qpos[runtime.joint_qpos_adr].tolist(),
            "solver_velocities": data.qvel[runtime.joint_dof_adr].tolist(),
            "contacts": contacts,
        })

    def physics_step():
        rows[-1]["limited_positions"] = data.qpos[runtime.joint_qpos_adr].tolist()
        rows[-1]["limited_velocities"] = data.qvel[runtime.joint_dof_adr].tolist()
        rows[-1]["solver_root_pose"] = rows[-1]["root_pose"]
        rows[-1]["root_pose"] = data.qpos[:7].tolist()
        rows[-1]["root_velocity"] = data.qvel[:6].tolist()
        rows[-1]["foot_positions"] = data.geom_xpos[[model.geom(name).id for name in ("FL", "FR", "RL", "RR")]].tolist()

    runtime.on_solver_step = solver_step
    runtime.on_physics_step = physics_step
    if targets is None:
        result = run_climb(runtime, seed, 0.2)
    else:
        if targets["initial_state"] != initial_state or targets["policy_sha256"] != sha256(policy):
            raise ValueError("Open-loop replay requires matching initial state and policy")
        if targets["physics_dt"] != runtime.sim_dt or len(targets["steps"]) % runtime.decimation:
            raise ValueError("Open-loop replay requires matching physics and control periods")
        for index in range(0, len(targets["steps"]), runtime.decimation):
            target = targets["steps"][index]["target"]
            if any(row["target"] != target for row in targets["steps"][index:index + runtime.decimation]):
                raise ValueError("Targets must be constant within each control period")
            runtime._simulate_target(np.array(target))
        result = {"seed": seed, "succeeded": False, "reason": "open_loop_complete", "elapsed": float(data.time)}
    solver_velocity = np.array([row["solver_velocities"] for row in rows])
    limited_velocity = np.array([row["limited_velocities"] for row in rows])
    position_correction = np.array([row["limited_positions"] for row in rows]) - np.array([row["solver_positions"] for row in rows])
    report = {
        "schema_version": 1, "backend": "mujoco", "mujoco_version": mujoco.__version__,
        "velocity_mode": velocity_mode, "diagnostic_only": True,
        "constraint_substeps": constraint_substeps,
        "contact_time_constant": contact_time_constant,
        "contact_damping_ratio": contact_damping_ratio,
        "contact_impedance": contact_impedance,
        "contact_width": contact_width,
        "contact_margin": contact_margin,
        "contact_solref": model.geom_solref.tolist(),
        "targets_sha256": None if targets is None else targets["input_sha256"],
        "policy_sha256": sha256(policy), "script_sha256": sha256(Path(__file__)),
        "source_sha256": {str(path): sha256(path) for path in (
            DEPLOY / "config.yaml", ROOT / "check_piper_box_skills.py",
            *(ROOT / "reconfigurable_navigation" / name for name in (
                "piper_box_runtime.py", "piper_robot_profile.py", "climb_runtime.py",
                "box_climb_runtime.py", "velocity_projection.py")),
            ROOT / "deploy/piper_robot_profile.json", ROOT / "deploy/piper_collision_profile.json",
        )},
        "physics_dt": runtime.sim_dt, "control_dt": runtime.control_dt,
        "joint_names": [model.joint(int(model.dof_jntid[index])).name for index in runtime.joint_dof_adr],
        "actuator_delay_steps": runtime.actuator_delay_steps.tolist(),
        "initial_state": initial_state, "kp": runtime.kp.tolist(), "kd": runtime.kd.tolist(),
        "torque_limits": runtime.ctrl_high.tolist(),
        "velocity_limits": runtime.joint_velocity_limits.tolist(), "result": result,
        "summary": {
            "steps": len(rows),
            "velocity_clipped_steps_per_joint": np.sum(np.abs(solver_velocity - limited_velocity) > 1e-9, axis=0).tolist(),
            "max_position_correction_per_joint": np.max(np.abs(position_correction), axis=0).tolist(),
            "max_solver_speed_per_joint": np.max(np.abs(solver_velocity), axis=0).tolist(),
        },
        "steps": rows,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=500)
    parser.add_argument("--velocity-mode", choices=("legacy", "coupled", "coupled-bounds"), default="legacy")
    parser.add_argument("--constraint-substeps", type=int, choices=(1, 2), default=1)
    parser.add_argument("--targets-json", type=Path)
    parser.add_argument("--contact-time-constant", type=float)
    parser.add_argument("--contact-damping-ratio", type=float)
    parser.add_argument("--contact-impedance", type=float)
    parser.add_argument("--contact-width", type=float)
    parser.add_argument("--contact-margin", type=float, default=0.0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    if args.seed < 0 or args.output_json.exists():
        parser.error("Require a nonnegative seed and a new output")
    if args.contact_time_constant is not None and (not np.isfinite(args.contact_time_constant) or args.contact_time_constant < 0.01):
        parser.error("Contact time constant must be finite and at least two physics steps (0.01 s)")
    if args.contact_damping_ratio is not None and (not np.isfinite(args.contact_damping_ratio) or args.contact_damping_ratio <= 0.0):
        parser.error("Contact damping ratio must be positive and finite")
    if args.contact_impedance is not None and (not np.isfinite(args.contact_impedance) or not 0.0 < args.contact_impedance < 0.95):
        parser.error("Contact impedance must be between 0 and 0.95")
    if args.contact_width is not None and (not np.isfinite(args.contact_width) or not 0.0 < args.contact_width <= 0.05):
        parser.error("Contact width must be between 0 and 0.05 m")
    if not np.isfinite(args.contact_margin) or not 0.0 <= args.contact_margin <= 0.01:
        parser.error("Contact margin must be between 0 and 0.01 m")
    torch.set_num_threads(1)
    targets = None
    if args.targets_json is not None:
        targets = json.loads(args.targets_json.read_text())
        targets["input_sha256"] = sha256(args.targets_json)
    report = trace_episode(args.policy, args.seed, args.velocity_mode, targets, args.constraint_substeps, args.contact_time_constant, args.contact_damping_ratio, args.contact_impedance, args.contact_width, args.contact_margin)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x") as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
    print(json.dumps({"result": report["result"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())