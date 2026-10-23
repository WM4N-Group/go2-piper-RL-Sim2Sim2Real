"""Scan MuJoCo contact margin and solver time constant for PIPER PUSH traces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from scan_piper_push_reachability import make_geometry_runtime


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--node-index", type=int, required=True)
    parser.add_argument("--margins", type=float, nargs="+", default=(0.0, 0.0005, 0.001, 0.002))
    parser.add_argument("--solref-times", type=float, nargs="+", default=(0.005, 0.01, 0.02, 0.04))
    parser.add_argument("--box-y", type=float, default=0.0)
    parser.add_argument("--box-yaw", type=float, default=0.0)
    args = parser.parse_args()
    if not args.trace_json.is_file() or args.output_json.exists():
        parser.error("Trace must exist and output must be new")
    if any(value < 0.0 for value in args.margins) or any(value <= 0.0 for value in args.solref_times):
        parser.error("Margins must be nonnegative and solref times must be positive")
    return args


def set_root(data, source):
    data.qpos[:7] = source["root_pose"]
    data.qvel[:6] = source["root_velocity"]


def run_case(trace, margin, solref_time, box_y, box_yaw):
    runtime = make_geometry_runtime(trace.get("seed", 210), trace.get("contact_height_offset", 0.03))
    data = runtime.data
    initial = trace["initial_state"]
    data.qpos[:7] = initial["root_pose"]
    data.qvel[:6] = initial["root_velocity"]
    data.qpos[runtime.joint_qpos_adr] = initial["joint_positions"]
    data.qvel[runtime.joint_dof_adr] = initial["joint_velocities"]
    box = data.joint("push_box_joint")
    box_state = trace["box_initial_state"]["root_pose"]
    box.qpos[:] = box_state
    box.qpos[1] = box_y
    box.qpos[3:7] = (np.cos(box_yaw / 2.0), 0.0, 0.0, np.sin(box_yaw / 2.0))
    box.qvel[:] = trace["box_initial_state"]["root_velocity"]
    box_body = runtime.model.body("push_box").id
    robot_geoms = np.flatnonzero(runtime.model.geom_bodyid != box_body)
    runtime.model.geom_margin[robot_geoms] = margin
    runtime.model.geom_solref[:, 0] = solref_time
    mujoco.mj_forward(runtime.model, data)
    runtime.target_history.clear()
    runtime.target_history.extend(
        np.asarray(trace["steps"][0]["target"], dtype=np.float64).copy()
        for _ in range(runtime.target_history.maxlen)
    )
    runtime.constraint_substeps = 1
    step_index = 0
    events = []

    def on_safety_step():
        nonlocal step_index
        forces = []
        for contact_index in range(data.ncon):
            contact = data.contact[contact_index]
            first = runtime.model.geom(contact.geom1).name
            second = runtime.model.geom(contact.geom2).name
            if "push_box" not in (first, second) or not (
                "piper_collision" in first or "piper_collision" in second
            ):
                continue
            wrench = np.zeros(6)
            mujoco.mj_contactForce(runtime.model, data, contact_index, wrench)
            forces.append(float(np.linalg.norm(wrench[:3])))
        if forces:
            events.append((step_index, max(forces)))
        if step_index < len(trace["steps"]):
            set_root(data, trace["steps"][step_index])
        step_index += 1

    runtime.on_safety_step = on_safety_step
    for start in range(0, len(trace["steps"]), runtime.decimation):
        set_root(data, trace["steps"][start])
        runtime._simulate_target(np.asarray(trace["steps"][start]["target"], dtype=np.float64))
    return {
        "margin": margin,
        "solref_time": solref_time,
        "box_y": box_y,
        "box_yaw": box_yaw,
        "first_contact_step": events[0][0] if events else None,
        "contact_event_count": len(events),
        "peak_contact_force": max((force for _, force in events), default=0.0),
    }


def main():
    args = parse_args()
    trace = json.loads(args.trace_json.read_text())
    if "box_initial_state" not in trace:
        raise ValueError("Solver scan requires box_initial_state in the trace")
    results = [
        run_case(trace, margin, solref_time, args.box_y, args.box_yaw)
        for margin in args.margins
        for solref_time in args.solref_times
    ]
    report = {
        "schema_version": 1,
        "diagnostic_only": True,
        "backend": "mujoco",
        "trace_sha256": hashlib.sha256(args.trace_json.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "node_index": args.node_index,
        "trace_steps": len(trace["steps"]),
        "results": results,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({"cases": len(results), "output_json": str(args.output_json)}))


if __name__ == "__main__":
    main()