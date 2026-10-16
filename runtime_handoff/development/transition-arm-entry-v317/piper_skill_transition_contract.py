"""Versioned, simulator-independent handoff events; no actuator authority.

READY describes a measured boundary before the next skill's first action.
It never means that an untested hold/retreat controller is safe.
"""
from dataclasses import dataclass, fields
from enum import Enum
import math
from types import MappingProxyType
from collections.abc import Mapping

CONTRACT_VERSION = 1


class Phase(str, Enum):
    ACTIVE = "active"
    PREPARING = "preparing"
    READY = "ready"
    STARTED = "started"
    FAILED = "failed"


@dataclass(frozen=True)
class EntryState:
    step: int
    physical_time_s: float
    joint_names: tuple[str, ...]
    joint_position: tuple[float, ...]
    joint_velocity: tuple[float, ...]
    applied_position_target: tuple[float, ...]
    applied_torque: tuple[float, ...]
    history_valid_frames: int
    source_id: str
    object_id: str
    gates: Mapping[str, bool]
    stable_seconds: float

    def __post_init__(self):
        # A READY snapshot must not change when a caller reuses its gate dict.
        object.__setattr__(self, 'gates', MappingProxyType(dict(self.gates)))
        for name in ('joint_names', 'joint_position', 'joint_velocity',
                     'applied_position_target', 'applied_torque'):
            object.__setattr__(self, name, tuple(getattr(self, name)))

    def to_dict(self):
        result = {field.name: getattr(self, field.name) for field in fields(self)}
        result['gates'] = dict(self.gates)
        return result

    def validate(self):
        if type(self.step) is not int or type(self.history_valid_frames) is not int or self.history_valid_frames < 0:
            raise ValueError("Step and valid history length must be integer counts")
        if self.step < 0 or not math.isfinite(self.physical_time_s) or self.physical_time_s < 0:
            raise ValueError("Invalid physical clock")
        if len(self.joint_names) != 18 or len(set(self.joint_names)) != 18:
            raise ValueError("Expected an explicit unique 18-axis order")
        for values in (self.joint_position, self.joint_velocity,
                       self.applied_position_target, self.applied_torque):
            if len(values) != 18 or not all(math.isfinite(v) for v in values):
                raise ValueError("Missing/nonfinite 18-axis state")
        if not self.source_id or not self.object_id:
            raise ValueError("Source and object binding required")
        if not math.isfinite(self.stable_seconds) or self.stable_seconds < 0:
            raise ValueError("Invalid stable duration")


def skill_elapsed_seconds(episode_step, activation_step, control_dt):
    """Separate local startup age from the monotonically increasing task clock."""
    if not math.isfinite(control_dt) or control_dt <= 0 or not 0 <= activation_step <= episode_step:
        raise ValueError("Invalid skill clock")
    return (episode_step - activation_step) * control_dt


