"""真实物理工程检查：零残差贴地站立、指令渐变、观测历史、课程隔离。不是训练效果验收。"""
import argparse,json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source/nav_skill2'))
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);AppLauncher.add_app_launcher_args(p);args=p.parse_args()
app=AppLauncher(args).app
env=None
try:
 import torch,gymnasium as gym
 torch.set_num_threads(4)
 import nav_skill2.tasks
 from nav_skill2.tasks.direct.nav_skill2.parameters import TaskConfig,FRAME,HISTORY
 from nav_skill2.tasks.direct.nav_skill2.nav_skill2_env_cfg import make_env_config
 task=TaskConfig(num_envs=4,randomization=False)
 env=gym.make('Isaac-Nav-Skill2-Go2-Piper-v0',cfg=make_env_config(task,args.device)).unwrapped
 env.manual_commands=True;env.reset();original_reset=env._reset_idx
 env.set_velocity_command([0.,0.,0.]);env._reset_idx=lambda ids:None
 peak=0.
 for i in range(250):
  obs,r,term,timeout,info=env.step(torch.zeros(4,18,device=env.device))
  assert obs['policy'].shape==(4,315) and obs['critic'].shape==(4,324)
  assert torch.isfinite(obs['policy']).all() and torch.isfinite(r).all()
  assert not bool(env.failure.any()),'Default zero residual stand failed'
  assert not bool(env.actions[:,12:].any()) and not bool(env.targets[:,12:].any())
  peak=max(peak,float(torch.acos((-env.robot.data.projected_gravity_b[:,2]).clamp(-1,1)).max()))
 assert not bool(env.success.any()),'Standing must not qualify locomotion curriculum'
 history=env.history.clone();env._get_observations();env._get_observations()
 assert torch.equal(history,env.history),'Repeated observations advanced history'
 env.set_velocity_command([-.2,.1,-.3]);env.set_velocity_command([.2,0.,.3]);previous=env.commands.clone()
 for i in range(20):
  obs,*_=env.step(torch.zeros(4,18,device=env.device))
  delta=(env.commands-previous).abs()
  assert bool((delta[:,:2]<=.01001).all()) and bool((delta[:,2]<=.02001).all())
  previous=env.commands.clone()
 assert bool((env.commands[:,0]>.1).all()) and bool((env.commands[:,2]>.2).all())
 assert bool((env.history[:,-1,-3:]==env.commands).all())
 # 人工设置统计检查升降级机制，不作为策略成绩。
 env._reset_idx=original_reset;env.failure[:]=False;env.linear_error_sq[:]=0.;env.yaw_error_sq[:]=0.;env.command_energy[:]=0.;env.motion_seconds[:]=0.;env.tracking_count[:]=200;env.wins[:]=2;env.levels[:]=0
 env._reset_idx(env.robot._ALL_INDICES)
 assert bool((env.levels==0).all()) and bool((env.wins==2).all())
 env.episode_length_buf[:]=1249;env.failure[:]=False;env.linear_error_sq[:]=.01;env.yaw_error_sq[:]=.01;env.command_energy[:]=2.;env.motion_seconds[:]=4.;env.tracking_count[:]=200;env.wins[:]=2
 env.response_count[:]=0.;env.response_count[:,1]=200.;env.response_sum[:]=0.;env.response_sum[:,1]=150.;env.good_count[:]=150.
 env._reset_idx(env.robot._ALL_INDICES)
 assert bool((env.levels==1).all()),'Good directional response did not advance curriculum'
 report=dict(status='passed',grounded_height=env.grounded_height,max_default_stand_tilt_deg=math.degrees(peak),actor_obs=315,critic_obs=324,zero_arm_output=True,smooth_commands=True,history_once_per_step=True,standing_cannot_promote=True,good_direction_response_can_promote=True,note='Engineering fixture; not trained gait/navigation acceptance')
 args.report.write_text(json.dumps(report,indent=2));print(report,flush=True)
except BaseException as exc:
 print('FIXTURE_ERROR',repr(exc),flush=True);raise
finally:
 if env is not None:env.close()
 app.close()
