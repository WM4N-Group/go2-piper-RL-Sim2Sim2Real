"""登台后制动：接触观察 → 接管 → 全身力矩QP → 必要补步 → 持续站立。

只依赖当前机器人状态和已知台面；不修改Actor、仿真位姿或物理参数。
参考结构：Unitree unitree_guide BalanceCtrl / MIT Cheetah BalanceStand。
所有可调数值集中在 StopConfig，运行状态由 StopController 独立持有。
"""
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Optional

import mujoco
import numpy as np
import osqp
from scipy import sparse
from scipy.spatial import ConvexHull

from bridge import EFFORT, SPEED, MotorCommand


@dataclass(frozen=True)
class StopConfig:
    """SI单位；这些是仿真控制参数，不是实机认证参数。"""

    edge_margin: float = .06
    clearance_tolerance: float = .015
    contact_on: float = 8.
    contact_off: float = 4.
    contact_confirm: float = .005
    takeover_contacts: int = 4
    takeover_tilt: float = .20
    blend_seconds: float = .10
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
    step_distance: float = .15
    step_height: float = .04
    step_seconds: float = .25
    stance_delay: float = .5
    # FL / FR / RL / RR：Nav零速实测的左右对称近似，单位rad。
    stance_joints: tuple = (.23,.91,-1.86, -.23,.91,-1.86,
                           -.09,.96,-1.63, .09,.96,-1.63)
    stance_seconds: float = 2.
    stance_posture_weight: float = .3
    stable_seconds: float = 1.
    verify_seconds: float = 3.
    stop_deadline: float = 5.
    linear_speed: float = .05
    angular_speed: float = .15
    foot_speed: float = .03
    stable_tilt: float = .10
    arm_error: float = .08


def now_stance_ready(controller):
    cfg = controller.config
    return controller.sim.data.time-controller.handoff_time >= cfg.stance_delay+cfg.stance_seconds


def support_polygon(points):
    """返回凸包的半空间 A*x+b<=0；退化支撑返回None。"""
    points = np.unique(np.asarray(points), axis=0)
    if len(points) < 3:
        return None
    if np.linalg.matrix_rank(points-points[0], tol=1e-5) < 2:
        return None
    return ConvexHull(points).equations


def polygon_contains(polygon, point, margin=0.):
    return polygon is not None and bool(np.all(polygon[:, :2]@point+polygon[:, 2] <= -margin))


def nearest_inside(polygon, point, margin=.015):
    """逐半空间投影，避免引入第二个优化器。"""
    result = np.array(point, dtype=float).copy()
    if polygon is None:
        return result
    for _ in range(20):
        for row in polygon:
            violation = row[:2]@result+row[2]+margin
            if violation > 0:
                result -= violation*row[:2]/(row[:2]@row[:2])
    return result


