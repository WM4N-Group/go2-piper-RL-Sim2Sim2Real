"""Deterministic physical evaluation of the separate box-skill actors."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import traceback

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser()
parser.add_argument("--task", required=True, choices=("GO2-ARX5-Box-Climb-Play", "GO2-ARX5-Box-Push-Play", "GO2-ARX5-Box-Push-Hybrid-Play", "GO2-PIPER-Box-Climb-Play", "GO2-PIPER-Box-Climb-Smooth-Play", "GO2-PIPER-Box-Climb-Robust-Play", "GO2-PIPER-Box-Climb-Contact-Robust-Play", "GO2-PIPER-Box-Push-Hybrid-Play", "GO2-PIPER-Box-Push-Tracking-Play", "GO2-PIPER-Box-Push-Low-Play"))
source_group = parser.add_mutually_exclusive_group(required=True)
source_group.add_argument("--checkpoint", type=Path)
source_group.add_argument("--actor-policy", type=Path, help="Diagnostic: directly evaluate a provenance-recorded TorchScript skill actor.")
source_group.add_argument("--locomotion-policy", type=Path, help="Use the frozen 210-input NAV actor for legs; requires --arm-ik.")
parser.add_argument("--output-json", type=Path, required=True)
parser.add_argument("--num_envs", type=int, default=32)
parser.add_argument("--inspect-env-index", type=int, default=0, help="Environment whose trace and optional video are recorded; batch evaluation remains unchanged.")
parser.add_argument("--failure-history-steps", type=int, default=0, help="PIPER Tracking: keep this many pre-step states per failed episode; zero disables (maximum 256).")
parser.add_argument("--steps", type=int, default=1200)
parser.add_argument("--episodes-per-env", type=int, default=1)
parser.add_argument("--episode-length-s", type=float)
parser.add_argument("--preparation-seconds", type=float, default=0.0)
parser.add_argument("--seed", type=int, default=100)
parser.add_argument("--box-height", type=float)
parser.add_argument("--approach-height", type=float, default=0.0)
parser.add_argument("--approach-gap", type=float, default=0.0)
parser.add_argument("--landing-length", type=float)
parser.add_argument("--landing-width", type=float)
parser.add_argument("--start-clearance", type=float)
parser.add_argument("--base-start-x", type=float)
parser.add_argument("--prepared-starts", type=Path)
parser.add_argument("--prepared-phase", choices=("ground", "platform"), default="ground")
parser.add_argument("--following-platform-height", type=float, default=0.0)
parser.add_argument("--surface-friction", type=float)
parser.add_argument("--box-mass", type=float)
parser.add_argument("--box-friction", type=float)
parser.add_argument("--box-length", type=float, help="World-model scene probe: visible PUSH box length in metres.")
parser.add_argument("--box-width", type=float, help="World-model scene probe: visible PUSH box width in metres.")
parser.add_argument("--press-depth", type=float)
parser.add_argument("--push-distance", type=float)
parser.add_argument("--push-height-offset", type=float)
parser.add_argument("--push-approach-height-gate", action="store_true")
parser.add_argument("--push-geometry-root", type=Path)
parser.add_argument("--push-geometry-minimum", type=float)
parser.add_argument("--push-joint4-floor", type=float)
parser.add_argument("--push-hand-pitch", type=float, default=0.8)
parser.add_argument("--push-ik-clearance-minimum", type=float, help="Diagnostic: project unlocked Tracking IK targets onto local body-center clearance constraints.")
parser.add_argument("--push-ik-orientation-weight", type=float, default=1.0, help="Tracking diagnostic: rotation residual scale in pose IK; 1 preserves the original solver.")
parser.add_argument("--push-ik-height-weight", type=float, default=1.0, help="Tracking diagnostic: world height residual weight for bounded IK; no safety threshold changes.")
parser.add_argument("--push-ik-joint-limit-solve", action="store_true", help="Tracking diagnostic: improve the pose solve within the original joint limits.")
parser.add_argument("--push-goal-hold-pose", action="store_true", help="Tracking diagnostic: hold the measured world hand pose on goal entry instead of withdrawing.")
parser.add_argument("--push-goal-brake-gain", type=float, default=0.0, help="Tracking diagnostic: bounded reverse command to brake residual forward base velocity at goal.")
parser.add_argument("--push-goal-release-distance", type=float, default=0.0, help="Tracking diagnostic: small outward hand target offset on goal entry to unload contact.")
parser.add_argument("--push-press-on-legal-contact", action="store_true", help="Tracking diagnostic: sustain pressing on current legal contact even if geometric approach readiness clears.")
parser.add_argument("--push-stop-distance", type=float, default=0.10, help="Tracking diagnostic: controller braking threshold; success criteria stay unchanged.")
parser.add_argument("--push-leg-release-on-contact", action="store_true", help="Tracking diagnostic: start leg action ramp only after real legal hand contact.")
parser.add_argument("--push-contact-memory-s", type=float, default=0.0, help="Tracking diagnostic: retain verified near-face contact briefly for the drive command.")
parser.add_argument("--push-leg-release-ramp-s", type=float, default=0.0, help="Tracking diagnostic: blend in leg actions after arm approach readiness.")
parser.add_argument("--push-leg-contact-ramp-s", type=float, default=0.0, help="Tracking diagnostic: increase leg blending rate during verified legal contact; zero disables.")
parser.add_argument("--push-forward-command-gain", type=float, default=1.0, help="Tracking diagnostic: increase positive base velocity commands while preserving separation and goal stops.")
parser.add_argument("--push-contact-gap-slowdown-start", type=float, default=0.0, help="Tracking diagnostic: cap forward speed below this base-to-face gap during current legal contact; zero disables.")
parser.add_argument("--push-target-maximum-reach", type=float, default=0.0, help="Tracking diagnostic: cap hand target reach in the base yaw frame; zero disables.")
parser.add_argument("--push-body-first", action="store_true", help="Tracking diagnostic: finish SAFE_APPROACH, position the base, then lower the arm to the push face.")
parser.add_argument("--push-velocity-feedback-gain", type=float, default=0.0, help="Tracking diagnostic: add bounded body velocity error feedback to the locomotion command.")
parser.add_argument("--push-velocity-integral-gain", type=float, default=0.0, help="Tracking diagnostic: bounded integral correction for persistent locomotion tracking bias.")
parser.add_argument("--arm-ik", action="store_true", help="Diagnostic: replace the learned arm output with rate-limited differential IK.")
parser.add_argument("--neutral-arm", action="store_true", help="Diagnostic: hold the nominal arm pose for CLIMB.")
parser.add_argument("--neutral-push-command", action="store_true", help="Diagnostic: keep the NAV actor end-effector command at its neutral reference during PUSH.")
parser.add_argument("--observation-noise", action="store_true", help="Diagnostic: retain training observation noise during evaluation.")
parser.add_argument("--video-path", type=Path)
parser.add_argument("--collision-usd", type=Path)
parser.add_argument("--staged-precontact", action="store_true")
parser.add_argument("--contact-servo", action="store_true")
parser.add_argument("--contact-action-ramp-time", type=float)
parser.add_argument("--neutral-legs", action="store_true")
parser.add_argument("--deployment-actor", type=Path, help="Compare exported TorchScript outputs on every evaluated observation.")
parser.add_argument("--world-model-shadow", type=Path, help="Read-only frozen PUSH consequence model; never changes actions.")
parser.add_argument("--world-model-sha256", help="Required SHA-256 of the frozen shadow model.")
parser.add_argument("--response-gate", type=Path, help="Read-only delayed PUSH response gate.")
parser.add_argument("--delayed-margin-shadow", type=Path, help="Read-only frozen 1.2 s terminal-error model.")
parser.add_argument("--delayed-margin-sha256", help="Required SHA-256 of the delayed terminal-error model.")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.world_model_shadow is not None:
    if (args.task != "GO2-PIPER-Box-Push-Tracking-Play" or args.num_envs != 1
            or args.episodes_per_env != 1 or not args.world_model_shadow.is_file()
            or args.world_model_sha256 is None):
        parser.error("Piper PUSH shadow requires one episode, an existing model and its SHA-256")
elif args.world_model_sha256 is not None:
    parser.error("--world-model-sha256 requires --world-model-shadow")
if args.response_gate is not None and (args.world_model_shadow is None or not args.response_gate.is_file()):
    parser.error("--response-gate requires PUSH shadow and an existing gate file")
if args.delayed_margin_shadow is not None:
    if (args.task != "GO2-PIPER-Box-Push-Tracking-Play" or args.num_envs != 1
            or args.episodes_per_env != 1 or not args.delayed_margin_shadow.is_file()
            or args.delayed_margin_sha256 is None):
        parser.error("Delayed-margin shadow requires one PUSH episode, an existing model and its SHA-256")
elif args.delayed_margin_sha256 is not None:
    parser.error("--delayed-margin-sha256 requires --delayed-margin-shadow")
if args.arm_ik and "Push" not in args.task:
    parser.error("--arm-ik only applies to PUSH")
if args.neutral_arm and "Climb" not in args.task:
    parser.error("--neutral-arm only applies to CLIMB")
if args.neutral_push_command and "Push" not in args.task:
    parser.error("--neutral-push-command only applies to PUSH")
if args.arm_ik and ("Hybrid" in args.task or "Push-Tracking" in args.task or "Push-Low" in args.task):
    parser.error("The hybrid task already contains its arm controller")
if args.locomotion_policy is not None and not args.arm_ik:
    parser.error("--locomotion-policy requires --arm-ik")
if args.output_json.exists():
    parser.error("Output file already exists")
if args.collision_usd is not None and (not args.task.startswith("GO2-PIPER-") or not args.collision_usd.is_file()):
    parser.error("Collision diagnostics require a PIPER task and an existing USD")
if args.staged_precontact and (args.collision_usd is None or "Push-Hybrid" not in args.task):
    parser.error("Staged precontact requires the collision-enabled PIPER hybrid PUSH diagnostic")
if (args.contact_servo or args.contact_action_ramp_time is not None or args.neutral_legs) and not args.staged_precontact:
    parser.error("Contact servo, action ramp time and neutral legs require the staged precontact diagnostic")
if args.contact_action_ramp_time is not None and (not math.isfinite(args.contact_action_ramp_time) or args.contact_action_ramp_time <= 0.0):
    parser.error("Contact action ramp time must be finite and positive")
if args.video_path is not None:
    if args.video_path.exists():
        parser.error("Video file already exists")
    args.enable_cameras = True
if args.steps < 1 or args.num_envs < 1 or args.episodes_per_env < 1:
    parser.error("Evaluation size must be positive")
if not 0 <= args.inspect_env_index < args.num_envs:
    parser.error("Inspect environment index must be in [0, num_envs)")
if not math.isfinite(args.preparation_seconds) or args.preparation_seconds < 0.0:
    parser.error("Preparation duration must be finite and nonnegative")
if args.preparation_seconds and ("Climb" not in args.task or args.episodes_per_env != 1):
    parser.error("Explicit preparation currently supports one CLIMB episode per environment")
for value in (args.box_height, args.box_mass, args.box_friction, args.episode_length_s, args.landing_length, args.landing_width, args.start_clearance, args.surface_friction):
    if value is not None and (not math.isfinite(value) or value <= 0.0):
        parser.error("Physical parameters must be positive and finite")
if args.box_length is not None and (not math.isfinite(args.box_length) or not 1.0 <= args.box_length <= 1.3):
    parser.error("PUSH box length must be finite and in [1.0, 1.3] m")
if args.box_width is not None and (not math.isfinite(args.box_width) or not 0.8 <= args.box_width <= 1.3):
    parser.error("PUSH box width must be finite and in [0.8, 1.3] m")
if (args.box_length is not None or args.box_width is not None) and "Push" not in args.task:
    parser.error("Box length and width overrides apply only to PUSH")
for value in (args.approach_height, args.approach_gap, args.following_platform_height):
    if not math.isfinite(value) or value < 0.0:
        parser.error("Approach height and gap must be finite and nonnegative")
if args.base_start_x is not None and (not math.isfinite(args.base_start_x) or abs(args.base_start_x) > 0.30):
    parser.error("Base start x must be finite and within 0.30 m of the nominal origin")
for value in (args.press_depth, args.push_distance):
    if value is not None and (not math.isfinite(value) or value <= 0.0):
        parser.error("PUSH parameters must be positive and finite")
if args.push_height_offset is not None and (not math.isfinite(args.push_height_offset) or not -0.03 <= args.push_height_offset <= 0.03):
    parser.error("PUSH height offset must be between -0.03 and 0.03 m")
if not math.isfinite(args.push_hand_pitch) or not 0.0 <= args.push_hand_pitch <= 1.2:
    parser.error("PUSH hand pitch must be between 0 and 1.2 rad")
if args.push_height_offset is not None and "Push" not in args.task:
    parser.error("--push-height-offset only applies to PUSH")
if args.push_ik_clearance_minimum is not None:
    if args.task != "GO2-PIPER-Box-Push-Tracking-Play" or not 0.08 < args.push_ik_clearance_minimum <= 0.25:
        parser.error("IK clearance requires PIPER Tracking and a distance in (0.08, 0.25]")
if not 0.0 < args.push_ik_orientation_weight <= 1.0:
    parser.error("IK orientation weight must be in (0, 1]")
if args.push_ik_orientation_weight != 1.0 and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Weighted pose IK requires PIPER Tracking")
if not 1.0 <= args.push_ik_height_weight <= 3.0:
    parser.error("IK height weight must be in [1, 3]")
if args.push_ik_height_weight != 1.0 and not args.push_ik_joint_limit_solve:
    parser.error("IK height weighting requires bounded pose IK")
if args.push_ik_joint_limit_solve and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Bounded pose IK requires PIPER Tracking")
if args.push_press_on_legal_contact and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Contact-sustained pressing requires PIPER Tracking")
if not 0.0 <= args.push_goal_brake_gain <= 2.0 or (args.push_goal_brake_gain and args.task != "GO2-PIPER-Box-Push-Tracking-Play"):
    parser.error("Goal braking requires PIPER Tracking and gain in [0, 2]")
if not 0.0 <= args.push_goal_release_distance <= 0.02 or (args.push_goal_release_distance and not args.push_goal_hold_pose):
    parser.error("Goal contact release requires goal pose hold and distance in [0, .02]")
if args.push_goal_hold_pose and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Goal pose hold requires PIPER Tracking")
if args.push_geometry_root is None or not args.push_geometry_root.is_dir() or not 0.015 <= args.push_geometry_minimum <= 0.05:
    parser.error("Geometry shield requires a model directory and 15-50mm clearance")
if args.push_joint4_floor is not None and not 0.5 <= args.push_joint4_floor <= 1.5:
    parser.error("Joint4 floor must be in [0.5, 1.5] radians")
if not 0.05 <= args.push_stop_distance <= 0.11:
    parser.error("PUSH control stop distance must be in [0.05, 0.11] metres")
if args.push_stop_distance != 0.10 and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Control stop distance diagnostic requires PIPER Tracking")
if args.push_leg_release_on_contact and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Contact-triggered leg release requires PIPER Tracking")
if not math.isfinite(args.push_contact_memory_s) or not 0.0 <= args.push_contact_memory_s <= 0.2:
    parser.error("Contact memory must be finite and in [0, 0.2] seconds")
if args.push_contact_memory_s and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Contact memory diagnostic requires PIPER Tracking")
if not math.isfinite(args.push_leg_release_ramp_s) or not 0.0 <= args.push_leg_release_ramp_s <= 2.0:
    parser.error("Leg release ramp must be finite and in [0, 2] seconds")
if args.push_leg_release_ramp_s and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Leg release ramp diagnostic requires PIPER Tracking")
if not 0.0 <= args.push_leg_contact_ramp_s <= args.push_leg_release_ramp_s:
    parser.error("Contact leg ramp must be in [0, ordinary leg ramp]")
if args.push_leg_contact_ramp_s and (args.task != "GO2-PIPER-Box-Push-Tracking-Play" or args.push_leg_release_on_contact):
    parser.error("Contact-accelerated blending requires ordinary Tracking leg release")
if not 1.0 <= args.push_forward_command_gain <= 2.0:
    parser.error("PUSH forward command gain must be in [1, 2]")
if args.push_forward_command_gain != 1.0 and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Forward command gain diagnostic requires PIPER Tracking")
if args.push_contact_gap_slowdown_start and (
    args.task != "GO2-PIPER-Box-Push-Tracking-Play"
    or not 0.43 < args.push_contact_gap_slowdown_start <= 0.65
    or args.push_body_first or args.staged_precontact
):
    parser.error("Contact gap slowdown requires ordinary PIPER Tracking and a start in (0.43, 0.65]")
if args.push_target_maximum_reach != 0.0 and (
    args.task != "GO2-PIPER-Box-Push-Tracking-Play" or not 0.43 <= args.push_target_maximum_reach <= 0.65
):
    parser.error("Target reach requires PIPER Tracking and a distance in [0.43, 0.65]")
if args.push_body_first and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Body-first approach diagnostic requires PIPER Tracking")
if not 0.0 <= args.push_velocity_feedback_gain <= 3.0:
    parser.error("PUSH velocity feedback gain must be in [0, 3]")
if args.push_velocity_feedback_gain and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Velocity feedback diagnostic requires PIPER Tracking")
if not 0.0 <= args.push_velocity_integral_gain <= 3.0:
    parser.error("PUSH velocity integral gain must be in [0, 3]")
if args.push_velocity_integral_gain and not args.push_velocity_feedback_gain:
    parser.error("Integral feedback requires proportional velocity feedback")
if not 0 <= args.failure_history_steps <= 256:
    parser.error("Failure history must contain 0 to 256 pre-step samples")
if args.failure_history_steps and (
    args.task != "GO2-PIPER-Box-Push-Tracking-Play"
    or args.num_envs * args.failure_history_steps > 65536
):
    parser.error("Failure history requires PIPER Tracking and at most 65536 environment-step slots")
launcher = AppLauncher(args)

import gymnasium as gym
import torch

import isaaclab_tasks
from isaaclab.managers import SceneEntityCfg
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import LeggedManip_Lab.tasks
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_climb, box_push
from box_evaluation_metrics import EpisodeHistory, EpisodeQuota, JointMotionTelemetry
from create_piper_collision_variant import configure_collision_candidate
from push_shadow_observer import PushShadowObserver
from push_delayed_margin_observer import PushDelayedMarginObserver


def main():
    config = load_cfg_from_registry(args.task, "env_cfg_entry_point")
    config.scene.num_envs = args.num_envs
    trace_index = args.inspect_env_index
    if args.video_path is not None:
        config.viewer.origin_type = "env"
        config.viewer.env_index = trace_index
        if "Push" in args.task:
            config.viewer.eye = (2.8, 2.4, 1.7)
            config.viewer.lookat = (0.8, 0.0, 0.25)
    config.seed = args.seed
    config.sim.device = args.device
    config.observations.policy.enable_corruption = args.observation_noise
    if args.push_ik_clearance_minimum is not None:
        config.push_ik_clearance_minimum = args.push_ik_clearance_minimum
    if args.push_ik_orientation_weight != 1.0:
        config.push_ik_orientation_weight = args.push_ik_orientation_weight
    config.push_ik_height_weight = args.push_ik_height_weight
    if args.push_ik_joint_limit_solve:
        config.push_ik_joint_limit_solve = True
    if args.push_goal_hold_pose:
        config.push_goal_hold_pose = True
    config.push_goal_brake_gain = args.push_goal_brake_gain
    config.push_goal_release_distance = args.push_goal_release_distance
    config.push_approach_height_gate = args.push_approach_height_gate
    config.push_geometry_root = args.push_geometry_root
    config.push_geometry_minimum = args.push_geometry_minimum
    config.push_joint4_floor = args.push_joint4_floor
    if args.push_press_on_legal_contact:
        config.push_press_on_legal_contact = True
    if args.push_stop_distance != 0.10:
        config.push_stop_distance = args.push_stop_distance
    if args.push_leg_release_on_contact:
        config.push_leg_release_on_contact = True
    if args.push_contact_memory_s:
        config.push_contact_memory_s = args.push_contact_memory_s
    if args.push_leg_release_ramp_s:
        config.push_leg_release_ramp_s = args.push_leg_release_ramp_s
    config.push_leg_contact_ramp_s = args.push_leg_contact_ramp_s
    config.push_contact_gap_slowdown_start = args.push_contact_gap_slowdown_start
    if args.push_forward_command_gain != 1.0:
        config.push_forward_command_gain = args.push_forward_command_gain
    if args.push_target_maximum_reach:
        config.push_target_maximum_reach = args.push_target_maximum_reach
    if args.push_body_first:
        config.push_body_first = True
    if args.push_velocity_feedback_gain:
        config.push_velocity_feedback_gain = args.push_velocity_feedback_gain
    if args.push_velocity_integral_gain:
        config.push_velocity_integral_gain = args.push_velocity_integral_gain
    if args.episode_length_s is not None:
        config.episode_length_s = args.episode_length_s
    climbing = "Climb" in args.task
    hybrid_push = not climbing and any(
        name in args.task for name in ("Push-Hybrid", "Push-Tracking", "Push-Low")
    )
    if args.prepared_starts is not None:
        if not climbing:
            raise ValueError("Prepared starts require the CLIMB task")
        config.prepared_start_path = str(args.prepared_starts)
        config.prepared_start_phase = args.prepared_phase
    if args.start_clearance is not None:
        config.scene.robot.init_state.pos = (*config.scene.robot.init_state.pos[:2], args.start_clearance)
    if args.base_start_x is not None:
        config.scene.robot.init_state.pos = (args.base_start_x, *config.scene.robot.init_state.pos[1:])
    if climbing:
        terrain = config.scene.terrain.terrain_generator.sub_terrains["box"]
        terrain.approach_height = args.approach_height
        terrain.approach_gap = args.approach_gap
        terrain.following_platform_height = args.following_platform_height
        if args.surface_friction is not None:
            config.scene.terrain.physics_material.static_friction = args.surface_friction
            config.scene.terrain.physics_material.dynamic_friction = args.surface_friction
            config.sim.physics_material = config.scene.terrain.physics_material
        if args.landing_length is not None:
            terrain.box_length = args.landing_length
        if args.landing_width is not None:
            terrain.box_width = args.landing_width
    if args.box_height is not None:
        if climbing:
            config.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (args.box_height, args.box_height)
        else:
            config.box_size = (*config.box_size[:2], args.box_height)
            config.scene.box.spawn.size = config.box_size
            config.scene.box.init_state.pos = (*config.scene.box.init_state.pos[:2], args.box_height / 2.0)
    if not climbing and (args.box_length is not None or args.box_width is not None):
        config.box_size = (
            args.box_length if args.box_length is not None else config.box_size[0],
            args.box_width if args.box_width is not None else config.box_size[1],
            config.box_size[2],
        )
        config.scene.box.spawn.size = config.box_size
    if not climbing:
        if args.push_height_offset is not None:
            config.push_hand_height_offset = args.push_height_offset
            if hasattr(config, "push_contact_height_offset"):
                config.push_contact_height_offset = args.push_height_offset
        config.actions.joint_pos.hand_pitch = args.push_hand_pitch
        if args.press_depth is not None:
            config.push_press_depth = args.press_depth
        if args.push_distance is not None:
            config.push_distance = args.push_distance
        if args.box_mass is not None:
            config.scene.box.spawn.mass_props.mass = args.box_mass
        if args.box_friction is not None:
            config.scene.box.spawn.physics_material.static_friction = args.box_friction
            config.scene.box.spawn.physics_material.dynamic_friction = args.box_friction
    collision_variant = configure_collision_candidate(
        config, args.collision_usd, args.staged_precontact, args.contact_servo, args.contact_action_ramp_time,
    ) if args.collision_usd else None
    agent_config = load_cfg_from_registry(args.task, "rsl_rl_cfg_entry_point")
    agent_config.device = args.device
    agent_config.seed = args.seed
    if agent_config.actor.activation != "elu":
        raise ValueError("Evaluation requires the project's ELU actor")
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "rsl_rl"))
    from safe_retraining import configure
    configure(config, args, training=False)
    assert args.box_mass == 3.0 and args.box_friction == 0.3
    config.scene.box.spawn.mass_props.mass = args.box_mass
    config.scene.box.spawn.physics_material.static_friction = args.box_friction
    config.scene.box.spawn.physics_material.dynamic_friction = args.box_friction
    env = RslRlVecEnvWrapper(gym.make(args.task, cfg=config, render_mode="rgb_array" if args.video_path else None), clip_actions=agent_config.clip_actions)
    base = env.unwrapped
    box_view = base.scene['box'].root_physx_view
    startup_masses = box_view.get_masses().flatten().tolist()
    startup_materials = box_view.get_material_properties().tolist()
    startup_ok = all(abs(v - 3.) < 1e-6 for v in startup_masses) and all(abs(m[0] - .3) < 1e-6 and abs(m[1] - .3) < 1e-6 and m[2] == 0. for row in startup_materials for m in row)
    import json as startup_json
    (args.output_json.parent / 'startup-physics.json').write_text(startup_json.dumps(dict(valid=startup_ok, box_mass_per_env=startup_masses, box_material_per_env=startup_materials), indent=2))
    assert startup_ok, 'Requested box physics not applied; abort before rollout'
    video = None
    if args.video_path is not None:
        import imageio.v2 as imageio

        args.video_path.parent.mkdir(parents=True, exist_ok=True)
        video = imageio.get_writer(str(args.video_path), fps=round(1.0 / (2 * base.step_dt)), codec="libx264")
        origin = base.scene.env_origins[0].cpu().numpy()
        camera_eye = [3.0, 3.0, 1.8] if climbing else [0.7, 3.2, 1.5]
        base.sim.set_camera_view(eye=origin + camera_eye, target=origin + [0.9, 0.0, 0.3])
    if args.locomotion_policy is not None:
        policy = torch.jit.load(str(args.locomotion_policy), map_location=args.device).eval()
        observation_groups = ["policy"]
    elif args.actor_policy is not None:
        policy = torch.jit.load(str(args.actor_policy), map_location=args.device).eval()
        observation_groups = agent_config.obs_groups["actor"]
    else:
        checkpoint = torch.load(args.checkpoint, map_location=args.device, weights_only=False)
        load_actor = runpy.run_path(str(Path(__file__).resolve().parent / "rsl_rl/initialization.py"))["actor_from_state_dict"]
        policy = load_actor(checkpoint["actor_state_dict"], device=args.device)
        observation_groups = agent_config.obs_groups["actor"]
    if args.neutral_legs:
        frozen_policy = policy

        def policy(observation):
            return torch.zeros_like(frozen_policy(observation))
    observation = env.get_observations()
    deployment_actor = torch.jit.load(str(args.deployment_actor), map_location=args.device).eval() if args.deployment_actor else None
    deployment_max_error = 0.0
    deployment_comparisons = 0
    robot = base.scene["robot"]
    arm_controller = None
    if args.arm_ik:
        from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_push_ik import PushArmIK

        arm_controller = PushArmIK(base, hold_legs_until_ready=args.locomotion_policy is not None, lock_arm_on_contact=args.locomotion_policy is not None)
    feet = SceneEntityCfg("robot", body_names=".*_foot")
    feet.resolve(base.scene)
    sensor = SceneEntityCfg("contact_forces", body_names=".*_foot")
    sensor.resolve(base.scene)
    hand = SceneEntityCfg("robot", body_names="end_effector")
    hand.resolve(base.scene)
    arm = SceneEntityCfg("robot", joint_names="joint.*")
    arm.resolve(base.scene)
    quota = EpisodeQuota(args.num_envs, args.episodes_per_env, args.device)
    completions, successes = quota.completed, quota.successful
    motion = JointMotionTelemetry(robot.data.joint_pos, base.step_dt)
    from bounded_gradient_v175 import install as install_bounded_gradient
    install_bounded_gradient(base.action_manager.get_term("joint_pos").controller.geometry_shield)
    from stage_hold_v192 import StageHold
    stage_hold = StageHold(base, quota)
    terminal_states = []
    failure_history = EpisodeHistory(args.num_envs, args.failure_history_steps, args.device) if args.failure_history_steps else None
    failure_histories = []
    original_pre_reset = base.recorder_manager.record_pre_reset

    def sample_motion(active):
        motion.sample(
            active, robot.data.joint_pos_target, robot.data.joint_vel, robot.data.joint_acc,
            robot.data.applied_torque, robot.data.joint_effort_limits, robot.data.root_ang_vel_w,
        )

    def record_pre_reset(env_ids, *arguments, **keywords):
        selected = env_ids[quota.active[env_ids]]
        terminal_mask = torch.zeros(args.num_envs, dtype=torch.bool, device=args.device)
        terminal_mask[selected] = True
        sample_motion(terminal_mask)
        fields = {
            "elapsed_seconds": base.episode_length_buf * base.step_dt,
            "robot_position": robot.data.root_pos_w - base.scene.env_origins,
            "robot_quaternion": robot.data.root_quat_w,
            "robot_velocity": robot.data.root_lin_vel_w,
            "robot_gravity": robot.data.projected_gravity_b,
            "robot_joint_position": robot.data.joint_pos,
            "robot_joint_velocity": robot.data.joint_vel,
            "robot_joint_acceleration": robot.data.joint_acc,
            "robot_joint_position_target": robot.data.joint_pos_target,
            "robot_applied_torque": robot.data.applied_torque,
            "robot_angular_velocity": robot.data.root_ang_vel_w,
            "robot_body_position": robot.data.body_pos_w - base.scene.env_origins[:, None, :],
            "body_contact_forces": base.scene["contact_forces"].data.net_forces_w,
            "body_contact_force_history": base.scene["contact_forces"].data.net_forces_w_history,
            "termination_flags": torch.stack([
                base.termination_manager.get_term(name) for name in base.termination_manager.active_terms
            ], dim=1),
        }
        if hybrid_push:
            controller = base.action_manager.get_term("joint_pos").controller
            fields.update(
                safe_approach_complete=controller.safe_approach_complete,
                approach_pitch_reference=controller.approach_pitch_reference,
                approach_height_aligned=controller.approach_height_aligned,
                approach_gate_advance=controller.approach_gate_advance,
                approach_face_ready=controller.approach_face_ready,
                approach_face_duration=controller.approach_face_duration,
                safe_approach_index=controller.safe_approach_index,
                precontact_stage=controller.precontact_stage,
                precontact_ready=controller.precontact_ready,
                body_ready=controller.body_ready,
                arm_command_position=controller.target_position - base.scene.env_origins,
                ik_clearance_residual=controller.clearance_residual,
                ik_clearance_correction=controller.clearance_correction,
                ik_clearance_distance=controller.clearance_distance,
                goal_hold_active=controller.goal_hold_active,
                geometry_clearance=controller.geometry_clearance,
                debug_gate_velocity_ready=controller.debug_gate_velocity_ready,
                debug_gate_geometric_ready=controller.debug_gate_geometric_ready,
                debug_predicted_clearance=controller.debug_predicted_clearance,
                debug_arm_velocity=controller.debug_arm_velocity,
                debug_reference_post_geometry=controller.debug_reference_post_geometry,
                debug_reference_pre_geometry=controller.debug_reference_pre_geometry,
                debug_pose_desired=controller.debug_pose_desired,
                debug_pose_rotation_error=controller.debug_pose_rotation_error,
                debug_pose_position_error=controller.debug_pose_position_error,
                geometry_blocked=controller.geometry_blocked,
                geometry_minimum_observed=controller.geometry_minimum_observed,
                geometry_observed_steps=controller.geometry_observed_steps,
                geometry_below_minimum_steps=controller.geometry_below_minimum_steps,
                leg_contact_ready=controller.leg_contact_ready,
            )
        if not climbing:
            box = base.scene["box"]
            settle_term = base.termination_manager.get_term_cfg("box_settled").func
            if hasattr(settle_term, "duration"):
                fields["settle_duration"] = settle_term.duration
            target = box_push.push_target(base)
            displacement = box.data.root_pos_w - target
            displacement = displacement.clone()
            displacement[:, 0] += config.push_distance
            terminal_hand_force = base.scene["box_contact_hand"].data.force_matrix_w.sum(dim=(1, 2))
            terminal_contact = base.scene["box_contact_hand"].data.contact_pos_w[:, 0, 0]
            terminal_valid = box_push.hand_contact(base, hand)
            terminal_strength = torch.linalg.vector_norm(terminal_hand_force, dim=1)
            unclassified = (terminal_strength > 1.0) & ~terminal_valid
            unclassified_hand_contact_steps[selected] += unclassified[selected].float()
            maximum_unclassified_hand_force[selected] = torch.maximum(
                maximum_unclassified_hand_force[selected], terminal_strength[selected] * unclassified[selected],
            )
            fields.update(
                box_position=box.data.root_pos_w - base.scene.env_origins,
                box_quaternion=box.data.root_quat_w,
                box_goal=target - base.scene.env_origins,
                box_displacement=displacement,
                box_goal_error=torch.linalg.vector_norm(target[:, :2] - box.data.root_pos_w[:, :2], dim=1),
                box_speed=torch.linalg.vector_norm(box.data.root_lin_vel_w, dim=1),
                box_angular_speed=torch.linalg.vector_norm(box.data.root_ang_vel_w, dim=1),
                hand_force=terminal_hand_force,
                hand_position=robot.data.body_pos_w[:, hand.body_ids[0]] - base.scene.env_origins,
                hand_quaternion=robot.data.body_quat_w[:, hand.body_ids[0]],
                hand_contact_position=torch.nan_to_num(terminal_contact - base.scene.env_origins),
                hand_contact_position_valid=torch.isfinite(terminal_contact).all(dim=1),
                hand_contact_valid=terminal_valid,
            )
        snapshots = quota.terminal_snapshot(env_ids, **fields)
        if failure_history is not None:
            failure_histories.extend(failure_history.finish(
                snapshots, list(base.termination_manager.active_terms), len(terminal_states),
            ))
        terminal_states.extend(snapshots)
        return original_pre_reset(env_ids, *arguments, **keywords)

    base.recorder_manager.record_pre_reset = record_pre_reset
    maximum_forward = torch.full((args.num_envs,), -torch.inf, device=args.device)
    minimum_base_height = torch.full((args.num_envs,), torch.inf, device=args.device)
    maximum_tilt = torch.zeros(args.num_envs, device=args.device)
    maximum_condition = torch.zeros(args.num_envs, device=args.device)
    condition_duration = torch.zeros_like(maximum_condition)
    maximum_support = torch.zeros_like(maximum_condition)
    maximum_joint_velocity = torch.zeros(robot.num_joints, device=args.device)
    maximum_torque_ratio = 0.0
    push_force_sum = torch.zeros(args.num_envs, device=args.device)
    push_contact_steps = torch.zeros_like(push_force_sum)
    maximum_push_force = torch.zeros_like(push_force_sum)
    unclassified_hand_contact_steps = torch.zeros_like(push_force_sum)
    maximum_unclassified_hand_force = torch.zeros_like(push_force_sum)
    reasons = {name: 0 for name in base.termination_manager.active_terms}
    trace = []
    shadow = PushShadowObserver(args.world_model_shadow, config.box_size, config.push_distance, base.step_dt,
                                args.response_gate) if args.world_model_shadow else None
    if shadow is not None and shadow.model_sha256 != args.world_model_sha256:
        raise ValueError("Frozen world-model hash differs from the requested shadow model")
    delayed_shadow = PushDelayedMarginObserver(
        args.delayed_margin_shadow, config.box_size, config.push_distance, base.step_dt,
        args.delayed_margin_sha256,
    ) if args.delayed_margin_shadow else None
    with torch.inference_mode():
        for step in range(args.steps):
            active = quota.active.clone()
            sample = None
            relative = robot.data.root_pos_w - base.scene.env_origins
            maximum_forward[active] = torch.maximum(maximum_forward[active], relative[active, 0])
            minimum_base_height[active] = torch.minimum(minimum_base_height[active], relative[active, 2])
            tilt = torch.acos((-robot.data.projected_gravity_b[:, 2]).clamp(-1.0, 1.0))
            maximum_tilt[active] = torch.maximum(maximum_tilt[active], tilt[active])
            if climbing:
                condition = box_climb.box_standing(base, feet, sensor)
                support = box_climb.supported_feet(base, feet, sensor).sum(dim=1).float()
                maximum_support[active] = torch.maximum(maximum_support[active], support[active])
            else:
                condition = box_push.hand_contact(base, hand)
                hand_force = base.scene["box_contact_hand"].data.force_matrix_w.sum(dim=(1, 2))
                normal_force = torch.linalg.vector_norm(hand_force, dim=1)
                push_force_sum += normal_force * (condition & active)
                push_contact_steps += (condition & active).float()
                maximum_push_force[active] = torch.maximum(maximum_push_force[active], normal_force[active])
                unclassified = (normal_force > 1.0) & ~condition & active
                unclassified_hand_contact_steps += unclassified.float()
                maximum_unclassified_hand_force = torch.maximum(maximum_unclassified_hand_force, normal_force * unclassified)
            condition_duration = torch.where(condition & active, condition_duration + base.step_dt, 0.0)
            maximum_condition = torch.maximum(maximum_condition, condition_duration)
            maximum_joint_velocity = torch.maximum(maximum_joint_velocity, robot.data.joint_vel[active].abs().max(dim=0).values)
            ratio = robot.data.applied_torque[active].abs() / robot.data.joint_effort_limits[active].clamp_min(1e-6)
            maximum_torque_ratio = max(maximum_torque_ratio, ratio.max().item())
            if active[trace_index]:
                sample = {
                    "step": step, "env_id": trace_index, "robot_position": relative[trace_index].tolist(),
                    "robot_gravity": robot.data.projected_gravity_b[trace_index].tolist(),
                    "robot_velocity": robot.data.root_lin_vel_w[trace_index].tolist(),
                    "robot_angular_velocity": robot.data.root_ang_vel_w[trace_index].tolist(),
                    "feet_height": (robot.data.body_pos_w[trace_index, feet.body_ids, 2] - base.scene.env_origins[trace_index, 2]).tolist(),
                }
                if climbing:
                    sample.update(
                        joint_position=robot.data.joint_pos[trace_index].tolist(),
                        joint_position_target=robot.data.joint_pos_target[trace_index].tolist(),
                        joint_velocity=robot.data.joint_vel[trace_index].tolist(),
                        joint_acceleration=robot.data.joint_acc[trace_index].tolist(),
                        applied_torque=robot.data.applied_torque[trace_index].tolist(),
                        foot_contact_force_z=base.scene["contact_forces"].data.net_forces_w[trace_index, sensor.body_ids, 2].tolist(),
                    )
                if not climbing:
                    action_term = base.action_manager.get_term("joint_pos") if hybrid_push else None
                    controller = action_term.controller if action_term is not None else None
                    target = controller.target_position[trace_index] if controller is not None else box_push.push_hand_target(base)[trace_index]
                    sample.update(
                        box_position=(base.scene["box"].data.root_pos_w[trace_index] - base.scene.env_origins[trace_index]).tolist(),
                        box_quaternion=base.scene["box"].data.root_quat_w[trace_index].tolist(),
                        hand_position=(robot.data.body_pos_w[trace_index, hand.body_ids[0]] - base.scene.env_origins[trace_index]).tolist(),
                        hand_contact=bool(condition[trace_index]),
                        approach_completed=bool(base.box_push_approached[trace_index]),
                        hand_force_world=hand_force[trace_index].tolist(),
                        hand_contact_position=torch.nan_to_num(
                            base.scene["box_contact_hand"].data.contact_pos_w[trace_index, 0, 0] - base.scene.env_origins[trace_index]
                        ).tolist(),
                        hand_contact_position_valid=bool(torch.isfinite(base.scene["box_contact_hand"].data.contact_pos_w[trace_index, 0, 0]).all()),
                        foot_contact_force_z=base.scene["contact_forces"].data.net_forces_w[trace_index, sensor.body_ids, 2].tolist(),
                        hand_target_error=(target - robot.data.body_pos_w[trace_index, hand.body_ids[0]]).tolist(),
                        velocity_command=box_push.push_velocity_commands(base, hand)[trace_index].tolist(),
                        arm_torque_limit_ratio=(robot.data.applied_torque[trace_index, arm.joint_ids].abs() / robot.data.joint_effort_limits[trace_index, arm.joint_ids]).tolist(),
                    )
                    if hybrid_push:
                        face, base_height, body_stable = box_push.preapproach_state(base)
                        sample.update(
                            arm_locked=bool(controller.locked[trace_index]),
                            drive_contact=bool(controller.drive_contact[trace_index]),
                            contact_memory_left=controller.contact_memory_left[trace_index].item(),
                            leg_release_elapsed=controller.leg_release_elapsed[trace_index].item(),
                            leg_release_blend=controller.leg_release_blend[trace_index].item(),
                            velocity_integral=controller.velocity_integral[trace_index].tolist(),
                            ik_clearance_residual=controller.clearance_residual[trace_index].item(),
                            ik_clearance_correction=controller.clearance_correction[trace_index].item(),
                            ik_clearance_distance=controller.clearance_distance[trace_index].item(),
                            geometry_clearance=controller.geometry_clearance[trace_index].item(),
                            geometry_blocked=bool(controller.geometry_blocked[trace_index]),
                            arm_joint_position=robot.data.joint_pos[trace_index, controller.joint_ids].tolist(),
                            robot_quaternion=robot.data.root_quat_w[trace_index].tolist(),
                            hand_quaternion=robot.data.body_quat_w[trace_index, hand.body_ids[0]].tolist(),
                            full_joint_position=robot.data.joint_pos[trace_index].tolist(),
                            full_joint_velocity=robot.data.joint_vel[trace_index].tolist(),
                            full_joint_position_target=robot.data.joint_pos_target[trace_index].tolist(),
                            full_applied_torque=robot.data.applied_torque[trace_index].tolist(),
                            foot_contact_forces_world=base.scene["contact_forces"].data.net_forces_w[trace_index, sensor.body_ids].tolist(),

                            arm_joint_reference=controller.reference[trace_index].tolist(),
                            safe_approach_complete=bool(controller.safe_approach_complete[trace_index]),
                            approach_pitch_reference=controller.approach_pitch_reference[trace_index].item(),
                            debug_gate_velocity_ready=controller.debug_gate_velocity_ready[trace_index].item(),
                            debug_gate_geometric_ready=controller.debug_gate_geometric_ready[trace_index].item(),
                            debug_predicted_clearance=controller.debug_predicted_clearance[trace_index].item(),
                            debug_arm_velocity=controller.debug_arm_velocity[trace_index].detach().cpu().tolist(),
                            debug_reference_post_geometry=controller.debug_reference_post_geometry[trace_index].detach().cpu().tolist(),
                            debug_reference_pre_geometry=controller.debug_reference_pre_geometry[trace_index].detach().cpu().tolist(),
                            debug_pose_desired=controller.debug_pose_desired[trace_index].detach().cpu().tolist(),
                            debug_pose_rotation_error=controller.debug_pose_rotation_error[trace_index].detach().cpu().tolist(),
                            debug_pose_position_error=controller.debug_pose_position_error[trace_index].detach().cpu().tolist(),
                            approach_height_aligned=bool(controller.approach_height_aligned[trace_index]),
                            approach_gate_advance=controller.approach_gate_advance[trace_index].item(),
                            approach_face_ready=bool(controller.approach_face_ready[trace_index]),
                            safe_approach_index=int(controller.safe_approach_index[trace_index]),
                            body_ready=bool(controller.body_ready[trace_index]),
                            body_stable=bool(body_stable[trace_index]),
                            body_ready_duration=controller.body_ready_duration[trace_index].item(),
                            preapproach_elapsed=controller.preapproach_elapsed[trace_index].item(),
                            precontact_ready=bool(controller.precontact_ready[trace_index]),
                            precontact_joint_error=(
                                robot.data.joint_pos[trace_index, controller.joint_ids] - controller.precontact_posture
                            ).abs().amax().item() if controller.precontact_posture.numel() else 0.0,
                            motion_ready=bool(controller.motion_ready[trace_index]),
                            face_local=face[trace_index].tolist(),
                            base_height=base_height[trace_index].item(),
                            linear_speed=torch.linalg.vector_norm(robot.data.root_lin_vel_w[trace_index]).item(),
                            angular_speed=torch.linalg.vector_norm(robot.data.root_ang_vel_w[trace_index]).item(),
                            contact_duration=controller.contact_duration[trace_index].item(),
                            policy_leg_action=action_term.raw_actions[trace_index].tolist(),
                            joint_command_leg_action=action_term.joint_commands[trace_index, controller.leg_slots].tolist(),
                        )
                trace.append(sample)
                if shadow is not None:
                    shadow.observe(sample)
                if delayed_shadow is not None:
                    delayed_shadow.observe(sample)
            if video is not None and step % 2 == 0:
                video.append_data(base.render())
            actor_input = torch.cat([observation[name] for name in observation_groups], dim=-1)
            if args.neutral_push_command:
                actor_input[:, 189:210] = actor_input.new_tensor((0.5, 0.0, 0.4, 1.0, 0.0, 0.0, 0.0)).repeat(3)
            actions = policy(actor_input)
            if deployment_actor is not None:
                deployed_actions = deployment_actor(actor_input)
                torch.testing.assert_close(deployed_actions, actions, rtol=1e-6, atol=1e-6)
                deployment_max_error = max(deployment_max_error, (deployed_actions - actions).abs().max().item())
                deployment_comparisons += int(active.sum().item())
            if arm_controller is not None:
                actions = arm_controller.apply(actions)
            if args.neutral_arm:
                actions = actions.clone()
                actions[:, 12:] = 0.0
            if step * base.step_dt < args.preparation_seconds:
                actions = torch.zeros_like(actions)
            if sample is not None:
                sample["applied_action"] = actions[trace_index].tolist()
            if failure_history is not None:
                # Read existing state only: do not call push_hand_target or
                # controller.apply, which advance controller state. Target and
                # joint references belong to the previously executed command;
                # next_policy_action is the action about to enter env.step.
                action_term = base.action_manager.get_term("joint_pos")
                controller = action_term.controller
                face, _height, _stable = box_push.preapproach_state(base)
                contact_position = base.scene["box_contact_hand"].data.contact_pos_w[:, 0, 0]
                failure_history.append(
                    active,
                    elapsed_seconds=base.episode_length_buf * base.step_dt,
                    robot_position=robot.data.root_pos_w - base.scene.env_origins,
                    robot_quaternion=robot.data.root_quat_w,
                    robot_velocity=robot.data.root_lin_vel_w,
                    box_position=base.scene["box"].data.root_pos_w - base.scene.env_origins,
                    box_quaternion=base.scene["box"].data.root_quat_w,
                    hand_position=robot.data.body_pos_w[:, hand.body_ids[0]] - base.scene.env_origins,
                    hand_quaternion=robot.data.body_quat_w[:, hand.body_ids[0]],
                    hand_contact_valid=condition,
                    forbidden_box_contact=box_push.forbidden_box_contact(base),
                    hand_force=hand_force,
                    hand_contact_position=torch.nan_to_num(contact_position - base.scene.env_origins),
                    hand_contact_position_valid=torch.isfinite(contact_position).all(dim=1),
                    arm_command_position=controller.target_position - base.scene.env_origins,
                    arm_joint_position=robot.data.joint_pos[:, controller.joint_ids],
                    arm_joint_reference=controller.reference,
                    arm_joint_target=robot.data.joint_pos_target[:, controller.joint_ids],
                    arm_joint_velocity=robot.data.joint_vel[:, controller.joint_ids],
                    arm_applied_torque=robot.data.applied_torque[:, controller.joint_ids],
                    face_local=face,
                    velocity_command=box_push.push_velocity_commands(base, hand),
                    safe_approach_complete=controller.safe_approach_complete,
                    safe_approach_index=controller.safe_approach_index,
                    approach_completed=base.box_push_approached,
                    motion_ready=controller.motion_ready,
                    leg_release_blend=controller.leg_release_blend,
                    ik_clearance_distance=controller.clearance_distance,
                    next_policy_action=actions,
                    geometry_clearance=controller.geometry_clearance,
                debug_gate_velocity_ready=controller.debug_gate_velocity_ready,
                debug_gate_geometric_ready=controller.debug_gate_geometric_ready,
                debug_predicted_clearance=controller.debug_predicted_clearance,
                debug_arm_velocity=controller.debug_arm_velocity,
                debug_reference_post_geometry=controller.debug_reference_post_geometry,
                debug_reference_pre_geometry=controller.debug_reference_pre_geometry,
                debug_pose_desired=controller.debug_pose_desired,
                debug_pose_rotation_error=controller.debug_pose_rotation_error,
                debug_pose_position_error=controller.debug_pose_position_error,
                    geometry_blocked=controller.geometry_blocked,
                )
            observation, _rewards, dones, _extras = env.step(actions)
            done = dones.bool()
            sample_motion(active & ~done)
            if arm_controller is not None:
                arm_controller.reset(done.nonzero(as_tuple=False).flatten())
            success = done & base.termination_manager.get_term("box_settled")
            for name in base.termination_manager.active_terms:
                if name not in ("box_settled", "time_out"):
                    success &= ~base.termination_manager.get_term(name)
            counted = quota.record(done, success)
            motion.reset_reference(counted, robot.data.joint_pos)
            for name in reasons:
                reasons[name] += int((counted & base.termination_manager.get_term(name)).sum().item())
            condition_duration[done] = 0.0
            if (step + 1) % 200 == 0:
                print(f"EVAL_STEP={step + 1} completed={completions.sum().item()} successes={successes.sum().item()}", flush=True)
            if not quota.active.any():
                break
    if video is not None:
        video.close()
    if climbing:
        terrain = config.scene.terrain.terrain_generator.sub_terrains["box"]
        actual_physics = {
            "box_height_range": terrain.box_height_range, "fixed_support": True,
            "approach_height": terrain.approach_height, "approach_gap": terrain.approach_gap,
            "approach_gap_range": terrain.approach_gap_range,
            "approach_length": terrain.approach_length, "approach_width": terrain.approach_width,
            "landing_length": terrain.box_length, "landing_width": terrain.box_width,
            "following_platform_height": terrain.following_platform_height,
            "following_platform_gap": terrain.following_platform_gap,
            "terrain_static_friction": config.scene.terrain.physics_material.static_friction,
            "terrain_dynamic_friction": config.scene.terrain.physics_material.dynamic_friction,
            "start_clearance": config.scene.robot.init_state.pos[2],
            "prepared_start_path": config.prepared_start_path,
            "prepared_start_phase": config.prepared_start_phase if config.prepared_start_path else None,
            "prepared_start_sha256": hashlib.sha256(Path(config.prepared_start_path).read_bytes()).hexdigest() if config.prepared_start_path else None,
        }
    else:
        box = base.scene["box"]
        actual_physics = {
            "box_mass_per_env": box.root_physx_view.get_masses().flatten().tolist(),
            "box_material_per_env": box.root_physx_view.get_material_properties().tolist(),
            "box_size": config.box_size, "fixed_support": False,
            "push_press_depth": config.push_press_depth, "push_distance": config.push_distance,
            "push_approach_distance": config.push_approach_distance,
            "push_hand_height_offset": config.push_hand_height_offset,
        }
    mdp_directory = Path(box_push.__file__).resolve().parent
    repository = Path(os.environ["PIPER_SOURCE_ROOT"]).resolve()
    robot_asset_directory = Path(config.scene.robot.spawn.usd_path).resolve().parent
    robot_asset_paths = sorted(robot_asset_directory.rglob("*.usd"))
    robot_asset_paths.extend(robot_asset_directory.glob("*.py"))
    actual_physics.update(
        robot_asset_sha256={str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest() for path in robot_asset_paths},
        robot_joint_names=list(robot.joint_names),
        robot_effort_limits=robot.data.joint_effort_limits[0].tolist(),
        robot_joint_defaults=robot.data.default_joint_pos[0].tolist(),
    )
    if hybrid_push:
        controller = base.action_manager.get_term("joint_pos").controller
        actual_physics["controller_contract"] = {
            "approach_pitch_start": 1.5,
            "approach_pitch_transition": "gate_advance_0_to_90mm",
            "approach_damped_ik": False,
            "approach_reference_rate": 0.25,
            "shield_diagnostics": True,
            "nominal_ik_clearance_margin": 0.055,
            "nominal_ik_clearance_weight": 10.0,
            "nominal_clearance_during_loaded_push": True,
            "preserve_incremental_clearance_recovery": True,
            "shield_reference_rate": 0.25,
            "nominal_shield_rate_decoupled": False,
            "approach_orientation_weight": 0.1,
            "pushing_orientation_weight": args.push_ik_orientation_weight,
            "approach_contact_confirmation_s": getattr(controller, "approach_contact_confirmation_s", None),
            "geometry_observation_scope": getattr(controller.geometry_shield, "observation_scope", "intervention_active_steps_only"),
            "diagnostic_hand_lateral_offset": getattr(controller, "diagnostic_hand_lateral_offset", 0.0),
            "lock_arm_on_contact": controller.lock_arm_on_contact,
            "align_hand_orientation": getattr(controller, "align_hand_orientation", False),
            "hand_pitch": getattr(config.actions.joint_pos, "hand_pitch", 0.0),
            "approach_distance": config.push_approach_distance,
            "hand_height_offset": config.push_hand_height_offset,
            "press_depth": config.push_press_depth, "control_dt": base.step_dt,
            "precontact_heights": controller.precontact_heights.tolist(),
            "ik_clearance_minimum": controller.clearance_minimum,
            "ik_orientation_weight": controller.orientation_weight,
            "ik_height_weight": controller.height_weight,
            "ik_joint_limit_solve": controller.joint_limit_solve,
            "goal_hold_pose": controller.goal_hold_pose,
            "goal_release_distance": controller.goal_release_distance,
            "goal_brake_gain": getattr(config, "push_goal_brake_gain", 0.0),
            "press_on_legal_contact": getattr(config, "push_press_on_legal_contact", False),
            "control_stop_distance": getattr(config, "push_stop_distance", 0.10),
            "leg_release_on_contact": controller.leg_release_on_contact,
            "contact_memory_s": controller.contact_memory_s,
            "leg_release_ramp_s": controller.leg_release_ramp_s,
            "leg_contact_ramp_s": controller.leg_contact_ramp_s,
            "forward_command_gain": getattr(config, "push_forward_command_gain", 1.0),
            "contact_gap_slowdown_start": getattr(config, "push_contact_gap_slowdown_start", 0.0),
            "target_maximum_reach": getattr(config, "push_target_maximum_reach", 0.0),
            "velocity_feedback_gain": getattr(config, "push_velocity_feedback_gain", 0.0),
            "velocity_integral_gain": controller.velocity_integral_gain,
            "body_first": controller.body_first,
            "preapproach_base_gap": getattr(config, "push_preapproach_base_gap", None) if controller.body_first else None,
            "ik_clearance_geometry": "body_centers_linearized" if controller.clearance_minimum is not None else None,
        }
    control_files = ("box_climb.py", "box_rewards.py", "box_terrain.py") if climbing else ("box_push.py", "box_push_control.py", "box_rewards.py")
    if climbing and config.prepared_start_path:
        control_files += ("climb_start_states.py",)
    if args.arm_ik:
        control_files += ("box_push_ik.py",)
    if hybrid_push:
        control_files += ("box_push_ik.py", "box_push_actions.py")
    result = {
        "stage_start_hold_diagnostic": stage_hold.summary(),
        "schema_version": 4,
        "policy_contract": "v117:226in->12frozen_leg_means+6post_face_arm_residual;not_legacy",
        "safe_training_source_sha256": hashlib.sha256((Path(__file__).parent / "rsl_rl/safe_retraining.py").read_bytes()).hexdigest(), "episodes_per_env": args.episodes_per_env,
        "neutral_arm_diagnostic": args.neutral_arm,
        "neutral_push_command_diagnostic": args.neutral_push_command,
        "preparation_seconds": args.preparation_seconds,
        "observation_noise_diagnostic": args.observation_noise,
        "collision_variant_diagnostic": collision_variant is not None,
        "collision_variant": collision_variant,
        "base_start_diagnostic": args.base_start_x is not None,
        "neutral_legs_diagnostic": args.neutral_legs,
        "base_start_position": config.scene.robot.init_state.pos,
        "terminal_states": terminal_states,
        "termination_flag_names": list(base.termination_manager.active_terms),
        "requested_episodes": args.num_envs * args.episodes_per_env,
        "incomplete_episodes": int((args.episodes_per_env - completions).sum().item()),
        "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest() if args.checkpoint else None,
        "actor_policy": str(args.actor_policy) if args.actor_policy else None,
        "actor_policy_sha256": hashlib.sha256(args.actor_policy.read_bytes()).hexdigest() if args.actor_policy else None,
        "locomotion_policy": str(args.locomotion_policy) if args.locomotion_policy else None,
        "locomotion_policy_sha256": hashlib.sha256(args.locomotion_policy.read_bytes()).hexdigest() if args.locomotion_policy else None,
        "evaluation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "deployment_actor_sha256": hashlib.sha256(args.deployment_actor.read_bytes()).hexdigest() if args.deployment_actor else None,
        "deployment_actor_max_abs_error": deployment_max_error if deployment_actor is not None else None,
        "deployment_actor_comparisons": deployment_comparisons,
        "control_sha256": {name: hashlib.sha256((mdp_directory / name).read_bytes()).hexdigest() for name in control_files},
        "actual_physics": actual_physics, "executed_steps": step + 1,
        "episode_length_s": config.episode_length_s,
        "arm_controller": "trained_legs_with_ik_arm" if hybrid_push else "differential_ik_gravity_diagnostic" if args.arm_ik else "learned_policy",
        "stand_until_arm_ready": args.locomotion_policy is not None or hybrid_push,
        "lock_arm_on_contact": base.action_manager.get_term("joint_pos").controller.lock_arm_on_contact if hybrid_push else args.locomotion_policy is not None,
        "inspect_env_index": trace_index, f"trace_env{trace_index}": trace, "video_path": str(args.video_path) if args.video_path else None,
        "world_model_shadow": shadow.result(terminal_states[0]["elapsed_seconds"]) if shadow is not None else None,
        "delayed_margin_shadow": delayed_shadow.result(terminal_states[0]["elapsed_seconds"]) if delayed_shadow is not None else None,
        "failure_history_steps": args.failure_history_steps,
        "failure_history_step_dt": float(base.step_dt),
        "failure_history_arm_joint_names": [robot.joint_names[i] for i in base.action_manager.get_term("joint_pos").controller.joint_ids] if failure_history is not None else [],
        "failure_histories": failure_histories,
        "failure_history_sample_phase": "pre_env_step; controller targets describe previous command; next_policy_action is the next action; terminal_state_index points to the post-physics pre-reset state",
        "evaluation_helpers_sha256": {"box_evaluation_metrics.py": hashlib.sha256((Path(__file__).parent / "box_evaluation_metrics.py").read_bytes()).hexdigest()},
        "task": args.task, "checkpoint": str(args.checkpoint) if args.checkpoint else None, "seed": args.seed,
        "num_envs": args.num_envs, "steps": args.steps, "box_height": args.box_height,
        "box_mass": args.box_mass, "box_friction": args.box_friction,
        "completed_episodes": int(completions.sum().item()), "successful_episodes": int(successes.sum().item()),
        "per_env_completions": completions.tolist(), "per_env_successes": successes.tolist(),
        "termination_reasons": reasons, "max_forward_per_env": maximum_forward.tolist(),
        "min_base_height_per_env": minimum_base_height.tolist(), "max_tilt_radians_per_env": maximum_tilt.tolist(),
        "max_standing_seconds" if climbing else "max_hand_contact_seconds": maximum_condition.tolist(),
        "max_supported_feet": maximum_support.tolist() if climbing else None,
        "max_torque_limit_ratio": maximum_torque_ratio,
        "joint_motion": motion.summary(),
        "push_contact_steps": push_contact_steps.tolist() if not climbing else None,
        "unclassified_hand_contact_steps": unclassified_hand_contact_steps.tolist() if not climbing else None,
        "max_unclassified_hand_force": maximum_unclassified_hand_force.tolist() if not climbing else None,
        "mean_hand_force_on_contact": (push_force_sum / push_contact_steps.clamp_min(1.0)).tolist() if not climbing else None,
        "max_hand_force": maximum_push_force.tolist() if not climbing else None,
        "joint_names": robot.joint_names, "body_names": robot.body_names,
        "contact_body_names": list(base.scene["contact_forces"].body_names),
        "max_abs_joint_velocity": maximum_joint_velocity.tolist(),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print("BOX_SKILL_EVALUATION=" + json.dumps(result, allow_nan=False))
    env.close()


try:
    main()
except Exception:
    traceback.print_exc()
    import os as failure_os,sys as failure_sys
    failure_sys.stdout.flush();failure_sys.stderr.flush();failure_os._exit(1)
else:
    launcher.app.close()
