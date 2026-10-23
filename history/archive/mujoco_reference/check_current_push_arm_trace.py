"""Compare current Isaac PUSH arm poses with the matching MuJoCo asset."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from reconfigurable_navigation.piper_box_runtime import make_episode
from reconfigurable_navigation.piper_robot_profile import COLLISION_PROFILE_PATH, PROFILE_PATH


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-report", type=Path, required=True)
    parser.add_argument("--expected-isaac-sha256", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--expected-policy-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trace-source", choices=("failure-history", "env0"), default="failure-history")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path")
    if sha256(args.isaac_report) != args.expected_isaac_sha256:
        parser.error("Isaac report SHA256 mismatch")
    if sha256(args.policy) != args.expected_policy_sha256:
        parser.error("Policy SHA256 mismatch")

    isaac = json.loads(args.isaac_report.read_text())
    if isaac["task"] != "GO2-PIPER-Box-Push-Tracking-Play" or isaac["failure_history_arm_joint_names"] != [
        f"joint{index}" for index in range(1, 7)
    ]:
        parser.error("Unexpected PUSH task or arm joint order")
    runtime = make_episode(
        "push", args.policy, 3701, push_ik_mode="pose", native_collisions=True,
        push_hand_pitch=0.6, push_height_offset=0.03, push_current_contract=True,
    )
    model, data = runtime.model, runtime.data
    hand = model.body("end_effector").id
    base_body = model.body("base_link").id
    base_geoms = [geom for geom in runtime.arm.collision_protected_geoms
                  if model.geom_bodyid[geom] == base_body]
    if not base_geoms:
        parser.error("No source-matched base collision geometry")
    box = data.joint("push_box_joint").qpos
    if args.trace_source == "env0":
        samples = isaac["trace_env0"]
        required = {"robot_quaternion", "robot_joint_position", "hand_quaternion"}
        if not samples or any(not required.issubset(sample) for sample in samples):
            parser.error("env0 trace requires root, joint, and hand poses on every sample")
        episodes = [(isaac["inspect_env_index"], samples)]
    else:
        episodes = [(failure["env_id"], failure["pre_step_samples"])
                    for failure in isaac["failure_histories"]]
    comparisons = []
    for env_id, episode_samples in episodes:
        for sample in episode_samples:
            data.qpos[:3] = sample["robot_position"]
            data.qpos[3:7] = sample["robot_quaternion"]
            if args.trace_source == "env0":
                for name, position in zip(isaac["joint_names"], sample["robot_joint_position"], strict=True):
                    data.qpos[model.joint(name).qposadr] = position
            else:
                data.qpos[runtime.arm.arm_qpos] = sample["arm_joint_position"]
            box[:3] = sample["box_position"]
            box[3:7] = sample["box_quaternion"]
            data.qvel.fill(0.0)
            mujoco.mj_forward(model, data)
            measured = runtime.arm.hand_position()
            expected = np.asarray(sample["hand_position"])
            quaternion = data.xquat[hand]
            expected_quaternion = np.asarray(sample["hand_quaternion"])
            angle = 2.0 * np.arccos(np.clip(abs(np.dot(quaternion, expected_quaternion)), 0.0, 1.0))
            protected_clearance = None
            protected_geoms = None
            body_origin_clearance = None
            body_origin_pair = None
            base_distance, arm_geom, base_geom = min(
                (mujoco.mj_geomDistance(model, data, arm, base, 1.0, None), arm, base)
                for arm in runtime.arm.collision_arm_geoms for base in base_geoms
            )
            if args.trace_source == "env0":
                distance, arm_geom, protected_geom = min(
                    (mujoco.mj_geomDistance(model, data, arm, protected, 1.0, None), arm, protected)
                    for arm in runtime.arm.collision_arm_geoms
                    for protected in runtime.arm.collision_protected_geoms
                )
                protected_clearance = float(distance)
                protected_geoms = [model.geom(arm_geom).name, model.geom(protected_geom).name]
                arm_bodies = ("link2", "link3", "link4", "link5", "link6", "end_effector")
                protected_bodies = ("base_link",) + tuple(
                    f"{leg}_{segment}" for leg in ("FL", "FR", "RL", "RR")
                    for segment in ("hip", "thigh", "calf", "foot")
                )
                body_origin_clearance, arm_body, protected_body = min(
                    (float(np.linalg.norm(data.xpos[model.body(arm_name).id]
                                          - data.xpos[model.body(protected_name).id])), arm_name, protected_name)
                    for arm_name in arm_bodies for protected_name in protected_bodies
                )
                body_origin_pair = [arm_body, protected_body]
            comparisons.append({
                "env_id": env_id,
                "time_s": (sample["step"] * isaac["failure_history_step_dt"] if args.trace_source == "env0"
                           else sample["elapsed_seconds"]),
                "isaac_hand_position": expected.tolist(),
                "mujoco_hand_position": measured.tolist(),
                "hand_position_error_m": float(np.linalg.norm(measured - expected)),
                "hand_orientation_error_rad": float(angle),
                "isaac_valid_contact": sample["hand_contact"] if args.trace_source == "env0" else sample["hand_contact_valid"],
                "mujoco_protected_clearance_m": protected_clearance,
                "mujoco_nearest_protected_geoms": protected_geoms,
                "mujoco_body_origin_clearance_m": body_origin_clearance,
                "mujoco_nearest_body_origin_pair": body_origin_pair,
                "mujoco_arm_base_signed_distance_m": float(base_distance),
                "mujoco_nearest_arm_base_geoms": [model.geom(arm_geom).name, model.geom(base_geom).name],
            })

    position_errors = np.array([entry["hand_position_error_m"] for entry in comparisons])
    orientation_errors = np.array([entry["hand_orientation_error_rad"] for entry in comparisons])
    report = {
        "scope": ("Static replay of recorded Isaac PUSH env0 full joint poses; no matched dynamics or acceptance"
                  if args.trace_source == "env0" else
                  "Static replay of recorded Isaac PUSH failure-history root and arm poses; no matched dynamics or acceptance"),
        "trace_source": args.trace_source,
        "isaac_report_sha256": sha256(args.isaac_report),
        "policy_sha256": sha256(args.policy),
        "mujoco_xml_sha256": sha256(ROOT / "robots/go2_piper/go2piper.xml"),
        "mujoco_profile_sha256": sha256(PROFILE_PATH),
        "mujoco_collision_profile_sha256": sha256(COLLISION_PROFILE_PATH),
        "script_sha256": sha256(Path(__file__)),
        "failure_episodes": len(isaac["failure_histories"]),
        "sample_count": len(comparisons),
        "contact_sample_count": sum(entry["isaac_valid_contact"] for entry in comparisons),
        "minimum_mujoco_protected_clearance_m": (
            min(entry["mujoco_protected_clearance_m"] for entry in comparisons)
            if args.trace_source == "env0" else None
        ),
        "contact_samples_below_15mm": (
            sum(entry["isaac_valid_contact"] and entry["mujoco_protected_clearance_m"] < 0.015
                for entry in comparisons) if args.trace_source == "env0" else None
        ),
        "arm_base_audit": {
            "scope": "Source-matched static MuJoCo collision hulls; no PhysX contact or visual-mesh depth measurement",
            "sampled_interval_s": [comparisons[0]["time_s"], comparisons[-1]["time_s"]],
            "minimum_signed_distance_m": min(entry["mujoco_arm_base_signed_distance_m"] for entry in comparisons),
            "negative_samples": sum(entry["mujoco_arm_base_signed_distance_m"] < 0 for entry in comparisons),
            "negative_legal_contact_samples": sum(entry["isaac_valid_contact"]
                                                  and entry["mujoco_arm_base_signed_distance_m"] < 0
                                                  for entry in comparisons),
            "first_negative_time_s": next((entry["time_s"] for entry in comparisons
                                            if entry["mujoco_arm_base_signed_distance_m"] < 0), None),
        },
        "max_hand_position_error_m": float(position_errors.max()),
        "mean_hand_position_error_m": float(position_errors.mean()),
        "max_hand_orientation_error_rad": float(orientation_errors.max()),
        "mean_hand_orientation_error_rad": float(orientation_errors.mean()),
        "comparisons": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in (
        "sample_count", "max_hand_position_error_m", "max_hand_orientation_error_rad",
    )}))


if __name__ == "__main__":
    main()
