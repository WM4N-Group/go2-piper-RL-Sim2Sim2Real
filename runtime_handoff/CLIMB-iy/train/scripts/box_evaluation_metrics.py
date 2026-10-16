"""Equal-episode accounting for parallel skill evaluations."""

import torch


class ClimbGaitTelemetry:
    """Control-rate support quality; force peaks include the physics sensor history."""

    def __init__(self, count, device, dt):
        self.dt = dt
        self.samples = torch.zeros(count, device=device)
        self.tripod_samples = torch.zeros_like(self.samples)
        self.flight = torch.zeros_like(self.samples)
        self.max_flight = torch.zeros_like(self.samples)
        self.airtime = torch.zeros_like(self.samples)
        self.max_vertical_speed = torch.zeros_like(self.samples)
        self.max_foot_force = torch.zeros_like(self.samples)

    def update(self, active, elapsed, feet_force, force_history, vertical_speed):
        selected = active & (elapsed >= .10)
        support = (feet_force[..., 2] > 2.).sum(dim=1)
        airborne = support == 0
        self.samples += selected
        self.tripod_samples += selected & (support >= 3)
        self.flight = torch.where(selected, torch.where(airborne, self.flight + self.dt, 0.), self.flight)
        self.max_flight = torch.maximum(self.max_flight, self.flight)
        self.airtime += (selected & airborne) * self.dt
        self.max_vertical_speed = torch.maximum(self.max_vertical_speed, torch.where(selected, vertical_speed.abs(), 0.))
        force_peak = force_history.norm(dim=-1).amax(dim=(1, 2))
        self.max_foot_force = torch.maximum(self.max_foot_force, torch.where(selected, force_peak, 0.))

    def reset_episode(self, env_ids):
        # Aggregate maxima remain, but flight cannot continue across a simulator reset.
        self.flight[env_ids] = 0

    def report(self):
        return {"sample_dt": self.dt, "initial_exclusion_s": .10, "support_force_z_threshold_n": 2.,
                "at_least_three_feet_fraction": (self.tripod_samples / self.samples.clamp_min(1)).tolist(),
                "max_continuous_airtime_s": self.max_flight.tolist(), "total_airtime_s": self.airtime.tolist(),
                "max_abs_base_vertical_speed": self.max_vertical_speed.tolist(),
                "max_single_foot_force_n": self.max_foot_force.tolist(), "samples": self.samples.tolist()}


class EpisodeQuota:
    def __init__(self, num_envs, episodes_per_env, device):
        if num_envs < 1 or episodes_per_env < 1:
            raise ValueError("Evaluation quotas must be positive")
        self.quota = episodes_per_env
        self.completed = torch.zeros(num_envs, dtype=torch.int64, device=device)
        self.successful = torch.zeros_like(self.completed)

    @property
    def active(self):
        return self.completed < self.quota

    def record(self, dones, successes):
        counted = self.active & dones.bool()
        self.completed += counted.long()
        self.successful += (counted & successes.bool()).long()
        return counted

    def terminal_snapshot(self, env_ids, **fields):
        selected = env_ids[self.active[env_ids]]
        values = {name: tensor[selected].tolist() for name, tensor in fields.items()}
        episodes = (self.completed[selected] + 1).tolist()
        return [
            {"env_id": env_id, "episode": episodes[index], **{name: value[index] for name, value in values.items()}}
            for index, env_id in enumerate(selected.tolist())
        ]


