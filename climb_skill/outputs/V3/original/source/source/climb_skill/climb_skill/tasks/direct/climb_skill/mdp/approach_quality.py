"""接近/跨沿诊断及固定参考步态升级门槛。所有统计在自动reset之前更新。"""
import torch


def playback_reference(config, expected_hash, device):
    from .....learning.amp import AMPConfig, load_pairs
    from .....learning.motion_reference import MotionReference, mirror_transitions
    cfg = AMPConfig(**config)
    pairs, digest, _ = load_pairs(cfg.dataset, device)
    if digest != expected_hash:
        raise ValueError('Gait evaluation reference differs from checkpoint dataset')
    if cfg.mirror_reference:
        pairs = torch.cat((pairs, mirror_transitions(pairs)))
    return MotionReference(pairs, cfg.reference_position_scale, cfg.reference_velocity_scale)


def front_clearance(feet, forces, heights, landed, cfg):
    """只约束未首次落台的前脚摆动；临近箱沿要求足底逐渐超过箱高。

    不指定关节角/固定步序，不给地面支撑脚抬升成本，也不奖励悬脚。
    箱沿之后逐渐解除净空，允许脚下降到台面承重。
    """
    x = feet[:, :2, 0] - cfg.box_front
    before = ((x + cfg.front_clearance_distance) / cfg.front_clearance_distance).clamp(0, 1)
    after = (1 - x / max(cfg.top_margin, .01)).clamp(0, 1)
    gate = torch.minimum(before, after)
    swing = forces[:, :2, 2] < cfg.support_force
    active = swing & ~landed & (feet[:, :2, 1].abs() < cfg.box_width / 2)
    desired = gate * (heights[:, None] + cfg.front_clearance_margin)
    deficit = ((desired - (feet[:, :2, 2] - cfg.foot_radius)) / cfg.front_clearance_scale).clamp(0, 1)
    return (gate * active * deficit.square()).mean(-1)


