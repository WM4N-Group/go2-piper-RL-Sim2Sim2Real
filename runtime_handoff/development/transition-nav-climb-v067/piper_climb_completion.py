"""Independent CLIMB endpoint qualification; never implies NAV readiness.

Consume measured, ordered samples without resetting physics. The caller must
supply the native safety status, including any failure latched between samples.
"""
from dataclasses import dataclass
import math


def norm(values):
    return math.sqrt(sum(value * value for value in values))


@dataclass
class ClimbCompletion:
    required_stable_s: float = 3.0
    stable_since: float | None = None
    previous_time: float | None = None
    failed: bool = False

    def __post_init__(self):
        if not math.isfinite(self.required_stable_s) or self.required_stable_s < 3.:
            raise ValueError("CLIMB completion requires at least three stable seconds")

    def update(self, sample, *, time_s, safety_ok):
        if not math.isfinite(time_s) or (self.previous_time is not None and time_s <= self.previous_time):
            raise ValueError('CLIMB completion requires strictly increasing physical time')
        # A missing sample cannot prove continuous stability.
        gap = self.previous_time is not None and time_s-self.previous_time > .020001
        self.previous_time = time_s
        self.failed |= not safety_ok
        try:
            feet = sample['feet_position']
            forces = sample['foot_contact_force_z']
            remaining = [max(0., sample['platform_final_goal'][i]-sample['guidance_body_target'][i]) for i in (0, 2)]
            tracking = [a-b for a,b in zip(sample['guidance_body_target'], sample['robot_position'])]
            numeric = [v for foot in feet for v in foot] + forces + sample['platform_final_goal'] + sample['guidance_body_target'] + sample['robot_position'] + sample['robot_velocity'] + sample['robot_angular_velocity'] + sample['guidance_command_limit_excess'] + [sample['guidance_reference_age']]
            shapes = all(len(sample[k])==3 for k in ('platform_final_goal','guidance_body_target','robot_position','robot_velocity','robot_angular_velocity')) and len(feet)==4 and all(len(f)==3 for f in feet) and len(forces)==4 and len(sample['guidance_command_limit_excess'])==4
            finite = all(math.isfinite(v) for v in numeric)
            gates = dict(
                safety=not self.failed,
                finite=finite,
                shapes=shapes,
                four_feet_on_platform=len(feet)==4 and all(.79 < f[0] < 1.91 and abs(f[1]) < .56 and .19 <= f[2] <= .26 for f in feet),
                four_loaded=len(forces)==4 and min(forces)>=8.,
                extension_complete=sample['platform_extension_completed']==2 and not sample['platform_extension_moving'],
                final_adjust_started=bool(sample['platform_final_started']),
                platform_hold=bool(sample['platform_hold_active']),
                final_reference_reached=norm(remaining)<=.002,
                reference_held=sample['guidance_reference_age']>=3.,
                body_tracking=norm(tracking)<.01,
                linear_stopped=norm(sample['robot_velocity'])<.025,
                angular_stopped=norm(sample['robot_angular_velocity'])<.1,
                command_limits=max(sample['guidance_command_limit_excess'])<1e-6,
            )
        except (KeyError, TypeError, ValueError, IndexError):
            gates = dict(complete_measurement=False, safety=not self.failed)
        ready = all(gates.values())
        if gap or not ready:
            self.stable_since = None
        if ready and self.stable_since is None:
            self.stable_since = time_s
        stable_s = time_s-self.stable_since if self.stable_since is not None else 0.
        return dict(complete=ready and stable_s+1e-9>=self.required_stable_s,
                    stable_s=stable_s, gates=gates, failure_latched=self.failed,
                    scope='CLIMB endpoint only; NAV handoff requires separate qualification')