class WholeBodyQP:
    """36变量：24维广义加速度 + 4脚×3维地面对机器人作用力。

    M*qdd+b = S*tau+J.T*f。浮动基座动力学必须满足；腿力矩由此恢复，
    臂力矩沿用已有PD。接触加速度是高权重任务，摩擦/力矩是硬约束。
    """

    def __init__(self, sim, config):
        self.sim, self.config = sim, config
        self.nv = sim.model.nv
        self.n = self.nv+12
        self.kinematic_data = mujoco.MjData(sim.model)
        self.solver = None
        self.previous_force = np.zeros(12)
        self.last_solution = None
        self.failure_seconds = 0.
        self.last_contacts = None
        self.solve_seconds = []
        self.maximum_residual = 0.

    def kinematics(self):
        """当前雅可比、速度及Jdot*v；差分只发生在独立数据副本。"""
        sim, model, data = self.sim, self.sim.model, self.sim.data
        feet_jac = np.zeros((4, 3, self.nv))
        for i, body in enumerate(sim.feet_ids):
            mujoco.mj_jacBody(model, data, feet_jac[i], None, int(body))
        com_jac = np.zeros((3, self.nv))
        mujoco.mj_jacSubtreeCom(model, data, com_jac, sim.base_id)
        rotation_jac = np.zeros((3, self.nv))
        mujoco.mj_jacBody(model, data, None, rotation_jac, sim.base_id)
        future = self.kinematic_data
        future.qpos[:] = data.qpos
        future.qvel[:] = data.qvel
        epsilon = 1e-5
        mujoco.mj_integratePos(model, future.qpos, data.qvel, epsilon)
        mujoco.mj_fwdPosition(model, future)
        next_feet = np.zeros_like(feet_jac)
        for i, body in enumerate(sim.feet_ids):
            mujoco.mj_jacBody(model, future, next_feet[i], None, int(body))
        next_com = np.zeros_like(com_jac)
        mujoco.mj_jacSubtreeCom(model, future, next_com, sim.base_id)
        feet_bias = ((next_feet-feet_jac)/epsilon)@data.qvel
        com_bias = ((next_com-com_jac)/epsilon)@data.qvel
        return feet_jac, com_jac, rotation_jac, feet_bias, com_bias

    def solve(self, contacts, anchors, foot_velocity, foot_acceleration,
              com_goal, yaw_goal, posture, arm_command):
        sim, cfg, data = self.sim, self.config, self.sim.data
        began = perf_counter()
        feet_jac, com_jac, rot_jac, feet_bias, com_bias = self.kinematics()
        feet_velocity = feet_jac@data.qvel
        com = data.subtree_com[sim.base_id].copy()
        com_velocity = com_jac@data.qvel
        mass_matrix = np.zeros((self.nv, self.nv))
        mujoco.mj_fullM(sim.model, mass_matrix, data.qM)
        bias = data.qfrc_bias-data.qfrc_passive
        # 每行映射QP变量到关节所需总力矩。
        dynamics = np.c_[mass_matrix, -feet_jac.reshape(12, self.nv).T]
        hessian = np.eye(self.n)*1e-5
        gradient = np.zeros(self.n)

        def task(matrix, desired, weight):
            nonlocal hessian, gradient
            hessian += weight*(matrix.T@matrix)
            gradient -= weight*(matrix.T@desired)

        desired_com = cfg.position_gain*(com_goal-com)-cfg.velocity_gain*com_velocity
        desired_com[2] = cfg.height_gain*(com_goal[2]-com[2])-cfg.height_damping*com_velocity[2]
        desired_com = np.clip(desired_com, -cfg.max_acceleration, cfg.max_acceleration)
        task(np.c_[com_jac, np.zeros((3, 12))], desired_com-com_bias, 10.)
        rotation = data.xmat[sim.base_id].reshape(3, 3)
        c, s = np.cos(yaw_goal), np.sin(yaw_goal)
        desired_rotation = np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])
        error = .5*sum((np.cross(rotation[:, i], desired_rotation[:, i]) for i in range(3)), np.zeros(3))
        angular_acc = cfg.attitude_gain*error-cfg.attitude_damping*(rot_jac@data.qvel)
        task(np.c_[rot_jac, np.zeros((3, 12))], np.clip(angular_acc, -15., 15.), 5.)
        actual_feet = data.xpos[sim.feet_ids]
        for i in range(4):
            acceleration = (foot_acceleration[i]+cfg.foot_gain*(anchors[i]-actual_feet[i])
                            + cfg.foot_damping*(foot_velocity[i]-feet_velocity[i]))
            task(np.c_[feet_jac[i], np.zeros((3, 12))], acceleration-feet_bias[i],
                 40. if contacts[i] else 15.)
        posture_task = np.zeros((12, self.n))
        posture_task[np.arange(12), sim.dids[:12]] = 1.
        posture_acc = 15.*(posture-data.qpos[sim.qids[:12]])-3.*data.qvel[sim.dids[:12]]
        task(posture_task, posture_acc, cfg.stance_posture_weight)
        # 超速/逼近角度边界时给予恢复任务；不篡改实际状态。
        q, qd = data.qpos[sim.qids[:12]], data.qvel[sim.dids[:12]]
        horizon = .08
        predicted = q+horizon*qd
        clipped = np.clip(predicted, *sim.soft_limits[:12].T)
        recovery = 2*(clipped-predicted)/horizon**2
        speed_excess = qd-np.clip(qd, -SPEED[:12], SPEED[:12])
        affected = (abs(clipped-predicted)>1e-6) | (abs(speed_excess)>1e-6)
        if affected.any():
            task(posture_task[affected], recovery[affected]-speed_excess[affected]/horizon, .2)
        force_task = np.c_[np.zeros((12, self.nv)), np.eye(12)]
        task(force_task, self.previous_force, .0002)
        task(force_task, np.zeros(12), .00001)

        matrices, lower, upper = [], [], []

        def constraint(matrix, lo, hi):
            matrices.append(matrix)
            lower.extend(np.broadcast_to(lo, matrix.shape[0]))
            upper.extend(np.broadcast_to(hi, matrix.shape[0]))

        base_dofs = np.arange(6)
        constraint(dynamics[base_dofs], -bias[base_dofs], -bias[base_dofs])
        arm_tau = (arm_command.kp[12:]*(arm_command.position[12:]-data.qpos[sim.qids[12:]])
                   + arm_command.kd[12:]*(arm_command.velocity[12:]-data.qvel[sim.dids[12:]])
                   + arm_command.feedforward[12:])
        arm_tau = np.clip(arm_tau, -EFFORT[12:], EFFORT[12:])
        constraint(dynamics[sim.dids[12:]], arm_tau-bias[sim.dids[12:]], arm_tau-bias[sim.dids[12:]])
        torque_limit = cfg.torque_fraction*EFFORT[:12]
        constraint(dynamics[sim.dids[:12]], -torque_limit-bias[sim.dids[:12]],
                   torque_limit-bias[sim.dids[:12]])
        for i in range(4):
            offset = self.nv+3*i
            selector = np.zeros((3, self.n))
            selector[:, offset:offset+3] = np.eye(3)
            if contacts[i]:
                constraint(selector[2:3], 0., 2.5*sim.model.body_mass.sum()*9.81)
            else:
                constraint(selector, 0., 0.)
            for axis in (0, 1):
                for sign in (-1., 1.):
                    row = sign*selector[axis]-cfg.planning_friction*selector[2]
                    constraint(row[None], -np.inf, 0.)
        matrix = np.vstack(matrices)
        # 保留固定稀疏结构，后续只更新数值，避免每5ms重建求解器。
        if self.solver is None:
            p = sparse.csc_matrix(np.triu(np.ones_like(hessian)))
            a = sparse.csc_matrix(np.ones_like(matrix))
            p.data[:] = np.concatenate([hessian[:i+1, i] for i in range(self.n)])
            a.data[:] = matrix.ravel(order='F')
            self.solver = osqp.OSQP()
            self.solver.setup(P=p, q=gradient, A=a, l=np.array(lower), u=np.array(upper),
                              verbose=False, eps_abs=1e-4, eps_rel=1e-4, max_iter=1500,
                              polishing=False)
            self.constraint_rows = matrix.shape[0]
        else:
            # 未接触脚多两行约束；重建只发生在接触模式变化时。
            if matrix.shape[0] != self.constraint_rows:
                self.solver = None
                return self.solve(contacts, anchors, foot_velocity, foot_acceleration,
                                  com_goal, yaw_goal, posture, arm_command)
            self.solver.update(Px=np.concatenate([hessian[:i+1, i] for i in range(self.n)]),
                               q=gradient, Ax=matrix.ravel(order='F'), l=np.array(lower), u=np.array(upper))
        result = self.solver.solve(raise_error=False)
        elapsed = perf_counter()-began
        self.solve_seconds.append(elapsed)
        valid = result.info.status_val in (1, 2) and result.x is not None and np.isfinite(result.x).all()
        if valid:
            tau = dynamics[sim.dids[:12]]@result.x+bias[sim.dids[:12]]
            valid = bool(np.all(abs(tau) <= torque_limit+.03))
        if not valid:
            unchanged = self.last_contacts is not None and np.array_equal(contacts, self.last_contacts)
            self.failure_seconds += sim.cfg['physics_dt']
            if unchanged and self.last_solution is not None and self.failure_seconds <= .01+1e-9:
                return self.last_solution.copy(), feet_velocity, com, com_velocity
            raise RuntimeError('stop_qp_failed:'+result.info.status)
        self.maximum_residual = max(self.maximum_residual, float(result.info.prim_res))
        self.failure_seconds = 0.
        self.last_contacts = contacts.copy()
        self.previous_force = result.x[self.nv:].copy()
        self.last_solution = tau.copy()
        return tau, feet_velocity, com, com_velocity