class ApproachQuality:
    def __init__(self, count, device, cfg):
        self.cfg, self.reference = cfg, None
        z = lambda *s: torch.zeros(count, *s, device=device)
        # 平地/箱顶分别累计，不让长平地段掩盖箱顶的坏步态。
        self.seconds, self.cost_sum, self.good_seconds = z(2), z(2), z(2)
        self.leg_sum = z(2, 4)
        self.landing_time = z(2)
        self.landed = z(2).bool()
        self.new_landing = z(2).bool()
        self.attempt = z(2).bool()
        self.ground_time = z(2)
        self.retries = z(2).long()
        self.wall_seconds = z(2)
        self.clearance = z()
        self.before = z(30)
        self.before_gate = z()

    def reset(self, ids):
        for name in ('seconds', 'cost_sum', 'good_seconds', 'leg_sum', 'landing_time',
                     'landed', 'new_landing', 'attempt', 'ground_time', 'retries',
                     'wall_seconds', 'clearance', 'before', 'before_gate'):
            getattr(self, name)[ids] = 0

    def accumulate(self, cost, legs, phase, eligible, speed, dt):
        cfg = self.cfg
        finite = torch.isfinite(cost) & torch.isfinite(legs).all(-1) & torch.isfinite(speed)
        # 坏数值计为坏帧，不通过筛掉坏帧美化质量。
        cost = torch.nan_to_num(cost, nan=1., posinf=1., neginf=1.)
        legs = torch.nan_to_num(legs, nan=1., posinf=1., neginf=1.)
        good = (finite & (cost <= cfg.gait_frame_cost_max)
                & (legs.amax(-1) <= cfg.gait_leg_cost_max)
                & (speed >= cfg.gait_speed_min) & (speed <= cfg.gait_speed_max))
        for index in (0, 1):
            weight = (eligible & (phase == index)).float() * dt
            self.seconds[:, index] += weight
            self.cost_sum[:, index] += weight * cost
            self.leg_sum[:, index] += weight[:, None] * legs
            self.good_seconds[:, index] += weight * good

    def passed(self):
        cfg = self.cfg
        den = self.seconds.clamp_min(1e-6)
        enough = self.seconds >= self.seconds.new_tensor([cfg.gait_ground_seconds, cfg.gait_top_seconds]) - 1e-6
        quality = ((self.cost_sum / den <= cfg.gait_mean_cost_max)
                   & ((self.leg_sum / den[..., None]).amax(-1) <= cfg.gait_leg_cost_max)
                   & (self.good_seconds / den >= cfg.gait_good_fraction_min))
        return (enough & quality).all(-1)

    def update(self, env, pos, feet, forces, support):
        from .amp import snapshot
        from .startup import movement_gain
        cfg, dt = self.cfg, env.step_dt
        if self.reference is None:
            raise RuntimeError('Attach fixed motion reference before stepping approach-quality task')
        after, gate = snapshot(env)
        # 只评价完全释放后的平地/箱顶；跨沿和起步准备不要求模仿平地参考。
        ground = (pos[:, 0] + .45 < cfg.box_front)
        top = ((pos[:, 0] - .45 > cfg.box_front)
               & (pos[:, 0] + .45 < cfg.box_front + cfg.box_length)
               & (pos[:, 1].abs() + .2 < cfg.box_width / 2))
        eligible = ((self.before_gate >= .999) & (gate >= .999)
                    & (movement_gain(env) >= .999) & (ground | top))
        phase = torch.where(top, 1, 0)
        # 只有有效平面样本做参考比较；不把跨台阶转换硬套平地运动。
        ids = eligible.nonzero().flatten()
        cost = torch.zeros_like(gate)
        legs = gate.new_zeros((len(gate), 4))
        if len(ids):
            cost[ids], legs[ids] = self.reference.cost(torch.cat((self.before[ids], after[ids]), -1))
        self.accumulate(cost, legs, phase, eligible, env.robot.data.root_lin_vel_w[:, 0], dt)
        self.clearance = front_clearance(feet, forces, env.heights, self.landed, cfg)
        self.landing_time = torch.where(support[:, :2], self.landing_time + dt, 0.)
        self.new_landing = (self.landing_time >= cfg.front_landing_seconds - 1e-6) & ~self.landed
        self.landed |= self.new_landing
        near = ((feet[:, :2, 0] > cfg.box_front - cfg.front_clearance_distance)
                & (feet[:, :2, 0] < cfg.box_front + cfg.top_margin))
        lifted = feet[:, :2, 2] - cfg.foot_radius > .04
        self.attempt |= near & lifted & ~self.landed
        ground_contact = ((feet[:, :2, 2] - cfg.foot_radius).abs() <= .025) & (forces[:, :2, 2] >= cfg.support_force)
        self.ground_time = torch.where(ground_contact, self.ground_time + dt, 0.)
        failed_attempt = self.attempt & ~self.landed & (self.ground_time >= .06)
        self.retries += failed_attempt.long()
        self.attempt &= ~(failed_attempt | self.landed)
        wall = near & (feet[:, :2, 2] - cfg.foot_radius < env.heights[:, None]) & (forces[:, :2, :2].norm(dim=-1) > cfg.support_force)
        self.wall_seconds += wall * dt

    def record(self, i):
        den = self.seconds[i].clamp_min(1e-6)
        return dict(gait_quality_pass=bool(self.passed()[i]),
                    gait_seconds_ground_top=self.seconds[i].tolist(),
                    gait_cost_ground_top=(self.cost_sum[i] / den).tolist(),
                    gait_leg_cost_ground_top=(self.leg_sum[i] / den[:, None]).tolist(),
                    gait_good_fraction_ground_top=(self.good_seconds[i] / den).tolist(),
                    front_retry_count=self.retries[i].tolist(),
                    front_wall_contact_seconds=self.wall_seconds[i].tolist(),
                    front_confirmed_landing=self.landed[i].tolist())
