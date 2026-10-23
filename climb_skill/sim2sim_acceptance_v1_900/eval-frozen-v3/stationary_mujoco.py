"""Development runner for the explicit V1/900 post-ascent stationary exit."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time
import shutil

import mujoco
import numpy as np
import torch
from bridge import ROOT, ClimbBridge, build_model, load_contract, sha, EFFORT, SPEED
from exit_control import ExitController, EXIT_SPEC, smooth
from velocity_constraints import constrained_model, VelocityClimbBridge


def run(args):
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    device='cuda' if torch.cuda.is_available() else 'cpu'
    if device!='cuda':raise RuntimeError('Acceptance requires the existing CUDA Actor environment')
    contract=load_contract();cfg=contract['configuration']['task']
    output=args.output or ROOT/'outputs'/datetime.now().strftime('stationary-dev-%Y%m%d-%H%M%S')
    output.mkdir(parents=True,exist_ok=False)
    actor=torch.jit.load(str(ROOT/'policy/actor.pt'),map_location=device).eval()
    report=dict(status='error',formal_acceptance=False,seed=args.seed,episodes=[],exit_spec=EXIT_SPEC,
                actor_sha256=contract['actor_sha256'],checkpoint_sha256=contract['checkpoint_sha256'],
                randomization=args.randomize,requested_episodes=args.episodes,
                source_sha256={p.name:sha(p) for p in (ROOT/'bridge.py',ROOT/'exit_control.py',ROOT/'velocity_constraints.py',Path(__file__))})
    report.update(started_episode_indices=[],inference_device=device,
        versions=dict(torch=torch.__version__,mujoco=mujoco.__version__,numpy=np.__version__),
        gpu=torch.cuda.get_device_name(),task_seconds=cfg['episode_seconds'])
    (output/'source').mkdir()
    for name in report['source_sha256']:shutil.copy2(ROOT/name,output/'source'/name)
    began=time.monotonic()
    try:
        for episode in range(args.episodes):
            report['started_episode_indices'].append(episode)
            seed=np.random.SeedSequence(args.seed+episode).spawn(2)
            rng=np.random.default_rng(seed[0])
            friction=min(.6,.75*rng.uniform(*cfg['friction_range'])) if args.randomize else .6
            mass=rng.uniform(*cfg['added_mass_range']) if args.randomize else 0.
            model,spec=constrained_model(cfg,.2,friction,mass)
            sim=VelocityClimbBridge(model,cfg,.2,seed[1],args.randomize)
            controller=ExitController(sim.reference,cfg)
            trace={k:[] for k in ('time','qpos','qvel','targets','torque','raw_torque','actor_action',
                                  'processed_action','forces','feet','com','phase','hold','margin',
                                  'velocity_constraint_torque','pre_constraint_velocity','free_velocity_prediction',
                                  'delayed_command','command_state','actuator_force','warnings')}
            (output/f'initial_{episode:03d}.json').write_text(json.dumps(dict(qpos=sim.data.qpos.tolist(),qvel=sim.data.qvel.tolist(),
                kp=sim.kp.tolist(),kd=sim.kd.tolist(),delays=sim.delays.tolist(),joint_qids=sim.qids.tolist(),
                joint_dids=sim.dids.tolist(),actuator_ids=sim.aids.tolist(),forbidden=sim.forbidden,feet_ids=sim.feet_ids.tolist())))
            obs=sim.observation();state='running';reason=''
            native_time=None
            renderer=writer=None
            if args.video:
                import imageio.v2 as imageio
                renderer=mujoco.Renderer(model,540,960)
                writer=imageio.get_writer(output/f'episode_{episode:03d}.mp4',fps=25,macro_block_size=2)
                cam=mujoco.MjvCamera();cam.distance=3.4;cam.azimuth=135;cam.elevation=-22;cam.lookat[:]=[1.2,0,.35]
            try:
                for step in range(args.steps or round(cfg['episode_seconds']/sim.dt)):
                    with torch.inference_mode():action=actor(torch.from_numpy(obs)[None].to(device)).cpu().numpy()[0]
                    sim.set_action(action)
                    if controller.phase!='ACTIVE':
                        sim.targets=controller.last_target.copy()
                        sim.actions=(sim.targets-sim.reference)/cfg['action_scale']
                    for _ in range(cfg['decimation']):
                        sim.physics_step()
                        if not np.isfinite(sim.data.qpos).all():raise FloatingPointError('Nonfinite state')
                        physics_state=dict(feet=sim.data.xpos[sim.feet_ids],forces=sim.forces[sim.feet_ids],
                            com=sim.data.subtree_com[sim.base_id],height=.2,tilt=sim.state()[3],
                            root_velocity=sim.data.qvel[:3],angular_velocity=sim.state()[0]@sim.data.qvel[3:6],
                            joint_velocity=sim.data.qvel[sim.dids],
                            arm_error=float(abs(sim.data.qpos[sim.qids[12:]]-sim.reference[12:]).max()))
                        controller.observe_physics(physics_state,model.opt.timestep)
                        values=dict(time=sim.data.time,qpos=sim.data.qpos.copy(),qvel=sim.data.qvel.copy(),
                                    targets=sim.targets.copy(),torque=sim.applied_torque.copy(),raw_torque=sim.raw_torque.copy(),
                                    actor_action=action.copy(),processed_action=sim.actions.copy(),forces=sim.forces.copy(),
                                    feet=sim.data.xpos[sim.feet_ids].copy(),com=sim.data.subtree_com[sim.base_id].copy(),
                                    phase=controller.phase,hold=controller.hold,margin=controller.metrics.get('com_margin_m',-1.))
                        values.update(velocity_constraint_torque=sim.velocity_constraint_torque.copy(),
                                      delayed_command=sim.delayed_command.copy(),command_state=sim.command_state.copy(),
                                      actuator_force=sim.data.qfrc_actuator.copy(),warnings=sim.data.warning.number.copy(),
                                      pre_constraint_velocity=sim.pre_constraint_velocity.copy(),
                                      free_velocity_prediction=sim.free_velocity_prediction.copy())
                        for k,v in values.items():trace[k].append(v)
                    native,why=sim.status()
                    data=dict(feet=sim.data.xpos[sim.feet_ids],forces=sim.forces[sim.feet_ids],
                              com=sim.data.subtree_com[sim.base_id],height=.2,tilt=sim.state()[3],
                              root_velocity=sim.data.qvel[:3],angular_velocity=sim.data.qvel[3:6],
                              joint_velocity=sim.data.qvel[sim.dids],
                              arm_error=float(abs(sim.data.qpos[sim.qids[12:]]-sim.reference[12:]).max()),seconds=sim.elapsed)
                    rot=sim.state()[0]
                    com_jac=np.zeros((3,model.nv));mujoco.mj_jacSubtreeCom(model,sim.data,com_jac,sim.base_id)
                    data.update(angular_velocity=rot@sim.data.qvel[3:6],com_velocity=com_jac@sim.data.qvel,friction=friction)
                    jacobians=[]
                    for foot in sim.feet_ids:
                        jac=np.zeros((3,model.nv));mujoco.mj_jacBody(model,sim.data,jac,None,int(foot))
                        jacobians.append(jac[:,sim.dids])
                    data.update(roll=float(np.arctan2(rot[2,1],rot[2,2])),pitch=float(np.arcsin(-rot[2,0])),
                                yaw=sim.state()[2],mass=float(model.body_mass.sum()),foot_jacobian=jacobians,
                                gravity_joint=sim.gravity_data.qfrc_bias[sim.dids].copy(),
                                joint_position=sim.data.qpos[sim.qids].copy(),kp=sim.kp,kd=sim.kd,soft_limits=sim.soft_limits)
                    outcome=controller.update(data,native=='success',sim.targets,sim.dt)
                    if native=='success' and native_time is None:native_time=sim.elapsed
                    if native=='failed':state,reason='failed',why
                    elif sim.elapsed>=cfg['episode_seconds']-1e-9:state,reason='timeout','task_timeout'
                    elif outcome=='success':state,reason='success','stationary_exit_complete'
                    elif outcome:state,reason='failed',outcome
                    elif native=='timeout':state,reason='timeout',why
                    obs=sim.observation()
                    if controller.phase=='BRAKE':obs[9]=cfg['approach_speed']*(1-smooth(controller.phase_time/EXIT_SPEC['brake_seconds']))
                    elif controller.phase!='ACTIVE':obs[9]=0.
                    if writer and (step%2==0 or state!='running'):
                        renderer.update_scene(sim.data,camera=cam);writer.append_data(renderer.render())
                    if step%100==0:print(f'{episode} t={sim.elapsed:.2f} x={sim.data.qpos[0]:.3f} {controller.phase} {controller.metrics}',flush=True)
                    if state!='running':break
                if state=='running':state,reason=('incomplete','debug_limit') if args.steps else ('timeout','task_timeout')
            finally:
                if writer:writer.close()
                if renderer:renderer.close()
            np.savez_compressed(output/f'trace_{episode:03d}.npz',**trace)
            (output/f'model_{episode:03d}.xml').write_text(spec.to_xml(),encoding='utf-8')
            mujoco.mj_saveModel(model,str(output/f'model_{episode:03d}.mjb'),None)
            record=dict(episode=episode,seed=args.seed+episode,state=state,reason=reason,seconds=sim.elapsed,
                        native_ascent_seconds=native_time,phase=controller.phase,events=controller.events,
                        front_done=controller.front_done,final_metrics=controller.metrics,
                        peak_joint_speed_rad_s=sim.peak_speed.tolist(),speed_exceeded_samples=sim.speed_exceeded_count.tolist(),
                        peak_torque_nm=sim.peak_torque.tolist(),mass_added=float(mass),friction=float(friction))
            report['episodes'].append(record);print(json.dumps(record),flush=True)
        report['status']='complete'
    except BaseException as exc:
        report['error']=repr(exc);raise
    finally:
        report['wall_seconds']=time.monotonic()-began
        report['successes']=sum(e['state']=='success' for e in report['episodes'])
        report['normal_failures']=sum(e['state'] in ('failed','timeout') for e in report['episodes'])
        report['started_missing_terminal']=len(report['started_episode_indices'])-sum(e['state'] in ('success','failed','timeout') for e in report['episodes'])
        report['not_run']=args.episodes-len(report['started_episode_indices'])
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return 0 if report['successes']==args.episodes else 2


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--episodes',type=int,default=1);p.add_argument('--seed',type=int,default=74001)
    p.add_argument('--output',type=Path);p.add_argument('--steps',type=int)
    p.add_argument('--randomize',action='store_true');p.add_argument('--video',action='store_true')
    raise SystemExit(run(p.parse_args()))
