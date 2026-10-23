"""Climb全身QP的本地副本：相同任务权重、摩擦锥和力矩约束。
仅适配Push包含自由箱子的模型和物理步长；不跨技能导入运行代码。
"""
from time import perf_counter
import mujoco
import numpy as np
import osqp
from scipy import sparse
from model import EFFORT, SPEED, PHYSICS_DT

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
                constraint(selector[2:3], 0., 2.5*sim.model.body_subtreemass[sim.base_id]*9.81)
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
            self.failure_seconds += PHYSICS_DT
            if unchanged and self.last_solution is not None and self.failure_seconds <= .01+1e-9:
                return self.last_solution.copy(), feet_velocity, com, com_velocity
            raise RuntimeError('stop_qp_failed:'+result.info.status)
        self.maximum_residual = max(self.maximum_residual, float(result.info.prim_res))
        self.failure_seconds = 0.
        self.last_contacts = contacts.copy()
        self.previous_force = result.x[self.nv:].copy()
        self.last_solution = tau.copy()
        return tau, feet_velocity, com, com_velocity

