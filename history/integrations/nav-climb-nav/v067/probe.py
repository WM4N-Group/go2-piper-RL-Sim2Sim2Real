"""Original-reset NAV in the frozen CLIMB scene; entry characterization only."""
from pathlib import Path
import argparse,copy,json,hashlib,traceback
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--nav-actor',type=Path,required=True);p.add_argument('--seed',type=int,default=3701);p.add_argument('--seconds',type=float,default=32.);AppLauncher.add_app_launcher_args(p);a=p.parse_args()
assert not a.output.exists();a.output.mkdir(parents=True);launcher=AppLauncher(a)
import torch,gymnasium as gym,isaaclab_tasks
from isaaclab_tasks.utils import load_cfg_from_registry
import LeggedManip_Lab.tasks
from isaaclab.managers import TerminationTermCfg as DoneTerm
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_climb_stages import StageClimbAction
from native_arm_effort_guard import guard_reference
from supported_brake import SupportedBrake, brake_precheck
from climb_handoff import activate as activate_climb, sample as climb_sample
from piper_climb_completion import ClimbCompletion
from platform_nav_exit import PlatformNavExit,PlatformExitRejected
from ground_entry_guidance import EntryPlanningRejected

from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_climb import BoxSettled
class NativeClimbSuccessEvent(BoxSettled):
 """Keep the original predicate/hold counter as an event for continuous control."""
 def __call__(self,env,asset_cfg,sensor_cfg,hold_time=1.0):
  native=super().__call__(env,asset_cfg=asset_cfg,sensor_cfg=sensor_cfg,hold_time=hold_time)
  env.transition_native_climb_success=native.clone()
  return torch.zeros_like(native)

class TerminalStop(Exception):pass

def issued_actions(env):
 t=env.action_manager.get_term('joint_pos')
 return getattr(t,'issued',torch.zeros((env.num_envs,18),device=env.device))

def pose_request(env):return torch.tensor([.5,0.,.2,1.,0.,0.,0.],device=env.device).repeat(env.num_envs,1)

def velocity_request(env):
 t=env.action_manager.get_term('joint_pos');r=env.scene['robot'];step=int(env.episode_length_buf[0]);age=step*env.step_dt
 if hasattr(t,'platform_exit'):return t.platform_exit.command_request()
 target=torch.tensor([.35,0.],device=env.device);pos=(r.data.root_pos_w-env.scene.env_origins)[:,:2];err=target-pos
 w,x,y,z=r.data.root_quat_w.unbind(-1);yaw=torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
 near=err.norm(dim=1)<.05
 world=1.2*err
 vx=world[:,0]*torch.cos(yaw)+world[:,1]*torch.sin(yaw);vy=-world[:,0]*torch.sin(yaw)+world[:,1]*torch.cos(yaw)
 cap=torch.sqrt(2*.10*(err[:,0]-.02).clamp(min=0.)).clamp(max=.15)
 desired=torch.stack((torch.where(near,0.,torch.minimum(vx,cap).clamp(-.10,.15)),torch.where(near,0.,vy.clamp(-.08,.08)),torch.where(yaw.abs()<.04,0.,(-yaw).clamp(-.2,.2))),dim=1)
 if age<6. or hasattr(t,'supported_brake'):desired[:]=0.
 if not hasattr(t,'request_step'):t.request_step=step;t.request=torch.zeros_like(desired)
 if step>t.request_step:
  delta=(step-t.request_step)*env.step_dt*torch.tensor([.10,.10,.25],device=env.device)
  t.request+=torch.maximum(torch.minimum(desired-t.request,delta),-delta);t.request_step=step
 return t.request.clone()

