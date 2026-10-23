"""Nav单一运行入口：10Hz命令、50Hz冻结WBC、200Hz MuJoCo。

python play.py --device cuda --velocity .3 0 0
python play.py --headless --video --velocity .2 0 .3
"""
import argparse
from datetime import datetime
import importlib.metadata
import json
from pathlib import Path
import time

import mujoco
import numpy as np
import torch

from bridge import C, CONTRACT, DECIMATION, EFFORT, ROOT, NavBridge, build_model, load_actor, sha


def configure_torch(device):
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    return ('cuda' if torch.cuda.is_available() else 'cpu') if device=='auto' else device


def observe_hold(sim, actor, device, *, viewer=None, seconds=None, output=None, goal_observer=None,
                 checks_observer=None,ee_command_provider=None,recorder=None):
    """回合后继续真实物理与零速WBC；窗口模式运行至关闭，也可有限时长测试。"""
    if seconds is None and viewer is None:
        raise ValueError('Unlimited observation requires a viewer')
    start, wall_start, step = float(sim.data.time), time.perf_counter(), 0
    report = dict(simulated_seconds=0., physics_steps=0, goal_hold_lost=False,
                  first_goal_hold_loss_time=None, final_goal_hold_ready=None,
                  max_planar_speed_m_s=0., max_yaw_rate_rad_s=0., max_tilt_rad=0., failures=[])
    was_ready = bool(goal_observer()) if goal_observer else False
    was_body_stable = False
    log = (Path(output)/'hold_observation.jsonl').open('w',encoding='utf-8') if output else None
    print('继续运行物理与零速保持；相机可自由拖动，关闭窗口退出。',flush=True)
    try:
        while seconds is None or sim.data.time-start < seconds-1e-8:
            if viewer is not None and not viewer.is_running():
                break
            if sim.physics_steps % sim.profile.navigation_decimation == 0:
                ee_command = ee_command_provider() if ee_command_provider else sim.ee_command.copy()
                sim.set_wbc_command((0.,0.,0.), ee_command)
            if sim.physics_steps % DECIMATION == 0:
                observation = sim.observation()
                if sim.policy_active:
                    with torch.inference_mode():
                        action = actor(torch.as_tensor(observation,device=device)[None]).cpu().numpy()[0]
                    sim.set_action(action)
            sim.physics_step()
            if recorder is not None:
                recorder.capture(sim.data, viewer.cam if viewer is not None else None)
            velocity, tilt = sim.velocity(), sim.state()[3]
            ready = bool(goal_observer()) if goal_observer else None
            checks = checks_observer() if checks_observer else None
            body_stable = (all(value for name,value in checks.items()
                               if name not in ('position','yaw','arm_position','arm_orientation','arm_joints',
                                               'zero_command_phase')) if checks else None)
            if checks is not None:
                report.update(final_checks=checks,final_body_stable=body_stable,
                              final_arm_pose_within_tolerance=bool(checks.get('arm_joints',True)
                                                                  and checks.get('arm_position',True)
                                                                  and checks.get('arm_orientation',True)),
                              final_goal_pose_within_tolerance=checks['position'] and checks['yaw'])
                report.setdefault('body_stability_lost',False)
                if was_body_stable and not body_stable:
                    report['body_stability_lost'] = True
                was_body_stable = was_body_stable or body_stable
            if ready is not None:
                if was_ready and not ready:
                    report['goal_hold_lost'] = True
                    if report['first_goal_hold_loss_time'] is None:
                        report['first_goal_hold_loss_time'] = float(sim.data.time)
                        report['first_goal_hold_loss_checks'] = checks
                        report['first_goal_hold_loss_state'] = dict(
                            root_position=sim.data.qpos[:3].tolist(),yaw_rad=sim.state()[2],
                            velocity=velocity.tolist(),tilt_rad=tilt,
                            arm_q=sim.data.qpos[sim.qids[12:]].tolist(),
                            arm_qd=sim.data.qvel[sim.dids[12:]].tolist())
                was_ready = was_ready or ready
            failure = sim.failure()
            if failure and failure not in report['failures']:
                report['failures'].append(failure)
            report.update(simulated_seconds=float(sim.data.time)-start,physics_steps=step+1,
                          final_goal_hold_ready=ready,
                          max_planar_speed_m_s=max(report['max_planar_speed_m_s'],float(np.linalg.norm(velocity[:2]))),
                          max_yaw_rate_rad_s=max(report['max_yaw_rate_rad_s'],abs(float(velocity[2]))),
                          max_tilt_rad=max(report['max_tilt_rad'],tilt))
            if step % C['HIGH_LEVEL_DECIMATION'] == 0 and log is not None:
                log.write(json.dumps(dict(time=float(sim.data.time),root_position=sim.data.qpos[:3].tolist(),
                                          velocity=velocity.tolist(),tilt_rad=tilt,yaw_rad=sim.state()[2],
                                          arm_q=sim.data.qpos[sim.qids[12:]].tolist(),
                                          arm_qd=sim.data.qvel[sim.dids[12:]].tolist(),goal_hold_ready=ready,
                                          body_stable=body_stable,checks=checks,
                                          ee_pose=sim.ee_pose().tolist(),ee_command=sim.ee_command.tolist()))+'\n')
            if step % 200 == 0:
                print(f'hold t={sim.data.time:.1f}s speed={np.linalg.norm(velocity[:2]):.3f}m/s '
                      f'wz={velocity[2]:.3f}rad/s body_stable={body_stable} goal_ready={ready}',flush=True)
                if output:
                    (Path(output)/'hold_observation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                if log is not None:
                    log.flush()
            if viewer is not None:
                if step % 8 == 0:
                    viewer.sync()
                remaining = (step+1)*C['PHYSICS_DT']-(time.perf_counter()-wall_start)
                if remaining>0:
                    time.sleep(remaining)
            step += 1
    finally:
        if log is not None:
            log.close()
        if output:
            (Path(output)/'hold_observation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def tracking_result(sim, samples, velocity, warmup, duration):
    """功能判定与电机诊断分开：按稳态样本的平均速度误差判断跟踪。

    默认跳过命令开始后的2秒；每轴线速度误差≤0.15m/s，yaw误差≤0.20rad/s。
    同时报告逐步RMSE、末端误差，不用平均数掩盖振荡或负荷问题。
    """
    steady = [sample for sample in samples if sample['time']>=warmup+2.-1e-8]
    if not steady:
        return dict(passed=False, reason='insufficient_tracking_samples')
    measured = np.array([sample['velocity'] for sample in steady])
    requested = np.array([sample['command'] for sample in steady])
    mean_error = abs((measured-requested).mean(axis=0))
    rmse = np.sqrt(((measured-requested)**2).mean(axis=0))
    ee_errors = np.array([sample['ee_error'] for sample in steady])
    survived = sim.data.time>=duration-1e-8 and not sim.failure()
    tracking = bool(np.all(mean_error<=np.array([.15,.15,.20])))
    return dict(passed=survived and tracking, reason=(sim.failure() or
                ('velocity_tracking_error' if not tracking else 'velocity_tracking_passed')),
                survived=survived, steady_samples=len(steady),
                requested_velocity=list(velocity), mean_velocity=measured.mean(axis=0).tolist(),
                mean_error=mean_error.tolist(), rmse=rmse.tolist(),
                mean_ee_position_error_m=ee_errors.mean(axis=0).tolist(),
                ee_position_error_norm_p95_m=float(np.percentile(np.linalg.norm(ee_errors,axis=1),95)))


def run_episode(actor, device, *, velocity=(.3,0.,0.), ee_position=None, duration=10.,
                warmup=2., seed=42001, delay_ms=None, friction=.6, added_mass=0.,
                output=None, headless=True, video=False, summary_only=False,
                keep_window=False, arm_zero=True, policy_path=None, observe_seconds=None):
    """验证和交互复用同一真实动力学循环；没有假输出或强制移动机器人。"""
    if arm_zero and ee_position is not None:
        raise ValueError('arm_zero cannot be combined with an explicit EE target')
    ee_position = C['EE_NOMINAL'] if ee_position is None else ee_position
    model, spec = build_model(friction, added_mass)
    sim = NavBridge(model, seed, delay_ms, arm_zero=arm_zero)
    # 在写输出、打开窗口前检查用户命令，然后恢复初始命令状态。
    sim.set_command(velocity, ee_position)
    sim.base_command[:] = 0.
    sim.ee_command[:] = np.r_[C['EE_NOMINAL'],C['EE_QUATERNION_WXYZ']]
    samples, trace = [], []
    viewer = renderer = writer = None
    camera = mujoco.MjvCamera()
    camera.distance, camera.azimuth, camera.elevation = 3.4, 135., -22.
    camera.lookat[:] = [0.,0.,.35]
    began = time.perf_counter()
    aborted = False
    try:
        if output is not None:
            output = Path(output)
            output.mkdir(parents=True, exist_ok=False)
            if not summary_only:
                (output/'model.xml').write_text(spec.to_xml(), encoding='utf-8')
        if not headless:
            from mujoco import viewer as mujoco_viewer
            viewer = mujoco_viewer.launch_passive(model, sim.data)
            viewer.cam.lookat[:], viewer.cam.distance = camera.lookat, camera.distance
            viewer.cam.azimuth, viewer.cam.elevation = camera.azimuth, camera.elevation
        if video:
            import imageio.v2 as imageio
            renderer = mujoco.Renderer(model, height=540, width=960)
            writer = imageio.get_writer(output/'nav.mp4', fps=25, codec='libx264', macro_block_size=2)
        for step in range(round(duration/C['PHYSICS_DT'])):
            if viewer is not None and not viewer.is_running():
                aborted = True
                break
            if step%C['HIGH_LEVEL_DECIMATION']==0:
                desired = velocity if sim.data.time>=warmup-1e-8 else (0.,0.,0.)
                sim.set_command(desired, ee_position)
            if step%DECIMATION==0:
                observation = sim.observation()
                with torch.inference_mode():
                    action = actor(torch.as_tensor(observation, device=device)[None]).cpu().numpy()[0]
                sim.set_action(action)
            sim.physics_step()
            if not summary_only:
                trace.append(np.r_[sim.data.time,sim.data.qpos[:7],sim.data.qvel[:6],
                                   sim.data.qpos[sim.qids],sim.data.qvel[sim.dids],
                                   sim.targets,sim.raw_torque,sim.torque])
            if (step+1)%DECIMATION==0:
                samples.append(dict(time=float(sim.data.time), velocity=sim.velocity().tolist(),
                                    command=sim.base_command.copy().tolist(),
                                    arm_position=sim.data.qpos[sim.qids[12:]].copy().tolist(),
                                    ee_error=(sim.ee_position()-sim.ee_command[:3]).tolist()))
            if step%8==0:
                camera.lookat[:2] = sim.data.qpos[:2]
                if writer is not None:
                    renderer.update_scene(sim.data,camera=camera)
                    writer.append_data(renderer.render())
                if viewer is not None:
                    viewer.sync()
            if viewer is not None:
                remaining = (step+1)*C['PHYSICS_DT']-(time.perf_counter()-began)
                if remaining>0:
                    time.sleep(remaining)
            if sim.failure():
                break
        result = tracking_result(sim, samples, velocity, warmup, duration)
        if aborted:
            result.update(passed=False, reason='viewer_closed')
        result.update(seed=seed, seconds=float(sim.data.time), warmup_seconds=warmup,
                      arm_control_mode='zero_pd' if arm_zero else 'policy',
                      ee_tracking_enabled=not arm_zero,
                      ee_target=None if arm_zero else list(ee_position),
                      friction=friction, added_mass_kg=added_mass,
                      actuator_delays_physics_steps=sim.delays.tolist(),
                      root_position=sim.data.qpos[:3].tolist(), yaw_rad=sim.state()[2],
                      final_tilt_rad=sim.state()[3], policy_ticks=sim.policy_ticks,
                      physics_steps=sim.physics_steps, peak_torque_nm=sim.peak_torque.tolist(),
                      torque_saturation_steps=sim.saturation_steps.tolist(),
                      peak_joint_speed_rad_s=sim.peak_speed.tolist(),
                      speed_exceeded_steps=sim.speed_exceeded_steps.tolist(),
                      angle_violation_rad=sim.angle_violation.tolist(),
                      robot_mass_kg=float(model.body_mass.sum()), wall_seconds=time.perf_counter()-began)
        if arm_zero:
            steady_arm = np.array([s['arm_position'] for s in samples if s['time']>=warmup+2.-1e-8])
            result.update(arm_target_rad=[0.]*6,
                          final_arm_position_rad=sim.data.qpos[sim.qids[12:]].tolist(),
                          steady_arm_abs_error_max_rad=(abs(steady_arm).max(axis=0).tolist()
                                                       if steady_arm.size else None))
            # 本模式不执行末端跟踪，不能把末端误差解释为控制验收指标。
            result['mean_ee_position_error_m'] = None
            result['ee_position_error_norm_p95_m'] = None
        if output is not None:
            report = dict(status='complete', task_scope=CONTRACT['scope'], formal_acceptance=False,
                          actor_sha256=sha(policy_path or ROOT/'policy/actor.pt'), inference_device=device,
                          physics_device='CPU', source_sha256={p.name:sha(p) for p in ROOT.glob('*.py')},
                          versions={name:importlib.metadata.version(name) for name in ('torch','numpy','mujoco')},
                          differences=CONTRACT['differences'], episode=result)
            (output/'report.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8')
            if not summary_only:
                # columns说明随数据保存，避免靠猜测切片。
                np.savez_compressed(output/'trace.npz', physics=np.array(trace),
                                    columns='time[1],root_pose[7],root_velocity[6],q[18],qd[18],target[18],raw_torque[18],torque[18]',
                                    sample_time=np.array([s['time'] for s in samples]),
                                    velocity=np.array([s['velocity'] for s in samples]),
                                    command=np.array([s['command'] for s in samples]),
                                    ee_error=np.array([s['ee_error'] for s in samples]))
        if (keep_window and viewer is not None) or observe_seconds is not None:
            if writer is not None:
                writer.close(); writer = None
            if renderer is not None:
                renderer.close(); renderer = None
            observe_hold(sim,actor,device,viewer=viewer,seconds=observe_seconds,output=output)
        return result
    finally:
        if writer is not None:
            writer.close()
        if renderer is not None:
            renderer.close()
        if viewer is not None:
            viewer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',default='cuda')
    parser.add_argument('--policy',type=Path)
    parser.add_argument('--observe-seconds',type=float,help='Finite post-episode zero-speed observation; window otherwise runs until closed')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--video',action='store_true')
    parser.add_argument('--velocity',type=float,nargs=3,default=(.3,0.,0.),metavar=('VX','VY','WZ'))
    arm_options = parser.add_mutually_exclusive_group()
    arm_options.add_argument('--ee',type=float,nargs=3,metavar=('X','Y','Z'))
    arm_options.add_argument('--arm-zero',action='store_true',
                             help='Hold six arm joint targets at zero through the existing delayed PD')
    parser.add_argument('--seconds',type=float,default=10.)
    parser.add_argument('--warmup',type=float,default=2.)
    parser.add_argument('--seed',type=int,default=42001)
    parser.add_argument('--delay-ms',type=int,choices=(0,5,10,15,20))
    parser.add_argument('--friction',type=float,default=.6)
    parser.add_argument('--added-mass',type=float,default=0.)
    parser.add_argument('--summary-only',action='store_true')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.observe_seconds is not None and (not np.isfinite(args.observe_seconds) or args.observe_seconds<=0):
        parser.error('observe-seconds must be finite and positive')
    if args.warmup<0 or args.seconds<=args.warmup+2.1 or args.friction<=0 or args.added_mass<0:
        parser.error('seconds must exceed warmup+2.1; warmup/mass>=0 and friction>0')
    device = configure_torch(args.device)
    output = args.output or ROOT/'outputs'/datetime.now().strftime('play-%Y%m%d-%H%M%S-%f')
    print('Output:',output.resolve(),flush=True)
    result = run_episode(load_actor(device,args.policy),device,velocity=args.velocity,ee_position=args.ee,
                         duration=args.seconds,warmup=args.warmup,seed=args.seed,
                         delay_ms=args.delay_ms,friction=args.friction,added_mass=args.added_mass,
                         output=output,headless=args.headless,video=args.video,
                         summary_only=args.summary_only,keep_window=True,arm_zero=args.ee is None,
                         policy_path=args.policy,observe_seconds=args.observe_seconds)
    print(json.dumps(result),flush=True)
    return 0 if result['passed'] else 2


if __name__=='__main__':
    raise SystemExit(main())