class StopController:
    """单向状态：climb → brake → hold → success；任何阶段可failed。"""

    def __init__(self, sim, config=None):
        self.sim, self.config = sim, config or StopConfig()
        self.qp = WholeBodyQP(sim, self.config)
        self.phase = 'climb'
        self.failure = ''
        self.contacts = np.zeros(4, dtype=bool)
        self.contact_age = np.zeros(4)
        self.first_clear_time: Optional[float] = None
        self.handoff_time: Optional[float] = None
        self.stable_start: Optional[float] = None
        self.stop_time: Optional[float] = None
        self.verify_start: Optional[float] = None
        self.anchors = None
        self.com_goal = None
        self.posture = None
        self.entry_command = None
        self.yaw_goal = 0.
        self.extra_steps = 0
        self.swing = None
        self.handoff_position = None
        self.last_position = None
        self.distance = self.maximum_forward = 0.
        self.candidate_distance = self.candidate_forward = 0.
        self.stopped_distance = self.stopped_forward = None
        self.events = []
        self.post_peak_speed = np.zeros(18)
        self.post_peak_torque = np.zeros(18)
        self.post_saturation = np.zeros(18, dtype=int)
        self.post_angle_violation = np.zeros(18)

    @property
    def active(self):
        return self.handoff_time is not None

    def on_platform(self, feet):
        cfg, margin = self.sim.cfg, self.config.edge_margin
        return ((feet[:, 0]>=cfg['box_front']+margin)
                & (feet[:, 0]<=cfg['box_front']+cfg['box_length']-margin)
                & (abs(feet[:, 1])<=cfg['box_width']/2-margin))

    def observe(self):
        """只在每个物理步读取一次，用真实步长累计接触确认时间。"""
        sim, cfg = self.sim, self.config
        feet = sim.data.xpos[sim.feet_ids]
        inside = self.on_platform(feet)
        surface = abs(feet[:, 2]-sim.height-sim.cfg['foot_radius']) <= sim.cfg['foot_height_tolerance']
        threshold = np.where(self.contacts, cfg.contact_off, cfg.contact_on)
        detected = inside & surface & (sim.forces[sim.feet_ids, 2]>=threshold)
        self.contact_age = np.where(detected, self.contact_age+sim.cfg['physics_dt'], 0.)
        self.contacts = detected
        clear = bool(np.all(inside & (feet[:, 2]-sim.cfg['foot_radius'] >= sim.height-cfg.clearance_tolerance)))
        if clear and self.first_clear_time is None:
            self.first_clear_time = float(sim.data.time)
        return clear, self.contacts & (self.contact_age>=cfg.contact_confirm-1e-9)

    def try_handoff(self, clear, confirmed):
        sim, cfg = self.sim, self.config
        if not clear or confirmed.sum()<cfg.takeover_contacts or sim.state()[3]>=cfg.takeover_tilt:
            return
        # 预测停止点位于四脚将形成的支撑区域；避免不具备制动空间时硬切。
        feet = sim.data.xpos[sim.feet_ids].copy()
        _, jac, _, _, _ = self.qp.kinematics()
        com = sim.data.subtree_com[sim.base_id].copy()
        velocity = jac@sim.data.qvel
        omega = np.sqrt(9.81/max(com[2]-sim.height, .15))
        capture = com[:2]+velocity[:2]/omega
        polygon = support_polygon(feet[:, :2])
        # 接管瞬间必须能由已确认的支撑脚接住重心，不能把悬空脚当成支撑。
        actual_support = support_polygon(feet[confirmed, :2])
        if not polygon_contains(actual_support, capture, .01):
            return
        self.handoff_time = float(sim.data.time)
        self.handoff_position = sim.data.qpos[:3].copy()
        self.last_position = self.handoff_position.copy()
        self.anchors = feet
        self.anchors[:, 2] = sim.height+sim.cfg['foot_radius']
        self.com_goal = np.r_[nearest_inside(polygon, capture), com[2]]
        self.yaw_goal = sim.state()[2]
        self.posture = sim.data.qpos[sim.qids[:12]].copy()
        self.entry_posture = self.posture.copy()
        self.entry_com_goal = self.com_goal.copy()
        # Nav零速实测的左右对称近似；此处按FL/FR/RL/RR顺序，不能直接复制Nav数组。
        self.stand_posture = np.array(cfg.stance_joints)
        reference = mujoco.MjData(sim.model)
        reference.qpos[:] = sim.data.qpos
        reference.qpos[sim.qids[:12]] = self.stand_posture
        reference.qpos[3:7] = [np.cos(self.yaw_goal/2),0.,0.,np.sin(self.yaw_goal/2)]
        reference.qvel[:] = 0.
        mujoco.mj_forward(sim.model, reference)
        # 四脚不滑移：由期望腿姿的FK估计站立高度和重心，不强制移动支撑脚。
        offset = reference.subtree_com[sim.base_id]-reference.xpos[sim.feet_ids].mean(axis=0)
        self.stand_com_goal = self.anchors.mean(axis=0)+offset
        self.stand_com_goal[:2] = nearest_inside(polygon,self.stand_com_goal[:2])
        self.phase = 'brake'
        self.events.append(dict(time=self.handoff_time, event='handoff', contacts=confirmed.tolist()))
        # 最多一个尚在空中的脚，用连续轨迹完成已有摆动，不算额外补步。
        airborne = np.flatnonzero(~confirmed)
        if len(airborne):
            self.begin_swing(int(airborne[0]), self.anchors[airborne[0]], extra=False)

    def begin_swing(self, leg, destination, extra):
        """五次曲线匹配起点速度，终点零速度/加速度。"""
        sim = self.sim
        duration = self.config.step_seconds if extra else .08
        jac = np.zeros((3, sim.model.nv))
        mujoco.mj_jacBody(sim.model, sim.data, jac, None, int(sim.feet_ids[leg]))
        position = sim.data.xpos[sim.feet_ids[leg]].copy()
        velocity = jac@sim.data.qvel
        coefficients = np.zeros((6, 3))
        coefficients[0], coefficients[1] = position, velocity
        matrix = np.array([[duration**3, duration**4, duration**5],
                           [3*duration**2, 4*duration**3, 5*duration**4],
                           [6*duration, 12*duration**2, 20*duration**3]])
        coefficients[3:] = np.linalg.solve(matrix, np.stack((destination-position-duration*velocity,
                                                            -velocity, np.zeros(3))))
        self.swing = dict(leg=leg, time=float(sim.data.time), coefficients=coefficients,
                          destination=np.array(destination), extra=extra, duration=duration)
        if extra:
            self.extra_steps += 1
            self.events.append(dict(time=float(sim.data.time), event='recovery_step', leg=leg,
                                    destination=np.asarray(destination).tolist()))

    def swing_targets(self):
        desired = self.anchors.copy()
        velocity, acceleration = np.zeros((4, 3)), np.zeros((4, 3))
        # 支撑计划与瞬时测得的接触不同：不能因瞬间卸载就永远撤掉该脚支撑。
        feet = self.sim.data.xpos[self.sim.feet_ids]
        near_surface = abs(feet[:, 2]-self.sim.height-self.sim.cfg['foot_radius']) < .015
        contacts = self.contacts | (near_surface & self.on_platform(feet))
        if self.swing is None:
            return desired, velocity, acceleration, contacts
        swing = self.swing
        duration = swing['duration']
        leg = swing['leg']
        age = float(self.sim.data.time)-swing['time']
        minimum_flight = .6*duration if swing['extra'] else .01
        if age>=duration or (age>=minimum_flight and self.contacts[leg]):
            # 仅在真实触地后锁定落脚点。时间到但尚未触地，继续追踪台面目标，
            # 不能把悬空的实测位置锁成站立锚点。
            if self.contacts[leg]:
                self.anchors[leg] = self.sim.data.xpos[self.sim.feet_ids[leg]]
            else:
                self.anchors[leg] = swing['destination']
            self.swing = None
            return self.anchors.copy(), velocity, acceleration, contacts
        coefficients = swing['coefficients']
        desired[leg] = np.array([age**k for k in range(6)])@coefficients
        velocity[leg] = np.array([0.]+[k*age**(k-1) for k in range(1, 6)])@coefficients
        acceleration[leg] = np.array([0., 0.]+[k*(k-1)*age**(k-2) for k in range(2, 6)])@coefficients
        if swing['extra']:
            # 64*s^3*(1-s)^3在两端位置/速度/加速度均为零。
            s = age/duration
            h = self.config.step_height
            desired[leg, 2] += 64*h*s**3*(1-s)**3
            velocity[leg, 2] += 64*h*(3*s**2-12*s**3+15*s**4-6*s**5)/duration
            acceleration[leg, 2] += 64*h*(6*s-36*s**2+60*s**3-30*s**4)/duration**2
        contacts[leg] = False
        return desired, velocity, acceleration, contacts

    def maybe_recovery_step(self):
        """只有四脚支撑且剩余三脚可支撑时，枚举一次短补步。"""
        if self.swing is not None or self.extra_steps or not self.contacts.all():
            return
        sim, cfg = self.sim, self.config
        _, jac, _, _, _ = self.qp.kinematics()
        com = sim.data.subtree_com[sim.base_id]
        velocity = jac@sim.data.qvel
        capture = com[:2]+velocity[:2]/np.sqrt(9.81/max(com[2]-sim.height, .15))
        feet = sim.data.xpos[sim.feet_ids].copy()
        if polygon_contains(support_polygon(feet[:, :2]), capture, .015):
            return
        candidates = []
        for leg in range(4):
            remaining = np.delete(feet[:, :2], leg, axis=0)
            if not polygon_contains(support_polygon(remaining), com[:2], .005):
                continue
            direction = capture-feet[leg, :2]
            direction /= max(np.linalg.norm(direction), 1e-6)
            for distance in (.05, .10, cfg.step_distance):
                target = feet[leg].copy()
                target[:2] += distance*direction
                target[2] = sim.height+sim.cfg['foot_radius']
                if not self.on_platform(target[None])[0]:
                    continue
                local = sim.state()[0].T@(target-sim.data.qpos[:3])
                if (leg in (0, 2) and local[1]<.03) or (leg in (1, 3) and local[1]>-.03):
                    continue
                # 用模型雅可比检查局部可达性，完整轨迹仍受QP和力矩约束。
                jac_leg = np.zeros((3, sim.model.nv))
                mujoco.mj_jacBody(sim.model, sim.data, jac_leg, None, int(sim.feet_ids[leg]))
                columns = sim.dids[3*leg:3*leg+3]
                offset = np.linalg.lstsq(jac_leg[:, columns], target-feet[leg], rcond=None)[0]
                q = sim.data.qpos[sim.qids[3*leg:3*leg+3]]+offset
                limits = sim.soft_limits[3*leg:3*leg+3]
                if np.any(q<limits[:, 0]) or np.any(q>limits[:, 1]):
                    continue
                proposed = feet[:, :2].copy()
                proposed[leg] = target[:2]
                if polygon_contains(support_polygon(proposed), capture, .015):
                    candidates.append((distance, float(np.linalg.norm(offset)), leg, target))
        if candidates:
            _, _, leg, target = min(candidates, key=lambda item: item[:3])
            self.begin_swing(leg, target, extra=True)
            polygon = support_polygon(np.array([target[:2] if i==leg else feet[i, :2] for i in range(4)]))
            self.com_goal[:2] = nearest_inside(polygon, capture)

    def command(self, policy_command):
        clear, confirmed = self.observe()
        if self.phase=='climb':
            self.try_handoff(clear, confirmed)
        if not self.active or self.failure:
            return policy_command
        if self.entry_command is None:
            self.entry_command = policy_command.position[:12].copy()
        self.maybe_recovery_step()
        if hasattr(self, 'stand_posture'):
            age = max(0.,float(self.sim.data.time)-self.handoff_time-self.config.stance_delay)
            fraction = np.clip(age/self.config.stance_seconds,0.,1.)
            blend = fraction*fraction*(3-2*fraction)
            self.posture = (1-blend)*self.entry_posture+blend*self.stand_posture
            self.com_goal = (1-blend)*self.entry_com_goal+blend*self.stand_com_goal
        anchors, velocity, acceleration, contacts = self.swing_targets()
        try:
            torque, _, _, _ = self.qp.solve(contacts, anchors, velocity, acceleration,
                                           self.com_goal, self.yaw_goal, self.posture, policy_command)
        except RuntimeError as error:
            self.failure = str(error)
            self.phase = 'failed'
            return policy_command
        age = float(self.sim.data.time)-self.handoff_time
        fraction = np.clip(age/self.config.blend_seconds, 0., 1.)
        blend = fraction*fraction*(3-2*fraction)
        command = MotorCommand(*(array.copy() for array in (
            policy_command.position, policy_command.velocity, policy_command.kp,
            policy_command.kd, policy_command.feedforward)))
        # 小增益本地反馈抑制命令延迟造成的高频误差；前馈扣除当前反馈贡献，
        # 当前状态下总力矩仍等于QP结果，不再重复叠加一套完整PD。
        q = self.sim.data.qpos[self.sim.qids[:12]]
        qd = self.sim.data.qvel[self.sim.dids[:12]]
        command.position[:12] = q
        command.kp[:12] = (1-blend)*policy_command.kp[:12]+blend*self.config.motor_kp
        command.kd[:12] = (1-blend)*policy_command.kd[:12]+blend*self.config.motor_kd
        old_position_torque = (1-blend)*policy_command.kp[:12]*(self.entry_command-q)
        command.feedforward[:12] = (old_position_torque
                                    + blend*(torque+self.config.motor_kd*qd))
        return command

    def after_step(self):
        """物理推进后评估；成功前始终继续动力学，不冻结画面冒充站稳。"""
        if not self.active or self.failure:
            return
        sim, cfg, data = self.sim, self.config, self.sim.data
        position = data.qpos[:3]
        self.distance += float(np.linalg.norm(position[:2]-self.last_position[:2]))
        self.maximum_forward = max(self.maximum_forward, float(position[0]-self.handoff_position[0]))
        self.last_position = position.copy()
        self.post_peak_speed = np.maximum(self.post_peak_speed, abs(data.qvel[sim.dids]))
        self.post_peak_torque = np.maximum(self.post_peak_torque, abs(sim.applied_torque))
        self.post_saturation += abs(sim.raw_torque)>=EFFORT
        q = data.qpos[sim.qids]
        limits = sim.model.jnt_range[sim.jids]
        self.post_angle_violation = np.maximum(self.post_angle_violation,
                                               np.maximum(limits[:, 0]-q, q-limits[:, 1]))
        jac = np.zeros((3, sim.model.nv))
        foot_speed = []
        for body in sim.feet_ids:
            mujoco.mj_jacBody(sim.model, data, jac, None, int(body))
            foot_speed.append(np.linalg.norm((jac@data.qvel)[:2]))
        feet = data.xpos[sim.feet_ids]
        support = (self.on_platform(feet)
                   & (abs(feet[:, 2]-sim.height-sim.cfg['foot_radius'])<=sim.cfg['foot_height_tolerance'])
                   & (sim.forces[sim.feet_ids, 2]>=cfg.contact_off))
        stable = bool(np.linalg.norm(data.qvel[:3])<cfg.linear_speed
                      and np.linalg.norm(data.qvel[3:6])<cfg.angular_speed
                      and sim.state()[3]<cfg.stable_tilt and support.all()
                      and max(foot_speed)<cfg.foot_speed
                      and abs(q[12:]-sim.reference[12:]).max()<cfg.arm_error
                      and self.swing is None
                      and (not hasattr(self, 'stand_posture') or now_stance_ready(self)))
        now = float(data.time)
        if stable:
            if self.stable_start is None:
                self.stable_start = now
                self.candidate_distance = self.distance
                self.candidate_forward = self.maximum_forward
            if now-self.stable_start>=cfg.stable_seconds-1e-8:
                if self.stop_time is None:
                    self.stop_time = self.stable_start
                    self.stopped_distance = self.candidate_distance
                    self.stopped_forward = self.candidate_forward
                    self.verify_start = now
                    self.phase = 'hold'
                    self.events.append(dict(time=now, event='stable_confirmed'))
                if now-self.verify_start>=cfg.verify_seconds-1e-8:
                    self.phase = 'success'
        else:
            self.stable_start = None
            if self.verify_start is not None:
                self.failure, self.phase = 'stop_hold_lost', 'failed'
        deadline = self.handoff_time+cfg.stop_deadline
        if (self.stop_time is None and now>deadline
                and (self.stable_start is None or self.stable_start>deadline) and not self.failure):
            self.failure, self.phase = 'stop_deadline', 'failed'

    def status(self, original_state, original_reason):
        if original_state in ('failed', 'timeout'):
            self.phase, self.failure = 'failed', original_reason
            return original_state, original_reason
        if self.failure:
            return 'failed', self.failure
        if self.phase=='success':
            return 'success', 'ascent_and_stationary_hold'
        return 'running', ''

    def report(self):
        time_from_handoff = None if self.stop_time is None else self.stop_time-self.handoff_time
        solve = np.asarray(self.qp.solve_seconds)
        return dict(phase=self.phase, final_leg_q_rad=self.sim.data.qpos[self.sim.qids[:12]].tolist(),
                    stance_target_rad=getattr(self,'stand_posture',np.array([])).tolist(), configuration=asdict(self.config), first_clear_time=self.first_clear_time,
                    handoff_time=self.handoff_time, stable_start_time=self.stop_time,
                    stop_seconds=time_from_handoff,
                    stop_seconds_from_clear=None if self.stop_time is None else self.stop_time-self.first_clear_time,
                    horizontal_distance_m=self.stopped_distance, maximum_forward_m=self.stopped_forward,
                    total_controlled_distance_m=self.distance, total_maximum_forward_m=self.maximum_forward,
                    extra_steps=self.extra_steps, events=self.events,
                    post_peak_speed_rad_s=self.post_peak_speed.tolist(),
                    post_peak_torque_nm=self.post_peak_torque.tolist(),
                    post_saturation_steps=self.post_saturation.tolist(),
                    post_angle_violation_rad=self.post_angle_violation.tolist(),
                    qp_solve_p95_ms=None if not len(solve) else float(np.percentile(solve, 95)*1000),
                    qp_max_residual=self.qp.maximum_residual, failure=self.failure)
