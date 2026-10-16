"""Mass-weighted velocity projection for explicit Sim-to-Sim diagnostics."""

import mujoco
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, lsq_linear, minimize


def contact_normal_jacobian(model, data):
    rows = []
    for contact in data.contact[:data.ncon]:
        if contact.efc_address < 0:
            continue
        first = np.zeros((3, model.nv))
        second = np.zeros_like(first)
        mujoco.mj_jac(model, data, first, None, contact.pos, int(model.geom_bodyid[contact.geom1]))
        mujoco.mj_jac(model, data, second, None, contact.pos, int(model.geom_bodyid[contact.geom2]))
        rows.append(contact.frame[:3] @ (second - first))
    return np.asarray(rows).reshape(-1, model.nv)


def project_joint_velocities(model, data, joint_dof_addresses, velocity_limits, dt, *, position_limits=False, preserve_contacts=True):
    original_velocity = data.qvel.copy()
    lower = np.full(model.nv, -np.inf)
    upper = np.full(model.nv, np.inf)
    lower[joint_dof_addresses] = -velocity_limits
    upper[joint_dof_addresses] = velocity_limits
    if position_limits:
        joint_ids = model.dof_jntid[joint_dof_addresses]
        limited = model.jnt_limited[joint_ids].astype(bool)
        addresses = joint_dof_addresses[limited]
        positions = data.qpos[model.jnt_qposadr[joint_ids[limited]]]
        ranges = model.jnt_range[joint_ids[limited]]
        lower[addresses] = np.maximum(lower[addresses], original_velocity[addresses] + (ranges[:, 0] - positions) / dt)
        upper[addresses] = np.minimum(upper[addresses], original_velocity[addresses] + (ranges[:, 1] - positions) / dt)
    if np.all(original_velocity >= lower) and np.all(original_velocity <= upper):
        return
    mass = np.zeros((model.nv, model.nv))
    mujoco.mj_fullM(model, data, mass)
    metric = np.linalg.cholesky(mass).T
    fixed = lower >= upper - 1e-12
    projected = np.zeros(model.nv)
    projected[fixed] = np.where(lower[fixed] > 0.0, upper[fixed], lower[fixed])
    free = ~fixed
    if np.any(free):
        right_hand_side = metric @ original_velocity - metric[:, fixed] @ projected[fixed]
        solution = lsq_linear(metric[:, free], right_hand_side, bounds=(lower[free], upper[free]), method="bvls", tol=1e-12)
        if not solution.success:
            raise RuntimeError(f"Velocity projection failed: {solution.message}")
        projected[free] = solution.x
    normal_jacobian = contact_normal_jacobian(model, data) if preserve_contacts else np.empty((0, model.nv))
    minimum_normal_speed = np.minimum(normal_jacobian @ original_velocity, 0.0)
    if np.any(normal_jacobian @ projected < minimum_normal_speed - 1.0e-9):
        def objective(velocity):
            difference = velocity - original_velocity
            return 0.5 * difference @ mass @ difference

        def gradient(velocity):
            return mass @ (velocity - original_velocity)

        solution = minimize(
            objective, projected, jac=gradient, method="SLSQP",
            bounds=Bounds(lower, upper),
            constraints=LinearConstraint(normal_jacobian, minimum_normal_speed, np.inf),
            options={"ftol": 1.0e-12, "maxiter": 100},
        )
        if not solution.success or np.any(normal_jacobian @ solution.x < minimum_normal_speed - 1.0e-8):
            raise RuntimeError(f"Contact velocity projection failed: {solution.message}")
        projected = solution.x
    data.qvel[:] = projected
    mujoco.mj_integratePos(model, data.qpos, data.qvel - original_velocity, dt)