class EntryAction(StageClimbAction):
 def choose_leg(self,feet):
  chosen=super().choose_leg(feet)
  local=feet-self._env.scene.env_origins[:,None]
  ground=(local[...,2]<.10).all(1)&(local[...,0]<.75).all(1)
  if getattr(self,'entry_rear_preparation',False):
   needs=local[...,0]<local.new_tensor([.58,.58,.14,.14])
   prepared=needs.to(torch.int64).argmax(1)
  else:
   needs=local[:,:2,0]<.58
   prepared=torch.where(needs[:,0],torch.zeros_like(chosen),torch.ones_like(chosen))
  return torch.where(ground&needs.any(1),prepared,chosen)
 def reset(self,env_ids=None):
  super().reset(env_ids)
  # Same reset target synchronization as preserved v212/v196. No joint/root
  # state write, actuator reset, delay resampling, or mid-episode queue reset.
  r=self._asset;selected=slice(None) if env_ids is None else env_ids
  position=r.data.joint_pos[selected].clone()
  r.set_joint_position_target(position,env_ids=env_ids)
  r.set_joint_velocity_target(torch.zeros_like(position),env_ids=env_ids)
  r.set_joint_effort_target(torch.zeros_like(position),env_ids=env_ids)
 def process_actions(self,actions):
  r=self._asset;ids=self._joint_ids;age=float(self._env.episode_length_buf[0])*self._env.step_dt
  if not hasattr(self,'initial_target'):
   self.initial_target=r.data.joint_pos[:,ids].clone()
   # Original-reset target buffer is not initialized by this task. Seed from
   # measured reset q, as the frozen CLIMB reference does; never all-zero legs.
   self.issued=torch.zeros_like(actions)
   self.arm_slots=[i for i,j in enumerate(ids) if r.joint_names[j].startswith('joint')]
   self.arm_ids=[ids[i] for i in self.arm_slots];self.leg_slots=[i for i in range(18) if i not in self.arm_slots]
   pd=[]
   for field in ['stiffness','damping','effort_limit']:
    values=[]
    for j in self.arm_ids:
     act=next(v for v in r.actuators.values() if j in v.joint_indices);values.append(getattr(act,field)[:,list(act.joint_indices).index(j)])
    pd.append(torch.stack(values,dim=1))
   self.arm_pd=pd
  if hasattr(self,'platform_exit'):
   self.platform_exit.process(actions,age);return
  if getattr(self,'climb_active',False):
   # Adapt only the initial front ground step to the measured NAV stance.
   # The original selector, support preview, real landing and reload gates remain.
   feet=self.feet_positions();leg=int(self.choose_leg(feet)[0])
   local=feet[0,leg]-self._env.scene.env_origins[0]
   allground=bool(((feet[0]-self._env.scene.env_origins[0])[:,2]<.10).all())
   threshold=.58 if leg<2 else .14
   goal=.60 if leg<2 else .15
   initial_ground=(leg<2 or allground) and float(local[0])<threshold and float(local[2])<.10
   self.cfg.stride=min(.12,max(.03,goal-float(local[0]))) if initial_ground else .22
   previous_leg=int(self.clock.leg[0]);previous_progress=float(self.clock.progress[0])
   try:super().process_actions(actions)
   except EntryPlanningRejected:
    # Rechoose the next step only at the original verified landing boundary.
    # No forced advance, no reference reseed, no simulator or delay-buffer reset.
    feet=self.feet_positions();local=feet-self._env.scene.env_origins[:,None]
    forces=self._env.scene['contact_forces'].data.net_forces_w[:,self.sensor_ids,2]
    old_reload=float(self.guidance.landing_contact.reload[0]);old_loaded=float(self.guidance.landing_contact.loaded_age[0])
    eligible=(bool(self.last_advance[0]) and previous_progress==1. and float(self.clock.progress[0])==0.
      and float(self.clock.elapsed[0])==0. and not bool(self.clock.lifted[0])
      and bool((local[...,2]<.10).all()) and bool((local[...,0]<.75).all())
      and int(self.clock.leg[0])<2 and float(self.landing[0,2]-self.start[0,2])>.1
      and bool((local[0,:2,0]>=.58).all()) and bool((local[0,2:,0]<.14).any())
      and bool((forces>=8.).all()) and old_reload>=1. and old_loaded>=.19999
      and float(r.data.root_lin_vel_w.norm())<.025 and float(r.data.root_ang_vel_w.norm())<.1
      and not getattr(self,'entry_rear_preparation',False))
    if not eligible:raise
    self.entry_rear_preparation=True;selected=self.choose_leg(feet)
    assert int(selected[0])>=2
    old_index=int(self.clock.index[0]);self.clock.index[:]=self.clock.order.argsort()[selected]
    self.start[:]=feet[self.rows,self.clock.leg];self.landing[:]=self.start
    x=float(local[0,int(selected[0]),0]);self.cfg.stride=min(.12,max(.03,.15-x))
    self.landing[:,0]+=self.cfg.stride;self.landing[:,2]=self._env.scene.env_origins[:,2]+.024
    self.foot_reference[:]=self.start;self.best_lift[:]=0.
    from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import stage_swing_inset
    self.swing_inset[:]=stage_swing_inset(self.start,self.landing,self.clock.leg,self._env.scene.env_origins,feet,self.contacts(),self.cfg.last_rear_swing_inset)
    record=dict(time_s=age,reason='direct first-front ascent infeasible after verified reload',previous_landed_leg=previous_leg,previous_progress=previous_progress,previous_reload=old_reload,previous_loaded_age=old_loaded,force_z=forces[0].tolist(),selected_leg=int(selected[0]),old_clock_index=old_index,elapsed=float(self.clock.elapsed[0]),reference=self.reference[0].tolist(),reference_velocity=self.reference_velocity[0].tolist(),feet=local[0].tolist(),landing=(self.landing[0]-self._env.scene.env_origins[0]).tolist())
    with (self.entry_output/'ground-reselection-events.jsonl').open('a') as out:out.write(json.dumps(record)+'\n')
    self.guidance.capture(torch.ones(self._env.num_envs,dtype=torch.bool,device=self._env.device))
    super().process_actions(actions)
   self.issued=(self._processed_actions-r.data.default_joint_pos[:,ids])/.25
   self.guard=dict(scope='Frozen iy StageClimbAction with unchanged reference and physical substep gates')
   return
  if hasattr(self,'supported_brake'):
   desired=self.supported_brake.target(age)
   self.issued=(desired-r.data.default_joint_pos[:,ids])/.25
   self._raw_actions[:]=actions.clamp(-10.,10.);self._processed_actions[:]=desired
   self.guard=dict(scope='supported brake bounded reference; original actual substep safety active')
   return
  if age>=2. and not hasattr(self,'nav_authority_started'):
   self.initial_target=r.data.joint_pos_target[:,ids].clone()
   self.nav_authority_started=True
  raw=actions.clamp(-10.,10.);default=r.data.default_joint_pos[:,ids];native=default+.25*raw
  u=max(0.,min(1.,(age-2.)/1.));blend=u**3*(10-15*u+6*u*u)
  desired=self.initial_target+blend*(native-self.initial_target)
  # Retain frozen NAV leg feedback from first command to arrest initial body drop.
  # Arm startup retains v010 gravity reference; source PD/queues/state unchanged.
  desired[:,self.leg_slots]=native[:,self.leg_slots]
  u=max(0.,min(1.,(age-2.)/4.));blend=u**3*(10-15*u+6*u*u)
  desired[:,self.arm_slots]=self.initial_target[:,self.arm_slots]+blend*(native[:,self.arm_slots]-self.initial_target[:,self.arm_slots])
  if age<2.:
   gravity=r.root_physx_view.get_gravity_compensation_forces().to(self._env.device)
   columns=self.arm_ids if gravity.shape[1]==r.num_joints else [j+6 for j in self.arm_ids]
   u=min(1.,age/.08);load_blend=u**3*(10.-15.*u+6.*u*u)
   desired[:,self.arm_slots]=self.initial_target[:,self.arm_slots]+load_blend*gravity[:,columns]/self.arm_pd[0]
  if age>=6.:desired=native.clone()
  bounds=r.data.soft_joint_pos_limits[:,self.arm_ids]
  if age>=6.:
   try:guarded,details=guard_reference(desired[:,self.arm_slots],r.data.joint_pos[:,self.arm_ids],r.data.joint_vel[:,self.arm_ids],*self.arm_pd,bounds[...,0],bounds[...,1])
   except ValueError:
    (a.output/'guard-infeasible.json').write_text(json.dumps(dict(age=age,q=r.data.joint_pos[0,self.arm_ids].tolist(),dq=r.data.joint_vel[0,self.arm_ids].tolist(),target=desired[0,self.arm_slots].tolist(),limits=bounds[0].tolist(),pd=[v[0].tolist() for v in self.arm_pd]),indent=2))
    raise
  else:
   # Match the existing NAV ingress contract: finite initialization/authority
   # ramp first, forecast guard only after full authority. Actual substep gate
   # remains active from the first physics step.
   guarded=torch.maximum(torch.minimum(desired[:,self.arm_slots],bounds[...,1]),bounds[...,0])
   details=dict(scope='initialization/finite NAV authority, actual substep gate active',changed=bool((guarded!=desired[:,self.arm_slots]).any()))
  desired[:,self.arm_slots]=guarded
  self.guard=details;self.issued=(desired-default)/.25
  self.issued[:,self.leg_slots]=raw[:,self.leg_slots]
  if age>=6.:self.issued[:,self.arm_slots]=torch.where(guarded==native[:,self.arm_slots],raw[:,self.arm_slots],self.issued[:,self.arm_slots])
  self._raw_actions[:]=raw;self._processed_actions[:]=default+.25*self.issued
  # Keep the CLIMB controller unengaged: this probe only measures the real NAV endpoint.

