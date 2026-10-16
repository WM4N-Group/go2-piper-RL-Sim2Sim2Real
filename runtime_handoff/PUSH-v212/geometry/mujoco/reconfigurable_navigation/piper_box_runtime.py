"""PIPER box-skill scene and runtimes with explicit robot configuration."""

from pathlib import Path
from functools import partial
import json

import mujoco
import numpy as np
import yaml

from .box_climb_runtime import BoxClimbRuntime
from .box_push_runtime import BoxPushRuntime
from .piper_locomotion_runtime import DEPLOY, JOINT_NAMES, ROOT
from .piper_robot_profile import apply_piper_collision_profile, apply_piper_robot_profile
from .velocity_projection import project_joint_velocities


PIPER_ARM_BODIES = frozenset(("Piper", "link1", "link2", "link3", "link4", "link5", "link6", "link7", "link8"))
PIPER_ADJACENT_BODY_PAIRS = frozenset(
    frozenset(pair) for pair in (
        ("base_link", "Piper"),
        ("Piper", "link1"),
        ("link1", "link2"),
        ("link2", "link3"),
        ("link3", "link4"),
        ("link4", "link5"),
        ("link5", "link6"),
        ("link6", "link7"),
        ("link6", "link8"),
    )
)

PIPER_SAFE_APPROACH_PATH = ROOT / "deploy/piper_push_safe_approach.json"


def load_piper_safe_approach():
    payload = json.loads(PIPER_SAFE_APPROACH_PATH.read_text())
    if payload["schema_version"] != 1 or payload["robot"] != "go2_piper":
        raise ValueError("Expected a GO2-PIPER safe approach path")
    return payload


def add_piper_collision_excludes(spec, robot_bodies, native_collisions):
    for index, first in enumerate(robot_bodies):
        for second in robot_bodies[index + 1:]:
            pair = frozenset((first, second))
            first_is_arm = first in PIPER_ARM_BODIES
            second_is_arm = second in PIPER_ARM_BODIES
            if (
                not native_collisions
                or pair in PIPER_ADJACENT_BODY_PAIRS
                or not first_is_arm and not second_is_arm
            ):
                spec.add_exclude(bodyname1=first, bodyname2=second)


def attach_piper_collision_monitor(runtime):
    model, data = runtime.model, runtime.data
    arm_bodies = {model.body(name).id for name in PIPER_ARM_BODIES}
    robot_bodies = {index for index in range(1, model.nbody) if model.body(index).name != "push_box"}
    runtime.self_collision = None
    runtime.collision_checks = 0

    def monitor():
        runtime.collision_checks += 1
        for contact in data.contact[:data.ncon]:
            first = int(model.geom_bodyid[contact.geom1])
            second = int(model.geom_bodyid[contact.geom2])
            if first not in robot_bodies or second not in robot_bodies:
                continue
            if first not in arm_bodies and second not in arm_bodies:
                continue
            if runtime.self_collision is None:
                runtime.self_collision = {
                    "time": float(data.time), "distance": float(contact.dist),
                    "kind": "penetration" if contact.dist < 0.0 else "contact_margin",
                    "bodies": [model.body(first).name, model.body(second).name],
                    "geoms": [model.geom(int(contact.geom1)).name, model.geom(int(contact.geom2)).name],
                }

    runtime.on_safety_step = monitor


