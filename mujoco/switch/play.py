"""同一 MuJoCo 世界里的技能切换。默认 CUDA、交互窗口、结束后继续真实物理。"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from runtime import Runtime
from machine import Machine
from plans import plan
from plugins import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sequence',choices=['nav-nav','nav-climb','nav-push','nav-push-climb','box-stairs'],default='nav-climb')
    parser.add_argument('--box-height',type=float,default=.2)
    parser.add_argument('--push-distance',type=float,default=.6)
    parser.add_argument('--delay-ms',type=int,choices=[0,5,10,15,20],default=20)
    parser.add_argument('--seed',type=int,default=3701)
    parser.add_argument('--device',default='cuda')
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--video',action='store_true')
    parser.add_argument('--near-climb',action='store_true',
                        help='Experimental in-place Push-to-Climb preparation; not yet validated')
    parser.add_argument('--observe-seconds',type=float)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if not np.isfinite(args.box_height) or not 0<=args.box_height<=.2:
        parser.error('box-height must be in [0,.2] metres')
    if not np.isfinite(args.push_distance) or args.push_distance<=0:
        parser.error('push-distance must be positive metres')
    if args.observe_seconds is not None and (not np.isfinite(args.observe_seconds) or args.observe_seconds<=0):
        parser.error('observe-seconds must be positive')
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    output = (args.output or Path(__file__).parent/'outputs'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')).resolve()
    output.mkdir(parents=True,exist_ok=False)
    print('Output:',output,flush=True)
    r = Runtime(args.sequence,args.box_height,args.push_distance,args.delay_ms,args.seed,args.device)
    r.near_climb=args.near_climb
    machine = Machine(r,plan(args.sequence,getattr(r,'staircase',None)))
    viewer = video = None
    report = dict(successful=False,reason='not_started',config=vars(args),tasks=machine.tasks,
        plant='Push/Climb USD mass/inertia; Push self collision on; damping=0 frictionloss=.01 fixed throughout',
        physics_device='CPU',inference_device=args.device,
        localization='Exact MuJoCo state; known map, manual obstacle-free waypoints; no real sensor model',
        formal_acceptance=False,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [*(p for folder in ['switch','nav','climb','push'] for p in (ROOT/folder).glob('*.py')),
                      *(ROOT/'push/controller').glob('*.py')]},
        actor_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ['nav','climb','push'] for p in (ROOT/folder/'policy').glob('*.pt')})
    rows = []
    began = time.perf_counter()
    complete_time = None
    hold_peak = 0.
    try:
        if not args.headless:
            import mujoco.viewer
            viewer = mujoco.viewer.launch_passive(r.sim.model,r.sim.data)
            viewer.cam.lookat[:] = [0.,-.7,.3]
            viewer.cam.distance,viewer.cam.azimuth,viewer.cam.elevation = 5.,115.,-35.
        if args.video:
            video = r.nav['video'].VideoRecorder(r.sim.model,output/'switch.mp4')
        for tick in range(50000):
            if viewer is not None and not viewer.is_running():
                report['reason']='viewer_closed'
                break
            machine.update()
            if machine.complete and complete_time is None:
                complete_time = float(r.sim.data.time)
                report.update(reason='sequence_complete',successful=True)
                (output/'report.json').write_text(json.dumps({**report,'events':machine.events,'results':machine.results},default=str,indent=2),encoding='utf-8')
            for _ in range(4):
                command = machine.next_command()
                r.step(command)
                machine.after_step()
            if complete_time is not None:
                hold_peak = max(hold_peak,float(np.linalg.norm(r.sim.data.qvel[:3])))
                observe = args.observe_seconds if args.observe_seconds is not None else (5. if args.headless else float('inf'))
                if r.sim.data.time-complete_time>=observe:
                    break
            rows.append(np.r_[r.sim.data.time,machine.index,r.sim.data.qpos,r.sim.data.qvel,r.sim.torque])
            if video is not None:
                video.capture(r.sim.data,viewer.cam if viewer is not None else None)
            if tick%250==0:
                print(f't={r.sim.data.time:.1f} task={machine.index} phase={machine.phase} xy={r.sim.data.qpos[:2]}',flush=True)
                if getattr(machine,'kind','')=='push' and machine.phase=='run' and machine.finish is None:
                    c=r.sim.controller
                    print('push approach:',int(c.safe_approach_index[0]),'face:',bool(c.approach_face_ready[0]),'root_z:',float(r.sim.data.qpos[2]),
                        'hand:',r.sim.robot.data.body_pos_w[0,c.hand_id].tolist(),flush=True)
            if viewer is not None:
                viewer.sync()
                remaining = r.sim.data.time-(time.perf_counter()-began)
                if remaining>0:
                    time.sleep(remaining)
        else:
            report.update(successful=False,reason='global_timeout')
    except Exception as error:
        report.update(successful=False,reason=str(error))
        import traceback
        traceback.print_exc()
    finally:
        if video is not None:
            video.close()
        if viewer is not None:
            viewer.close()
        p = r.sim
        report.update(seconds=float(p.data.time),events=machine.events,results=machine.results,
            switches=machine.switch_metrics,physical_steps=r.step_count,
            delay_steps=p.delays.tolist(),peak_torque_nm=p.peak_torque.tolist(),
            saturation_physics_steps=p.saturation.tolist(),peak_joint_speed_rad_s=p.peak_speed.tolist(),
            speed_exceeded_physics_steps=p.speed_exceeded.tolist(),max_tilt_rad=r.max_tilt,
            angle_violation_rad=r.angle_violation.tolist(),
            final_position=p.data.qpos[:3].tolist(),final_speed_m_s=float(np.linalg.norm(p.data.qvel[:3])),
            final_hold_seconds=0. if complete_time is None else float(p.data.time)-complete_time,
            final_hold_peak_speed_m_s=hold_peak,minimum_arm_base_clearance_m=machine.guard.minimum_surface,
            robot_mass_kg=float(p.model.body_subtreemass[p.base_id]))
        if hasattr(machine,'push_entry'):
            report['push_entry']=machine.push_entry.report()
        if hasattr(r,'staircase'):
            report['staircase']=r.staircase.report(p)
        if hasattr(machine,'preparation'):
            report['last_preparation']=machine.preparation.report()
        report['failure_contact']=getattr(r,'failure_contact',None)
        (output/'report.json').write_text(json.dumps(report,default=str,indent=2)+'\n',encoding='utf-8')
        np.savez_compressed(output/'trace.npz',trace=np.array(rows),
            final_qpos=p.data.qpos.copy(),final_qvel=p.data.qvel.copy(),
            columns='time,task_index,qpos[32],qvel[30],torque[18]',joint_names=r.push['model'].JOINTS)
        print(json.dumps({k:report[k] for k in ['successful','reason','seconds','final_position']},ensure_ascii=False),flush=True)
    return 0 if report['successful'] else 1


if __name__=='__main__':
    raise SystemExit(main())
