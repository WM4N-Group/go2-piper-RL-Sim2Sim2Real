"""Paired independent NAV diagnostic with explicit preparation, native ACTIVE.
The flat ground is a separate diagnostic scenario. Original chain robot USD,
self collisions, limits, PD, randomization/reset and physical safety terms stay.
No reset or queue/history clearing follows initial env.reset.
"""
from pathlib import Path
import argparse,json,hashlib,copy,traceback,math
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=3703);p.add_argument('--ee-z',type=float,required=True);p.add_argument('--ee-x',type=float,required=True);p.add_argument('--request-accel',type=float,default=.1);p.add_argument('--prepare-leg-mode',choices=['fixed','native'],default='fixed');p.add_argument('--speed',type=float,required=True);p.add_argument('--blend-s',type=float,default=1.);p.add_argument('--support-min-s',type=float,required=True);p.add_argument('--body-damping',type=float,required=True);p.add_argument('--posture-template',type=Path,required=True);p.add_argument('--seconds',type=float,default=18.);AppLauncher.add_app_launcher_args(p);a=p.parse_args()
assert not a.output.exists();a.output.mkdir(parents=True)
source_plan=json.loads((a.source.parent/'plan.json').read_text())
for n,h in source_plan['source_sha256'].items():assert hashlib.sha256((a.source/n).read_bytes()).hexdigest()==h,n
assert hashlib.sha256(a.policy.read_bytes()).hexdigest()=='72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8'
posture_template=json.loads(a.posture_template.read_text());assert posture_template['policy_sha256']==hashlib.sha256(a.policy.read_bytes()).hexdigest()
launcher=AppLauncher(a)
import torch,gymnasium as gym,isaaclab_tasks,LeggedManip_Lab.tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
from isaaclab.managers import TerminationTermCfg
class EndEpisode(Exception):pass
class ReferenceRejected(Exception):pass

def issued_actions(env):
 t=env.action_manager.get_term('joint_pos');return getattr(t,'issued',torch.zeros((env.num_envs,18),device=env.device))
def pose_request(env):
 t=env.action_manager.get_term('joint_pos');initial=getattr(t,'prep_brake',None) is None
 return torch.tensor([.5 if initial else a.ee_x,0.,.2 if initial else a.ee_z,1.,0.,0.,0.],device=env.device).repeat(env.num_envs,1)
def velocity_request(env):
 t=env.action_manager.get_term('joint_pos');initial=getattr(t,'prep_brake',None) is None;t.request=torch.tensor([[0. if initial else a.speed,0.,0.]],device=env.device);return t.request.clone()
def joint_violation(env):return getattr(env,'native_joint_limit_failure',torch.zeros(env.num_envs,dtype=torch.bool,device=env.device))
def effort_violation(env):return getattr(env,'native_effort_failure',torch.zeros(env.num_envs,dtype=torch.bool,device=env.device))

from supported_brake import SupportedBrake,brake_precheck
from native_arm_effort_guard import guard_reference

class CanonicalPrepare(SupportedBrake):
 def target(self,age):
  # Original native zero leg action reference, executed by real PD.
  # The posture template only supplies arm reference goals, never physics state.
  t=self.t;r=t._asset;desired=r.data.default_joint_pos[:,t._joint_ids].clone();u=max(0.,min(1.,(age-self.conversion_start)/6.));blend=u**3*(10.-15.*u+6.*u*u);desired[:,t.arm_slots]=self.conversion_source+blend*(self.conversion_goal-self.conversion_source)
  limits=r.data.soft_joint_pos_limits[:,t._joint_ids];desired=torch.maximum(torch.minimum(desired,limits[...,1]),limits[...,0]);target=torch.tensor(self.reference.advance(desired[0].tolist()),device=t._env.device)[None]
  self.details={'mode':'Canonical native zero leg-action PD reference plus bounded arm preparation','arm_conversion_fraction':u,'leg_reference_error_rad':float((target[:,t.leg_slots]-r.data.default_joint_pos[:,[t._joint_ids[i] for i in t.leg_slots]]).abs().max())};return target