def make_episode(skill, policy, seed, height=0.20, *, push_ik_mode="position", native_collisions=False, velocity_mode="legacy", constraint_substeps=1, contact_time_constant=None, contact_damping_ratio=None, contact_impedance=None, contact_width=None, contact_margin=0.0, push_height_offset=0.0, push_hand_pitch=0.8, projection_contacts=True, push_safe_precontact=False, push_current_contract=False, fix_root_link=False, fixed_root_pose=None, disable_floor=False):
    if skill not in ("push", "climb") or not np.isfinite(height) or height <= 0:
        raise ValueError("Expected PUSH/CLIMB and a positive height")
    if push_ik_mode not in ("position", "pose"):
        raise ValueError("Unknown PUSH IK mode")
    if velocity_mode not in ("legacy", "coupled", "coupled-bounds"):
        raise ValueError("Unknown velocity constraint mode")
    if push_safe_precontact and (skill != "push" or not native_collisions):
        raise ValueError("Online precontact requires the native-collision PUSH scene")
    if push_current_contract and (skill != "push" or not native_collisions or push_safe_precontact or push_ik_mode != "pose"):
        raise ValueError("Current PUSH transfer requires native collisions and ordinary pose Tracking")
    if constraint_substeps not in (1, 2):
        raise ValueError("Constraint substeps must be 1 or 2")
    if contact_time_constant is not None and (not np.isfinite(contact_time_constant) or contact_time_constant < 0.01):
        raise ValueError("Contact time constant must be at least 0.01 s")
    if contact_damping_ratio is not None and (not np.isfinite(contact_damping_ratio) or contact_damping_ratio <= 0.0):
        raise ValueError("Contact damping ratio must be positive")
    if contact_impedance is not None and (not np.isfinite(contact_impedance) or not 0.0 < contact_impedance < 0.95):
        raise ValueError("Contact impedance must be between 0 and 0.95")
    if contact_width is not None and (not np.isfinite(contact_width) or not 0.0 < contact_width <= 0.05):
        raise ValueError("Contact width must be between 0 and 0.05 m")
    if not np.isfinite(contact_margin) or not 0.0 <= contact_margin <= 0.01:
        raise ValueError("Contact margin must be between 0 and 0.01 m")
    if not np.isfinite(push_height_offset) or not -0.03 <= push_height_offset <= 0.03:
        raise ValueError("PUSH height offset must be between -0.03 and 0.03 m")
    if not np.isfinite(push_hand_pitch) or not 0.0 <= push_hand_pitch <= 1.2:
        raise ValueError("PUSH hand pitch must be between 0 and 1.2 rad")
    spec = mujoco.MjSpec.from_file(str(ROOT / "robots/go2_piper/go2piper.xml"))
    for mesh in spec.meshes:
        mesh.file = str(ROOT / "robots/go2_piper/assets" / Path(mesh.file).name)
    if fix_root_link:
        if fixed_root_pose is None or len(fixed_root_pose) != 7:
            raise ValueError("Fixed-root episodes require a seven-element root pose")
        root_body = spec.body("base_link")
        root_body.pos = fixed_root_pose[:3]
        root_body.quat = fixed_root_pose[3:7]
        spec.delete(root_body.joints[0])
    apply_piper_robot_profile(spec)
    if native_collisions:
        apply_piper_collision_profile(spec)
    for geom in spec.geoms:
        if not geom.contype and not geom.conaffinity:
            geom.group = 2
        elif not native_collisions:
            geom.group = 3
    robot_bodies = [body.name for body in spec.bodies if body.name and body.name != "world"]
    add_piper_collision_excludes(spec, robot_bodies, native_collisions)
    if not disable_floor:
        spec.worldbody.add_geom(name="floor", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[0, 0, 0.05], friction=[0.6, 0, 0], priority=1, condim=3)
    if skill == "push":
        box = spec.worldbody.add_body(name="push_box", pos=[1.10, 0.0, height / 2])
        box.add_freejoint(name="push_box_joint")
        box.add_geom(name="push_box", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.6, 0.6, height / 2], mass=5.0, friction=[0.4, 0, 0], priority=2, condim=3)
    else:
        spec.worldbody.add_geom(name="support_box", type=mujoco.mjtGeom.mjGEOM_BOX, pos=[1.35, 0, height / 2], size=[0.6, 0.6, height / 2], friction=[0.6, 0, 0], priority=1, condim=3)
    model = spec.compile()
    if contact_time_constant is not None:
        model.geom_solref[:, 0] = contact_time_constant
    if contact_damping_ratio is not None:
        model.geom_solref[:, 1] = contact_damping_ratio
    if contact_impedance is not None:
        model.geom_solimp[:, 0] = contact_impedance
    if contact_width is not None:
        model.geom_solimp[:, 2] = contact_width
    if contact_margin:
        robot_body_ids = {model.body(name).id for name in robot_bodies}
        model.geom_margin[np.isin(model.geom_bodyid, list(robot_body_ids))] = contact_margin
    data = mujoco.MjData(model)
    with (DEPLOY / "config.yaml").open() as source:
        config = yaml.safe_load(source)
    config["kps"][:12] = [30.0] * 12
    config["kds"][:12] = [0.6] * 12
    options = {"model": model, "data": data, "deploy_config": config, "joint_names": JOINT_NAMES, "base_body_name": "base_link"}
    if skill == "push":
        box_id = model.geom("push_box").id
        safe_approach = load_piper_safe_approach() if native_collisions else None
        runtime = BoxPushRuntime(policy, box_geom=box_id, goal=np.array([1.7, 0, height / 2]), arm_config={
            "hand_body_name": "end_effector", "mount_body_name": "Piper",
            "hand_body_names": ("link6", "link7", "link8"), "hand_offset": (0, 0, 0),
            "align_hand_orientation": push_ik_mode == "pose", "hand_pitch": push_hand_pitch if push_ik_mode == "pose" else 0.0,
            "approach_distance": 0.03 if push_ik_mode == "pose" else 0.10,
            "hand_height_offset": push_height_offset,
            "collision_arm_body_names": ("link1", "link2", "link3", "link4", "link5", "link6"),
            "collision_protected_body_names": ("base_link", "FL_hip", "FL_thigh", "FL_calf", "FL_foot", "FR_hip", "FR_thigh", "FR_calf", "FR_foot", "RL_hip", "RL_thigh", "RL_calf", "RL_foot", "RR_hip", "RR_thigh", "RR_calf", "RR_foot"),
            "collision_clearance": 0.015 if native_collisions else 0.0,
            "body_clearance_minimum": 0.10 if push_current_contract else 0.0,
            "safe_approach_waypoints": () if safe_approach is None else safe_approach["waypoints"],
            "safe_approach_position_tolerance": 0.04 if safe_approach is None else safe_approach["settle_position_tolerance_rad"],
            "safe_approach_velocity_tolerance": 0.12 if safe_approach is None else safe_approach["settle_velocity_tolerance_rad_s"],
            "safe_approach_hold": native_collisions and not push_safe_precontact and not push_current_contract,
            "safe_precontact": push_safe_precontact,
            "press_depth": 0.10 if push_current_contract else 0.02,
            "press_on_legal_contact": push_current_contract,
            "lock_arm_on_contact": not push_current_contract,
            "leg_release_ramp_s": 0.7 if push_current_contract else 0.0,
            "leg_contact_ramp_s": 0.2 if push_current_contract else 0.0,
            "forward_command_gain": 2.0 if push_current_contract else 1.0,
            "stop_distance": 0.11 if push_current_contract else 0.10,
            "source_bounded_pose_ik": push_current_contract,
            "orientation_weight": 0.5 if push_current_contract else 1.0,
        }, **options)
    else:
        runtime = BoxClimbRuntime(policy, linear_velocity_at_com=True, **options)
    runtime.constraint_substeps = constraint_substeps
    model.opt.timestep = runtime.sim_dt / constraint_substeps
    runtime.joint_velocity_limits[12:] = 3.0
    if velocity_mode != "legacy":
        runtime.velocity_projector = partial(project_joint_velocities, position_limits=velocity_mode == "coupled-bounds", preserve_contacts=projection_contacts)
    if native_collisions:
        attach_piper_collision_monitor(runtime)
    generator = np.random.default_rng(seed)
    span = (0.03, 0.03, 0.04) if skill == "push" else (0.10, 0.08, 0.06)
    if not fix_root_link:
        data.qpos[:3] = [generator.uniform(-span[0], span[0]), generator.uniform(-span[1], span[1]), 0.33]
        yaw = generator.uniform(-span[2], span[2])
        data.qpos[3:7] = [np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]
    joint_ids = model.dof_jntid[runtime.joint_dof_adr]
    midpoints = model.jnt_range[joint_ids].mean(axis=1)
    half_ranges = np.ptp(model.jnt_range[joint_ids], axis=1) * 0.45
    spread = 0.05 if skill == "push" else 0.1
    data.qpos[runtime.joint_qpos_adr] = np.clip(runtime.default_qpos * generator.uniform(1-spread, 1+spread, 18), midpoints-half_ranges, midpoints+half_ranges)
    if skill == "push":
        box_position = data.joint("push_box_joint").qpos
        box_position[:2] += generator.uniform(-0.03, 0.03, 2)
        yaw = generator.uniform(-0.04, 0.04)
        box_position[3:7] = [np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]
    mujoco.mj_forward(model, data)
    if skill == "push":
        runtime.arm.goal = data.geom_xpos[box_id].copy() + [0.6, 0, 0]
    runtime.activate()
    return runtime