def effort_violation(env):return getattr(env,'entry_effort_failure',torch.zeros(env.num_envs,dtype=torch.bool,device=env.device))

def main():
 D=Path(__file__).resolve().parent;manifest=json.loads((D/'plan.json').read_text());source_plan=json.loads((a.source.parent/'plan.json').read_text())
 for n,h in source_plan['source_sha256'].items():assert hashlib.sha256((a.source/n).read_bytes()).hexdigest()==h,n
 assert hashlib.sha256(a.nav_actor.read_bytes()).hexdigest()=='72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8'
 cfg=load_cfg_from_registry('GO2-PIPER-Box-Climb-Stages-Play','env_cfg_entry_point');cfg.scene.num_envs=1;cfg.seed=a.seed;cfg.sim.device=a.device;cfg.episode_length_s=a.seconds
 assert not cfg.climb_stage_bank and cfg.events.reset_climb_stages is None
 assert cfg.terminations.box_settled.func is BoxSettled
 cfg.terminations.box_settled.func=NativeClimbSuccessEvent
 cfg.actions.joint_pos.class_type=EntryAction
 navcfg=load_cfg_from_registry('GO2-PIPER-Flat-Play','env_cfg_entry_point')
 cfg.observations.policy.enable_corruption=False
 cfg.observations.nav_policy=copy.deepcopy(navcfg.observations.policy);cfg.observations.nav_policy.enable_corruption=False
 cfg.observations.nav_policy.actions.func=issued_actions;cfg.observations.nav_policy.actions.params={}
 cfg.observations.nav_policy.velocity_commands.func=velocity_request;cfg.observations.nav_policy.velocity_commands.params={}
 cfg.observations.nav_policy.pos_commands.func=pose_request;cfg.observations.nav_policy.pos_commands.params={}
 cfg.terminations.transition_effort=DoneTerm(func=effort_violation)
 for name in vars(cfg.rewards):
  v=getattr(cfg.rewards,name)
  if hasattr(v,'weight'):v.weight=0.
 env=gym.make('GO2-PIPER-Box-Climb-Stages-Play',cfg=cfg);b=env.unwrapped;obs,_=env.reset(seed=a.seed);r=b.scene['robot'];t=b.action_manager.get_term('joint_pos');ids=t._joint_ids
 actor=torch.jit.load(str(a.nav_actor),map_location=a.device).eval();assert obs['nav_policy'].shape==(1,210)
 climb_actor_path=a.source.parent.parent/'climb-crawl-20261001-d/stand_actor304.pt'
 assert hashlib.sha256(climb_actor_path.read_bytes()).hexdigest()=='d9673b2b49f5dce08d844a1de81a3a37e7f90e85d20b86489a5751b8aa2b1dee'
 climb_actor=torch.jit.load(str(climb_actor_path),map_location=a.device).eval()
 assert obs['policy'].shape==(1,304)
 completion=ClimbCompletion()

 rep=dict(scope='Original-reset continuous NAV to frozen iy CLIMB;420s extended diagnostic with real extra front steps for NAV stance',seed=a.seed,physical_resets_after_initial=0,outcome='incomplete',termination={},events=[],max_substep_arm_effort=0.,max_substep_joint_effort=0.,airborne_samples=0,under_three_support_samples=0,max_abs_vz=0.,max_foot_force=0.,max_sum_force=0.,steps=0,source12_verified=True)
 arm_ids=r.find_joints(['joint[1-6]'],preserve_order=True)[0];footids=b.scene['contact_forces'].find_bodies(['FL_foot','FR_foot','RL_foot','RR_foot'],preserve_order=True)[0]
 def stop(env_ids,*args,**kwargs):
  if len(env_ids):
   rep['termination']={n:bool(b.termination_manager.get_term(n)[0]) for n in b.termination_manager.active_terms};raise TerminalStop()
 b.recorder_manager.record_pre_reset=stop
 original_update=b.scene.update
 def update(dt):
  original_update(dt);ratio=(r.data.applied_torque.abs()/r.data.joint_effort_limits);arm=float(ratio[:,arm_ids].max());rep['max_substep_arm_effort']=max(rep['max_substep_arm_effort'],arm);rep['max_substep_joint_effort']=max(rep['max_substep_joint_effort'],float(ratio.max()))
  if arm>=.98:
   b.entry_effort_failure=torch.ones(1,dtype=torch.bool,device=b.device)
   rep.setdefault('first_effort_violation',dict(control_step=int(b.episode_length_buf[0]),ratio=arm,q=r.data.joint_pos[0,arm_ids].tolist(),dq=r.data.joint_vel[0,arm_ids].tolist(),torque=r.data.applied_torque[0,arm_ids].tolist()))
 b.scene.update=update
 (a.output/'actuator-contract.json').write_text(json.dumps(dict(joint_names=[r.joint_names[i] for i in ids],default=r.data.default_joint_pos[0,ids].tolist(),actuators={n:{k:str(getattr(v,k,None)) for k in ['stiffness','damping','min_delay','max_delay','effort_limit']} for n,v in r.actuators.items()}),indent=2))
 (a.output/'initial-state.json').write_text(json.dumps(dict(q=r.data.joint_pos[0,ids].tolist(),pd_target=r.data.joint_pos_target[0,ids].tolist(),root_position=(r.data.root_pos_w[0]-b.scene.env_origins[0]).tolist(),feet=(t.feet_positions()[0]-b.scene.env_origins[0]).tolist()),indent=2))
 stable=0.;converted_stable=0.;log=(a.output/'control.jsonl').open('x')
 try:
  with torch.inference_mode():
   for i in range(round(a.seconds/b.step_dt)):
    inp=obs['nav_policy'].clone();source_input=obs['policy'].clone() if getattr(t,'climb_active',False) else None
    action=(climb_actor(source_input) if source_input is not None else actor(inp)).clamp(-10.,10.);terminal=False
    if source_input is not None:assert action.shape==(1,18) and bool((action==0.).all()),'Frozen CLIMB actor residual contract changed'

    try:obs,*_=env.step(action)
    except TerminalStop:terminal=True
    f=b.scene['contact_forces'].data.net_forces_w[0,footids];pos=r.data.root_pos_w[0]-b.scene.env_origins[0];feet=t.feet_positions()[0]-b.scene.env_origins[0]
    w,x,y,z=r.data.root_quat_w[0];yaw=2*torch.atan2(z,w)
    gates=dict(position=float((pos[:2]-torch.tensor([.35,0.],device=b.device)).norm())<.05,orientation=abs(float(yaw))<.12 and float(r.data.projected_gravity_b[0,2])<-.98,loaded=bool((f[:,2]>=8).all()),stopped=float(r.data.root_lin_vel_w[0].norm())<.025 and float(r.data.root_ang_vel_w[0].norm())<.1,legs_slow=float(r.data.joint_vel[0,[ids[j] for j in t.leg_slots]].abs().max())<.35,arm_slow=float(r.data.joint_vel[0,arm_ids].abs().max())<.2,feet_before_edge=bool((feet[:,0]<.70).all()),no_failure=not any(v for k,v in rep['termination'].items() if k!='time_out'))
    stable=stable+b.step_dt if all(gates.values()) and i>=300 else 0.
    row=dict(step=int(b.episode_length_buf[0]),time_s=float(b.episode_length_buf[0])*b.step_dt,root_position=pos.tolist(),root_quaternion=r.data.root_quat_w[0].tolist(),q=r.data.joint_pos[0,ids].tolist(),dq=r.data.joint_vel[0,ids].tolist(),pd_target=r.data.joint_pos_target[0,ids].tolist(),feet=feet.tolist(),foot_forces=f.tolist(),nav_input=inp[0].tolist(),native_action=action[0].tolist(),issued_action=t.issued[0].tolist(),guard=t.guard,gates=gates,stable_s=stable)
    row['arm_conversion_stable_s']=converted_stable
    row.update(root_velocity=r.data.root_lin_vel_w[0].tolist(),root_angular_velocity=r.data.root_ang_vel_w[0].tolist(),velocity_request=t.request[0].tolist(),phase='climb' if getattr(t,'climb_active',False) else 'supported_brake' if hasattr(t,'supported_brake') else 'native_nav')
    if not terminal and row['time_s']>=6. and not hasattr(t,'supported_brake'):
     eligible,details=brake_precheck(t,f,gates);row['brake_precheck']=details
     if eligible:
      t.supported_brake=SupportedBrake(t,row['time_s'])
      rep['events'].append(dict(event='supported_braking_started_not_ready',time_s=row['time_s']))
    if hasattr(t,'supported_brake'):row['brake']=t.supported_brake.details
    if getattr(t,'climb_active',False):
     row['climb']=climb_sample(t)
     safe=not bool(getattr(b,'entry_effort_failure',torch.zeros(1,device=b.device,dtype=torch.bool))[0]) and not any(v for k,v in rep['termination'].items() if k not in ['time_out','box_settled'])
     row['climb_completion']=completion.update(row['climb'],time_s=row['time_s'],safety_ok=safe)
     row['climb_actor_input']=source_input[0].tolist() if source_input is not None else None
    if hasattr(t,'platform_exit') and not terminal:
     row['platform_exit']=t.platform_exit.observe(row['time_s'],f,gates['no_failure'])
     row['phase']=t.platform_exit.phase
    row['native_climb_task_success']=bool(getattr(b,'transition_native_climb_success',torch.zeros(1,device=b.device,dtype=torch.bool))[0])
    if row['native_climb_task_success'] and 'native_climb_task_success_time_s' not in rep:
     rep['native_climb_task_success_time_s']=row['time_s'];rep['events'].append(dict(event='original_task_success_predicate_observed_without_reset',time_s=row['time_s']))
    log.write(json.dumps(row)+'\n');log.flush();rep['steps']+=1
    count=int((f[:,2]>2.).sum());rep['airborne_samples']+=count==0;rep['under_three_support_samples']+=count<3;rep['max_abs_vz']=max(rep['max_abs_vz'],abs(float(r.data.root_lin_vel_w[0,2])));rep['max_foot_force']=max(rep['max_foot_force'],float(f.norm(dim=-1).max()));rep['max_sum_force']=max(rep['max_sum_force'],float(f.sum(0).norm()))
    if terminal:rep['outcome']='native_termination';break
    if hasattr(t,'platform_exit'):
     if t.platform_exit.rejection:
      rep['outcome']='platform_nav_exit_rejected';rep['exit_rejection']=t.platform_exit.rejection;rep['platform_exit_state']=row;break
     if t.platform_exit.complete:
      rep['outcome']='nav_climb_nav_platform_target_stable';rep['platform_exit_state']=row;break
     if row['time_s']-t.platform_exit.start>=120.:rep['outcome']='platform_nav_exit_timeout';break
     continue
    if getattr(t,'climb_active',False):
     if row['climb_completion']['complete']:
      rep['outcome']='climb_complete_exit_pending';rep['climb_completion_state']=row
      rep['events'].append(dict(event='live_independent_climb_complete',time_s=row['time_s']))
      t.platform_exit=PlatformNavExit(t,row['time_s'],rep['parking_state']);t.climb_active=False
      rep['events'].append(dict(event='platform_body_preparation_requested',time_s=row['time_s']))
     continue

    if stable>=.5 and hasattr(t,'supported_brake') and not hasattr(t.supported_brake,'conversion_start'):
     rep['parking_state']=row
     rep['events'].append(dict(event='nav_parking_stable_arm_conversion_started',time_s=row['time_s']))
     t.supported_brake.begin_arm_conversion(row['time_s'])
    if hasattr(t,'supported_brake') and hasattr(t.supported_brake,'conversion_start'):
     br=t.supported_brake
     final_reference=float((r.data.joint_pos_target[:,t.arm_ids]-br.conversion_goal).abs().max())<1e-4
     conversion_done=row['time_s']-br.conversion_start>=6. and final_reference and all(gates.values())
     converted_stable=converted_stable+b.step_dt if conversion_done else 0.
     if converted_stable>=1.:
      rep['arm_conversion_state']=row
      rep['events'].append(dict(event='original_climb_arm_reference_loaded_stable',time_s=row['time_s'],continuous_hold_s=converted_stable))
      t.entry_output=a.output
      activation=activate_climb(t,a.source)
      (a.output/'climb-activation.json').write_text(json.dumps(activation,indent=2)+'\n')
      rep['events'].append(dict(event='continuous_iy_climb_controller_activated',time_s=row['time_s']))
   else:rep['outcome']='entry_window_exhausted'
 except PlatformExitRejected as exc:
  rep['outcome']='platform_nav_exit_rejected';rep['exit_rejection']=str(exc)
 except EntryPlanningRejected as exc:
  rep['outcome']='entry_planning_rejected';rep['planning_rejection']=str(exc)
 except Exception:rep['outcome']='runtime_error';rep['error']=traceback.format_exc()
 finally:
  log.close();(a.output/'report.json').write_text(json.dumps(rep,indent=2)+'\n');env.close();print(json.dumps({k:v for k,v in rep.items() if k not in ['parking_state']}))
main();launcher.app.close()
