"""Record a fixed PIPER PUSH arm pose as a per-physics-step actuator trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

from scan_piper_push_reachability import (
    gravity_compensated_target,
    make_geometry_runtime,
    prescribe_base_pose,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--node-index", type=int, default=0)
    parser.add_argument("--control-steps", type=int, default=10)
    parser.add_argument("--delay-buffer-initialization", choices=("zero", "current"), default="zero")
    parser.add_argument("--box-x", type=float, default=None, help="Diagnostic-only PUSH box x override")
    parser.add_argument("--base-height-offset", type=float, default=0.0, help="Diagnostic-only initial root height offset")
    parser.add_argument("--fix-root-link", action="store_true", help="Diagnostic-only fixed-base replay")
    parser.add_argument("--disable-floor", action="store_true", help="Diagnostic-only floor collision removal")
    parser.add_argument("--zero-floor-friction", action="store_true", help="Diagnostic-only floor and foot friction removal")
    parser.add_argument("--zero-gravity", action="store_true", help="Diagnostic-only zero-gravity replay")
    parser.add_argument("--zero-gravity-physics-only", action="store_true", help="Keep gravity-compensated targets while disabling physics gravity")
    parser.add_argument("--zero-effort", action="store_true", help="Diagnostic-only zero applied joint torque")
    args = parser.parse_args()
    if not args.path_json.is_file() or args.output_json.exists() or args.control_steps < 1 or not np.isfinite(args.base_height_offset):
        parser.error("Require an existing path, a new output and positive control steps")
    return args


def reported_root_state(data, root_pose, fix_root_link):
    if fix_root_link:
        return root_pose.tolist(), [0.0] * 6
    return data.qpos[:7].tolist(), data.qvel[:6].tolist()


def foot_forces(model, data):
    foot_normal_forces = {name: 0.0 for name in ("FL", "FR", "RL", "RR")}
    foot_forces_world = {name: np.zeros(3) for name in foot_normal_forces}
    foot_contacts = []
    for contact_index, contact in enumerate(data.contact):
        geom1 = model.geom(contact.geom1).name
        geom2 = model.geom(contact.geom2).name
        if "floor" not in (geom1, geom2):
            continue
        foot_name = geom2 if geom1 == "floor" else geom1
        if foot_name in foot_normal_forces:
            wrench = np.zeros(6)
            mujoco.mj_contactForce(model, data, contact_index, wrench)
            foot_normal_forces[foot_name] += float(wrench[0])
            foot_forces_world[foot_name] += (1.0 if geom1 == "floor" else -1.0) * contact.frame.reshape(3, 3).T @ wrench[:3]
            foot_contacts.append({
                "geom1": geom1, "geom2": geom2,
                "normal": contact.frame[:3].tolist(),
                "distance": float(contact.dist),
                "normal_force": float(wrench[0]),
            })
    return foot_normal_forces, foot_contacts, {name: force.tolist() for name, force in foot_forces_world.items()}


def main():
    args = parse_args()
    path = json.loads(args.path_json.read_text())
    trajectory = path.get("selected_trajectory")
    if trajectory is None or not trajectory.get("nodes"):
        raise ValueError("Path report must contain a selected continuous trajectory")
    if not 0 <= args.node_index < len(trajectory["nodes"]):
        raise ValueError("Node index must select a continuous trajectory node")
    node = trajectory["nodes"][args.node_index]
    initial_root_pose = np.concatenate((
        (node["base_x"], node["base_y"], node["base_height"] + args.base_height_offset),
        (1.0, 0.0, 0.0, 0.0),
    )).tolist()
    runtime = make_geometry_runtime(
        path["seed"], path["contact_height_offset"],
        fix_root_link=args.fix_root_link, fixed_root_pose=initial_root_pose,
        disable_floor=args.disable_floor,
    )
    if args.zero_floor_friction:
        for geom_name in ("floor", "FL", "FR", "RL", "RR"):
            runtime.model.geom(geom_name).friction[:] = 0.0
    if args.zero_gravity and not args.zero_gravity_physics_only:
        runtime.model.opt.gravity[:] = 0.0
    arm, data = runtime.arm, runtime.data
    position = np.array((node["base_x"], node["base_y"], node["base_height"] + args.base_height_offset))
    desired = np.asarray(node["joint_position"], dtype=np.float64)
    root_pose = np.asarray(initial_root_pose, dtype=np.float64)

    def prescribe_root():
        if args.fix_root_link:
            return
        data.qpos[:3] = position
        data.qpos[3:7] = (1.0, 0.0, 0.0, 0.0)
        data.qvel[:6] = 0.0
        mujoco.mj_forward(runtime.model, data)

    prescribe_root()
    data.qpos[arm.arm_qpos] = desired
    data.qvel[arm.arm_dof] = 0.0
    mujoco.mj_forward(runtime.model, data)
    runtime.constraint_substeps = 1
    leg_target = data.qpos[runtime.joint_qpos_adr[:12]].copy()

    def target():
        result = gravity_compensated_target(runtime, desired)
        result[:12] = leg_target
        return result

    runtime.target_history.clear()
    initial_target = target()
    if args.zero_gravity_physics_only:
        runtime.model.opt.gravity[:] = 0.0
        physics_target = initial_target.copy()

        def target():
            return physics_target.copy()

    if args.delay_buffer_initialization == "zero":
        history_target = np.zeros(18, dtype=np.float64)
    else:
        history_target = initial_target
    runtime.target_history.extend(history_target.copy() for _ in range(runtime.target_history.maxlen))
    if args.zero_effort:
        runtime.kp[:] = 0.0
        runtime.kd[:] = 0.0

        def target():
            return initial_target.copy()
    initial_root, initial_velocity = reported_root_state(data, root_pose, args.fix_root_link)
    initial_state = {
        "root_pose": initial_root,
        "root_velocity": initial_velocity,
        "joint_positions": data.qpos[runtime.joint_qpos_adr].tolist(),
        "joint_velocities": data.qvel[runtime.joint_dof_adr].tolist(),
    }
    gravity_bias_initial = data.qfrc_bias[runtime.joint_dof_adr].tolist()
    box_data = data.joint("push_box_joint")
    box_qpos = box_data.qpos
    box_qvel = box_data.qvel
    if args.box_x is not None:
        if not np.isfinite(args.box_x):
            parser.error("Box x override must be finite")
        box_qpos[0] = args.box_x
        mujoco.mj_forward(runtime.model, data)
    box_initial_state = {
        "root_pose": box_qpos.tolist(),
        "root_velocity": box_qvel.tolist(),
    }
    initial_contacts = [
        {
            "geom1": runtime.model.geom(contact.geom1).name,
            "geom2": runtime.model.geom(contact.geom2).name,
            "distance": float(contact.dist),
            "position": contact.pos.tolist(),
        }
        for contact in data.contact
    ]
    initial_foot_colliders = [
        {
            "geom": runtime.model.geom(geom_id).name,
            "type": "Sphere",
            "world_position": data.geom_xpos[geom_id].tolist(),
            "sphere_radius": float(runtime.model.geom_size[geom_id, 0]),
            "solref": runtime.model.geom_solref[geom_id].tolist(),
            "solimp": runtime.model.geom_solimp[geom_id].tolist(),
            "friction": runtime.model.geom_friction[geom_id].tolist(),
            "margin": float(runtime.model.geom_margin[geom_id]),
        }
        for geom_id in range(runtime.model.ngeom)
        if runtime.model.geom(geom_id).name in ("FL", "FR", "RL", "RR")
        and runtime.model.geom_type[geom_id] == mujoco.mjtGeom.mjGEOM_SPHERE
    ]
    if len(initial_foot_colliders) != 4:
        raise ValueError("Expected four foot collision spheres")
    foot_geom_ids = {foot: runtime.model.geom(foot).id for foot in ("FL", "FR", "RL", "RR")}

    def foot_centers_world():
        return {foot: data.geom_xpos[geom_id].tolist() for foot, geom_id in foot_geom_ids.items()}

    rows = []
    original_monitor = runtime.on_safety_step
    original_solver_step = getattr(runtime, "on_solver_step", None)
    forces_before_projection = []
    post_step_data = mujoco.MjData(runtime.model)

    def record_solver_step():
        if original_solver_step is not None:
            original_solver_step()
        forces, contacts, forces_world = foot_forces(runtime.model, data)
        post_step_data.time = data.time
        post_step_data.qpos[:] = data.qpos
        post_step_data.qvel[:] = data.qvel
        post_step_data.act[:] = data.act
        post_step_data.ctrl[:] = data.ctrl
        mujoco.mj_forward(runtime.model, post_step_data)
        post_step_forces, post_step_contacts, post_step_forces_world = foot_forces(runtime.model, post_step_data)
        forces_before_projection.append((
            forces, contacts, forces_world,
            data.qpos[runtime.joint_qpos_adr].tolist(),
            data.qvel[runtime.joint_dof_adr].tolist(),
            foot_centers_world(),
            post_step_forces, post_step_contacts, post_step_forces_world,
        ))

    def record_step():
        original_monitor()
        solver_root, solver_velocity = reported_root_state(data, root_pose, args.fix_root_link)
        projected_forces, projected_contacts, projected_forces_world = foot_forces(runtime.model, data)
        rows.append({
            "physics_step": len(rows),
            "time": float(data.time),
            "root_pose": root_pose.tolist(),
            "root_velocity": [0.0] * 6,
            "solver_root_pose": solver_root,
            "solver_root_velocity": solver_velocity,
            "target": runtime.target_history[-1].tolist(),
            "torque": data.ctrl.tolist(),
            "foot_normal_forces": projected_forces,
            "foot_contacts": projected_contacts,
            "foot_forces_world": projected_forces_world,
            "foot_normal_forces_before_projection": forces_before_projection[-1][0],
            "foot_contacts_before_projection": forces_before_projection[-1][1],
            "foot_forces_world_before_projection": forces_before_projection[-1][2],
            "solver_positions_before_projection": forces_before_projection[-1][3],
            "solver_velocities_before_projection": forces_before_projection[-1][4],
            "foot_centers_world_before_projection": forces_before_projection[-1][5],
            "foot_normal_forces_post_step": forces_before_projection[-1][6],
            "foot_contacts_post_step": forces_before_projection[-1][7],
            "foot_forces_world_post_step": forces_before_projection[-1][8],
            "foot_centers_world": foot_centers_world(),
            "limited_positions": data.qpos[runtime.joint_qpos_adr].tolist(),
            "limited_velocities": data.qvel[runtime.joint_dof_adr].tolist(),
        })
        prescribe_root()

    runtime.on_solver_step = record_solver_step
    runtime.on_safety_step = record_step
    for _ in range(args.control_steps):
        prescribe_root()
        runtime._simulate_target(target())
    report = {
        "schema_version": 1,
        "backend": "mujoco",
        "diagnostic_only": True,
        "task": "GO2-PIPER-Box-Push-Hybrid-Play",
        "root_mode": "fixed" if args.fix_root_link else "kinematic_prescribed_each_physics_step",
        "disable_floor": args.disable_floor,
        "zero_floor_friction": args.zero_floor_friction,
        "zero_gravity": args.zero_gravity or args.zero_gravity_physics_only,
        "zero_gravity_physics_only": args.zero_gravity_physics_only,
        "zero_effort": args.zero_effort,
        "path_sha256": hashlib.sha256(args.path_json.read_bytes()).hexdigest(),
        "path_node_index": args.node_index,
        "contact_force_sampling": {
            "foot_normal_forces_before_projection": "after mj_step: contact solver output for pre-integration geometry",
            "foot_normal_forces_post_step": "independent mj_forward at integrated post-step state, before velocity limits or root restore",
            "foot_normal_forces": "after joint state assignment and mj_forward: refreshed contact solver output for post-integration geometry",
            "foot_forces_world": "floor-foot contact force on foot in world coordinates, including tangential components; excludes other foot contacts",
        },
        "source_sha256": {
            "trace": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "piper_box_runtime": hashlib.sha256(Path(make_geometry_runtime.__code__.co_filename).read_bytes()).hexdigest(),
        },
        "physics_dt": runtime.sim_dt,
        "control_dt": runtime.control_dt,
        "joint_names": [runtime.model.joint(int(runtime.model.dof_jntid[index])).name for index in runtime.joint_dof_adr],
        "actuator_delay_steps": runtime.actuator_delay_steps.tolist(),
        "initial_state": initial_state,
        "box_initial_state": box_initial_state,
        "initial_contacts": initial_contacts,
        "initial_foot_colliders": initial_foot_colliders,
        "box_x_override": args.box_x,
        "base_height_offset": args.base_height_offset,
        "desired_arm_joint_position": desired.tolist(),
        "leg_target_mode": "initial_hold",
        "delay_buffer_initialization": args.delay_buffer_initialization,
        "gravity_bias_initial": gravity_bias_initial,
        "kp": runtime.kp.tolist(),
        "kd": runtime.kd.tolist(),
        "steps": rows,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
    print(json.dumps({"physics_steps": len(rows), "output_json": str(args.output_json)}, allow_nan=False))


if __name__ == "__main__":
    main()