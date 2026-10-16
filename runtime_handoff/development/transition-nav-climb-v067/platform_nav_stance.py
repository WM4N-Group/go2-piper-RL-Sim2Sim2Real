"""Checked four-contact body preparation after independently completed CLIMB."""
import json,math
import torch
from supported_brake import SupportedBrake
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import balanced_vertical_loads,predicted_support_com
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_leg_kinematics import rotate_vector
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_body_clearance import support_path_geometry,leg_path_gap

def checked_path(t,goal,rotation):
 r=t._asset;g=t.guidance;feet=t.feet_positions();origin=r.data.root_pos_w.clone();quat=r.data.root_quat_w.clone()
 slots=torch.tensor(t._joint_ids,device=t._env.device)[g.slots]
 bounds=r.data.soft_joint_pos_limits[:,slots];bias=r.data.joint_pos_target[:,slots]-r.data.joint_pos[:,slots]
 gravity=r.root_physx_view.get_gravity_compensation_forces();offset=0 if gravity.shape[1]==r.num_joints else 6;gravity=gravity[:,slots+offset]
 effort=r.data.joint_effort_limits[:,slots];weight=t.mass.sum(1)*9.81
 preview=dict(com=t.center_of_mass(),orientation=quat,rotation_active=torch.ones(len(feet),dtype=torch.bool,device=feet.device))
 gap,oldmargin,patherror=support_path_geometry(g.model,feet,origin,quat,goal[:,None],rotation[:,None],bias,bounds,g.body_bounds,g.box_bounds)
 legs=leg_path_gap(g.model,feet,origin,quat,goal[:,None],rotation[:,None],g.link_bounds,g.box_bounds)
 minimum=float('inf');resmax=0.;margin=float('inf');ratio=0.;error=0.
 for u in torch.linspace(0.,1.,21,device=feet.device):
  pose=torch.lerp(origin,goal,u);turn=torch.lerp(quat,rotation,u);turn/=turn.norm(dim=-1,keepdim=True)
  local=rotate_vector(turn[:,None],feet-pose[:,None],True);joints=g.model.inverse(local)
  com=predicted_support_com(origin,pose[:,None],turn[:,None],preview)[:,0]
  loads,res=balanced_vertical_loads(feet,com,weight,torch.zeros(len(feet),dtype=torch.long,device=feet.device),torch.zeros_like(weight))
  up=pose.new_tensor([0.,0.,1.]).expand_as(pose)
  vertical=(g.model.jacobian(joints)*rotate_vector(turn,up,True)[:,None,:,None]).sum(-2)
  torque=gravity-vertical*loads[...,None];command=joints+torque/30.
  nominal=torch.minimum(joints-bounds[...,0],bounds[...,1]-joints).amin()-.01
  cmd=torch.minimum(command-bounds[...,0],bounds[...,1]-command).amin()
  margin=min(margin,float(torch.minimum(nominal,cmd)));ratio=max(ratio,float((torque.abs()/effort).max()))
  minimum=min(minimum,float(loads.min()));resmax=max(resmax,float(res.norm(dim=-1).max()));error=max(error,float((g.model.forward(joints)-local).norm(dim=-1).max()))
 angle=float(2*torch.acos((quat*rotation).sum(-1).abs().clamp(max=1.))[0])
 valid=(float(gap.min())>=.01 and float(legs.min())>=.005 and float(oldmargin.min())>=0. and float(patherror.max())<.001 and minimum>=8. and resmax<.1 and margin>=.03 and ratio<=.75 and error<.001 and angle<=.35)
 result=dict(valid=valid,body_gap=float(gap.min()),leg_gap=float(legs.min()),old_bias_margin=float(oldmargin.min()),command_margin=margin,minimum_path_load=minimum,maximum_load_residual=resmax,maximum_effort_ratio=ratio,maximum_ik_error=error,angle_rad=angle)
 record=dict(time_s=float(t._env.episode_length_buf[0])*t._env.step_dt,origin=origin,quaternion=quat,goal=goal,goal_quaternion=rotation,feet=feet,bounds=bounds,bias=bias,gravity=gravity,effort=effort,weight=weight,com=preview['com'],box_bounds=g.box_bounds,result=result)
 def pack(v):
  if torch.is_tensor(v):return v.detach().cpu().tolist()
  if isinstance(v,dict):return {k:pack(x) for k,x in v.items()}
  return v
 with (t.entry_output/'platform-body-plans.jsonl').open('a') as f:f.write(json.dumps(pack(record))+'\n')
 return result

