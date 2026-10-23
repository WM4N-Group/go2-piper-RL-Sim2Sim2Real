"""Check the Isaac CLIMB leg PD law against post-physics substep samples."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-substeps", type=Path, required=True)
    parser.add_argument("--expected-substeps-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    source_hash = sha256(args.isaac_substeps)
    if source_hash != args.expected_substeps_sha256:
        parser.error("Isaac substep source SHA256 mismatch")
    source = json.loads(args.isaac_substeps.read_text())
    rows = source["trace"]
    names = source["joint_names"]
    if (len(rows) != 240 or source["physics_dt"] != 0.005
            or source["control_decimation"] != 4
            or [(row["step"], row["substep"]) for row in rows]
            != [(step, substep) for step in range(200, 260) for substep in range(4)]):
        parser.error("Substep timing contract mismatch")
    leg_ids = [index for index, name in enumerate(names)
               if name.endswith(("_hip_joint", "_thigh_joint", "_calf_joint"))]
    if len(leg_ids) != 12:
        parser.error("Expected 12 leg joints")
    position = np.asarray([row["joint_position"] for row in rows])[:, leg_ids]
    velocity = np.asarray([row["joint_velocity"] for row in rows])[:, leg_ids]
    target = np.asarray([row["joint_position_target"] for row in rows])[:, leg_ids]
    effort = np.asarray([row["applied_torque"] for row in rows])[:, leg_ids]
    post_state_error = effort - (30.0 * (target - position) - 0.6 * velocity)
    # scene.update records after each physics step; the actuator used the previous state.
    pre_state_error = effort[1:] - (30.0 * (target[1:] - position[:-1]) - 0.6 * velocity[:-1])
    report = {
        "kind": "isaac_climb_substep_actuation_phase_check",
        "scope": "239 aligned source substeps; offline torque identity, not MuJoCo validation",
        "source_substeps_sha256": source_hash,
        "script_sha256": sha256(Path(__file__)),
        "leg_joint_names": [names[index] for index in leg_ids],
        "post_state_rmse_nm": float(np.sqrt(np.mean(post_state_error**2))),
        "pre_state_rmse_nm": float(np.sqrt(np.mean(pre_state_error**2))),
        "pre_state_max_abs_error_nm": float(np.max(np.abs(pre_state_error))),
        "pre_state_rmse_by_joint_nm": np.sqrt(np.mean(pre_state_error**2, axis=0)).tolist(),
        "target_change_boundaries": int((np.max(np.abs(np.diff(target, axis=0)), axis=1) > 1e-7).sum()),
        "limitations": [
            "The first sample has no preceding recorded state and is excluded from the aligned fit.",
            "Recorded joint_position_target matches the effective target in this window; the reset delay selection is not independently recovered.",
            "The fit does not establish contact-model or full StageGuidance agreement.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("post_state_rmse_nm", "pre_state_rmse_nm", "pre_state_max_abs_error_nm")}))


if __name__ == "__main__":
    main()
