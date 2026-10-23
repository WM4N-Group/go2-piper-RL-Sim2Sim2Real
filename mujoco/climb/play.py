"""独立MuJoCo运行V1/900。Windows默认窗口；服务器用--headless --video。"""
import argparse
from datetime import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent


def observe_after_episode(sim, actor, device, cfg, stop, *, viewer=None, seconds=None, output=None, observation=None, recorder=None):
    """继续原控制器和物理，不冻结qpos；记录停止保持是否丢失。"""
    import numpy as np
    import torch
    if seconds is None and viewer is None:
        raise ValueError('Unlimited observation requires a viewer')
    started, wall_start, tick = float(sim.data.time), time.perf_counter(), 0
    summary = dict(simulated_seconds=0., physics_steps=0, max_linear_speed_m_s=0.,
                   max_angular_speed_rad_s=0., max_tilt_rad=0., stop_hold_lost=False,
                   first_stop_hold_loss_time=None,
                   controller='stop' if stop is not None else 'original_ascent')
    log = (Path(output)/'hold_observation.jsonl').open('w',encoding='utf-8') if output else None
    obs = sim.observation() if observation is None else observation
    print('继续真实物理与当前控制器；相机可拖动，关闭窗口退出。',flush=True)
    try:
        while seconds is None or sim.data.time-started < seconds-1e-8:
            if viewer is not None and not viewer.is_running():
                break
            with torch.inference_mode():
                action = actor(torch.from_numpy(obs).unsqueeze(0).to(device)).cpu().numpy()[0]
            sim.set_action(action)
            for _ in range(cfg['decimation']):
                command = stop.command(sim.policy_command()) if stop is not None else None
                sim.physics_step(command)
                if recorder is not None:
                    recorder.capture(sim.data, viewer.cam if viewer is not None else None)
                if stop is not None:
                    stop.after_step()
                    if stop.failure:
                        summary['stop_hold_lost'] = True
                        if summary['first_stop_hold_loss_time'] is None:
                            summary['first_stop_hold_loss_time'] = float(sim.data.time)
                summary['physics_steps'] += 1
                summary['max_linear_speed_m_s'] = max(summary['max_linear_speed_m_s'],float(np.linalg.norm(sim.data.qvel[:3])))
                summary['max_angular_speed_rad_s'] = max(summary['max_angular_speed_rad_s'],float(np.linalg.norm(sim.data.qvel[3:6])))
                summary['max_tilt_rad'] = max(summary['max_tilt_rad'],sim.state()[3])
            summary['simulated_seconds'] = float(sim.data.time)-started
            obs = sim.observation()
            if log is not None:
                log.write(json.dumps(dict(time=float(sim.data.time),root_position=sim.data.qpos[:3].tolist(),
                                          root_velocity=sim.data.qvel[:6].tolist(),
                                          stop_phase=stop.phase if stop is not None else 'ascent',
                                          stop_failure=stop.failure if stop is not None else None))+'\n')
            if tick % 50 == 0:
                print(f'hold t={sim.data.time:.1f}s x={sim.data.qpos[0]:.3f} '
                      f'speed={np.linalg.norm(sim.data.qvel[:3]):.3f}m/s '
                      f'phase={stop.phase if stop is not None else "ascent"}',flush=True)
                if output:
                    (Path(output)/'hold_observation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
                if log is not None:
                    log.flush()
            if viewer is not None:
                viewer.sync()
                remaining = (tick+1)*sim.dt-(time.perf_counter()-wall_start)
                if remaining>0:
                    time.sleep(remaining)
            tick += 1
    finally:
        if log is not None:
            log.close()
        if stop is not None:
            summary['stop'] = stop.report()
        if output:
            (Path(output)/'hold_observation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--box-height','--height', type=float, default=.20,
                        help='障碍物高度，单位米，范围[0,0.20]；0为平地基线，默认0.20')
    parser.add_argument('--seed', type=int, default=42001)
    parser.add_argument('--episodes', type=int, default=1)
    parser.add_argument('--device', default='cuda', help='默认自动选择CUDA；MuJoCo物理始终CPU')
    parser.add_argument('--randomize', action='store_true', help='启用训练范围质量/摩擦/腿PD随机化')
    parser.add_argument('--steps', type=int, help='调试控制步上限；截断不算失败或成功')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--observe-seconds',type=float,help='有限时长的回合后物理观察；默认窗口持续运行至关闭')
    parser.add_argument('--finish-mode', choices=('ascent', 'stop'), default='stop',
                        help='ascent原登台；stop登台后制动并持续站稳')
    parser.add_argument('--friction', type=float, help='显式指定地面/机器人滑动摩擦')
    parser.add_argument('--added-mass', type=float, help='机身附加质量kg')
    parser.add_argument('--delay-ms', type=float, choices=(0., 10., 20.), help='所有执行器固定命令延迟')
    parser.add_argument('--summary-only', action='store_true', help='批量验证只保存结果，不保存逐步轨迹/模型')
    args = parser.parse_args()
    if not 0 <= args.box_height <= .20 or args.episodes<1 or (args.steps is not None and args.steps<1):
        parser.error('高度须在[0,0.20]米，回合与steps为正整数')
    if args.friction is not None and args.friction<=0 or args.added_mass is not None and args.added_mass<0:
        parser.error('摩擦须为正数，附加质量不能为负数')
    if args.headless and sys.platform.startswith('linux'):
        os.environ.setdefault('MUJOCO_GL', 'egl')
    import numpy as np
    import torch
    import mujoco
    if args.observe_seconds is not None and (not np.isfinite(args.observe_seconds) or args.observe_seconds<=0):
        parser.error('observe-seconds must be finite and positive')
    from bridge import ClimbBridge, build_model, load_contract, robot_directory, ROOT as SOURCE_ROOT, sha
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if args.device == 'auto':
        args.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    contract = load_contract()
    cfg = contract['configuration']['task']
    actor = torch.jit.load(str(ROOT/'policy/actor.pt'), map_location=args.device).eval()
    output = args.output or ROOT/'outputs'/datetime.now().strftime('play-%Y%m%d-%H%M%S-%f')
    output = output.resolve(); output.mkdir(parents=True, exist_ok=False)
    print(f'Output: {output}', flush=True)
    report = dict(status='running', formal_acceptance=False, version='V1', iteration=900,
                  checkpoint_sha256=contract['checkpoint_sha256'], actor_sha256=contract['actor_sha256'],
                  requested_episodes=args.episodes, box_height=args.box_height, seed=args.seed,
                  randomization=args.randomize, inference_device=args.device, physics_device='CPU',
                  inference_hardware=torch.cuda.get_device_name(args.device) if str(args.device).startswith('cuda') else 'CPU',
                  source_sha256={p.name: sha(p) for p in ROOT.glob('*.py')},
                  robot_sha256={str(p.relative_to(robot_directory())): sha(p) for p in robot_directory().rglob('*') if p.is_file()},
                  versions={n: importlib.metadata.version(n) for n in ('mujoco', 'torch', 'numpy')},
                  task_scope='Original V1 ascent' if args.finish_mode=='ascent' else 'V1 ascent with independent WBC stop',
                  finish_mode=args.finish_mode,
                  sensor_scope='Analytic oracle height map and exact box height; not camera perception',
                  differences=['MuJoCo contact solver differs from PhysX; single sliding friction approximates dynamic min-combine friction.',
                               'Nominal mass/friction/PD by default; --randomize samples within training ranges, not identical Isaac RNG.',
                               'Motor effort limits are enforced; velocity limits monitored, not a PhysX-equivalent solver hard constraint.',
                               'Stop mode uses simulation state and known platform; hardware state estimation not validated.'],
                  episodes=[])
    (output/'run.json').write_text(json.dumps(vars(args), default=str, indent=2)+'\n', encoding='utf-8')
    writer = renderer = viewer = None
    began = time.perf_counter()
    try:
        for episode in range(args.episodes):
            rng = np.random.default_rng(args.seed+episode)
            friction = min(.6, .75*rng.uniform(*cfg['friction_range'])) if args.randomize else .6
            mass = float(rng.uniform(*cfg['added_mass_range'])) if args.randomize else 0.
            if args.friction is not None: friction = args.friction
            if args.added_mass is not None: mass = args.added_mass
            model, spec = build_model(cfg, args.box_height, friction=friction, added_mass=mass)
            sim = ClimbBridge(model, cfg, args.box_height, args.seed+episode, args.randomize)
            if args.delay_ms is not None:
                sim.delays[:] = round(args.delay_ms/1000/cfg['physics_dt'])
            stop = None
            if args.finish_mode=='stop':
                from stop import StopController
                stop = StopController(sim)
            # 保存本回合实际加载模型，路径指向包内mesh。
            if not args.summary_only:
                (output/f'model_{episode:03d}.xml').write_text(spec.to_xml(), encoding='utf-8')
            recorder = None
            if args.video:
                from video import VideoRecorder
                recorder = VideoRecorder(model, output/f'climb_{episode:03d}.mp4')
                writer = recorder
            if not args.headless:
                import mujoco.viewer
                viewer = mujoco.viewer.launch_passive(model, sim.data)
                viewer.cam.distance = 3.4; viewer.cam.azimuth = 135.; viewer.cam.elevation = -22.
                viewer.cam.lookat[:] = [1.2, 0., .35]
            cam = mujoco.MjvCamera()
            cam.distance = 3.4; cam.azimuth = 135.; cam.elevation = -22.
            cam.lookat[:] = [1.2, 0., .35]
            state, reason = 'running', ''
            trace = {k: [] for k in ('time', 'root_pose', 'root_velocity', 'joint_position', 'joint_velocity', 'target', 'torque', 'raw_torque',
                                     'actuator_torque', 'foot_position', 'foot_force', 'stop_phase')}
            obs = sim.observation()
            start = time.perf_counter()
            for step in range(args.steps or round(cfg['episode_seconds']/sim.dt)):
                if viewer is not None and not viewer.is_running():
                    state, reason = 'incomplete', 'viewer_closed'; break
                with torch.inference_mode():
                    action = actor(torch.from_numpy(obs).unsqueeze(0).to(args.device)).cpu().numpy()[0]
                sim.set_action(action)
                for _ in range(cfg['decimation']):
                    command = stop.command(sim.policy_command()) if stop is not None else None
                    sim.physics_step(command)
                    if stop is not None: stop.after_step()
                    if not args.summary_only:
                        trace['time'].append(float(sim.data.time))
                        trace['root_pose'].append(sim.data.qpos[:7].copy())
                        trace['root_velocity'].append(sim.data.qvel[:6].copy())
                        trace['joint_position'].append(sim.data.qpos[sim.qids].copy())
                        trace['joint_velocity'].append(sim.data.qvel[sim.dids].copy())
                        trace['target'].append(sim.targets.copy())
                        trace['torque'].append(sim.applied_torque.copy())
                        trace['raw_torque'].append(sim.raw_torque.copy())
                        trace['actuator_torque'].append(sim.data.qfrc_actuator[sim.dids].copy())
                        trace['foot_position'].append(sim.data.xpos[sim.feet_ids].copy())
                        trace['foot_force'].append(sim.forces[sim.feet_ids].copy())
                        trace['stop_phase'].append(stop.phase if stop is not None else 'ascent')
                if not np.isfinite(sim.data.qpos).all() or not np.isfinite(sim.data.qvel).all():
                    raise FloatingPointError('Nonfinite simulation state')
                state, reason = sim.status()
                if stop is not None: state, reason = stop.status(state, reason)
                obs = sim.observation()
                if recorder is not None:
                    recorder.capture(sim.data, viewer.cam if viewer is not None else None)
                if viewer is not None:
                    viewer.sync()
                    remaining = (step+1)*sim.dt-(time.perf_counter()-start)
                    if remaining>0: time.sleep(remaining)
                if step%100==0: print(f'episode={episode} t={sim.elapsed:.2f}s x={sim.data.qpos[0]:.3f} top={sim.max_supported} ready={sim.ready}', flush=True)
                if state!='running': break
            if state=='running': state, reason = 'incomplete', 'debug_step_limit'
            if not args.summary_only:
                np.savez_compressed(output/f'trace_{episode:03d}.npz', **trace)
            record = dict(episode=episode, state=state, reason=reason, seconds=sim.elapsed,
                          seed=args.seed+episode, startup_ready=sim.ready,
                          startup_release_seconds=sim.release_time if sim.ready else None,
                          final_tilt_rad=sim.state()[3], final_yaw_rad=sim.state()[2],
                          final_arm_error_rad=float(abs(sim.data.qpos[sim.qids[12:]]-sim.reference[12:]).max()),
                          final_foot_positions=sim.data.xpos[sim.feet_ids].tolist(),
                          final_foot_forces=sim.forces[sim.feet_ids].tolist(),
                          final_top_contact_age_s=[float(v) if np.isfinite(v) else None for v in sim.top_age],
                          ascent_hold_seconds=sim.hold,
                          root_position=sim.data.qpos[:3].tolist(), max_root_x=sim.max_root_x,
                          max_supported_feet=sim.max_supported, ever_top_support=sim.ever_top.tolist(),
                          peak_arm_error_rad=sim.peak_arm_error, peak_torque_nm=sim.peak_torque.tolist(),
                          saturation_physics_steps=sim.saturation_count.tolist(),
                          peak_joint_speed_rad_s=sim.peak_speed.tolist(),
                          speed_exceeded_physics_steps=sim.speed_exceeded_count.tolist(),
                          actuator_delays_physics_steps=sim.delays.tolist(), friction=friction, added_mass_kg=mass,
                          robot_mass_kg=float(model.body_mass.sum()), wall_seconds=time.perf_counter()-start)
            report['episodes'].append(record)
            if stop is not None: record['stop'] = stop.report()
            print(json.dumps(record, ensure_ascii=False), flush=True)
            if writer is not None and episode < args.episodes-1: writer.close(); writer=None
            if renderer is not None: renderer.close(); renderer=None
            if viewer is not None and episode < args.episodes-1:
                viewer.close(); viewer=None
        report['status']='complete'
        # 先保存原回合结果；后续真实物理观察另记，避免覆盖第一次成功/失败状态。
        report['wall_seconds']=time.perf_counter()-began
        report['successes']=sum(e['state']=='success' for e in report['episodes'])
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        if viewer is not None or args.observe_seconds is not None:
            report['post_episode_observation'] = observe_after_episode(
                sim,actor,args.device,cfg,stop,viewer=viewer,seconds=args.observe_seconds,output=output,observation=obs,recorder=recorder)
    except BaseException as exc:
        report['status']='error'; report['error']=repr(exc); traceback.print_exc()
        raise
    finally:
        if writer is not None: writer.close()
        if renderer is not None: renderer.close()
        if viewer is not None: viewer.close()
        report['wall_seconds']=time.perf_counter()-began
        report['successes']=sum(e['state']=='success' for e in report['episodes'])
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return 0 if report['successes']==args.episodes else 2


if __name__ == '__main__':
    raise SystemExit(main())
