"""推箱退出：平衡接管 → 检查逆向收臂路径 → Climb零位站立 → 持续验证。

不改策略，不改物理状态。全部命令通过原延迟电机接口执行。
"""
from dataclasses import asdict,dataclass
import json
import mujoco
import numpy as np

from balance import WholeBodyQP
from model import ROOT,PHYSICS_DT,KP,KD,EFFORT,JOINTS
from motor import MotorCommand


@dataclass(frozen=True)
class FinishConfig:
    # 与Climb StopConfig相同的全身平衡参数。
    planning_friction: float = .40
    torque_fraction: float = .95
    motor_kp: float = 5.
    motor_kd: float = 1.
    velocity_gain: float = 8.
    position_gain: float = 20.
    height_gain: float = 100.
    height_damping: float = 20.
    attitude_gain: float = 100.
    attitude_damping: float = 20.
    foot_gain: float = 250.
    foot_damping: float = 32.
    max_acceleration: float = 3.
    stance_posture_weight: float = .3
    blend_seconds: float = .10
    stance_delay: float = .5
    stance_seconds: float = 2.
    # 按Push的 FR/FL/RR/RL 顺序重排Climb目标，不能原样复制数组。
    stance_joints: tuple = (-.23,.91,-1.86, .23,.91,-1.86,
                           .09,.96,-1.63, -.09,.96,-1.63)
    arm_pose: tuple = (0.,0.,0.,0.,0.,0.)
    arm_speed: float = 2.2
    minimum_segment_seconds: float = .6
    final_segment_seconds: float = 1.5
    arm_tolerance: float = .04
    arm_velocity: float = .12
    surface_clearance: float = .035
    collision_margin: float = .002
    linear_speed: float = .05
    angular_speed: float = .15
    foot_speed: float = .03
    stable_tilt: float = .10
    arm_error: float = .08
    stable_seconds: float = 1.
    verify_seconds: float = 3.
    deadline: float = 25.


class CollisionGuard:
    """独立数据副本检查非相邻碰撞体；包含箱子、地面、腿和臂自身。

    同一焊接体及直接相邻体沿用MuJoCo默认排除。机身额外保留原35mm净空。
    只允许退出最初的手端接触；不允许新路径穿过箱子。
    """
    def __init__(self,sim,config):
        self.sim,self.config = sim,config
        self.data = mujoco.MjData(sim.model)
        model = sim.model
        self.arm = {model.body(f'link{i}').id for i in range(1,7)}|{model.body('end_effector').id}
        self.hand = {model.body('link6').id,model.body('end_effector').id}
        geoms = [i for i in range(model.ngeom) if model.geom_contype[i] or model.geom_conaffinity[i]]
        self.pairs = []
        for index,i in enumerate(geoms):
            for j in geoms[index+1:]:
                a,b = map(int,model.geom_bodyid[[i,j]])
                if a not in self.arm and b not in self.arm:continue
                wa,wb = map(int,model.body_weldid[[a,b]])
                if (wa==wb or model.body_weldid[model.body_parentid[wa]]==wb
                        or model.body_weldid[model.body_parentid[wb]]==wa):continue
                self.pairs.append((i,j,a,b))
        self.minimum = float('inf')
        self.minimum_surface = float('inf')
        self.blocked = 0

    def check(self,q,allow_hand_contact=False,record=False,joint_limits=True):
        sim,model = self.sim,self.sim.model
        limits = model.jnt_range[sim.jids[12:]]
        if joint_limits and (np.any(q<limits[:,0]-.001) or np.any(q>limits[:,1]+.001)):
            return 'arm_joint_limit'
        self.data.qpos[:] = sim.data.qpos
        self.data.qpos[sim.qids[12:]] = q
        mujoco.mj_kinematics(model,self.data)
        minimum,surface,reason = float('inf'),float('inf'),''
        for i,j,a,b in self.pairs:
            distance = float(mujoco.mj_geomDistance(model,self.data,i,j,1.,None))
            hand_box = sim.box_id in (a,b) and (a in self.hand or b in self.hand)
            if hand_box and allow_hand_contact:continue
            minimum = min(minimum,distance)
            if sim.base_id in (a,b):
                surface = min(surface,distance)
                threshold = self.config.surface_clearance
            else:threshold = self.config.collision_margin
            if distance<threshold and not reason:
                reason = f'{model.body(a).name}:{model.body(b).name}:{distance:.5f}m'
        if record:
            self.minimum = min(self.minimum,minimum)
            self.minimum_surface = min(self.minimum_surface,surface)
        return reason

    def segment(self,start,end):
        # 关节插值间隔<=0.02rad；动态时另检查当前到下一参考以及100ms速度外推。
        count = max(2,int(np.ceil(np.max(abs(end-start))/.02))+1)
        for fraction in np.linspace(0.,1.,count):
            reason = self.check(start+fraction*(end-start))
            if reason:return reason
        return ''


