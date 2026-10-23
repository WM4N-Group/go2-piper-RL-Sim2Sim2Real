"""导航到Push的物理准备：校准原静站姿态，承重移脚，再确认实际站姿。

校准在独立数据中运行原Push启动，不修改任务世界。真实机器人始终由电机驱动。
"""
from dataclasses import asdict, dataclass, replace
import importlib
import numpy as np


@dataclass(frozen=True)
class EntryConfig:
    # 平地入口仅需小幅移脚；五次轨迹两端速度、加速度均为零。
    swing_seconds: float = .30
    lift_height: float = .012
    landing_depth: float = .006
    align_seconds: float = .25
    shift_seconds: float = .10
    load_seconds: float = .08
    capture_margin: float = .015
    planning_margin: float = .04
    foot_error: float = .015
    tilt: float = .035
    stable_seconds: float = .4
    timeout: float = 45.


def reference_stance(runtime):
    """只取独立Push承重后的几何参考，不把校准状态写回真实机器人。"""
    with runtime.push.active():
        module = importlib.import_module('play')
        sim = runtime.push['bridge'].PushBridge(seed=3701,delay_ms=20)
        startup = module.settle(sim)
    if not startup['stable']:
        raise RuntimeError('push_reference_calibration_not_stable')
    feet = [sim.model.body(f'{leg}_foot').id for leg in ('FR','FL','RR','RL')]
    rotation = sim.data.xmat[sim.base_id].reshape(3,3)
    root = sim.data.qpos[:3]
    return dict(height=float(root[2]),
        feet_local=((sim.data.xpos[feet]-root)@rotation),
        com_local=rotation.T@(sim.data.subtree_com[sim.base_id]-root),
        joints=sim.data.qpos[sim.qids].copy())


