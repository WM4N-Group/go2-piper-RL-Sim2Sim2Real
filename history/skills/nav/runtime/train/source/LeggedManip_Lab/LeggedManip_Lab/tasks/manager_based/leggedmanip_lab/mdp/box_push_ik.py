"""Optional IK arm controller for physical PUSH diagnostics."""

import torch

from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import compute_pose_error, quat_apply, quat_apply_inverse, quat_from_euler_xyz, quat_mul, yaw_quat

from .box_push import hand_contact, nominal_push_velocity_commands, preapproach_state, push_control_at_goal, push_hand_target
from .box_push_control import advance_leg_blend, bounded_pose_delta, bounded_push_target, confirmed_push_contact, contact_action_blend, coordinated_joint_target, force_limited_contact_advance, latch_goal_pose, latch_leg_contact, pose_task_scale, project_clearance_target, retained_push_contact, stabilized_ik_target, weighted_pose_delta


class PushArmIK:
    def __init__(self, env, hold_legs_until_ready=False, lock_arm_on_contact=False, align_hand_orientation=False, hand_pitch=0.0, safe_approach_waypoints=(), safe_approach_position_tolerance=0.04, safe_approach_velocity_tolerance=0.12, safe_approach_start_complete=False, safe_approach_hold=False, legs_active_after_safe_approach=False):
        self.env = env
        self.robot = env.scene["robot"]
        self.hand_id = self.robot.find_bodies("end_effector")[0][0]
        self.mount_id = self.robot.find_bodies("link0")[0][0]
        self.hand_cfg = SceneEntityCfg("robot", body_names="end_effector")
        self.hand_cfg.resolve(env.scene)
        self.lock_arm_on_contact = lock_arm_on_contact
        self.align_hand_orientation = align_hand_orientation
        self.orientation_weight = getattr(env.cfg, "push_ik_orientation_weight", 1.0)
        self.joint_limit_solve = getattr(env.cfg, "push_ik_joint_limit_solve", False)
        self.height_weight = getattr(env.cfg, "push_ik_height_weight", 1.0)
        if not 1.0 <= self.height_weight <= 3.0 or (self.height_weight != 1.0 and not self.joint_limit_solve):
            raise ValueError("PUSH IK height weight requires [1, 3] and bounded pose IK")
        if not 0.0 < self.orientation_weight <= 1.0:
            raise ValueError("PUSH IK orientation weight must be in (0, 1]")
        if self.orientation_weight != 1.0 and not align_hand_orientation:
            raise ValueError("Weighted pose IK requires hand orientation alignment")
        if self.joint_limit_solve and not align_hand_orientation:
            raise ValueError("Bounded pose IK requires hand orientation alignment")
        self.hand_rotation = quat_from_euler_xyz(
            torch.zeros(env.num_envs, device=env.device),
            torch.full((env.num_envs,), hand_pitch, device=env.device),
            torch.zeros(env.num_envs, device=env.device),
        )
        self.locked = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        env.box_push_pose_override_active = self.locked
        env.box_push_pose_override = torch.zeros((env.num_envs, 7), device=env.device)
        self.joint_ids = self.robot.find_joints("joint.*", preserve_order=True)[0]
        action_joints = self.robot.find_joints(env.cfg.actions.joint_pos.joint_names, preserve_order=True)[0]
        self.action_slots = [action_joints.index(joint_id) for joint_id in self.joint_ids]
        self.leg_slots = [index for index in range(len(action_joints)) if index not in self.action_slots]
        self.hold_legs_until_ready = hold_legs_until_ready
        self.motion_ready = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        self.body_first = getattr(env.cfg, "push_body_first", False)
        self.full_body_preapproach = getattr(env.cfg, "push_full_body_preapproach", False) or self.body_first
        self.body_ready = torch.zeros_like(self.motion_ready)
        self.body_ready_duration = torch.zeros(env.num_envs, device=env.device)
        self.preapproach_elapsed = torch.zeros(env.num_envs, device=env.device)
        self.safe_approach_complete = torch.zeros_like(self.motion_ready)
        env.box_push_body_ready = self.body_ready
        env.box_push_preapproach_elapsed = self.preapproach_elapsed
        env.box_push_safe_approach_complete = self.safe_approach_complete
        offset = 0 if self.robot.is_fixed_base else 6
        self.jacobian_columns = [joint_id + offset for joint_id in self.joint_ids]
        self.jacobian_body = self.hand_id - 1 if self.robot.is_fixed_base else self.hand_id
        self.scale = env.cfg.actions.joint_pos.scale
        if not isinstance(self.scale, (int, float)) or self.scale <= 0.0:
            raise ValueError("IK diagnostic requires a positive scalar joint action scale")
        self.reference = self.robot.data.joint_pos[:, self.joint_ids].clone()
        self.clearance_minimum = getattr(env.cfg, "push_ik_clearance_minimum", None)
        self.clearance_residual = torch.zeros(env.num_envs, device=env.device)
        self.clearance_correction = torch.zeros(env.num_envs, device=env.device)
        self.clearance_distance = torch.zeros(env.num_envs, device=env.device)
        if self.clearance_minimum is not None:
            if not 0.08 < self.clearance_minimum <= 0.15 or self.lock_arm_on_contact:
                raise ValueError("Clearance diagnostic requires an unlocked arm and a distance in (0.08, 0.15]")
            self.clearance_arm_ids = self.robot.find_bodies("link[2-6]|end_effector")[0]
            self.clearance_protected_ids = self.robot.find_bodies("base|.*_(hip|thigh|calf|foot)")[0]
            if not self.clearance_arm_ids or not self.clearance_protected_ids:
                raise ValueError("Clearance diagnostic requires arm and protected robot bodies")
        self.locked_reference = self.reference.clone()
        self.safe_approach_waypoints = torch.as_tensor(safe_approach_waypoints, dtype=torch.float32, device=env.device)
        if self.safe_approach_waypoints.numel() == 0:
            self.safe_approach_waypoints = self.safe_approach_waypoints.reshape(0, len(self.joint_ids))
        if self.safe_approach_waypoints.ndim != 2 or self.safe_approach_waypoints.shape[1] != len(self.joint_ids):
            raise ValueError("PUSH safe approach waypoints must have one row per arm joint target")
        if not torch.isfinite(self.safe_approach_waypoints).all() or safe_approach_position_tolerance <= 0.0 or safe_approach_velocity_tolerance <= 0.0:
            raise ValueError("Invalid PUSH safe approach configuration")
        self.safe_approach_position_tolerance = safe_approach_position_tolerance
        self.safe_approach_velocity_tolerance = safe_approach_velocity_tolerance
        self.safe_approach_start_complete = safe_approach_start_complete
        self.safe_approach_hold = safe_approach_hold
        self.legs_active_after_safe_approach = legs_active_after_safe_approach
        self.safe_approach_index = torch.full((env.num_envs,), 1 if len(self.safe_approach_waypoints) > 1 else 0, dtype=torch.long, device=env.device)
        self.safe_approach_complete[:] = len(self.safe_approach_waypoints) == 0
        self.precontact_posture = torch.as_tensor(
            getattr(env.cfg, "push_precontact_posture", ()), dtype=torch.float32, device=env.device,
        )
        if self.precontact_posture.numel() not in (0, len(self.joint_ids)):
            raise ValueError("PUSH precontact posture must contain one target per arm joint")
        if not torch.isfinite(self.precontact_posture).all():
            raise ValueError("PUSH precontact posture must be finite")
        self.precontact_heights = torch.as_tensor(
            getattr(env.cfg, "push_precontact_heights", ()), dtype=torch.float32, device=env.device,
        )
        if self.precontact_heights.numel():
            if self.precontact_heights.ndim != 1 or not torch.isfinite(self.precontact_heights).all():
                raise ValueError("Cartesian precontact heights must be a finite vector")
            if (self.precontact_heights < 0.0).any() or self.precontact_heights[-1] != 0.0:
                raise ValueError("Cartesian precontact must end at the contact height")
            if self.precontact_posture.numel() or self.full_body_preapproach or self.safe_approach_hold or len(self.safe_approach_waypoints) < 2:
                raise ValueError("Cartesian precontact requires a released safe approach without a joint-posture override")
        self.precontact_stage = torch.zeros(env.num_envs, dtype=torch.long, device=env.device)
        self.contact_duration = torch.zeros(env.num_envs, device=env.device)
        self.precontact_raise_position = torch.zeros((env.num_envs, 3), device=env.device)
        self.precontact_raise_initialized = torch.zeros_like(self.motion_ready)
        self.contact_advance = torch.zeros(env.num_envs, device=env.device)
        self.target_position = self.robot.data.body_pos_w[:, self.hand_id].clone()
        self.goal_hold_pose = getattr(env.cfg, "push_goal_hold_pose", False)
        self.goal_release_distance = getattr(env.cfg, "push_goal_release_distance", 0.0)
        if not 0.0 <= self.goal_release_distance <= 0.02 or (self.goal_release_distance and not self.goal_hold_pose):
            raise ValueError("Goal contact release requires goal pose hold and distance in [0, .02]")
        self.leg_release_on_contact = getattr(env.cfg, "push_leg_release_on_contact", False)
        if self.leg_release_on_contact and (lock_arm_on_contact or self.precontact_heights.numel() or self.full_body_preapproach):
            raise ValueError("Contact-triggered leg release requires ordinary unlocked Tracking")
        self.leg_contact_ready = torch.zeros_like(self.motion_ready)
        if self.goal_hold_pose and (lock_arm_on_contact or not align_hand_orientation or self.precontact_heights.numel() or self.full_body_preapproach):
            raise ValueError("Goal pose hold requires ordinary unlocked pose Tracking")
        self.goal_hold_active = torch.zeros_like(self.motion_ready)
        self.goal_hold_position = self.target_position.clone()
        self.goal_hold_quaternion = self.robot.data.body_quat_w[:, self.hand_id].clone()
        if self.goal_hold_pose:
            env.box_push_goal_hold_active = self.goal_hold_active
            env.box_push_goal_hold_position = self.goal_hold_position
        env.box_push_precontact_stage = self.precontact_stage
        self.precontact_ready = torch.full(
            (env.num_envs,), self.precontact_posture.numel() == 0 and self.precontact_heights.numel() == 0, dtype=torch.bool, device=env.device,
        )
        env.box_push_precontact_ready = self.precontact_ready
        self.contact_memory_s = getattr(env.cfg, "push_contact_memory_s", 0.0)
        if not 0.0 <= self.contact_memory_s <= 0.2:
            raise ValueError("PUSH contact memory must be in [0, 0.2] seconds")
        self.contact_memory_left = torch.zeros(env.num_envs, device=env.device)
        self.drive_contact = torch.zeros_like(self.motion_ready)
        env.box_push_drive_contact = self.drive_contact
        self.leg_release_ramp_s = getattr(env.cfg, "push_leg_release_ramp_s", 0.0)
        if not 0.0 <= self.leg_release_ramp_s <= 2.0:
            raise ValueError("PUSH leg release ramp must be in [0, 2] seconds")
        self.leg_contact_ramp_s = getattr(env.cfg, "push_leg_contact_ramp_s", 0.0)
        if not 0.0 <= self.leg_contact_ramp_s <= self.leg_release_ramp_s:
            raise ValueError("Contact leg ramp must be nonnegative and <= ordinary leg ramp")
        if self.leg_contact_ramp_s and (self.leg_release_on_contact or self.full_body_preapproach or self.precontact_heights.numel() or lock_arm_on_contact):
            raise ValueError("Contact-accelerated blending requires ordinary unlocked Tracking")
        self.leg_release_blend = torch.zeros(env.num_envs, device=env.device)
        self.leg_release_elapsed = torch.zeros(env.num_envs, device=env.device)
        self.velocity_integral_gain = getattr(env.cfg, "push_velocity_integral_gain", 0.0)
        if not 0.0 <= self.velocity_integral_gain <= 3.0:
            raise ValueError("PUSH velocity integral gain must be in [0, 3]")
        if self.velocity_integral_gain and not getattr(env.cfg, "push_velocity_feedback_gain", 0.0):
            raise ValueError("PUSH integral feedback requires proportional feedback")
        self.velocity_integral = torch.zeros((env.num_envs, 2), device=env.device)
        env.box_push_velocity_integral = self.velocity_integral
        self.stiffness = torch.stack([
            self.robot.actuators[self.robot.joint_names[joint_id]].stiffness[:, 0]
            for joint_id in self.joint_ids
        ], dim=1)
        if (self.stiffness <= 0.0).any():
            raise ValueError("Gravity compensation requires positive arm stiffness")
        self.controller = DifferentialIKController(
            DifferentialIKControllerCfg(command_type="pose" if align_hand_orientation else "position", use_relative_mode=False, ik_method="dls", ik_params={"lambda_val": 0.1}),
            num_envs=env.num_envs, device=env.device,
        )
        self.position_controller = DifferentialIKController(
            DifferentialIKControllerCfg(command_type="position", use_relative_mode=False, ik_method="dls", ik_params={"lambda_val": 0.1}),
            num_envs=env.num_envs, device=env.device,
        ) if self.precontact_heights.numel() else None

    def reset(self, env_ids):
        selected = slice(None) if env_ids is None else env_ids
        self.reference[selected] = self.robot.data.joint_pos[selected][:, self.joint_ids]
        self.motion_ready[selected] = False
        self.body_ready[selected] = False
        self.body_ready_duration[selected] = 0.0
        self.preapproach_elapsed[selected] = 0.0
        self.locked[selected] = False
        self.clearance_residual[selected] = 0.0
        self.clearance_correction[selected] = 0.0
        self.clearance_distance[selected] = 0.0
        self.safe_approach_index[selected] = len(self.safe_approach_waypoints) if self.safe_approach_start_complete else 1 if len(self.safe_approach_waypoints) > 1 else 0
        self.safe_approach_complete[selected] = self.safe_approach_index[selected] >= len(self.safe_approach_waypoints)
        self.precontact_stage[selected] = 0
        self.contact_duration[selected] = 0.0
        self.contact_memory_left[selected] = 0.0
        self.drive_contact[selected] = False
        self.leg_release_elapsed[selected] = 0.0
        self.leg_release_blend[selected] = 0.0
        self.velocity_integral[selected] = 0.0
        self.precontact_raise_initialized[selected] = False
        self.contact_advance[selected] = 0.0
        self.target_position[selected] = self.robot.data.body_pos_w[selected, self.hand_id]
        self.goal_hold_active[selected] = False
        self.leg_contact_ready[selected] = False
        self.precontact_ready[selected] = self.precontact_posture.numel() == 0 and self.precontact_heights.numel() == 0

    def cartesian_precontact_target(self, contact_target, position, quaternion):
        box = self.env.scene["box"]
        initialize = self.safe_approach_complete & self.body_ready & ~self.precontact_raise_initialized
        self.precontact_raise_position[initialize] = position[initialize]
        self.precontact_raise_initialized |= initialize
        raise_position = torch.where(self.precontact_raise_initialized[:, None], self.precontact_raise_position, position)
        stage = self.precontact_stage.clamp(max=self.precontact_heights.numel() - 1)
        offset = torch.zeros_like(position)
        offset[:, 0] = -self.env.cfg.box_size[0] / 2.0 - self.env.cfg.push_approach_distance
        offset[:, 2] = self.precontact_heights[stage] + getattr(self.env.cfg, "push_hand_height_offset", 0.0)
        target = box.data.root_pos_w + quat_apply(box.data.root_quat_w, offset)
        target[:, :2] = torch.where((stage == 0)[:, None], raise_position[:, :2], target[:, :2])
        settled = torch.linalg.vector_norm(position - target, dim=1) < 0.025
        settled &= self.robot.data.joint_vel[:, self.joint_ids].abs().amax(dim=1) < 0.20
        if self.align_hand_orientation:
            orientation = quat_mul(box.data.root_quat_w, self.hand_rotation)
            angle = 2.0 * torch.acos((quaternion * orientation).sum(dim=1).abs().clamp(max=1.0))
            settled &= (stage < 2) | (angle < 0.15)
        advance = settled & self.safe_approach_complete & self.body_ready & ~self.precontact_ready
        self.precontact_stage += advance.long()
        self.precontact_ready[:] = self.precontact_stage >= self.precontact_heights.numel()
        stage = self.precontact_stage.clamp(max=self.precontact_heights.numel() - 1)
        offset[:, 2] = self.precontact_heights[stage] + getattr(self.env.cfg, "push_hand_height_offset", 0.0)
        target = box.data.root_pos_w + quat_apply(box.data.root_quat_w, offset)
        target[:, :2] = torch.where((stage == 0)[:, None], raise_position[:, :2], target[:, :2])
        can_advance = self.precontact_ready & ~self.locked & ~push_control_at_goal(self.env)
        travel_limit = self.env.cfg.push_approach_distance + self.env.cfg.push_press_depth
        if getattr(self.env.cfg, "push_contact_force_target", None) is not None:
            force = self.env.scene["box_contact_hand"].data.force_matrix_w.sum(dim=(1, 2))
            normal_force = -quat_apply_inverse(box.data.root_quat_w, force)[:, 0]
            self.contact_advance = force_limited_contact_advance(
                self.contact_advance, normal_force, can_advance, dt=self.env.step_dt,
                target_force=self.env.cfg.push_contact_force_target,
                gain=self.env.cfg.push_contact_force_gain,
                speed_limit=self.env.cfg.push_contact_approach_speed, travel_limit=travel_limit,
            )
        else:
            self.contact_advance += can_advance.float() * self.env.step_dt * getattr(self.env.cfg, "push_contact_approach_speed", 0.025)
            self.contact_advance.clamp_(max=travel_limit)
        contact_offset = torch.zeros_like(position)
        contact_offset[:, 0] = -self.env.cfg.box_size[0] / 2.0 - self.env.cfg.push_approach_distance + self.contact_advance
        contact_offset[:, 2] = getattr(self.env.cfg, "push_hand_height_offset", 0.0)
        contact_target = box.data.root_pos_w + quat_apply(box.data.root_quat_w, contact_offset)
        self.env.box_push_approached[:] = self.precontact_ready
        return torch.where(self.precontact_ready[:, None], contact_target, target)

    def apply(self, actions):
        position = self.robot.data.body_pos_w[:, self.hand_id]
        quaternion = self.robot.data.body_quat_w[:, self.hand_id]
        if self.goal_hold_pose:
            eligible = self.safe_approach_complete & self.motion_ready & push_control_at_goal(self.env)
            release_axis = torch.zeros_like(position)
            release_axis[:, 0] = 1.0
            release_axis = quat_apply(self.env.scene["box"].data.root_quat_w, release_axis)
            active, hold_position, hold_quaternion = latch_goal_pose(
                eligible, self.goal_hold_active, self.goal_hold_position, self.goal_hold_quaternion, position, quaternion,
                release_axis=release_axis, release_distance=self.goal_release_distance,
            )
            self.goal_hold_active[:] = active
            self.goal_hold_position[:] = hold_position
            self.goal_hold_quaternion[:] = hold_quaternion
        if self.velocity_integral_gain:
            nominal = nominal_push_velocity_commands(self.env, self.hand_cfg)
            velocity = quat_apply_inverse(yaw_quat(self.robot.data.root_quat_w), self.robot.data.root_lin_vel_w)
            enabled = self.safe_approach_complete & (self.motion_ready | self.full_body_preapproach)
            error = nominal[:, :2] - velocity[:, :2]
            self.velocity_integral[:] = torch.where(
                enabled[:, None],
                (self.velocity_integral + self.env.step_dt * self.velocity_integral_gain * error).clamp(-0.4, 0.4),
                0.0,
            )
        contact = hand_contact(self.env, self.hand_cfg)
        if self.contact_memory_s:
            box = self.env.scene["box"]
            local = quat_apply_inverse(box.data.root_quat_w, position - box.data.root_pos_w)
            height_error = (local[:, 2] - getattr(self.env.cfg, "push_hand_height_offset", 0.0)).abs()
            near_face = ((local[:, 0] + self.env.cfg.box_size[0] / 2.0).abs() < 0.04)
            near_face &= (local[:, 1].abs() < 0.10) & (height_error < 0.06)
            near_face &= self.safe_approach_complete & ~push_control_at_goal(self.env)
            self.contact_memory_left[:], self.drive_contact[:] = retained_push_contact(
                contact, near_face, self.contact_memory_left,
                dt=self.env.step_dt, memory_s=self.contact_memory_s,
            )
            # A verified front-face contact also establishes that approach is complete.
            # The safety classifier and its raw contact forces remain unchanged.
            if hasattr(self.env, "box_push_approached"):
                self.env.box_push_approached |= contact & near_face & (height_error < 0.035)
        target = push_hand_target(self.env)
        if self.precontact_heights.numel():
            target = self.cartesian_precontact_target(target, position, quaternion)
        maximum_reach = getattr(self.env.cfg, "push_target_maximum_reach", 0.0)
        if maximum_reach:
            forward = torch.zeros_like(target)
            forward[:, 0] = 1.0
            forward = quat_apply(yaw_quat(self.robot.data.root_quat_w), forward)
            target = bounded_push_target(target, self.robot.data.root_pos_w, forward, maximum=maximum_reach)
        self.target_position = target
        if self.position_controller is not None:
            self.position_controller.set_command(target, ee_quat=quaternion)
        if self.align_hand_orientation:
            orientation = quat_mul(self.env.scene["box"].data.root_quat_w, self.hand_rotation)
            if self.goal_hold_pose:
                orientation = torch.where(self.goal_hold_active[:, None], self.goal_hold_quaternion, orientation)
            if self.precontact_heights.numel():
                preserve_orientation = (self.precontact_stage < 2) & ~self.precontact_ready
                orientation = torch.where(preserve_orientation[:, None], quaternion, orientation)
            target = torch.cat((target, orientation), dim=1)
        self.controller.set_command(target, ee_quat=quaternion)
        at_goal = push_control_at_goal(self.env)
        if self.precontact_heights.numel():
            self.contact_duration, confirmed_contact = confirmed_push_contact(
                contact, self.precontact_ready & self.safe_approach_complete, at_goal, self.contact_duration,
                dt=self.env.step_dt, hold_time=getattr(self.env.cfg, "push_contact_hold_time", 0.10),
            )
            released = self.locked & ~confirmed_contact
            self.reference[released] = self.robot.data.joint_pos[released][:, self.joint_ids]
            self.locked &= confirmed_contact
            self.motion_ready[:] = confirmed_contact
            contact = confirmed_contact
        if self.lock_arm_on_contact:
            contact_release = self.precontact_ready if self.full_body_preapproach or self.precontact_heights.numel() else torch.ones_like(self.locked)
            newly_locked = contact & contact_release & ~self.locked & ~at_goal
            self.locked_reference[newly_locked] = self.reference[newly_locked]
            command_position = quat_apply_inverse(
                self.robot.data.body_quat_w[:, self.mount_id], position - self.robot.data.body_pos_w[:, self.mount_id],
            )
            self.env.box_push_pose_override[newly_locked, :3] = command_position[newly_locked]
            self.env.box_push_pose_override[newly_locked, 3] = 1.0
            self.locked |= newly_locked
            self.locked &= ~at_goal
            self.motion_ready |= self.locked
        else:
            self.motion_ready |= self.precontact_ready & contact if self.precontact_heights.numel() else self.env.box_push_approached
        jacobian = self.robot.root_physx_view.get_jacobians()[:, self.jacobian_body][:, :, self.jacobian_columns]
        desired = self.controller.compute(position, quaternion, jacobian, self.robot.data.joint_pos[:, self.joint_ids])
        if self.orientation_weight != 1.0 or self.joint_limit_solve:
            position_error, rotation_error = compute_pose_error(
                position, quaternion, target[:, :3], target[:, 3:], rot_error_type="axis_angle",
            )
            joint_position = self.robot.data.joint_pos[:, self.joint_ids]
            if self.joint_limit_solve:
                limits = self.robot.data.soft_joint_pos_limits[:, self.joint_ids]
                scale = pose_task_scale(jacobian, orientation_weight=self.orientation_weight, height_weight=self.height_weight)
                delta = bounded_pose_delta(
                    jacobian * scale[None, :, None], torch.cat((position_error, rotation_error), dim=-1) * scale,
                    limits[..., 0] - joint_position, limits[..., 1] - joint_position,
                )
            else:
                delta = weighted_pose_delta(jacobian, position_error, rotation_error, orientation_weight=self.orientation_weight)
            desired = joint_position + delta
        if self.position_controller is not None:
            position_desired = self.position_controller.compute(
                position, quaternion, jacobian, self.robot.data.joint_pos[:, self.joint_ids],
            )
            position_only = (self.precontact_stage < 2) & ~self.precontact_ready
            desired = torch.where(position_only[:, None], position_desired, desired)
            damped = stabilized_ik_target(
                self.robot.data.joint_pos[:, self.joint_ids], self.robot.data.joint_vel[:, self.joint_ids], desired,
                gain=getattr(self.env.cfg, "push_precontact_ik_gain", 1.0),
                velocity_feedback_time=getattr(self.env.cfg, "push_precontact_velocity_feedback_time", 0.0),
            )
            precontact_active = self.safe_approach_complete & self.body_ready & ~self.locked
            desired = torch.where(precontact_active[:, None], damped, desired)
        limits = self.robot.data.soft_joint_pos_limits[:, self.joint_ids]
        desired = torch.clamp(desired, min=limits[..., 0], max=limits[..., 1])
        active = torch.zeros(self.env.num_envs, dtype=torch.bool, device=self.env.device)
        safe_target = self.reference
        if len(self.safe_approach_waypoints):
            joint_position = self.robot.data.joint_pos[:, self.joint_ids]
            joint_velocity = self.robot.data.joint_vel[:, self.joint_ids]
            active = self.safe_approach_index < len(self.safe_approach_waypoints)
            waypoint_index = torch.clamp(self.safe_approach_index, max=len(self.safe_approach_waypoints) - 1)
            waypoint = self.safe_approach_waypoints[waypoint_index]
            settled = (joint_position - waypoint).abs().amax(dim=1) < self.safe_approach_position_tolerance
            settled &= joint_velocity.abs().amax(dim=1) < self.safe_approach_velocity_tolerance
            self.safe_approach_index = torch.where(active & settled, self.safe_approach_index + 1, self.safe_approach_index)
            waypoint_index = torch.clamp(self.safe_approach_index, max=len(self.safe_approach_waypoints) - 1)
            active = self.safe_approach_index < len(self.safe_approach_waypoints)
            safe_target = self.safe_approach_waypoints[-1] if self.safe_approach_hold else self.safe_approach_waypoints[waypoint_index]
            if not self.full_body_preapproach and not self.precontact_heights.numel():
                self.motion_ready |= ~active & (self.env.box_push_approached | self.legs_active_after_safe_approach)
        self.safe_approach_complete[:] = ~active
        if self.full_body_preapproach or self.precontact_heights.numel():
            if self.full_body_preapproach:
                _, _, body_stable = preapproach_state(self.env)
            else:
                body_stable = (
                    (torch.linalg.vector_norm(self.robot.data.root_lin_vel_w, dim=1) < 0.06)
                    & (torch.linalg.vector_norm(self.robot.data.root_ang_vel_w, dim=1) < 0.20)
                    & (self.robot.data.projected_gravity_b[:, 2] < -0.96)
                )
            body_stable &= self.safe_approach_complete
            self.body_ready_duration[:] = torch.where(
                body_stable,
                self.body_ready_duration + self.env.step_dt,
                torch.zeros_like(self.body_ready_duration),
            )
            self.body_ready |= self.body_ready_duration >= getattr(self.env.cfg, "push_preapproach_hold_time", 0.20)
            self.preapproach_elapsed += (
                self.safe_approach_complete & ~self.body_ready
            ).float() * self.env.step_dt
        if self.precontact_posture.numel():
            joint_position = self.robot.data.joint_pos[:, self.joint_ids]
            self.precontact_ready |= (
                self.safe_approach_complete & self.body_ready
                & ((joint_position - self.precontact_posture).abs().amax(dim=1)
                   < getattr(self.env.cfg, "push_precontact_position_tolerance", 0.04))
            )
            if getattr(self.env.cfg, "push_release_on_hand_contact", False):
                self.precontact_ready |= (
                    self.safe_approach_complete & self.body_ready & hand_contact(self.env, self.hand_cfg)
                )
        if self.full_body_preapproach:
            self.motion_ready |= (
                self.safe_approach_complete & self.precontact_ready
                & (self.env.box_push_approached | self.legs_active_after_safe_approach)
            )
        hold_for_body = (self.full_body_preapproach or bool(self.precontact_heights.numel())) & ~self.body_ready
        move_to_precontact = self.full_body_preapproach & self.body_ready & ~self.precontact_ready
        precontact_target = self.precontact_posture if self.precontact_posture.numel() else desired
        desired = torch.where(
            (active | self.safe_approach_hold | hold_for_body)[:, None], safe_target,
            torch.where(move_to_precontact[:, None], precontact_target, desired),
        )
        arm_max_delta = self.env.step_dt
        if self.full_body_preapproach:
            slow_precontact = self.safe_approach_complete & self.body_ready & ~self.motion_ready
            rate_scale = torch.full_like(
                self.preapproach_elapsed, getattr(self.env.cfg, "push_preapproach_arm_rate_scale", 1.0),
            )
            rate_scale = torch.where(
                move_to_precontact,
                torch.full_like(rate_scale, getattr(self.env.cfg, "push_precontact_arm_rate_scale", 1.0)),
                rate_scale,
            )
            arm_max_delta = torch.where(
                slow_precontact,
                self.env.step_dt * rate_scale,
                torch.full_like(self.preapproach_elapsed, self.env.step_dt),
            )[:, None]
        next_reference = coordinated_joint_target(self.reference, desired, arm_max_delta)
        if self.clearance_minimum is not None:
            arm_positions = self.robot.data.body_pos_w[:, self.clearance_arm_ids]
            protected_positions = self.robot.data.body_pos_w[:, self.clearance_protected_ids]
            separation = arm_positions[:, :, None, :] - protected_positions[:, None, :, :]
            distance = torch.linalg.vector_norm(separation, dim=-1)
            normal = separation / distance[..., None].clamp_min(1.0e-9)
            body_jacobian = self.robot.root_physx_view.get_jacobians()[..., :3, :][..., self.jacobian_columns]
            if self.robot.is_fixed_base:
                body_jacobian = torch.cat((torch.zeros_like(body_jacobian[:, :1]), body_jacobian), dim=1)
            relative_jacobian = (
                body_jacobian[:, self.clearance_arm_ids, None]
                - body_jacobian[:, None, self.clearance_protected_ids]
            )
            gradient = (normal[..., None] * relative_jacobian).sum(dim=-2).flatten(1, 2)
            projected, residual = project_clearance_target(
                next_reference, self.robot.data.joint_pos[:, self.joint_ids], gradient, distance.flatten(1),
                torch.maximum(limits[..., 0], self.reference - arm_max_delta),
                torch.minimum(limits[..., 1], self.reference + arm_max_delta),
                minimum=self.clearance_minimum,
            )
            enabled = self.safe_approach_complete & (not self.safe_approach_hold) & ~hold_for_body
            self.clearance_residual[:] = torch.where(enabled, residual, 0.0)
            self.clearance_correction[:] = torch.where(enabled, (projected - next_reference).abs().amax(dim=1), 0.0)
            self.clearance_distance[:] = distance.flatten(1).amin(dim=1)
            next_reference = torch.where(enabled[:, None], projected, next_reference)
        self.reference = next_reference
        self.reference = torch.where(self.locked[:, None], self.locked_reference, self.reference)
        gravity = self.robot.root_physx_view.get_gravity_compensation_forces()
        columns = self.joint_ids if gravity.shape[1] == self.robot.num_joints else self.jacobian_columns
        compensated = self.reference + gravity[:, columns] / self.stiffness
        result = actions.clone()
        result[:, self.action_slots] = (compensated - self.robot.data.default_joint_pos[:, self.joint_ids]) / self.scale
        if self.full_body_preapproach:
            scale = getattr(self.env.cfg, "push_preapproach_leg_action_scale", 0.25)
            result[:, self.leg_slots] = torch.where(
                self.motion_ready[:, None], result[:, self.leg_slots], scale * result[:, self.leg_slots],
            )
        if self.hold_legs_until_ready:
            if self.leg_release_on_contact:
                self.leg_contact_ready[:] = latch_leg_contact(self.leg_contact_ready, self.safe_approach_complete, contact)
                self.motion_ready &= self.leg_contact_ready
            release_legs = self.motion_ready | self.full_body_preapproach
            if self.body_first:
                release_legs &= self.safe_approach_complete
            result[:, self.leg_slots] = torch.where(release_legs[:, None], result[:, self.leg_slots], 0.0)
            if self.leg_release_ramp_s:
                self.leg_release_elapsed[:] = torch.where(
                    release_legs, self.leg_release_elapsed + self.env.step_dt, 0.0,
                )
                blend = contact_action_blend(
                    self.leg_release_elapsed, hold_time=0.0, ramp_time=self.leg_release_ramp_s,
                )
                if self.leg_contact_ramp_s:
                    self.leg_release_blend[:] = advance_leg_blend(
                        self.leg_release_blend, release_legs,
                        contact & self.safe_approach_complete,
                        dt=self.env.step_dt, ramp_time=self.leg_release_ramp_s,
                        contact_ramp_time=self.leg_contact_ramp_s,
                    )
                    blend = self.leg_release_blend
                result[:, self.leg_slots] *= blend[:, None]
        if self.precontact_heights.numel():
            blend = contact_action_blend(
                self.contact_duration, hold_time=getattr(self.env.cfg, "push_contact_hold_time", 0.10),
                ramp_time=getattr(self.env.cfg, "push_contact_action_ramp_time", 0.50),
            )
            result[:, self.leg_slots] *= blend[:, None]
        return result
