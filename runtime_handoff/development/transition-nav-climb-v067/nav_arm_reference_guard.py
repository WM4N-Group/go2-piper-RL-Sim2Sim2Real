"""Explicit smooth arm reference intersected with original PD/soft-limit domain."""
import torch
class ArmReferenceInfeasible(ValueError):
 def __init__(self,details):super().__init__('NAV arm smooth/effort interval empty');self.details=details
class ArmReferenceGuard:
 def __init__(self,position,velocity,dt):
  assert position.shape==velocity.shape and bool(torch.isfinite(position).all()) and bool(torch.isfinite(velocity).all())
  if bool((velocity.abs()>.45001).any()):raise ValueError('Initial arm command velocity exceeds .45rad/s')
  self.position=position.clone();self.velocity=velocity.clone();self.dt=dt
 def step(self,raw,q,dq,kp,kd,effort,lower,upper):
  dt=self.dt;vmin=(self.velocity-dt).clamp_min(-.45);vmax=(self.velocity+dt).clamp_max(.45)
  lo_rate=self.position+dt*vmin;hi_rate=self.position+dt*vmax
  # Bound next reference speed so an acceleration-limited stop remains possible
  # before either STATIC original soft limit. dt*v + v^2/(2*a) <= distance,
  # with a=1 rad/s^2, accounts conservatively for the next command interval.
  soft_lo=lower+1e-6;soft_hi=upper-1e-6
  room_lo=(self.position-soft_lo).clamp_min(0.)
  room_hi=(soft_hi-self.position).clamp_min(0.)
  stop_lo=(torch.sqrt(dt*dt+2.*room_lo)-dt).clamp(min=0.,max=.45)
  stop_hi=(torch.sqrt(dt*dt+2.*room_hi)-dt).clamp(min=0.,max=.45)
  viable_lo=self.position-dt*stop_lo;viable_hi=self.position+dt*stop_hi
  c0=q+kd/kp*dq;c1=c0+.04*dq;radius=.85*effort/kp
  lo=torch.maximum(torch.maximum(torch.maximum(lo_rate,soft_lo),viable_lo),torch.maximum(c0,c1)-radius)
  hi=torch.minimum(torch.minimum(torch.minimum(hi_rate,soft_hi),viable_hi),torch.minimum(c0,c1)+radius)
  if bool((lo>hi).any()):
   raise ArmReferenceInfeasible(dict(position=self.position[0].tolist(),velocity=self.velocity[0].tolist(),q=q[0].tolist(),dq=dq[0].tolist(),raw=raw[0].tolist(),lower=lo[0].tolist(),upper=hi[0].tolist(),soft_lower=soft_lo[0].tolist(),soft_upper=soft_hi[0].tolist(),rate_lower=lo_rate[0].tolist(),rate_upper=hi_rate[0].tolist(),viable_lower=viable_lo[0].tolist(),viable_upper=viable_hi[0].tolist()))
  bounded_raw=torch.maximum(torch.minimum(raw,soft_hi),soft_lo)
  delta=bounded_raw-self.position;stop_speed=torch.sqrt(2.*delta.abs()).clamp(max=.45)
  desired_v=torch.maximum(torch.minimum(delta.sign()*stop_speed,vmax),vmin)
  target=torch.maximum(torch.minimum(self.position+dt*desired_v,hi),lo)
  target=torch.where((raw>=lo)&(raw<=hi),raw,target)
  velocity=(target-self.position)/dt;acceleration=(velocity-self.velocity)/dt
  assert bool((velocity.abs()<=.45002).all()) and bool((acceleration.abs()<=1.002).all())
  def ratio(x):return torch.maximum((kp*(x-q)-kd*dq).abs()/effort,(kp*(x-q-.04*dq)-kd*dq).abs()/effort).max()
  details=dict(changed=bool((target!=raw).any()),maximum_correction_rad=float((target-raw).abs().max()),predicted_ratio_before=float(ratio(raw)),predicted_ratio_after=float(ratio(target)),horizon_s=.04,reserve_ratio=.85,command_speed_max=float(velocity.abs().max()),command_acceleration_max=float(acceleration.abs().max()),soft_limit_braking_active=bool(((target<lo_rate)|(target>hi_rate)).any() or ((viable_lo>lo_rate)&(target<=viable_lo+1e-7)).any() or ((viable_hi<hi_rate)&(target>=viable_hi-1e-7)).any()),soft_limit_min_margin_rad=float(torch.minimum(target-soft_lo,soft_hi-target).min()),scope='smooth reference plus static soft-limit stopping envelope and original forecast intersection; actual torque gate remains')
  self.position=target.clone();self.velocity=velocity.clone();return target,details
