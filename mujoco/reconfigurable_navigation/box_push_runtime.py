"""MuJoCo counterpart of the hybrid PUSH arm controller."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import runpy

import mujoco
import numpy as np
import torch

from .box_climb_runtime import BoxClimbRuntime
from .locomotion_runtime import JOINT_NAMES, MJ_POLICY_INDICES, POLICY_MJ_INDICES, projected_gravity


CONTROL_PATH = Path(__file__).resolve().parents[2] / "source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/box_push_control.py"
CONTROL = runpy.run_path(str(CONTROL_PATH))


def batch(value):
    return torch.as_tensor(np.asarray(value), dtype=torch.float64).unsqueeze(0)


class BoxPushArmController:
    def __init__(self, runtime, box_geom: int, goal: np.ndarray, *, hand_body_name="x5_link6", mount_body_name="x5_base_link", hand_body_names=("x5_link6", "x5_link7", "x5_link8"), hand_offset=(0.15, 0.0, 0.0), align_hand_orientation=False, hand_pitch=0.0, approach_distance=0.10, hand_height_offset=0.0, collision_arm_body_names=(), collision_protected_body_names=(), collision_clearance=0.0, body_clearance_minimum=0.0, safe_approach_waypoints=(), safe_approach_position_tolerance=0.04, safe_approach_velocity_tolerance=0.12, safe_approach_hold=False, safe_precontact=False, press_depth=0.02, press_on_legal_contact=False, lock_arm_on_contact=True, leg_release_ramp_s=0.0, leg_contact_ramp_s=0.0, forward_command_gain=1.0, stop_distance=0.10, source_bounded_pose_ik=False, orientation_weight=1.0):
        self.runtime = runtime
        self.model, self.data = runtime.model, runtime.data
        self.box_geom = box_geom
        self.box_body = int(self.model.geom_bodyid[box_geom])
        self.box_size = self.model.geom_size[box_geom].copy() * 2.0
        self.goal = np.asarray(goal, dtype=np.float64).copy()
        self.hand_body = runtime._body_id(hand_body_name)
        self.mount_body = runtime._body_id(mount_body_name)
        self.hand_bodies = {runtime._body_id(name) for name in hand_body_names}
        self.hand_offset = np.asarray(hand_offset, dtype=np.float64)
        self.align_hand_orientation = align_hand_orientation
        self.hand_pitch = hand_pitch
        self.approach_distance = approach_distance
        self.hand_height_offset = hand_height_offset
        self.press_depth = float(press_depth)
        self.press_on_legal_contact = bool(press_on_legal_contact)
        self.lock_arm_on_contact = bool(lock_arm_on_contact)
        self.leg_release_ramp_s = float(leg_release_ramp_s)
        self.leg_contact_ramp_s = float(leg_contact_ramp_s)
        self.forward_command_gain = float(forward_command_gain)
        self.stop_distance = float(stop_distance)
        self.source_bounded_pose_ik = bool(source_bounded_pose_ik)
        self.orientation_weight = float(orientation_weight)
        if not np.isfinite([hand_pitch, approach_distance, hand_height_offset]).all() or approach_distance <= 0:
            raise ValueError("Invalid hand orientation or approach distance")
        if not (0.0 < self.press_depth <= 0.15 and 0.0 <= self.leg_contact_ramp_s <= self.leg_release_ramp_s <= 2.0 and 0.0 < self.forward_command_gain <= 3.0 and 0.0 < self.stop_distance <= 0.2):
            raise ValueError("Invalid PUSH transfer contract")
        if self.leg_contact_ramp_s and (self.lock_arm_on_contact or safe_precontact):
            raise ValueError("Contact-accelerated leg blending requires unlocked ordinary PUSH")
        if not 0.0 < self.orientation_weight <= 1.0 or (self.source_bounded_pose_ik and not align_hand_orientation):
            raise ValueError("Bounded pose IK requires an oriented hand and a valid weight")
        if not np.isfinite(collision_clearance) or collision_clearance < 0.0:
            raise ValueError("Collision clearance must be finite and nonnegative")
        if body_clearance_minimum and (not source_bounded_pose_ik or not 0.08 < body_clearance_minimum <= 0.15):
            raise ValueError("Body clearance projection requires bounded pose IK and a minimum in (0.08, 0.15]")
        if self.hand_offset.shape != (3,) or not np.isfinite(self.hand_offset).all():
            raise ValueError("Expected a finite three-dimensional hand offset")
        self.arm_qpos = runtime.joint_qpos_adr[12:]
        self.arm_dof = runtime.joint_dof_adr[12:]
        joint_ids = self.model.dof_jntid[self.arm_dof]
        midpoint = self.model.jnt_range[joint_ids].mean(axis=1)
        half_range = 0.45 * np.ptp(self.model.jnt_range[joint_ids], axis=1)
        self.lower, self.upper = midpoint - half_range, midpoint + half_range
        self.gravity_data = mujoco.MjData(self.model)
        self.collision_clearance = float(collision_clearance)
        self.body_clearance_minimum = float(body_clearance_minimum)
        self.geometry_speed_slowdown_start = 0.0
        self.clearance_arm_bodies = tuple(runtime._body_id(name) for name in (
            "link2", "link3", "link4", "link5", "link6", "end_effector"
        )) if body_clearance_minimum else ()
        self.clearance_protected_bodies = tuple(runtime._body_id(name) for name in (
            "base_link", *(f"{leg}_{segment}" for leg in ("FL", "FR", "RL", "RR")
                           for segment in ("hip", "thigh", "calf", "foot"))
        )) if body_clearance_minimum else ()
        self.collision_blocked = False
        collision_arm_bodies = {runtime._body_id(name) for name in collision_arm_body_names}
        collision_protected_bodies = {runtime._body_id(name) for name in collision_protected_body_names}
        self.collision_arm_geoms = tuple(
            index for index, body_id in enumerate(self.model.geom_bodyid)
            if int(body_id) in collision_arm_bodies and (self.model.geom_contype[index] or self.model.geom_conaffinity[index])
        )
        self.collision_protected_geoms = tuple(
            index for index, body_id in enumerate(self.model.geom_bodyid)
            if int(body_id) in collision_protected_bodies and (self.model.geom_contype[index] or self.model.geom_conaffinity[index])
        )
        self.safe_approach_waypoints = np.asarray(safe_approach_waypoints, dtype=np.float64)
        if self.safe_approach_waypoints.size == 0:
            self.safe_approach_waypoints = self.safe_approach_waypoints.reshape(0, len(self.arm_qpos))
        if self.safe_approach_waypoints.ndim != 2 or self.safe_approach_waypoints.shape[1] != len(self.arm_qpos):
            raise ValueError("PUSH safe approach waypoints must have one row per arm joint target")
        if not np.isfinite(self.safe_approach_waypoints).all() or safe_approach_position_tolerance <= 0.0 or safe_approach_velocity_tolerance <= 0.0:
            raise ValueError("Invalid PUSH safe approach configuration")
        self.safe_approach_position_tolerance = float(safe_approach_position_tolerance)
        self.safe_approach_velocity_tolerance = float(safe_approach_velocity_tolerance)
        self.safe_approach_hold = safe_approach_hold
        self.safe_precontact = safe_precontact
        self.precontact_heights = (0.20, 0.10, 0.0)
        if safe_precontact and (safe_approach_hold or len(self.safe_approach_waypoints) < 2):
            raise ValueError("Online precontact requires a safe approach path and released final hold")
        self.reset()

    def reset(self):
        self.reference = self.data.qpos[self.arm_qpos].copy()
        self.locked_reference = self.reference.copy()
        self.locked = False
        self.motion_ready = False
        self.approached = False
        self.collision_blocked = False
        self.body_clearance_distance = None
        self.body_clearance_residual = 0.0
        self.body_clearance_correction = 0.0
        self.geometry_speed_scale = 1.0
        self.last_valid_contact_time = -np.inf
        self.safe_approach_index = 1 if len(self.safe_approach_waypoints) > 1 else 0
        self.precontact_index = 0
        self.precontact_stable_time = 0.0
        self.leg_release_blend = 0.0
        self.leg_release_elapsed = 0.0
        self.pose_override = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])

    def hand_position(self):
        rotation = self.data.xmat[self.hand_body].reshape(3, 3)
        return self.data.xpos[self.hand_body] + rotation @ self.hand_offset

    def box_rotation(self):
        return self.data.geom_xmat[self.box_geom].reshape(3, 3)

    def at_goal(self):
        return self.goal[0] - self.data.geom_xpos[self.box_geom, 0] < self.stop_distance

    def hand_target(self):
        position = self.data.geom_xpos[self.box_geom]
        rotation = self.box_rotation()
        local = rotation.T @ (self.hand_position() - position)
        self.approached |= bool(CONTROL["side_approach_ready"](
            batch(local), self.box_size[0] / 2.0, self.approach_distance,
            target_height=self.hand_height_offset,
        )[0])
        self.approached &= abs(local[2] - self.hand_height_offset) < 0.06
        legal_contact = self.press_on_legal_contact and self.safe_approach_complete() and self.contacts()["valid"]
        press = self.press_depth if (self.approached or legal_contact) and not self.at_goal() else -self.approach_distance
        return position + rotation @ np.array([-self.box_size[0] / 2.0 + press, 0.0, self.hand_height_offset])

    def contacts(self):
        hand_force = np.zeros(3)
        hand_total_force = np.zeros(3)
        positions = []
        contact_pairs = []
        other_forces = {}
        wrench = np.zeros(6)
        for index in range(self.data.ncon):
            contact = self.data.contact[index]
            if self.box_geom not in (contact.geom1, contact.geom2):
                continue
            other = contact.geom2 if contact.geom1 == self.box_geom else contact.geom1
            body = int(self.model.geom_bodyid[other])
            if body == 0:
                continue
            mujoco.mj_contactForce(self.model, self.data, index, wrench)
            force = contact.frame.reshape(3, 3)[0] * wrench[0]
            total_force = contact.frame.reshape(3, 3).T @ wrench[:3]
            if other == contact.geom1:
                force = -force
                total_force = -total_force
            if body in self.hand_bodies:
                hand_force += force
                hand_total_force += total_force
                if np.linalg.norm(force) > 0.0:
                    positions.append(contact.pos.copy())
                    contact_pairs.append({
                        "geom": self.model.geom(other).name,
                        "body": self.model.body(body).name,
                        "position": contact.pos.copy().tolist(),
                        "normal_force": force.copy().tolist(),
                    })
            else:
                other_forces[body] = other_forces.get(body, np.zeros(3)) + force
        position = np.mean(positions, axis=0) if positions else np.full(3, np.nan)
        local = self.box_rotation().T @ (position - self.data.geom_xpos[self.box_geom])
        near_tip = np.linalg.norm(position - self.hand_position()) < 0.07
        strength = float(np.linalg.norm(hand_force))
        resisting_force = float(-hand_force @ self.box_rotation()[:, 0])
        criteria = {
            "finite": bool(np.isfinite(local).all()),
            "near_tip": bool(near_tip),
            "strength": strength > 1.0,
            "force_direction": resisting_force > 0.8 * strength,
            "front_face": bool(np.isfinite(local[0]) and abs(local[0] + self.box_size[0] / 2.0) < 0.02),
            "within_width": bool(np.isfinite(local[1]) and abs(local[1]) < self.box_size[1] / 2.0),
            "within_height": bool(np.isfinite(local[2]) and abs(local[2]) < self.box_size[2] / 2.0 - 0.01),
        }
        valid = bool(CONTROL["valid_front_contact"](
            batch(hand_force), batch(self.box_rotation()[:, 0]), batch(local),
            torch.tensor([bool(near_tip)], dtype=torch.bool), self.box_size,
        )[0])
        return {
            "valid": valid,
            "invalid_hand": bool(np.linalg.norm(hand_force) > 1.0 and not valid),
            "forbidden": any(np.linalg.norm(force) > 1.0 for force in other_forces.values()),
            "force": hand_force,
            "total_force": hand_total_force,
            "position": position,
            "local_position": local,
            "tip_distance": float(np.linalg.norm(position - self.hand_position())),
            "resisting_force": resisting_force,
            "criteria": criteria,
            "contacts": contact_pairs,
        }

    def _minimum_protected_clearance(self, arm_qpos):
        if not self.collision_arm_geoms or not self.collision_protected_geoms:
            return float("inf")
        original = self.data.qpos[self.arm_qpos].copy()
        self.data.qpos[self.arm_qpos] = arm_qpos
        mujoco.mj_forward(self.model, self.data)
        minimum = min(
            mujoco.mj_geomDistance(self.model, self.data, arm, protected, 1.0, None)
            for arm in self.collision_arm_geoms
            for protected in self.collision_protected_geoms
        )
        self.data.qpos[self.arm_qpos] = original
        mujoco.mj_forward(self.model, self.data)
        return float(minimum)

    def protected_collision_active(self):
        protected_pairs = {
            frozenset((arm, protected))
            for arm in self.collision_arm_geoms
            for protected in self.collision_protected_geoms
        }
        return any(
            frozenset((int(contact.geom1), int(contact.geom2))) in protected_pairs
            for contact in self.data.contact[:self.data.ncon]
        )

    def _clearance_retreat_target(self):
        current = self.data.qpos[self.arm_qpos].copy()
        candidate = current.copy()
        step = 0.04
        for _ in range(3):
            best = candidate
            best_clearance = self._minimum_protected_clearance(candidate)
            for joint_index in range(len(candidate)):
                for direction in (-1.0, 1.0):
                    proposal = candidate.copy()
                    proposal[joint_index] = np.clip(
                        proposal[joint_index] + direction * step,
                        self.lower[joint_index],
                        self.upper[joint_index],
                    )
                    clearance = self._minimum_protected_clearance(proposal)
                    if clearance > best_clearance:
                        best, best_clearance = proposal, clearance
            if np.array_equal(best, candidate):
                break
            candidate = best
        return candidate

    def _collision_safe_target(self, desired):
        current = self.data.qpos[self.arm_qpos].copy()
        if self._minimum_protected_clearance(current) < 1.15 * self.collision_clearance:
            desired = self._clearance_retreat_target()
        for fraction in (1.0, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125, 0.0):
            candidate = current + fraction * (desired - current)
            path = np.linspace(current, candidate, 8)
            if all(self._minimum_protected_clearance(point) >= self.collision_clearance for point in path):
                self.collision_blocked = fraction < 1.0
                return candidate
        self.collision_blocked = True
        return current

    def _project_body_clearance(self, next_reference):
        arm_positions = self.data.xpos[list(self.clearance_arm_bodies)]
        protected_positions = self.data.xpos[list(self.clearance_protected_bodies)]
        separation = arm_positions[:, None, :] - protected_positions[None, :, :]
        distance = np.linalg.norm(separation, axis=2)
        normal = separation / np.maximum(distance[:, :, None], 1.0e-9)
        jacobian = np.zeros((3, self.model.nv))

        def body_jacobians(body_ids):
            values = []
            for body_id in body_ids:
                mujoco.mj_jacBody(self.model, self.data, jacobian, None, body_id)
                values.append(jacobian[:, self.arm_dof].copy())
            return np.stack(values)

        relative = (body_jacobians(self.clearance_arm_bodies)[:, None]
                    - body_jacobians(self.clearance_protected_bodies)[None, :])
        gradient = np.sum(normal[..., None] * relative, axis=2).reshape(1, -1, len(self.arm_qpos))
        lower = np.maximum(self.lower, self.reference - self.runtime.control_dt)
        upper = np.minimum(self.upper, self.reference + self.runtime.control_dt)
        projected, residual = CONTROL["project_clearance_target"](
            batch(next_reference), batch(self.data.qpos[self.arm_qpos]),
            torch.as_tensor(gradient), batch(distance.ravel()), batch(lower), batch(upper),
            minimum=self.body_clearance_minimum,
        )
        projected = projected[0].numpy()
        self.body_clearance_distance = float(distance.min())
        self.body_clearance_residual = float(residual[0])
        self.body_clearance_correction = float(np.max(np.abs(projected - next_reference)))
        return projected

    def safe_approach_complete(self):
        return self.safe_approach_index >= len(self.safe_approach_waypoints)

    def _safe_approach_target(self):
        if self.safe_approach_complete():
            return self.safe_approach_waypoints[-1] if self.safe_approach_hold and len(self.safe_approach_waypoints) else None
        joint_position = self.data.qpos[self.arm_qpos]
        joint_velocity = self.data.qvel[self.arm_dof]
        waypoint = self.safe_approach_waypoints[self.safe_approach_index]
        if (
            np.max(np.abs(joint_position - waypoint)) < self.safe_approach_position_tolerance
            and np.max(np.abs(joint_velocity)) < self.safe_approach_velocity_tolerance
        ):
            self.safe_approach_index += 1
            if self.safe_approach_complete():
                return self.safe_approach_waypoints[-1] if self.safe_approach_hold or self.safe_precontact else None
            waypoint = self.safe_approach_waypoints[self.safe_approach_index]
        return waypoint

    def precontact_complete(self):
        return not self.safe_precontact or self.precontact_index >= len(self.precontact_heights)

    def _precontact_target(self):
        if self.precontact_complete():
            return None
        offset = np.array([
            -self.box_size[0] / 2.0 - self.approach_distance,
            0.0, self.hand_height_offset + self.precontact_heights[self.precontact_index],
        ])
        target = self.data.geom_xpos[self.box_geom] + self.box_rotation() @ offset
        settled = (
            np.linalg.norm(self.hand_position() - target) < 0.025
            and np.max(np.abs(self.data.qvel[self.arm_dof])) < 0.20
        )
        final_contact = self.precontact_index == len(self.precontact_heights) - 1 and self.contacts()["valid"]
        if settled or final_contact:
            self.precontact_index += 1
            return self._precontact_target()
        return target

    def apply(self, leg_actions, *, target=None):
        if np.shape(leg_actions) != (12,):
            raise ValueError("Hybrid PUSH requires 12 leg actions")
        position = self.hand_position()
        safe_approach_target = self._safe_approach_target()
        precontact_target = None
        if self.safe_precontact and self.safe_approach_complete() and not self.precontact_complete():
            stable = (
                np.linalg.norm(self.data.qvel[:3]) < 0.06
                and np.linalg.norm(self.data.qvel[3:6]) < 0.20
                and projected_gravity(self.data.qpos[3:7])[2] < -0.96
            )
            self.precontact_stable_time = self.precontact_stable_time + self.runtime.control_dt if stable else 0.0
            if self.precontact_stable_time < 0.5:
                safe_approach_target = self.safe_approach_waypoints[-1]
            else:
                precontact_target = self._precontact_target()
        if target is None:
            target = self.hand_target() if precontact_target is None else precontact_target
        else:
            target = np.asarray(target, dtype=np.float64)
        if target.shape != (3,) or not np.isfinite(target).all():
            raise ValueError("Arm target requires three finite world coordinates")
        if self.lock_arm_on_contact and self.contacts()["valid"] and self.precontact_complete() and not self.locked and not self.at_goal():
            self.locked_reference = self.reference.copy()
            self.pose_override[:3] = self.data.xmat[self.mount_body].reshape(3, 3).T @ (position - self.data.xpos[self.mount_body])
            self.locked = True
        self.locked &= not self.at_goal()
        self.motion_ready |= self.locked
        if not self.lock_arm_on_contact and self.safe_approach_complete():
            self.motion_ready |= self.approached
        jacobian = np.zeros((3, self.model.nv))
        angular_jacobian = np.zeros_like(jacobian) if self.align_hand_orientation else None
        mujoco.mj_jac(self.model, self.data, jacobian, angular_jacobian, position, self.hand_body)
        arm_jacobian = jacobian[:, self.arm_dof]
        error = target - position
        if self.align_hand_orientation:
            box_quaternion, actual_quaternion, inverse_actual = np.zeros(4), np.zeros(4), np.zeros(4)
            mujoco.mju_mat2Quat(box_quaternion, self.box_rotation().ravel())
            mujoco.mju_mat2Quat(actual_quaternion, self.data.xmat[self.hand_body])
            desired_quaternion, difference = np.zeros(4), np.zeros(4)
            mujoco.mju_mulQuat(desired_quaternion, box_quaternion, np.array([np.cos(self.hand_pitch/2), 0, np.sin(self.hand_pitch/2), 0]))
            mujoco.mju_negQuat(inverse_actual, actual_quaternion)
            mujoco.mju_mulQuat(difference, desired_quaternion, inverse_actual)
            if difference[0] < 0:
                difference *= -1
            angular_error = np.zeros(3)
            mujoco.mju_quat2Vel(angular_error, difference, 1.0)
            arm_jacobian = np.concatenate((arm_jacobian, angular_jacobian[:, self.arm_dof]))
            error = np.concatenate((error, angular_error))
        if self.source_bounded_pose_ik:
            scale = CONTROL["pose_task_scale"](
                torch.as_tensor(arm_jacobian).unsqueeze(0), orientation_weight=self.orientation_weight,
            ).numpy()
            joint_position = self.data.qpos[self.arm_qpos]
            delta = CONTROL["bounded_pose_delta"](
                torch.as_tensor((arm_jacobian * scale[:, None])[None]),
                torch.as_tensor((error * scale)[None]),
                torch.as_tensor((self.lower - joint_position)[None]),
                torch.as_tensor((self.upper - joint_position)[None]),
            )[0].numpy()
        else:
            delta = arm_jacobian.T @ np.linalg.solve(arm_jacobian @ arm_jacobian.T + 0.01 * np.eye(len(error)), error)
        desired = np.clip(self.data.qpos[self.arm_qpos] + delta, self.lower, self.upper)
        if safe_approach_target is not None:
            desired = safe_approach_target
        if self.locked:
            desired = self.locked_reference.copy()
        if self.body_clearance_minimum and self.safe_approach_complete():
            next_reference = CONTROL["coordinated_joint_target"](
                batch(self.reference), batch(desired), self.runtime.control_dt,
            )[0].numpy()
            desired = self._project_body_clearance(next_reference)
        desired = self._collision_safe_target(desired)
        if self.locked and (self.collision_blocked or not np.allclose(desired, self.locked_reference, atol=1.0e-10, rtol=0.0)):
            self.locked = False
            self.motion_ready = False
        if self.collision_blocked:
            self.reference = self.data.qpos[self.arm_qpos].copy()
        self.reference = CONTROL["coordinated_joint_target"](batch(self.reference), batch(desired), self.runtime.control_dt)[0].numpy()
        if self.locked:
            self.reference = desired.copy()
        self.gravity_data.qpos[:] = self.data.qpos
        self.gravity_data.qvel.fill(0.0)
        mujoco.mj_forward(self.model, self.gravity_data)
        compensated = self.reference + self.gravity_data.qfrc_bias[self.arm_dof] / self.runtime.kp[12:]
        combined = np.zeros(18)
        if self.motion_ready:
            if self.leg_release_ramp_s:
                self.leg_release_elapsed += self.runtime.control_dt
                if self.leg_contact_ramp_s:
                    legal_contact = self.contacts()["valid"] and self.safe_approach_complete()
                    self.leg_release_blend = float(CONTROL["advance_leg_blend"](
                        torch.tensor([self.leg_release_blend]), torch.tensor([True]),
                        torch.tensor([legal_contact]), dt=self.runtime.control_dt,
                        ramp_time=self.leg_release_ramp_s, contact_ramp_time=self.leg_contact_ramp_s,
                    )[0])
                else:
                    self.leg_release_blend = min(1.0, self.leg_release_elapsed / self.leg_release_ramp_s)
                combined[:12] = leg_actions * self.leg_release_blend
            else:
                combined[:12] = leg_actions
        else:
            self.leg_release_elapsed = self.leg_release_blend = 0.0
        combined[12:] = (compensated - self.runtime.default_qpos[12:]) / self.runtime.action_scale[12:]
        return combined


class BoxPushRuntime(BoxClimbRuntime):
    def __init__(self, policy_path, *, model, data, box_geom, goal, deploy_config=None, joint_names=JOINT_NAMES, base_body_name="base", arm_config=None):
        super().__init__(policy_path, model=model, data=data, deploy_config=deploy_config, joint_names=joint_names, base_body_name=base_body_name)
        self.joint_velocity_limits[12:] = 3.0
        self.arm = BoxPushArmController(self, box_geom, goal, **(arm_config or {}))
        self.history = deque(maxlen=3)
        self.activate()

    def activate(self):
        super().activate()
        if hasattr(self, "arm"):
            self.arm.reset()
            frame = self._frame()
            self.history.clear()
            self.history.extend(frame.copy() for _ in range(3))

    def _yaw_rotation(self):
        rotation = self.data.xmat[self.base_id].reshape(3, 3)
        yaw = np.arctan2(rotation[1, 0], rotation[0, 0])
        return np.array([[np.cos(yaw), -np.sin(yaw), 0.0], [np.sin(yaw), np.cos(yaw), 0.0], [0.0, 0.0, 1.0]])

    def _box_velocity(self):
        velocity = np.zeros(6)
        mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self.arm.box_body, velocity, 0)
        return velocity[3:]

    def _commands(self):
        rotation = self._yaw_rotation()
        position = self.data.geom_xpos[self.arm.box_geom]
        face = position - self.arm.box_rotation()[:, 0] * self.arm.box_size[0] / 2.0
        relative_face = rotation.T @ (face - self.data.xpos[self.base_id])
        direction = rotation.T @ (self.arm.goal - position)
        contact = self.arm.contacts()
        velocity = CONTROL["contact_push_velocity"](
            batch(relative_face), batch(rotation.T @ self._box_velocity()),
            torch.tensor([self.arm.goal[0] - position[0]], dtype=torch.float64),
            torch.tensor([contact["valid"] and not contact["forbidden"]], dtype=torch.bool),
            torch.tensor([np.arctan2(direction[1], direction[0])], dtype=torch.float64),
            forward_gain=self.arm.forward_command_gain, stop_distance=self.arm.stop_distance,
        )[0].numpy()
        self.arm.geometry_speed_scale = 1.0
        if contact["valid"]:
            self.arm.last_valid_contact_time = float(self.data.time)
        recent_contact = self.data.time - self.arm.last_valid_contact_time <= 0.10
        if self.arm.geometry_speed_slowdown_start and recent_contact and velocity[0] > 0.0:
            clearance = self.arm._minimum_protected_clearance(self.data.qpos[self.arm.arm_qpos])
            self.arm.geometry_speed_scale = float(np.clip(
                (clearance - self.arm.collision_clearance)
                / (self.arm.geometry_speed_slowdown_start - self.arm.collision_clearance), 0.0, 1.0,
            ))
            velocity[0] *= self.arm.geometry_speed_scale
        target = self.arm.hand_target()
        local = self.data.xmat[self.arm.mount_body].reshape(3, 3).T @ (target - self.data.xpos[self.arm.mount_body])
        pose = self.arm.pose_override.copy() if self.arm.locked else np.concatenate((local, [1.0, 0.0, 0.0, 0.0]))
        return velocity, pose

    def _frame(self):
        velocity, pose = self._commands()
        return np.concatenate((
            self.data.qvel[3:6] * 0.2, projected_gravity(self.data.xquat[self.base_id]),
            (self.data.qpos[self.joint_qpos_adr] - self.default_qpos)[MJ_POLICY_INDICES],
            self.data.qvel[self.joint_dof_adr][MJ_POLICY_INDICES] * 0.05,
            self.last_action, velocity, pose,
        )).astype(np.float32)

    def observation(self):
        slices = ((0, 3), (3, 6), (6, 24), (24, 42), (42, 60), (60, 63), (63, 70))
        history = np.concatenate([frame[start:end] for start, end in slices for frame in self.history])
        rotation = self._yaw_rotation()
        position = self.data.geom_xpos[self.arm.box_geom]
        box = np.concatenate((
            rotation.T @ (position - self.data.xpos[self.base_id]),
            rotation.T @ self._box_velocity(), rotation.T @ (self.arm.goal - position),
            (rotation.T @ self.arm.box_rotation()[:, 0])[:2], self.arm.box_size,
            [float(self.arm.locked), float(self.arm.contacts()["valid"])],
        ))
        observation = np.concatenate((history, box)).astype(np.float32)
        if observation.shape != (226,) or not np.isfinite(observation).all():
            raise ValueError("Hybrid PUSH requires 226 finite observations")
        return observation

    def step(self):
        with torch.inference_mode():
            actions = self.policy(torch.from_numpy(self.observation()).unsqueeze(0))[0].numpy()
        combined = self.arm.apply(actions)
        self._simulate_target(self.default_qpos + combined[POLICY_MJ_INDICES] * self.action_scale)
        self.last_action = combined.copy()
        self.history.append(self._frame())
        return combined.copy()
