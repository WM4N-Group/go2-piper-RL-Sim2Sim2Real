"""Push v212 Sim-to-Sim：双Actor→原IK/接触控制→MuJoCo延迟PD。

python play.py                    # CUDA推理、可拖动窗口
python play.py --video            # 可选录像，包含回合后持续物理
python play.py --headless --observe-seconds 15
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time

import mujoco
import numpy as np
import torch

from bridge import PushBridge
from model import ROOT, JOINTS, EFFORT, PHYSICS_DT
from timing import DEFAULT_APPROACH


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def settle(sim):
    """沿原启动流程真实承重；初始化阶段结束后才开始任务计时。"""
    feet = [sim.model.body(f'{leg}_foot').id for leg in ('FL','FR','RL','RR')]
    start = sim.data.qpos[:2].copy()
    bottoms = []
    for foot in feet:
        for gid in np.flatnonzero(sim.model.geom_bodyid==foot):
            if sim.model.geom_type[gid]==mujoco.mjtGeom.mjGEOM_SPHERE:
                bottoms.append(sim.data.geom_xpos[gid,2]-sim.model.geom_size[gid,0])
    if len(bottoms)!=4:
        raise ValueError('Expected four USD foot collision spheres')
    sim.data.qpos[2] -= max(0.,min(bottoms)-.002)
    sim.refresh()
    stable_age = 0.
    for step in range(2000):
        sim.physics_step()
        loaded = np.all(np.linalg.norm(sim.forces[feet],axis=1)>3.)
        good = np.linalg.norm(sim.data.qvel[:3])<.035 and np.linalg.norm(sim.data.qvel[3:6])<.12 and loaded
        stable_age = stable_age+PHYSICS_DT if good else 0.
        if step*PHYSICS_DT>=6. and stable_age>=.3:
            break
    initial_stable = stable_age>=.3
    if initial_stable:
        # 原Isaac启动也在承重后恢复起点XY，随后再真实沉降0.5s。
        # 只发生在任务开始前；任务中绝不写入位姿。
        sim.data.qpos[:2] = start
        sim.data.qvel[:6] = 0.
        for _ in range(100):
            sim.physics_step()
    good = (initial_stable and np.linalg.norm(sim.data.qvel[:3])<.035
            and np.linalg.norm(sim.data.qvel[3:6])<.12
            and np.all(np.linalg.norm(sim.forces[feet],axis=1)>3.)
            and np.linalg.norm(sim.data.qpos[:2]-start)<.01)
    result = dict(stable=bool(good),seconds=float(sim.data.time),root_position=sim.data.qpos[:3].tolist(),
                  linear_speed=float(np.linalg.norm(sim.data.qvel[:3])),
                  angular_speed=float(np.linalg.norm(sim.data.qvel[3:6])),scope='Physical initialization only')
    sim.controller.reset(None)
    sim.applied_commands[:] = 0.
    sim.history = None
    return result


def infer(actors,observation,device):
    with torch.inference_mode():
        inputs = torch.as_tensor(observation,device=device)[None]
        return [actor(inputs).cpu().numpy()[0] for actor in actors]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',default='cuda')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--video',action='store_true')
    parser.add_argument('--seed',type=int,default=3701)
    parser.add_argument('--push-distance','--distance',type=float,default=.6,
        help='箱子沿世界+X方向的目标位移，单位米，必须大于0；默认0.6')
    parser.add_argument('--timeout',type=float,default=48.,help='推箱阶段超时秒数，不含启动、收臂和站稳')
    parser.add_argument('--arm-speed',type=float,default=DEFAULT_APPROACH.entry_gain)
    parser.add_argument('--friction',type=float,default=.6)
    parser.add_argument('--delay-ms',type=int,choices=(0,5,10,15,20))
    parser.add_argument('--observe-seconds',type=float)
    parser.add_argument('--steps',type=int,help='Debug control-step cap; truncation is not success')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if not np.isfinite(args.push_distance) or args.push_distance<=0:
        parser.error('push-distance must be finite and positive, in metres')
    if not np.isfinite(args.timeout) or args.timeout<=0 or (args.steps is not None and args.steps<1):
        parser.error('timeout must be finite and positive; steps must be a positive integer')
    if not 1<=args.arm_speed<=4 or args.friction<=0 or (args.observe_seconds is not None and args.observe_seconds<=0):
        parser.error('arm-speed in [1,4], friction and observation duration positive')
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    output = (args.output or ROOT/'outputs'/datetime.now().strftime('play-%Y%m%d-%H%M%S-%f')).resolve()
    output.mkdir(parents=True,exist_ok=False)
    print('Output:',output,flush=True)
    from policy_loader import load_actors
    actors = load_actors(ROOT/'policy',args.device)
    sim = PushBridge(args.seed,args.arm_speed,args.friction,args.delay_ms,push_distance=args.push_distance)
    goal_position = sim.box_push_target[0].numpy().astype(float).copy()
    report = dict(status='running',successful=False,formal_acceptance=False,engine='MuJoCo',
                  inference_device=args.device,physics_device='CPU',seed=args.seed,
                  actor_sha256={name:sha(ROOT/'policy'/name) for name in ('leg_actor.pt','arm_actor.pt')},
                  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [*ROOT.glob('*.py'),*ROOT.glob('controller/*.py')]},
                  robot_mass_kg=float(sim.model.body_mass.sum()-1.),box_mass_kg=1.,box_friction=.15,
                  robot_friction=args.friction,actuator_delays_steps=sim.delays.tolist(),
                  push_distance_m=args.push_distance,target_box_position=goal_position.tolist(),
                  push_timeout_seconds=args.timeout,
                  notes=['Exact state and known box pose; no perception or state-estimation noise.',
                         'PhysX and MuJoCo contact/delay RNG differ; identical seeds do not imply identical initial states.',
                         'Success requires arm retraction and stationary hold; not hardware readiness.'])
    viewer = recorder = finish = None
    trace = []
    try:
        if not args.headless:
            from mujoco import viewer as mj_viewer
            viewer = mj_viewer.launch_passive(sim.model,sim.data)
            viewer.cam.distance,viewer.cam.azimuth,viewer.cam.elevation = 3.,105.,-20.
            viewer.cam.lookat[:] = [.9,0.,.3]
        startup = settle(sim)
        (output/'startup.json').write_text(json.dumps(startup,indent=2)+'\n',encoding='utf-8')
        if not startup['stable']:
            raise RuntimeError('Physical startup did not settle; inspect startup.json')
        if args.video:
            from video import VideoRecorder
            recorder = VideoRecorder(sim.model,output/'push.mp4')
            recorder.next_frame = float(sim.data.time)
            recorder.camera.distance,recorder.camera.azimuth,recorder.camera.elevation = 3.,105.,-20.
        began,started = time.perf_counter(),float(sim.data.time)
        report['initial_box_position'] = sim.data.xpos[sim.box_id].tolist()
        observation = sim.observation()
        flags = {}
        phase_times = {}
        for step in range(args.steps or max(1,round(args.timeout/sim.step_dt))):
            if viewer is not None and not viewer.is_running():
                report['status'] = 'viewer_closed'
                break
            leg,arm = infer(actors,observation,args.device)
            sim.set_action(leg,arm)
            for _ in range(4):
                sim.physics_step()
            sim.episode_length_buf += 1
            flags = sim.termination()
            observation = sim.observation()
            c = sim.controller
            elapsed = float(sim.data.time)-started
            for name,ready in [('safe_waypoint',c.safe_approach_complete),
                               ('height_aligned',c.approach_height_aligned),
                               ('face_geometry',c.debug_face_geometric_ready),
                               ('face_ready',c.approach_face_ready),('base_released',c.motion_ready)]:
                if bool(ready[0]) and name not in phase_times:
                    phase_times[name] = elapsed
            trace.append(np.r_[elapsed,sim.data.qpos,sim.data.qvel,sim.targets,sim.torque,
                               sim.applied_commands,float(c.safe_approach_index[0]),
                               bool(c.approach_face_ready[0]),bool(c.motion_ready[0])])
            if recorder is not None:
                recorder.capture(sim.data,viewer.cam if viewer is not None else None)
            if viewer is not None:
                viewer.sync()
                remaining = elapsed-(time.perf_counter()-began)
                if remaining>0:time.sleep(remaining)
            if step%100==0:
                print(f't={elapsed:.2f}s path={int(c.safe_approach_index[0])} '
                      f'face={bool(c.approach_face_ready[0])} box_x={sim.data.xpos[sim.box_id,0]:.3f}',flush=True)
            failures = [name for name,value in flags.items() if name!='box_settled' and value]
            if failures or flags['box_settled']:
                report.update(status='complete',successful=bool(flags['box_settled'] and not failures),
                              terminal_flags=flags,reason=','.join(failures) if failures else 'box_settled')
                break
        else:
            report.update(status='incomplete' if args.steps else 'timeout',reason='step_limit' if args.steps else 'push_timeout')
        report['push_successful'] = report['successful']
        report['approach_phase_seconds'] = phase_times
        report['approach_timing'] = dict(entry_gain=args.arm_speed,
            alignment_rate_rad_s=sim.cfg.play_alignment_rate,
            confirmation_seconds=sim.cfg.play_approach_confirmation,
            face_advance_m_s=sim.cfg.play_face_advance_speed,
            alignment_joint_speed_rad_s=sim.cfg.play_alignment_velocity,
            leg_release_seconds=sim.cfg.push_leg_release_ramp_s)
        report['smooth_approach'] = dict(enabled=sim.cfg.play_smooth_approach,
            pose_seconds=c.pose_approach.duration,ik_gain=c.pose_approach.ik_gain,
            velocity_feedback_seconds=c.pose_approach.velocity_feedback_time,
            entry_minimum_seconds=c.pose_approach.entry_minimum_seconds,
            entry_peak_rad_s=c.pose_approach.entry_peak_rad_s,
            residual_transition_seconds=.4)
        report['push_seconds'] = float(sim.data.time)-started
        if report['push_successful']:
            from finish import FinishController
            finish = FinishController(sim)
            finish_trace = []
            report['successful'] = False
            for exit_step in range(1300):
                if viewer is not None and not viewer.is_running():
                    report.update(status='viewer_closed',reason='closed_during_retraction');break
                for _ in range(4):
                    command = finish.command()
                    sim.physics_step(command)
                    finish.after_step()
                sim.episode_length_buf += 1
                elapsed = float(sim.data.time)-started
                finish_trace.append(np.r_[elapsed,sim.data.qpos,sim.data.qvel,command.position,sim.torque])
                if recorder is not None:recorder.capture(sim.data,viewer.cam if viewer is not None else None)
                if viewer is not None:
                    viewer.sync()
                    remaining = elapsed-(time.perf_counter()-began)
                    if remaining>0:time.sleep(remaining)
                if exit_step%100==0:
                    print(f't={elapsed:.2f}s finish={finish.phase} arm_error={np.max(abs(sim.data.qpos[sim.qids[12:]])):.3f}',flush=True)
                if finish.failure or finish.phase=='success':
                    report.update(successful=not bool(finish.failure),status='complete' if not finish.failure else 'failed',
                        reason=finish.failure or 'push_retracted_and_stationary')
                    break
            np.savez_compressed(output/'finish_trace.npz',trace=np.array(finish_trace),
                columns='time[1],qpos[32],qvel[30],target[18],torque[18]',action_joint_names=JOINTS)
            report['finish'] = finish.report()
        box_position = sim.data.xpos[sim.box_id].copy()
        report.update(seconds=float(sim.data.time)-started,box_position=box_position.tolist(),
                      box_displacement_m=(box_position-np.array(report['initial_box_position'])).tolist(),
                      goal_error_xy_m=float(np.linalg.norm(box_position[:2]-goal_position[:2])),
                      peak_torque_nm=sim.peak_torque.tolist(),torque_saturation_steps=sim.saturation.tolist(),
                      peak_speed_rad_s=sim.peak_speed.tolist(),speed_exceeded_steps=sim.speed_exceeded.tolist(),
                      minimum_arm_base_surface_clearance_m=sim.min_clearance,
                      max_arm_control_sample_torque_ratio=sim.max_arm_ratio,
                      final_arm_joint_rad=sim.data.qpos[sim.qids[12:]].tolist())
        np.savez_compressed(output/'trace.npz',trace=np.array(trace),
                            columns='time[1],qpos[32],qvel[30],target[18],torque[18],commands[18],path,face_ready,motion_ready',
                            action_joint_names=JOINTS)
        print(json.dumps(report,ensure_ascii=False),flush=True)
        if viewer is not None or args.observe_seconds is not None:
            observe_start,observe_wall = float(sim.data.time),time.perf_counter()
            observation_failures = []
            observation_peaks = dict(linear_speed_m_s=0.,angular_speed_rad_s=0.,arm_error_rad=0.)
            first_observation_failure = None
            next_observation_log = 0.
            hold_log = (output/'hold_observation.jsonl').open('w',encoding='utf-8')
            maximum_goal_error = report['goal_error_xy_m']
            original_success = report['successful']
            continue_controller = original_success
            while args.observe_seconds is None or sim.data.time-observe_start<args.observe_seconds-1e-8:
                if viewer is not None and not viewer.is_running():break
                if finish is not None:
                    for _ in range(4):
                        sim.physics_step(finish.command())
                        finish.after_step()
                elif continue_controller:
                    leg,arm = infer(actors,observation,args.device)
                    sim.set_action(leg,arm)
                    for _ in range(4):sim.physics_step()
                else:
                    for _ in range(4):sim.physics_step()
                sim.episode_length_buf += 1
                observation = sim.observation()
                later_flags = sim.termination()
                failures = [name for name,value in later_flags.items() if name!='box_settled' and value]
                if finish is not None and finish.failure:
                    failures.append(finish.failure)
                if failures:
                    if first_observation_failure is None:
                        first_observation_failure = dict(after_success_seconds=float(sim.data.time)-observe_start,failures=failures)
                    observation_failures.extend(name for name in failures if name not in observation_failures)
                    continue_controller = False
                metrics = dict(linear_speed_m_s=float(np.linalg.norm(sim.data.qvel[:3])),
                    angular_speed_rad_s=float(np.linalg.norm(sim.data.qvel[3:6])),
                    arm_error_rad=float(np.max(abs(sim.data.qpos[sim.qids[12:]]))))
                for name,value in metrics.items():observation_peaks[name] = max(observation_peaks[name],value)
                observed_age = float(sim.data.time)-observe_start
                if observed_age>=next_observation_log-1e-8:
                    hold_log.write(json.dumps(dict(after_success_seconds=observed_age,
                        base_position=sim.data.qpos[:3].tolist(),box_position=sim.data.xpos[sim.box_id].tolist(),
                        phase=finish.phase if finish is not None else 'push',failures=failures,**metrics))+'\n')
                    hold_log.flush()
                    next_observation_log += 1.
                if finish is not None and abs(observed_age/30.-round(observed_age/30.))<1e-6:
                    print(f'observe={observed_age:.0f}s phase={finish.phase} speed={metrics["linear_speed_m_s"]:.5f}m/s',flush=True)
                maximum_goal_error = max(maximum_goal_error,float(np.linalg.norm(sim.data.xpos[sim.box_id,:2]-goal_position[:2])))
                if recorder is not None:recorder.capture(sim.data,viewer.cam if viewer is not None else None)
                if viewer is not None:
                    viewer.sync()
                    remaining = sim.data.time-observe_start-(time.perf_counter()-observe_wall)
                    if remaining>0:time.sleep(remaining)
            report['observation_seconds'] = float(sim.data.time)-observe_start
            hold_log.close()
            report['observation_peaks'] = observation_peaks
            report['first_observation_failure'] = first_observation_failure
            report['observation_final_box_position'] = sim.data.xpos[sim.box_id].tolist()
            report['observation_failures'] = observation_failures
            report['observation_max_goal_error_m'] = maximum_goal_error
            report['observation_goal_maintained'] = original_success and not observation_failures and maximum_goal_error<.12
            if finish is not None:
                report['finish'] = finish.report()
                report['observation_robot_stable'] = finish.phase=='success' and not finish.failure
                report['completion_successful'] = original_success
                if observation_failures:
                    report.update(successful=False,status='failed',reason='post_completion:'+','.join(observation_failures))
    except BaseException as error:
        report.update(status='error',error=repr(error))
        raise
    finally:
        if recorder is not None:recorder.close()
        if viewer is not None:viewer.close()
        (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return 0 if report['successful'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
