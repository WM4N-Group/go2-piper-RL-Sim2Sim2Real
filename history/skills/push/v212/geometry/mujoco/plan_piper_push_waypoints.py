"""Search and dynamically validate collision-safe PIPER PUSH arm waypoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.optimize import differential_evolution

from reconfigurable_navigation.piper_box_runtime import make_episode


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=500)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--static-clearance", type=float, default=0.03)
    parser.add_argument("--dynamic-clearance", type=float, default=0.015)
    parser.add_argument("--max-iterations", type=int, default=12000)
    parser.add_argument("--minimum-waypoints", type=int, default=8)
    parser.add_argument("--attempts", type=int, default=12)
    args = parser.parse_args()
    if args.output_json.exists() or args.max_iterations < 1 or args.minimum_waypoints < 2 or args.attempts < 1:
        parser.error("output must be new and iteration counts must be positive")
    if not 0.0 < args.dynamic_clearance <= args.static_clearance:
        parser.error("dynamic clearance must be positive and no greater than static clearance")
    return args


def arm_hand_position(runtime, joint_position):
    arm, data = runtime.arm, runtime.data
    saved = data.qpos[arm.arm_qpos].copy()
    data.qpos[arm.arm_qpos] = joint_position
    mujoco.mj_forward(runtime.model, data)
    position = arm.hand_position().copy()
    data.qpos[arm.arm_qpos] = saved
    mujoco.mj_forward(runtime.model, data)
    return position


def static_edge_is_safe(runtime, first, second, clearance):
    arm = runtime.arm
    samples = max(2, int(np.ceil(np.max(np.abs(second - first)) / 0.02)) + 1)
    return all(
        arm._minimum_protected_clearance(first + fraction * (second - first)) >= clearance
        for fraction in np.linspace(0.0, 1.0, samples)
    )


def find_high_approach(runtime, clearance):
    arm = runtime.arm
    target = arm.hand_target() + np.array([-0.18, 0.0, 0.25])

    def objective(candidate):
        gap = arm._minimum_protected_clearance(candidate)
        error = np.linalg.norm(arm_hand_position(runtime, candidate) - target)
        return error + 1_000_000.0 * max(0.0, clearance - gap) ** 2

    result = differential_evolution(
        objective,
        list(zip(arm.lower, arm.upper)),
        seed=57,
        popsize=16,
        maxiter=100,
        polish=True,
        tol=1e-5,
    )
    return result.x, target, float(result.fun)


def find_static_path(runtime, start, goal, clearance, max_iterations, minimum_waypoints, seed):
    arm = runtime.arm
    rng = np.random.default_rng(seed)
    span = arm.upper - arm.lower
    nodes, parents, depths = [start], [-1], [1]
    for iteration in range(max_iterations):
        sample = goal if rng.random() < 0.18 else rng.uniform(arm.lower, arm.upper)
        nearest_index = int(np.argmin([np.linalg.norm((node - sample) / span) for node in nodes]))
        nearest = nodes[nearest_index]
        delta = sample - nearest
        normalized_length = np.linalg.norm(delta / span)
        candidate = sample if normalized_length <= 0.065 else nearest + delta * (0.065 / normalized_length)
        if not static_edge_is_safe(runtime, nearest, candidate, clearance):
            continue
        nodes.append(candidate)
        parents.append(nearest_index)
        depths.append(depths[nearest_index] + 1)
        if depths[-1] >= minimum_waypoints - 1 and static_edge_is_safe(runtime, candidate, goal, clearance):
            nodes.append(goal)
            parents.append(len(nodes) - 2)
            index, path = len(nodes) - 1, []
            while index >= 0:
                path.append(nodes[index])
                index = parents[index]
            return list(reversed(path)), iteration + 1
    return None, max_iterations


def dynamically_validate(runtime, path, clearance):
    arm = runtime.arm
    minimum = float("inf")
    settled = []
    for index, waypoint in enumerate(path[1:], 1):
        for step in range(500):
            arm.gravity_data.qpos[:] = runtime.data.qpos
            arm.gravity_data.qvel.fill(0.0)
            mujoco.mj_forward(runtime.model, arm.gravity_data)
            compensated = waypoint + arm.gravity_data.qfrc_bias[arm.arm_dof] / runtime.kp[12:]
            target = runtime.default_qpos.copy()
            target[12:] = compensated
            runtime._simulate_target(target)
            current = arm._minimum_protected_clearance(runtime.data.qpos[arm.arm_qpos])
            minimum = min(minimum, current)
            if arm.protected_collision_active() or current < clearance:
                return False, minimum, settled
            if np.max(np.abs(runtime.data.qpos[arm.arm_qpos] - waypoint)) < 0.04 and np.max(np.abs(runtime.data.qvel[arm.arm_dof])) < 0.12:
                settled.append({"waypoint_index": index, "steps": step + 1})
                break
        else:
            return False, minimum, settled
    return True, minimum, settled


def main():
    args = parse_args()
    runtime = make_episode("push", args.policy, args.seed, push_ik_mode="pose", native_collisions=True)
    arm = runtime.arm
    start = runtime.data.qpos[arm.arm_qpos].copy()
    high_approach, target, objective = find_high_approach(runtime, args.static_clearance)
    candidates = []
    selected = None
    for attempt in range(args.attempts):
        candidate_runtime = make_episode("push", args.policy, args.seed, push_ik_mode="pose", native_collisions=True)
        path, iterations = find_static_path(
            candidate_runtime,
            candidate_runtime.data.qpos[candidate_runtime.arm.arm_qpos].copy(),
            high_approach,
            args.static_clearance,
            args.max_iterations,
            args.minimum_waypoints,
            20260924 + attempt,
        )
        passed = False
        minimum_dynamic_clearance = None
        settled = []
        if path is not None:
            passed, minimum_dynamic_clearance, settled = dynamically_validate(candidate_runtime, path, args.dynamic_clearance)
        candidate = {
            "attempt": attempt,
            "search_iterations": iterations,
            "path": None if path is None else [waypoint.tolist() for waypoint in path],
            "dynamic_validation_passed": passed,
            "minimum_dynamic_clearance": minimum_dynamic_clearance,
            "settled_waypoints": settled,
        }
        candidates.append(candidate)
        if selected is None or (
            candidate["minimum_dynamic_clearance"] is not None
            and (selected["minimum_dynamic_clearance"] is None or candidate["minimum_dynamic_clearance"] > selected["minimum_dynamic_clearance"])
        ):
            selected = candidate
        if passed:
            break
    report = {
        "schema_version": 1,
        "seed": args.seed,
        "static_clearance": args.static_clearance,
        "dynamic_clearance": args.dynamic_clearance,
        "minimum_waypoints": args.minimum_waypoints,
        "attempts": args.attempts,
        "high_approach_joint_position": high_approach.tolist(),
        "high_approach_hand_target": target.tolist(),
        "high_approach_hand_position": arm_hand_position(runtime, high_approach).tolist(),
        "high_approach_objective": objective,
        "candidates": candidates,
        "selected": selected,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({
        "attempts": len(candidates),
        "dynamic_validation_passed": selected["dynamic_validation_passed"],
        "minimum_dynamic_clearance": selected["minimum_dynamic_clearance"],
    }, indent=2))
    return 0 if selected["dynamic_validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())