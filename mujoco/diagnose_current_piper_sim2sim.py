"""First MuJoCo transfer diagnostics for the current PIPER skill candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import mujoco
import numpy as np
import torch

from check_box_push_policy import run_episode as run_push_episode
from reconfigurable_navigation import box_push_runtime
from reconfigurable_navigation.piper_box_runtime import make_episode
from reconfigurable_navigation.piper_locomotion_runtime import JOINT_NAMES
from reconfigurable_navigation.piper_robot_profile import COLLISION_PROFILE_PATH, PROFILE_PATH


REPO = Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    Path(__file__),
    REPO / "mujoco/check_box_push_policy.py",
    REPO / "mujoco/reconfigurable_navigation/box_push_runtime.py",
    REPO / "mujoco/reconfigurable_navigation/box_climb_runtime.py",
    REPO / "mujoco/reconfigurable_navigation/climb_runtime.py",
    REPO / "mujoco/reconfigurable_navigation/piper_box_runtime.py",
    REPO / "mujoco/deploy/deploy_mujoco/go2_piper/config.yaml",
    REPO / "mujoco/deploy/piper_push_safe_approach.json",
    REPO / "mujoco/robots/go2_piper/go2piper.xml",
    PROFILE_PATH,
    COLLISION_PROFILE_PATH,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_file(path: Path, expected: str) -> None:
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"SHA256 mismatch for {path}: {actual} != {expected}")


def export_push_actor(checkpoint: Path, source_root: Path, output: Path) -> dict:
    loader = runpy.run_path(str(source_root / "scripts/rsl_rl/initialization.py"))["actor_from_state_dict"]
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["actor_state_dict"]
    actor = loader(state)
    if (actor[0].in_features, actor[-1].out_features) != (226, 12):
        raise ValueError("Expected the current 226-to-12 PUSH actor")
    scripted = torch.jit.script(actor)
    probes = torch.cat((torch.zeros(1, 226), torch.randn(64, 226, generator=torch.Generator().manual_seed(0))))
    with torch.inference_mode():
        reference = actor(probes)
        torch.testing.assert_close(scripted(probes), reference, rtol=1e-6, atol=1e-6)
    scripted.save(str(output))
    with torch.inference_mode():
        restored = torch.jit.load(str(output), map_location="cpu").eval()
        torch.testing.assert_close(restored(probes), reference, rtol=1e-6, atol=1e-6)
    return {
        "checkpoint_sha256": digest(checkpoint),
        "exported_actor_sha256": digest(output),
        "source_initialization_sha256": digest(source_root / "scripts/rsl_rl/initialization.py"),
        "probe_count": len(probes),
        "max_abs_export_error": float((scripted(probes) - reference).abs().max()),
    }


def push_diagnostic(args, output: Path) -> dict:
    contract = json.loads(args.contract.read_text())
    if contract["push_press_depth"] != 0.10 or contract["push_distance"] != 0.60:
        raise ValueError("Expected the accepted 100mm PUSH evaluation contract")
    verify_file(args.policy, args.expected_policy_sha256)
    actor_path = output / "exported-push-actor.pt"
    export = export_push_actor(args.policy, args.source_root, actor_path)
    candidate_control = args.source_root / "source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/box_push_control.py"
    box_push_runtime.CONTROL = runpy.run_path(str(candidate_control))
    current_prefix = args.push_control_mode == "current-prefix"
    runtime = make_episode(
        "push", actor_path, args.seed, push_ik_mode="pose", native_collisions=True,
        push_hand_pitch=0.6, push_height_offset=0.03,
        push_safe_precontact=not current_prefix, push_current_contract=current_prefix,
    )
    if current_prefix:
        runtime.arm.leg_contact_ramp_s = args.push_contact_ramp_s
        runtime.arm.geometry_speed_slowdown_start = args.push_geometry_slowdown_start
    arm_body_names = ("link2", "link3", "link4", "link5", "link6", "end_effector")
    protected_body_names = ("base_link",) + tuple(
        f"{leg}_{segment}"
        for leg in ("FL", "FR", "RL", "RR")
        for segment in ("hip", "thigh", "calf", "foot")
    )
    arm_body_ids = [runtime.model.body(name).id for name in arm_body_names]
    protected_body_ids = [runtime.model.body(name).id for name in protected_body_names]

    def body_origin_clearance(arm_qpos):
        original = runtime.data.qpos[runtime.arm.arm_qpos].copy()
        try:
            runtime.data.qpos[runtime.arm.arm_qpos] = arm_qpos
            mujoco.mj_forward(runtime.model, runtime.data)
            distances = np.linalg.norm(
                runtime.data.xpos[arm_body_ids, None, :] - runtime.data.xpos[None, protected_body_ids, :], axis=2,
            )
            arm_index, protected_index = np.unravel_index(np.argmin(distances), distances.shape)
            return float(distances[arm_index, protected_index]), [
                arm_body_names[arm_index], protected_body_names[protected_index],
            ]
        finally:
            runtime.data.qpos[runtime.arm.arm_qpos] = original
            mujoco.mj_forward(runtime.model, runtime.data)

    clearance_trace = []
    drive_trace = []
    original_safe_target = runtime.arm._collision_safe_target
    original_step = runtime.step
    original_safety_step = runtime.on_safety_step
    foot_names = ("FL_foot", "FR_foot", "RL_foot", "RR_foot")
    foot_ids = {runtime.model.body(name).id: index for index, name in enumerate(foot_names)}
    substep_trace = {
        "samples": 0,
        "leg_torque_saturated_samples": 0,
        "arm_torque_saturated_samples": 0,
        "arm_torque_abs_max_nm": np.zeros(6),
        "box_floor_horizontal_force_max_n": 0.0,
        "foot_normal_force_max_n": np.zeros(4),
        "loaded_foot_speed_xy_max_mps": np.zeros(4),
        "loaded_foot_samples": np.zeros(4, dtype=int),
        "contact_point_tangent_speed_max_mps": np.zeros(4),
        "contact_point_tangent_speed_weighted_sum": np.zeros(4),
        "contact_point_normal_force_sum_n": np.zeros(4),
    }
    foot_contact_jacobian = np.empty((3, runtime.model.nv))
    terrain_contact_jacobian = np.empty((3, runtime.model.nv))
    floor_geom = runtime.model.geom("floor").id

    def traced_safety_step():
        if original_safety_step is not None:
            original_safety_step()
        substep_trace["samples"] += 1
        substep_trace["leg_torque_saturated_samples"] += int(np.any(
            np.isclose(runtime.data.ctrl[:12], runtime.ctrl_low[:12])
            | np.isclose(runtime.data.ctrl[:12], runtime.ctrl_high[:12])
        ))
        substep_trace["arm_torque_saturated_samples"] += int(np.any(
            np.isclose(runtime.data.ctrl[12:18], runtime.ctrl_low[12:18])
            | np.isclose(runtime.data.ctrl[12:18], runtime.ctrl_high[12:18])
        ))
        substep_trace["arm_torque_abs_max_nm"] = np.maximum(
            substep_trace["arm_torque_abs_max_nm"], np.abs(runtime.data.ctrl[12:18]),
        )
        normal_force = np.zeros(4)
        wrench = np.zeros(6)
        box_floor_force_world = np.zeros(3)
        for contact_index, contact in enumerate(runtime.data.contact[:runtime.data.ncon]):
            first, second = int(contact.geom1), int(contact.geom2)
            if {first, second} == {runtime.arm.box_geom, floor_geom}:
                mujoco.mj_contactForce(runtime.model, runtime.data, contact_index, wrench)
                contact_force_world = contact.frame.reshape(3, 3).T @ wrench[:3]
                box_floor_force_world += contact_force_world * (1.0 if first == runtime.arm.box_geom else -1.0)
            if first in runtime.terrain_geom_ids:
                foot_index = foot_ids.get(int(runtime.model.geom_bodyid[second]))
                foot_geom, terrain_geom = second, first
            elif second in runtime.terrain_geom_ids:
                foot_index = foot_ids.get(int(runtime.model.geom_bodyid[first]))
                foot_geom, terrain_geom = first, second
            else:
                continue
            if foot_index is None:
                continue
            mujoco.mj_contactForce(runtime.model, runtime.data, contact_index, wrench)
            force_world = contact.frame.reshape(3, 3).T @ wrench[:3]
            vertical_force = abs(force_world[2])
            normal_force[foot_index] += vertical_force
            if vertical_force > 2.0:
                foot_body = int(runtime.model.geom_bodyid[foot_geom])
                terrain_body = int(runtime.model.geom_bodyid[terrain_geom])
                mujoco.mj_jac(runtime.model, runtime.data, foot_contact_jacobian, None, contact.pos, foot_body)
                if terrain_body == 0:
                    terrain_contact_jacobian.fill(0.0)
                else:
                    mujoco.mj_jac(runtime.model, runtime.data, terrain_contact_jacobian, None, contact.pos, terrain_body)
                relative_velocity = (foot_contact_jacobian - terrain_contact_jacobian) @ runtime.data.qvel
                normal = contact.frame.reshape(3, 3)[0]
                tangent_velocity = relative_velocity - np.dot(relative_velocity, normal) * normal
                tangent_speed = float(np.linalg.norm(tangent_velocity))
                substep_trace["contact_point_tangent_speed_max_mps"][foot_index] = max(
                    substep_trace["contact_point_tangent_speed_max_mps"][foot_index], tangent_speed,
                )
                substep_trace["contact_point_tangent_speed_weighted_sum"][foot_index] += vertical_force * tangent_speed
                substep_trace["contact_point_normal_force_sum_n"][foot_index] += vertical_force
        substep_trace["foot_normal_force_max_n"] = np.maximum(
            substep_trace["foot_normal_force_max_n"], normal_force
        )
        for foot_id, index in foot_ids.items():
            if normal_force[index] <= 2.0:
                continue
            velocity = np.zeros(6)
            mujoco.mj_objectVelocity(
                runtime.model, runtime.data, mujoco.mjtObj.mjOBJ_BODY, foot_id, velocity, 0,
            )
            substep_trace["loaded_foot_speed_xy_max_mps"][index] = max(
                substep_trace["loaded_foot_speed_xy_max_mps"][index],
                float(np.linalg.norm(velocity[3:5])),
            )
            substep_trace["loaded_foot_samples"][index] += 1
        substep_trace["box_floor_horizontal_force_max_n"] = max(
            substep_trace["box_floor_horizontal_force_max_n"],
            float(np.linalg.norm(box_floor_force_world[:2])),
        )

    def traced_safe_target(desired):
        candidate_geometry = runtime.arm._minimum_protected_clearance(desired)
        candidate_body_distance, candidate_body_pair = body_origin_clearance(desired)
        accepted = original_safe_target(desired)
        clearance_trace.append({
            "time_s": float(runtime.data.time),
            "blocked": bool(runtime.arm.collision_blocked),
            "candidate_geometry_clearance_m": candidate_geometry,
            "candidate_body_origin_distance_m": candidate_body_distance,
            "candidate_body_origin_pair": candidate_body_pair,
            "current_arm_qpos": runtime.data.qpos[runtime.arm.arm_qpos].tolist(),
            "candidate_arm_qpos": np.asarray(desired).tolist(),
            "accepted_arm_qpos": np.asarray(accepted).tolist(),
        })
        return accepted

    runtime.arm._collision_safe_target = traced_safe_target
    def traced_step():
        substep_trace["samples"] = 0
        substep_trace["leg_torque_saturated_samples"] = 0
        substep_trace["arm_torque_saturated_samples"] = 0
        substep_trace["arm_torque_abs_max_nm"].fill(0.0)
        substep_trace["box_floor_horizontal_force_max_n"] = 0.0
        substep_trace["foot_normal_force_max_n"].fill(0.0)
        substep_trace["loaded_foot_speed_xy_max_mps"].fill(0.0)
        substep_trace["loaded_foot_samples"].fill(0)
        substep_trace["contact_point_tangent_speed_max_mps"].fill(0.0)
        substep_trace["contact_point_tangent_speed_weighted_sum"].fill(0.0)
        substep_trace["contact_point_normal_force_sum_n"].fill(0.0)
        action = original_step()
        target = runtime.default_qpos + action[box_push_runtime.POLICY_MJ_INDICES] * runtime.action_scale
        drive_trace.append({
            "time_s": float(runtime.data.time),
            "next_observation_forward_command_mps": float(runtime.history[-1][60]),
            "geometry_speed_scale": runtime.arm.geometry_speed_scale,
            "leg_release_blend": runtime.arm.leg_release_blend,
            "leg_action": action[:12].tolist(),
            "leg_joint_position": runtime.data.qpos[runtime.joint_qpos_adr[:12]].tolist(),
            "leg_joint_target": target[:12].tolist(),
            "leg_joint_velocity": runtime.data.qvel[runtime.joint_dof_adr[:12]].tolist(),
            "leg_actuator_torque": runtime.data.ctrl[:12].tolist(),
            "arm_joint_position": runtime.data.qpos[runtime.joint_qpos_adr[12:18]].tolist(),
            "arm_joint_reference": runtime.arm.reference.tolist(),
            "arm_gravity_bias_nm": runtime.arm.gravity_data.qfrc_bias[runtime.arm.arm_dof].tolist(),
            "arm_joint_target": target[12:18].tolist(),
            "arm_joint_velocity": runtime.data.qvel[runtime.joint_dof_adr[12:18]].tolist(),
            "arm_actuator_torque": runtime.data.ctrl[12:18].tolist(),
            "arm_torque_saturated_substeps": substep_trace["arm_torque_saturated_samples"],
            "arm_torque_abs_max_nm": substep_trace["arm_torque_abs_max_nm"].tolist(),
            "hand_target_error_m": float(np.linalg.norm(runtime.arm.hand_target() - runtime.arm.hand_position())),
            "box_floor_horizontal_force_max_n": substep_trace["box_floor_horizontal_force_max_n"],
            "leg_actuator_saturated": bool(np.any(
                np.isclose(runtime.data.ctrl[:12], runtime.ctrl_low[:12])
                | np.isclose(runtime.data.ctrl[:12], runtime.ctrl_high[:12])
            )),
            "physics_substeps": substep_trace["samples"],
            "leg_torque_saturated_substeps": substep_trace["leg_torque_saturated_samples"],
            "foot_normal_force_max_n": substep_trace["foot_normal_force_max_n"].tolist(),
            "loaded_foot_speed_xy_max_mps": substep_trace["loaded_foot_speed_xy_max_mps"].tolist(),
            "loaded_foot_samples": substep_trace["loaded_foot_samples"].tolist(),
            "contact_point_tangent_speed_max_mps": substep_trace["contact_point_tangent_speed_max_mps"].tolist(),
            "contact_point_tangent_speed_force_weighted_mean_mps": np.divide(
                substep_trace["contact_point_tangent_speed_weighted_sum"],
                substep_trace["contact_point_normal_force_sum_n"],
                out=np.zeros(4),
                where=substep_trace["contact_point_normal_force_sum_n"] > 0.0,
            ).tolist(),
        })
        return action

    runtime.step = traced_step
    runtime.on_safety_step = traced_safety_step
    try:
        result = run_push_episode(actor_path, args.seed, duration=args.duration, runtime=runtime, diagnostic_trace=True)
    finally:
        runtime.on_safety_step = original_safety_step
        runtime.step = original_step
        runtime.arm._collision_safe_target = original_safe_target
    protected_pairs = (
        (mujoco.mj_geomDistance(runtime.model, runtime.data, arm, protected, 1.0, None), arm, protected)
        for arm in runtime.arm.collision_arm_geoms
        for protected in runtime.arm.collision_protected_geoms
    )
    nearest_distance, nearest_arm, nearest_protected = min(protected_pairs, key=lambda item: item[0])
    nearest_body_distance, nearest_body_pair = body_origin_clearance(runtime.data.qpos[runtime.arm.arm_qpos])
    blocked_trace = [entry for entry in clearance_trace if entry["blocked"]]
    hand_position = runtime.arm.hand_position()
    hand_target = runtime.arm.hand_target()
    return {
        "source": export,
        "contract_sha256": digest(args.contract),
        "candidate_control_sha256": digest(candidate_control),
        "push_control_mode": args.push_control_mode,
        "applied_control": {
            "press_depth_m": runtime.arm.press_depth,
            "leg_release_ramp_s": runtime.arm.leg_release_ramp_s,
            "leg_contact_ramp_s": runtime.arm.leg_contact_ramp_s,
            "lock_arm_on_contact": runtime.arm.lock_arm_on_contact,
            "staged_precontact": runtime.arm.safe_precontact,
            "forward_command_gain": runtime.arm.forward_command_gain,
            "stop_distance_m": runtime.arm.stop_distance,
            "source_bounded_pose_ik": runtime.arm.source_bounded_pose_ik,
            "orientation_weight": runtime.arm.orientation_weight,
            "body_clearance_minimum_m": runtime.arm.body_clearance_minimum,
            "geometry_speed_slowdown_start_m": runtime.arm.geometry_speed_slowdown_start,
        },
        "result": result,
        "drive_probe": {
            "scope": "Post-step leg/arm targets and actuator state; arm_joint_target includes gravity compensation and arm_joint_reference does not; forward command is the next observation frame; foot loads, loaded-foot body speeds, contact-point relative tangent speeds, box-floor horizontal force and torque saturation include physics substeps but exclude initialization",
            "trace": drive_trace,
        },
        "terminal_geometry": {
            "hand_position": hand_position.tolist(), "hand_target": hand_target.tolist(),
            "hand_target_error_m": float(np.linalg.norm(hand_target - hand_position)),
            "approached": bool(runtime.arm.approached),
            "nearest_protected_clearance_m": float(nearest_distance),
            "nearest_protected_geoms": [runtime.model.geom(nearest_arm).name,
                                        runtime.model.geom(nearest_protected).name],
            "nearest_body_origin_distance_m": nearest_body_distance,
            "nearest_body_origin_pair": nearest_body_pair,
        },
        "candidate_clearance_probe": {
            "scope": "MuJoCo candidate IK target before geometric path filtering; not an Isaac replay",
            "count": len(clearance_trace),
            "blocked_count": len(blocked_trace),
            "blocked_candidate_body_origin_above_80mm": sum(
                entry["candidate_body_origin_distance_m"] >= 0.08 for entry in blocked_trace
            ),
            "blocked_candidate_geometry_above_15mm": sum(
                entry["candidate_geometry_clearance_m"] >= 0.015 for entry in blocked_trace
            ),
            "trace": clearance_trace,
        },
        "final_controller_state": {
            "safe_approach_complete": runtime.arm.safe_approach_complete(),
            "precontact_stage": runtime.arm.precontact_index,
            "precontact_complete": runtime.arm.precontact_complete(),
            "motion_ready": bool(runtime.arm.motion_ready),
            "self_collision": runtime.self_collision,
            "body_clearance_distance_m": runtime.arm.body_clearance_distance,
            "body_clearance_residual_m": runtime.arm.body_clearance_residual,
            "body_clearance_correction_rad": runtime.arm.body_clearance_correction,
        },
        "control_gaps": ([
            "Legacy MuJoCo staged precontact and locked arm are absent from the accepted Tracking candidate.",
            "Legacy MuJoCo arm target uses 20mm press instead of 100mm and has no 0.7s/0.2s leg blend.",
        ] if not current_prefix else [
            "Bounded pose IK and 100mm body-center projection call source math; MuJoCo Jacobians, state trajectory and the additional 15mm geometry filter remain unmatched.",
            "Full source contact retention, goal pose hold and detailed actuator/observation traces remain unmatched.",
        ]) + [
            "MuJoCo reset randomization is not the accepted Isaac reset distribution.",
        ],
    }


def climb_diagnostic(args) -> dict:
    verify_file(args.policy, args.expected_policy_sha256)
    verify_file(args.stage_bank, args.expected_stage_bank_sha256)
    stage_bank = json.loads(args.stage_bank.read_text())
    if stage_bank["box_height_m"] != 0.2 or len(stage_bank["states"]) != 1:
        raise ValueError("Expected the current 20cm, single-state stage bank")
    runtime = make_episode("climb", args.policy, args.seed, native_collisions=True)
    model, data = runtime.model, runtime.data
    state = stage_bank["states"][0]
    names = stage_bank["joint_names"]
    if len(names) != 18 or len(set(names)) != 18:
        raise ValueError("Stage bank has an invalid joint list")
    qpos = {name: value for name, value in zip(names, state["joint_position"])}
    target = {name: value for name, value in zip(names, state["joint_position_target"])}
    data.qpos[:7] = state["root_pose"]
    data.qvel[:] = 0.0
    data.qpos[runtime.joint_qpos_adr] = [qpos[name] for name in JOINT_NAMES]
    mujoco.mj_forward(model, data)
    runtime.activate()
    target_vector = np.array([target[name] for name in JOINT_NAMES])
    runtime.target_history.clear()
    runtime.target_history.extend(target_vector.copy() for _ in range(runtime.target_history.maxlen))
    observation = runtime.observation()
    actor_input = next(value.shape[1] for name, value in runtime.policy.state_dict().items() if name.endswith("weight"))
    if observation.shape != (253,) or actor_input != 304:
        raise ValueError("Expected the known 253-to-304 CLIMB observation gap")
    actor_state = runtime.policy.state_dict()
    output_weight, output_bias = actor_state["6.weight"], actor_state["6.bias"]
    if output_weight.shape != (18, 128) or output_bias.shape != (18,):
        raise ValueError("Unexpected CLIMB actor output layer")
    random_observations = torch.randn(16, 304, generator=torch.Generator().manual_seed(0))
    with torch.inference_mode():
        random_actions = runtime.policy(random_observations)
    zero_residual_actor = {
        "output_weight_nonzero": int(torch.count_nonzero(output_weight)),
        "output_bias_nonzero": int(torch.count_nonzero(output_bias)),
        "random_probe_count": len(random_observations),
        "random_probe_max_abs_action": float(random_actions.abs().max()),
    }
    if any((zero_residual_actor["output_weight_nonzero"], zero_residual_actor["output_bias_nonzero"],
            zero_residual_actor["random_probe_max_abs_action"])):
        raise ValueError("Current CLIMB candidate is no longer the zero-residual actor")
    feet = [model.geom(name).id for name in ("FL", "FR", "RL", "RR")]
    box = model.geom("support_box").id
    floor = model.geom("floor").id
    initial_ground_support = runtime.support_contacts(feet, {floor})
    initial_top_support = runtime.support_contacts(feet, {box})
    # Isaac's first post-reset crawl observation has pending=True, so its
    # foot and joint reference errors are zero until the first action update.
    crawl_suffix = np.concatenate((
        [1.0, 0.0, 0.0, 0.0],  # selected first leg
        [0.0, 0.0, 0.0],  # progress, stable time, lifted
        [float(foot in initial_ground_support or foot in initial_top_support) for foot in feet],
        [1.0],  # the stage-bank pose is still before the platform
        np.zeros(3 + 18 + 18),
    )).astype(np.float32)
    actor_observation = np.concatenate((observation, crawl_suffix))
    if actor_observation.shape != (304,) or not np.isfinite(actor_observation).all():
        raise ValueError("Invalid provisional CLIMB actor observation")
    with torch.inference_mode():
        first_action = runtime.policy(torch.from_numpy(actor_observation).unsqueeze(0))[0].numpy()
    if first_action.shape != (18,) or not np.isfinite(first_action).all():
        raise ValueError("CLIMB actor returned an invalid first action")
    initial = {"root_pose": data.qpos[:7].tolist(), "joint_position": data.qpos[runtime.joint_qpos_adr].tolist()}
    trace = []
    for step in range(round(args.duration / runtime.control_dt)):
        runtime._simulate_target(target_vector)
        top_support = runtime.support_contacts(feet, {box})
        ground_support = runtime.support_contacts(feet, {floor})
        if step % 10 == 0 or step == round(args.duration / runtime.control_dt) - 1:
            trace.append({
                "time_s": float(data.time), "root_position": data.qpos[:3].tolist(),
                "root_velocity": data.qvel[:6].tolist(),
                "top_loaded_feet": len(top_support), "ground_loaded_feet": len(ground_support),
                "top_contact_height": {model.geom(index).name: height for index, height in top_support.items()},
                "ground_contact_height": {model.geom(index).name: height for index, height in ground_support.items()},
                "self_collision": getattr(runtime, "self_collision", None),
            })
        if runtime.self_collision is not None or runtime.base_contacts_terrain():
            break
    return {
        "actor_sha256": digest(args.policy), "stage_bank_sha256": digest(args.stage_bank),
        "legacy_runtime_observation_dimension": len(observation), "current_actor_input_dimension": actor_input,
        "zero_residual_actor": zero_residual_actor,
        "provisional_post_reset_actor_probe": {
            "scope": "finite inference only; 253-feature prefix and crawl state are not source-matched",
            "observation_dimension": len(actor_observation),
            "crawl_suffix": crawl_suffix.tolist(), "first_action": first_action.tolist(),
        },
        "initial": initial, "trace": trace,
        "control_gaps": [
            "This is a physical stage-initialization and loaded-hold probe, not a climb rollout.",
            "The Isaac support-transfer/foot-placement/front-extension controller is not ported to MuJoCo.",
            "The original MuJoCo completion predicate still uses the old platform-center goal.",
            "Stage bank has one prepared state; the 32 Isaac environments use a different reset distribution.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=("push", "climb"), required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--expected-policy-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--duration", type=float, default=1.0)
    parser.add_argument("--push-control-mode", choices=("legacy-precontact", "current-prefix"), default="legacy-precontact")
    parser.add_argument("--push-contact-ramp-s", type=float, default=0.2)
    parser.add_argument("--push-geometry-slowdown-start", type=float, default=0.0)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--stage-bank", type=Path)
    parser.add_argument("--expected-stage-bank-sha256")
    args = parser.parse_args()
    if args.output_dir.exists() or not np.isfinite(args.duration) or args.duration <= 0:
        parser.error("Use a new output directory and positive finite duration")
    if args.skill == "push" and (args.source_root is None or args.contract is None):
        parser.error("PUSH requires its frozen source tree and evaluation contract")
    if not np.isfinite(args.push_contact_ramp_s) or not 0.2 <= args.push_contact_ramp_s <= 0.7:
        parser.error("PUSH contact ramp must be in [0.2, 0.7] seconds")
    if args.push_control_mode != "current-prefix" and args.push_contact_ramp_s != 0.2:
        parser.error("A PUSH contact-ramp comparison requires current-prefix mode")
    if args.push_geometry_slowdown_start and (
        args.push_control_mode != "current-prefix"
        or not 0.03 <= args.push_geometry_slowdown_start <= 0.06
    ):
        parser.error("Geometry slowdown requires current-prefix mode and 30-60mm onset")
    if args.skill == "climb" and (args.stage_bank is None or args.expected_stage_bank_sha256 is None):
        parser.error("CLIMB requires its verified stage bank and SHA256")
    torch.set_num_threads(1)
    args.output_dir.mkdir(parents=True)
    report = {
        "schema_version": 1,
        "scope": ("single-seed extended-window MuJoCo transfer diagnostic; not 12s task acceptance"
                  if args.skill == "push" and args.duration > 12 else
                  "single-seed MuJoCo transfer diagnostic; not task acceptance"),
        "skill": args.skill, "seed": args.seed, "requested_duration_s": args.duration,
        "backend": {"mujoco": mujoco.__version__, "torch": torch.__version__, "numpy": np.__version__},
        "runtime_sha256": {str(path.relative_to(REPO)): digest(path) for path in RUNTIME_FILES},
    }
    report.update(push_diagnostic(args, args.output_dir) if args.skill == "push" else climb_diagnostic(args))
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"scope": report["scope"], "skill": args.skill, "report": str(args.output_dir / 'report.json')}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
