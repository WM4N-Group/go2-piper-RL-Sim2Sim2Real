"""PIPER-specific robot configurations for the existing physical box tasks."""

import json
from pathlib import Path

from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.utils import configclass

from LeggedManip_Lab.assets.go2_piper.go2_piper_articulation_cfg import GO2_PIPER_CFG

from ... import mdp
from ..go2_arx5.box_climb_env_cfg import Go2ARX5BoxClimbEnvCfg
from ..go2_arx5.box_push_env_cfg import Go2ARX5BoxPushHybridEnvCfg
from ...mdp import box_push
from ...mdp.box_climb import box_target_delta


PIPER_ARM_EFFORT_LIMITS = (20.0, 20.0, 15.0, 7.0, 5.0, 5.0)
PIPER_SAFE_APPROACH_PATH = Path(__file__).resolve().parents[8] / "mujoco/deploy/piper_push_safe_approach.json"


def piper_safe_approach_config():
    payload = json.loads(PIPER_SAFE_APPROACH_PATH.read_text())
    if payload["schema_version"] != 1 or payload["robot"] != "go2_piper":
        raise ValueError("Expected a GO2-PIPER safe approach path")
    return payload


def climb_target_distance(env):
    return box_target_delta(env)[:, :2].norm(dim=1)


def piper_box_robot_cfg(arm_joint_positions=None):
    robot = GO2_PIPER_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    robot.init_state.pos = (0.0, 0.0, 0.33)
    effort = {".*_hip_joint": 23.7, ".*_thigh_joint": 23.7, ".*_calf_joint": 45.43}
    velocity = {".*_hip_joint": 30.1, ".*_thigh_joint": 30.1, ".*_calf_joint": 15.7}
    legs = robot.actuators["base_legs"]
    legs.effort_limit = effort.copy()
    legs.effort_limit_sim = effort.copy()
    legs.velocity_limit = velocity.copy()
    legs.velocity_limit_sim = velocity.copy()
    for index, limit in enumerate(PIPER_ARM_EFFORT_LIMITS, 1):
        actuator = robot.actuators[f"joint{index}"]
        actuator.effort_limit = limit
        actuator.effort_limit_sim = limit
        actuator.velocity_limit = 3.0
        actuator.velocity_limit_sim = 3.0
    robot.spawn.articulation_props.solver_position_iteration_count = 8
    robot.spawn.articulation_props.solver_velocity_iteration_count = 2
    if arm_joint_positions is not None:
        if len(arm_joint_positions) != 6:
            raise ValueError("Expected six PIPER arm joint positions")
        robot.init_state.joint_pos.pop("joint.*", None)
        robot.init_state.joint_pos.update({
            f"joint{index}": float(position)
            for index, position in enumerate(arm_joint_positions, 1)
        })
    return robot


@configclass
class Go2PiperBoxPushHybridEnvCfg(Go2ARX5BoxPushHybridEnvCfg):
    box_size: tuple[float, float, float] = (1.2, 1.2, 0.20)
    push_hand_height_offset: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        self.scene.robot = piper_box_robot_cfg()
        self.actions.joint_pos.lock_arm_on_contact = True
        self.actions.joint_pos.align_hand_orientation = True
        self.actions.joint_pos.hand_pitch = 0.8
        safe_approach = piper_safe_approach_config()
        self.actions.joint_pos.safe_approach_waypoints = tuple(
            tuple(waypoint) for waypoint in safe_approach["waypoints"]
        )
        self.actions.joint_pos.safe_approach_position_tolerance = safe_approach["settle_position_tolerance_rad"]
        self.actions.joint_pos.safe_approach_velocity_tolerance = safe_approach["settle_velocity_tolerance_rad_s"]
        self.push_approach_distance = 0.03
        failures = (*self.rewards.completion.params["failure_terms"], "arm_body_clearance")
        self.rewards.completion.params["failure_terms"] = failures
        self.rewards.physical_failure.params["failure_terms"] = failures
        self.terminations.arm_body_clearance = DoneTerm(
            func=mdp.arm_body_clearance_violation,
            params={"min_distance": 0.08},
        )
        self.rewards.completion.weight = 150.0
        self.rewards.box_goal.weight = 0.0
        self.rewards.end_effector_position_tracking_exp.weight = 0.0
        self.rewards.track_base_height_exp.weight = 0.0
        self.rewards.track_ang_vel_z_exp.weight = 0.0
        self.rewards.hand_contact.weight = 0.0
        self.rewards.track_lin_vel_xy_exp.weight = 6.0


