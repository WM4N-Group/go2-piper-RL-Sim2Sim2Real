"""Replay identical joint targets in Isaac without actor feedback or resets."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--trace-json", type=Path, required=True)
parser.add_argument("--output-json", type=Path, required=True)
parser.add_argument("--task", choices=("GO2-PIPER-Box-Climb-Play", "GO2-PIPER-Box-Push-Hybrid-Play"), default="GO2-PIPER-Box-Climb-Play")
parser.add_argument("--prescribe-root", action="store_true")
parser.add_argument("--zero-gravity", action="store_true")
parser.add_argument("--progress", action="store_true")
parser.add_argument("--capture-collider-offsets", action="store_true")
parser.add_argument("--capture-contact-details", action="store_true")
parser.add_argument("--capture-robot-materials", action="store_true")
parser.add_argument("--capture-foot-ground-forces", action="store_true")
parser.add_argument("--probe-contact-dt", action="store_true")
parser.add_argument("--fix-root-link", action="store_true")
parser.add_argument("--disable-ground", action="store_true")
parser.add_argument("--zero-effort", action="store_true")
parser.add_argument("--max-depenetration-velocity", type=float, default=None)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output_json.exists():
    parser.error("Require a new output")
if args.probe_contact_dt and not args.capture_foot_ground_forces:
    parser.error("Contact dt probe requires foot ground force capture")
if args.max_depenetration_velocity is not None and (not math.isfinite(args.max_depenetration_velocity) or args.max_depenetration_velocity <= 0):
    parser.error("Max depenetration velocity must be finite and positive")
launcher = AppLauncher(args)

import gymnasium as gym
import torch
import isaaclab_tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab.utils.math import quat_apply, quat_apply_inverse
from isaaclab.sensors import ContactSensorCfg
import LeggedManip_Lab.tasks
import omni.usd
from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics


def main():
    trace = json.loads(args.trace_json.read_text())
    if args.prescribe_root and trace.get("root_mode") != "kinematic_prescribed_each_physics_step":
        raise ValueError("Root-prescribed replay requires a matching trace")
    config = load_cfg_from_registry(args.task, "env_cfg_entry_point")
    config.scene.num_envs = 1
    config.sim.device = args.device
    config.sim.dt = trace["physics_dt"]
    if args.zero_gravity:
        config.sim.gravity = (0.0, 0.0, 0.0)
    if args.max_depenetration_velocity is not None:
        config.scene.robot.spawn.rigid_props.max_depenetration_velocity = args.max_depenetration_velocity
    if args.capture_foot_ground_forces:
        ground_plane_path = "/World/ground/terrain/GroundPlane/CollisionPlane"
        for foot in ("FL", "FR", "RL", "RR"):
            setattr(config.scene, f"ground_contact_{foot}", ContactSensorCfg(
                prim_path=f"{{ENV_REGEX_NS}}/Robot/{foot}_foot",
                filter_prim_paths_expr=[ground_plane_path],
                track_friction_forces=True,
                max_contact_data_count_per_prim=8,
            ))
    config.seed = 60
    if "Climb" in args.task:
        config.events.add_base_mass = None
    initial = trace["initial_state"]
    if args.fix_root_link:
        config.scene.robot.spawn.articulation_props.fix_root_link = True
        config.scene.robot.init_state.pos = tuple(initial["root_pose"][:3])
        config.scene.robot.init_state.rot = tuple(initial["root_pose"][3:7])
        config.events.reset_base = None
    box_initial = trace.get("box_initial_state")
    if box_initial is not None and "Push" in args.task:
        config.events.reset_box = None
        config.scene.box.init_state.pos = tuple(box_initial["root_pose"][:3])
        config.scene.box.init_state.rot = tuple(box_initial["root_pose"][3:7])
        config.scene.box.init_state.lin_vel = tuple(box_initial["root_velocity"][:3])
        config.scene.box.init_state.ang_vel = tuple(box_initial["root_velocity"][3:6])
    config.observations.policy.enable_corruption = False
    env = gym.make(args.task, cfg=config).unwrapped
    if args.progress:
        print("PIPER_REPLAY_STAGE=env_created", flush=True)
    if args.capture_foot_ground_forces:
        stage = omni.usd.get_context().get_stage()
        ground_planes = [str(prim.GetPath()) for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies())
                         if str(prim.GetPath()).startswith("/World/ground") and prim.GetTypeName() == "Plane"]
        if ground_planes != [ground_plane_path]:
            raise ValueError(f"Unexpected ground collision planes: {ground_planes}")
    try:
        env.reset()
        if args.progress:
            print("PIPER_REPLAY_STAGE=env_reset", flush=True)
        if args.disable_ground:
            stage = omni.usd.get_context().get_stage()
            for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
                if not str(prim.GetPath()).startswith("/World/ground") or not prim.HasAPI(UsdPhysics.CollisionAPI):
                    continue
                UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Set(False)
        robot = env.scene["robot"]
        names = trace["joint_names"]
        joint_ids = [robot.joint_names.index(name) for name in names]
        state = robot.data.default_root_state.clone()
        state[0, :7] = torch.tensor(initial["root_pose"], device=args.device)
        state[:, :3] += env.scene.env_origins
        velocity = torch.tensor(initial["root_velocity"], device=args.device).unsqueeze(0)
        state[:, 7:10] = velocity[:, :3]
        state[:, 10:13] = quat_apply(state[:, 3:7], velocity[:, 3:6])
        positions = robot.data.default_joint_pos.clone()
        velocities = torch.zeros_like(positions)
        positions[0, joint_ids] = torch.tensor(initial["joint_positions"], device=args.device)
        velocities[0, joint_ids] = torch.tensor(initial["joint_velocities"], device=args.device)
        if not args.fix_root_link:
            if args.progress:
                print("PIPER_REPLAY_STAGE=before_robot_root_write", flush=True)
            robot.write_root_state_to_sim(state)
            if args.progress:
                print("PIPER_REPLAY_STAGE=after_robot_root_write", flush=True)
        robot.write_joint_state_to_sim(positions, velocities)
        if args.progress:
            print("PIPER_REPLAY_STAGE=after_robot_joint_write", flush=True)
        robot.reset()
        if args.progress:
            print("PIPER_REPLAY_STAGE=after_robot_reset", flush=True)
        measured_initial_box_state = None
        if args.progress:
            print("PIPER_REPLAY_STAGE=state_written", flush=True)
        delay_by_native_joint = torch.zeros(robot.num_joints, dtype=torch.long, device=args.device)
        delay_by_native_joint[joint_ids] = torch.tensor(trace["actuator_delay_steps"], device=args.device)
        all_joints = torch.arange(robot.num_joints, device=args.device)
        for actuator in robot.actuators.values():
            delays = delay_by_native_joint[all_joints[actuator.joint_indices]].unique()
            if delays.numel() != 1:
                raise ValueError("Expected one delay per native actuator group")
            for buffer_name in ("positions_delay_buffer", "velocities_delay_buffer", "efforts_delay_buffer"):
                buffer = getattr(actuator, buffer_name)
                buffer.set_time_lag(int(delays.item()))
                buffer.reset()
            if args.zero_effort:
                actuator.stiffness[:] = 0.0
                actuator.damping[:] = 0.0
        robot.set_joint_position_target(positions)
        env.sim.forward()
        env.scene.update(0.0)
        if args.progress:
            print("PIPER_REPLAY_STAGE=initial_forward", flush=True)
        measured_initial = {
            "root_pose": torch.cat((robot.data.root_pos_w[0] - env.scene.env_origins[0], robot.data.root_quat_w[0])).tolist(),
            "joint_positions": robot.data.joint_pos[0, joint_ids].tolist(),
            "joint_velocities": robot.data.joint_vel[0, joint_ids].tolist(),
        }
        if args.fix_root_link and not torch.allclose(
            torch.tensor(measured_initial["root_pose"], device=args.device),
            torch.tensor(initial["root_pose"], device=args.device), atol=1e-5, rtol=0.0,
        ):
            raise ValueError("Fixed-root initial pose differs from the source trace")
        gravity_compensation = robot.root_physx_view.get_gravity_compensation_forces()[0, joint_ids].tolist()
        if args.progress:
            print("PIPER_REPLAY_STAGE=measured_initial", flush=True)
        if "box_initial_state" in trace and "Push" in args.task:
            measured_initial_box_state = {
                "root_pose": torch.cat((
                    env.scene["box"].data.root_pos_w[0] - env.scene.env_origins[0],
                    env.scene["box"].data.root_quat_w[0],
                )).tolist(),
                "root_velocity": env.scene["box"].data.root_vel_w[0].tolist(),
            }
        collider_offsets = []
        foot_colliders = {}
        if args.capture_collider_offsets or args.capture_foot_ground_forces:
            stage = omni.usd.get_context().get_stage()
            transforms = UsdGeom.XformCache()
            for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
                if "/env_0/Robot/" not in str(prim.GetPath()) or not prim.HasAPI(UsdPhysics.CollisionAPI):
                    continue
                collision = PhysxSchema.PhysxCollisionAPI(prim)
                body_name = str(prim.GetPath()).split("/Robot/", 1)[1].split("/", 1)[0]
                body_index = robot.body_names.index(body_name)
                body_prim = stage.GetPrimAtPath(f"/World/envs/env_0/Robot/{body_name}")
                body_transform = transforms.GetLocalToWorldTransform(body_prim)
                local_transform = body_transform.GetInverse() * transforms.GetLocalToWorldTransform(prim)
                local_position = torch.tensor(list(local_transform.ExtractTranslation()), device=args.device, dtype=robot.data.body_pos_w.dtype)
                position = robot.data.body_pos_w[0, body_index] + quat_apply(
                    robot.data.body_quat_w[0, body_index].unsqueeze(0), local_position.unsqueeze(0),
                )[0]
                if args.capture_collider_offsets:
                    collider_offsets.append({
                        "prim": str(prim.GetPath()),
                        "type": prim.GetTypeName(),
                        "world_position": (position - env.scene.env_origins[0]).tolist(),
                        "sphere_radius": UsdGeom.Sphere(prim).GetRadiusAttr().Get() if prim.IsA(UsdGeom.Sphere) else None,
                        "contact_offset": collision.GetContactOffsetAttr().Get(),
                        "rest_offset": collision.GetRestOffsetAttr().Get(),
                        "offsets_explicitly_set": collision.GetContactOffsetAttr().HasAuthoredValueOpinion() and collision.GetRestOffsetAttr().HasAuthoredValueOpinion(),
                    })
                if args.capture_foot_ground_forces and body_name in ("FL_foot", "FR_foot", "RL_foot", "RR_foot") and prim.IsA(UsdGeom.Sphere):
                    foot = body_name[:2]
                    if foot in foot_colliders:
                        raise ValueError(f"Multiple foot spheres for {foot}")
                    foot_colliders[foot] = (body_index, local_position, float(UsdGeom.Sphere(prim).GetRadiusAttr().Get()))
            if args.capture_collider_offsets and not collider_offsets:
                raise ValueError("No native colliders found; contact-offset evidence is incomplete")
            if args.capture_foot_ground_forces and set(foot_colliders) != {"FL", "FR", "RL", "RR"}:
                raise ValueError(f"Expected four foot spheres, found {sorted(foot_colliders)}")
        if args.progress:
            print("PIPER_REPLAY_STAGE=collider_offsets", flush=True)
        actuator_parameters = {}
        for group_name, actuator in robot.actuators.items():
            values = {}
            for attribute in (
                "joint_names", "joint_indices", "stiffness", "damping", "armature", "friction",
                "dynamic_friction", "viscous_friction", "effort_limit", "velocity_limit",
            ):
                if not hasattr(actuator, attribute):
                    continue
                value = getattr(actuator, attribute)
                if torch.is_tensor(value):
                    value = value.detach().cpu().tolist()
                values[attribute] = value
            actuator_parameters[group_name] = values
        if args.progress:
            print("PIPER_REPLAY_STAGE=actuator_parameters", flush=True)
        physx_joint_parameters = {
            "damping": robot.root_physx_view.get_dof_dampings()[0].tolist(),
            "armature": robot.root_physx_view.get_dof_armatures()[0].tolist(),
            "friction_coefficients": robot.root_physx_view.get_dof_friction_coefficients()[0].tolist(),
            "friction_properties": robot.root_physx_view.get_dof_friction_properties()[0].tolist(),
        }
        if args.progress:
            print("PIPER_REPLAY_STAGE=physx_joint_parameters", flush=True)
        physx_body_parameters = {
            "masses": robot.root_physx_view.get_masses()[0].tolist(),
            "inertias": robot.root_physx_view.get_inertias()[0].tolist(),
            "coms": robot.root_physx_view.get_coms()[0].tolist(),
        }
        robot_materials = None
        if args.capture_robot_materials:
            robot_materials = robot.root_physx_view.get_material_properties()[0].tolist()
        if args.progress:
            print("PIPER_REPLAY_STAGE=physx_body_parameters", flush=True)
        contacts = env.scene["contact_forces"]
        hand_box_contacts = env.scene["box_contact_hand"]
        ground_contacts = {foot: env.scene[f"ground_contact_{foot}"] for foot in ("FL", "FR", "RL", "RR")} if args.capture_foot_ground_forces else {}
        rows = []
        if args.progress:
            print("PIPER_REPLAY_STAGE=sensors_ready", flush=True)
        if args.progress:
            print("PIPER_REPLAY_STAGE=loop_start", flush=True)

        def write_prescribed_root(source):
            if args.fix_root_link:
                return
            prescribed = robot.data.default_root_state.clone()
            prescribed[0, :7] = torch.tensor(source["root_pose"], device=args.device)
            prescribed[:, :3] += env.scene.env_origins
            velocity = torch.tensor(source["root_velocity"], device=args.device).unsqueeze(0)
            prescribed[:, 7:10] = velocity[:, :3]
            prescribed[:, 10:13] = quat_apply(prescribed[:, 3:7], velocity[:, 3:6])
            robot.write_root_state_to_sim(prescribed)

        for source in trace["steps"]:
            if args.progress and source["physics_step"] < 3:
                print(f"PIPER_REPLAY_STAGE=step_{source['physics_step']}", flush=True)
            if args.prescribe_root:
                write_prescribed_root(source)
            positions[0, joint_ids] = torch.tensor(source["target"], device=args.device)
            robot.set_joint_position_target(positions)
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=before_data_write", flush=True)
            env.scene.write_data_to_sim()
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=after_data_write", flush=True)
            torque_before_step = robot.data.applied_torque[0, joint_ids].tolist()
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=before_sim_step", flush=True)
            env.sim.step(render=False)
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=after_sim_step", flush=True)
            env.scene.update(config.sim.dt)
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=after_scene_update", flush=True)
            torque = robot.data.applied_torque[0, joint_ids].tolist()
            solver_root_position = robot.data.root_pos_w[0] - env.scene.env_origins[0]
            solver_quaternion = robot.data.root_quat_w[0]
            solver_angular = quat_apply_inverse(solver_quaternion.unsqueeze(0), robot.data.root_ang_vel_w)[0]
            contact_forces_before_root_restore = contacts.data.net_forces_w[0].tolist()
            foot_ground_forces = {
                foot: {
                    "filtered_force_w": sensor.data.force_matrix_w[0].sum(dim=(0, 1)).tolist(),
                    "friction_force_w": sensor.data.friction_forces_w[0].sum(dim=(0, 1)).tolist(),
                }
                for foot, sensor in ground_contacts.items()
            }
            contact_dt_probe = None
            if args.probe_contact_dt and source["physics_step"] == 0:
                contact_dt_probe = {
                    foot: {
                        "normal_half_dt_w": sensor.contact_physx_view.get_contact_force_matrix(
                            dt=config.sim.dt / 2
                        ).view(1, 1, -1, 3)[0].sum(dim=(0, 1)).tolist(),
                        "friction_half_dt_w": sensor.contact_physx_view.get_friction_data(
                            dt=config.sim.dt / 2
                        )[0].sum(dim=0).tolist(),
                    }
                    for foot, sensor in ground_contacts.items()
                }
            foot_spheres_before_root_restore = {}
            for foot, (body_index, local_position, radius) in foot_colliders.items():
                center = robot.data.body_pos_w[0, body_index] + quat_apply(
                    robot.data.body_quat_w[0, body_index].unsqueeze(0), local_position.unsqueeze(0),
                )[0] - env.scene.env_origins[0]
                foot_spheres_before_root_restore[foot] = {
                    "center_w": center.tolist(), "radius": radius, "bottom_z": center[2].item() - radius,
                }
            if args.prescribe_root:
                write_prescribed_root(source)
                env.scene.write_data_to_sim()
                env.sim.forward()
                env.scene.update(0.0)
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=after_root_restore", flush=True)
            body_positions = (robot.data.body_pos_w[0] - env.scene.env_origins[0]).tolist()
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=body_positions", flush=True)
            contact_forces = contacts.data.net_forces_w[0].tolist()
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=contact_forces", flush=True)
            hand_force = hand_box_contacts.data.force_matrix_w[0].sum(dim=(0, 1)).tolist()
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=hand_force", flush=True)
            hand_time = None
            hand_position = None
            if args.capture_contact_details:
                hand_time = hand_box_contacts.data.current_contact_time[0].tolist()
                if args.progress and source["physics_step"] == 0:
                    print("PIPER_REPLAY_STAGE=hand_time", flush=True)
                hand_position = hand_box_contacts.data.contact_pos_w[0].tolist()
                if args.progress and source["physics_step"] == 0:
                    print("PIPER_REPLAY_STAGE=hand_position", flush=True)
            root_position = robot.data.root_pos_w[0] - env.scene.env_origins[0]
            quaternion = robot.data.root_quat_w[0]
            angular = quat_apply_inverse(quaternion.unsqueeze(0), robot.data.root_ang_vel_w)[0]
            rows.append({
                "physics_step": source["physics_step"], "time": (source["physics_step"] + 1) * config.sim.dt,
                "root_pose": torch.cat((root_position, quaternion)).tolist(),
                "root_velocity": torch.cat((robot.data.root_link_lin_vel_w[0], angular)).tolist(),
                "solver_root_pose": torch.cat((solver_root_position, solver_quaternion)).tolist(),
                "solver_root_velocity": torch.cat((robot.data.root_link_lin_vel_w[0], solver_angular)).tolist(),
                "target": source["target"], "torque": torque, "torque_before_step": torque_before_step,
                "solver_positions": robot.data.joint_pos[0, joint_ids].tolist(),
                "solver_velocities": robot.data.joint_vel[0, joint_ids].tolist(),
                "body_positions": body_positions,
                "contact_forces": contact_forces,
                "contact_forces_before_root_restore": contact_forces_before_root_restore,
                "foot_ground_forces_before_root_restore": foot_ground_forces,
                **({"contact_dt_probe": contact_dt_probe} if contact_dt_probe is not None else {}),
                "foot_spheres_before_root_restore": foot_spheres_before_root_restore,
                "box_contact_hand_force": hand_force,
                "box_contact_hand_time": hand_time,
                "box_contact_hand_position": hand_position,
            })
            if args.progress and source["physics_step"] == 0:
                print("PIPER_REPLAY_STAGE=row_written", flush=True)
        report = {
            "schema_version": 1, "backend": "isaac", "diagnostic_only": True, "task": args.task,
            "contact_force_sampling": {
                "contact_forces_before_root_restore": "sensor net normal body contact force after scene.update(dt), from get_net_contact_forces(dt=physics_dt)",
                "contact_forces": "same sensor net normal body contact force after root restore and scene.update(0); no ground filter",
                "foot_ground_forces_before_root_restore": "per-foot ground-filtered normal force matrix and separately summed friction forces after scene.update(dt); both queried with dt=physics_dt, not a post-step forward solve",
            },
            "root_mode": "fixed" if args.fix_root_link else trace.get("root_mode") if args.prescribe_root else "free",
            "trace_sha256": hashlib.sha256(args.trace_json.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "physics_dt": config.sim.dt, "joint_names": names, "initial_state": initial,
            "zero_gravity": args.zero_gravity,
            "zero_effort": args.zero_effort,
            "fix_root_link": args.fix_root_link,
            "disable_ground": args.disable_ground,
            "max_depenetration_velocity": config.scene.robot.spawn.rigid_props.max_depenetration_velocity,
            "measured_initial_state": measured_initial,
            "gravity_compensation_forces": gravity_compensation,
            "measured_initial_box_state": measured_initial_box_state,
            "joint_ranges": robot.root_physx_view.get_dof_limits()[0, joint_ids].tolist(),
            "collider_offsets": collider_offsets, "contact_body_names": list(contacts.body_names),
            "masses": robot.root_physx_view.get_masses()[0].tolist(),
            "body_names": list(robot.body_names), "actuator_parameters": actuator_parameters,
            "physx_joint_parameters": physx_joint_parameters, "physx_body_parameters": physx_body_parameters,
            "robot_material_properties": robot_materials,
            "steps": rows,
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with args.output_json.open("x") as destination:
            json.dump(report, destination, indent=2, allow_nan=False)
        print(f"PIPER_REPLAY steps={len(rows)} output={args.output_json}", flush=True)
    finally:
        env.close()


try:
    main()
finally:
    launcher.app.close()