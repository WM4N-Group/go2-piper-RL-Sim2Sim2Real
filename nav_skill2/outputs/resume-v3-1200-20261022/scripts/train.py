"""PPO+AMP训练；每100轮原子保存模型并独立录像，录像完成后继续。"""
import argparse,json,subprocess,sys,time
from dataclasses import asdict
from pathlib import Path
from collections import deque
from nav_skill2.tasks.direct.nav_skill2.parameters import TaskConfig,PPOConfig,load_config,configuration
from nav_skill2.utils.runtime import project_root,output_directory,provenance,write_json,load_checkpoint,dataset_path

def main():
    from isaaclab.app import AppLauncher
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=project_root()/'configs/nav.json')
    parser.add_argument('--num-envs','--num_envs',dest='num_envs',type=int)
    parser.add_argument('--iterations','--max_iterations',dest='iterations',type=int,help='本次额外训练轮数')
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--save-interval',type=int)
    parser.add_argument('--checkpoint-video',action=argparse.BooleanOptionalAction,default=True)
    parser.add_argument('--video-seconds',type=float,default=12.,help='每个案例秒数；自动覆盖前后侧移/左右转向/混合并停车')
    parser.add_argument('--video-device',default='cpu',help='子进程物理/策略设备，CPU降低额外显存；渲染仍GPU')
    parser.add_argument('--video-timeout',type=float,default=900.)
    AppLauncher.add_app_launcher_args(parser);args=parser.parse_args()
    if args.video_seconds<=0 or args.video_timeout<=0:parser.error('Video duration must be positive')
    state=load_checkpoint(args.resume) if args.resume else None
    if state:
        from nav_skill2.tasks.direct.nav_skill2.parameters import REVISION
        if state['configuration']['revision']!=REVISION:parser.error('checkpoint版本与当前奖励/AMP不兼容，请从头训练')
        task=TaskConfig(**state['configuration']['task']);ppo=PPOConfig(**state['configuration']['ppo'])
    else:task,ppo=load_config(args.config)
    if args.num_envs is not None:task.num_envs=args.num_envs
    if args.iterations is not None:ppo.iterations=args.iterations
    if args.save_interval is not None:ppo.save_interval=args.save_interval
    task.validate()
    if min(ppo.iterations,ppo.steps_per_env,ppo.minibatches,ppo.save_interval)<1:parser.error('Counts must be positive')
    if ppo.amp_enabled and not dataset_path().is_file():parser.error(f'AMP dataset missing: {dataset_path()}')
    output=output_directory(args.output,'train');print(f'NAV2 output: {output}',flush=True)
    app=AppLauncher(args).app;env=None;status={'status':'failed'}
    try:
        import torch,gymnasium as gym
        import nav_skill2.tasks
        from nav_skill2.tasks.direct.nav_skill2.nav_skill2_env_cfg import make_env_config
        from nav_skill2.learning.ppo import ActorCritic,PPO
        from nav_skill2.learning.amp import AMP
        torch.set_num_threads(4)
        env=gym.make('Isaac-Nav-Skill2-Go2-Piper-v0',cfg=make_env_config(task,args.device)).unwrapped
        model=ActorCritic(ppo.initial_std).to(env.device)
        amp=AMP(ppo,dataset_path(),env.device) if ppo.amp_enabled else None
        algorithm=PPO(model,ppo,amp)
        if state:algorithm.load(state,env)
        config=configuration(task,ppo);provenance(output,config,env.cfg.robot.spawn.usd_path)
        if amp:write_json(output/'amp_dataset.json',{'sha256':amp.dataset_sha256,**amp.manifest})
        obs=env.reset()[0];recent=deque(maxlen=1000)
        end=algorithm.iteration+ppo.iterations
        with (output/'metrics.jsonl').open('w') as metrics,(output/'episodes.jsonl').open('w') as episodes:
            while algorithm.iteration<end:
                start=time.monotonic();obs,batch,records,reward=algorithm.collect(env,obs);logs=algorithm.update(batch);recent.extend(records)
                for record in records:episodes.write(json.dumps({'iteration':algorithm.iteration,**record})+'\n')
                episodes.flush()
                eligible=[v for v in recent if v['eligible']]
                logs['recent_motion_qualified']=sum(v['success'] for v in eligible)/len(eligible) if eligible else None
                logs['recent_direction_response']=sum(v['direction_response'] for v in recent)/len(recent) if recent else None
                logs['recent_linear_rmse']=sum(v['linear_rmse'] for v in recent)/len(recent) if recent else None
                logs['recent_yaw_rmse']=sum(v['yaw_rmse'] for v in recent)/len(recent) if recent else None
                logs.update(iteration=algorithm.iteration,reward=reward,success=sum(v['success'] for v in records),completed=len(records),recent_success=sum(v['success'] for v in recent)/len(recent) if recent else None,mean_level=float(env.levels.float().mean()),level_counts=torch.bincount(env.levels,minlength=task.levels).tolist(),reward_terms=env.reward_terms,seconds=time.monotonic()-start)
                metrics.write(json.dumps(logs,allow_nan=False)+'\n');metrics.flush()
                print(f"iteration {algorithm.iteration}: reward={reward:.4f}, qualified={logs['success']}/{len(records)}, recent={logs['recent_success']}, levels={logs['level_counts']}, {logs['seconds']:.2f}s",flush=True)
                if algorithm.iteration%ppo.save_interval==0 or algorithm.iteration==end:
                    checkpoint=output/f'model_{algorithm.iteration}.pt';algorithm.save(checkpoint,config,env)
                    print(f'Checkpoint: {checkpoint}',flush=True);status['checkpoint']=str(checkpoint)
                    if args.checkpoint_video:
                        level=int(env.levels.float().median())
                        destination=output/'checkpoint_videos'/checkpoint.stem
                        command=[sys.executable,str(project_root()/'play.py'),'--checkpoint',str(checkpoint),'--headless','--enable_cameras','--device',args.video_device,'--level',str(level),'--suite','--seconds',str(args.video_seconds),'--output',str(destination)]
                        print(f'Recording checkpoint {algorithm.iteration}, level={level}; training is waiting',flush=True)
                        destination.parent.mkdir(exist_ok=True)
                        with (output/f'video_{algorithm.iteration}.log').open('w') as log:
                            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=args.video_timeout,cwd=project_root())
                        if result.returncode:raise RuntimeError(f'Checkpoint video failed: see video_{algorithm.iteration}.log; model preserved')
                        report=json.loads((destination/'report.json').read_text())
                        if report['status']!='complete':raise RuntimeError('Video incomplete; training stopped with checkpoint preserved')
                        print(f"Video: {destination/'locomotion.mp4'}, results={report['cases']}",flush=True)
        status.update(status='complete',iteration=algorithm.iteration,note='Training completed; not skill acceptance')
    except BaseException as exc:status['error']=repr(exc);raise
    finally:
        write_json(output/'status.json',status)
        if env is not None:env.close()
        app.close()

if __name__=='__main__':main()
