"""本地动作节奏；不修改Actor、接触判据或机器人物理参数。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ApproachTiming:
    entry_gain: float = 4.
    # 安全路点之后、箱面就绪之前的关节参考速率；仍乘Actor速度系数。
    alignment_rate_rad_s: float = 1.2
    confirmation_seconds: float = .1
    face_advance_m_s: float = .1
    # 放行时允许小幅关节调整；这不是电机最大转速（仍为3rad/s）。
    alignment_joint_speed_rad_s: float = .30
    leg_release_seconds: float = .7


DEFAULT_APPROACH = ApproachTiming()
ISAAC_APPROACH = ApproachTiming(entry_gain=1.5,alignment_rate_rad_s=.25,
    confirmation_seconds=.1,face_advance_m_s=.1,
    alignment_joint_speed_rad_s=.25,leg_release_seconds=.7)
