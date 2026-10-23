"""Measure persistent low-speed NAV stagnation; no physics/state writes."""
from collections import deque
class ProgressMonitor:
 def __init__(self):
  self.samples=deque();self.active=False;self.trigger=None
 def update(self,age,x,error_x,forward_requested):
  if self.samples and age<=self.samples[-1][0]:return self.active
  self.samples.append((age,x))
  while self.samples and age-self.samples[0][0]>2.0001:self.samples.popleft()
  if not self.active and age-self.samples[0][0]>=1.999 and x-self.samples[0][1]<.005 and error_x>.025 and forward_requested>0:
   self.active=True;self.trigger=dict(time_s=age,progress2s_m=x-self.samples[0][1],forward_error_m=error_x,previous_forward_request=forward_requested)
  return self.active
