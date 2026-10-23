"""Explicit supported NAV braking; actual parking gates remain in caller.
Uses preserved v317 wrench and bounded-reference contracts. No physical writes.
"""
import torch
from isaaclab.utils.math import quat_mul, quat_conjugate
from stance_wrench_math import allocate_wrench
from stance_wrench_fallback import refine_stance_wrench
from piper_skill_transition_contract import BoundedReference


def leg_torques(r, feet, leg_ids, loads):
 jacobians=r.root_physx_view.get_jacobians()
 gravity=r.root_physx_view.get_gravity_compensation_forces()
 offset=0 if r.is_fixed_base else 6
 values=[]
 for leg,body in enumerate(feet):
  ids=leg_ids[3*leg:3*leg+3]
  jac=jacobians[:,body-(1 if r.is_fixed_base else 0),:3][:,:,[j+offset for j in ids]]
  columns=ids if gravity.shape[1]==r.num_joints else [j+offset for j in ids]
  values.append(gravity[:,columns]-(jac.transpose(1,2)@loads[:,leg,:,None]).squeeze(-1))
 return torch.cat(values,dim=1)


def brake_precheck(t, forces, gates, require_zero_request=True):
 r=t._asset
 # Braking initiation is a dynamic support domain, never the stationary READY gate.
 # Bound measured arm speed below the unchanged .45rad/s reference envelope;
 # retain four loads>=12N, conservative wrench/friction and <.75 effort reserve.
 good=(all(gates[k] for k in ['position','orientation','feet_before_edge','no_failure'])
       and bool((forces[:,2]>=12.).all())
       and float(r.data.root_lin_vel_w.norm())<.08
       and float(r.data.root_ang_vel_w.norm())<.4
       and float(r.data.root_lin_vel_w[0,2].abs())<.04
       and float(r.data.root_ang_vel_w[0,2].abs())<.1
       and float(r.data.joint_vel[:,[t._joint_ids[i] for i in t.leg_slots]].abs().max())<.95
       and float(r.data.joint_vel[:,t.arm_ids].abs().max())<.4
       and (not require_zero_request or float(t.request.abs().max())<1e-6))
 if not good:return False,dict(kinematic_precheck=False,request_zero_required=require_zero_request,request_zero_actual=bool(t.request.abs().max()<1e-6))
 feet=r.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0]
 leg_ids=[t._joint_ids[i] for i in t.leg_slots]
 mass=r.root_physx_view.get_masses().to(t._env.device)
 com=(r.data.body_com_pos_w*mass[:,:,None]).sum(1)/mass.sum(1)[:,None]
 acc=-5.*r.data.root_lin_vel_w;acc[:,2]=-8.*r.data.root_lin_vel_w[:,2]
 force=mass.sum(1)[:,None]*(acc.clamp(-.5,.5)+torch.tensor([0.,0.,9.81],device=t._env.device))
 moment=(-2.*r.data.root_ang_vel_w).clamp(-4.,4.)
 loads,residual=allocate_wrench(r.data.body_pos_w[:,feet],com,force,moment,minimum_normal=12.,friction=.3)
 torque=leg_torques(r,feet,leg_ids,loads)
 ratio=float((torque.abs()/r.data.joint_effort_limits[:,leg_ids]).max())
 feasible=bool(residual[:,:3].abs().max()<=.5 and residual[:,3:].abs().max()<=.1)
 limits=r.data.soft_joint_pos_limits[:,t._joint_ids]
 q=r.data.joint_pos[:,t._joint_ids];target=r.data.joint_pos_target[:,t._joint_ids]
 within=bool(((q>=limits[...,0])&(q<=limits[...,1])&(target>=limits[...,0])&(target<=limits[...,1])).all())
 return feasible and ratio<.75 and within,dict(kinematic_precheck=True,request_zero_required=require_zero_request,request_zero_actual=bool(t.request.abs().max()<1e-6),wrench_feasible=feasible,effort_ratio=ratio,soft_limits=within,residual=residual[0].tolist(),loads=loads[0].tolist())