@configclass
class Go2PiperBoxPushLowEnvCfg(Go2PiperBoxPushHybridEnvCfg):
    """ARX5 low-board task geometry with the validated PIPER precontact offset."""

    box_size: tuple[float, float, float] = (1.10, 0.48, 0.08)
    push_distance: float = 0.90
    push_approach_distance: float = 0.08
    push_contact_height_offset: float = -0.005
    push_contact_height_margin: float = 0.0
    push_contact_tip_radius: float = 0.12
    push_approach_height_tolerance: float = 0.015
    push_hold_legs_until_ready: bool = True
    push_release_on_hand_contact: bool = True
    push_full_body_preapproach: bool = True
    push_preapproach_base_gap: float = 0.36
    push_contact_base_gap: float = 0.35
    push_min_base_gap: float = 0.32
    push_preapproach_base_height: float = 0.28
    push_preapproach_gap_tolerance: float = 0.07
    push_preapproach_lateral_tolerance: float = 0.08
    push_preapproach_height_tolerance: float = 0.035
    push_preapproach_linear_speed: float = 0.06
    push_preapproach_angular_speed: float = 0.20
    push_preapproach_hold_time: float = 0.50
    push_preapproach_leg_action_scale: float = 0.15
    push_preapproach_arm_rate_scale: float = 0.25
    push_precontact_arm_rate_scale: float = 1.0
    push_precontact_posture: tuple[float, ...] = (-0.310836, 2.967048, -1.563753, 0.502395, 0.531252, 0.932656)
    push_precontact_position_tolerance: float = 0.04

    def __post_init__(self):
        super().__post_init__()
        self.episode_length_s = 24.0
        self.actions.joint_pos.lock_arm_on_contact = False
        self.actions.joint_pos.align_hand_orientation = False
        self.scene.box.spawn.size = self.box_size
        self.scene.box.spawn.mass_props.mass = 2.5
        self.scene.box.spawn.physics_material.static_friction = 0.7
        self.scene.box.spawn.physics_material.dynamic_friction = 0.7
        self.scene.box.init_state.pos = (0.94, 0.0, self.box_size[2] / 2.0)
        self.events.box_mass.params["mass_distribution_params"] = (2.0, 3.5)
        self.events.box_material.params["static_friction_range"] = (0.5, 0.9)
        self.events.box_material.params["dynamic_friction_range"] = (0.5, 0.9)
        self.rewards.preapproach = RewTerm(func=box_push.preapproach_reward, weight=4.0)
        self.rewards.track_base_height_exp.params["target_height"] = self.push_preapproach_base_height
        self.terminations.preapproach_timeout = DoneTerm(func=box_push.preapproach_timeout, params={"timeout": 4.0})


