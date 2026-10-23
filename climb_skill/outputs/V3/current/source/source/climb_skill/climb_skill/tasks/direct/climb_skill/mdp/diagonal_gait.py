"""Soft, terrain-dependent diagonal walking; no commanded phase or foot-switch gate.

Order is FL, FR, RL, RR. Sensor timers restart at real contact transitions, so
diagonal synchrony plus bounded stance/swing durations favor alternating pairs.
There is no positive standing/stepping reward, nor a minimum-speed escape gate.
"""
import torch
from .flat_walking import flat_walking_mask, walking_quality_curriculum
from .geometry import box_scan


def diagonal_walking_mask(pos, feet, heights, ever_top_support, cfg):
    if cfg.walking_refinement_enabled:
        from .walking_refinement import settled_flat_mask, early_gait_gain
        return settled_flat_mask(pos, feet, heights, ever_top_support, cfg) * early_gait_gain(heights, cfg)
    mask = flat_walking_mask(pos, feet, heights, cfg)
    root_on_top = box_scan(pos[:, None, :2], heights, cfg).squeeze(-1) > 0.
    # A projected footprint on top does not mean the rear legs have landed.
    # 地面可直接学走；箱顶必须本回合四脚都曾真实承重，避免把前腿跃上阶段当普通箱顶步行。
    landed = ~root_on_top | ever_top_support.all(-1)
    return walking_quality_curriculum(mask * landed, heights, cfg)


def diagonal_gait_costs(mask, air_time, contact_time, cfg):
    """All outputs bounded [0,1]; brief transfers and three/four-foot stance are free.

    Timers are in seconds from Isaac's physics-rate contact sensor. Ignoring the
    first transfer_seconds of swing avoids penalizing a diagonal toe-off delay
    or a single brief contact loss. This is a soft learning objective only.
    """
    grace = cfg.diagonal_transfer_seconds
    # 读ContactSensor的连续无接触时间；60ms内的短暂离地不算成熟摆动，不直接取四足支撑总数。
    swing = air_time > grace
    # Penalize front-front AND rear-rear swing, including four-foot flight.
    # FL/FR同空或RL/RR同空均罚，四脚同时腾空也罚；对角两腿腾空不触发此项。
    paired = ((swing[:, 0] & swing[:, 1]) | (swing[:, 2] & swing[:, 3])).float()
    if cfg.walking_refinement_enabled:
        # 同步宽容仍60ms；成对腾空从15ms起计，之后30ms内连续升到1。
        # 取max而不是相加，保持上限1，避免前后同时腾空时成本翻倍。
        pair_air = torch.stack((air_time[:, :2].amin(-1), air_time[:, 2:].amin(-1)), -1)
        paired = ((pair_air - cfg.walking_pair_grace_seconds)
                  / cfg.walking_pair_ramp_seconds).clamp(0., 1.).amax(-1)
    # A diagonal mate may lag by grace; penalize only a sustained mismatch.
    stance_mature = contact_time > grace
    mismatch_a = ((swing[:, 0] & stance_mature[:, 3])
                  | (swing[:, 3] & stance_mature[:, 0]))
    mismatch_b = ((swing[:, 1] & stance_mature[:, 2])
                  | (swing[:, 2] & stance_mature[:, 1]))
    sync = (mismatch_a.float() + mismatch_b.float()) / 2.
    # Without these bounds, holding one diagonal or all feet down is a loophole.
    # No fixed period: any alternating timing inside the broad bounds is allowed.
    # 时间超限只是软罚；没有“满0.5秒自动换腿”的硬控制。微小接触也可能重置计时，仍需录像核验。
    stance = ((contact_time - cfg.diagonal_max_stance_seconds) / .25).clamp(0., 1.)
    air = ((air_time - cfg.diagonal_max_swing_seconds) / .20).clamp(0., 1.)
    duration = torch.maximum(stance, air).square().mean(-1)
    return {"diagonal_pair": mask * paired,
            "diagonal_sync": mask * sync,
            "diagonal_duration": mask * duration}
