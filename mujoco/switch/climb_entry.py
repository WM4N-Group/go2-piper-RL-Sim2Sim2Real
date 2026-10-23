"""近距离Push→Climb入口：四脚原地承重、机身调平并抬高、确认停稳。

不后退、不手工把前脚放上箱子、不修改Actor。所有姿态变化通过现有全身QP
和同一延迟电机队列完成；仍须通过原碰撞/力矩保护。
"""
from dataclasses import asdict, dataclass, replace
import numpy as np
from runtime import blend_command


@dataclass(frozen=True)
class ClimbEntryConfig:
    base_height: float = .32
    height_tolerance: float = .012
    linear_speed: float = .03
    angular_speed: float = .12
    tilt: float = .03
    stable_seconds: float = .3
    blend_seconds: float = .3
    timeout: float = 6.
    # 保留原策略启动参数；更短斜坡的对照均未通过，不作为默认方案。
    policy_ramp_seconds: float = .8
    policy_speed: float = .4


class ClimbEntry:
    def __init__(self, runtime, item):
        self.r=runtime
        self.config=ClimbEntryConfig()
        self.previous=runtime.last
        self.started=float(runtime.sim.data.time)
        p=runtime.sim
        if hasattr(runtime,'staircase'):
            geometry=runtime.staircase.climb_geometry(p,item['surface'])
            self.surface_height=geometry['base_height']
            self.front=geometry['front']
        else:
            self.surface_height=0.
            self.front=runtime.cfg['box_front']
        self.goal=p.data.qpos[:2].copy()
        self.initial_base=p.data.qpos[:3].copy()
        self.base_goal=self.config.base_height+self.surface_height
        self.com_goal=p.data.subtree_com[p.base_id].copy()
        self.com_goal[2]+=self.base_goal-p.data.qpos[2]
        p.feet_ids=np.array([p.model.body(f'{leg}_foot').id for leg in ('FR','FL','RR','RL')])
        p.soft_limits=p.model.jnt_range[p.jids].copy()
        self.anchors=p.data.xpos[p.feet_ids].copy()
        self.posture=p.data.qpos[p.qids[:12]].copy()
        cfg=replace(runtime.push['finish'].FinishConfig(),stance_posture_weight=0.)
        self.qp=runtime.push['balance'].WholeBodyQP(p,cfg)
        self.ready=False
        self.finished=None
        self.stable_age=0.
        self.metrics={}

    def update(self):
        r,cfg,p=self.r,self.config,self.r.sim
        if p.data.time-self.started>cfg.timeout:
            raise RuntimeError('near_climb_entry_timeout:'+str(self.metrics))
        self.metrics=dict(base_height_m=float(p.data.qpos[2]),
            initial_gap_m=float(self.front-self.initial_base[0]),
            gap_m=float(self.front-p.data.qpos[0]),
            xy_drift_m=float(np.linalg.norm(p.data.qpos[:2]-self.goal)),
            tilt_rad=float(r.n.state()[3]),speed_m_s=float(np.linalg.norm(p.data.qvel[:3])),
            angular_speed_rad_s=float(np.linalg.norm(p.data.qvel[3:6])),
            supported=(p.forces[p.feet_ids,2]>4.).tolist(),
            arm_error_rad=float(np.max(abs(p.data.qpos[p.qids[12:]]))))
        good=(abs(self.metrics['base_height_m']-self.base_goal)<cfg.height_tolerance and
              self.metrics['tilt_rad']<cfg.tilt and self.metrics['speed_m_s']<cfg.linear_speed and
              self.metrics['angular_speed_rad_s']<cfg.angular_speed and
              all(self.metrics['supported']) and self.metrics['arm_error_rad']<.08)
        self.stable_age=self.stable_age+.02 if good else 0.
        self.ready=self.stable_age>=cfg.stable_seconds
        if self.ready and self.finished is None:
            self.finished=float(p.data.time)

    def command(self):
        r,p=self.r,self.r.sim
        pm=r.push['model']
        gravity=p.data.qfrc_bias[p.dids[12:]]
        command=r.Command(pm.REFERENCE.copy(),np.zeros(18),pm.KP.copy(),pm.KD.copy(),
                          np.r_[np.zeros(12),gravity])
        torque,*_=self.qp.solve(np.ones(4,dtype=bool),self.anchors,
            np.zeros((4,3)),np.zeros((4,3)),self.com_goal,0.,self.posture,command)
        command.position[:12]=p.data.qpos[p.qids[:12]]
        command.kp[:12]=5.
        command.kd[:12]=1.
        command.feedforward[:12]=torque+p.data.qvel[p.dids[:12]]
        return blend_command(r.Command,self.previous,command,
            (p.data.time-self.started)/self.config.blend_seconds)

    def report(self):
        return dict(mode='near_in_place',configuration=asdict(self.config),goal=self.goal.tolist(),
            surface_height=self.surface_height,ready=self.ready,metrics=self.metrics,
            seconds=(self.finished if self.finished is not None else float(self.r.sim.data.time))-self.started)
