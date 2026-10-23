"""真实物理：随机化承重缓存、重复reset、18维目标和观测合同；不作策略验收。"""
import argparse,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source/nav_skill2'))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--num-envs',type=int,default=32);AppLauncher.add_app_launcher_args(p);args=p.parse_args()
app=AppLauncher(args).app;env=None
try:
 import torch,gymnasium as gym
 torch.set_num_threads(4)
 import nav_skill2.tasks
 from nav_skill2.tasks.direct.nav_skill2.parameters import load_config
 from nav_skill2.tasks.direct.nav_skill2.nav_skill2_env_cfg import make_env_config
 task,_=load_config(Path(__file__).resolve().parents[1]/'configs/nav.json');task.num_envs=args.num_envs
 env=gym.make('Isaac-Nav-Skill2-Go2-Piper-v0',cfg=make_env_config(task,args.device)).unwrapped
 env.manual_commands=True;worst_drop=0.;worst_vz=0.;peak_tilt=0.
 for repeat in range(3):
  env.reset();env.set_velocity_command([0.,0.,0.])
  initial=env.robot.data.root_pos_w[:,2].clone()
  for step in range(40):
   obs,*_=env.step(torch.zeros(args.num_envs,18,device=env.device))
   worst_drop=max(worst_drop,float((initial-env.robot.data.root_pos_w[:,2]).max()))
   worst_vz=max(worst_vz,float(env.robot.data.root_lin_vel_w[:,2].abs().max()))
   peak_tilt=max(peak_tilt,float(torch.acos((-env.robot.data.projected_gravity_b[:,2]).clamp(-1,1)).max()))
   assert not bool(env.failure.any())
   assert obs['policy'].shape==(args.num_envs,315) and obs['critic'].shape==(args.num_envs,324)
   assert not bool(env.actions[:,12:].any()) and not bool(env.targets[:,12:].any())
   torch.testing.assert_close(env.reference,env.robot.data.default_joint_pos[:,env.joint_ids])
 assert worst_drop<.01,(worst_drop,worst_vz,peak_tilt)
 assert worst_vz<.15,(worst_drop,worst_vz,peak_tilt)
 assert peak_tilt<task.reset_settle_max_tilt,(worst_drop,worst_vz,peak_tilt)
 # 回合末只平滑清零指令；调用上层手动速度接口时不擅自清零。
 env.reset();env.manual_commands=False
 tail=round((task.episode_seconds-task.terminal_stop_seconds)/env.step_dt)
 env.episode_length_buf[:]=tail;env.commands[:,0]=.3;env.desired_commands[:,0]=.3;env.standing[:]=False
 env.command_last_elapsed[:]=(tail-1)*env.step_dt;env.command_deadline[:]=1e6;env.command_stamp=-1
 env._update_commands()
 assert not bool(env.desired_commands.any()) and bool(env.standing.all())
 assert bool((env.commands[:,0]>.28).all()),'Brake must be smooth, not a command jump'
 stamp=env.command_sample_time.clone();env.episode_length_buf+=1;env.command_stamp=-1;env._update_commands()
 torch.testing.assert_close(stamp,env.command_sample_time)
 env.set_velocity_command([.3,0.,0.]);env.episode_length_buf+=1;env.command_stamp=-1;env._update_commands()
 assert bool((env.desired_commands[:,0]==.3).all()) and not bool(env.standing.any())
 result=dict(status='passed',num_envs=args.num_envs,terminal_stop_checks=True,settle_actual_seconds=env.settle_elapsed_seconds,resets=3,seconds_per_reset=.8,randomization=True,settle_seconds=3.,action_ramp_seconds=2.,worst_height_drop=worst_drop,max_absolute_vertical_speed=worst_vz,max_tilt_rad=peak_tilt,note='Zero-policy support/reset fixture, not trained locomotion acceptance')
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2));print(result,flush=True)
except BaseException as exc:
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(dict(status='failed',error=repr(exc)),indent=2));print(f'STARTUP CHECK FAILED: {exc!r}',flush=True);raise
finally:
 if env is not None:env.close()
 app.close()
