"""可对照的执行器配置；不修改质量、惯量、几何、关节范围或电机限位。

isaac：保留原 go2_push 执行器参数。
skills：借鉴 MujocoSkills/configs/runtime.yaml 与机器人XML的PD和被动阻力。
最低速度和末端目标属于导航任务，放在 navigate.py；不在这里混入。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlProfile:
    kp: tuple
    kd: tuple
    passive_damping: tuple
    frictionloss: float
    default_delay_ms: int | None
    startup_pd_seconds: float = 0.
    policy_warmup_seconds: float = 0.
    observation_limit: float | None = None
    action_limit: float | None = None
    wbc_velocity_limits: tuple = (.5,.4,.8)
    command_slew: bool = True
    safe_ee_pose: tuple = (.5,0.,.4,1.,0.,0.,0.)
    navigation_decimation: int = 20


PROFILES = {
    'isaac': ControlProfile(
        kp=(30.,)*12+(50.,50.,80.,30.,30.,20.),
        kd=(.6,)*12+(3.,2.,3.,3.,2.5,1.),
        passive_damping=(0.,)*18,
        frictionloss=.01,
        default_delay_ms=None),
    'skills': ControlProfile(
        kp=(30.,)*12+(40.,40.,40.,20.,20.,20.),
        kd=(.8,)*12+(1.,)*6,
        passive_damping=(.1,)*12+(1.,)*6,
        frictionloss=.2,
        default_delay_ms=20,  # Simulation assumption, not a hardware measurement.
        startup_pd_seconds=3.,
        policy_warmup_seconds=.24,
        observation_limit=100.,
        action_limit=20.,
        wbc_velocity_limits=(1.,1.,.9),
        command_slew=False,
        safe_ee_pose=(.4,0.,.4,1.,0.,0.,0.),
        navigation_decimation=4),
}


def get_profile(name):
    if name not in PROFILES:
        raise ValueError(f'Unknown control profile {name!r}; choose {tuple(PROFILES)}')
    return PROFILES[name]
