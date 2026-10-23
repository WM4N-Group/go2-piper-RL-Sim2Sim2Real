"""Scan PIPER PUSH hand-box contact timing over box pose perturbations."""

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
    parser.add_argument("--y-offsets", type=float, nargs="+", default=(-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03))
    parser.add_argument("--yaw-values", type=float, nargs="+", default=(-0.04, -0.02, 0.0, 0.02, 0.04))
    args = parser.parse_args()
    if not args.trace_json.is_file() or args.output_json.exists():
        parser.error("Trace must exist and output must be new")
    if not args.y_offsets or not args.yaw_values:
        parser.error("At least one y offset and yaw value are required")
    return args


def set_root(data, source):
    data.qpos[:7] = source["root_pose"]
    data.qvel[:6] = source["root_velocity"]


def run_case(trace, y_offset, yaw):
    runtime = make_geometry_runtime(trace.get("seed", 210), trace.get("contact_height_offset", 0.03))
    data = runtime.data
    initial = trace["initial_state"]
    data.qpos[:7] = initial["root_pose"]
    data.qvel[:6] = initial["root_velocity"]
    data.qpos[runtime.joint_qpos_adr] = initial["joint_positions"]
    data.qvel[runtime.joint_dof_adr] = initial["joint_velocities"]
    box_state = trace["box_initial_state"]
    box = data.joint("push_box_joint")
    box.qpos[:] = box_state["root_pose"]
    box.qpos[1] = y_offset
    box.qpos[3:7] = (np.cos(yaw / 2.0), 0.0, 0.0, np.sin(yaw / 2.0))
    box.qvel[:] = box_state["root_velocity"]
    mujoco.mj_forward(runtime.model, data)
    runtime.target_history.clear()
    runtime.target_history.extend(
        np.asarray(trace["steps"][0]["target"], dtype=np.float64).copy()
        for _ in range(runtime.target_history.maxlen)
    )
    runtime.constraint_substeps = 1
    step_index = 0
    contact_steps = []
    contact_forces = []

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
            contact_steps.append(step_index)
            contact_forces.append(max(forces))
        if step_index < len(trace["steps"]):
            set_root(data, trace["steps"][step_index])
        step_index += 1

    runtime.on_safety_step = on_safety_step
    for start in range(0, len(trace["steps"]), runtime.decimation):
        set_root(data, trace["steps"][start])
        runtime._simulate_target(np.asarray(trace["steps"][start]["target"], dtype=np.float64))
    return {
        "y_offset": y_offset,
        "yaw": yaw,
        "first_contact_step": contact_steps[0] if contact_steps else None,
        "contact_event_count": len(contact_steps),
        "peak_contact_force": max(contact_forces, default=0.0),
    }


def main():
    args = parse_args()
    trace = json.loads(args.trace_json.read_text())
    if "box_initial_state" not in trace:
        raise ValueError("Contact timing scan requires box_initial_state in the trace")
    results = [
        run_case(trace, y_offset, yaw)
        for y_offset in args.y_offsets
        for yaw in args.yaw_values
    ]
    report = {
        "schema_version": 1,
        "diagnostic_only": True,
        "backend": "mujoco",
        "trace_sha256": hashlib.sha256(args.trace_json.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "node_index": args.node_index,
        "trace_steps": len(trace["steps"]),
        "y_offsets": list(args.y_offsets),
        "yaw_values": list(args.yaw_values),
        "results": results,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({"cases": len(results), "output_json": str(args.output_json)}))


if __name__ == "__main__":
    main()