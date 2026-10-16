"""Compare first-step foot geometry at Isaac and MuJoCo solver states."""

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from scan_piper_push_reachability import make_geometry_runtime


def foot_centers(model, data, joint_addresses, pose, positions):
    data.qpos[:7] = pose
    data.qpos[joint_addresses] = positions
    mujoco.mj_kinematics(model, data)
    return {foot: data.geom(foot).xpos.copy() for foot in ("FL", "FR", "RL", "RR")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-json", type=Path, required=True)
    parser.add_argument("--isaac-json", type=Path, required=True)
    parser.add_argument("--mujoco-json", type=Path, required=True)
    args = parser.parse_args()

    path_bytes = args.path_json.read_bytes()
    path = json.loads(path_bytes)
    isaac = json.loads(args.isaac_json.read_text())
    mujoco_report = json.loads(args.mujoco_json.read_text())
    if hashlib.sha256(path_bytes).hexdigest() != mujoco_report["path_sha256"]:
        raise ValueError("Path hash differs from MuJoCo trace")
    if isaac["joint_names"] != mujoco_report["joint_names"]:
        raise ValueError("Joint orders differ")
    if isaac["physics_dt"] != mujoco_report["physics_dt"]:
        raise ValueError("Physics time steps differ")
    runtime = make_geometry_runtime(path["seed"], path["contact_height_offset"])
    model = runtime.model
    data = mujoco.MjData(model)
    isaac_step = isaac["steps"][0]
    mujoco_step = mujoco_report["steps"][0]
    initial_isaac = isaac["measured_initial_state"]
    initial_mujoco = mujoco_report["initial_state"]
    velocity_delta = np.asarray(isaac_step["solver_velocities"]) - np.asarray(
        mujoco_step["solver_velocities_before_projection"]
    )
    torque_delta = np.asarray(isaac_step["torque_before_step"]) - np.asarray(mujoco_step["torque"])
    print(json.dumps({
        "initial_joint_max_delta_rad": float(np.max(np.abs(
            np.asarray(initial_isaac["joint_positions"]) - np.asarray(initial_mujoco["joint_positions"])
        ))),
        "initial_root_position_max_delta_mm": float(np.max(np.abs(
            np.asarray(initial_isaac["root_pose"][:3]) - np.asarray(initial_mujoco["root_pose"][:3])
        )) * 1000),
        "torque_max_delta_nm": float(np.max(np.abs(torque_delta))),
        "velocity_deltas_rad_s": dict(zip(isaac["joint_names"], velocity_delta.tolist())),
    }))
    isaac_centers = foot_centers(
        model, data, runtime.joint_qpos_adr,
        isaac_step["solver_root_pose"], isaac_step["solver_positions"],
    )
    mujoco_centers = foot_centers(
        model, data, runtime.joint_qpos_adr,
        mujoco_step["solver_root_pose"], mujoco_step["solver_positions_before_projection"],
    )
    joints_only_centers = foot_centers(
        model, data, runtime.joint_qpos_adr,
        mujoco_step["solver_root_pose"], isaac_step["solver_positions"],
    )
    post_step_distances = {
        contact["geom2"]: contact["distance"]
        for contact in mujoco_step["foot_contacts_post_step"]
        if contact["geom1"] == "floor"
    }
    for foot in isaac_centers:
        measured_isaac = np.asarray(isaac_step["foot_spheres_before_root_restore"][foot]["center_w"])
        measured_mujoco_z = post_step_distances[foot] + model.geom(foot).size[0]
        print(json.dumps({
            "foot": foot,
            "kinematic_z_delta_mm": float((isaac_centers[foot][2] - mujoco_centers[foot][2]) * 1000),
            "joint_z_delta_mm": float((joints_only_centers[foot][2] - mujoco_centers[foot][2]) * 1000),
            "root_z_delta_mm": float((isaac_centers[foot][2] - joints_only_centers[foot][2]) * 1000),
            "measured_z_delta_mm": float((measured_isaac[2] - measured_mujoco_z) * 1000),
            "isaac_model_residual_mm": ((isaac_centers[foot] - measured_isaac) * 1000).tolist(),
            "mujoco_model_z_residual_mm": float((mujoco_centers[foot][2] - measured_mujoco_z) * 1000),
        }))


if __name__ == "__main__":
    main()