@configclass
class Go2PiperBoxPushLowEnvCfg_PLAY(Go2PiperBoxPushLowEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.events.box_mass = None
        self.events.box_material = None


@configclass
class Go2PiperBoxPushHybridEnvCfg_PLAY(Go2PiperBoxPushHybridEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.events.box_mass = None
        self.events.box_material = None


@configclass
class Go2PiperBoxPushTrackingEnvCfg(Go2PiperBoxPushHybridEnvCfg):
    # Keep training and evaluation on the same optional IK controller contract.
    push_ik_clearance_minimum: float | None = None
    push_ik_orientation_weight: float = 1.0
    push_ik_height_weight: float = 1.0
    push_ik_joint_limit_solve: bool = False
    push_goal_hold_pose: bool = False
    push_goal_release_distance: float = 0.0
    push_goal_brake_gain: float = 0.0
    push_press_on_legal_contact: bool = False
    push_stop_distance: float = 0.10
    push_leg_release_on_contact: bool = False
    push_contact_memory_s: float = 0.0
    push_leg_release_ramp_s: float = 0.0
    push_leg_contact_ramp_s: float = 0.0
    push_forward_command_gain: float = 1.0
    push_contact_gap_slowdown_start: float = 0.0
    push_target_maximum_reach: float = 0.0
    push_velocity_feedback_gain: float = 0.0
    push_velocity_integral_gain: float = 0.0
    push_body_first: bool = False
    push_preapproach_base_gap: float = 0.46
    push_preapproach_base_height: float = 0.28
    push_preapproach_leg_action_scale: float = 1.0

    def __post_init__(self):
        super().__post_init__()
        self.actions.joint_pos.lock_arm_on_contact = False
        self.rewards.end_effector_position_tracking_exp.weight = 2.0
        self.rewards.hand_contact.weight = 1.0


@configclass
class Go2PiperBoxPushTrackingEnvCfg_PLAY(Go2PiperBoxPushTrackingEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.events.box_mass = None
        self.events.box_material = None


@configclass
class Go2PiperBoxPushSafeBaseEnvCfg(Go2PiperBoxPushHybridEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        safe_approach = piper_safe_approach_config()
        self.scene.robot = piper_box_robot_cfg(safe_approach["waypoints"][-1])
        self.actions.joint_pos.safe_approach_start_complete = True
        self.actions.joint_pos.safe_approach_hold = True
        self.actions.joint_pos.legs_active_after_safe_approach = True
        self.rewards.completion.weight = 0.0
        self.rewards.box_progress.weight = 0.0
        self.rewards.box_goal.weight = 0.0
        self.rewards.hand_contact.weight = 0.0
        self.rewards.track_lin_vel_xy_exp.weight = 6.0
        self.rewards.track_base_height_exp.weight = 4.0
        self.rewards.track_base_height_exp.params = {"target_height": 0.33, "std": 0.03}
        self.rewards.flat_orientation_l2.weight = -4.0
        self.rewards.lin_vel_z_l2.weight = -4.0
        self.rewards.ang_vel_xy_l2.weight = -0.2
        self.rewards.action_rate_l2.weight = -0.03


@configclass
class Go2PiperBoxPushSafeBaseEnvCfg_PLAY(Go2PiperBoxPushSafeBaseEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.events.box_mass = None
        self.events.box_material = None


@configclass
class Go2PiperBoxClimbEnvCfg(Go2ARX5BoxClimbEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.robot = piper_box_robot_cfg()
        self.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (0.05, 0.20)
        self.rewards.completion.weight = 200.0
        self.rewards.box_standing.weight = 1.0
        self.rewards.box_support.weight = 1.0
        self.rewards.box_clearance.weight = 0.5
        self.rewards.posture_failure.weight = -30.0
        self.rewards.box_center_distance = RewTerm(func=climb_target_distance, weight=-1.0)


@configclass
class Go2PiperBoxClimbEnvCfg_PLAY(Go2PiperBoxClimbEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.scene.terrain.max_init_terrain_level = None
        self.scene.terrain.terrain_generator.curriculum = False
        self.scene.terrain.terrain_generator.num_rows = 1
        self.scene.terrain.terrain_generator.num_cols = 4
        self.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (0.20, 0.20)
        self.curriculum.terrain_levels = None


@configclass
class Go2PiperBoxClimbSmoothEnvCfg(Go2PiperBoxClimbEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.rewards.action_rate_l2.weight = -0.12
        self.rewards.dof_acc_l2.weight = -1.0e-6
        self.rewards.dof_torques_l2.weight = -4.0e-5
        self.rewards.ang_vel_xy_l2.weight = -0.5
        self.rewards.flat_orientation_l2.weight = -4.0


@configclass
class Go2PiperBoxClimbSmoothEnvCfg_PLAY(Go2PiperBoxClimbSmoothEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.scene.terrain.max_init_terrain_level = None
        self.scene.terrain.terrain_generator.curriculum = False
        self.scene.terrain.terrain_generator.num_rows = 1
        self.scene.terrain.terrain_generator.num_cols = 4
        self.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (0.20, 0.20)
        self.curriculum.terrain_levels = None


@configclass
class Go2PiperBoxClimbRobustEnvCfg(Go2PiperBoxClimbEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.randomize_actuator_gains = EventTerm(
            func=mdp.randomize_actuator_gains,
            mode="reset",
            params={
                "asset_cfg": SceneEntityCfg("robot", joint_names=".*"),
                "stiffness_distribution_params": (0.85, 1.15),
                "damping_distribution_params": (0.8, 1.2),
                "operation": "scale",
            },
        )
        self.events.physics_material.params.update(
            static_friction_range=(0.7, 0.9),
            dynamic_friction_range=(0.5, 0.7),
            restitution_range=(0.0, 0.02),
        )


@configclass
class Go2PiperBoxClimbRobustEnvCfg_PLAY(Go2PiperBoxClimbRobustEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.scene.terrain.max_init_terrain_level = None
        self.scene.terrain.terrain_generator.curriculum = False
        self.scene.terrain.terrain_generator.num_rows = 1
        self.scene.terrain.terrain_generator.num_cols = 4
        self.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (0.20, 0.20)
        self.curriculum.terrain_levels = None


@configclass
class Go2PiperBoxClimbContactRobustEnvCfg(Go2PiperBoxClimbEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.events.reset_base.params["velocity_range"] = {
            "x": (-0.05, 0.05),
            "y": (-0.05, 0.05),
            "z": (-0.03, 0.03),
            "roll": (-0.10, 0.10),
            "pitch": (-0.10, 0.10),
            "yaw": (-0.10, 0.10),
        }
        self.events.reset_robot_joints.params["velocity_range"] = (-0.15, 0.15)


@configclass
class Go2PiperBoxClimbContactRobustEnvCfg_PLAY(Go2PiperBoxClimbContactRobustEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 16
        self.observations.policy.enable_corruption = False
        self.events.reset_base.params["velocity_range"] = {
            axis: (0.0, 0.0) for axis in ("x", "y", "z", "roll", "pitch", "yaw")
        }
        self.events.reset_robot_joints.params["velocity_range"] = (0.0, 0.0)
        self.scene.terrain.max_init_terrain_level = None
        self.scene.terrain.terrain_generator.curriculum = False
        self.scene.terrain.terrain_generator.num_rows = 1
        self.scene.terrain.terrain_generator.num_cols = 4
        self.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (0.20, 0.20)
        self.curriculum.terrain_levels = None