class FinishController:
    def __init__(self,sim,config=None):
        self.sim,self.config = sim,config or FinishConfig()
        cfg = self.config
        sim.feet_ids = np.array([sim.model.body(f'{leg}_foot').id for leg in ('FR','FL','RR','RL')])
        sim.soft_limits = sim.robot.data.soft_joint_pos_limits.numpy()[0][
            [sim.robot.joint_names.index(name) for name in JOINTS]]
        self.qp,self.guard = WholeBodyQP(sim,cfg),CollisionGuard(sim,cfg)
        self.started = float(sim.data.time)
        self.phase,self.failure = 'brake',''
        self.events = [dict(time=self.started,event='balance_takeover')]
        self.anchors = sim.data.xpos[sim.feet_ids].copy()
        self.anchors[:,2] = .022
        self.entry_position = sim.targets[:12].copy()
        self.entry_kp,self.entry_kd = KP.copy(),KD.copy()
        self.entry_posture = sim.data.qpos[sim.qids[:12]].copy()
        self.posture = self.entry_posture.copy()
        self.stand_posture = np.array(cfg.stance_joints)
        self.entry_com = sim.data.subtree_com[sim.base_id].copy()
        self.com_goal = self.entry_com.copy()
        rotation = sim.data.xmat[sim.base_id].reshape(3,3)
        self.yaw = float(np.arctan2(rotation[1,0],rotation[0,0]))
        reference = mujoco.MjData(sim.model)
        reference.qpos[:] = sim.data.qpos
        reference.qpos[sim.qids[:12]] = self.stand_posture
        reference.qpos[sim.qids[12:]] = cfg.arm_pose
        reference.qpos[3:7] = [np.cos(self.yaw/2),0.,0.,np.sin(self.yaw/2)]
        mujoco.mj_forward(sim.model,reference)
        offset = reference.subtree_com[sim.base_id]-reference.xpos[sim.feet_ids].mean(axis=0)
        self.stand_com = self.anchors.mean(axis=0)+offset
        self.arm_reference = sim.data.qpos[sim.qids[12:]].copy()
        self.arm_velocity_reference = np.zeros(6)
        self.arm_start = self.arm_reference.copy()
        self.waypoints = list(reversed(json.loads((ROOT/'source/push_skill/runtime/mujoco/deploy/piper_push_safe_approach.json').read_text())['waypoints']))
        self.waypoints.append(list(cfg.arm_pose))
        self.waypoint = 0
        self.segment_start = None
        self.segment_duration = 0.
        self.last_control = -float('inf')
        self.stable_since = self.verify_since = None
        self.stable_time = self.success_time = None
        self.retracted_time = None
        self.max_drift = 0.
        self.initial_base = sim.data.qpos[:3].copy()
        self.peak_speed = np.zeros(18)
        self.peak_torque = np.zeros(18)
        self.saturation = np.zeros(18,dtype=int)
        self.last_metrics = {}

    def fail(self,reason):
        if not self.failure:
            self.failure,self.phase = reason,'failed'
            self.arm_velocity_reference[:] = 0.
            self.events.append(dict(time=float(self.sim.data.time),event='failure',reason=reason))

    def _arm_step(self):
        sim,cfg,now = self.sim,self.config,float(self.sim.data.time)
        actual = sim.data.qpos[sim.qids[12:]]
        if self.phase=='brake':
            if now-self.started<.5:return
            # 先等WBC接住底盘，再开始运动；脚可真实落地，不伪造接触。
            if np.linalg.norm(sim.data.qvel[:3])>.08:return
            start = actual.copy()
            for goal in self.waypoints:
                reason = self.guard.segment(start,np.array(goal))
                if reason:
                    self.fail('retraction_path_blocked:'+reason);return
                start = np.array(goal)
            self.phase = 'retract'
            self.events.append(dict(time=now,event='retraction_path_checked'))
        if self.phase!='retract':return
        goal = np.array(self.waypoints[self.waypoint])
        if self.segment_start is None:
            self.arm_start = self.arm_reference.copy()
            self.segment_start = now
            # 回零位于joint2/3物理边界，最后一段单独留制动时间。
            minimum = cfg.final_segment_seconds if self.waypoint==len(self.waypoints)-1 else cfg.minimum_segment_seconds
            self.segment_duration = max(minimum,1.875*np.max(abs(goal-self.arm_start))/cfg.arm_speed)
        fraction = np.clip((now-self.segment_start)/self.segment_duration,0.,1.)
        blend = fraction**3*(10.-15.*fraction+6.*fraction**2)
        candidate = self.arm_start+blend*(goal-self.arm_start)
        candidate_velocity = (30.*fraction**2*(1.-fraction)**2/self.segment_duration)*(goal-self.arm_start)
        reason = self.guard.segment(actual,candidate)
        if not reason:
            predicted = actual+.10*sim.data.qvel[sim.dids[12:]]
            # 恒速度外推只作碰撞预警；它忽略PD制动，不能当作将实际越限的证据。
            # 真实关节角和整段发送参考始终独立检查关节范围。
            reason = self.guard.check(predicted,joint_limits=False)
        if reason:
            self.guard.blocked += 1
            self.fail('retraction_dynamic_clearance:'+reason);return
        self.arm_reference = candidate
        self.arm_velocity_reference = candidate_velocity
        if (fraction>=1. and np.max(abs(actual-goal))<cfg.arm_tolerance
                and np.max(abs(sim.data.qvel[sim.dids[12:]]))<cfg.arm_velocity):
            self.events.append(dict(time=now,event='arm_waypoint_complete',index=self.waypoint))
            self.waypoint += 1;self.segment_start = None
            if self.waypoint==len(self.waypoints):
                self.phase,self.retracted_time = 'settle',now

    def command(self):
        sim,cfg,data = self.sim,self.config,self.sim.data
        now = float(data.time)
        if now-self.last_control>=.02-1e-9:
            self.last_control = now
            if not self.failure:self._arm_step()
            # 实测净空也检查，不仅检查参考轨迹。
            reason = self.guard.check(data.qpos[sim.qids[12:]],allow_hand_contact=self.phase=='brake',record=True)
            if reason:self.fail('actual_retraction_clearance:'+reason)
            flags = sim.termination()
            failures = [name for name,value in flags.items() if name!='box_settled' and value]
            if failures:self.fail('finish_safety:'+','.join(failures))
            if np.linalg.norm(data.xpos[sim.box_id,:2]-sim.box_push_target[0,:2].numpy())>=.12:
                self.fail('finish_box_left_goal')
        fraction = np.clip((now-self.started-cfg.stance_delay)/cfg.stance_seconds,0.,1.)
        blend = fraction*fraction*(3.-2.*fraction)
        self.posture = (1-blend)*self.entry_posture+blend*self.stand_posture
        self.com_goal = (1-blend)*self.entry_com+blend*self.stand_com
        position = np.r_[self.posture,self.arm_reference]
        gravity = sim.robot.get_gravity_compensation_forces().numpy()[0]
        arm_columns = [sim.robot.joint_names.index(f'joint{i}') for i in range(1,7)]
        feedforward = np.r_[np.zeros(12),gravity[arm_columns]]
        command = MotorCommand(position,np.r_[np.zeros(12),self.arm_velocity_reference],KP.copy(),KD.copy(),feedforward)
        feet_velocity,feet_acceleration = np.zeros((4,3)),np.zeros((4,3))
        try:
            # 四脚落地支撑计划；实测四脚承重仍是成功的必要条件。
            torque,*_ = self.qp.solve(np.ones(4,dtype=bool),self.anchors,feet_velocity,
                feet_acceleration,self.com_goal,self.yaw,self.posture,command)
        except RuntimeError as error:
            self.fail(str(error))
            # 明确失败后仍尝试静态重力/阻尼支撑，不重新启用行走策略。
            command.position[:12] = self.posture
            return command
        takeover = np.clip((now-self.started)/cfg.blend_seconds,0.,1.)
        takeover = takeover*takeover*(3.-2.*takeover)
        q,qd = data.qpos[sim.qids[:12]],data.qvel[sim.dids[:12]]
        command.position[:12] = q
        command.kp[:12] = (1-takeover)*KP[:12]+takeover*cfg.motor_kp
        command.kd[:12] = (1-takeover)*KD[:12]+takeover*cfg.motor_kd
        command.feedforward[:12] = ((1-takeover)*KP[:12]*(self.entry_position-q)
            +takeover*(torque+cfg.motor_kd*qd))
        return command

    def after_step(self):
        sim,cfg,data = self.sim,self.config,self.sim.data
        self.peak_torque = np.maximum(self.peak_torque,abs(sim.torque))
        self.peak_speed = np.maximum(self.peak_speed,abs(data.qvel[sim.dids]))
        self.saturation += abs(sim.raw_torque)>=EFFORT
        self.max_drift = max(self.max_drift,float(np.linalg.norm(data.qpos[:2]-self.initial_base[:2])))
        if self.failure:return
        # 接触力每个物理步检查，初期允许手端脱离原合法接触。
        for contact_index,contact in enumerate(data.contact):
            a,b = map(int,sim.model.geom_bodyid[[contact.geom1,contact.geom2]])
            if a not in self.guard.arm and b not in self.guard.arm:continue
            force = np.zeros(6);mujoco.mj_contactForce(sim.model,data,contact_index,force)
            if np.linalg.norm(force[:3])<=1.:continue
            if (self.phase=='brake' and sim.box_id in (a,b)
                    and (a in self.guard.hand or b in self.guard.hand)):continue
            self.fail('arm_collision:'+sim.model.body(a).name+':'+sim.model.body(b).name)
        if self.failure:return
        linear,angular = np.linalg.norm(data.qvel[:3]),np.linalg.norm(data.qvel[3:6])
        tilt = float(np.arccos(np.clip(data.xmat[sim.base_id].reshape(3,3)[2,2],-1.,1.)))
        foot_speeds = []
        for foot in sim.feet_ids:
            jac = np.zeros((3,sim.model.nv));mujoco.mj_jacBody(sim.model,data,jac,None,int(foot))
            foot_speeds.append(float(np.linalg.norm((jac@data.qvel)[:2])))
        support = sim.forces[sim.feet_ids,2]>4.
        arm_error = float(np.max(abs(data.qpos[sim.qids[12:]]-cfg.arm_pose)))
        self.last_metrics = dict(linear_speed=float(linear),angular_speed=float(angular),
            tilt=tilt,foot_speed=max(foot_speeds),support=support.tolist(),arm_error=arm_error)
        stable = (self.retracted_time is not None and linear<cfg.linear_speed
            and angular<cfg.angular_speed and tilt<cfg.stable_tilt and support.all()
            and max(foot_speeds)<cfg.foot_speed and arm_error<cfg.arm_error)
        now = float(data.time)
        if stable:
            if self.stable_since is None:self.stable_since = now
            if now-self.stable_since>=cfg.stable_seconds-1e-8:
                if self.verify_since is None:
                    self.verify_since = now;self.stable_time = self.stable_since;self.phase = 'hold'
                if now-self.verify_since>=cfg.verify_seconds-1e-8 and self.success_time is None:
                    self.phase,self.success_time = 'success',now
                    self.events.append(dict(time=now,event='retracted_and_stationary'))
        else:
            self.stable_since = None
            if self.verify_since is not None:self.fail('finish_hold_lost')
        if self.success_time is None and now-self.started>cfg.deadline:self.fail('finish_timeout')

    def report(self):
        sim = self.sim
        return dict(phase=self.phase,failure=self.failure,configuration=asdict(self.config),
            events=self.events,started=self.started,retracted_time=self.retracted_time,
            stable_time=self.stable_time,success_time=self.success_time,
            final_leg_q_rad=sim.data.qpos[sim.qids[:12]].tolist(),
            final_arm_q_rad=sim.data.qpos[sim.qids[12:]].tolist(),
            final_metrics=self.last_metrics,max_base_drift_m=self.max_drift,
            minimum_nonadjacent_clearance_m=self.guard.minimum,
            minimum_arm_base_clearance_m=self.guard.minimum_surface,
            collision_blocked_steps=self.guard.blocked,peak_torque_nm=self.peak_torque.tolist(),
            peak_speed_rad_s=self.peak_speed.tolist(),saturation_steps=self.saturation.tolist(),
            qp_max_residual=self.qp.maximum_residual)
