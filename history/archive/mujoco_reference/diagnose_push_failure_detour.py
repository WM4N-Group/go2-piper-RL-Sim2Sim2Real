"""Search a static arm detour from one recorded PUSH self-collision failure."""

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
from scipy.spatial.transform import Rotation

from reconfigurable_navigation.piper_box_runtime import make_episode
from reconfigurable_navigation.piper_locomotion_runtime import JOINT_NAMES


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def from_wxyz(quaternion):
    return Rotation.from_quat(np.asarray(quaternion)[[1, 2, 3, 0]])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env", type=int, default=0)
    parser.add_argument("--start-time", type=float, default=7.5)
    parser.add_argument("--goal-kind", choices=("observed-terminal", "source-command"), default="observed-terminal")
    parser.add_argument("--hand-pitch", type=float)
    parser.add_argument("--seed", type=int, default=1708)
    parser.add_argument("--clearance", type=float, default=0.015)
    parser.add_argument("--box-clearance", type=float, default=0.005)
    parser.add_argument("--orientation-tolerance", type=float, default=0.35)
    parser.add_argument("--orientation-weight", type=float, default=0.02)
    parser.add_argument("--candidate-count", type=int, default=4)
    parser.add_argument("--max-iterations", type=int, default=90)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    if args.candidate_count < 1 or args.max_iterations < 1 or not np.isfinite(args.orientation_weight) or args.orientation_weight <= 0.0:
        parser.error("Search budget and orientation weight must be positive")
    if args.goal_kind == "source-command" and (args.hand_pitch is None or not np.isfinite(args.hand_pitch)):
        parser.error("Source-command goal requires a finite --hand-pitch from the candidate contract")
    if not np.isfinite(args.box_clearance) or args.box_clearance < 0.005:
        parser.error("Planning box clearance must be finite and at least the 5mm collision gate")
    report = json.loads(args.report.read_text())
    history = next(row["pre_step_samples"] for row in report["failure_histories"] if row["env_id"] == args.env)
    start = min(history, key=lambda row: abs(row["elapsed_seconds"] - args.start_time))
    goal = history[-1]
    terminal = next(row for row in report["terminal_states"] if row["env_id"] == args.env)
    with patch("reconfigurable_navigation.climb_runtime.torch.jit.load", return_value=torch.nn.Identity()):
        runtime = make_episode("push", "geometry-only.pt", args.seed, push_ik_mode="pose", native_collisions=True)
    model, data, arm = runtime.model, runtime.data, runtime.arm
    source_joints = dict(zip(report["joint_names"], start.get("full_joint_position", terminal["robot_joint_position"])))
    data.qpos[:3] = start["robot_position"]
    data.qpos[3:7] = start["robot_quaternion"]
    data.qpos[runtime.joint_qpos_adr] = [source_joints[name] for name in JOINT_NAMES]
    data.qpos[arm.arm_qpos] = start["arm_joint_position"]
    data.joint("push_box_joint").qpos[:3] = start["box_position"]
    data.joint("push_box_joint").qpos[3:7] = start["box_quaternion"]
    data.qvel[:] = 0.0
    if "full_joint_velocity" in start:
        source_velocity = dict(zip(report["joint_names"], start["full_joint_velocity"]))
        data.qvel[:3] = start["robot_velocity"]
        data.qvel[3:6] = start["robot_angular_velocity"]
        data.qvel[runtime.joint_dof_adr] = [source_velocity[name] for name in JOINT_NAMES]
    mujoco.mj_forward(model, data)

    initial = np.asarray(start["arm_joint_position"])
    if args.goal_kind == "source-command":
        target_position = np.asarray(goal["arm_command_position"])
        target_rotation = from_wxyz(goal["box_quaternion"]) * Rotation.from_euler("y", args.hand_pitch)
    else:
        target_position = np.asarray(goal["hand_position"])
        target_rotation = from_wxyz(goal["hand_quaternion"])
    target_xyzw = target_rotation.as_quat()
    target_wxyz = target_xyzw[[3, 0, 1, 2]]
    box_geom = arm.box_geom
    base_state = data.qpos.copy()
    initial_velocity = data.qvel.copy()
    source_target = dict(zip(report["joint_names"], start.get("full_joint_position_target", terminal["robot_joint_position_target"])))
    def metrics(joints):
        data.qpos[arm.arm_qpos] = joints
        mujoco.mj_forward(model, data)
        hand_error = float(np.linalg.norm(arm.hand_position() - target_position))
        rotation = Rotation.from_matrix(data.xmat[arm.hand_body].reshape(3, 3))
        angle_error = float((target_rotation.inv() * rotation).magnitude())
        protected = arm._minimum_protected_clearance(joints)
        data.qpos[arm.arm_qpos] = joints
        mujoco.mj_forward(model, data)
        box_clearance = min(float(mujoco.mj_geomDistance(model, data, geom, box_geom, 1.0, None)) for geom in arm.collision_arm_geoms)
        return hand_error, angle_error, protected, box_clearance

    def safe(joints):
        if np.any(joints < arm.lower) or np.any(joints > arm.upper):
            return False
        _, _, protected, box_clearance = metrics(joints)
        return protected >= args.clearance and box_clearance >= args.box_clearance

    def edge(first, second):
        steps = max(1, int(np.ceil(np.max(np.abs(second - first)) / 0.02)))
        minimum_protected = float("inf")
        minimum_box = float("inf")
        for alpha in np.linspace(0.0, 1.0, steps + 1):
            _, _, protected, box = metrics(first * (1 - alpha) + second * alpha)
            minimum_protected = min(minimum_protected, protected)
            minimum_box = min(minimum_box, box)
            if protected < args.clearance or box < args.box_clearance:
                return False, minimum_protected, minimum_box
        return True, minimum_protected, minimum_box

    if not safe(initial):
        raise RuntimeError("Recorded start is already unsafe under the selected static geometry")

    def objective(joints):
        position, angle, protected, box = metrics(joints)
        return position + args.orientation_weight * angle + 100.0 * max(0.0, args.clearance + 0.005 - protected) + 100.0 * max(0.0, args.box_clearance + 0.005 - box)

    bounds = list(zip(arm.lower, arm.upper))
    candidates = []
    for index in range(args.candidate_count):
        result = differential_evolution(objective, bounds, seed=args.seed + index, maxiter=args.max_iterations, popsize=8, polish=True)
        joint = np.asarray(result.x)
        position, angle, protected, box = metrics(joint)
        candidates.append({"joint": joint.tolist(), "position_error": position, "orientation_error": angle,
                           "protected_clearance": protected, "box_clearance": box, "objective": float(result.fun)})
    feasible = [row for row in candidates if row["position_error"] <= 0.025 and row["orientation_error"] <= args.orientation_tolerance
                and row["protected_clearance"] >= args.clearance and row["box_clearance"] >= args.box_clearance]
    selected = min(feasible, key=lambda row: row["objective"]) if feasible else None

    path = None
    if selected is not None:
        target = np.asarray(selected["joint"])
        rng = np.random.default_rng(args.seed)
        trees = [[{"joint": initial, "parent": -1}], [{"joint": target, "parent": -1}]]
        joins = None
        for iteration in range(2000):
            side = iteration % 2
            tree, other = trees[side], trees[1 - side]
            sample = other[0]["joint"] if rng.random() < 0.2 else rng.uniform(arm.lower, arm.upper)
            parent = min(range(len(tree)), key=lambda i: np.linalg.norm(tree[i]["joint"] - sample))
            delta = sample - tree[parent]["joint"]
            if np.max(np.abs(delta)) < 1e-9:
                continue
            candidate = tree[parent]["joint"] + delta * min(1.0, 0.18 / np.max(np.abs(delta)))
            valid, _, _ = edge(tree[parent]["joint"], candidate)
            if not valid:
                continue
            tree.append({"joint": candidate, "parent": parent})
            nearest = min(range(len(other)), key=lambda i: np.linalg.norm(other[i]["joint"] - candidate))
            valid, _, _ = edge(candidate, other[nearest]["joint"])
            if valid:
                joins = (side, len(tree) - 1, nearest)
                break
        if joins is not None:
            side, first_index, second_index = joins
            def branch(tree, index):
                indices = []
                while index >= 0:
                    indices.append(tree[index]["joint"])
                    index = tree[index]["parent"]
                return indices[::-1]
            first_branch = branch(trees[side], first_index)
            second_branch = branch(trees[1 - side], second_index)
            nodes = first_branch + second_branch[::-1] if side == 0 else second_branch + first_branch[::-1]
            edges = [edge(first, second) for first, second in zip(nodes, nodes[1:])]
            path = {"nodes": [node.tolist() for node in nodes], "edges": [
                {"safe": valid, "minimum_protected_clearance": protected, "minimum_box_clearance": box}
                for valid, protected, box in edges], "iterations": iteration + 1}
    data.qpos[:] = base_state
    mujoco.mj_forward(model, data)
    result = {"schema_version": 1, "kind": "static_fixed_base_diagnostic", "source_report_sha256": sha256(args.report),
              "script_sha256": sha256(Path(__file__)), "runtime_source_sha256": sha256(Path(make_episode.__code__.co_filename)),
              "env": args.env, "start_time": start["elapsed_seconds"], "goal_time": goal["elapsed_seconds"],
              "goal_kind": args.goal_kind, "hand_pitch": args.hand_pitch,
              "base_qpos": base_state.tolist(), "base_qvel": initial_velocity.tolist(),
              "source_leg_target": [source_target[name] for name in JOINT_NAMES[:12]],
              "minimum_required_clearance": args.clearance,
              "minimum_required_box_clearance": args.box_clearance,
              "orientation_tolerance": args.orientation_tolerance,
              "orientation_weight": args.orientation_weight,
              "candidate_count": args.candidate_count, "max_iterations": args.max_iterations,
              "start_joint": initial.tolist(), "target_hand_position": target_position.tolist(),
              "target_hand_quaternion": target_wxyz.tolist(), "candidates": candidates,
              "selected_candidate": selected, "path": path,
              "limitations": "Fixed base and legs, static MuJoCo geometry only; no PD, torque, moving-base or full-task validation."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"selected": selected is not None, "path_found": path is not None,
                      "nodes": None if path is None else len(path["nodes"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