class Handoff:
    def __init__(self, source_skill, destination_skill, required_gates,
                 stable_seconds=0.5, history_frames=3):
        if not required_gates or not math.isfinite(stable_seconds) or stable_seconds <= 0 or history_frames < 1:
            raise ValueError("Explicit entry contract required")
        self.source_skill, self.destination_skill = source_skill, destination_skill
        self.required_gates = tuple(required_gates)
        self.stable_seconds, self.history_frames = stable_seconds, history_frames
        self.phase = Phase.ACTIVE
        self.events = []
        self._last_step = -1
        self._last_time = -1.0
        self._identity = None
        self.ready_state = None

    def _observe(self, state):
        state.validate()
        if state.step < self._last_step or state.physical_time_s < self._last_time:
            raise ValueError("Physical clock reset at handoff")
        identity = (state.joint_names, state.source_id, state.object_id)
        if self._identity is not None and identity != self._identity:
            raise ValueError("Source/object/joint order changed during handoff")
        self._identity = identity
        self._last_step, self._last_time = state.step, state.physical_time_s

    def _event(self, name, state, **extra):
        self.events.append(dict(contract_version=CONTRACT_VERSION,
                                event=name, step=state.step, time_s=state.physical_time_s,
                                source_skill=self.source_skill, destination_skill=self.destination_skill,
                                source_id=state.source_id, object_id=state.object_id, **extra))

    def begin(self, state):
        if self.phase != Phase.ACTIVE:
            raise ValueError("Handoff already started")
        self._observe(state)
        self.phase = Phase.PREPARING
        self._event("transition_started", state)

    def offer(self, state):
        if self.phase not in (Phase.PREPARING, Phase.READY):
            raise ValueError("No pending handoff")
        self._observe(state)
        eligible = (state.history_valid_frames >= self.history_frames
                    and state.stable_seconds >= self.stable_seconds
                    and all(state.gates.get(k) is True for k in self.required_gates))
        if not eligible:
            if self.phase == Phase.READY:
                self._event("transition_ready_revoked", state)
            self.phase, self.ready_state = Phase.PREPARING, None
            return False
        if self.phase != Phase.READY:
            self._event("transition_ready", state, entry_state=state.to_dict())
        elif self.ready_state != state:
            self._event("transition_ready_refreshed", state, entry_state=state.to_dict())
        self.phase, self.ready_state = Phase.READY, state
        return True

    def start(self, state, *, authorized):
        if self.phase != Phase.READY or authorized is not True:
            raise ValueError("Fresh readiness and explicit authorization required")
        if self.ready_state != state:
            raise ValueError("Recheck measured state after waiting; stale readiness")
        self._observe(state)
        self.phase = Phase.STARTED
        self._event("skill_started", state)

    def fail(self, state, reason):
        if not reason or self.phase in (Phase.FAILED, Phase.STARTED):
            raise ValueError("Invalid handoff failure")
        self._observe(state)
        self.phase, self.ready_state = Phase.FAILED, None
        self._event("transition_failed", state, reason=reason)


class BoundedReference:
    """Rate/acceleration bounded command state, not a support or safety controller.

    Seed from the last issued target and its measured command velocity. A moving
    desired target can cause tracking lag/overshoot; callers must check limits,
    contact and load separately. No measured joint state is written here.
    """
    def __init__(self, position, velocity, speed_limits, acceleration_limits, dt):
        n = len(position)
        if not n or any(len(x) != n for x in (velocity, speed_limits, acceleration_limits)):
            raise ValueError('Reference dimensions differ')
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('Invalid reference period')
        if not all(math.isfinite(v) for xs in (position, velocity, speed_limits, acceleration_limits) for v in xs):
            raise ValueError('Nonfinite reference')
        if any(v <= 0 for xs in (speed_limits, acceleration_limits) for v in xs):
            raise ValueError('Reference limits must be positive')
        if any(abs(v) > limit for v, limit in zip(velocity, speed_limits)):
            raise ValueError('Initial reference velocity exceeds contract')
        self.position, self.velocity = tuple(position), tuple(velocity)
        self.speed_limits, self.acceleration_limits, self.dt = tuple(speed_limits), tuple(acceleration_limits), dt

    def advance(self, desired):
        if len(desired) != len(self.position) or not all(math.isfinite(v) for v in desired):
            raise ValueError('Invalid desired reference')
        position, velocity = [], []
        for q, v, goal, vmax, accel in zip(self.position, self.velocity, desired, self.speed_limits, self.acceleration_limits):
            delta = goal-q
            braking_speed = math.sqrt(2*accel*abs(delta))
            wanted = math.copysign(min(abs(delta)/self.dt, vmax, braking_speed), delta)
            updated = max(v-accel*self.dt, min(v+accel*self.dt, wanted))
            updated = max(-vmax, min(vmax, updated))
            velocity.append(updated); position.append(q+self.dt*updated)
        self.position, self.velocity = tuple(position), tuple(velocity)
        return self.position
