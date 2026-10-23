"""Calibrate MuJoCo passive arm dynamics against a root-fixed Isaac PUSH trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.optimize import differential_evolution

from scan_piper_push_reachability import make_geometry_runtime


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mujoco-trace", type=Path, required=True)
    parser.add_argument("--isaac-trace", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--mode", choices=("passive", "pd"), default="passive")
    parser.add_argument("--constraint-substeps", type=int, choices=(1, 2, 4), default=1)
    parser.add_argument("--integrator", choices=("Euler", "implicit", "implicitfast"), default="Euler")
    parser.add_argument("--zero-gravity", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=40)
    parser.add_argument("--population", type=int, default=8)
    parser.add_argument("--armature-min", type=float, default=0.002)
    parser.add_argument("--armature-max", type=float, default=0.08)
    parser.add_argument("--damping-max", type=float, default=5.0)
    parser.add_argument("--kp-scale-min", type=float, default=0.5)
    parser.add_argument("--kp-scale-max", type=float, default=2.5)
    parser.add_argument("--kd-scale-min", type=float, default=0.25)
    parser.add_argument("--kd-scale-max", type=float, default=3.0)
    args = parser.parse_args()
    if args.output_json.exists() or args.max_iterations < 1 or args.population < 4:
        parser.error("Output must be new and search limits must be positive")
    if not 0.0 < args.armature_min < args.armature_max or not 0.0 < args.damping_max:
        parser.error("Armature and damping bounds must be positive and ordered")
    if not 0.0 < args.kp_scale_min < args.kp_scale_max or not 0.0 < args.kd_scale_min < args.kd_scale_max:
        parser.error("PD scale bounds must be positive and ordered")
    return args


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_trace_pair(mujoco_trace, isaac_trace):
    for key in ("task", "joint_names", "physics_dt", "initial_state"):
        if mujoco_trace[key] != isaac_trace[key]:
            raise ValueError(f"Trace mismatch: {key}")
    if mujoco_trace.get("root_mode") != "kinematic_prescribed_each_physics_step":
        raise ValueError("Calibration requires a root-prescribed MuJoCo trace")
    if isaac_trace.get("root_mode") != mujoco_trace["root_mode"]:
        raise ValueError("Isaac trace must use the same prescribed-root mode")
    if len(mujoco_trace["steps"]) != len(isaac_trace["steps"]) or not mujoco_trace["steps"]:
        raise ValueError("Trace pair requires equal nonempty physics steps")
    for source, native in zip(mujoco_trace["steps"], isaac_trace["steps"]):
        if source["physics_step"] != native["physics_step"] or source["target"] != native["target"]:
            raise ValueError("Trace targets must match at every physics step")


def set_root(runtime, source):
    runtime.data.qpos[:7] = source["root_pose"]
    runtime.data.qvel[:6] = source["root_velocity"]
    mujoco.mj_forward(runtime.model, runtime.data)


def trace_groups(trace, decimation):
    steps = trace["steps"]
    if len(steps) % decimation:
        raise ValueError("Trace length must be divisible by the control decimation")
    groups = []
    for start in range(0, len(steps), decimation):
        group = steps[start:start + decimation]
        if any(row["target"] != group[0]["target"] for row in group):
            raise ValueError("Targets must be constant inside each control period")
        groups.append(group)
    return groups


def replay(trace, *, joint2_armature, joint3_armature, joint2_damping, joint3_damping, joint2_kp_scale, joint3_kp_scale, joint2_kd_scale, joint3_kd_scale, constraint_substeps=1, integrator="Euler", zero_gravity=False):
    runtime = make_geometry_runtime(210, 0.03)
    model, data = runtime.model, runtime.data
    if zero_gravity:
        model.opt.gravity[:] = 0.0
    model.opt.integrator = {
        "Euler": mujoco.mjtIntegrator.mjINT_EULER,
        "implicit": mujoco.mjtIntegrator.mjINT_IMPLICIT,
        "implicitfast": mujoco.mjtIntegrator.mjINT_IMPLICITFAST,
    }[integrator]
    initial = trace["initial_state"]
    data.qpos[:7] = initial["root_pose"]
    data.qvel[:6] = initial["root_velocity"]
    data.qpos[runtime.joint_qpos_adr] = initial["joint_positions"]
    data.qvel[runtime.joint_dof_adr] = initial["joint_velocities"]
    if "box_initial_state" in trace:
        box_state = data.joint("push_box_joint")
        box_state.qpos[:] = trace["box_initial_state"]["root_pose"]
        box_state.qvel[:] = trace["box_initial_state"]["root_velocity"]
    mujoco.mj_forward(model, data)
    joint2_dof = int(model.jnt_dofadr[model.joint("joint2").id])
    joint3_dof = int(model.jnt_dofadr[model.joint("joint3").id])
    model.dof_armature[joint2_dof] = joint2_armature
    model.dof_armature[joint3_dof] = joint3_armature
    model.dof_damping[joint2_dof] = joint2_damping
    model.dof_damping[joint3_dof] = joint3_damping
    runtime.kp[13] *= joint2_kp_scale
    runtime.kp[14] *= joint3_kp_scale
    runtime.kd[13] *= joint2_kd_scale
    runtime.kd[14] *= joint3_kd_scale
    runtime.constraint_substeps = constraint_substeps
    runtime.target_history.clear()
    runtime.target_history.extend(np.zeros(18, dtype=np.float64) for _ in range(runtime.target_history.maxlen))
    rows = []
    groups = trace_groups(trace, runtime.decimation)
    step_index = 0
    solver_step_index = 0

    def record_step():
        nonlocal solver_step_index, step_index
        source = trace["steps"][step_index]
        if solver_step_index % constraint_substeps == constraint_substeps - 1:
            rows.append({
                "joint_positions": data.qpos[runtime.joint_qpos_adr].copy(),
                "joint_velocities": data.qvel[runtime.joint_dof_adr].copy(),
                "torque": data.ctrl.copy(),
            })
            step_index += 1
        set_root(runtime, source)
        solver_step_index += 1

    runtime.on_safety_step = record_step
    for group in groups:
        set_root(runtime, group[0])
        runtime._simulate_target(np.asarray(group[0]["target"], dtype=np.float64))
    if step_index != len(trace["steps"]):
        raise ValueError("Replay emitted an unexpected number of physics steps")
    return rows


def errors(rows, reference, names):
    actual_position = np.asarray([row["joint_positions"] for row in rows])
    actual_velocity = np.asarray([row["joint_velocities"] for row in rows])
    actual_torque = np.asarray([row["torque"] for row in rows])
    expected_position = np.asarray([row["solver_positions"] for row in reference["steps"]])
    expected_velocity = np.asarray([row["solver_velocities"] for row in reference["steps"]])
    expected_torque = np.asarray([row["torque"] for row in reference["steps"]])
    indices = [names.index("joint2"), names.index("joint3")]
    position = actual_position[:, indices] - expected_position[:, indices]
    velocity = actual_velocity[:, indices] - expected_velocity[:, indices]
    torque = actual_torque[:, indices] - expected_torque[:, indices]
    return {
        "position_rmse": float(np.sqrt(np.mean(np.square(position)))),
        "velocity_rmse": float(np.sqrt(np.mean(np.square(velocity)))),
        "torque_rmse": float(np.sqrt(np.mean(np.square(torque)))),
        "position_max_abs": float(np.max(np.abs(position))),
        "velocity_max_abs": float(np.max(np.abs(velocity))),
        "torque_max_abs": float(np.max(np.abs(torque))),
        "joint2_position_error_final": float(position[-1, 0]),
        "joint3_position_error_final": float(position[-1, 1]),
    }


def objective(metrics):
    return (
        (metrics["position_rmse"] / 0.05) ** 2
        + (metrics["velocity_rmse"] / 1.0) ** 2
        + (metrics["torque_rmse"] / 1.0) ** 2
    )


def main():
    args = parse_args()
    source = json.loads(args.mujoco_trace.read_text())
    native = json.loads(args.isaac_trace.read_text())
    validate_trace_pair(source, native)
    names = source["joint_names"]
    baseline_parameters = {
        "joint2_armature": 0.01, "joint3_armature": 0.01,
        "joint2_damping": 0.0, "joint3_damping": 0.0,
        "joint2_kp_scale": 1.0, "joint3_kp_scale": 1.0,
        "joint2_kd_scale": 1.0, "joint3_kd_scale": 1.0,
    }
    baseline_rows = replay(
        source, **baseline_parameters, constraint_substeps=args.constraint_substeps, integrator=args.integrator,
        zero_gravity=args.zero_gravity,
    )
    if args.constraint_substeps == 1:
        source_positions = np.asarray([row["limited_positions"] for row in source["steps"]])
        reproduction_error = float(
            np.max(np.abs(source_positions - np.asarray([row["joint_positions"] for row in baseline_rows])))
        )
    else:
        reproduction_error = None
    baseline_metrics = errors(baseline_rows, native, names)

    def evaluate(values):
        parameters = baseline_parameters.copy()
        if args.mode == "passive":
            parameters.update({
                "joint2_armature": values[0], "joint3_armature": values[1],
                "joint2_damping": values[2], "joint3_damping": values[3],
            })
        else:
            parameters.update({
                "joint2_kp_scale": values[0], "joint3_kp_scale": values[1],
                "joint2_kd_scale": values[2], "joint3_kd_scale": values[3],
            })
        rows = replay(
            source, **parameters, constraint_substeps=args.constraint_substeps, integrator=args.integrator,
            zero_gravity=args.zero_gravity,
        )
        return objective(errors(rows, native, names))

    bounds = (
        (
            (args.armature_min, args.armature_max),
            (args.armature_min, args.armature_max),
            (0.0, args.damping_max),
            (0.0, args.damping_max),
        ) if args.mode == "passive" else (
            (args.kp_scale_min, args.kp_scale_max),
            (args.kp_scale_min, args.kp_scale_max),
            (args.kd_scale_min, args.kd_scale_max),
            (args.kd_scale_min, args.kd_scale_max),
        )
    )

    result = differential_evolution(
        evaluate,
        bounds=bounds,
        seed=20260926,
        popsize=args.population,
        maxiter=args.max_iterations,
        polish=True,
        tol=1.0e-5,
        workers=1,
        updating="immediate",
    )
    values = result.x.tolist()
    optimized_parameters = baseline_parameters.copy()
    if args.mode == "passive":
        optimized_parameters.update({
            "joint2_armature": values[0], "joint3_armature": values[1],
            "joint2_damping": values[2], "joint3_damping": values[3],
        })
    else:
        optimized_parameters.update({
            "joint2_kp_scale": values[0], "joint3_kp_scale": values[1],
            "joint2_kd_scale": values[2], "joint3_kd_scale": values[3],
        })
    optimized_metrics = errors(
        replay(
            source, **optimized_parameters, constraint_substeps=args.constraint_substeps, integrator=args.integrator,
            zero_gravity=args.zero_gravity,
        ), native, names,
    )
    report = {
        "schema_version": 1,
        "diagnostic_only": True,
        "mujoco_trace_sha256": sha256(args.mujoco_trace),
        "isaac_trace_sha256": sha256(args.isaac_trace),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "trace_steps": len(source["steps"]),
        "mode": args.mode,
        "constraint_substeps": args.constraint_substeps,
        "integrator": args.integrator,
        "zero_gravity": args.zero_gravity,
        "reproduction_max_position_error": reproduction_error,
        "baseline": {"parameters": baseline_parameters, "metrics": baseline_metrics, "objective": objective(baseline_metrics)},
        "optimized": {
            "parameters": optimized_parameters,
            "metrics": optimized_metrics,
            "objective": objective(optimized_metrics),
            "optimizer_success": bool(result.success),
            "optimizer_message": str(result.message),
        },
        "bounds": {
            "armature": [args.armature_min, args.armature_max],
            "damping": [0.0, args.damping_max],
            "kp_scale": [args.kp_scale_min, args.kp_scale_max],
            "kd_scale": [args.kd_scale_min, args.kd_scale_max],
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({
        "reproduction_max_position_error": reproduction_error,
        "baseline_objective": report["baseline"]["objective"],
        "optimized_objective": report["optimized"]["objective"],
        "optimized_parameters": optimized_parameters,
    }, allow_nan=False))


if __name__ == "__main__":
    main()