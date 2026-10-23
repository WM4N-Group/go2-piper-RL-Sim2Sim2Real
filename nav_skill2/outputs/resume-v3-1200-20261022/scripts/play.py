"""底层速度策略回放：起步→速度跟踪→减速站稳；无目标点导航。"""
import argparse,math
from pathlib import Path
from nav_skill2.tasks.direct.nav_skill2.parameters import TaskConfig,REVISION
from nav_skill2.utils.runtime import load_checkpoint,output_directory,write_json


def main():
    from isaaclab.app import AppLauncher
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--command',nargs=3,type=float,default=[.25,0.,0.],metavar=('VX','VY','WZ'))
    parser.add_argument('--reset-settle-seconds',type=float,help='显式覆盖旧权重：真实承重预落稳，默认沿用checkpoint')
    parser.add_argument('--startup-action-ramp-seconds',type=float,help='显式覆盖旧权重：腿部动作渐入秒数，默认沿用checkpoint')
    parser.add_argument('--suite',action='store_true')
    parser.add_argument('--level',type=int,help='默认最终课程，自动录像用当前课程中位等级')
    parser.add_argument('--seconds',type=float,default=25.)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--video',action=argparse.BooleanOptionalAction,default=True)
    AppLauncher.add_app_launcher_args(parser);args=parser.parse_args()
    if args.seconds<=0:parser.error('seconds must be positive')
    saved=load_checkpoint(args.checkpoint)
    if saved['configuration']['revision']!=REVISION:parser.error('checkpoint与当前Nav2版本不兼容，请用该权重对应源码')
    task=TaskConfig(**saved['configuration']['task']);task.num_envs=1;task.randomization=False;task.curriculum=False
    overrides={}
    for name in ('reset_settle_seconds','startup_action_ramp_seconds'):
        value=getattr(args,name)
        if value is not None:setattr(task,name,value);overrides[name]=value
    task.validate()
    # 指定视频长度独立于训练回合预算；每个案例内部不自动reset。
    task.episode_seconds=max(task.episode_seconds,args.seconds+1.)
    level=task.levels-1 if args.level is None else args.level
    if not 0<=level<task.levels:parser.error('Invalid level')
    args.enable_cameras=args.video or args.enable_cameras
    output=output_directory(args.output,'play');app=AppLauncher(args).app;env=None;writer=None
    report=dict(status='failed',checkpoint=str(args.checkpoint.resolve()),level=level,startup_overrides=overrides,effective_startup=dict(reset_settle_seconds=task.reset_settle_seconds,startup_action_ramp_seconds=task.startup_action_ramp_seconds),cases=[])
    try:
        import torch,gymnasium as gym,numpy as np,json,imageio.v2 as imageio
        from PIL import Image,ImageDraw
        from nav_skill2.tasks.direct.nav_skill2.commands import motion_terms
        import nav_skill2.tasks
        from nav_skill2.tasks.direct.nav_skill2.nav_skill2_env_cfg import make_env_config
        from nav_skill2.learning.ppo import ActorCritic
        torch.set_num_threads(4)
        cfg=make_env_config(task,args.device);cfg.sim.render_interval=20;cfg.viewer.resolution=(640,480)
        env=gym.make('Isaac-Nav-Skill2-Go2-Piper-v0',cfg=cfg,render_mode='rgb_array' if args.video else None).unwrapped
        model=ActorCritic().to(env.device);model.load_state_dict(saved['model']);model.eval()
        speed=min(.3,task.speed_limits[level]);turn=min(.5,task.yaw_rate_limits[level])
        lateral=min(speed,task.lateral_speed_limits[level])
        cases=[('forward',[speed,0.,0.]),('backward',[-speed,0.,0.]),('left',[0.,lateral,0.]),('right',[0.,-lateral,0.]),('turn_left',[0.,0.,turn]),('turn_right',[0.,0.,-turn]),('arc',[speed*.6,0.,turn])] if args.suite else [('custom',args.command)]
        original_reset=env._reset_idx
        writer=imageio.get_writer(str(output/'locomotion.mp4'),fps=10,codec='libx264',quality=7) if args.video else None
        with (output/'trace.jsonl').open('w') as trace,torch.inference_mode():
            for name,command in cases:
                env._reset_idx=original_reset;env.manual_commands=True;env.levels[:]=level
                env.reset()
                pose=env.robot.data.root_state_w[:,:7].clone();pose[:,3:7]=env.settled_root[:,3:7] if env.settled_root is not None else pose.new_tensor([1.,0.,0.,0.])
                env.robot.write_root_pose_to_sim(pose);env.fresh[:]=True
                env.set_velocity_command([0.,0.,0.]);obs=env._get_observations()
                env._reset_idx=lambda ids:None
                failed=False;max_tilt=0.;max_arm=0.;frames=0;moving_errors=[];stop_errors=[];responses=[];good_samples=[]
                start_time=min(2.,args.seconds*.15);stop_time=max(start_time,args.seconds-min(5.,args.seconds*.25))
                for step in range(math.ceil(args.seconds/env.step_dt)):
                    t=step*env.step_dt
                    desired=command if start_time<=t<stop_time and not failed else [0.,0.,0.]
                    env.set_velocity_command(desired)
                    # 本步指令平滑要到下一次观测才能影响动作，保存实际生效指令用于误差核对。
                    applied_command=env.commands[0].clone()
                    action=model.actor(obs['policy'])
                    if failed:action.zero_()
                    obs,reward,terminated,truncated,info=env.step(action)
                    vel=env.robot.data.root_lin_vel_b[0];omega=env.robot.data.root_ang_vel_b[0]
                    error=(vel[:2]-applied_command[:2]).square().sum()+.25*(omega[2]-applied_command[2]).square()
                    if start_time+1.<t<stop_time:
                        moving_errors.append(float(error))
                        _,response,good=motion_terms(applied_command[None],vel[None],omega[None])
                        responses.append(float(response[0]));good_samples.append(bool(good[0]))
                    if t>stop_time+1.:stop_errors.append([float(vel[:2].norm()),float(omega[2].abs()),float((env.robot.data.joint_pos[0,env.joint_ids[:12]]-env.reference[0,:12]).square().mean().sqrt())])
                    tilt=float(torch.acos((-env.robot.data.projected_gravity_b[0,2]).clamp(-1,1)))
                    arm=float(env.robot.data.joint_pos[0,env.joint_ids[12:]].abs().max());max_tilt=max(max_tilt,tilt);max_arm=max(max_arm,arm)
                    failed|=bool(env.failure[0])
                    contact=(env.contact.data.net_forces_w[0,env.contact_feet].norm(dim=-1)>3.).cpu().tolist()
                    trace.write(json.dumps(dict(case=name,t=t+env.step_dt,desired_command=desired,applied_command=applied_command.cpu().tolist(),commands=env.commands[0].cpu().tolist(),position=env.robot.data.root_pos_w[0].cpu().tolist(),linear_velocity=vel.cpu().tolist(),angular_velocity=omega.cpu().tolist(),tilt_deg=math.degrees(tilt),arm_error=arm,feet_contact=contact,policy_action=action[0].cpu().tolist(),executed_action=env.actions[0].cpu().tolist(),joint_target=env.targets[0].cpu().tolist(),joint_position=env.robot.data.joint_pos[0,env.joint_ids].cpu().tolist(),torque=env.robot.data.applied_torque[0,env.joint_ids].cpu().tolist(),failed=failed))+'\n')
                    if writer and step%5==0:
                        pos=env.robot.data.root_pos_w[0].cpu().numpy()
                        env.sim.set_camera_view((pos+np.array([2.4,2.4,1.5])).tolist(),(pos+np.array([0.,0.,.1])).tolist())
                        canvas=Image.fromarray(env.render()).convert('RGB');draw=ImageDraw.Draw(canvas);draw.rectangle((0,0,640,80),fill='black')
                        draw.text((8,5),f'Nav2 velocity | iter={saved["iteration"]} level={level} | {name} {t:.1f}s',fill='white')
                        draw.text((8,24),f'cmd={applied_command.cpu().tolist()} actual=({float(vel[0]):.2f},{float(vel[1]):.2f},{float(omega[2]):.2f})',fill='white')
                        draw.text((8,43),f'tilt={math.degrees(tilt):.1f} arm={arm:.3f} feet={contact}',fill='white')
                        draw.text((8,62),'FAILURE' if failed else ('STOPPING / STANDING' if t>=stop_time else 'VELOCITY TRACKING'),fill='red' if failed else 'white')
                        writer.append_data(np.asarray(canvas));frames+=1
                    if not app.is_running():raise RuntimeError('Viewer closed before completion')
                stop_mean=np.mean(stop_errors,axis=0).tolist() if stop_errors else None
                response_mean=float(np.mean(responses)) if responses else None
                good_fraction=float(np.mean(good_samples)) if good_samples else None
                qualified=not failed and response_mean is not None and response_mean>=task.curriculum_response and good_fraction>=task.curriculum_good_fraction and stop_mean is not None and stop_mean[0]<.1 and stop_mean[1]<.2
                report['cases'].append(dict(directional_response=response_mean,good_motion_fraction=good_fraction,motion_and_stop_qualified=qualified,name=name,command=command,result='failure' if failed else 'completed_without_fall',seconds=args.seconds,tracking_weighted_rmse=math.sqrt(sum(moving_errors)/len(moving_errors)) if moving_errors else None,stop_mean_speed_yaw_posture=stop_mean,max_tilt_deg=math.degrees(max_tilt),max_arm_error=max_arm,frames=frames))
        env._reset_idx=original_reset
        report.update(status='complete',note='Velocity development cases; completed_without_fall does not prove tracking quality or formal acceptance.')
    except BaseException as exc:report['error']=repr(exc);raise
    finally:
        if writer:writer.close()
        write_json(output/'report.json',report)
        if env is not None:env.close()
        app.close()

if __name__=='__main__':main()
