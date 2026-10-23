"""Keep an arrival stop intent long enough for the unchanged request slew.
This is not a success predicate; original position/contact/brake gates decide.
"""
class ArrivalStopLatch:
 def __init__(self):
  self.active=False;self.start=None;self.last=None;self.event=None;self.minimum_hold=1.
 def update(self,age,error,request_zero,calm,enter_distance=.025,minimum_hold=1.):
  assert .025<=enter_distance<=.080001 and 1.<=minimum_hold<=2.300001
  self.event=None
  if self.last is not None and age<=self.last:return self.active
  self.last=age
  if self.active:
   held=age-self.start
   # Retry approach after significant drift, or after a calm stop outside the
   # ORIGINAL 35mm completion domain. Never widen completion tolerance.
   if held>=self.minimum_hold and (error>.05 or (request_zero and calm and error>=.035)):
    self.active=False;self.event=dict(time_s=age,event='arrival_stop_released_for_reapproach',error_m=error,held_s=held)
  elif error<enter_distance:
   self.active=True;self.start=age;self.minimum_hold=minimum_hold;self.event=dict(time_s=age,event='arrival_stop_latched',error_m=error,entry_distance_m=enter_distance,minimum_hold_s=minimum_hold)
  return self.active
