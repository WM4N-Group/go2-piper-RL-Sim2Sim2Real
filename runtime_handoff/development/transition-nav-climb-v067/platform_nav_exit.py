"""Finite native NAV authority after measured independent CLIMB completion."""
import math
from nav_progress_request import ProgressMonitor
from nav_arrival_stop import ArrivalStopLatch
from nav_tracking_compensation import TrackingCompensation
import json
from nav_arm_reference_guard import ArmReferenceGuard,ArmReferenceInfeasible
import torch
from native_arm_effort_guard import guard_reference
from supported_brake import SupportedBrake,brake_precheck
from platform_nav_stance import PlatformNavStance
from platform_front_prepare import PlatformFrontPrepare

class PlatformExitRejected(Exception):pass

class PlatformNavExit:
 def __init__(self,t,age,nav_snapshot):
  self.progress_monitor=ProgressMonitor();self.progress_trigger_saved=False;self.arrival_stop=ArrivalStopLatch();self.tracking_compensation=TrackingCompensation()
  self.t=t;self.start=age;self.phase='platform_nav_blend';self.stable=0.;self.complete=False;self.rejection=None
  r=t._asset;self.initial_target=r.data.joint_pos_target[:,t._joint_ids].clone()
  self.origin=r.data.root_pos_w.clone();self.goal=self.origin.clone();self.goal[:,0]+=.12
  self.request_step=int(t._env.episode_length_buf[0]);self.brake=None;self.details={};self.native_samples=0;self.guarded_samples=0
  self.prep_brake=SupportedBrake(t,age);self.nav_start=None;self.prep_stable=0.;self.prep_goal=None
  self.nav_snapshot=nav_snapshot;self.front_prepare=PlatformFrontPrepare(t,age,nav_snapshot);self.body_prepare=None;self.arm_prepare_start=age
  self.phase='platform_front_stance_prepare'
  if self.front_prepare.done:self.start_body_prepare(age)
  self.check_platform()
 def start_body_prepare(self,age):
  self.body_prepare=PlatformNavStance(self.t,age,self.nav_snapshot);self.phase='platform_supported_body_prepare'
  if self.body_prepare.rejection:raise PlatformExitRejected(self.body_prepare.rejection)
 def check_platform(self,raise_on_failure=True):
  t=self.t;r=t._asset;feet=t.feet_positions()[0]-t._env.scene.env_origins[0]
  good=bool(((feet[:,0]>.80)&(feet[:,0]<1.85)&(feet[:,1].abs()<.50)&(feet[:,2]>.19)).all())
  if not good and raise_on_failure:raise PlatformExitRejected('Platform foot/edge domain violated')
  return good
 def command_request(self):
  t=self.t;r=t._asset;step=int(t._env.episode_length_buf[0]);age=step*t._env.step_dt
  err=self.goal[:,:2]-r.data.root_pos_w[:,:2];w,x,y,z=r.data.root_quat_w.unbind(-1)
  yaw=torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z));world=1.2*err
  vx=world[:,0]*yaw.cos()+world[:,1]*yaw.sin();vy=-world[:,0]*yaw.sin()+world[:,1]*yaw.cos()
  near=err.norm(dim=1)<.025;cap=torch.sqrt(2*.10*(err[:,0]-.01).clamp_min(0)).clamp(max=.08)
  assist=False
  if self.nav_start is not None and self.brake is None and age-self.nav_start>=1.:
   assist=self.progress_monitor.update(age,float(r.data.root_pos_w[0,0]),float(err[0,0]),float(t.request[0,0]))
   if assist and not self.progress_trigger_saved:
    (t.entry_output/'nav-progress-assist.json').write_text(json.dumps(self.progress_monitor.trigger,indent=2)+'\n');self.progress_trigger_saved=True
  # Normal cap remains .08. Only recorded persistent stagnation permits .12,
  # still reduced by the unchanged distance-braking law and .10m/s2 slew.
  forward_limit=.12 if assist else .08
  if assist:cap=torch.sqrt(2*.10*(err[:,0]-.01).clamp_min(0)).clamp(max=forward_limit)
  forward=torch.where(vx>0.,vx.clamp_min(forward_limit),vx) if assist else vx
  desired=torch.stack((torch.where(near,0.,torch.minimum(forward,cap).clamp(-.04,forward_limit)),torch.where(near,0.,vy.clamp(-.04,.04)),torch.where(yaw.abs()<.04,0.,(-yaw).clamp(-.1,.1))),-1)
  if self.nav_start is not None and self.brake is None:
   measured_forward=float((r.data.root_lin_vel_w[:,0]*yaw.cos()+r.data.root_lin_vel_w[:,1]*yaw.sin())[0])
   bias=self.tracking_compensation.update(age,float(r.data.root_pos_w[0,0]),float(err[0,0]),measured_forward,assist,self.arrival_stop.active)
   weight=((err[:,0]-.025)/.05).clamp(0.,1.)
   correction=bias*weight if measured_forward<float(cap[0]) else torch.zeros_like(weight)
   desired[:,0]=torch.where(desired[:,0]>0.,(desired[:,0]+correction).clamp(max=.20),desired[:,0])
   if self.tracking_compensation.event is not None:
    with (t.entry_output/'nav-tracking-compensation-events.jsonl').open('a') as f:f.write(json.dumps(self.tracking_compensation.event)+'\n')
  if self.nav_start is not None and self.brake is None:
   calm=bool(r.data.root_lin_vel_w.norm()<.025 and r.data.root_ang_vel_w.norm()<.1)
   stopped_request=bool(t.request.abs().max()<1e-6)
   entry_distance=.025;minimum_hold=1.
   travel=float((r.data.root_pos_w[:,:2]-self.origin[:,:2]).norm())
   if self.tracking_compensation.active and travel>=.06 and float(err[0,0])>0.:
    toward=max(0.,float((r.data.root_lin_vel_w[:,:2]*err).sum()/err.norm().clamp_min(1e-6)))
    ramp=min(2.,max(0.,float(t.request[0,0]))/.10)
    lead=max(toward*toward/(2.*.10),.5*toward*ramp)
    entry_distance=min(.08,.025+lead);minimum_hold=min(2.3,max(1.,ramp+.3))
   if self.arrival_stop.update(age,float(err.norm()),stopped_request,calm,entry_distance,minimum_hold):desired[:]=0.
   if self.arrival_stop.event is not None:
    with (t.entry_output/'nav-arrival-stop-events.jsonl').open('a') as f:f.write(json.dumps(self.arrival_stop.event)+'\n')
  if self.nav_start is None or self.brake is not None:desired[:]=0.
  if step>self.request_step:
   allowance=(step-self.request_step)*t._env.step_dt*desired.new_tensor([.10,.10,.25])
   t.request+=torch.maximum(torch.minimum(desired-t.request,allowance),-allowance);self.request_step=step
  return t.request.clone()
 def process(self,actions,age):
  t=self.t;r=t._asset;self.check_platform();raw=actions.clamp(-10.,10.)
  default=r.data.default_joint_pos[:,t._joint_ids];native=default+.25*raw
  if not self.front_prepare.done:
   desired=self.front_prepare.target(actions,age);t.issued=(desired-default)/.25;t._raw_actions[:]=raw;t._processed_actions[:]=desired
   t.guard=dict(scope='Original platform front steps for NAV stance; unchanged physical landing/reload gates')
   return
  if not self.body_prepare.done:
   desired=self.body_prepare.target_reference(age);t.issued=(desired-default)/.25;t._raw_actions[:]=raw;t._processed_actions[:]=desired
   t.guard=dict(scope='checked four-support NAV body preparation',details=self.body_prepare.brake.details)
   return
  if self.nav_start is None:
   if self.prep_goal is None:
    bounds=r.data.soft_joint_pos_limits[:,t.arm_ids]
    self.prep_goal=torch.maximum(torch.minimum(native[:,t.arm_slots],bounds[...,1]-1e-6),bounds[...,0]+1e-6).clone()
    self.arm_prepare_start=age;self.prep_brake.begin_arm_conversion(age);self.prep_brake.conversion_goal=self.prep_goal
   desired=self.initial_target.clone() if abs(age-self.start)<1e-8 else self.prep_brake.target(age)
   t.issued=(desired-default)/.25;t._raw_actions[:]=raw;t._processed_actions[:]=desired
   t.guard=dict(scope='four-support arm preparation before native NAV legs',goal=self.prep_goal[0].tolist(),details=self.prep_brake.details)
   return
  if self.brake is not None:
   desired=self.brake.target(age);t.issued=(desired-default)/.25
   t.guard=dict(scope='platform arrival supported braking',details=self.brake.details)
  else:
   elapsed=age-self.nav_start;u=max(0.,min(1.,elapsed/1.));blend=u**3*(10-15*u+6*u*u)
   desired=self.initial_target+blend*(native-self.initial_target)
   u=max(0.,min(1.,elapsed/1.));arm_blend=u**3*(10-15*u+6*u*u)
   desired[:,t.arm_slots]=self.initial_target[:,t.arm_slots]+arm_blend*(native[:,t.arm_slots]-self.initial_target[:,t.arm_slots])
   if elapsed>=1.:desired=native.clone()
   bounds=r.data.soft_joint_pos_limits[:,t.arm_ids]
   try:arm,guard=self.arm_filter.step(desired[:,t.arm_slots],r.data.joint_pos[:,t.arm_ids],r.data.joint_vel[:,t.arm_ids],*t.arm_pd,bounds[...,0],bounds[...,1])
   except ArmReferenceInfeasible as exc:
    (t.entry_output/'nav-arm-reference-infeasible.json').write_text(json.dumps(exc.details,indent=2)+'\n')
    raise PlatformExitRejected('NAV arm smooth/effort reference intersection infeasible')
   changed=bool((arm!=desired[:,t.arm_slots]).any());desired[:,t.arm_slots]=arm
   leg_bounds=r.data.soft_joint_pos_limits[:,[t._joint_ids[i] for i in t.leg_slots]]
   leg_requested=desired[:,t.leg_slots].clone()
   leg=torch.maximum(torch.minimum(leg_requested,leg_bounds[...,1]-1e-6),leg_bounds[...,0]+1e-6)
   desired[:,t.leg_slots]=leg
   leg_changed=bool((leg!=leg_requested).any())
   t.issued=(desired-default)/.25
   if elapsed>=1.:t.issued[:,t.leg_slots]=torch.where(leg==native[:,t.leg_slots],raw[:,t.leg_slots],t.issued[:,t.leg_slots])
   if elapsed>=1.:t.issued[:,t.arm_slots]=torch.where(arm==native[:,t.arm_slots],raw[:,t.arm_slots],t.issued[:,t.arm_slots])
   passthrough=elapsed>=1. and torch.equal(t.issued,raw)
   self.native_samples+=int(passthrough);self.guarded_samples+=int(changed or leg_changed)
   t.guard=dict(scope='finite native NAV authority on platform',elapsed_s=elapsed,leg_authority=blend,arm_authority=arm_blend,arm_guard=guard,leg_soft_limit_projection=dict(changed=leg_changed,requested=leg_requested[0].tolist(),projected=leg[0].tolist(),native_target=native[0,t.leg_slots].tolist(),maximum_correction_rad=float((leg-leg_requested).abs().max())),native18_pass_through=passthrough,progress_assist=self.progress_monitor.active,arrival_stop_latched=self.arrival_stop.active,tracking_compensation_active=self.tracking_compensation.active,tracking_bias_mps=self.tracking_compensation.bias)
   self.phase='platform_nav_active' if elapsed>=1. else 'platform_nav_blend'
  t._raw_actions[:]=raw;t._processed_actions[:]=default+.25*t.issued
  limits=r.data.soft_joint_pos_limits[:,t._joint_ids]
  if not bool(((t._processed_actions>=limits[...,0])&(t._processed_actions<=limits[...,1])).all()):raise PlatformExitRejected('NAV exit target outside original soft limits')
 def observe(self,age,forces,no_failure):
  t=self.t;r=t._asset;inside=self.check_platform(False);err=float((r.data.root_pos_w[:,:2]-self.goal[:,:2]).norm());travel=float((r.data.root_pos_w[:,:2]-self.origin[:,:2]).norm())
  w,x,y,z=r.data.root_quat_w[0];yaw=float(torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z)))
  if not inside:self.rejection='Platform foot/edge domain violated'
  gates=dict(position=err<.035,orientation=abs(yaw)<.12 and float(r.data.projected_gravity_b[0,2])<-.98,feet_before_edge=inside,no_failure=no_failure)
  capture=False;details={}
  if not self.front_prepare.done:
   self.details=self.front_prepare.observe(age,forces,no_failure)
   if self.front_prepare.done:self.start_body_prepare(age)
   return self.details
  if not self.body_prepare.done:
   body=self.body_prepare.observe(age,forces)
   if self.body_prepare.rejection:self.rejection=self.body_prepare.rejection
   if self.body_prepare.done:
    self.prep_brake=SupportedBrake(t,age);self.initial_target=r.data.joint_pos_target[:,t._joint_ids].clone();self.phase='platform_supported_arm_prepare';self.arm_prepare_start=age
   self.details=dict(phase=self.phase,elapsed_s=age-self.start,body_prepare=body,complete=False)
   return self.details
  if self.nav_start is None:
   stopped=bool(r.data.root_lin_vel_w.norm()<.025 and r.data.root_ang_vel_w.norm()<.1 and (forces[:,2]>=8.).all() and r.data.joint_vel[:,[t._joint_ids[i] for i in t.leg_slots]].abs().max()<.35 and r.data.joint_vel[:,t.arm_ids].abs().max()<.2)
   reached=self.prep_goal is not None and float((r.data.joint_pos_target[:,t.arm_ids]-self.prep_goal).abs().max())<1e-4
   ready=age-self.arm_prepare_start>=6. and stopped and reached and inside and no_failure
   self.prep_stable=self.prep_stable+t._env.step_dt if ready else 0.
   if self.prep_stable>=1.:
    self.nav_start=age;self.initial_target=r.data.joint_pos_target[:,t._joint_ids].clone();self.origin=r.data.root_pos_w.clone();self.goal=self.origin.clone();self.goal[:,0]+=.12;self.phase='platform_nav_blend'
    self.arm_filter=ArmReferenceGuard(self.initial_target[:,t.arm_slots],self.initial_target.new_tensor([self.prep_brake.reference.velocity[i] for i in t.arm_slots])[None],t._env.step_dt)
   self.details=dict(phase=self.phase,elapsed_s=age-self.start,arm_prepare_stable_s=self.prep_stable,arm_goal_reached=reached,loaded_stopped=stopped,nav_started=self.nav_start is not None,nav_start_s=self.nav_start,complete=False)
   return self.details
  if self.brake is None and age-self.nav_start>=1.1 and travel>=.08:
   capture,details=brake_precheck(t,forces,gates,require_zero_request=not self.arrival_stop.active)
   if capture:
    issued=r.data.joint_pos_target[:,t.arm_ids]
    assert float((issued-self.arm_filter.position).abs().max())<1e-6
    self.brake=SupportedBrake(t,age,arm_reference_velocity=self.arm_filter.velocity);self.phase='platform_nav_arrival_brake'
    record=dict(time_s=age,scope='Seed arm braking reference from last issued reference derivative; no measured state writes',position=issued[0].tolist(),issued_velocity=self.arm_filter.velocity[0].tolist(),measured_joint_velocity=r.data.joint_vel[0,t.arm_ids].tolist(),seed_velocity=[self.brake.reference.velocity[i] for i in t.arm_slots])
    (t.entry_output/'nav-brake-reference-handoff.json').write_text(json.dumps(record,indent=2)+'\n')
  stopped=bool(r.data.root_lin_vel_w.norm()<.025 and r.data.root_ang_vel_w.norm()<.1 and (forces[:,2]>=8.).all() and r.data.joint_vel[:,[t._joint_ids[i] for i in t.leg_slots]].abs().max()<.35 and r.data.joint_vel[:,t.arm_ids].abs().max()<.2)
  request_zero=bool(t.request.abs().max()<1e-6)
  final=self.brake is not None and all(gates.values()) and stopped and travel>=.08 and request_zero
  self.stable=self.stable+t._env.step_dt if final else 0.;self.complete=self.stable>=1.
  self.details=dict(goal=(self.goal[0]-t._env.scene.env_origins[0]).tolist(),elapsed_s=age-self.start,goal_error_m=err,travel_m=travel,phase=self.phase,gates=gates,stopped=stopped,request_zero=request_zero,capture=capture,brake_precheck=details,stable_s=self.stable,complete=self.complete,native18_samples=self.native_samples,guarded_samples=self.guarded_samples)
  return self.details