class NativeEntry(JointPositionAction):
 def reset(self,env_ids=None):
  super().reset(env_ids);r=self._asset;s=slice(None) if env_ids is None else env_ids
  q=r.data.joint_pos[s].clone();r.set_joint_position_target(q,env_ids=env_ids);r.set_joint_velocity_target(torch.zeros_like(q),env_ids=env_ids);r.set_joint_effort_target(torch.zeros_like(q),env_ids=env_ids)
 def process_actions(self,actions):
  super().process_actions(actions);r=self._asset;ids=self._joint_ids;ids=list(range(r.num_joints))[ids] if isinstance(ids,slice) else list(ids);self._joint_ids=ids;age=float(self._env.episode_length_buf[0])*self._env.step_dt
  if not hasattr(self,'initial_target'):
   self.initial_target=r.data.joint_pos[:,ids].clone();self.arm_slots=[i for i,j in enumerate(ids) if r.joint_names[j].startswith('joint')];self.arm_ids=[ids[i] for i in self.arm_slots];self.leg_slots=[i for i in range(18) if i not in self.arm_slots];self.prep_brake=None;self.release_start=None;self.ready_dwell=0.;self.preparation_details={};self.arm_pd=[]
   for field in ['stiffness','damping','effort_limit']:
    vals=[]
    for j in self.arm_ids:
     act=next(v for v in r.actuators.values() if j in v.joint_indices);vals.append(getattr(act,field)[:,list(act.joint_indices).index(j)])
    self.arm_pd.append(torch.stack(vals,dim=1))
   self.contact_ids=self._env.scene['contact_forces'].find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0];self.damping_feet=r.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0]
  native=self._processed_actions.clone();default=r.data.default_joint_pos[:,ids];limits=r.data.soft_joint_pos_limits[:,ids];self.native_target=native
  if self.release_start is not None:
   elapsed=age-self.release_start;u=max(0.,min(1.,elapsed/a.blend_s));b=u**3*(10.-15.*u+6.*u*u);desired=self.release_target+b*(native-self.release_target)
   self.phase='NAV_BLEND' if elapsed<a.blend_s else 'NAV_ACTIVE'
   if elapsed>=a.blend_s:desired=native.clone()
  else:
   self.phase='NAV_PREPARE';desired=default.clone();g=r.root_physx_view.get_gravity_compensation_forces().to(self._env.device);cols=self.arm_ids if g.shape[1]==r.num_joints else [j+6 for j in self.arm_ids];u=min(1.,age/.08);b=u**3*(10.-15.*u+6.*u*u);bounds=limits[:,self.arm_slots]
   desired[:,self.arm_slots]=self.initial_target[:,self.arm_slots]+b*g[:,cols]/self.arm_pd[0];desired[:,self.arm_slots]=torch.maximum(torch.minimum(desired[:,self.arm_slots],bounds[...,1]),bounds[...,0])
   forces=self._env.scene['contact_forces'].data.net_forces_w[0,self.contact_ids]
   if self.prep_brake is None:
    # Loaded feet apply a small horizontal damping wrench through PD references.
    # No external force or physical state is assigned. Original PD gains remain.
    fz=forces[:,2].clamp_min(0.);loaded=fz>=8.;normal=torch.where(loaded,fz,torch.zeros_like(fz));masses=r.root_physx_view.get_masses().to(self._env.device);mass=masses.sum();com=(r.data.body_com_pos_w*masses[:,:,None]).sum(1)/mass;force=-mass*a.body_damping*r.data.root_lin_vel_w[:,:2];norm=force.norm(dim=1,keepdim=True).clamp_min(1e-9);force*=torch.minimum(torch.ones_like(norm),mass*.5/norm);loads=torch.zeros((1,4,3),device=self._env.device);residual=None
    selected=loaded.nonzero().flatten().tolist()
    if len(selected)>=3:
     footpos=r.data.body_pos_w[0,self.damping_feet];blocks=[]
     for leg in selected:
      dx,dy,dz=(footpos[leg]-com[0]).unbind();zero=torch.zeros_like(dx);cross=torch.stack((torch.stack((zero,-dz,dy)),torch.stack((dz,zero,-dx)),torch.stack((-dy,dx,zero))));blocks.append(torch.cat((torch.eye(3,device=self._env.device),cross),dim=0))
     A=torch.cat(blocks,dim=1);weights=(normal[selected]/normal[selected].sum()).sqrt().repeat_interleave(3);Aw=A*weights[None];wrench=torch.cat((force[0],torch.zeros(4,device=self._env.device)));solution=weights*(torch.linalg.pinv(Aw)@wrench);candidate=solution.reshape(-1,3);vertical=.2*normal[selected]/candidate[:,2].abs().clamp_min(1e-9);horizontal=.3*normal[selected]/candidate[:,:2].norm(dim=1).clamp_min(1e-9);scale=torch.minimum(vertical.min(),horizontal.min()).clamp(max=1.);candidate*=scale;loads[0,selected]=candidate;residual=(A@candidate.flatten()-scale*wrench).tolist()
    jac=r.root_physx_view.get_jacobians();offset=0 if r.is_fixed_base else 6;values=[];legids=[ids[i] for i in self.leg_slots]
    for leg,foot in enumerate(self.damping_feet):
     columns=[j+offset for j in legids[3*leg:3*leg+3]];J=jac[:,foot-(1 if r.is_fixed_base else 0),:3][:,:,columns];values.append(-(J.transpose(1,2)@loads[:,leg,:,None]).squeeze(-1))
    correction=torch.cat(values,dim=1);cap=.1*r.data.joint_effort_limits[:,legids];scale=(cap/correction.abs().clamp_min(1e-9)).min().clamp(max=1.);correction*=scale;desired[:,self.leg_slots]+=correction/30.;self.initial_body_damping_details={'requested_horizontal_force_N':force[0].tolist(),'contact_force_correction_targets_N':loads[0].tolist(),'wrench_reference_point':'actual whole-robot COM','desired_additional_moment_Nm':[0.,0.,0.],'wrench_residual':residual,'leg_torque_correction_max_Nm':float(correction.abs().max()),'actual_loaded_contact_count':len(selected),'acceleration_cap_mps2':.5,'friction_correction_ratio_cap':.3,'normal_correction_ratio_cap':.2}
    try:arm,details=guard_reference(desired[:,self.arm_slots],r.data.joint_pos[:,self.arm_ids],r.data.joint_vel[:,self.arm_ids],*self.arm_pd,bounds[...,0],bounds[...,1]);desired[:,self.arm_slots]=arm;self.early_arm_forecast=details
    except ValueError:
     self.rejection={'scope':'Initial gravity-hold arm forecast/soft-limit intersection infeasible','time_s':age,'q':r.data.joint_pos[0,self.arm_ids].tolist(),'dq':r.data.joint_vel[0,self.arm_ids].tolist()};raise ReferenceRejected()
   if self.prep_brake is None and age>=a.support_min_s:
    eligible,details=brake_precheck(self,forces,dict(position=True,orientation=bool(float(r.data.projected_gravity_b[0,2])<-.98),feet_before_edge=True,no_failure=True),require_zero_request=False);self.preparation_details={'support_precheck':details}
    if eligible:
     self.ground_support_event={'time_s':age,'physical_precheck':details,'actual_foot_fz':forces[:,2].tolist(),'scope':'Actual initial support precheck before arm preparation; final full READY dwell remains separate'}
     self.prep_brake=CanonicalPrepare(self,age)
     mass=r.root_physx_view.get_masses().to(self._env.device);com=(r.data.body_com_pos_w*mass[:,:,None]).sum(1)/mass.sum(1)[:,None];feet=r.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0];center=r.data.body_pos_w[:,feet,:2].mean(1)
     self.prep_brake.origin[:,:2]+=(center-com[:,:2]);self.prep_brake.origin[:,2]=self._env.scene.env_origins[:,2]+.28
     w,x,y,z=r.data.root_quat_w.unbind(-1);yaw=torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z));self.prep_brake.orientation=torch.stack((torch.cos(yaw/2),torch.zeros_like(yaw),torch.zeros_like(yaw),torch.sin(yaw/2)),-1)
     self.entry_body_goal={'root_position':self.prep_brake.origin[0].tolist(),'root_quaternion':self.prep_brake.orientation[0].tolist(),'support_centroid_xy':center[0].tolist(),'COM_before_prepare':com[0].tolist(),'scope':'Reference goals only; actual pose evolves through supported controller, no state writes'}
     self.live_arm_goal_start=None;self.template_stable=0.;self.template_pose=torch.tensor(posture_template['measured_pose_median_rad'],device=self._env.device)[None];self.template_basin=torch.tensor(posture_template['live_compatibility_basin_rad'],device=self._env.device)[None];self.prep_brake.conversion_start=age;self.prep_brake.conversion_source=r.data.joint_pos_target[:,ids][:,self.arm_slots].clone();self.prepare_started=age
   if self.prep_brake is not None:
    # Re-evaluate target from actual current observations each control step.
    # Conversion remains an explicit preparation stage, never native ACTIVE.
    goal=native[:,self.arm_slots]
    if self.live_arm_goal_start is None:
     pose_error=float((r.data.joint_pos[:,self.arm_ids]-self.template_pose).abs().max());slow=float(r.data.joint_vel[:,self.arm_ids].abs().max())<.2
     self.template_stable=self.template_stable+self._env.step_dt if age-self.prepare_started>=6. and pose_error<.04 and slow else 0.
     if self.template_stable>=.3:
      self.live_arm_goal_start=age;self.prepare_started=age;self.prep_brake.conversion_start=age;self.prep_brake.conversion_source=torch.tensor(self.prep_brake.reference.position,device=self._env.device)[None][:,self.arm_slots].clone()
    if self.live_arm_goal_start is None:
     # Follow measured original NAV posture with current gravity compensation.
     # This is a commanded trajectory under real physics, never a state assignment.
     gravity=r.root_physx_view.get_gravity_compensation_forces();columns=self.arm_ids if gravity.shape[1]==r.num_joints else [j+6 for j in self.arm_ids];target=self.template_pose+gravity[:,columns]/self.arm_pd[0]
    else:target=goal
    self.prep_brake.conversion_goal=torch.maximum(torch.minimum(target,bounds[...,1]),bounds[...,0]);desired=self.prep_brake.target(age)
    kp,kd,effort=self.arm_pd;q=r.data.joint_pos[:,self.arm_ids];dq=r.data.joint_vel[:,self.arm_ids];predicted=float(((kp*(goal-q)-kd*dq).abs()/effort).max());error=float((desired[:,self.arm_slots]-goal).abs().max())
    legids=[ids[i] for i in self.leg_slots];leggoal=native[:,self.leg_slots];legbounds=limits[:,self.leg_slots];legprediction=float(((30.*(leggoal-r.data.joint_pos[:,legids])-.6*r.data.joint_vel[:,legids]).abs()/r.data.joint_effort_limits[:,legids]).max())
    gates={'live_native_goal_enabled':self.live_arm_goal_start is not None,'normal_wrist_branch':bool(r.data.joint_pos[0,self.arm_ids[3]]>.5 and r.data.joint_pos[0,self.arm_ids[5]]<-.5),'actual_leg_state_within_soft_limits':bool(((r.data.joint_pos[:,legids]>=legbounds[...,0])&(r.data.joint_pos[:,legids]<=legbounds[...,1])).all()),'native_leg_predicted_torque_reserve':legprediction<.75,'canonical_leg_reference_match':float((desired[:,self.leg_slots]-default[:,self.leg_slots]).abs().max())<1e-4,'canonical_body_height':float((r.data.root_pos_w[:,2]-self._env.scene.env_origins[:,2]-posture_template['body_height_reference_m']).abs().max())<posture_template['body_height_tolerance_m'],'original_body_orientation_gate':float(r.data.projected_gravity_b[0,2])<-.98,'conversion_elapsed':age-self.prepare_started>=6.,'native_arm_within_soft_limits':bool(((goal>=bounds[...,0])&(goal<=bounds[...,1])).all()),'native_arm_reference_match':error<.03,'native_arm_predicted_torque_reserve':predicted<.75,'body_stopped':float(r.data.root_lin_vel_w.norm())<.025 and float(r.data.root_ang_vel_w.norm())<.1,'all_four_loaded':bool((forces[:,2]>=12.).all()),'legs_slow':float(r.data.joint_vel[:,[ids[i] for i in self.leg_slots]].abs().max())<.35,'arm_slow':float(dq.abs().max())<.2,'references_slow':max(abs(v) for v in self.prep_brake.reference.velocity)<.2,'no_effort_failure':not bool(getattr(self._env,'native_effort_failure',torch.zeros(1,device=self._env.device,dtype=torch.bool))[0])}
    self.ready_dwell=self.ready_dwell+self._env.step_dt if all(gates.values()) else 0.;self.preparation_details={'ready_gates':gates,'ready_dwell_s':self.ready_dwell,'native_arm_reference_error_rad':error,'native_arm_predicted_torque_ratio':predicted,'native_leg_predicted_torque_ratio':legprediction,'body_reference_domain':{'height_m':posture_template['body_height_reference_m'],'height_tolerance_m':posture_template['body_height_tolerance_m'],'projected_gravity_xy_limit':posture_template['projected_gravity_xy_limit']},'template_live_goal_started_s':self.live_arm_goal_start,'template_stable_s':self.template_stable,'support_control':self.prep_brake.details}
    if self.ready_dwell>=.5:
     self.release_start=age;self.release_target=desired.clone();self.ready_event={'time_s':age,'gates':gates,'continuous_stable_s':self.ready_dwell,'actual_q':r.data.joint_pos[0,ids].tolist(),'actual_root':r.data.root_pos_w[0].tolist(),'issued_target':desired[0].tolist(),'pending_native_target':native[0].tolist(),'native_arm_predicted_ratio':predicted}
  if self.phase=='NAV_PREPARE':
   self.preparation_details['subphase']='initial_support' if age<2. else 'raised_arm_warmup' if self.prep_brake is None else 'supported_arm_preparation'
   # Preparation owns its commands; constrain every issued reference to the
   # unchanged original soft limits before issuing it. Native ACTIVE is never projected.
   unbounded=desired.clone();desired=torch.maximum(torch.minimum(desired,limits[...,1]),limits[...,0]);self.preparation_details['preparation_soft_projection_max_rad']=float((desired-unbounded).abs().max())
  self._processed_actions[:]=desired;self.issued=(desired-default)/.25
  if self.phase=='NAV_ACTIVE':
   self.issued[:]=actions.clamp(-10.,10.);assert torch.equal(desired,native)
  # Native leg PD references are virtual spring targets, not actual joint pose.
  # Keep native targets and preserve actual soft-limit and .04s forecast gates.
  legids=[ids[i] for i in self.leg_slots];legbounds=limits[:,self.leg_slots];qleg=r.data.joint_pos[:,legids];future=qleg+.04*r.data.joint_vel[:,legids]
  self.virtual_leg_reference_soft_excess_rad=float(torch.maximum(legbounds[...,0]-desired[:,self.leg_slots],desired[:,self.leg_slots]-legbounds[...,1]).clamp_min(0.).max())
  actual_or_future=torch.maximum(torch.maximum(legbounds[...,0]-qleg,qleg-legbounds[...,1]),torch.maximum(legbounds[...,0]-future,future-legbounds[...,1])).clamp_min(0.)
  if float(actual_or_future.max())>1e-5:
   self.rejection={'scope':'Actual leg state or .04s linear forecast beyond original soft limits; native target not projected','time_s':age,'maximum_excess_rad':float(actual_or_future.max()),'q':qleg[0].tolist(),'forecast_q':future[0].tolist(),'target':desired[0].tolist()};raise ReferenceRejected()
  arm_excess=torch.maximum(limits[:,self.arm_slots,0]-desired[:,self.arm_slots],desired[:,self.arm_slots]-limits[:,self.arm_slots,1]).clamp_min(0.)
  if float(arm_excess.max())>1e-5:
   self.rejection={'scope':'Arm reference outside original soft limits; no native projection','time_s':age,'maximum_excess_rad':float(arm_excess.max()),'target':desired[0].tolist()};raise ReferenceRejected()

