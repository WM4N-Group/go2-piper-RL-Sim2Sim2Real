"""Scan collision-safe PIPER PUSH arm poses across advancing base positions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import mujoco
import numpy as np
import torch
from scipy.optimize import differential_evolution

from reconfigurable_navigation.piper_box_runtime import make_episode


ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=210)
    parser.add_argument("--base-x", type=float, nargs="+", default=(-0.14, -0.10, -0.06, -0.02))
    parser.add_argument("--base-y", type=float, nargs="+", default=(0.0,))
    parser.add_argument("--base-height", type=float, nargs="+", default=(0.28,))
    parser.add_argument("--hand-pitch", type=float, nargs="+", default=(0.8, 1.0, 1.2))
    parser.add_argument("--contact-height-offset", type=float, default=0.03)
    parser.add_argument("--hand-center-backoff", type=float, default=0.012)
    parser.add_argument("--clearance", type=float, default=0.015)
    parser.add_argument("--position-tolerance", type=float, default=0.025)
    parser.add_argument("--orientation-tolerance", type=float, default=0.15)
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument("--population", type=int, default=12)
    parser.add_argument("--edge-samples", type=int, default=25)
    parser.add_argument("--kinematic-base-pd", action="store_true")
    parser.add_argument("--pd-initial-settle", type=float, default=2.0)
    parser.add_argument("--pd-edge-duration", type=float, default=4.0)
    parser.add_argument("--pd-max-joint-rate", type=float, default=0.5)
    parser.add_argument("--pd-joint-tolerance", type=float, default=0.04)
    args = parser.parse_args()
    def expand_base_values(values, name):
        if len(values) == 1:
            return tuple(values) * len(args.base_x)
        if len(values) != len(args.base_x):
            parser.error(f"{name} must be one value or match the number of base x values")
        return tuple(values)

    args.base_y = expand_base_values(args.base_y, "Base y")
    args.base_height = expand_base_values(args.base_height, "Base height")
    scalar_values = (
        *args.base_y, *args.base_height, args.contact_height_offset, args.hand_center_backoff,
        args.clearance, args.position_tolerance, args.orientation_tolerance,
        args.pd_initial_settle, args.pd_edge_duration, args.pd_max_joint_rate, args.pd_joint_tolerance,
    )
    if args.output_json.exists() or args.max_iterations < 1 or args.population < 4 or args.edge_samples < 2:
        parser.error("Output must be new and search limits must be positive")
    if not all(np.isfinite(value) and value > 0.0 for value in scalar_values):
        parser.error("Scan tolerances, offsets and base height must be finite and positive")
    if not all(np.isfinite(value) for value in (*args.base_x, *args.hand_pitch)):
        parser.error("Base positions and hand pitches must be finite")
    if any(not 0.0 <= value <= 1.2 for value in args.hand_pitch):
        parser.error("Hand pitches must be between 0 and 1.2 rad")
    return args


def desired_hand_rotation(box_rotation, pitch):
    cosine, sine = np.cos(pitch), np.sin(pitch)
    return box_rotation @ np.array(((cosine, 0.0, sine), (0.0, 1.0, 0.0), (-sine, 0.0, cosine)))


def rotation_error(actual, desired):
    cosine = np.clip((np.trace(desired.T @ actual) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.arccos(cosine))


def set_base_pose(runtime, base_x, base_y, base_height):
    runtime.data.qpos[:3] = (base_x, base_y, base_height)
    runtime.data.qpos[3:7] = (1.0, 0.0, 0.0, 0.0)
    runtime.data.qvel[:] = 0.0
    mujoco.mj_forward(runtime.model, runtime.data)
    runtime.arm.reset()


def contact_target(runtime, contact_height_offset, hand_center_backoff):
    arm = runtime.arm
    box_center = runtime.data.geom_xpos[arm.box_geom]
    box_rotation = arm.box_rotation()
    return box_center + box_rotation @ np.array((
        -arm.box_size[0] / 2.0 - hand_center_backoff,
        0.0,
        contact_height_offset,
    ))


def pose_metrics(runtime, joint_position, target, pitch):
    arm, data = runtime.arm, runtime.data
    original = data.qpos[arm.arm_qpos].copy()
    data.qpos[arm.arm_qpos] = joint_position
    mujoco.mj_forward(runtime.model, data)
    position = arm.hand_position().copy()
    actual_rotation = data.xmat[arm.hand_body].reshape(3, 3).copy()
    desired_rotation = desired_hand_rotation(arm.box_rotation(), pitch)
    clearance = arm._minimum_protected_clearance(joint_position)
    data.qpos[arm.arm_qpos] = original
    mujoco.mj_forward(runtime.model, data)
    return {
        "hand_position": position,
        "position_error": float(np.linalg.norm(position - target)),
        "orientation_error": rotation_error(actual_rotation, desired_rotation),
        "minimum_protected_clearance": clearance,
    }


def solve_pose(runtime, target, pitch, *, clearance, position_tolerance, orientation_tolerance, max_iterations, population, seed):
    arm = runtime.arm

    def objective(candidate):
        metrics = pose_metrics(runtime, candidate, target, pitch)
        clearance_error = max(0.0, clearance - metrics["minimum_protected_clearance"])
        return metrics["position_error"] + 0.10 * metrics["orientation_error"] + 10_000.0 * clearance_error

    result = differential_evolution(
        objective,
        list(zip(arm.lower, arm.upper)),
        seed=seed,
        popsize=population,
        maxiter=max_iterations,
        polish=True,
        tol=1.0e-5,
        workers=1,
        updating="immediate",
    )
    metrics = pose_metrics(runtime, result.x, target, pitch)
    feasible = (
        metrics["position_error"] <= position_tolerance
        and metrics["orientation_error"] <= orientation_tolerance
        and metrics["minimum_protected_clearance"] >= clearance
    )
    return {
        "joint_position": result.x.tolist(),
        "hand_position": metrics["hand_position"].tolist(),
        "position_error": metrics["position_error"],
        "orientation_error": metrics["orientation_error"],
        "minimum_protected_clearance": metrics["minimum_protected_clearance"],
        "objective": float(result.fun),
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "feasible": feasible,
    }


def candidate_groups(rows, base_poses):
    groups = []
    for base_x, base_y, base_height in base_poses:
        candidates = [
            row for row in rows
            if row["base_x"] == base_x and row["base_y"] == base_y
            and row["base_height"] == base_height and row["feasible"]
        ]
        if not candidates:
            return None
        groups.append(candidates)
    return groups


def trajectory_edges(runtime, nodes, *, contact_height_offset, hand_center_backoff, clearance, position_tolerance, orientation_tolerance, samples):
    edges = []
    for first, second in zip(nodes, nodes[1:]):
        minimum_clearance = float("inf")
        maximum_position_error = 0.0
        maximum_orientation_error = 0.0
        for fraction in np.linspace(0.0, 1.0, samples):
            base_x = (1.0 - fraction) * first["base_x"] + fraction * second["base_x"]
            base_y = (1.0 - fraction) * first["base_y"] + fraction * second["base_y"]
            base_height = (1.0 - fraction) * first["base_height"] + fraction * second["base_height"]
            pitch = (1.0 - fraction) * first["hand_pitch"] + fraction * second["hand_pitch"]
            joint_position = (1.0 - fraction) * np.asarray(first["joint_position"]) + fraction * np.asarray(second["joint_position"])
            set_base_pose(runtime, base_x, base_y, base_height)
            metrics = pose_metrics(
                runtime, joint_position,
                contact_target(runtime, contact_height_offset, hand_center_backoff), pitch,
            )
            minimum_clearance = min(minimum_clearance, metrics["minimum_protected_clearance"])
            maximum_position_error = max(maximum_position_error, metrics["position_error"])
            maximum_orientation_error = max(maximum_orientation_error, metrics["orientation_error"])
        edges.append({
            "from_base_x": first["base_x"],
            "to_base_x": second["base_x"],
            "from_hand_pitch": first["hand_pitch"],
            "to_hand_pitch": second["hand_pitch"],
            "minimum_protected_clearance": minimum_clearance,
            "maximum_position_error": maximum_position_error,
            "maximum_orientation_error": maximum_orientation_error,
            "static_safe": (
                minimum_clearance >= clearance
                and maximum_position_error <= position_tolerance
                and maximum_orientation_error <= orientation_tolerance
            ),
        })
    return edges


def select_continuous_trajectory(runtime, groups, *, contact_height_offset, hand_center_backoff, clearance, position_tolerance, orientation_tolerance, samples):
    if groups is None:
        return None, []
    states = {
        id(node): {"node": node, "nodes": [node], "edges": [], "score": node["minimum_protected_clearance"]}
        for node in groups[0]
    }
    evaluated_edges = []
    for next_group in groups[1:]:
        next_states = {}
        for state in states.values():
            for next_node in next_group:
                edge = trajectory_edges(
                    runtime, [state["node"], next_node],
                    contact_height_offset=contact_height_offset,
                    hand_center_backoff=hand_center_backoff,
                    clearance=clearance,
                    position_tolerance=position_tolerance,
                    orientation_tolerance=orientation_tolerance,
                    samples=samples,
                )[0]
                evaluated_edges.append(edge)
                if not edge["static_safe"]:
                    continue
                score = min(state["score"], next_node["minimum_protected_clearance"], edge["minimum_protected_clearance"])
                previous = next_states.get(id(next_node))
                if previous is None or score > previous["score"]:
                    next_states[id(next_node)] = {
                        "node": next_node,
                        "nodes": [*state["nodes"], next_node],
                        "edges": [*state["edges"], edge],
                        "score": score,
                    }
        states = next_states
        if not states:
            return None, evaluated_edges
    selected = max(states.values(), key=lambda state: state["score"])
    return {
        "nodes": selected["nodes"],
        "edges": selected["edges"],
        "minimum_protected_clearance": selected["score"],
        "static_safe": True,
    }, evaluated_edges


def prescribe_base_pose(runtime, position, velocity):
    runtime.data.qpos[:3] = position
    runtime.data.qpos[3:7] = (1.0, 0.0, 0.0, 0.0)
    runtime.data.qvel[:3] = velocity
    runtime.data.qvel[3:6] = 0.0
    mujoco.mj_forward(runtime.model, runtime.data)


def gravity_compensated_target(runtime, joint_position):
    arm = runtime.arm
    arm.gravity_data.qpos[:] = runtime.data.qpos
    arm.gravity_data.qvel.fill(0.0)
    mujoco.mj_forward(runtime.model, arm.gravity_data)
    target = runtime.default_qpos.copy()
    target[12:] = joint_position + arm.gravity_data.qfrc_bias[arm.arm_dof] / runtime.kp[12:]
    return target


def kinematic_base_pd_validation(runtime, trajectory, *, contact_height_offset, hand_center_backoff, clearance, position_tolerance, orientation_tolerance, initial_settle, edge_duration, max_joint_rate, joint_tolerance):
    arm, data = runtime.arm, runtime.data
    nodes = trajectory["nodes"]
    first = nodes[0]
    first_position = np.array((first["base_x"], first["base_y"], first["base_height"]))
    prescribe_base_pose(runtime, first_position, np.zeros(3))
    data.qpos[arm.arm_qpos] = first["joint_position"]
    data.qvel[arm.arm_dof] = 0.0
    mujoco.mj_forward(runtime.model, data)
    arm.reference = np.asarray(first["joint_position"], dtype=np.float64).copy()
    initial_target = gravity_compensated_target(runtime, arm.reference)
    runtime.target_history.clear()
    runtime.target_history.extend(initial_target.copy() for _ in range(runtime.target_history.maxlen))
    runtime.constraint_substeps = 2

    settle_steps = int(np.ceil(initial_settle / runtime.control_dt))
    for _ in range(settle_steps):
        prescribe_base_pose(runtime, first_position, np.zeros(3))
        runtime._simulate_target(initial_target)
    settle_metrics = pose_metrics(
        runtime, data.qpos[arm.arm_qpos],
        contact_target(runtime, contact_height_offset, hand_center_backoff), first["hand_pitch"],
    )
    settle_joint_error = float(np.max(np.abs(data.qpos[arm.arm_qpos] - arm.reference)))

    minimum_clearance = float("inf")
    maximum_position_error = 0.0
    maximum_orientation_error = 0.0
    maximum_joint_error = 0.0
    steps = 0
    collision = None
    segments = []
    for segment_index, (first, second) in enumerate(zip(nodes, nodes[1:])):
        first_position = np.array((first["base_x"], first["base_y"], first["base_height"]))
        second_position = np.array((second["base_x"], second["base_y"], second["base_height"]))
        first_joint = np.asarray(first["joint_position"], dtype=np.float64)
        second_joint = np.asarray(second["joint_position"], dtype=np.float64)
        pitch_delta = abs(second["hand_pitch"] - first["hand_pitch"])
        joint_delta = np.max(np.abs(second_joint - first_joint))
        segment_steps = max(
            1,
            int(np.ceil(edge_duration / runtime.control_dt)),
            int(np.ceil(joint_delta / (max_joint_rate * runtime.control_dt))),
            int(np.ceil(pitch_delta / (max_joint_rate * runtime.control_dt))),
        )
        base_velocity = (second_position - first_position) / (segment_steps * runtime.control_dt)
        segment_minimum_clearance = float("inf")
        segment_maximum_position_error = 0.0
        segment_maximum_orientation_error = 0.0
        segment_maximum_joint_error = 0.0
        metrics = None
        for index in range(1, segment_steps + 1):
            fraction = index / segment_steps
            prescribed_position = (1.0 - fraction) * first_position + fraction * second_position
            desired_joint = (1.0 - fraction) * first_joint + fraction * second_joint
            pitch = (1.0 - fraction) * first["hand_pitch"] + fraction * second["hand_pitch"]
            prescribe_base_pose(runtime, prescribed_position, base_velocity)
            runtime._simulate_target(gravity_compensated_target(runtime, desired_joint))
            metrics = pose_metrics(
                runtime, data.qpos[arm.arm_qpos],
                contact_target(runtime, contact_height_offset, hand_center_backoff), pitch,
            )
            minimum_clearance = min(minimum_clearance, metrics["minimum_protected_clearance"])
            maximum_position_error = max(maximum_position_error, metrics["position_error"])
            maximum_orientation_error = max(maximum_orientation_error, metrics["orientation_error"])
            joint_error = float(np.max(np.abs(data.qpos[arm.arm_qpos] - desired_joint)))
            maximum_joint_error = max(maximum_joint_error, joint_error)
            segment_minimum_clearance = min(segment_minimum_clearance, metrics["minimum_protected_clearance"])
            segment_maximum_position_error = max(segment_maximum_position_error, metrics["position_error"])
            segment_maximum_orientation_error = max(segment_maximum_orientation_error, metrics["orientation_error"])
            segment_maximum_joint_error = max(segment_maximum_joint_error, joint_error)
            steps += 1
            if runtime.self_collision is not None or arm.protected_collision_active():
                collision = runtime.self_collision
                break
        segments.append({
            "index": segment_index,
            "from_base_x": first["base_x"],
            "to_base_x": second["base_x"],
            "control_steps": segment_steps,
            "minimum_protected_clearance": segment_minimum_clearance,
            "maximum_position_error": segment_maximum_position_error,
            "maximum_orientation_error": segment_maximum_orientation_error,
            "maximum_joint_error": segment_maximum_joint_error,
            "desired_joint_position": desired_joint.tolist(),
            "joint_position": data.qpos[arm.arm_qpos].tolist(),
            "hand_position": None if metrics is None else metrics["hand_position"].tolist(),
        })
        if collision is not None:
            break
    return {
        "base_mode": "kinematic_prescribed",
        "initial_settle": {
            "control_steps": settle_steps,
            "position_error": settle_metrics["position_error"],
            "orientation_error": settle_metrics["orientation_error"],
            "joint_error": settle_joint_error,
        },
        "control_steps": steps,
        "minimum_protected_clearance": minimum_clearance,
        "maximum_position_error": maximum_position_error,
        "maximum_orientation_error": maximum_orientation_error,
        "maximum_joint_error": maximum_joint_error,
        "collision": collision,
        "segments": segments,
        "passed": (
            collision is None
            and minimum_clearance >= clearance
            and maximum_position_error <= position_tolerance
            and maximum_orientation_error <= orientation_tolerance
            and maximum_joint_error <= joint_tolerance
        ),
    }


def make_geometry_runtime(seed, contact_height_offset, *, fix_root_link=False, fixed_root_pose=None, disable_floor=False):
    with patch("reconfigurable_navigation.climb_runtime.torch.jit.load", return_value=torch.nn.Identity()):
        return make_episode(
            "push", "geometry-only.pt", seed, push_ik_mode="pose", native_collisions=True,
            push_height_offset=contact_height_offset, fix_root_link=fix_root_link, fixed_root_pose=fixed_root_pose,
            disable_floor=disable_floor,
        )


def main():
    args = parse_args()
    runtime = make_geometry_runtime(args.seed, args.contact_height_offset)
    rows = []
    base_poses = tuple(zip(args.base_x, args.base_y, args.base_height))
    for base_index, (base_x, base_y, base_height) in enumerate(base_poses):
        set_base_pose(runtime, base_x, base_y, base_height)
        target = contact_target(runtime, args.contact_height_offset, args.hand_center_backoff)
        for pitch_index, pitch in enumerate(args.hand_pitch):
            result = solve_pose(
                runtime, target, pitch,
                clearance=args.clearance,
                position_tolerance=args.position_tolerance,
                orientation_tolerance=args.orientation_tolerance,
                max_iterations=args.max_iterations,
                population=args.population,
                seed=args.seed * 1000 + base_index * 100 + pitch_index,
            )
            rows.append({
                "base_x": base_x,
                "base_y": base_y,
                "base_height": base_height,
                "hand_pitch": pitch,
                "target_position": target.tolist(),
                **result,
            })
    groups = candidate_groups(rows, base_poses)
    selected, candidate_edges = select_continuous_trajectory(
        runtime, groups,
        contact_height_offset=args.contact_height_offset,
        hand_center_backoff=args.hand_center_backoff,
        clearance=args.clearance,
        position_tolerance=args.position_tolerance,
        orientation_tolerance=args.orientation_tolerance,
        samples=args.edge_samples,
    )
    pd_validation = None
    if args.kinematic_base_pd and selected is not None:
        pd_runtime = make_geometry_runtime(args.seed, args.contact_height_offset)
        pd_validation = kinematic_base_pd_validation(
            pd_runtime, selected,
            contact_height_offset=args.contact_height_offset,
            hand_center_backoff=args.hand_center_backoff,
            clearance=args.clearance,
            position_tolerance=args.position_tolerance,
            orientation_tolerance=args.orientation_tolerance,
            initial_settle=args.pd_initial_settle,
            edge_duration=args.pd_edge_duration,
            max_joint_rate=args.pd_max_joint_rate,
            joint_tolerance=args.pd_joint_tolerance,
        )
    report = {
        "schema_version": 1,
        "seed": args.seed,
        "native_collisions": True,
        "base_positions": [list(pose) for pose in base_poses],
        "clearance_required": args.clearance,
        "position_tolerance": args.position_tolerance,
        "orientation_tolerance": args.orientation_tolerance,
        "contact_height_offset": args.contact_height_offset,
        "hand_center_backoff": args.hand_center_backoff,
        "rows": rows,
        "feasible_rows": sum(row["feasible"] for row in rows),
        "selected_trajectory": selected,
        "candidate_edges": candidate_edges,
        "kinematic_base_pd_validation": pd_validation,
        "source_sha256": {
            "scanner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "piper_box_runtime": hashlib.sha256(Path(make_episode.__code__.co_filename).read_bytes()).hexdigest(),
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({
        "rows": len(rows), "feasible_rows": report["feasible_rows"],
        "trajectory_static_safe": None if selected is None else selected["static_safe"],
        "kinematic_base_pd_passed": None if pd_validation is None else pd_validation["passed"],
        "output_json": str(args.output_json),
    }, allow_nan=False))


if __name__ == "__main__":
    main()