class PushEntry:
    def __init__(self,runtime,previous):
        self.r,self.previous=runtime,previous
        p=runtime.sim
        before=np.r_[p.data.qpos,p.data.qvel].copy()
        queue_before=[item.copy() for item in p.queue]
        self.reference=getattr(runtime,'push_reference',None)
        if self.reference is None:
            self.reference=reference_stance(runtime)
        assert np.array_equal(before,np.r_[p.data.qpos,p.data.qvel])
        assert len(queue_before)==len(p.queue) and all(
            np.array_equal(a,b) for a,b in zip(queue_before,p.queue))
        self.config=EntryConfig()
        p.feet_ids=np.array([p.model.body(f'{leg}_foot').id for leg in ('FR','FL','RR','RL')])
        p.soft_limits=p.model.jnt_range[p.jids].copy()
        # 重心转移时不能同时把腿拉回对称站姿，否则静态误差会使卸载脚
        # 一直承重。足端锚点和机身姿态已约束运动，无需额外腿关节姿态任务。
        cfg=replace(runtime.push['finish'].FinishConfig(),stance_posture_weight=0.,
                    position_gain=60.,velocity_gain=16.,foot_gain=600.,foot_damping=32.)
        self.qp=runtime.push['balance'].WholeBodyQP(p,cfg)
        self.anchors=p.data.xpos[p.feet_ids].copy()
        self.base_goal=np.array([-.08,runtime.box_y,self.reference['height']])
        self.foot_goal=self.base_goal+self.reference['feet_local']
        self.nominal_com=self.base_goal+self.reference['com_local']
        self.com_goal=p.data.subtree_com[p.base_id].copy()
        self.started=self.stage_started=float(p.data.time)
        self.stage='align'
        self.done=[]
        self.leg=None
        self.events=[]
        self.stable_age=0.
        self.last_command=previous
        self.ready=False
        self.metrics={}

    def change(self,stage,**values):
        self.stage=stage
        self.stage_started=float(self.r.sim.data.time)
        event=dict(time=self.stage_started,stage=stage,**values)
        self.events.append(event)
        print('Push entry:',event,flush=True)

    def update(self):
        p,cfg=self.r.sim,self.config
        now=float(p.data.time)
        if now-self.started>cfg.timeout:
            raise RuntimeError('push_start_pose_timeout:'+self.stage+':'+str(self.metrics))
        support=p.forces[p.feet_ids,2]>4.
        _,com_jac,*_=self.qp.kinematics()
        com=p.data.subtree_com[p.base_id]
        velocity=com_jac@p.data.qvel
        capture=com[:2]+velocity[:2]/np.sqrt(9.81/max(com[2],.15))
        stop=self.r.climb['stop']
        age=now-self.stage_started
        tilt=self.r.n.state()[3]
        self.metrics=dict(tilt=float(tilt),speed=float(np.linalg.norm(p.data.qvel[:3])),
            foot_error=float(np.max(np.linalg.norm(p.data.xpos[p.feet_ids]-self.foot_goal,axis=1))),
            supported=support.tolist(),base_error=float(np.linalg.norm(p.data.qpos[:3]-self.base_goal)))
        self.metrics.update(com=com.tolist(),com_goal=self.com_goal.tolist(),
            capture=capture.tolist())
        if self.stage=='shift':
            self.metrics['support_margin']=float(-np.max(self.polygon[:,:2]@capture+self.polygon[:,2]))
        if self.stage=='align':
            self.com_goal=self.nominal_com.copy()
            if age>=cfg.align_seconds and support.all() and np.linalg.norm(velocity)<.05 and tilt<.06:
                self.change('select')
        if self.stage=='select':
            remaining=[i for i in range(4) if i not in self.done]
            if not remaining:
                self.com_goal=self.nominal_com.copy()
                self.change('settle')
            else:
                def polygon(i):return stop.support_polygon(np.delete(self.anchors[:,:2],i,axis=0))
                self.leg=max(remaining,key=lambda i:-np.max(polygon(i)[:,:2]@capture+polygon(i)[:,2]))
                self.polygon=polygon(self.leg)
                self.com_goal=self.nominal_com.copy()
                self.com_goal[:2]=stop.nearest_inside(self.polygon,self.nominal_com[:2],margin=cfg.planning_margin)
                self.change('shift',leg=self.leg)
        elif self.stage=='shift':
            others=np.delete(support,self.leg)
            if (age>cfg.shift_seconds and others.all() and np.linalg.norm(velocity[:2])<.04
                    and stop.polygon_contains(self.polygon,capture,cfg.capture_margin)):
                self.swing_start=p.data.xpos[p.feet_ids[self.leg]].copy()
                self.change('swing',leg=self.leg)
        elif self.stage=='swing':
            actual=p.data.xpos[p.feet_ids[self.leg]]
            if (age>=cfg.swing_seconds and support[self.leg]
                    and np.linalg.norm(actual[:2]-self.foot_goal[self.leg,:2])<cfg.foot_error):
                self.anchors[self.leg]=actual
                self.done.append(self.leg)
                self.change('load',leg=self.leg)
            elif age>cfg.swing_seconds+1.2:
                raise RuntimeError('push_entry_foot_not_landed:'+str(self.leg))
        elif self.stage=='load' and age>cfg.load_seconds and support.all():
            self.change('select')
        elif self.stage=='settle':
            good=(support.all() and self.metrics['foot_error']<cfg.foot_error and tilt<cfg.tilt
                  and self.metrics['base_error']<.025 and self.metrics['speed']<.035
                  and np.linalg.norm(p.data.qvel[3:6])<.12
                  and np.max(abs(p.data.qpos[p.qids[12:]]))<.08)
            self.stable_age=self.stable_age+.02 if good else 0.
            if self.stable_age>=cfg.stable_seconds:
                self.ready=True
                self.change('ready')

    def command(self):
        r,p,cfg=self.r,self.r.sim,self.config
        pm=r.push['model']
        gravity=p.data.qfrc_bias[p.dids[12:]]
        arm=r.Command(pm.REFERENCE.copy(),np.zeros(18),pm.KP.copy(),pm.KD.copy(),np.r_[np.zeros(12),gravity])
        anchors=self.anchors.copy()
        velocities,accelerations=np.zeros((4,3)),np.zeros((4,3))
        support=np.ones(4,dtype=bool)
        if self.stage=='swing':
            i=self.leg
            age=p.data.time-self.stage_started
            duration=cfg.swing_seconds
            u=np.clip(age/duration,0.,1.)
            w=u**3*(10.-15.*u+6.*u*u)
            dw=30*u*u*(1-u)**2/duration
            ddw=60*u*(1-u)*(1-2*u)/duration**2
            delta=self.foot_goal[i]-self.swing_start
            # 目标略低于承重脚中心，使接触在轨迹末段自然建立。
            # 这只是电机控制参考；实际足端仍由接触物理决定，不会穿地重置。
            delta[2]-=cfg.landing_depth
            anchors[i]=self.swing_start+w*delta
            velocities[i]=dw*delta
            accelerations[i]=ddw*delta
            anchors[i,2]+=cfg.lift_height*64*u**3*(1-u)**3
            velocities[i,2]+=cfg.lift_height*64*(3*u*u-12*u**3+15*u**4-6*u**5)/duration
            accelerations[i,2]+=cfg.lift_height*64*(6*u-36*u*u+60*u**3-30*u**4)/duration**2
            if age>duration:
                anchors[i,2]-=min(.025,(age-duration)*.03)
                velocities[i,2]=-.03
            support[i]=False
        torque,*_=self.qp.solve(support,anchors,velocities,accelerations,
            self.com_goal,0.,self.reference['joints'][:12],arm)
        arm.position[:12]=p.data.qpos[p.qids[:12]]
        arm.kp[:12]=5.
        arm.kd[:12]=1.
        arm.feedforward[:12]=torque+p.data.qvel[p.dids[:12]]
        from runtime import blend_command
        self.last_command=blend_command(r.Command,self.previous,arm,(p.data.time-self.started)/.3)
        return self.last_command

    def report(self):
        return dict(configuration=asdict(self.config),stage=self.stage,ready=self.ready,metrics=self.metrics,events=self.events,
            expected_base=self.base_goal.tolist(),expected_feet=self.foot_goal.tolist())
