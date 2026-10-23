"""平地目标导航技能：世界坐标目标(x,y,yaw) → 机体系速度 → 原WBC。

python navigate.py --goal 1 0 --yaw-deg 90
仅使用仿真真值定位，不包含地图规划或避障。默认CUDA推理，机械臂六关节零位PD保持。
"""
import argparse
from dataclasses import asdict, replace
from datetime import datetime
import json
from pathlib import Path
import time

import mujoco
import numpy as np
import torch

from bridge import C, DECIMATION, ROOT, NavBridge, build_model, load_actor, sha
from play import configure_torch, observe_hold
from control_profiles import PROFILES, get_profile
from arm_control import ee_feedback_command
from navigation import (NavConfig, NavState, NavSkill, profile_nav_config,
                        wrap_angle, pose_error, effective_velocity)


def read_state(sim):
    """定位适配层：目前读取MuJoCo真值；实机时替换为定位/状态估计。"""
    _, _, yaw, tilt = sim.state()
    return NavState(float(sim.data.time), sim.data.qpos[:2].copy(), yaw, sim.velocity(),
                    sim.data.qpos[sim.qids[12:]].copy(),
                    sim.data.qvel[sim.dids[12:]].copy(), tilt, sim.ee_pose())


def run_navigation(actor, device, goal_xy, goal_yaw, *, config=None, seed=42001,
                   friction=.6, added_mass=0., delay_ms=None, output=None,
                   headless=True, keep_window=False, policy_path=None, observe_seconds=None,
                   control_profile='skills',ee_pose_target=None,arm_zero=True,video=False):
    """执行层：skills导航与Actor均50Hz、物理200Hz；isaac导航反馈10Hz。"""
    if arm_zero and ee_pose_target is not None:
        raise ValueError('arm_zero cannot be combined with an explicit EE target')
    skill = NavSkill(goal_xy, goal_yaw, profile_nav_config(control_profile,config),arm_zero=arm_zero)
    cfg = skill.config
    _, spec = build_model(friction, added_mass, control_profile=control_profile)
    # 目标圆及朝向线只显示，不参与碰撞。
    spec.worldbody.add_geom(name='nav_goal', type=mujoco.mjtGeom.mjGEOM_CYLINDER,
                            pos=[*skill.goal, .003], size=[cfg.position_tolerance, .002, 0.],
                            contype=0, conaffinity=0, rgba=[.1, .85, .2, .5])
    endpoint = skill.goal + .3*np.array([np.cos(goal_yaw), np.sin(goal_yaw)])
    spec.worldbody.add_geom(name='nav_heading', type=mujoco.mjtGeom.mjGEOM_CAPSULE,
                            fromto=[*skill.goal, .015, *endpoint, .015], size=[.012, 0., 0.],
                            contype=0, conaffinity=0, rgba=[1., .8, 0., 1.])
    sim = NavBridge(spec.compile(), seed, delay_ms, arm_zero=arm_zero,control_profile=control_profile)
    arm_pose_target = np.array(ee_pose_target if ee_pose_target is not None else sim.profile.safe_ee_pose,
                               dtype=float)
    if arm_zero:
        arm_pose_target = sim.zero_arm_ee_pose()
    if (arm_pose_target.shape != (7,) or not np.isfinite(arm_pose_target).all()
            or np.linalg.norm(arm_pose_target[3:]) < 1e-8):
        raise ValueError('EE target must be finite XYZ+wxyz')
    arm_pose_target[3:] /= np.linalg.norm(arm_pose_target[3:])
    skill.arm_pose_target = arm_pose_target.copy()
    print('Safe EE command (XYZ+wxyz):',arm_pose_target.tolist(),flush=True)
    output = Path(output) if output is not None else None
    if output is not None:
        output.mkdir(parents=True, exist_ok=False)
        (output/'model.xml').write_text(spec.to_xml(), encoding='utf-8')
    rows, physics, events, ee_poses, ee_commands = [], [], [], [], []
    viewer = None
    recorder = None
    reason, previous_phase = 'timeout', None
    began = time.perf_counter()
    try:
        if video:
            from video import VideoRecorder
            if output is None:
                raise ValueError('Video requires an output directory')
            recorder = VideoRecorder(sim.model, output/'nav.mp4')
        if not headless:
            from mujoco import viewer as mj_viewer
            viewer = mj_viewer.launch_passive(sim.model, sim.data)
            viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 4., 130., -35.
            viewer.cam.lookat[:] = [*sim.data.qpos[:2], .3]
        for step in range(round(cfg.timeout_seconds/C['PHYSICS_DT'])):
            if viewer is not None and not viewer.is_running():
                reason = 'viewer_closed'
                break
            if step % sim.profile.navigation_decimation == 0:
                state = read_state(sim)
                command = skill.update(state)
                ee_command = (ee_feedback_command(state.ee_pose,arm_pose_target,
                              cfg.ee_feedback_gain,cfg.ee_feedback_limit)
                              if not arm_zero and state.time >= cfg.warmup_seconds else arm_pose_target)
                sim.set_wbc_command(command, ee_command)
                rows.append([state.time, *state.xy, state.yaw, *state.velocity,
                             *command, skill.distance, skill.yaw_error, skill.hold_elapsed])
                if skill.phase != previous_phase:
                    events.append(dict(time=state.time, phase=skill.phase))
                    print(f't={state.time:.1f}s {skill.phase} distance={skill.distance:.3f}m '
                          f'yaw_error={np.rad2deg(skill.yaw_error):.1f}deg', flush=True)
                    previous_phase = skill.phase
            if skill.arrived:
                reason = 'arrived'
                break
            if step % DECIMATION == 0:
                observation = sim.observation()
                if sim.policy_active:
                    with torch.inference_mode():
                        action = actor(torch.as_tensor(observation, device=device)[None]).cpu().numpy()[0]
                    sim.set_action(action)
            sim.physics_step()
            if recorder is not None:
                recorder.capture(sim.data, viewer.cam if viewer is not None else None)
            state = read_state(sim)
            ee_poses.append(state.ee_pose.copy())
            ee_commands.append(sim.ee_command.copy())
            physics.append(np.r_[state.time, state.xy, state.yaw, state.velocity, state.tilt,
                                 sim.data.qpos[sim.qids], sim.data.qvel[sim.dids],
                                 sim.targets, sim.torque])
            if sim.failure():
                reason = sim.failure()
                break
            skill.observe(state)
            if skill.arrived:
                reason = 'arrived'
                events.append(dict(time=state.time, phase='arrived'))
                print(f't={state.time:.2f}s arrived (stable for {skill.hold_elapsed:.2f}s)',flush=True)
                break
            if viewer is not None:
                if step % 8 == 0:
                    viewer.sync()
                remaining = (step+1)*C['PHYSICS_DT']-(time.perf_counter()-began)
                if remaining > 0:
                    time.sleep(remaining)
        final = read_state(sim)
        result = dict(arrived=reason == 'arrived', reason=reason, seconds=final.time,
                      survived=not bool(sim.failure()),
                      goal_xy=skill.goal.tolist(), goal_yaw_rad=skill.goal_yaw,
                      final_xy=final.xy.tolist(), final_yaw_rad=final.yaw,
                      position_error_m=float(np.linalg.norm(skill.goal-final.xy)),
                      yaw_error_rad=wrap_angle(skill.goal_yaw-final.yaw),
                      final_velocity=final.velocity.tolist(), final_tilt_rad=final.tilt,
                      arm_target_ee_pose=arm_pose_target.tolist(),
                      arm_control_mode='zero_pd' if arm_zero else 'wbc_safe_ee_pose',
                      arm_target_rad=[0.]*6 if arm_zero else None,
                      arm_joint_error_max_rad=float(np.max(abs(final.arm_q))) if arm_zero else None,
                      final_ee_pose=final.ee_pose.tolist(),
                      ee_position_error_m=pose_error(final.ee_pose,arm_pose_target)[0],
                      ee_orientation_error_rad=pose_error(final.ee_pose,arm_pose_target)[1],
                      final_checks=skill.stability_checks(final),
                      final_arm_q_rad=final.arm_q.tolist(),
                      final_arm_qd_rad_s=final.arm_qd.tolist(),
                      stable_hold_seconds=skill.hold_elapsed,
                      handoff_ready=reason == 'arrived',
                      peak_torque_nm=sim.peak_torque.tolist(),
                      torque_saturation_steps=sim.saturation_steps.tolist(),
                      peak_joint_speed_rad_s=sim.peak_speed.tolist(),
                      speed_exceeded_steps=sim.speed_exceeded_steps.tolist(),
                      angle_violation_rad=sim.angle_violation.tolist())
        if output is not None:
            report = dict(episode=result, config=asdict(cfg), events=events,
                          inference_device=device, physics_device='CPU',
                          localization='MuJoCo ground truth', arm_control_mode=result['arm_control_mode'],
                          control_profile=control_profile, actuator_settings=asdict(sim.profile),
                          arm_bias_compensation=bool(arm_zero),
                          action_history='executed joint target residuals' if arm_zero else 'policy actions',
                          robot_mass_kg=float(np.sum(sim.model.body_mass)),
                          ee_target_outside_push_xyz_bounds=bool(np.any(abs(
                              (arm_pose_target[:3]-C['EE_NOMINAL'])/np.asarray(C['EE_OFFSET_SCALE'])) > 1.)),
                          seed=seed, friction=friction, added_mass_kg=added_mass,
                          actuator_delays_physics_steps=sim.delays.tolist(),
                          actor_path=str(Path(policy_path or ROOT/'policy/actor.pt').resolve()),
                          actor_sha256=sha(policy_path or ROOT/'policy/actor.pt'),
                          source_sha256={name:sha(ROOT/name) for name in
                                         ('navigate.py','bridge.py','play.py','control_profiles.py','arm_control.py')},
                          formal_acceptance=False)
            (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
            np.savez_compressed(output/'trace.npz', navigation=np.array(rows), physics=np.array(physics),
                                ee_pose=np.array(ee_poses), ee_command=np.array(ee_commands),
                                ee_pose_target=arm_pose_target,
                                navigation_columns='time,world_x,world_y,yaw,body_vx,body_vy,world_wz,cmd_vx,cmd_vy,cmd_wz,distance,yaw_error,hold_seconds',
                                physics_columns='time[1],world_xy[2],yaw[1],velocity[3],tilt[1],q[18],qd[18],target[18],torque[18]')
        print(json.dumps(result), flush=True)
        if (keep_window and viewer is not None) or observe_seconds is not None:
            # 到达后只观察零速保持，不重新追点，以免掩盖保持失败。
            skill.phase = 'settle'
            def observe_goal():
                skill.observe(read_state(sim))
                return skill.arrived
            observe_hold(sim,actor,device,viewer=viewer,seconds=observe_seconds,
                         output=output,goal_observer=observe_goal,recorder=recorder,
                         checks_observer=lambda:skill.stability_checks(read_state(sim)),
                         ee_command_provider=lambda:ee_feedback_command(sim.ee_pose(),arm_pose_target,
                             cfg.ee_feedback_gain,cfg.ee_feedback_limit) if not arm_zero else arm_pose_target.copy())
        return result
    finally:
        if recorder is not None:
            recorder.close()
        if viewer is not None:
            viewer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goal', type=float, nargs=2, required=True, metavar=('X','Y'))
    parser.add_argument('--yaw-deg', type=float, default=0., help='World yaw in degrees, counterclockwise positive')
    parser.add_argument('--max-speed', type=float, help='Override profile maximum forward speed')
    parser.add_argument('--min-speed', type=float, help='Override profile minimum forward speed')
    parser.add_argument('--min-lateral-speed', type=float, help='Override minimum sideways command in m/s')
    parser.add_argument('--min-yaw-rate', type=float, help='Override minimum turning command in rad/s')
    parser.add_argument('--position-tolerance', type=float, help='Override profile position tolerance in meters')
    parser.add_argument('--yaw-tolerance-deg', type=float, help='Override profile yaw tolerance in degrees')
    parser.add_argument('--ee-pose',type=float,nargs=7,help='Optional fixed EE XYZ+wxyz command')
    parser.add_argument('--arm-zero',action='store_true',default=True,help='Hold six arm joint targets at zero using PD, overriding arm policy actions')
    parser.add_argument('--timeout', type=float, default=60.)
    parser.add_argument('--device', default='cuda')
    parser.add_argument('--video',action='store_true',help='Record episode and continued hold to MP4')
    parser.add_argument('--policy', type=Path, help='Optional TorchScript with the same observation/action contract')
    parser.add_argument('--control-profile',choices=tuple(PROFILES),default='skills',
                        help='Actuator settings only; robot mass/inertia/geometry/limits stay unchanged')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--observe-seconds',type=float,help='Finite post-episode hold observation; window otherwise runs until closed')
    parser.add_argument('--seed', type=int, default=42001)
    parser.add_argument('--friction', type=float, default=.6)
    parser.add_argument('--added-mass', type=float, default=0.)
    parser.add_argument('--delay-ms', type=int, choices=(0,5,10,15,20))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.observe_seconds is not None and (not np.isfinite(args.observe_seconds) or args.observe_seconds<=0):
        parser.error('observe-seconds must be finite and positive')
    overrides = dict(timeout_seconds=args.timeout)
    for name in ('max_speed','min_speed','min_lateral_speed','min_yaw_rate','position_tolerance'):
        if getattr(args,name) is not None:
            overrides[name] = getattr(args,name)
    if args.yaw_tolerance_deg is not None:
        overrides['yaw_tolerance'] = np.deg2rad(args.yaw_tolerance_deg)
    cfg = replace(profile_nav_config(args.control_profile),**overrides)
    if not np.isfinite([*args.goal,args.yaw_deg,args.friction,args.added_mass]).all() or args.friction<=0 or args.added_mass<0:
        parser.error('Goal/parameters must be finite; friction>0 and added-mass>=0')
    device = configure_torch(args.device)
    output = args.output or ROOT/'outputs'/datetime.now().strftime('navigate-%Y%m%d-%H%M%S-%f')
    print('Output:',output.resolve(),flush=True)
    result = run_navigation(load_actor(device,args.policy), device, args.goal, np.deg2rad(args.yaw_deg),
                            config=cfg, seed=args.seed, friction=args.friction,
                            added_mass=args.added_mass, delay_ms=args.delay_ms,
                            output=output, headless=args.headless, keep_window=True,policy_path=args.policy,
                            observe_seconds=args.observe_seconds,control_profile=args.control_profile,
                            ee_pose_target=args.ee_pose,arm_zero=args.ee_pose is None,video=args.video)
    return 0 if result['arrived'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