class EpisodeHistory:
    """Bounded per-environment state history, copied before automatic resets."""

    def __init__(self, num_envs, capacity, device):
        if num_envs < 1 or capacity < 1:
            raise ValueError("Episode history requires positive dimensions")
        self.num_envs, self.capacity = num_envs, capacity
        self.next = torch.zeros(num_envs, dtype=torch.long, device=device)
        self.count = torch.zeros_like(self.next)
        self.fields = {}

    def append(self, active, **fields):
        if active.shape != (self.num_envs,) or active.dtype != torch.bool or active.device != self.next.device:
            raise ValueError("History activity must be a matching boolean mask")
        if not fields or (self.fields and fields.keys() != self.fields.keys()):
            raise ValueError("History fields must be nonempty and consistent")
        for name, value in fields.items():
            if value.ndim < 1 or value.shape[0] != self.num_envs or value.device != self.next.device:
                raise ValueError(f"Invalid history field: {name}")
            if name in self.fields:
                previous = self.fields[name]
                if previous.shape[1:] != value.shape or previous.dtype != value.dtype:
                    raise ValueError(f"History field shape/dtype changed: {name}")
        if not self.fields:
            self.fields = {name: value.new_empty((self.capacity, *value.shape)) for name, value in fields.items()}
        selected = active.nonzero(as_tuple=False).flatten()
        slots = self.next[selected]
        for name, value in fields.items():
            self.fields[name][slots, selected] = value.detach()[selected]
        self.next[selected] = (slots + 1) % self.capacity
        self.count[selected] = (self.count[selected] + 1).clamp(max=self.capacity)

    def snapshot(self, env_id):
        count = int(self.count[env_id].item())
        indices = (torch.arange(count, device=self.next.device) + self.next[env_id] - count) % self.capacity
        values = {name: value[indices, env_id].tolist() for name, value in self.fields.items()}
        return [{name: value[i] for name, value in values.items()} for i in range(count)]

    def finish(self, terminal_states, termination_names, first_terminal_index):
        """Save failures only; clear both successful and failed episode histories."""
        settled = termination_names.index("box_settled")
        safety = [i for i, name in enumerate(termination_names) if name not in ("time_out", "box_settled")]
        records = []
        for offset, state in enumerate(terminal_states):
            env_id = state["env_id"]
            flags = state["termination_flags"]
            successful = flags[settled] and not any(flags[i] for i in safety)
            if not successful:
                records.append({"env_id": env_id, "episode": state["episode"],
                                "terminal_state_index": first_terminal_index + offset,
                                "pre_step_samples": self.snapshot(env_id)})
            self.next[env_id] = 0
            self.count[env_id] = 0
        return records


class JointMotionTelemetry:
    """Accumulate control-step motion metrics for selected environments."""

    def __init__(self, initial_target, step_dt, saturation_ratio=0.98):
        self.previous_target = initial_target.clone()
        self.step_dt = step_dt
        self.saturation_ratio = saturation_ratio
        self.max_target_step = torch.zeros(initial_target.shape[1], device=initial_target.device)
        self.max_velocity = torch.zeros_like(self.max_target_step)
        self.max_acceleration = torch.zeros_like(self.max_target_step)
        self.max_mechanical_power = torch.zeros_like(self.max_target_step)
        self.saturation_seconds = torch.zeros_like(initial_target)
        self.max_base_angular_speed_xy = torch.zeros(initial_target.shape[0], device=initial_target.device)

    def sample(self, active, target, velocity, acceleration, torque, effort_limits, base_angular_velocity):
        if not active.any():
            return
        target_step = (target[active] - self.previous_target[active]).abs()
        self.max_target_step = torch.maximum(self.max_target_step, target_step.amax(dim=0))
        self.max_velocity = torch.maximum(self.max_velocity, velocity[active].abs().amax(dim=0))
        self.max_acceleration = torch.maximum(self.max_acceleration, acceleration[active].abs().amax(dim=0))
        power = (torque[active] * velocity[active]).abs()
        self.max_mechanical_power = torch.maximum(self.max_mechanical_power, power.amax(dim=0))
        ratio = torque[active].abs() / effort_limits[active].clamp_min(1e-6)
        self.saturation_seconds[active] += (ratio >= self.saturation_ratio).float() * self.step_dt
        angular_speed = torch.linalg.vector_norm(base_angular_velocity[active, :2], dim=1)
        self.max_base_angular_speed_xy[active] = torch.maximum(
            self.max_base_angular_speed_xy[active], angular_speed
        )
        self.previous_target[active] = target[active]

    def reset_reference(self, reset, target):
        self.previous_target[reset] = target[reset]

    def summary(self):
        return {
            "max_abs_joint_target_step": self.max_target_step.tolist(),
            "max_abs_joint_velocity": self.max_velocity.tolist(),
            "max_abs_joint_acceleration": self.max_acceleration.tolist(),
            "max_abs_joint_mechanical_power": self.max_mechanical_power.tolist(),
            "torque_saturation_threshold_ratio": self.saturation_ratio,
            "torque_saturation_seconds_per_env_joint": self.saturation_seconds.tolist(),
            "max_base_angular_speed_xy_per_env": self.max_base_angular_speed_xy.tolist(),
        }