def main():
 chain=load_cfg_from_registry('GO2-PIPER-Box-Climb-Stages-Play','env_cfg_entry_point');cfg=load_cfg_from_registry('GO2-PIPER-Flat','env_cfg_entry_point');cfg.scene.num_envs=1;cfg.sim.device=a.device;cfg.seed=a.seed;cfg.episode_length_s=a.seconds+1.
 cfg.scene.robot=copy.deepcopy(chain.scene.robot);cfg.scene.lazy_sensor_update=chain.scene.lazy_sensor_update;cfg.scene.contact_forces.history_length=chain.scene.contact_forces.history_length
 # All robot startup/reset events and all failure terms are taken from the chain.
 cfg.events=copy.deepcopy(chain.events);cfg.prepared_start_path=chain.prepared_start_path;cfg.prepared_start_phase=chain.prepared_start_phase
 assert not cfg.prepared_start_path, 'No prepared-state injection in standalone diagnostic'
 assert getattr(cfg.events,'reset_climb_stages',None) is None
 cfg.terminations=copy.deepcopy(chain.terminations);cfg.terminations.box_settled=None;cfg.terminations.transition_effort=TerminationTermCfg(func=effort_violation);cfg.terminations.native_actual_joint_limit=TerminationTermCfg(func=joint_violation)
 cfg.actions.joint_pos=copy.deepcopy(load_cfg_from_registry('GO2-PIPER-Flat','env_cfg_entry_point').actions.joint_pos);cfg.actions.joint_pos.class_type=NativeEntry
 cfg.observations.policy.enable_corruption=False;cfg.observations.policy.actions.func=issued_actions;cfg.observations.policy.actions.params={};cfg.observations.policy.velocity_commands.func=velocity_request;cfg.observations.policy.velocity_commands.params={};cfg.observations.policy.pos_commands.func=pose_request;cfg.observations.policy.pos_commands.params={}
 for term in vars(cfg.rewards).values():
  if hasattr(term,'weight'):term.weight=0.
 # Command managers keep the original input dimensions but never resample.
 for key in ['base_velocity','ee_pose']:
  cmd=getattr(cfg.commands,key);cmd.resampling_time_range=(10000.,10000.);cmd.debug_vis=False
 env=gym.make('GO2-PIPER-Flat',cfg=cfg).unwrapped;obs,_=env.reset(seed=a.seed);r=env.scene['robot'];t=env.action_manager.get_term('joint_pos');ids=t._joint_ids;ids=list(range(r.num_joints))[ids] if isinstance(ids,slice) else list(ids);arm_ids=r.find_joints(['joint[1-6]'],preserve_order=True)[0];footids=env.scene['contact_forces'].find_bodies(['FL_foot','FR_foot','RL_foot','RR_foot'],preserve_order=True)[0]
 assert obs['policy'].shape==(1,210)
 actor=torch.jit.load(str(a.policy),map_location=a.device).eval()
 rep={'scope':'Independent flat diagnostic with original chain robot, reset, physical limits and failure terms; no task-arrival or deployment acceptance','ee_x_m':a.ee_x,'posture_template_sha256':hashlib.sha256(a.posture_template.read_bytes()).hexdigest(),'support_min_s':a.support_min_s,'initial_body_damping_s_inv':a.body_damping,'initial_root_position':r.data.root_pos_w[0].tolist(),'maximum_preparation_horizontal_excursion_m':0.,'initial_leg_mode':'Original native zero leg action PD throughout preparation; gravity and forecast-bounded arm loading','seed':a.seed,'ee_z_m':a.ee_z,'outcome':'incomplete','steps':0,'phase_counts':{},'active_samples':0,'active_native18_exact_samples':0,'max_native_target_error_rad':0.,'termination':{},'max_arm_effort_ratio_including_init':0.,'max_all_effort_ratio_including_init':0.,'airborne_control_samples':0,'under_three_support_control_samples':0,'exactly_three_support_control_samples':0,'max_abs_vz_mps':0.,'max_foot_force_N':0.,'max_resultant_contact_force_N':0.,'actual_arm_limits_Nm':r.data.joint_effort_limits[0,arm_ids].tolist(),'self_collisions_enabled':cfg.scene.robot.spawn.articulation_props.enabled_self_collisions,'policy_sha256':hashlib.sha256(a.policy.read_bytes()).hexdigest(),'physical_resets_after_initial':0,'active_extra_arm_filter':False,'velocity_request_mode':'Explicit initial support uses known EE(.5,0,.2), velocity0 and native leg feedback with gravity arm hold; after support precheck switch pending native EE/velocity input without history clearing','requested_forward_speed_mps':a.speed,'prepare_leg_mode':'supported-body plus iterative bounded native arm target','blend_s':a.blend_s,'active_native_soft_limit_policy':'Native leg virtual references unprojected; actual leg q checked each physics substep and .04s linear forecast before control; arm reference soft limit retained','source_plan_sha256':hashlib.sha256((a.source.parent/'plan.json').read_bytes()).hexdigest()}
 assert rep['actual_arm_limits_Nm']==[20.,20.,15.,7.,5.,5.]
 rep['robot_total_mass_kg']=float(r.root_physx_view.get_masses().sum());rep['sampled_actuator_delays']={}
 for name,actuator in r.actuators.items():
  delays={}
  for field in dir(actuator):
   if 'delay' in field.lower():
    item=getattr(actuator,field)
    if hasattr(item,'time_lags'):delays[field]=item.time_lags.tolist()
  rep['sampled_actuator_delays'][name]=delays

 (a.output/'initial-state.json').write_text(json.dumps({'q':r.data.joint_pos[0,ids].tolist(),'root_position':r.data.root_pos_w[0].tolist(),'root_quaternion':r.data.root_quat_w[0].tolist(),'joint_names':[r.joint_names[i] for i in ids]},indent=2)+'\n')
 (a.output/'actuator-contract.json').write_text(json.dumps({n:{k:str(getattr(v,k,None)) for k in ['stiffness','damping','effort_limit','cfg']} for n,v in r.actuators.items()},indent=2)+'\n')
 def stop(env_ids,*args,**kwargs):
  if len(env_ids):rep['termination']={n:bool(env.termination_manager.get_term(n)[0]) for n in env.termination_manager.active_terms};raise EndEpisode()
 env.recorder_manager.record_pre_reset=stop;original_update=env.scene.update
 def update(dt):
  original_update(dt);ratios=r.data.applied_torque.abs()/r.data.joint_effort_limits;arm=float(ratios[:,arm_ids].max());rep['max_arm_effort_ratio_including_init']=max(rep['max_arm_effort_ratio_including_init'],arm);rep['max_all_effort_ratio_including_init']=max(rep['max_all_effort_ratio_including_init'],float(ratios.max()))
  leg_ids=[ids[i] for i,n in enumerate([r.joint_names[j] for j in ids]) if not n.startswith('joint')];lim=r.data.soft_joint_pos_limits[:,leg_ids];qleg=r.data.joint_pos[:,leg_ids];margin=float(torch.minimum(qleg-lim[...,0],lim[...,1]-qleg).min());rep['minimum_actual_leg_soft_margin_rad_including_init']=min(rep.get('minimum_actual_leg_soft_margin_rad_including_init',float('inf')),margin)
  if margin < -1e-5:
   env.native_joint_limit_failure=torch.ones(1,dtype=torch.bool,device=env.device);rep.setdefault('first_actual_joint_limit_violation',{'control_start_s':int(env.episode_length_buf[0])*env.step_dt,'minimum_actual_soft_margin_rad':margin,'q':qleg[0].tolist()})
  if arm>=.98:
   env.native_effort_failure=torch.ones(1,dtype=torch.bool,device=env.device);rep.setdefault('first_effort_violation',{'control_start_s':int(env.episode_length_buf[0])*env.step_dt,'ratio':arm,'q':r.data.joint_pos[0,arm_ids].tolist(),'dq':r.data.joint_vel[0,arm_ids].tolist(),'torque_Nm':r.data.applied_torque[0,arm_ids].tolist()})
 env.scene.update=update;active_origin=None;vel=[]
 try:
  with (a.output/'control.jsonl').open('x') as log,torch.inference_mode():
   for i in range(round(a.seconds/env.step_dt)):
    before=obs['policy'].clone();action=actor(before).clamp(-10.,10.);terminal=False
    try:obs,*_=env.step(action)
    except ReferenceRejected:rep['outcome']='native_reference_rejected';rep['reference_rejection']=t.rejection;break
    except EndEpisode:terminal=True
    phase=t.phase;pos=r.data.root_pos_w[0];
    if phase=='NAV_PREPARE':rep['maximum_preparation_horizontal_excursion_m']=max(rep['maximum_preparation_horizontal_excursion_m'],float((pos[:2]-torch.tensor(rep['initial_root_position'][:2],device=env.device)).norm()))
    f=env.scene['contact_forces'].data.net_forces_w[0,footids];n=int((f[:,2]>2.).sum());rep['airborne_control_samples']+=n==0;rep['under_three_support_control_samples']+=n<3;rep['exactly_three_support_control_samples']+=n==3;rep['max_abs_vz_mps']=max(rep['max_abs_vz_mps'],abs(float(r.data.root_lin_vel_w[0,2])));rep['max_foot_force_N']=max(rep['max_foot_force_N'],float(f.norm(dim=-1).max()));rep['max_resultant_contact_force_N']=max(rep['max_resultant_contact_force_N'],float(f.sum(0).norm()));rep['steps']+=1;rep['phase_counts'][phase]=rep['phase_counts'].get(phase,0)+1
    error=float((t._processed_actions-t.native_target).abs().max())
    if phase=='NAV_ACTIVE':
     if active_origin is None:active_origin=pos.clone()
     rep['active_samples']+=1;rep['active_native18_exact_samples']+=int(error<1e-7 and torch.equal(t.issued,action));rep['max_native_target_error_rad']=max(rep['max_native_target_error_rad'],error);vel.append(r.data.root_lin_vel_b[0,:2].tolist())
    row={'time_s':int(env.episode_length_buf[0])*env.step_dt,'phase':phase,'root_position':pos.tolist(),'root_quaternion':r.data.root_quat_w[0].tolist(),'root_velocity':r.data.root_lin_vel_w[0].tolist(),'root_angular_velocity':r.data.root_ang_vel_w[0].tolist(),'q':r.data.joint_pos[0,ids].tolist(),'dq':r.data.joint_vel[0,ids].tolist(),'pd_target':r.data.joint_pos_target[0,ids].tolist(),'observation':before[0].tolist(),'native_action':action[0].tolist(),'issued_action':t.issued[0].tolist(),'velocity_request':t.request[0].tolist(),'arm_torque_Nm':r.data.applied_torque[0,arm_ids].tolist(),'foot_forces':f.tolist(),'native_target_error_rad':error,'virtual_leg_reference_soft_excess_rad':t.virtual_leg_reference_soft_excess_rad,'terminal':terminal,'preparation':t.preparation_details,'initial_body_damping':getattr(t,'initial_body_damping_details',None)};log.write(json.dumps(row)+'\n')
    if terminal:rep['outcome']='native_termination';break
    if rep['active_samples']>=500:rep['outcome']='completed_native_active_diagnostic';break
   else:rep['outcome']='entry_not_ready_or_active_incomplete'
 except Exception:rep['outcome']='runtime_error';rep['error']=traceback.format_exc()
 finally:
  rep['ground_support_event']=getattr(t,'ground_support_event',None);rep['ready_event']=getattr(t,'ready_event',None);rep['last_preparation_details']=t.preparation_details;rep['active_horizontal_net_travel_m']=None if active_origin is None else float((r.data.root_pos_w[0,:2]-active_origin[:2]).norm());rep['active_mean_body_velocity_xy']=None if not vel else [sum(x[j] for x in vel)/len(vel) for j in range(2)];rep['control_sha256']=hashlib.file_digest((a.output/'control.jsonl').open('rb'),'sha256').hexdigest();(a.output/'report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True);env.close()
main();launcher.app.close()
