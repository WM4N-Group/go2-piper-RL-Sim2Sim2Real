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
from ..go2_arx5.box_push_env_cfg import Go2ARX5BoxPushHybridEnvCfg
from ...mdp import box_push


PIPER_ARM_EFFORT_LIMITS = (20.0, 20.0, 15.0, 7.0, 5.0, 5.0)
PIPER_SAFE_APPROACH_PATH = Path(__file__).resolve().parents[8] / "mujoco/deploy/piper_push_safe_approach.json"


def piper_safe_approach_config():
    payload = json.loads(PIPER_SAFE_APPROACH_PATH.read_text())
    if payload["schema_version"] != 1 or payload["robot"] != "go2_piper":
        raise ValueError("Expected a GO2-PIPER safe approach path")
    return payload




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




















