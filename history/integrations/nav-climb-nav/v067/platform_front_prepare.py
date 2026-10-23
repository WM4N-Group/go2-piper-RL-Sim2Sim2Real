"""Additional real front footsteps for NAV stance, after independent CLIMB.
Reuse original 8cm-bounded platform extension and unchanged swing/load gates.
No physics writes, command-reference resets or actuator-history changes.
"""
import json
import torch
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.crawl_gait import PlatformFrontExtension
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_climb_stages import StageClimbAction
from climb_handoff import sample
class PlatformFrontPrepare:
 def __init__(self,t,age,nav_snapshot):
  self.t=t;self.start=age;self.stable=0.;self.done=False;self.initial=t._asset.data.joint_pos_target[:,t._joint_ids].clone()
  self.original_final_adjust=t.cfg.platform_final_adjust
  feet=t.feet_positions();origin=t._env.scene.env_origins
  navroot=feet.new_tensor(nav_snapshot['root_position'])[None]
  navfeet=feet.new_tensor(nav_snapshot['feet'])[None]
  body_x=(feet[:,2:,0]-(navfeet[:,2:,0]-navroot[:,None,0])).amax(1)
  desired=body_x[:,None]+navfeet[:,:2,0]-navroot[:,None,0]
  deficit=desired-feet[:,:2,0]
  # One additional pair, within the original per-foot extension contract.
  self.distance=min(.08,max(0.,float(deficit.max())))
  self.enabled=self.distance>.04
  record=dict(time_s=age,scope='Independent NAV stance preparation after CLIMBcomplete',enabled=self.enabled,distance_m=self.distance,nominal_body_x=(body_x-origin[:,0]).tolist(),front_native_deficit=deficit[0].tolist(),prior_extension_completed=int(t.extension.completed[0]),initial_reference=self.initial[0].tolist())
  (t.entry_output/'nav-front-prepare-plan.json').write_text(json.dumps(record,indent=2)+'\n')
  if not self.enabled:self.done=True;return
  assert bool(t.platform_hold.all()) and int(t.extension.completed[0])==2 and not bool(t.extension.moving.any()) and not bool(t.pending.any())
  t.extension=PlatformFrontExtension(t._env.num_envs,t._env.device,self.distance)
  t.cfg.platform_final_adjust=False
  t.guidance.capture_hold(torch.ones(t._env.num_envs,device=t._env.device,dtype=torch.bool))
 def target(self,actions,age):
  t=self.t
  if abs(age-self.start)<1e-8:return self.initial.clone()
  StageClimbAction.process_actions(t,torch.zeros_like(actions))
  return t._processed_actions.clone()
 def observe(self,age,forces,no_failure):
  t=self.t;r=t._asset;c=sample(t)
  stopped=bool(r.data.root_lin_vel_w.norm()<.025 and r.data.root_ang_vel_w.norm()<.1 and (forces[:,2]>=8.).all() and r.data.joint_vel[:,[t._joint_ids[i] for i in t.leg_slots]].abs().max()<.35 and r.data.joint_vel[:,t.arm_ids].abs().max()<.2)
  ready=bool(t.platform_hold.all()) and int(t.extension.completed[0])==2 and not bool(t.extension.moving.any()) and float(t.guidance.age[0])>=2. and float((t.guidance.target-r.data.root_pos_w).norm())<.01 and bool(t.guidance.valid_legs.all()) and float(t.guidance.command_limit_excess.max())<1e-6 and stopped and no_failure
  self.stable=self.stable+t._env.step_dt if ready else 0.
  self.done=self.stable>=1.
  if self.done:t.cfg.platform_final_adjust=self.original_final_adjust
  detail=dict(time_s=age,phase='platform_front_stance_prepare',elapsed_s=age-self.start,distance_m=self.distance,stable_s=self.stable,done=self.done,loaded_stopped=stopped,stage=c)
  with (t.entry_output/'nav-front-prepare.jsonl').open('a') as f:f.write(json.dumps(detail)+'\n')
  return detail
