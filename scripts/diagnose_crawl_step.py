"""Remote Isaac diagnostic of one flat-ground step, not CLIMB acceptance."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--num-envs", type=int, default=32)
parser.add_argument("--seed", type=int, default=512)
parser.add_argument("--shift-mode", choices=("centroid", "none"), default="centroid")
parser.add_argument("--shift-target", choices=("centroid", "margin"), default="centroid")
parser.add_argument("--desired-margin", type=float, default=.03)
parser.add_argument("--gain", type=float, default=1.)
parser.add_argument("--feedback-mode", choices=("reference_integral", "posture_pd", "anchor_ik"), default="anchor_ik")
parser.add_argument("--damping-s", type=float, default=.3)
parser.add_argument("--audit-jacobian", action="store_true")
parser.add_argument("--body-feedback", type=float, default=.5)
parser.add_argument("--body-damping-s", type=float, default=.1)
parser.add_argument("--body-feedback-after-shift", action="store_true")
parser.add_argument("--stance-after-landing", action="store_true")
parser.add_argument("--swing-integral-gain", type=float, default=0.)
parser.add_argument("--swing-feedback", type=float, default=1.)
parser.add_argument("--swing-damping-s", type=float, default=.1)
parser.add_argument("--unload-before-lift", action="store_true")
parser.add_argument("--step-body-advance-m", type=float, default=0.)
parser.add_argument("--reload-on-contact", action="store_true")
parser.add_argument("--landing-probe-m", type=float, default=0.)
parser.add_argument("--reload-touch-force-n", type=float, default=2.)
parser.add_argument("--next-support-only", action="store_true")
parser.add_argument("--next-shift-max-m", type=float, default=.10)
parser.add_argument("--next-unload-only", action="store_true")
parser.add_argument("--continuous-swing-s", type=float, default=0.)
parser.add_argument("--reuse-landing-stability", action="store_true")
parser.add_argument("--next-step", action="store_true", help="Execute the optional RR flat step; not climb acceptance")
parser.add_argument("--prepare-with-shift", action="store_true", help="Combine initial four-foot leveling and COM shift")
parser.add_argument("--first-leg", choices=("FL", "FR"), default="FL",
                    help="Independent flat pair diagnostic: FL/RR or FR/RL, not a consecutive four-step cycle")
parser.add_argument("--approach-support-search", action="store_true", help="Search alternative support placements within the eroded triangle for joint feasibility")
parser.add_argument("--plan-approach", action="store_true", help="Joint/body sampled preflight; stop before unloading when no ground reference is feasible")
parser.add_argument("--approach-stride-m", type=float, default=0., help="Experimental ground approach stride, capped before the box; not a step-up controller")
parser.add_argument("--cyclic", action="store_true", help="Experimental continuous FL/RR/FR/RL schedule, same24s")
parser.add_argument("--prepare-for-next-support", action="store_true", help="Place initial COM for the next support while preserving current swing margin")
parser.add_argument("--bounded-cyclic-swing", action="store_true", help="Allow cyclic arc duration >=1.8s; nominal peak speed <.12m/s and acceleration <.4m/s2")
parser.add_argument("--adaptive-preparation", action="store_true", help="Size leveling/COM transfer duration from nominal velocity and acceleration budgets")
parser.add_argument("--early-preparation", action="store_true", help="Allow preparation from1s after four-contact and velocity gates; retain post-leveling rest")
parser.add_argument("--overlap-landing-waits", action="store_true", help="Search for contact after the arc while end stability is checked; reuse first measured loaded rest")
parser.add_argument("--force-feedforward", action="store_true")
parser.add_argument("--support-wrench", choices=("none", "damping"), default="none")
parser.add_argument("--pose-reference", choices=("linear", "analytic"), default="linear")
parser.add_argument("--idle-only", action="store_true")
parser.add_argument("--climb-start-s", type=float, default=2.)
parser.add_argument("--start-stable-s", type=float, default=0.)
parser.add_argument("--takeover-s", type=float, default=0.)
parser.add_argument("--level-stance", action="store_true")
parser.add_argument("--level-before-step", action="store_true")
parser.add_argument("--nav-policy", type=Path)
parser.add_argument("--nav-observe-only", action="store_true")
parser.add_argument("--nav-ramp-s", type=float, default=0.)
parser.add_argument("--force-geometry", choices=("live", "planned"), default="live")
parser.add_argument("--stop-after-shift", action="store_true")
parser.add_argument("--force-filter-s", type=float, default=0.)
parser.add_argument("--hold-reference-mode", choices=("none", "command", "equilibrium"), default="none")
parser.add_argument("--capture-between-steps", action="store_true")
parser.add_argument("--capture-after-landing-only", action="store_true")
parser.add_argument("--settled-landing-capture", action="store_true")
parser.add_argument("--video-path", type=Path)
parser.add_argument("--camera-side", choices=("auto", "left", "right"), default="auto")
parser.add_argument("--inspect-env-index", type=int, default=0)
parser.add_argument("--trace-stride", type=int, default=10)
parser.add_argument("--output", type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.nav_policy and not args.idle_only:
    parser.error("NAV compatibility probe currently requires idle-only; transfer is not validated")
if args.nav_observe_only and not args.nav_policy:
    parser.error("NAV observe-only requires a policy for the matched observation configuration")
if not math.isfinite(args.nav_ramp_s) or args.nav_ramp_s < 0 or (args.nav_ramp_s and not args.nav_policy):
    parser.error("NAV ramp requires a policy and a finite nonnegative duration")
if args.nav_policy and hashlib.sha256(args.nav_policy.read_bytes()).hexdigest() != "72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8":
    parser.error("Expected the frozen PIPER NAV actor")
if not 0 <= args.inspect_env_index < args.num_envs:
    parser.error("inspect-env-index must be in the simulated batch")
if args.trace_stride < 1:
    parser.error("trace-stride must be positive")
if args.video_path:
    if args.video_path.exists():
        parser.error("Refusing to overwrite a video")
    args.enable_cameras = True
launcher = AppLauncher(args)

import gymnasium as gym
import torch
import LeggedManip_Lab.tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab.utils.io import dump_yaml
import crawl_support
from box_evaluation_metrics import ClimbGaitTelemetry, JointMotionTelemetry, EpisodeHistory


def main():
    cfg = load_cfg_from_registry("GO2-PIPER-Box-Climb-Crawl-Play", "env_cfg_entry_point")
    cfg.scene.num_envs = args.num_envs
    cfg.seed = args.seed
    cfg.sim.device = args.device
    native = None
    if args.nav_policy:
        native = load_cfg_from_registry("GO2-PIPER-Flat", "env_cfg_entry_point")
        if native.scene.robot.init_state.joint_pos != cfg.scene.robot.init_state.joint_pos:
            raise RuntimeError("NAV default joint offsets differ from the crawl model")
        cfg.observations.native_nav = copy.deepcopy(native.observations.policy)
        cfg.observations.native_nav.enable_corruption = False
        cfg.commands.base_velocity = copy.deepcopy(native.commands.base_velocity)
        cfg.commands.ee_pose = copy.deepcopy(native.commands.ee_pose)
        for command in (cfg.commands.base_velocity, cfg.commands.ee_pose):
            command.debug_vis = False
            command.resampling_time_range = (10000., 10000.)
            command.curriculum_enabled = False
        cfg.commands.base_velocity.heading_command = False
        cfg.commands.base_velocity.rel_standing_envs = 0.
        for ranges in (cfg.commands.base_velocity.ranges, cfg.commands.base_velocity.limit_ranges):
            for name in ("lin_vel_x", "lin_vel_y", "ang_vel_z"):
                setattr(ranges, name, (0., 0.))
        for ranges in (cfg.commands.ee_pose.ranges, cfg.commands.ee_pose.limit_ranges):
            for name, value in zip(("pos_x", "pos_y", "pos_z", "roll", "pitch", "yaw"), (.5, 0., .1, 0., 0., 0.)):
                setattr(ranges, name, (value, value))
    if args.video_path:
        cfg.viewer.origin_type = "env"
        cfg.viewer.env_index = args.inspect_env_index
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dump_yaml(str(args.output.with_suffix(".env.yaml")), cfg)
    env = gym.make("GO2-PIPER-Box-Climb-Crawl-Play", cfg=cfg, render_mode="rgb_array" if args.video_path else None)
    video = None
    try:
        observations, _ = env.reset()
        base = env.unwrapped
        controller = crawl_support.SingleStepController(base, shift=args.shift_mode == "centroid", gain=args.gain,
                                                       feedback_mode=args.feedback_mode, damping_s=args.damping_s,
                                                       body_feedback=args.body_feedback, swing_feedback=args.swing_feedback,
                                                       force_feedforward=args.force_feedforward,
                                                       shift_target=args.shift_target, desired_margin=args.desired_margin,
                                                       body_damping_s=args.body_damping_s,
                                                       body_feedback_after_shift=args.body_feedback_after_shift,
                                                       stance_after_landing=args.stance_after_landing,
                                                       swing_integral_gain=args.swing_integral_gain,
                                                       force_geometry=args.force_geometry, stop_after_shift=args.stop_after_shift,
                                                       force_filter_s=args.force_filter_s, hold_reference_mode=args.hold_reference_mode,
                                                       capture_between_steps=args.capture_between_steps,
                                                       capture_after_landing_only=args.capture_after_landing_only,
                                                       settled_landing_capture=args.settled_landing_capture,
                                                       support_wrench=args.support_wrench, pose_reference=args.pose_reference,
                                                       idle_only=args.idle_only, climb_start_s=args.climb_start_s,
                                                       start_stable_s=args.start_stable_s, takeover_s=args.takeover_s,
                                                       level_stance=args.level_stance, level_before_step=args.level_before_step,
                                                       swing_damping_s=args.swing_damping_s,
                                                       unload_before_lift=args.unload_before_lift,
                                                       step_body_advance_m=args.step_body_advance_m,
                                                       reload_on_contact=args.reload_on_contact,
                                                       landing_probe_m=args.landing_probe_m,
                                                       reload_touch_force_n=args.reload_touch_force_n,
                                                       next_support_only=args.next_support_only,
                                                       next_shift_max_m=args.next_shift_max_m,
                                                       next_unload_only=args.next_unload_only,
                                                       continuous_swing_s=args.continuous_swing_s,
                                                       reuse_landing_stability=args.reuse_landing_stability,
                                                       next_step=args.next_step,
                                                       prepare_with_shift=args.prepare_with_shift,
                                                       first_leg=args.first_leg, cyclic=args.cyclic,
                                                       prepare_for_next_support=args.prepare_for_next_support,
                                                       bounded_cyclic_swing=args.bounded_cyclic_swing,
                                                       adaptive_preparation=args.adaptive_preparation,
                                                       early_preparation=args.early_preparation,
                                                       overlap_landing_waits=args.overlap_landing_waits,
                                                       approach_stride_m=args.approach_stride_m,plan_approach=args.plan_approach,
                                                       approach_support_search=args.approach_support_search)
        robot = base.scene["robot"]
        nav = torch.jit.load(str(args.nav_policy), map_location=base.device).eval() if args.nav_policy else None
        nav_audit = None
        if nav is not None:
            native_ids = robot.find_joints(native.actions.joint_pos.joint_names, preserve_order=True)[0]
            if native_ids != controller.joint_ids or native.actions.joint_pos.scale != controller.action.cfg.scale:
                raise RuntimeError("NAV action order/scale differs from crawl action contract")
            if observations["native_nav"].shape != (args.num_envs, 210):
                raise RuntimeError("Expected native 210-dimensional observation with manager-maintained history")
            nav_audit = dict(policy_sha256=hashlib.sha256(args.nav_policy.read_bytes()).hexdigest(),
                             observe_only=args.nav_observe_only, history_length=cfg.observations.native_nav.history_length,
                             observation_terms=base.observation_manager.active_terms["native_nav"],
                             action_joint_names=[robot.joint_names[i] for i in native_ids],
                             action_scale=controller.action.cfg.scale, start_s=2.,
                             ramp_s=args.nav_ramp_s, default_joint_positions=robot.data.default_joint_pos[0].tolist(),
                             command=base.command_manager.get_command("ee_pose").tolist(),
                             scope="Native observation group and real history; crawl rate/acceleration limits and safety unchanged. Not native-task acceptance.",
                             observation_samples=[])
        initial_actuator_delays = {name: actuator.positions_delay_buffer.time_lags.tolist()
                                   for name, actuator in robot.actuators.items()
                                   if hasattr(actuator, "positions_delay_buffer")}
        active = torch.ones(args.num_envs, dtype=torch.bool, device=base.device)
        held = torch.zeros(args.num_envs, device=base.device)
        verified = torch.zeros_like(active)
        quiet_seconds = torch.zeros_like(held)
        quiet_anchor = robot.data.root_pos_w.clone()
        history = EpisodeHistory(args.num_envs, 256, base.device)
        failure_histories = []
        shift_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        landing_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        idle_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        preparation_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        level_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        swing_quality = crawl_support.SwingQuality(args.num_envs, base.device)
        unload_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        swing_support_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt, foot_count=3)
        next_support_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt)
        next_support_quiet = torch.zeros(args.num_envs, device=base.device)
        next_support_verified = torch.zeros(args.num_envs, device=base.device, dtype=torch.bool)
        next_unload_hold = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt, foot_count=3)
        rr_swing_quality = crawl_support.SwingQuality(args.num_envs, base.device)
        rr_support_quality = crawl_support.HoldQuality(args.num_envs, base.device, base.step_dt, foot_count=3)
        cycle_swing = [crawl_support.SwingQuality(args.num_envs, base.device) for _ in range(4)]
        if args.video_path:
            import imageio.v2 as imageio
            from isaacsim.core.utils.stage import get_current_stage
            from pxr import UsdGeom
            stage = get_current_stage()
            for index in range(args.num_envs):
                if index != args.inspect_env_index:
                    UsdGeom.Imageable(stage.GetPrimAtPath(f"/World/envs/env_{index}")).MakeInvisible()
            UsdGeom.Imageable(stage.GetPrimAtPath(f"/World/envs/env_{args.inspect_env_index}")).CreateVisibilityAttr().Set(UsdGeom.Tokens.inherited)
            origin = base.scene.env_origins[args.inspect_env_index].cpu().numpy()
            camera_y = 2.2 if args.first_leg == "FL" else -2.2
            if args.camera_side != "auto":
                camera_y = 2.2 if args.camera_side == "left" else -2.2
            base.sim.set_camera_view(eye=origin + [1.5, camera_y, 1.2], target=origin + [0., 0., .22])
            args.video_path.parent.mkdir(parents=True, exist_ok=True)
            video = imageio.get_writer(str(args.video_path), fps=round(1 / (2 * base.step_dt)), codec="libx264")
        gait = ClimbGaitTelemetry(args.num_envs, base.device, base.step_dt)
        maneuver_gait = ClimbGaitTelemetry(args.num_envs, base.device, base.step_dt)
        post_takeover_gait = ClimbGaitTelemetry(args.num_envs, base.device, base.step_dt)
        motion = JointMotionTelemetry(robot.data.joint_pos, base.step_dt)
        terminals, trace = [], []
        original = base.recorder_manager.record_pre_reset

        def sample(mask):
            feet = robot.data.body_pos_w[:, controller.feet_ids]
            if controller.cycle is not None:
                c = controller.cycle
                for leg, quality in enumerate(cycle_swing):
                    quality.sample(mask & (c.stage >= 2) & (c.stage <= 3) & (c.leg == leg) & ~controller.contacts()[:,leg],
                                   feet[:,leg], controller.foot_target[:,leg], robot.data.body_link_lin_vel_w[:,controller.feet_ids[leg]])
            swing_quality.sample(mask & (controller.phase >= 2) & (controller.phase <= 4) & ~controller.contacts()[:, 0],
                                 feet[:, 0], controller.foot_target[:, 0],
                                 robot.data.body_link_lin_vel_w[:, controller.feet_ids[0]])
            margin = crawl_support.triangle_margin(controller.com()[:, :2], feet[:, [1, 3, 2], :2])
            next_margin = crawl_support.triangle_margin(controller.com()[:, :2], feet[:, [0, 1, 2], :2])
            rr_stage = controller.rear_step.stage
            next_stage = (controller.phase == 7) & (rr_stage == 0)
            next_support_hold.sample(mask & next_stage, robot.data.root_pos_w, controller.base_target,
                                     feet, controller.foot_target, robot.data.root_lin_vel_w,
                                     robot.data.root_ang_vel_w, controller.contacts(), next_margin)
            next_ready = (next_stage & (controller.timer >= 3.) & controller.contacts().all(dim=1)
                          & (next_margin >= .015) & (robot.data.root_lin_vel_w.norm(dim=1) < .025)
                          & (robot.data.root_ang_vel_w.norm(dim=1) < .1)
                          & (robot.data.projected_gravity_b[:, 2] < -.98)
                          & ((robot.data.root_pos_w - controller.base_target).norm(dim=1) < .015))
            next_support_quiet[:] = torch.where(mask, torch.where(next_ready, next_support_quiet + base.step_dt, 0.), next_support_quiet)
            next_support_verified.logical_or_(mask & (next_support_quiet >= 1.))
            next_unload_hold.sample(mask & (controller.next_unload_started_at >= 0) & (rr_stage == 0),
                                    robot.data.root_pos_w, controller.base_target,
                                    feet[:, :3], controller.foot_target[:, :3], robot.data.root_lin_vel_w,
                                    robot.data.root_ang_vel_w, controller.contacts()[:, :3], next_margin)
            rr_swing_quality.sample(mask & (rr_stage > 0) & ~controller.contacts()[:, 3],
                                    feet[:, 3], controller.foot_target[:, 3],
                                    robot.data.body_link_lin_vel_w[:, controller.feet_ids[3]])
            rr_support_quality.sample(mask & (rr_stage > 0), robot.data.root_pos_w, controller.base_target,
                                      feet[:, :3], controller.foot_target[:, :3], robot.data.root_lin_vel_w,
                                      robot.data.root_ang_vel_w, controller.contacts()[:, :3], next_margin)
            unload_stage = (controller.phase == 2) & ~controller.lift_released & args.unload_before_lift
            unload_hold.sample(mask & unload_stage, robot.data.root_pos_w, controller.base_target,
                               feet, controller.foot_target, robot.data.root_lin_vel_w, robot.data.root_ang_vel_w,
                               controller.contacts()[:, 1:], margin)
            swing_stage = (controller.phase >= 2) & (controller.phase <= 4) & ~unload_stage
            swing_support_hold.sample(mask & swing_stage, robot.data.root_pos_w, controller.base_target,
                                      feet[:, 1:], controller.foot_target[:, 1:], robot.data.root_lin_vel_w,
                                      robot.data.root_ang_vel_w, controller.contacts()[:, 1:], margin)
            for quality, stage in ((level_hold, controller.preparing),
                                   (preparation_hold, controller.phase == 1),
                                   (idle_hold, (controller.phase == 0) & (base.episode_length_buf * base.step_dt >= 2.)),
                                   (shift_hold, (controller.phase == 1) & ~controller.preparing & (controller.timer >= 3.)),
                                   (landing_hold, (controller.phase >= 5) & (controller.phase <= 6))):
                quality.sample(mask & stage, robot.data.root_pos_w, controller.base_target,
                               feet, controller.foot_target, robot.data.root_lin_vel_w, robot.data.root_ang_vel_w,
                               controller.contacts(), margin)
            quiet = ((base.episode_length_buf * base.step_dt >= 5.) & controller.contacts().all(dim=1)
                     & (robot.data.root_lin_vel_w.norm(dim=1) < .025)
                     & (robot.data.root_ang_vel_w.norm(dim=1) < .1)
                     & (robot.data.projected_gravity_b[:, 2] < -.94))
            restart = mask & (quiet_seconds == 0)
            quiet_anchor[restart] = robot.data.root_pos_w[restart]
            quiet &= (robot.data.root_pos_w - quiet_anchor).norm(dim=1) < .01
            quiet_seconds[:] = torch.where(mask, torch.where(quiet, quiet_seconds + base.step_dt, 0.), quiet_seconds)
            stable = (controller.completed & controller.contacts().all(dim=1)
                      & (robot.data.root_lin_vel_w.norm(dim=1) < .05)
                      & (robot.data.root_ang_vel_w.norm(dim=1) < .4)
                      & (robot.data.projected_gravity_b[:, 2] < -.94)
                      & ((robot.data.body_pos_w[:, controller.feet_ids[0]] - controller.foot_target[:, 0]).norm(dim=1) < .025))
            held[:] = torch.where(mask, torch.where(stable, held + base.step_dt, 0.), held)
            verified.logical_or_(mask & (held >= 1.))
            contact = base.scene["contact_forces"].data
            gait.update(mask, base.episode_length_buf * base.step_dt,
                        contact.net_forces_w[:, controller.sensor_ids],
                        contact.net_forces_w_history[:, :, controller.sensor_ids], robot.data.root_lin_vel_w[:, 2])
            maneuver_gait.update(mask & (base.episode_length_buf * base.step_dt >= 2.),
                                 base.episode_length_buf * base.step_dt,
                                 contact.net_forces_w[:, controller.sensor_ids],
                                 contact.net_forces_w_history[:, :, controller.sensor_ids], robot.data.root_lin_vel_w[:, 2])
            post_takeover_gait.update(mask & (controller.preparation_started_at >= 0),
                                     base.episode_length_buf * base.step_dt,
                                     contact.net_forces_w[:, controller.sensor_ids],
                                     contact.net_forces_w_history[:, :, controller.sensor_ids], robot.data.root_lin_vel_w[:, 2])
            motion.sample(mask, robot.data.joint_pos_target, robot.data.joint_vel, robot.data.joint_acc,
                          robot.data.applied_torque, robot.data.joint_effort_limits, robot.data.root_ang_vel_w)
            history.append(mask, elapsed_s=base.episode_length_buf * base.step_dt, phase=controller.phase,
                           base_position=robot.data.root_pos_w - base.scene.env_origins,
                           base_target=controller.base_target - base.scene.env_origins,
                           linear_velocity=robot.data.root_lin_vel_w, angular_velocity=robot.data.root_ang_vel_w,
                           gravity_z=robot.data.projected_gravity_b[:, 2],
                           foot_force=contact.net_forces_w[:, controller.sensor_ids],
                           feet=robot.data.body_pos_w[:, controller.feet_ids] - base.scene.env_origins[:, None],
                           feet_target=controller.foot_target - base.scene.env_origins[:, None],
                           joint_position=robot.data.joint_pos, joint_target=robot.data.joint_pos_target,
                           torque=robot.data.applied_torque, support_force_target=controller.support_force,
                           **({"cycle_stage":controller.cycle.stage,"cycle_completed":controller.cycle.completed,
                               "cycle_leg":controller.cycle.leg,"cycle_reload":controller.cycle.reload,
                               "cycle_tail_index":controller.cycle.current_index,
                               "cycle_final_rest":controller.cycle.final_rest} if controller.cycle is not None else {}))

        def record(env_ids, *arguments, **keywords):
            selected = env_ids[active[env_ids]]
            mask = torch.zeros_like(active)
            mask[selected] = True
            sample(mask)
            fields = controller.state()
            for index in selected.tolist():
                state = {key: value[index].tolist() for key, value in fields.items()}
                state.update(env_id=index, elapsed_s=float(base.episode_length_buf[index] * base.step_dt),
                             next_support_verified_1s=bool(next_support_verified[index]),
                             next_support_final_quiet_s=float(next_support_quiet[index]),
                             single_step_verified_1s=bool(verified[index]),
                             final_step_stable_s=float(held[index]),
                             final_quiet_s=float(quiet_seconds[index]),
                             termination_flags={name: bool(base.termination_manager.get_term(name)[index]) for name in base.termination_manager.active_terms})
                terminals.append(state)
                if quiet_seconds[index] < 5. or (not (args.stop_after_shift or args.idle_only) and not verified[index]) or any(
                        value for name, value in state["termination_flags"].items() if name not in ("time_out", "box_settled")):
                    failure_histories.append({"env_id": index, "states": history.snapshot(index)})
            gait.reset_episode(env_ids)
            maneuver_gait.reset_episode(env_ids)
            post_takeover_gait.reset_episode(env_ids)
            active[selected] = False
            return original(env_ids, *arguments, **keywords)

        base.recorder_manager.record_pre_reset = record
        with torch.inference_mode():
            for step in range(1300):
                sample(active)
                actions = controller.compute(active)
                if nav is not None:
                    nav_observation = observations["native_nav"]
                    nav_actions = nav(nav_observation).clamp(-10., 10.)
                    if nav_actions.shape != actions.shape or not torch.isfinite(nav_actions).all():
                        raise RuntimeError("Invalid NAV output")
                    use_nav = active & (base.episode_length_buf * base.step_dt >= 2.)
                    if args.nav_ramp_s:
                        fraction = crawl_support.smooth_fraction((base.episode_length_buf * base.step_dt - 2.) / args.nav_ramp_s)
                        nav_actions = torch.lerp(actions, nav_actions, fraction[:, None])
                    if not args.nav_observe_only:
                        actions = torch.where(use_nav[:, None], nav_actions, actions)
                    if step in (0, 98, 99, 100, 101, 102, 103, 200):
                        index = args.inspect_env_index
                        nav_audit["observation_samples"].append(dict(step=step, observation=nav_observation[index].tolist(),
                                                                   requested_action=actions[index].tolist()))
                if video is not None and active[args.inspect_env_index] and step % 2 == 0:
                    video.append_data(base.render())
                index = args.inspect_env_index
                if active[index] and (step < 50 or step % args.trace_stride == 0):
                    state = {key: value[index].tolist() for key, value in controller.state().items()}
                    if args.audit_jacobian:
                        state.update({key: value[index].tolist() for key, value in controller.velocity_audit().items()})
                        state.update(joint_position=robot.data.joint_pos[index].tolist(),
                                     joint_target=robot.data.joint_pos_target[index].tolist(),
                                     joint_velocity=robot.data.joint_vel[index].tolist(),
                                     applied_joint_torque=robot.data.applied_torque[index].tolist(),
                                     root_quaternion=robot.data.root_quat_w[index].tolist())
                    state.update(step=step, robot_position=(robot.data.root_pos_w[index] - base.scene.env_origins[index]).tolist())
                    trace.append(state)
                observations, _, _, _, _ = env.step(actions)
                if (step + 1) % 200 == 0:
                    print("STEP", step + 1, "terminal", len(terminals), "single_step", int(controller.completed.sum()), "phases", controller.phase.bincount(minlength=7).tolist(), flush=True)
                    if controller.cycle is not None:
                        print("CYCLE tail_completed_counts", controller.cycle.completed.bincount(minlength=4).tolist(),
                              "four_steps_and_rest", int(controller.cycle.verified.sum()), flush=True)
                if not active.any():
                    break
        safety = [s for s in terminals if any(v for k, v in s["termination_flags"].items() if k not in ("time_out", "box_settled"))]
        result = dict(diagnostic=("FL_then_RR_flat_steps_not_climb_acceptance" if args.first_leg == "FL" else
                                  "FR_then_RL_independent_flat_pair_not_four_consecutive_steps") if args.next_step else
                      "FL_step_then_RR_unload_no_second_lift" if args.next_unload_only else
                      "FL_step_then_RR_support_transfer_no_second_lift" if args.next_support_only else
                      "ordinary_idle_stand_not_climb_acceptance" if args.idle_only else
                      ("support_shift_hold_not_climb_acceptance" if args.stop_after_shift else "kinematic_flat_ground_single_step_not_climb_acceptance"), shift_mode=args.shift_mode,
                      shift_target=args.shift_target, desired_margin=args.desired_margin,
                      seed=args.seed, gain=args.gain, feedback_mode=args.feedback_mode, damping_s=args.damping_s,
                      body_feedback=args.body_feedback, swing_feedback=args.swing_feedback,
                      body_damping_s=args.body_damping_s,
                      swing_damping_s=args.swing_damping_s, trace_stride=args.trace_stride,
                      unload_before_lift=args.unload_before_lift,
                      step_body_advance_m=args.step_body_advance_m,
                      reload_on_contact=args.reload_on_contact,
                      landing_probe_m=args.landing_probe_m,
                      next_support_only=args.next_support_only,
                      next_shift_max_m=args.next_shift_max_m,
                      next_unload_only=args.next_unload_only,
                      continuous_swing_s=args.continuous_swing_s,
                      reuse_landing_stability=args.reuse_landing_stability,
                      next_step=args.next_step,
                      prepare_with_shift=args.prepare_with_shift,
                      first_leg=args.first_leg, physical_step_order=[controller.leg_order[0], controller.leg_order[3]],
                      telemetry_leg_mapping={"first_step_legacy_FL_fields":controller.leg_order[0],
                                             "second_step_legacy_rr_fields":controller.leg_order[3],
                                             "foot_array_order":list(controller.leg_order)},
                      rr_step_verified_1s_without_safety_failure=sum(s["rr_step_verified_1s"] and s not in safety for s in terminals),
                      rr_swing_quality=rr_swing_quality.report(), rr_support_quality=rr_support_quality.report(),
                      rr_stage_names=["waiting", "arc", "contact_search_and_reload", "loaded_hold"],
                      continuous_swing_contract={"distance_m":controller.stride_m,"height_m":.05,"duration_s":args.continuous_swing_s,
                                                 "observed_clearance_min_m":.035,"observed_midpoint_x_min_m":.03,
                                                 "observed_midpoint_z_min_m":.03,"contact_reload_unchanged":True} if args.continuous_swing_s else None,
                      next_unload_verified_without_safety_failure=sum(s["next_unload_verified"] and s not in safety for s in terminals),
                      next_unload_quality=next_unload_hold.report(),
                      next_support_verified_1s_without_safety_failure=sum(s["next_support_verified_1s"] and s not in safety for s in terminals),
                      next_support_quality=next_support_hold.report(),
                      reload_gate={"contact_force_n":args.reload_touch_force_n, "support_contact_force_n":2., "continuous_contact_s":.06,
                                   "ramp_s":.5, "missing_support":"ramp clock retreats at1s/s"} if args.reload_on_contact else None,
                      lift_release_gate_columns=[*[leg + "_force_n" for leg in controller.leg_order],
                                                 "margin_m", "linear_speed_m_s", "angular_speed_rad_s", "stable_s"],
                      unloading_gate={"ramp_s":1., "measured_foot_force_max_n":5., "stable_s":.1,
                                      "support_margin_min_m":.015, "body_speed_max_m_s":.05,
                                      "body_angular_speed_max_rad_s":.1} if args.unload_before_lift else None,
                      swing_quality=swing_quality.report(),
                      body_feedback_after_shift=args.body_feedback_after_shift,
                      stance_after_landing=args.stance_after_landing, swing_integral_gain=args.swing_integral_gain,
                      initial_actuator_delay_physics_steps=initial_actuator_delays,
                      force_feedforward=args.force_feedforward,
                      support_wrench=args.support_wrench,
                      pose_reference=args.pose_reference, leg_geometry=controller.kinematics.geometry,
                      idle_only=args.idle_only, climb_start_s=args.climb_start_s,
                      start_stable_s=args.start_stable_s,
                      takeover_s=args.takeover_s,
                      level_stance=args.level_stance,
                      level_before_step=args.level_before_step,
                      nav_compatibility=nav_audit,
                      support_wrench_parameters={"velocity_gain_s_inv":4.,
                                                "max_acceleration_m_s2":.4, "scope":"flat-ground diagnostic only"} if args.support_wrench != "none" else None,
                      hold_quality={"scope":"Entire stage; displacement never resets on renewed quiet. Raw metrics, not climb acceptance.",
                                    "level":level_hold.report(), "preparation":preparation_hold.report(), "idle":idle_hold.report(),
                                    "shift":shift_hold.report(), "landing":landing_hold.report(),
                                    "unload":unload_hold.report(), "swing_support":swing_support_hold.report(),
                                    "support_scope":("unload tracks all4 foot positions; swing_support tracks FR/RL/RR. Both require only these3 stance contacts; swing body displacement includes planned motion." if args.first_leg == "FL" else
                                                     "unload tracks all4 positions in FR/FL/RR/RL order; first swing support is FL/RR/RL. Second swing support is FR/FL/RR. Displacements include planned motion.")},
                      force_geometry=args.force_geometry, stop_after_shift=args.stop_after_shift,
                      force_filter_s=args.force_filter_s,
                      hold_reference_mode=args.hold_reference_mode,
                      capture_between_steps=args.capture_between_steps,
                      capture_after_landing_only=args.capture_after_landing_only,
                      settled_landing_capture=args.settled_landing_capture,
                      landing_capture_criteria={"hold_s":.5, "linear_speed_m_s":.025, "angular_speed_rad_s":.1,
                                                "linear_acceleration_m_s2":.5, "angular_acceleration_rad_s2":1.} if args.settled_landing_capture else None,
                      single_step_and_quiet_hold_5s_without_safety_failure=sum(s["single_step_verified_1s"] and s["final_quiet_s"] >= 5. and s not in safety for s in terminals),
                      quiet_hold_5s_without_safety_failure=sum(s["final_quiet_s"] >= 5. and s not in safety for s in terminals),
                      quiet_hold_criteria={"hold_s":5., "linear_speed_m_s":.025, "angular_speed_rad_s":.1,
                                           "drift_m":.01, "projected_gravity_z":-.94, "four_contacts":True,
                                           "after_s":5., "scope":"additional stand diagnostic; original climb gates unchanged"},
                      failure_histories=failure_histories,
                      num_envs=args.num_envs, episode_length_s=cfg.episode_length_s,
                      completed_episodes=len(terminals), incomplete_episodes=int(active.sum()),
                      single_step_completed=sum(s["single_step_completed"] for s in terminals),
                      single_step_completed_without_safety_failure=sum(s["single_step_completed"] and s not in safety for s in terminals),
                      safety_terminated_episodes=len(safety), terminal_states=terminals,
                      single_step_verified_1s_without_safety_failure=sum(s["single_step_verified_1s"] and s not in safety for s in terminals),
                      single_step_verification={"hold_s": 1., "max_linear_speed_m_s": .05, "max_angular_speed_rad_s": .4,
                                                "max_projected_gravity_z": -.94, "max_landing_error_m": .025,
                                                "requires_four_contacts": True, "not_climb_acceptance": True},
                      video_path=str(args.video_path) if args.video_path else None, inspect_env_index=args.inspect_env_index,
                      phase_names=controller.names, joint_names=robot.joint_names,
                      action_joint_names=[robot.joint_names[i] for i in controller.joint_ids],
                      leg_reference_order={"legs":list(controller.kinematics.legs), "joints":["hip", "thigh", "calf"]},
                      robot_mass_kg=controller.mass.sum(dim=1).tolist(), gait_quality=gait.report(), joint_motion=motion.summary(),
                      source_sha256={str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__), Path(crawl_support.__file__), Path(__file__).with_name("box_evaluation_metrics.py"), Path(__file__).with_name("crawl_leg_kinematics.py"))},
                      collision_usd_sha256=hashlib.sha256(Path(cfg.scene.robot.spawn.usd_path).read_bytes()).hexdigest())
        # Record collision geometry alongside angular velocities so a moving
        # round foot center is not automatically classified as contact slip.
        from pxr import Usd, UsdGeom, UsdPhysics
        asset_stage = Usd.Stage.Open(cfg.scene.robot.spawn.usd_path)
        xforms = UsdGeom.XformCache()
        foot_geometry = []
        for prim in asset_stage.Traverse(Usd.TraverseInstanceProxies()):
            if not prim.HasAPI(UsdPhysics.CollisionAPI):
                continue
            parent = prim
            while parent and parent.GetName() not in ("FL_foot", "FR_foot", "RL_foot", "RR_foot"):
                parent = parent.GetParent()
            if not parent:
                continue
            relative, reset = xforms.ComputeRelativeTransform(prim, parent)
            foot_geometry.append(dict(foot=parent.GetName(), path=str(prim.GetPath()),
                                      shape=prim.GetTypeName(), radius=prim.GetAttribute("radius").Get(),
                                      transform_to_foot=[list(row) for row in relative], reset_stack=reset,
                                      collision_enabled=UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()))
        result["foot_collision_geometry"] = foot_geometry
        if args.cyclic:
            result['diagnostic'] = ('terrain_ground_approach_not_step_up_or_climb_acceptance' if args.approach_stride_m
                                    else 'continuous_FL_RR_FR_RL_flat_crawl_not_climb_acceptance')
            result['terrain_approach'] = dict(enabled=bool(args.approach_stride_m), stride_m=controller.stride_m,
                body_advance_per_step_m=args.step_body_advance_m, ground_target_edge_clearance_m=.06,
                planned_approach=args.plan_approach, support_search=args.approach_support_search, plan_input_layout={'base_xyz':3,'quaternion_wxyz':4,'com_xyz':3,'feet_FL_FR_RL_RR_xyz':12,'captured_joints_FL_FR_RL_RR':12,'soft_lower':12,'soft_upper':12,'leg':1,'positions':'relative to environment origin'}, plan_metrics_columns=['joint_margin_rad','sampled_joint_speed_rad_s','sampled_joint_acceleration_rad_s2','fk_residual_m','support_margin_m','feasible_candidates'],
                sampled_planner_contract={'samples':65,'joint_margin_rad':.025,'joint_speed_rad_s':1.,'joint_acceleration_rad_s2':5.,'finite_difference_multiplier':1.1,'body_speed_m_s':.075,'body_acceleration_m_s2':.133,'nominal_foot_speed_bound_m_s':.18},
                box_approach_distance_m=cfg.scene.terrain.terrain_generator.sub_terrains['box'].approach_distance,
                box_height_range_m=cfg.scene.terrain.terrain_generator.sub_terrains['box'].box_height_range,
                scope='Original reset, ground approach only. No20cm clearance path, no reset near the box, no task acceptance.')
            result['cycle_report'] = dict(
                prepare_for_next_support=args.prepare_for_next_support,
                bounded_cyclic_swing=args.bounded_cyclic_swing,
                adaptive_preparation=args.adaptive_preparation,
                early_preparation=args.early_preparation,
                overlap_landing_waits=args.overlap_landing_waits,
                early_preparation_gate_columns=['contact_count','linear_speed_m_s','angular_speed_rad_s','gravity_z','stable_s'],
                final_rest_reuses_last_landing_observations=True,
                swing_duration_s=args.continuous_swing_s,
                nominal_uninterrupted_arc_speed_bound_m_s=(math.hypot(1.875*controller.stride_m,.172) if args.approach_stride_m else .2)/args.continuous_swing_s,
                nominal_uninterrupted_arc_acceleration_bound_m_s2=(math.hypot(5.774*controller.stride_m,1.2) if args.approach_stride_m else 1.2)/args.continuous_swing_s**2,
                physical_step_order=['FL','RR','FR','RL'],
                internal_loaded_rest_s=.2, final_loaded_rest_s=1.,
                transfer_reference_max_speed_m_s=.075, transfer_reference_max_acceleration_m_s2=.133,
                tail_steps_completed_counts={str(k):sum(s['cycle_tail_steps_completed']==k for s in terminals) for k in range(4)},
                four_steps_and_1s_rest_without_safety_failure=sum(s['cycle_verified_4steps_1s'] and s not in safety for s in terminals),
                swing_quality_by_physical_leg={leg:q.report() for leg,q in zip(controller.leg_order,cycle_swing)},
                scope='One continuous first episode, no reset. Old two-step1s auxiliary counts do not define internal transition success.')
            path = Path(__file__).with_name('crawl_cycle.py')
            result['source_sha256'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            if args.plan_approach:
                path=Path(__file__).with_name('crawl_approach.py')
                result['source_sha256'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        result["measured_foot_force_semantics"] = "Isaac ContactSensor.net_forces_w: normal contact forces only; excludes tangential friction"
        result[f"trace_env{args.inspect_env_index}"] = trace
        result["maneuver_gait_quality"] = {**maneuver_gait.report(), "initial_exclusion_s": 2.,
                                            "scope": "Additional view after2s; full-episode gait_quality remains authoritative"}
        result["post_takeover_gait_quality"] = {**post_takeover_gait.report(),
            "scope": "From each environment's actual preparation takeover, including early motion before2s. Full-episode metrics still authoritative."}
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({k: result[k] for k in ("completed_episodes", "incomplete_episodes", "single_step_completed", "single_step_completed_without_safety_failure", "safety_terminated_episodes")}))
    finally:
        if video is not None:
            video.close()
        env.close()


try:
    main()
except BaseException as error:
    # Kit shutdown can exit before Python emits an uncaught exception. Save it
    # first so an aborted run cannot look like a clean completed evaluation.
    import traceback
    details = traceback.format_exc()
    print(details, flush=True)
    args.output.with_suffix('.error.json').write_text(json.dumps({
        'error_type': type(error).__name__, 'message': str(error), 'traceback': details
    }, indent=2) + '\n')
    raise
finally:
    launcher.app.close()
