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
        if self.goal_hold_height_margin:
            box = self.env.scene["box"]
            local = quat_apply_inverse(box.data.root_quat_w, hold_position - box.data.root_pos_w)
            local[:, 2] = local[:, 2].clamp(max=self.env.cfg.box_size[2] / 2.0 - self.goal_hold_height_margin)
            hold_position = box.data.root_pos_w + quat_apply(box.data.root_quat_w, local)
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
    if self.approach_height_gate:
        box = self.env.scene["box"]
        local = quat_apply_inverse(box.data.root_quat_w, position - box.data.root_pos_w)
        retreat = self.env.cfg.box_size[0] / 2.0 + 0.06
        height = getattr(self.env.cfg, "push_hand_height_offset", 0.0)
        aligned = ((local[:, 0] + retreat).abs() < 0.05) & (local[:, 1].abs() < 0.08)
        aligned &= (local[:, 2] - height).abs() < 0.045
        self.debug_gate_geometric_ready[:] = aligned.float()
        self.debug_gate_velocity_ready[:] = (self.robot.data.joint_vel[:, self.joint_ids].abs().amax(dim=1) < 0.25).float()
        aligned &= self.robot.data.joint_vel[:, self.joint_ids].abs().amax(dim=1) < 0.25
        active = self.safe_approach_complete & ~self.approach_height_aligned
        self.approach_height_duration[:] = torch.where(
            active & aligned, self.approach_height_duration + self.env.step_dt,
            torch.where(active, torch.zeros_like(self.approach_height_duration), self.approach_height_duration),
        )
        self.approach_height_aligned |= self.approach_height_duration >= 0.10
        height_ok = (local[:, 2] - height).abs() < 0.035
        self.approach_gate_advance += (
            self.safe_approach_complete & self.approach_height_aligned
            & ~self.approach_face_ready & height_ok
        ).float() * self.env.step_dt * 0.10
        self.approach_gate_advance.clamp_(max=0.03)
        gate_offset = torch.zeros_like(position)
        gate_offset[:, 0] = -retreat + self.approach_gate_advance
        gate_offset[:, 2] = height
        gate_target = box.data.root_pos_w + quat_apply(box.data.root_quat_w, gate_offset)
        face_aligned = self.approach_gate_advance >= 0.03 - 1.0e-5
        face_aligned &= (local[:, 0] - gate_offset[:, 0]).abs() < 0.035
        face_aligned &= (local[:, 1].abs() < 0.06) & height_ok
        face_aligned &= self.robot.data.joint_vel[:, self.joint_ids].abs().amax(dim=1) < 0.25
        # Real front-face contact may arrive before the geometric waypoint settles.
        # Require the same 100ms continuous confirmation and original contact classifier.
        contact_aligned = contact & height_ok & (local[:, 1].abs() < 0.06)
        face_aligned |= contact_aligned
        self.approach_face_duration[:] = torch.where(
            self.safe_approach_complete & face_aligned,
            self.approach_face_duration + self.env.step_dt,
            torch.zeros_like(self.approach_face_duration),
        )
        self.approach_face_ready |= self.approach_face_duration >= 0.10
        self.env.box_push_approached &= self.approach_face_ready
        target = torch.where((self.safe_approach_complete & ~self.approach_face_ready)[:, None], gate_target, target)
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
        if self.approach_height_gate:
            phase = (self.approach_gate_advance / 0.03).clamp(0.0, 1.0)
            entry_pitch = 1.5 + (self.entry_exit_pitch - 1.5) * phase
            entry_active = self.safe_approach_complete & ~self.approach_face_ready
            self.approach_pitch_reference[:] = torch.where(entry_active, entry_pitch, self.entry_exit_pitch)
            zeros = torch.zeros_like(entry_pitch)
            entry_orientation = quat_mul(self.env.scene["box"].data.root_quat_w,
                                         quat_from_euler_xyz(zeros, entry_pitch, zeros))
            orientation = torch.where(entry_active[:, None], entry_orientation, orientation)
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
        ready = self.precontact_ready & contact if self.precontact_heights.numel() else self.env.box_push_approached
        if self.approach_height_gate:
            ready &= self.approach_face_ready
        self.motion_ready |= ready
    jacobian = self.robot.root_physx_view.get_jacobians()[:, self.jacobian_body][:, :, self.jacobian_columns]
    desired = self.controller.compute(position, quaternion, jacobian, self.robot.data.joint_pos[:, self.joint_ids])
    if self.orientation_weight != 1.0 or self.joint_limit_solve:
        position_error, rotation_error = compute_pose_error(
            position, quaternion, target[:, :3], target[:, 3:], rot_error_type="axis_angle",
        )
        self.debug_pose_position_error[:] = position_error
        self.debug_pose_rotation_error[:] = rotation_error
        joint_position = self.robot.data.joint_pos[:, self.joint_ids]
        if self.joint_limit_solve:
            limits = self.robot.data.soft_joint_pos_limits[:, self.joint_ids]
            if self.joint4_floor is not None:
                limits = limits.clone()
                limits[:, 3, 0] = torch.where(
                    self.safe_approach_complete,
                    limits[:, 3, 0].clamp_min(self.joint4_floor), limits[:, 3, 0],
                )
            scale = pose_task_scale(jacobian, orientation_weight=self.orientation_weight, height_weight=self.height_weight)
            # Prioritize Cartesian alignment while the gated approach is active.
            # Restore the original pose objective before loaded pushing.
            entry_active = self.safe_approach_complete & ~self.approach_face_ready
            task_scale = scale[None, :].expand(self.env.num_envs, -1).clone()
            if self.approach_height_gate:
                task_scale[:, 3:] = torch.where(
                    entry_active[:, None], torch.full_like(task_scale[:, 3:], 0.1), task_scale[:, 3:],
                )
            task_jacobian = jacobian * task_scale[:, :, None]
            task_error = torch.cat((position_error, rotation_error), dim=-1) * task_scale
            if self.geometry_shield is not None and self.approach_height_gate:
                gradient, residual = self.geometry_shield.linearized_margin(
                    joint_position.detach().cpu().numpy(), (self.safe_approach_complete & ~self.goal_hold_active).detach().cpu().numpy(), 0.055,
                )
                gradient = torch.as_tensor(gradient, dtype=jacobian.dtype, device=jacobian.device)
                residual = torch.as_tensor(residual, dtype=jacobian.dtype, device=jacobian.device)
                task_jacobian = torch.cat((task_jacobian, 10.0 * gradient[:, None, :]), dim=1)
                task_error = torch.cat((task_error, 10.0 * residual[:, None]), dim=1)
            delta = bounded_pose_delta(
                task_jacobian, task_error,
                limits[..., 0] - joint_position, limits[..., 1] - joint_position,
            )
        else:
            delta = weighted_pose_delta(jacobian, position_error, rotation_error, orientation_weight=self.orientation_weight)
        desired = joint_position + delta
        self.debug_pose_desired[:] = desired
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
    if self.joint4_floor is not None:
        limits = limits.clone()
        limits[:, 3, 0] = torch.where(
            self.safe_approach_complete,
            limits[:, 3, 0].clamp_min(self.joint4_floor), limits[:, 3, 0],
        )
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
            ready = self.env.box_push_approached | self.legs_active_after_safe_approach
            if self.approach_height_gate:
                ready &= self.approach_face_ready
            self.motion_ready |= ~active & ready
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
    # Experimental startup blend; no reset-state changes or safety grace period.
    startup_u = ((self.env.episode_length_buf - getattr(self.env, 'box_push_activation_step', 0)).float() * self.env.step_dt / 1.0).clamp(0.0, 1.0)
    startup_blend = startup_u.square() * (3.0 - 2.0 * startup_u)
    # Learned residual precedes joint limits, reference rate limits and both shields.
    residual = getattr(self.env, "box_push_arm_residual", None)
    if residual is not None:
        # Keep waypoint correction below the existing measured arrival tolerance.
        # Full learned residual resumes after measured face readiness; subsequent
        # joint reference smoothing and all geometry/contact gates still apply.
        waypoint_residual = residual.clamp(-0.5 * self.safe_approach_position_tolerance,
                                           0.5 * self.safe_approach_position_tolerance)
        residual = torch.where(self.approach_face_ready[:, None], residual, waypoint_residual)
        residual_active = ~self.goal_hold_active & ~self.locked
        desired = torch.where(residual_active[:, None], desired + startup_blend[:, None] * residual, desired)
        desired = torch.maximum(torch.minimum(desired, limits[..., 1]), limits[..., 0])
    entry_slow = self.safe_approach_complete & ~self.approach_face_ready
    arm_max_delta = torch.where(entry_slow, 0.25 * self.env.step_dt, self.env.step_dt)[:, None]
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
    speed_scale = getattr(self.env, 'box_push_arm_speed_scale', torch.ones(self.env.num_envs, device=self.env.device))
    speed_scale = 0.2 + startup_blend * (speed_scale - 0.2)
    arm_max_delta = arm_max_delta * speed_scale[:, None]
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
    self.debug_reference_pre_geometry[:] = next_reference
    self.debug_arm_velocity[:] = self.robot.data.joint_vel[:, self.joint_ids]
    if self.geometry_shield is not None:
        lower = torch.maximum(limits[..., 0], self.reference - arm_max_delta)
        upper = torch.minimum(limits[..., 1], self.reference + arm_max_delta)
        geometry_active = ~self.locked  # v202: intervene during approach, not observation only
        shielded, measured, blocked = self.geometry_shield.project(
            self.robot.data.joint_pos[:, self.joint_ids].detach().cpu().numpy(),
            self.robot.data.joint_vel[:, self.joint_ids].detach().cpu().numpy(),
            next_reference.detach().cpu().numpy(),
            lower.detach().cpu().numpy(), upper.detach().cpu().numpy(),
            geometry_active.detach().cpu().numpy(),
        )
        next_reference = torch.as_tensor(shielded, dtype=next_reference.dtype, device=next_reference.device)
        observed = torch.as_tensor(measured, dtype=next_reference.dtype, device=next_reference.device)
        self.geometry_clearance[:] = observed
        self.geometry_blocked[:] = torch.as_tensor(blocked, device=next_reference.device)
        self.geometry_minimum_observed[:] = torch.where(
            self.geometry_observed_steps == 0, observed,
            torch.minimum(self.geometry_minimum_observed, observed),
        )
        self.geometry_observed_steps += 1
        self.geometry_below_minimum_steps += (
            observed < self.geometry_shield.minimum
        ).long()
    self.debug_reference_post_geometry[:] = next_reference
    if self.geometry_shield is not None:
        self.debug_predicted_clearance[:] = torch.as_tensor(self.geometry_shield.last_predicted_clearance, dtype=next_reference.dtype, device=next_reference.device)
    self.reference = next_reference
    self.reference = torch.where(self.locked[:, None], self.locked_reference, self.reference)
    gravity = self.robot.root_physx_view.get_gravity_compensation_forces()
    columns = self.joint_ids if gravity.shape[1] == self.robot.num_joints else self.jacobian_columns
    compensated = self.reference + gravity[:, columns] / self.stiffness
    # Bound the final PD position command, including gravity compensation.
    # Reset starts from the measured native reset pose; actuator/PD/delays unchanged.
    compensated = self.last_compensated_reference + (compensated - self.last_compensated_reference) * (self.env.step_dt / (0.06 + self.env.step_dt))
    self.last_compensated_reference[:] = compensated

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
