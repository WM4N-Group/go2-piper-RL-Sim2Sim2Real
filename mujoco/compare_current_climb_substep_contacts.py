"""Compare source CLIMB substep poses with MuJoCo foot contact geometry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from reconfigurable_navigation.piper_box_runtime import make_episode
from reconfigurable_navigation.piper_locomotion_runtime import JOINT_NAMES
from reconfigurable_navigation.piper_robot_profile import COLLISION_PROFILE_PATH, PROFILE_PATH


LEGS = ("FL", "FR", "RL", "RR")
ROOT = Path(__file__).resolve().parent


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
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--stage-bank", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    source_hash = sha256(args.isaac_substeps)
    if source_hash != args.expected_substeps_sha256:
        parser.error("Isaac substep source SHA256 mismatch")
    plan = json.loads((args.candidate / "plan.json").read_text())
    if sha256(args.policy) != plan["actor_sha256"] or sha256(args.stage_bank) != plan["stage_bank_sha256"]:
        parser.error("Frozen actor or stage bank does not match candidate")
    source = json.loads(args.isaac_substeps.read_text())
    names = source["joint_names"]
    trace = source["trace"]
    if (source["seed"] != 27302 or source["physics_dt"] != 0.005
            or source["control_decimation"] != 4 or len(names) != 18 or len(trace) != 240):
        parser.error("Substep source contract mismatch")
    if [(row["step"], row["substep"]) for row in trace] != [
        (step, substep) for step in range(200, 260) for substep in range(4)
    ]:
        parser.error("Substep order mismatch")
    if any("root_quaternion" not in row or "root_angular_velocity" not in row for row in trace):
        parser.error("Exact root pose and velocity are required for every substep")

    runtime = make_episode("climb", args.policy, 27302, native_collisions=True)
    model, data = runtime.model, runtime.data
    foot_geoms = [model.geom(leg).id for leg in LEGS]
    foot_bodies = [model.body(f"{leg}_foot").id for leg in LEGS]
    terrain_geoms = sorted(runtime.terrain_geom_ids)
    if not terrain_geoms:
        parser.error("No terrain collision geometry in MuJoCo runtime")
    ordered = [names.index(name) for name in JOINT_NAMES]
    wrench = np.zeros(6)
    rows = []
    for sample in trace:
        data.qpos[:7] = [*sample["root_position"], *sample["root_quaternion"]]
        data.qvel[:6] = [*sample["root_velocity"], *sample["root_angular_velocity"]]
        data.qpos[runtime.joint_qpos_adr] = np.asarray(sample["joint_position"])[ordered]
        data.qvel[runtime.joint_dof_adr] = np.asarray(sample["joint_velocity"])[ordered]
        data.ctrl[:] = np.asarray(sample["applied_torque"])[ordered]
        mujoco.mj_forward(model, data)
        gaps = [min(float(mujoco.mj_geomDistance(model, data, foot, terrain, 1.0, None))
                    for terrain in terrain_geoms) for foot in foot_geoms]
        loads = np.zeros(4)
        contacts = [0] * 4
        for contact_index, contact in enumerate(data.contact[:data.ncon]):
            first, second = int(contact.geom1), int(contact.geom2)
            foot = second if first in terrain_geoms else first if second in terrain_geoms else None
            if foot not in foot_geoms:
                continue
            index = foot_geoms.index(foot)
            mujoco.mj_contactForce(model, data, contact_index, wrench)
            loads[index] += abs(float((contact.frame.reshape(3, 3).T @ wrench[:3])[2]))
            contacts[index] += 1
        source_loads = np.asarray(sample["foot_contact_force_z"])
        rows.append({
            "step": sample["step"], "substep": sample["substep"],
            "isaac_foot_force_z_n": source_loads.tolist(),
            "mujoco_static_foot_force_z_n": loads.tolist(),
            "mujoco_foot_terrain_gap_m": gaps,
            "mujoco_contact_count": contacts,
            "foot_body_position_error_m": np.linalg.norm(
                data.xpos[foot_bodies] - np.asarray(sample["feet_position"]), axis=1).tolist(),
        })
    source_forces = np.asarray([row["isaac_foot_force_z_n"] for row in rows])
    mujoco_forces = np.asarray([row["mujoco_static_foot_force_z_n"] for row in rows])
    gaps = np.asarray([row["mujoco_foot_terrain_gap_m"] for row in rows])
    report = {
        "kind": "source_pose_static_contact_diagnostic",
        "scope": "240 source-matched poses; static contact activation, not CLIMB replay or success rate",
        "source_substeps_sha256": source_hash,
        "candidate_plan_sha256": sha256(args.candidate / "plan.json"),
        "actor_sha256": sha256(args.policy),
        "stage_bank_sha256": sha256(args.stage_bank),
        "mujoco_xml_sha256": sha256(ROOT / "robots/go2_piper/go2piper.xml"),
        "mujoco_profile_sha256": sha256(PROFILE_PATH),
        "mujoco_collision_profile_sha256": sha256(COLLISION_PROFILE_PATH),
        "script_sha256": sha256(Path(__file__)),
        "terrain_geoms": [model.geom(geom).name for geom in terrain_geoms],
        "loaded_over_2n": {
            "isaac": (source_forces > 2.0).sum(axis=0).tolist(),
            "mujoco_static": (mujoco_forces > 2.0).sum(axis=0).tolist(),
        },
        "source_loaded_positive_gap": ((source_forces > 2.0) & (gaps > 0.0)).sum(axis=0).tolist(),
        "gap_min_m": gaps.min(axis=0).tolist(),
        "gap_max_m": gaps.max(axis=0).tolist(),
        "maximum_foot_body_position_error_m": max(max(row["foot_body_position_error_m"]) for row in rows),
        "rows": rows,
        "limitations": [
            "mj_forward at each Isaac pose does not restore MuJoCo constraint solver history.",
            "MuJoCo static contact forces are not directly comparable to dynamic PhysX contact forces.",
            "No StageGuidance, closed-loop actuation or complete-stage rollout is run.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"rows": len(rows), "loaded_over_2n": report["loaded_over_2n"],
                      "source_loaded_positive_gap": report["source_loaded_positive_gap"]}))


if __name__ == "__main__":
    main()
