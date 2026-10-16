"""Control-step PD reference envelope; not a certified dynamic safety model.

Use measured velocity over a 40ms horizon (20ms command hold + up to20ms
actuator delay). Keep existing actuator queues and actual substep termination.
The90% predicted bound reserves margin for unmodelled acceleration/contact.
"""
import torch

def guard_reference(native, position, velocity, stiffness, damping, limits, lower, upper, horizon=.04, reserve=.90):
    if not 0.<reserve<.98 or horizon<=0. or bool((stiffness<=0.).any()):
        raise ValueError('Invalid native arm effort guard contract')
    center0=position+damping/stiffness*velocity
    center1=center0+horizon*velocity
    radius=reserve*limits/stiffness
    minimum=torch.maximum(torch.maximum(center0,center1)-radius,lower)
    maximum=torch.minimum(torch.minimum(center0,center1)+radius,upper)
    if bool((minimum>maximum).any()):raise ValueError('No feasible native arm PD reference interval')
    guarded=torch.maximum(torch.minimum(native,maximum),minimum)
    before=torch.stack((stiffness*(native-position)-damping*velocity,stiffness*(native-position-horizon*velocity)-damping*velocity),dim=-1)
    after=torch.stack((stiffness*(guarded-position)-damping*velocity,stiffness*(guarded-position-horizon*velocity)-damping*velocity),dim=-1)
    return guarded,dict(changed=bool((guarded!=native).any()),maximum_correction_rad=float((guarded-native).abs().max()),predicted_ratio_before=float((before.abs()/limits[...,None]).max()),predicted_ratio_after=float((after.abs()/limits[...,None]).max()),horizon_s=horizon,reserve_ratio=reserve)
