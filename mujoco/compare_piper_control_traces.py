"""Locate divergence in provenance-matched MuJoCo and Isaac open-loop traces."""

import argparse
import json
from pathlib import Path

import numpy as np

from check_piper_startup import sha256


def compare(local, native, target_sha256):
    if native["trace_sha256"] != target_sha256:
        raise ValueError("Native replay does not match the requested target trace")
    if local.get("targets_sha256") not in (None, target_sha256):
        raise ValueError("Local replay does not match the requested target trace")
    for key in ("joint_names", "initial_state", "physics_dt"):
        if local[key] != native[key]:
            raise ValueError(f"Trace mismatch: {key}")
    measured = native.get("measured_initial_state")
    if measured is None:
        raise ValueError("Native trace lacks measured initial-state evidence")
    for key, value in measured.items():
        if not np.allclose(value, local["initial_state"][key], atol=5e-6, rtol=0.0):
            raise ValueError(f"Measured initial-state mismatch: {key}")
    if len(local["steps"]) != len(native["steps"]) or not local["steps"]:
        raise ValueError("Require equal nonempty step counts")
    metrics = {"root_position_m": [], "joint_position_rad": [], "joint_velocity_rad_s": [], "torque_nm": []}
    for left, right in zip(local["steps"], native["steps"]):
        if left["physics_step"] != right["physics_step"] or left["target"] != right["target"]:
            raise ValueError("Trace step or target mismatch")
        if abs(left["time"] - right["time"]) > 1e-8:
            raise ValueError("Trace timestamps mismatch")
        metrics["root_position_m"].append(float(np.linalg.norm(np.array(left["root_pose"][:3]) - right["root_pose"][:3])))
        for name, left_key, right_key in (
            ("joint_position_rad", "limited_positions", "solver_positions"),
            ("joint_velocity_rad_s", "limited_velocities", "solver_velocities"),
            ("torque_nm", "torque", "torque"),
        ):
            metrics[name].append(float(np.max(np.abs(np.array(left[left_key]) - right[right_key]))))
    thresholds = {"root_position_m": 0.01, "joint_position_rad": 0.05, "joint_velocity_rad_s": 1.0, "torque_nm": 1.0}
    first = {}
    for name, threshold in thresholds.items():
        indices = np.flatnonzero(np.array(metrics[name]) > threshold)
        first[name] = None if not len(indices) else {"physics_step": int(indices[0]), "time": local["steps"][indices[0]]["time"], "error": metrics[name][indices[0]]}
    checkpoints = []
    for index in (0, 3, 9, 19, 39, 99, len(local["steps"]) - 1):
        if index < len(local["steps"]):
            checkpoints.append({"physics_step": index, "time": local["steps"][index]["time"], **{key: values[index] for key, values in metrics.items()}})
    return {"thresholds": thresholds, "initial_state_tolerance": 5e-6, "first_divergence": first, "checkpoints": checkpoints}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-json", type=Path, required=True)
    parser.add_argument("--native-json", type=Path, required=True)
    parser.add_argument("--targets-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    if args.output_json.exists():
        parser.error("Require a new output")
    local = json.loads(args.local_json.read_text())
    native = json.loads(args.native_json.read_text())
    target_hash = sha256(args.targets_json)
    if local.get("targets_sha256") is None and sha256(args.local_json) != target_hash:
        parser.error("Closed-loop local trace must be the native target source")
    report = {"schema_version": 1, "diagnostic_only": True,
              "local_sha256": sha256(args.local_json), "native_sha256": sha256(args.native_json),
              "targets_sha256": target_hash, "analysis_sha256": sha256(Path(__file__)),
              **compare(local, native, target_hash)}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x") as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()