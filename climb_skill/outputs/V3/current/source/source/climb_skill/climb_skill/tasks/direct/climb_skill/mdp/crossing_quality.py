"""足端驱动的跨沿质量：只改变学习引导/升级资格，不增加终止条件。

所有坐标为环境局部坐标。FL/FR/RL/RR分别跟踪；并不规定固定步序。
起脚距离是几何代理，不能替代运动学或动力学可达性求解。
"""
import torch
from .approach_quality import ApproachQuality, front_clearance


class CrossingQuality(ApproachQuality):
    def __init__(self, count, device, cfg):
        super().__init__(count, device, cfg)
        z = lambda *s: torch.zeros(count, *s, device=device)
        self.prev_feet = z(4, 3)
        self.speed_sum = z(2)
        self.speed_good_seconds = z(2)
        self.unsafe_time = z(4)
        self.max_attempt_x = z(4)
        self.prev_forces = z(4, 3)
        self.takeoff_x = z(4)
        self.have_takeoff = z(4).bool()
        self.active = z(4).bool()
        self.crossed = z(4).bool()
        self.confirmed = z(4).bool()
        self.failed = z(4).bool()
        self.new_failure = z(4).bool()
        self.load_time = z(4)
        self.return_time = z(4)
        self.wall_time = z(4)
        self.attempt_time = z(4)
        self.guidance = z()
        self.mixed_cost = z()
        self.mixed_seconds = z()
        self.mixed_good_seconds = z()
        self.reason_flags = z(4, 5).bool()  # 净空不足/回落/撞沿/不安全落点/超时

    def reset(self, ids):
        super().reset(ids)
        for name in ('speed_sum', 'speed_good_seconds', 'unsafe_time', 'max_attempt_x', 'prev_feet', 'prev_forces', 'takeoff_x', 'have_takeoff',
                     'active', 'crossed', 'confirmed', 'failed', 'new_failure',
                     'load_time', 'return_time', 'wall_time', 'attempt_time',
                     'guidance', 'mixed_cost', 'mixed_seconds', 'mixed_good_seconds', 'reason_flags'):
            getattr(self, name)[ids] = 0

    def capture(self, feet, forces):
        self.prev_feet.copy_(feet)
        self.prev_forces.copy_(forces)
        # 记住最后真实地面支撑点；普通摆动不等同于一次登台尝试。
        ground = ((feet[..., 2] - self.cfg.foot_radius).abs() <= .025)
        ground &= forces[..., 2] >= self.cfg.support_force
        ground &= feet[..., 0] < self.cfg.box_front
        self.takeoff_x = torch.where(ground, feet[..., 0], self.takeoff_x)
        self.have_takeoff |= ground

    def intent(self, feet, heights):
        cfg = self.cfg
        bottom = feet[..., 2] - cfg.foot_radius
        threshold = torch.minimum(torch.full_like(heights, cfg.crossing_intent_height),
                                  heights * cfg.crossing_intent_ratio)
        # 足底已经指向真实台阶并高于普通摆动阈值；不再按机身±45cm豁免。
        near = ((feet[..., 0] >= cfg.box_front - cfg.crossing_intent_distance)
                & (feet[..., 0] <= cfg.box_front + cfg.top_margin)
                & (feet[..., 1].abs() <= cfg.box_width / 2))
        advancing = feet[..., 0] > self.prev_feet[..., 0] + .001
        return near & advancing & (bottom >= threshold[:, None]) & ~self.confirmed

    def masks(self, feet, heights):
        cfg = self.cfg
        ascending = self.active | self.intent(feet, heights)
        # 已落台的腿重新参与参考；地面普通摆腿也参与，不能通过抬脚逃避检查。
        mask = ~ascending | self.confirmed
        ground = (feet[..., 0] < cfg.box_front).all(-1) & ~ascending.any(-1) & ~self.confirmed.any(-1)
        top = (self.confirmed.all(-1)
               & (feet[..., 0] >= cfg.box_front + cfg.top_margin).all(-1)
               & (feet[..., 0] <= cfg.box_front + cfg.box_length - cfg.top_margin).all(-1)
               & (feet[..., 1].abs() <= cfg.box_width / 2 - cfg.top_margin).all(-1)
               & (feet[..., 2] - cfg.foot_radius >= heights[:, None] - cfg.foot_height_tolerance).all(-1))
        return ground, top, mask

    def flat_gate(self, feet, heights):
        ground, top, _ = self.masks(feet, heights)
        return (ground | top).to(feet.dtype)

    def track(self, feet, forces, support, heights, dt):
        cfg = self.cfg
        x, bottom = feet[..., 0], feet[..., 2] - cfg.foot_radius
        px, pb = self.prev_feet[..., 0], self.prev_feet[..., 2] - cfg.foot_radius
        loaded = forces[..., 2] >= cfg.support_force
        cross = (px < cfg.box_front) & (x >= cfg.box_front) & ~self.confirmed
        self.active |= (self.intent(feet, heights) | cross) & ~self.confirmed
        # 控制步之间线性插值沿口足底高度；这是20ms采样代理，不是假称连续碰撞证明。
        fraction = ((cfg.box_front - px) / (x - px).clamp_min(1e-8)).clamp(0, 1)
        edge_bottom = pb + fraction * (bottom - pb)
        low_cross = cross & (edge_bottom < heights[:, None] + cfg.crossing_clearance_min)
        self.crossed |= cross
        self.load_time = torch.where(support, self.load_time + dt, 0.)
        new_confirm = (self.load_time >= cfg.front_landing_seconds - 1e-6) & ~self.confirmed
        self.confirmed |= new_confirm
        self.new_landing = new_confirm[:, :2]
        self.landed = self.confirmed[:, :2].clone()
        ground_load = loaded & (bottom.abs() <= .025) & (x < cfg.box_front)
        self.return_time = torch.where(self.active & ground_load, self.return_time + dt, 0.)
        returned = self.active & (self.return_time >= cfg.crossing_return_seconds - 1e-6)
        if cfg.quality_window_enabled and not cfg.curriculum_only_enabled:
            self.max_attempt_x = torch.where(self.active, torch.maximum(self.max_attempt_x, x), x)
            committed = self.crossed | (self.max_attempt_x >= cfg.box_front - cfg.crossing_commit_distance)
            ordinary_return = returned & ~committed
            returned &= committed
            self.active &= ~ordinary_return
        near_wall = ((x - cfg.box_front).abs() <= cfg.foot_radius + .02)
        wall = (near_wall & (bottom < heights[:, None] - .005)
                & (forces[..., :2].norm(dim=-1) >= cfg.support_force) & ~ground_load)
        self.active |= wall & ~self.confirmed
        self.wall_time = torch.where(wall & self.active, self.wall_time + dt, 0.)
        hit_wall = self.wall_time >= cfg.crossing_wall_seconds - 1e-6
        # 落在沿口/侧边等非安全区而承重，不能算成功落台。
        unsafe = (self.active & loaded & (bottom >= heights[:, None] - cfg.foot_height_tolerance)
                  & (x >= cfg.box_front) & ~support & ~self.confirmed)
        if cfg.quality_window_enabled and not cfg.curriculum_only_enabled:
            inside = ((x >= cfg.box_front + cfg.top_margin)
                      & (x <= cfg.box_front + cfg.box_length - cfg.top_margin)
                      & (feet[..., 1].abs() <= cfg.box_width / 2 - cfg.top_margin))
            at_top = (bottom - heights[:, None]).abs() <= cfg.foot_height_tolerance
            unsafe = self.active & loaded & at_top & (x >= cfg.box_front) & ~inside & ~self.confirmed
            self.unsafe_time = torch.where(unsafe, self.unsafe_time + dt, 0.)
            unsafe = self.unsafe_time >= cfg.crossing_unsafe_seconds - 1e-6
        self.attempt_time = torch.where(self.active & ~self.confirmed, self.attempt_time + dt, 0.)
        timeout = self.attempt_time >= cfg.crossing_timeout
        reasons = torch.stack((low_cross, returned, hit_wall, unsafe, timeout), -1)
        self.reason_flags |= reasons
        bad = reasons.any(-1)
        self.new_failure = bad & ~self.failed
        self.failed |= bad  # 本回合锁存，恢复上台不洗掉失败记录。
        self.retries += (returned[:, :2] & self.active[:, :2]).long()
        self.wall_seconds += wall[:, :2] * dt
        self.active &= ~(returned | self.confirmed)
        self.return_time = torch.where(self.active, self.return_time, 0.)
        # 距离只作软引导；地面正常步子不被惩罚。
        distance = cfg.box_front - self.takeoff_x
        takeoff = ((cfg.crossing_takeoff_min - distance).clamp_min(0)
                   + (distance - cfg.crossing_takeoff_max).clamp_min(0)) / cfg.crossing_takeoff_max
        landing = ((cfg.box_front + cfg.top_margin - x).clamp_min(0)
                   + (x - (cfg.box_front + cfg.box_length - cfg.top_margin)).clamp_min(0)
                   + (feet[..., 1].abs() - (cfg.box_width/2 - cfg.top_margin)).clamp_min(0))
        descending = bottom < pb
        landing = landing / max(cfg.top_margin, .01) * (self.crossed & descending)
        self.guidance = ((takeoff * self.have_takeoff + landing).clamp(0, 1) * self.active).mean(-1)
        self.clearance = front_clearance(feet, forces, heights, self.landed, cfg)

    def update(self, env, pos, feet, forces, support):
        from .amp import snapshot
        from .startup import movement_gain
        if self.reference is None:
            raise RuntimeError('Attach fixed motion reference before crossing-quality stepping')
        dt, cfg = env.step_dt, self.cfg
        before_ground, before_top, before_mask = self.masks(self.prev_feet, env.heights)
        self.track(feet, forces, support, env.heights, dt)
        after, _ = snapshot(env)
        ground, top, mask = self.masks(feet, env.heights)
        ready = movement_gain(env) >= .999
        eligible = ready & ((ground & before_ground) | (top & before_top))
        pairs = torch.cat((self.before, after), -1)
        cost = torch.zeros_like(self.clearance)
        legs = feet.new_zeros((len(feet), 4))
        ids = eligible.nonzero().flatten()
        if len(ids):
            cost[ids], legs[ids] = self.reference.cost(pairs[ids])
        self.accumulate(cost, legs, top.long(), eligible, env.robot.data.root_lin_vel_w[:, 0], dt)
        # 过渡帧只检查两端均未跨沿的腿，仍共享一个参考相位。
        mask &= before_mask
        mixed = ready & ~eligible & mask.any(-1)
        ids = mixed.nonzero().flatten()
        self.mixed_cost.zero_()
        good = torch.zeros_like(mixed)
        if len(ids):
            c, l = self.reference.cost(pairs[ids], leg_mask=mask[ids])
            self.mixed_cost[ids] = torch.nan_to_num(c, nan=1., posinf=1., neginf=1.)
            good[ids] = (torch.isfinite(c) & torch.isfinite(l).all(-1)
                         & (c <= cfg.gait_frame_cost_max) & (l.amax(-1) <= cfg.gait_leg_cost_max))
        self.mixed_seconds += mixed * dt
        self.mixed_good_seconds += good * dt

    def accumulate(self, cost, legs, phase, eligible, speed, dt):
        if not self.cfg.quality_window_enabled:
            return super().accumulate(cost, legs, phase, eligible, speed, dt)
        # 步态比例仅检查参考误差；速度另外按每段均值约束，不删除静止样本。
        finite = torch.isfinite(speed)
        for j in (0, 1):
            weight = (eligible & (phase == j)).float() * dt
            self.speed_sum[:, j] += weight * torch.nan_to_num(speed, nan=0., posinf=0., neginf=0.)
            self.speed_good_seconds[:, j] += weight * (finite & (speed >= self.cfg.gait_speed_min) & (speed <= self.cfg.gait_speed_max))
        representative = torch.full_like(speed, (self.cfg.gait_speed_min + self.cfg.gait_speed_max) / 2)
        representative = torch.where(finite, representative, float('nan'))
        super().accumulate(cost, legs, phase, eligible, representative, dt)

    def passed(self):
        mixed_ok = ((self.mixed_seconds <= 1e-6)
                    | (self.mixed_good_seconds / self.mixed_seconds.clamp_min(1e-6) >= self.cfg.gait_good_fraction_min))
        if self.cfg.quality_window_enabled:
            speed = self.speed_sum / self.seconds.clamp_min(1e-6)
            mixed_ok = ((speed >= self.cfg.gait_speed_min) & (speed <= self.cfg.gait_speed_max)).all(-1)
        return (super().passed() & ~self.failed.any(-1) & self.confirmed.all(-1)
                & self.crossed.all(-1) & mixed_ok)

    def record(self, i):
        result = super().record(i)
        result.update(crossing_failed_feet=self.failed[i].tolist(),
                      crossing_failure_reasons=self.reason_flags[i].tolist(),
                      crossing_reason_order=['low_clearance', 'returned_ground', 'wall_contact', 'unsafe_landing', 'timeout'],
                      crossing_confirmed_feet=self.confirmed[i].tolist(),
                      crossing_crossed_feet=self.crossed[i].tolist(),
                      mixed_gait_seconds=float(self.mixed_seconds[i]),
                      mixed_gait_good_fraction=float(self.mixed_good_seconds[i] / self.mixed_seconds[i].clamp_min(1e-6)))
        if self.cfg.quality_window_enabled:
            den = self.seconds[i].clamp_min(1e-6)
            result.update(gait_mean_speed_ground_top=(self.speed_sum[i] / den).tolist(),
                          speed_good_fraction_ground_top=(self.speed_good_seconds[i] / den).tolist(),
                          gait_fraction_includes_speed=False, mixed_gait_is_promotion_gate=False)
        return result