class SupportedBrake:
 def __init__(self,t,age,arm_reference_velocity=None):
  self.t=t;r=t._asset;self.start=age
  self.feet=r.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0]
  self.leg_ids=[t._joint_ids[i] for i in t.leg_slots]
  self.origin=r.data.root_pos_w.clone();self.orientation=r.data.root_quat_w.clone()
  self.mass=r.root_physx_view.get_masses().to(t._env.device)
  current=r.data.joint_pos_target[:,t._joint_ids].clone()
  self.initial_leg=current[:,t.leg_slots].clone()
  self.arm_pose=r.data.joint_pos[:,t.arm_ids].clone()
  # Issued position is continuous; measured dq seeds the new braking law.
  # This does not claim continuity of the old NAV target derivative.
  seed_velocity=r.data.joint_vel[:,t._joint_ids].clone()
  if arm_reference_velocity is not None:
   assert arm_reference_velocity.shape==seed_velocity[:,t.arm_slots].shape and bool(torch.isfinite(arm_reference_velocity).all())
   assert bool((arm_reference_velocity.abs()<=.45002).all())
   # Normalize only float32 roundoff at the original .45 limit.
   seed_velocity[:,t.arm_slots]=arm_reference_velocity.clamp(-.45,.45)
  self.reference=BoundedReference(current[0].tolist(),seed_velocity[0].tolist(),[1.]*12+[.45]*6,[4.]*12+[1.]*6,t._env.step_dt)
  self.details={}
 def target(self,age):
  t=self.t;r=t._asset
  com=(r.data.body_com_pos_w*self.mass[:,:,None]).sum(1)/self.mass.sum(1)[:,None]
  acc=12.*(self.origin-r.data.root_pos_w)-5.*r.data.root_lin_vel_w
  acc[:,2]=25.*(self.origin[:,2]-r.data.root_pos_w[:,2])-8.*r.data.root_lin_vel_w[:,2]
  if hasattr(self,'tracking_integral_acceleration'):acc=acc+self.tracking_integral_acceleration
  force=self.mass.sum(1)[:,None]*(acc.clamp(-.5,.5)+torch.tensor([0.,0.,9.81],device=t._env.device))
  error=quat_mul(self.orientation,quat_conjugate(r.data.root_quat_w))
  rotation=2.*error[:,1:]*torch.where(error[:,:1]<0.,-1.,1.)
  moment=(8.*rotation-2.*r.data.root_ang_vel_w).clamp(-4.,4.)
  loads,residual=allocate_wrench(r.data.body_pos_w[:,self.feet],com,force,moment)
  fallback=None
  if float(residual[:,:3].abs().max())>.5 or float(residual[:,3:].abs().max())>.1:
   replacement,fallback=refine_stance_wrench(r.data.body_pos_w[:,self.feet],com,force,moment,loads)
   if replacement is not None:loads,residual=replacement
  self.details=dict(loads=loads[0].tolist(),residual=residual[0].tolist(),fallback=fallback)
  if hasattr(self,'tracking_integral_acceleration'):self.details['tracking_integral_acceleration']=self.tracking_integral_acceleration[0].tolist()
  if float(residual[:,:3].abs().max())>.5 or float(residual[:,3:].abs().max())>.1:raise ValueError('Supported brake wrench infeasible')
  torque=leg_torques(r,self.feet,self.leg_ids,loads)
  cap=.75*r.data.joint_effort_limits[:,self.leg_ids]
  self.details['unclipped_leg_effort_ratio']=float((torque.abs()/r.data.joint_effort_limits[:,self.leg_ids]).max())
  loaded=r.data.joint_pos[:,self.leg_ids]+torch.maximum(torch.minimum(torque,cap),-cap)/30.+.6*r.data.joint_vel[:,self.leg_ids]/30.
  u=max(0.,min(1.,(age-self.start)/.3));blend=u**3*(10.-15.*u+6.*u*u)
  desired=torch.tensor(self.reference.position,device=t._env.device)[None]
  desired[:,t.leg_slots]=(1.-blend)*self.initial_leg+blend*loaded
  gravity=r.root_physx_view.get_gravity_compensation_forces()
  columns=t.arm_ids if gravity.shape[1]==r.num_joints else [j+6 for j in t.arm_ids]
  bounds=r.data.soft_joint_pos_limits[:,t.arm_ids]
  desired[:,t.arm_slots]=torch.maximum(torch.minimum(self.arm_pose+gravity[:,columns]/t.arm_pd[0],bounds[...,1]-.01),bounds[...,0]+.01)
  if hasattr(self,'conversion_start'):
   u=max(0.,min(1.,(age-self.conversion_start)/6.));blend=u**3*(10.-15.*u+6.*u*u)
   desired[:,t.arm_slots]=self.conversion_source+blend*(self.conversion_goal-self.conversion_source)
   self.details['arm_conversion_fraction']=u
   self.details['arm_conversion_goal']=self.conversion_goal[0].tolist()

  target=torch.tensor(self.reference.advance(desired[0].tolist()),device=t._env.device)[None]
  limits=r.data.soft_joint_pos_limits[:,t._joint_ids]
  if not bool(((target>=limits[...,0])&(target<=limits[...,1])).all()):raise ValueError('Supported brake reference outside original soft limits')
  return target

 def begin_arm_conversion(self,age):
  t=self.t;r=t._asset;bounds=r.data.soft_joint_pos_limits[:,t.arm_ids]
  self.conversion_start=age
  self.conversion_source=torch.tensor(self.reference.position,device=t._env.device)[None][:,t.arm_slots].clone()
  # Exact original CLIMB PD reference, not a new measured posture or bank state.
  self.conversion_goal=torch.maximum(torch.minimum(r.data.default_joint_pos[:,t.arm_ids],bounds[...,1]),bounds[...,0])