class PlatformNavStance:
 def __init__(self,t,age,nav_snapshot):
  self.t=t;r=t._asset;self.start=age;self.segment_start=age;self.done=False;self.rejection=None;self.stable=0.;self.details={}
  self.initial_target=r.data.joint_pos_target[:,t._joint_ids].clone();self.origin=r.data.root_pos_w.clone();self.quat=r.data.root_quat_w.clone()
  feet=t.feet_positions();navroot=self.origin.new_tensor(nav_snapshot['root_position'])[None];navfeet=self.origin.new_tensor(nav_snapshot['feet'])[None]
  self.goal=self.origin.clone();self.goal[:,0]=torch.maximum(self.origin[:,0],(feet[:,2:,0]-(navfeet[:,2:,0]-navroot[:,None,0])).amax(1))
  self.goal[:,2]=feet[...,2].mean(1)+navroot[:,2]-navfeet[...,2].mean(1)
  self.rotation=self.origin.new_tensor(nav_snapshot['root_quaternion'])[None]
  self.rotation*=torch.where((self.rotation*self.quat).sum(1)<0,-1.,1.)[:,None]
  self.rotation/=self.rotation.norm(dim=-1,keepdim=True)
  if float((self.goal-self.origin)[:,:2].norm())>.24 or float((self.goal-self.origin)[:,2].abs().max())>.08:self.rejection='NAV preparation displacement outside diagnostic envelope'
  self.segments=max(1,math.ceil(float((self.goal-self.origin)[:,:2].norm())/.08));self.index=0
  self.brake=SupportedBrake(t,age);self.brake.tracking_integral_acceleration=torch.zeros_like(self.origin);self.tracking_stall=0.;self.ref_origin=self.origin.clone();self.ref_quat=self.quat.clone()
  self.nominal_goal=self.goal.clone();self.goal_projection=[0.,0.];self.goal_projection_trials=[]
  def room(goal):
   projected=goal[:,None,:2]+navfeet[:,:,:2]-navroot[:,None,:2]-t._env.scene.env_origins[:,None,:2]
   return bool((projected[...,0]>.81).all() and (projected[...,0]<1.84).all() and (projected[...,1].abs()<.49).all())
  self.full_plan=checked_path(t,self.goal,self.rotation)
  ready=self.full_plan['valid'] and self.full_plan['minimum_path_load']>=15. and room(self.goal)
  if not ready:
   shifts=[(-.005*i,y) for i in range(9) for y in (0.,.005,-.005,.01,-.01) if i or y]
   shifts.sort(key=lambda v:(v[0]*v[0]+v[1]*v[1],abs(v[0]),abs(v[1]),-v[1]))
   for dx,dy in shifts:
    trial=self.nominal_goal.clone();trial[:,0]+=dx;trial[:,1]+=dy
    if bool((trial[:,0]<self.origin[:,0]).any()) or not room(trial):continue
    check=checked_path(t,trial,self.rotation);accepted=check['valid'] and check['minimum_path_load']>=15.
    self.goal_projection_trials.append(dict(delta=[dx,dy],result=check,accepted=accepted))
    if accepted:self.goal=trial;self.full_plan=check;self.goal_projection=[dx,dy];ready=True;break
  if not ready:self.rejection='Full supported NAV pose path infeasible'
  self.segments=max(1,math.ceil(float((self.goal-self.origin)[:,:2].norm())/.08))
  (t.entry_output/'platform-body-goal-selection.json').write_text(json.dumps(dict(scope='Checked bounded NAV body-goal projection, original actual8N gate retained',nominal=(self.nominal_goal[0]-t._env.scene.env_origins[0]).tolist(),selected=(self.goal[0]-t._env.scene.env_origins[0]).tolist(),delta=self.goal_projection,planning_minimum_load=15.,ready=ready,trials=self.goal_projection_trials),indent=2)+'\n')
  self.set_segment(age)
 def set_segment(self,age):
  u=(self.index+1)/self.segments;self.target=torch.lerp(self.origin,self.goal,u);self.turn=torch.lerp(self.quat,self.rotation,u);self.turn/=self.turn.norm(dim=-1,keepdim=True)
  self.plan=checked_path(self.t,self.target,self.turn)
  if not self.plan['valid']:self.rejection='Supported NAV preparation segment infeasible'
  self.tracking_stall=0.;self.segment_start=age;self.ref_origin=self.brake.origin.clone();self.ref_quat=self.brake.orientation.clone();self.stable=0.
 def target_reference(self,age):
  if abs(age-self.start)<1e-8:return self.initial_target.clone()
  r=self.t._asset;dt=self.t._env.step_dt;error=self.target-r.data.root_pos_w
  forces=self.t._env.scene['contact_forces'].data.net_forces_w[:,self.t.sensor_ids,2]
  calm=bool(r.data.root_lin_vel_w.norm()<.025 and r.data.root_ang_vel_w.norm()<.1 and (forces>=8.).all())
  stalled=age-self.segment_start>=3. and calm and .005<=float(error.norm())<.02
  self.tracking_stall=self.tracking_stall+dt if stalled else 0.
  if self.tracking_stall>=.5:
   # Add slow bounded force feedback; target and every settling gate stay fixed.
   self.brake.tracking_integral_acceleration=(self.brake.tracking_integral_acceleration+error*dt).clamp(-.06,.06)
  u=max(0.,min(1.,(age-self.segment_start)/3.));blend=u**3*(10-15*u+6*u*u)
  self.brake.origin=torch.lerp(self.ref_origin,self.target,blend)
  self.brake.orientation=torch.lerp(self.ref_quat,self.turn,blend);self.brake.orientation/=self.brake.orientation.norm(dim=-1,keepdim=True)
  return self.brake.target(age)
 def observe(self,age,forces):
  t=self.t;r=t._asset
  if bool((forces[:,2]<2.).any()):self.rejection='Contact lost during four-support NAV posture preparation'
  error=float((r.data.root_pos_w-self.target).norm());angle=float(2*torch.acos((r.data.root_quat_w*self.turn).sum(1).abs().clamp(max=1.))[0])
  stopped=bool(r.data.root_lin_vel_w.norm()<.025 and r.data.root_ang_vel_w.norm()<.1 and (forces[:,2]>=8.).all() and r.data.joint_vel[:,[t._joint_ids[i] for i in t.leg_slots]].abs().max()<.35 and r.data.joint_vel[:,t.arm_ids].abs().max()<.2)
  ready=age-self.segment_start>=3. and error<.005 and angle<.025 and stopped and self.rejection is None
  self.stable=self.stable+t._env.step_dt if ready else 0.
  self.details=dict(segment=self.index+1,segments=self.segments,segment_elapsed_s=age-self.segment_start,goal=(self.goal[0]-t._env.scene.env_origins[0]).tolist(),target=(self.target[0]-t._env.scene.env_origins[0]).tolist(),position_error=error,angle_error=angle,loaded_stopped=stopped,stable_s=self.stable,plan=self.plan,rejection=self.rejection,done=self.done)
  if self.stable>=.5:
   self.index+=1
   if self.index==self.segments:self.done=True
   else:self.set_segment(age)
  self.details['done']=self.done
  return self.details
