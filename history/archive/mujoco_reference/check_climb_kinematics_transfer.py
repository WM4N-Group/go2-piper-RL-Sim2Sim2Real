"""Compare frozen CLIMB leg kinematics with the matching MuJoCo model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy

import mujoco
import numpy as np
import torch

from reconfigurable_navigation.piper_box_runtime import make_episode
from reconfigurable_navigation.piper_locomotion_runtime import JOINT_NAMES
from reconfigurable_navigation.piper_robot_profile import COLLISION_PROFILE_PATH, PROFILE_PATH


LEGS = ("FL", "FR", "RL", "RR")
JOINT_PARTS = ("hip", "thigh", "calf")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--stage-bank", required=True, type=Path)
    parser.add_argument("--numeric-geometry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=28302)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new diagnostic output path")

    plan = json.loads((args.candidate / "plan.json").read_text())
    numeric = json.loads(args.numeric_geometry.read_text())
    bank = json.loads(args.stage_bank.read_text())
    source = (args.candidate / "train/source/LeggedManip_Lab/LeggedManip_Lab/tasks"
              "/manager_based/leggedmanip_lab/mdp/climb_leg_kinematics.py")
    relative = source.relative_to(args.candidate / "train").as_posix()
    usd = (args.candidate / "train/source/LeggedManip_Lab/LeggedManip_Lab"
           "/assets/go2_piper/go2_piper.usd")
    if (sha256(source) != plan["source_sha256"][relative]
            or sha256(source) != numeric["math_source_sha256"][source.name]
            or sha256(usd) != numeric["usd_sha256"]
            or sha256(args.policy) != plan["actor_sha256"]
            or sha256(args.stage_bank) != plan["stage_bank_sha256"]):
        raise ValueError("CLIMB source, USD, actor or stage bank hash mismatch")
    if bank["box_height_m"] != 0.2 or len(bank["states"]) != 1:
        raise ValueError("Expected the frozen single-state 20cm stage bank")

    kinematics = runpy.run_path(str(source))["LegKinematics"](
        numeric["geometry"], dtype=torch.float64
    )
    runtime = make_episode("climb", args.policy, args.seed, native_collisions=True)
    model, data = runtime.model, runtime.data
    stage = bank["states"][0]
    values = dict(zip(bank["joint_names"], stage["joint_position"]))
    data.qpos[:7] = stage["root_pose"]
    data.qpos[runtime.joint_qpos_adr] = [values[name] for name in JOINT_NAMES]
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    base_id = model.body("base_link").id
    feet = [model.body(f"{leg}_foot").id for leg in LEGS]
    joint_dofs = np.array([
        [int(model.jnt_dofadr[model.joint(f"{leg}_{part}_joint").id]) for part in JOINT_PARTS]
        for leg in LEGS
    ])
    joint_qpos = np.array([
        [int(model.jnt_qposadr[model.joint(f"{leg}_{part}_joint").id]) for part in JOINT_PARTS]
        for leg in LEGS
    ])
    joint_ids = model.dof_jntid[joint_dofs]
    lower = model.jnt_range[joint_ids, 0] + 0.01
    upper = model.jnt_range[joint_ids, 1] - 0.01
    initial = data.qpos[joint_qpos].copy()
    rng = np.random.default_rng(args.seed)
    poses = [initial] + [np.clip(initial + rng.normal(0.0, 0.05, (4, 3)), lower, upper)
                         for _ in range(16)]
    comparisons = []
    for pose in poses:
        data.qpos[joint_qpos] = pose
        mujoco.mj_forward(model, data)
        rotation = data.xmat[base_id].reshape(3, 3)
        joints = torch.from_numpy(pose.copy()).unsqueeze(0)
        predicted_local = kinematics.forward(joints)[0].numpy()
        predicted_jacobian = kinematics.jacobian(joints)[0].numpy()
        predicted_world = data.xpos[base_id] + predicted_local @ rotation.T
        measured_world = data.xpos[feet].copy()
        jacobian_errors = []
        for leg_index, foot_id in enumerate(feet):
            jacobian_position = np.zeros((3, model.nv))
            jacobian_rotation = np.zeros((3, model.nv))
            mujoco.mj_jacBody(model, data, jacobian_position, jacobian_rotation, foot_id)
            measured = jacobian_position[:, joint_dofs[leg_index]]
            predicted = rotation @ predicted_jacobian[leg_index]
            jacobian_errors.append(float(np.max(np.abs(predicted - measured))))
        comparisons.append({
            "joint_position": pose.tolist(),
            "foot_position_error_m": np.linalg.norm(predicted_world - measured_world, axis=1).tolist(),
            "foot_jacobian_max_abs_error": jacobian_errors,
        })

    result = {
        "scope": "Static stage-bank pose and 16 bounded joint perturbations; no CLIMB rollout or acceptance",
        "source_sha256": sha256(source), "usd_sha256": sha256(usd),
        "actor_sha256": sha256(args.policy), "stage_bank_sha256": sha256(args.stage_bank),
        "numeric_geometry_sha256": sha256(args.numeric_geometry),
        "mujoco_xml_sha256": sha256(Path(__file__).resolve().parent / "robots/go2_piper/go2piper.xml"),
        "mujoco_robot_profile_sha256": sha256(PROFILE_PATH),
        "mujoco_collision_profile_sha256": sha256(COLLISION_PROFILE_PATH),
        "pose_count": len(comparisons),
        "max_foot_position_error_m": max(max(item["foot_position_error_m"]) for item in comparisons),
        "max_foot_jacobian_abs_error": max(max(item["foot_jacobian_max_abs_error"])
                                            for item in comparisons),
        "comparisons": comparisons,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "pose_count", "max_foot_position_error_m", "max_foot_jacobian_abs_error"
    )}))


if __name__ == "__main__":
    main()
