"""Isolated V1 snapshot evaluation and runtime contract probe; never modifies training."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    from isaaclab.app import AppLauncher
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=72001)
    parser.add_argument('--num-envs',type=int,default=1)
    parser.add_argument('--episodes',type=int,default=1)
    parser.add_argument('--nominal',action='store_true')
    parser.add_argument('--steps',type=int,default=None)
    parser.add_argument('--exit-control',action='store_true')
    AppLauncher.add_app_launcher_args(parser)
    args=parser.parse_args()
    if args.exit_control and args.episodes>args.num_envs:
        parser.error('EXIT evaluation supports one episode per environment; episodes must be <= num-envs')
    args.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(args.snapshot/'source/climb_skill'))
    app=AppLauncher(args).app
    env=None
    report=dict(status='error',mode='native',seed=args.seed,requested_episodes=args.episodes,
                checkpoint_sha256=digest(args.checkpoint),command=[sys.executable,*sys.argv],
                started_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'),episodes=[],formal_acceptance=False)
    report['started_episodes']=0
    start=time.monotonic()
    try:
        import numpy as np
        import torch
        from climb_skill.tasks.direct.climb_skill.task_parameters import TaskConfig
        from climb_skill.tasks.direct.climb_skill.climb_skill_env_cfg import make_env_config
        from climb_skill.tasks.direct.climb_skill.climb_skill_env import ClimbSkillEnv
        from climb_skill.learning.actor_critic import ClimbActorCritic
        torch.set_num_threads(2)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        saved=torch.load(args.checkpoint,map_location='cpu',weights_only=False)
        task=TaskConfig(**saved['configuration']['task'])
        task.num_envs=args.num_envs;task.seed=args.seed;task.curriculum=False
        if args.nominal: task.randomization=False
        env=ClimbSkillEnv(cfg=make_env_config(task,args.device))
        if args.exit_control:
            limits=env.robot.root_physx_view.get_dof_max_velocities().to(env.device)-.005
            env.robot.write_joint_velocity_limit_to_sim(limits)
            report['velocity_guard_rad_s']=.005
        actor=ClimbActorCritic().to(env.device).eval()
        actor.load_state_dict(saved['model'],strict=True)
        obs=env.reset()[0]['policy']
        report['started_episodes']=min(args.episodes,args.num_envs)
        source_paths={name:(Path(__file__).parent/name if (Path(__file__).parent/name).is_file() else Path(__file__).resolve().parents[1]/name) for name in ('isaac_reference.py','isaac_exit_hooks.py','exit_control.py')}
        report['source_sha256']={name:digest(path) for name,path in source_paths.items()}
        (args.output/'source').mkdir()
        import shutil
        for name in report['source_sha256']:shutil.copy2(source_paths[name],args.output/'source'/name)
        if args.exit_control:
            sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
            from isaac_exit_hooks import install
            install(env,args.output)
            report['mode']='full_exit_development'
        view=env.robot.root_physx_view
        def array(value):
            return value.detach().cpu().numpy().tolist() if hasattr(value,'detach') else value
        probe=dict(body_names=env.robot.body_names,joint_names=env.robot.joint_names,
                   ordered_joint_names=[env.robot.joint_names[i] for i in env.joint_ids],
                   configuration=saved['configuration'],nominal=args.nominal,
                   robot_usd=os.environ.get('CLIMB_ROBOT_USD'),torch=torch.__version__,
                   task_source=str(sys.modules[ClimbSkillEnv.__module__].__file__))
        for name in ('get_masses','get_inertias','get_coms','get_dof_limits','get_dof_max_velocities',
                     'get_dof_max_forces','get_dof_armatures','get_dof_friction_coefficients','get_dof_friction_properties'):
            try: probe[name]=array(getattr(view,name)())
            except Exception as exc: probe[name]=dict(error=repr(exc))
        for name in ('default_joint_pos','soft_joint_pos_limits','joint_pos_limits','joint_velocity_limits'):
            try: probe[name]=array(getattr(env.robot.data,name))
            except Exception as exc: probe[name]=dict(error=repr(exc))
        probe['body_pos_w']=array(env.robot.data.body_pos_w)
        probe['reset_joint_pos']=array(env.robot.data.joint_pos)
        probe['body_quat_w']=array(env.robot.data.body_quat_w)
        probe['actuators']={name:dict(joint_indices=array(a.joint_indices),stiffness=array(a.stiffness),
                                   damping=array(a.damping),effort_limit=array(a.effort_limit),
                                   velocity_limit=array(a.velocity_limit)) for name,a in env.robot.actuators.items()}
        (args.output/'runtime_contract.json').write_text(json.dumps(probe,indent=2,default=str)+'\n')
        speed=torch.tensor([30.1,30.1,15.7]*4+[3.]*6,device=env.device)
        peak=torch.zeros(args.num_envs,18,device=env.device)
        exceeded=torch.zeros_like(peak,dtype=torch.int64)
        peak_torque=torch.zeros_like(peak)
        original_apply=env._apply_action
        def apply():
            original_apply()
            velocity=env.robot.data.joint_vel[:,env.joint_ids].abs()
            peak.maximum_(velocity) if hasattr(peak,'maximum_') else peak.copy_(torch.maximum(peak,velocity))
            exceeded.add_((velocity>speed+1e-5).long())
            torque=env.robot.data.applied_torque[:,env.joint_ids].abs()
            peak_torque.copy_(torch.maximum(peak_torque,torque))
        env._apply_action=apply
        quotas=[args.episodes//args.num_envs+(i<args.episodes%args.num_envs) for i in range(args.num_envs)]
        counts=[0]*args.num_envs
        with torch.inference_mode():
            for step in range(args.steps or max(quotas)*(env.max_episode_length+1)):
                actions=actor(obs)
                obs,_,_,_,info=env.step(actions)
                obs=obs['policy']
                for record in info.get('episode_records',[]):
                    i=record['env']
                    if counts[i]<quotas[i]:
                        report['episodes'].append(dict(**record,episode=counts[i],
                            peak_speed_rad_s=array(peak[i]),speed_exceeded_physics_samples=array(exceeded[i]),
                            peak_torque_nm=array(peak_torque[i])))
                        counts[i]+=1
                        print(f"episode={len(report['episodes'])}/{args.episodes} {record['reason']}",flush=True)
                    peak[i]=0;exceeded[i]=0;peak_torque[i]=0
                if len(report['episodes'])==args.episodes:break
        report.update(status='complete' if len(report['episodes'])==args.episodes else 'incomplete',
                      successes=sum(r['success'] for r in report['episodes']),
                      missing_episodes=args.episodes-len(report['episodes']),
                      physics_dt=task.physics_dt,control_dt=env.step_dt,randomization=task.randomization)
    except BaseException as exc:
        report['error']=repr(exc)
        raise
    finally:
        report['wall_seconds']=time.monotonic()-start
        report['normal_failures']=sum(not r['success'] for r in report['episodes'])
        report['started_missing_terminal']=report['started_episodes']-len(report['episodes'])
        report['not_run']=args.episodes-report['started_episodes']
        (args.output/'report.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
        if env is not None:env.close()
        app.close()
    return 0 if report['status']=='complete' else 2


if __name__=='__main__':raise SystemExit(main())
