"""Bounded command correction after persistent measured failure to advance.
The correction is a NAV request, not a direct actuator output or success gate.
"""
class TrackingCompensation:
 def __init__(self):
  self.best=None;self.last_advance=None;self.last_age=None;self.active=False;self.bias=0.;self.event=None
 def update(self,age,x,error_x,measured_forward,assist,stopping):
  self.event=None
  if self.last_age is not None and age<=self.last_age:return self.bias
  dt=0. if self.last_age is None else age-self.last_age;self.last_age=age
  if not assist:return self.bias
  if self.best is None:self.best=x;self.last_advance=age
  if x>self.best+.005:self.best=x;self.last_advance=age
  if not self.active and age-self.last_advance>=10. and error_x>.05 and not stopping:
   self.active=True;self.event=dict(time_s=age,no_progress_s=age-self.last_advance,error_x_m=error_x,measured_forward_mps=measured_forward)
  if self.active:
   if stopping or error_x<.035:self.bias=max(0.,self.bias-.04*dt)
   else:
    desired_actual=min(.08,max(0.,1.2*error_x))
    error=max(-.05,min(.05,desired_actual-measured_forward))
    self.bias=max(0.,min(.08,self.bias+.2*error*dt))
  return self.bias
