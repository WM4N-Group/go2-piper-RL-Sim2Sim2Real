"""Track a recorded static PUSH detour with MuJoCo PD and substep safety checks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import mujoco
import numpy as np
import torch
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from reconfigurable_navigation.piper_box_runtime import make_episode


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-rate", type=float, default=0.5)
    parser.add_argument("--settle-seconds", type=float, default=0.5)
    parser.add_argument("--final-hold-seconds", type=float, default=2.0)
    parser.add_argument("--joint-tolerance", type=float, default=0.04)
    parser.add_argument("--hand-tolerance", type=float, default=0.025)
    parser.add_argument("--orientation-tolerance", type=float, default=0.35)
    parser.add_argument("--orientation-weight", type=float, default=0.03)
    parser.add_argument("--base-mode", choices=("prescribed", "free"), default="prescribed")
    parser.add_argument("--terminal-correction", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    if not np.isfinite(args.orientation_weight) or not 0.0 < args.orientation_weight <= 1.0:
        parser.error("Orientation weight must be finite and in (0, 1]")
    source = json.loads(args.path_report.read_text())
    if source["path"] is None or not all(edge["safe"] for edge in source["path"]["edges"]):
        parser.error("Input must contain a statically safe path")
    with patch("reconfigurable_navigation.climb_runtime.torch.jit.load", return_value=torch.nn.Identity()):
        runtime = make_episode("push", "geometry-only.pt", 1708, push_ik_mode="pose", native_collisions=True,
                               constraint_substeps=2)
    model, data, arm = runtime.model, runtime.data, runtime.arm
    nodes = [np.asarray(row) for row in source["path"]["nodes"]]
    target_rotation = Rotation.from_quat(np.asarray(source["target_hand_quaternion"])[[1, 2, 3, 0]])
    data.qpos[:] = source["base_qpos"]
    data.qvel[:] = source.get("base_qvel", np.zeros(model.nv))
    mujoco.mj_forward(model, data)
    arm.reset()
    root_qpos = data.qpos[:7].copy()
    minimum_base_height = float(data.qpos[2])
    base_floor_contact = False
    minimum_supported_feet = 4
    airborne_substeps = 0
    maximum_foot_contact_force = 0.0
    maximum_vertical_speed = 0.0
    leg_target = np.asarray(source.get("source_leg_target", data.qpos[runtime.joint_qpos_adr[:12]])).copy()
    minimum_protected = float("inf")
    minimum_box = float("inf")
    maximum_joint_error = 0.0
    max_torque_ratio = 0.0
    saturated_substeps = 0
    substeps = 0
    collision = None
    active_desired = nodes[0]
    original_monitor = runtime.on_safety_step
    last_target = None
    protected_pairs = [(first, second) for first in arm.collision_arm_geoms
                       for second in arm.collision_protected_geoms]
    box_pairs = [(first, arm.box_geom) for first in arm.collision_arm_geoms]

    def monitor():
        nonlocal minimum_protected, minimum_box, maximum_joint_error
        nonlocal max_torque_ratio, saturated_substeps, substeps, collision
        nonlocal minimum_base_height, base_floor_contact
        nonlocal minimum_supported_feet, airborne_substeps, maximum_foot_contact_force, maximum_vertical_speed
        original_monitor()
        protected = min(float(mujoco.mj_geomDistance(model, data, first, second, 1.0, None))
                        for first, second in protected_pairs)
        box = min(float(mujoco.mj_geomDistance(model, data, first, second, 1.0, None))
                  for first, second in box_pairs)
        minimum_protected = min(minimum_protected, protected)
        minimum_box = min(minimum_box, box)
        maximum_joint_error = max(maximum_joint_error, float(np.max(np.abs(data.qpos[arm.arm_qpos] - active_desired))))
        limits = np.where(data.ctrl >= 0.0, runtime.ctrl_high, -runtime.ctrl_low)
        ratios = np.abs(data.ctrl) / limits
        max_torque_ratio = max(max_torque_ratio, float(np.max(ratios)))
        saturated_substeps += int(np.any(ratios >= 1.0 - 1e-8))
        substeps += 1
        minimum_base_height = min(minimum_base_height, float(data.qpos[2]))
        base_floor_contact = base_floor_contact or runtime.base_contacts_terrain()
        maximum_vertical_speed = max(maximum_vertical_speed, abs(float(data.qvel[2])))
        foot_forces = {name: 0.0 for name in ("FL", "FR", "RL", "RR")}
        for contact_index, contact in enumerate(data.contact[:data.ncon]):
            names = (model.geom(int(contact.geom1)).name, model.geom(int(contact.geom2)).name)
            if "floor" not in names:
                continue
            foot_name = names[1] if names[0] == "floor" else names[0]
            if foot_name in foot_forces:
                force = np.zeros(6)
                mujoco.mj_contactForce(model, data, contact_index, force)
                foot_forces[foot_name] += abs(float(force[0]))
        supported = sum(force > 2.0 for force in foot_forces.values())
        minimum_supported_feet = min(minimum_supported_feet, supported)
        airborne_substeps += int(supported == 0)
        maximum_foot_contact_force = max(maximum_foot_contact_force, *foot_forces.values())
        if collision is None and (protected < source["minimum_required_clearance"] or box < 0.005
                                  or (runtime.self_collision is not None and runtime.self_collision["distance"] < 0.0)):
            collision = {"time": float(data.time), "protected_clearance": protected,
                         "box_clearance": box, "self_collision": runtime.self_collision}

    runtime.on_safety_step = monitor
    runtime.target_history.clear()
    base_target = data.qpos[runtime.joint_qpos_adr].copy()
    runtime.target_history.extend(base_target.copy() for _ in range(runtime.target_history.maxlen))

    def simulate(desired):
        nonlocal last_target
        if args.base_mode == "prescribed":
            data.qpos[:7] = root_qpos
            data.qvel[:6] = 0.0
            mujoco.mj_forward(model, data)
        arm.gravity_data.qpos[:] = data.qpos
        arm.gravity_data.qvel.fill(0.0)
        mujoco.mj_forward(model, arm.gravity_data)
        target = base_target.copy()
        target[:12] = leg_target
        target[12:] = desired + arm.gravity_data.qfrc_bias[arm.arm_dof] / runtime.kp[12:]
        last_target = target.copy()
        runtime._simulate_target(target)

    settle_steps = int(np.ceil(args.settle_seconds / runtime.control_dt))
    for _ in range(settle_steps):
        simulate(nodes[0])
        if collision is not None:
            break
    segments = []
    if collision is None:
        for index, (first, second) in enumerate(zip(nodes, nodes[1:])):
            steps = max(1, int(np.ceil(np.max(np.abs(second - first)) / (args.max_rate * runtime.control_dt))))
            for step in range(1, steps + 1):
                active_desired = first + (second - first) * step / steps
                simulate(active_desired)
                if collision is not None:
                    break
            segments.append({"index": index, "planned_steps": steps, "completed_steps": step,
                             "joint_position": data.qpos[arm.arm_qpos].tolist(),
                             "joint_error": float(np.max(np.abs(data.qpos[arm.arm_qpos] - active_desired)))})
            if collision is not None:
                break
    final_hold_steps = 0
    if collision is None and len(segments) == len(nodes) - 1:
        active_desired = nodes[-1]
        for _ in range(int(np.ceil(args.final_hold_seconds / runtime.control_dt))):
            simulate(active_desired)
            final_hold_steps += 1
            if collision is not None:
                break
    final_desired = nodes[-1]
    correction = None
    if args.terminal_correction and collision is None and len(segments) == len(nodes) - 1:
        correction_start = data.qpos[arm.arm_qpos].copy()
        saved_qpos = data.qpos.copy()

        def correction_residual(candidate):
            data.qpos[arm.arm_qpos] = candidate
            mujoco.mj_forward(model, data)
            hand_residual = arm.hand_position() - source["target_hand_position"]
            hand_rotation = Rotation.from_matrix(data.xmat[arm.hand_body].reshape(3, 3))
            orientation_residual = (target_rotation.inv() * hand_rotation).as_rotvec()
            protected = arm._minimum_protected_clearance(candidate)
            box_clearance = min(float(mujoco.mj_geomDistance(model, data, first, arm.box_geom, 1.0, None))
                                for first in arm.collision_arm_geoms)
            return np.r_[hand_residual, args.orientation_weight * orientation_residual,
                         0.005 * (candidate - correction_start),
                         10.0 * max(0.0, source["minimum_required_clearance"] + 0.003 - protected),
                         10.0 * max(0.0, 0.008 - box_clearance)]

        solved = least_squares(correction_residual, correction_start, bounds=(arm.lower, arm.upper),
                               max_nfev=80)
        data.qpos[:] = saved_qpos
        mujoco.mj_forward(model, data)
        proposed = solved.x
        samples = max(1, int(np.ceil(np.max(np.abs(proposed - correction_start)) / 0.01)))
        static_min_protected = float("inf")
        static_min_box = float("inf")
        for fraction in np.linspace(0.0, 1.0, samples + 1):
            candidate = correction_start + fraction * (proposed - correction_start)
            data.qpos[arm.arm_qpos] = candidate
            mujoco.mj_forward(model, data)
            static_min_protected = min(static_min_protected, arm._minimum_protected_clearance(candidate))
            static_min_box = min(static_min_box, *(float(mujoco.mj_geomDistance(
                model, data, first, arm.box_geom, 1.0, None)) for first in arm.collision_arm_geoms))
        data.qpos[:] = saved_qpos
        mujoco.mj_forward(model, data)
        static_safe = static_min_protected >= source["minimum_required_clearance"] and static_min_box >= 0.005
        correction = {"optimizer_success": bool(solved.success), "proposed_joint": proposed.tolist(),
                      "static_minimum_protected_clearance": static_min_protected,
                      "static_minimum_box_clearance": static_min_box, "static_safe": static_safe,
                      "executed_steps": 0}
        if static_safe:
            steps = max(1, int(np.ceil(np.max(np.abs(proposed - correction_start)) / (args.max_rate * runtime.control_dt))))
            for step in range(1, steps + 1):
                active_desired = correction_start + (proposed - correction_start) * step / steps
                simulate(active_desired)
                correction["executed_steps"] += 1
                if collision is not None:
                    break
            if collision is None:
                for _ in range(int(np.ceil(args.final_hold_seconds / runtime.control_dt))):
                    simulate(proposed)
                    correction["executed_steps"] += 1
                    if collision is not None:
                        break
            final_desired = proposed
    final_joint_error = float(np.max(np.abs(data.qpos[arm.arm_qpos] - final_desired)))
    final_hand_position = arm.hand_position().copy()
    final_hand_target_error = float(np.linalg.norm(final_hand_position - source["target_hand_position"]))
    hand_rotation = Rotation.from_matrix(data.xmat[arm.hand_body].reshape(3, 3))
    final_hand_orientation_error = float((target_rotation.inv() * hand_rotation).magnitude())
    arm_joint_ids = model.dof_jntid[arm.arm_dof]
    final_contacts = [
        {"first": model.geom(int(contact.geom1)).name, "second": model.geom(int(contact.geom2)).name,
         "distance": float(contact.dist)}
        for contact in data.contact[:data.ncon]
    ]
    result = {
        "schema_version": 1, "kind": "pd_substep_detour_diagnostic", "base_mode": args.base_mode,
        "env": source["env"],
        "source_path_sha256": sha256(args.path_report), "script_sha256": sha256(Path(__file__)),
        "runtime_source_sha256": sha256(Path(make_episode.__code__.co_filename)),
        "source_report_sha256": source["source_report_sha256"],
        "max_rate_rad_s": args.max_rate, "settle_seconds": args.settle_seconds,
        "final_hold_seconds": args.final_hold_seconds, "final_hold_steps": final_hold_steps,
        "joint_tolerance": args.joint_tolerance, "final_joint_error": final_joint_error,
        "hand_tolerance": args.hand_tolerance,
        "orientation_tolerance": args.orientation_tolerance,
        "orientation_weight": args.orientation_weight,
        "final_desired_joint": final_desired.tolist(), "final_target_joint": last_target[12:].tolist(),
        "terminal_correction": correction,
        "final_actual_joint": data.qpos[arm.arm_qpos].tolist(),
        "final_hand_position": final_hand_position.tolist(),
        "target_hand_position": source["target_hand_position"],
        "final_hand_target_error": final_hand_target_error,
        "final_hand_orientation_error": final_hand_orientation_error,
        "final_joint_velocity": data.qvel[arm.arm_dof].tolist(),
        "final_arm_ctrl": data.ctrl[12:].tolist(), "final_arm_bias": data.qfrc_bias[arm.arm_dof].tolist(),
        "final_arm_constraint_force": data.qfrc_constraint[arm.arm_dof].tolist(),
        "final_arm_passive_force": data.qfrc_passive[arm.arm_dof].tolist(),
        "final_arm_acceleration": data.qacc[arm.arm_dof].tolist(),
        "arm_joint_range": model.jnt_range[arm_joint_ids].tolist(),
        "final_contacts": final_contacts,
        "final_base_qpos": data.qpos[:7].tolist(), "minimum_base_height": minimum_base_height,
        "base_floor_contact": base_floor_contact,
        "minimum_supported_feet": minimum_supported_feet, "airborne_substeps": airborne_substeps,
        "maximum_foot_contact_force": maximum_foot_contact_force,
        "maximum_vertical_speed": maximum_vertical_speed,
        "substeps": substeps, "duration_s": float(data.time), "minimum_protected_clearance": minimum_protected,
        "minimum_box_clearance": minimum_box, "maximum_joint_error": maximum_joint_error,
        "maximum_torque_limit_ratio": max_torque_ratio, "saturated_substeps_including_settle": saturated_substeps,
        "collision": collision, "segments": segments,
        "passed": collision is None and not base_floor_contact and len(segments) == len(nodes) - 1 and saturated_substeps == 0
                  and final_joint_error <= args.joint_tolerance and final_hand_target_error <= args.hand_tolerance
                  and final_hand_orientation_error <= args.orientation_tolerance,
        "limitations": "Source legs held without NAV policy; no full PUSH task validation. Prescribed mode resets the base every 20ms.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"passed": result["passed"], "collision": collision,
                      "saturated_substeps": saturated_substeps, "output": str(args.output)}))


if __name__ == "__main__":
    main()
