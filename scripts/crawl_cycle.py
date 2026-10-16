"""Experimental continuous flat crawl after the established FL first step.

Internal transitions use measured .2s loaded rest; final four-step rest is1s.
No reset, teleport, longer episode or change to the20cm success predicate.
"""
import torch
from crawl_support import (smooth_fraction, flat_swing_arc, support_shift, triangle_margin,
                           settled_stance, support_acceleration_forces, damped_leg_delta, level_orientation)
from crawl_leg_kinematics import rotate_vector


def transfer_duration(distance):
    """Quintic COM reference bounded by .075m/s and .133m/s²."""
    return torch.maximum(torch.ones_like(distance), torch.maximum(1.875 * distance / .075,
                                                                 (5.774 * distance / .133).sqrt()))


def level_transfer_duration(distance, quaternion):
    """Bound nominal translation and quaternion leveling rates before rest.

    Translation uses the existing .075m/s and .133m/s² budget. Analytic
    normalized-lerp derivative bounds give .2rad/s and .5rad/s² for leveling.
    Actual loaded stability after the trajectory is still separately required.
    """
    goal = level_orientation(quaternion, torch.ones_like(distance))
    angle = 2 * (quaternion * goal).sum(-1).abs().clamp(0, 1).acos()
    first = 4 * (angle / 4).tan()
    second = 4 * (angle / 2).sin() * (1 - (angle / 2).cos()) / (angle / 4).cos().pow(4)
    angular = torch.maximum(1.875 * first / .2, ((3.515625 * second + 5.774 * first) / .5).sqrt())
    return torch.maximum(transfer_duration(distance), angular)


def path_support_shift(point, triangle, advance, desired_margin=.03, max_distance=.14):
    """Plan for both ends of the upcoming COM advance inside a convex triangle.

    The centroid of the path is aimed at the support centroid. The bounded
    result can be infeasible; measured support still controls actual release.
    """
    delta = triangle.mean(dim=1) - advance / 2 - point
    delta *= (max_distance / delta.norm(dim=1).clamp_min(max_distance))[:, None]

    def path_margin(position):
        return torch.minimum(triangle_margin(position, triangle),
                             triangle_margin(position + advance, triangle))

    low, high = torch.zeros_like(point[:, 0]), torch.ones_like(point[:, 0])
    for _ in range(16):
        middle = (low + high) / 2
        sufficient = path_margin(point + middle[:, None] * delta) >= desired_margin
        high = torch.where(sufficient, middle, high)
        low = torch.where(sufficient, low, middle)
    scale = torch.where(path_margin(point) >= desired_margin, 0., high)
    return delta * scale[:, None]


def new_step_completion(ready, started, completed, step_index):
    rows = torch.arange(len(step_index), device=step_index.device)
    return ready & (started[rows, step_index] >= 0) & (completed[rows, step_index] < 0)


def next_support_preparation(point, triangle, advance, next_triangle, margin=.03):
    """Reach the nearest safe boundary facing the next support triangle.

    This targets the next support without crossing either current endpoint's
    inward margin. Actual contact, stability and release gates remain required.
    """
    # Work near the COM rather than at the vectorized world's large offsets.
    triangle = triangle - point[:, None]
    next_triangle = next_triangle - point[:, None]
    point = torch.zeros_like(point)
    edges = triangle.roll(-1, 1) - triangle
    area = edges[:, 0, 0] * edges[:, 1, 1] - edges[:, 0, 1] * edges[:, 1, 0]
    normal = torch.stack((-edges[..., 1], edges[..., 0]), dim=-1)
    normal *= area.sign()[:, None, None] / edges.norm(dim=-1).clamp_min(1e-8)[..., None]
    offset = (normal * triangle).sum(-1) + margin
    offset += (-(normal * advance[:, None]).sum(-1)).clamp_min(0)
    other = normal.roll(-1, 1); other_offset = offset.roll(-1, 1)
    determinant = normal[..., 0] * other[..., 1] - normal[..., 1] * other[..., 0]
    safe = torch.where(determinant.abs() > 1e-8, determinant, torch.ones_like(determinant))
    vertices = torch.stack((offset * other[..., 1] - normal[..., 1] * other_offset,
                            normal[..., 0] * other_offset - offset * other[..., 0]), dim=-1) / safe[..., None]
    # The next centroid identifies the relevant boundary, but is not itself a
    # body target: chasing it also makes a large, unnecessary tangential move.
    next_goal = next_triangle.mean(1) - advance
    boundary = ((normal * next_goal[:, None]).sum(-1) - offset).argmin(1)
    rows = torch.arange(len(point), device=point.device)
    selected_normal, selected_offset = normal[rows, boundary], offset[rows, boundary]
    goal = point + (selected_offset - (selected_normal * point).sum(-1))[:, None] * selected_normal
    projection = goal[:, None] + (offset - (normal * goal[:, None]).sum(-1))[..., None] * normal
    candidates = torch.cat((goal[:, None], projection, vertices), dim=1)
    feasible = ((candidates[:, :, None] * normal[:, None]).sum(-1) >= offset[:, None] - 1e-7).all(-1)
    valid = (area.abs() > 1e-6) & (determinant.abs() > 1e-8).all(1)
    cost = (candidates - goal[:, None]).square().sum(-1).masked_fill(~feasible, float('inf'))
    chosen = candidates[torch.arange(len(point), device=point.device), cost.argmin(1)]
    fallback = point + path_support_shift(point, triangle, advance)
    target = torch.where((valid & feasible.any(1))[:, None], chosen, fallback)
    delta = target - point
    return delta * (.14 / delta.norm(dim=1).clamp_min(.14))[:, None]


class CrawlCycle:
    # After the first FL step: RR, FR, RL. State0 waits;1 shifts/unloads;
    #2 swings;3 searches/reloads;4 holds at completion.
    order = (3, 1, 2)

    def __init__(self, owner):
        self.o = owner
        self.swing_duration = owner.continuous_swing_s
        n, device = owner.env.num_envs, owner.env.device
        z = lambda: torch.zeros(n, device=device)
        self.stage = torch.zeros(n, device=device, dtype=torch.long)
        self.completed = torch.zeros_like(self.stage)
        self.current_index = torch.zeros_like(self.stage)
        self.leg = torch.full_like(self.stage, 3)
        self.timer, self.duration, self.unload, self.release_time = z(), z(), z(), z()
        self.preload_time, self.end_time, self.touch_time = z(), z(), z()
        self.reload, self.probe, self.rest, self.final_rest = z(), z(), z(), z()
        self.advance = torch.full_like(self.timer,owner.step_body_advance_m)
        self.plan_feasible = torch.ones(n,device=device,dtype=torch.bool)
        self.plan_metrics = torch.zeros((n,6),device=device)
        self.plan_inputs = torch.zeros((n,59),device=device)
        self.started_at = torch.full_like(self.timer, -1.)
        self.clearance = torch.zeros(n, device=device, dtype=torch.bool)
        self.midpoint = self.clearance.clone()
        self.verified = self.clearance.clone()
        self.base_start = owner.robot.data.root_pos_w.clone()
        self.base_target = self.base_start.clone()
        self.quat = owner.robot.data.root_quat_w.clone()
        self.feet = owner.robot.data.body_pos_w[:, owner.feet_ids].clone()
        self.foot_target = self.feet.clone()
        self.swing_origin = self.feet[:, 3].clone()
        self.delta = torch.zeros_like(self.base_start)
        self.q_start = owner.robot.data.joint_pos[:, owner.joint_ids].clone()
        self.reference_start = owner.action.reference.clone()
        self.target = owner.action.reference.clone()
        self.margin = z()
        self.planned_path_margin = z()
        self.max_nominal_error = z()
        self.missing_support_s = z()
        self.swing_started = torch.full((n, 3), -1., device=device)
        self.step_completed_at = self.swing_started.clone()
        self.max_height = torch.zeros_like(self.swing_started)
        self.release_gates = torch.zeros((n, 3, 8), device=device)
        self.rows = torch.arange(n, device=device)
        self.all_orders = torch.tensor([[k]+[j for j in range(4) if j != k] for k in range(4)], device=device)

    def state(self):
        return dict(cycle_planned_body_advance_m=self.advance,cycle_plan_feasible=self.plan_feasible,
                    cycle_plan_metrics=self.plan_metrics,cycle_plan_inputs=self.plan_inputs,cycle_stage=self.stage, cycle_tail_steps_completed=self.completed,
                    cycle_tail_step_index=self.current_index,
                    cycle_selected_leg_index=self.leg, cycle_phase_s=self.timer,
                    cycle_transfer_duration_s=self.duration, cycle_unload_s=self.unload,
                    cycle_reload_s=self.reload, cycle_final_rest_s=self.final_rest,
                    cycle_verified_4steps_1s=self.verified, cycle_swing_started_s=self.swing_started,
                    cycle_tail_completed_at_s=self.step_completed_at, cycle_max_height_m=self.max_height,
                    cycle_release_gates=self.release_gates, cycle_margin_m=self.margin,
                    cycle_planned_path_margin_m=self.planned_path_margin,
                    cycle_max_nominal_error_m=self.max_nominal_error,
                    cycle_missing_support_s=self.missing_support_s)

    def compute(self, active, linear_acceleration, angular_acceleration):
        o, dt = self.o, self.o.env.step_dt
        robot, rows = o.robot, self.rows
        now = o.env.episode_length_buf * dt
        feet = robot.data.body_pos_w[:, o.feet_ids]
        contact = o.contacts()
        force = o.env.scene['contact_forces'].data.net_forces_w[:, o.sensor_ids, 2]
        com = o.com()
        quiet = settled_stance(contact, robot.data.root_lin_vel_w, robot.data.root_ang_vel_w,
                               linear_acceleration, angular_acceleration, robot.data.projected_gravity_b[:, 2])
        first_landed = (o.phase == 6)
        if o.overlap_landing_waits:
            first_landed |= (o.phase == 5) & (o.reload_elapsed >= .5)
        begin = active & (self.stage == 0) & first_landed & quiet & (o.next_support_stable >= .2)
        if o.overlap_landing_waits:
            # Reuse the measured loaded rest accumulated during first landing;
            # phase5 must not add another .2s after the same checks passed.
            o.phase[begin] = 6
            o.completed[begin] = True
        # Continue only after measured fully loaded rest; no per-step reset.
        again = (active & (self.stage == 3) & (self.reload >= .5) & quiet & (self.rest >= .2)
                 & (self.completed < 3) & ((feet[rows,self.leg]-self.foot_target[rows,self.leg]).norm(dim=1)<.025))
        begin |= again
        if begin.any():
            self.current_index[begin] = self.completed[begin]
            self.leg[begin] = torch.tensor(self.order, device=feet.device)[self.completed[begin]]
            self.feet[begin] = feet[begin]
            self.base_start[begin] = robot.data.root_pos_w[begin]
            self.quat[begin] = robot.data.root_quat_w[begin]
            self.q_start[begin] = robot.data.joint_pos[:, o.joint_ids][begin]
            self.reference_start[begin] = o.action.reference[begin]
            order = self.all_orders[self.leg]
            triangle = feet.gather(1, order[:, 1:, None].expand(-1, -1, 3))[:, :, :2]
            advance = torch.zeros_like(com[:, :2]); advance[:, 0] = o.step_body_advance_m
            delta = path_support_shift(com[:, :2], triangle, advance)
            planned_margin = torch.minimum(triangle_margin(com[:, :2] + delta, triangle),
                                           triangle_margin(com[:, :2] + delta + advance, triangle))
            self.planned_path_margin[begin] = planned_margin[begin]
            self.delta[begin, :2] = delta[begin]
            self.delta[begin, 2] = 0.
            self.duration[begin] = transfer_duration(delta.norm(dim=1))[begin]
            if o.plan_approach:
                plan = o.make_approach_plan(self.base_start,self.quat,com,feet,self.q_start,self.leg)
                self.advance[begin] = plan['advance'][begin]
                self.delta[begin] = plan['delta'][begin]
                self.duration[begin] = plan['duration'][begin]
                self.planned_path_margin[begin] = plan['support_margin'][begin]
                self.plan_feasible[begin] = plan['feasible'][begin]
                self.plan_metrics[begin] = o.plan_metrics(plan)[begin]
                self.plan_inputs[begin] = plan['inputs'][begin]
            self.started_at[begin] = now[begin]
            for value in (self.timer, self.unload, self.release_time, self.preload_time, self.end_time,
                          self.touch_time, self.reload, self.probe, self.rest):
                value[begin] = 0.
            self.clearance[begin] = False
            self.midpoint[begin] = False
            self.stage[begin] = 1
        order = self.all_orders[self.leg]
        triangle = feet.gather(1, order[:, 1:, None].expand(-1, -1, 3))[:, :, :2]
        self.margin[:] = triangle_margin(com[:, :2], triangle)
        support = contact.gather(1, order[:, 1:]).all(dim=1) & (self.margin >= .015)
        engaged = active & (self.stage > 0)
        self.missing_support_s += (engaged & (self.stage == 2) & ~support) * dt
        shifting = engaged & (self.stage == 1)
        swing = engaged & (self.stage == 2)
        landing = engaged & (self.stage == 3)
        advancing = (shifting & (contact.all(dim=1) | ((self.unload > 0) & support))) | (swing & support)
        self.timer[advancing & ~begin] += dt
        final_base = self.base_start + self.delta
        shift_u = (self.timer / self.duration.clamp_min(1.)).clamp(0., 1.)
        self.base_target[:] = final_base
        self.base_target[shifting] = (self.base_start + self.delta * smooth_fraction(shift_u)[:, None])[shifting]
        preload_ready = (shifting & contact.all(dim=1) & support
                         & ((robot.data.root_pos_w - final_base).norm(dim=1) < .015)
                         & (robot.data.root_lin_vel_w.norm(dim=1) < .05)
                         & (robot.data.root_ang_vel_w.norm(dim=1) < .1)
                         & (linear_acceleration.norm(dim=1) < .5) & (angular_acceleration.norm(dim=1) < 1.)
                         & (robot.data.projected_gravity_b[:, 2] < -.98))
        self.preload_time[:] = torch.where(shifting & (self.unload == 0), torch.where(preload_ready, self.preload_time + dt, 0.), self.preload_time)
        start_unload = shifting & (self.unload == 0) & (self.preload_time >= .1) & self.plan_feasible
        self.swing_origin[start_unload] = feet[rows, self.leg][start_unload]
        unloading = shifting & ((self.unload > 0) | start_unload)
        self.unload[:] = torch.where(unloading, (self.unload + torch.where(support, dt, -dt)).clamp(0., 1.), self.unload)
        released = (shifting & support & (self.timer >= self.duration) & (self.unload >= 1.)
                    & (force[rows, self.leg] <= 5.) & (robot.data.root_lin_vel_w.norm(dim=1) < .05)
                    & (robot.data.root_ang_vel_w.norm(dim=1) < .1))
        self.release_time[:] = torch.where(shifting, torch.where(released, self.release_time + dt, 0.), self.release_time)
        clear = o.approach_foothold_clear(self.swing_origin, o.stride_m)
        o.approach_edge_blocked |= shifting & ~clear
        release = released & (self.release_time >= .1) & clear & self.plan_feasible
        if release.any():
            indices = self.current_index[release]
            self.swing_started[rows[release], indices] = now[release]
            gate = torch.cat((force, self.margin[:, None], robot.data.root_lin_vel_w.norm(dim=1)[:, None],
                              robot.data.root_ang_vel_w.norm(dim=1)[:, None], self.release_time[:, None]), dim=1)
            self.release_gates[rows[release], indices] = gate[release]
            self.stage[release] = 2
            self.timer[release] = 0.
        swing = engaged & (self.stage == 2)
        u = (self.timer / self.swing_duration).clamp(0., 1.)
        self.foot_target[:] = self.feet
        self.foot_target[rows, self.leg] = torch.lerp(self.feet[rows, self.leg], self.swing_origin,
                                                   smooth_fraction(self.unload)[:, None])
        moving_foot = engaged & (self.stage >= 2)
        arc = flat_swing_arc(u, o.stride_m)
        arc[self.stage >= 3] = torch.tensor([o.stride_m, 0., 0.], device=feet.device)
        self.foot_target[rows[moving_foot], self.leg[moving_foot]] = (self.swing_origin + arc)[moving_foot]
        self.base_target[moving_foot, 0] += (self.advance * torch.where(swing, smooth_fraction(u), 1.))[moving_foot]
        height = feet[rows, self.leg, 2] - self.swing_origin[:, 2]
        for index in range(3):
            mask = swing & (self.current_index == index)
            self.max_height[mask, index] = torch.maximum(self.max_height[mask, index], height[mask])
        self.clearance |= swing & ~contact[rows, self.leg] & (height >= .035)
        self.midpoint |= swing & ~contact[rows, self.leg] & (height >= .03) & (feet[rows, self.leg, 0] - self.swing_origin[:, 0] >= .03)
        error = (feet[rows, self.leg] - self.foot_target[rows, self.leg]).norm(dim=1)
        end = swing & support & (self.timer >= self.swing_duration) & self.clearance & self.midpoint & (error < .025)
        self.end_time[:] = torch.where(swing, torch.where(end, self.end_time + dt, 0.), self.end_time)
        landed = end & (self.end_time >= .2)
        self.stage[landed] = 3
        landing = engaged & (self.stage == 3) & ~landed
        searching = landing
        if o.overlap_landing_waits:
            searching = searching | (swing & (self.timer >= self.swing_duration) & self.clearance & self.midpoint)
        probe = searching & support & ~contact[rows, self.leg]
        self.probe[probe] = (self.probe[probe] + dt).clamp(max=1.)
        self.foot_target[rows, self.leg, 2] -= .003 * smooth_fraction(self.probe)
        touch = landing & support & (force[rows, self.leg] > .5)
        self.touch_time[:] = torch.where(landing, torch.where(touch, self.touch_time + dt, 0.), self.touch_time)
        load = touch & (self.touch_time >= .06)
        self.reload[:] = torch.where(landing, (self.reload + torch.where(load, dt, -dt)).clamp(0., .5), self.reload)
        ready = landing & (self.reload >= .5) & quiet & (error < .025)
        self.rest[:] = torch.where(landing, torch.where(ready, self.rest + dt, 0.), self.rest)
        finish = new_step_completion(ready & (self.rest >= .2), self.swing_started,
                                     self.step_completed_at, self.current_index)
        # Defer the next capture to the next frame to keep this frame's force/pose consistent.
        self.step_completed_at[rows[finish], self.current_index[finish]] = now[finish]
        self.completed[finish] += 1
        final_landing = finish & (self.completed == 3)
        self.stage[final_landing] = 4
        # The same measured loaded-rest observations already accumulated for
        # the last landing count toward the final1s hold. Do not count this
        # frame twice; the common update below adds its dt once.
        self.final_rest[final_landing] = (self.rest[final_landing] - dt).clamp_min(0)
        self.final_rest[:] = torch.where(engaged & (self.stage == 4), torch.where(quiet & (error < .025), self.final_rest + dt, 0.), self.final_rest)
        self.verified |= self.final_rest >= 1.
        weight = torch.where(self.stage == 1, smooth_fraction(self.unload), 1 - smooth_fraction(self.reload / .5))
        weight = torch.where(self.stage == 4, 0., weight)
        velocity = self.delta * (30 * shift_u.square() * (1-shift_u).square() / self.duration.clamp_min(1.))[:, None]
        velocity[~shifting | ~advancing] = 0.
        velocity[swing, 0] = (self.advance * 30 * u.square() * (1-u).square() / self.swing_duration)[swing]
        velocity[swing & ~support] = 0.
        com_velocity = (robot.data.body_com_lin_vel_w * o.mass[..., None]).sum(dim=1) / o.mass.sum(dim=1, keepdim=True)
        acceleration = 4 * (velocity[:, :2] - com_velocity[:, :2])
        acceleration *= (.4 / acceleration.norm(dim=1).clamp_min(.4))[:, None]
        vectors = support_acceleration_forces(feet.gather(1, order[:, :, None].expand(-1,-1,3)), com,
                                             o.mass.sum(dim=1)*9.81, weight, acceleration)
        vectors = vectors.gather(1, order.argsort(dim=1)[:, :, None].expand(-1,-1,3))
        nominal = o.kinematics.inverse(rotate_vector(self.quat[:,None], self.foot_target-self.base_target[:,None], inverse=True))
        actual_q = robot.data.root_quat_w
        scalar = (actual_q*self.quat).sum(dim=1)
        rotation_error = 2*scalar.sign()[:,None]*(-self.quat[:,:1]*actual_q[:,1:]+actual_q[:,:1]*self.quat[:,1:]-torch.cross(self.quat[:,1:],actual_q[:,1:],dim=1))
        jacobians = robot.root_physx_view.get_jacobians()
        gravity = robot.root_physx_view.get_gravity_compensation_forces()
        target = o.action.reference.clone()
        for leg in range(4):
            slots = o.slots[leg]; ids = [o.joint_ids[i] for i in slots]
            limits = robot.data.soft_joint_pos_limits[:, ids]
            lower = torch.maximum(self.q_start[:,slots]-.7, limits[:,:,0]);upper=torch.minimum(self.q_start[:,slots]+.7,limits[:,:,1])
            nominal[:,leg] = torch.maximum(torch.minimum(nominal[:,leg],upper),lower)
            relative = feet[:,leg]-robot.data.root_pos_w
            body_error = -(self.base_target-robot.data.root_pos_w).clamp(-.10,.10)-torch.cross(rotation_error,relative,dim=1)
            body_error += .1*(robot.data.root_lin_vel_w+torch.cross(robot.data.root_ang_vel_w,relative,dim=1))
            correction = .25*body_error
            swing_error = .5*(self.foot_target[:,leg]-feet[:,leg])
            blend = torch.where(self.leg==leg, weight, 0.)
            correction = torch.lerp(correction,swing_error,blend[:,None])
            jac = jacobians[:,o.bodies[leg],:3][:,:,o.columns[leg]]
            columns = ids if gravity.shape[1]==robot.num_joints else o.columns[leg]
            torque = gravity[:,columns]-(jac.transpose(1,2)@vectors[:,leg,:,None]).squeeze(-1)
            limit = .75*robot.data.joint_effort_limits[:,ids]
            torque = torque.clamp(-limit,limit)
            target[:,slots] = nominal[:,leg]+damped_leg_delta(jac,correction.clamp(-.08,.08)).clamp(-.4,.4)+torque/30.
            o.feedforward_torque[:,slots] = torch.where(engaged[:,None],torque,o.feedforward_torque[:,slots])
        foot_error = (rotate_vector(self.quat[:,None],o.kinematics.forward(nominal))+self.base_target[:,None]-self.foot_target).norm(dim=2)
        residual = foot_error.amax(dim=1)
        self.max_nominal_error[engaged] = torch.maximum(self.max_nominal_error[engaged],residual[engaged])
        target = torch.lerp(self.reference_start,target,smooth_fraction((now-self.started_at)/.5)[:,None])
        self.target[engaged] = target[engaged]
        o.foot_target[engaged] = self.foot_target[engaged]
        o.base_target[engaged] = self.base_target[engaged]
        o.command_target[engaged] = target[engaged]
        o.nominal_leg_reference[engaged] = nominal[engaged]
        o.nominal_foot_error[engaged] = foot_error[engaged]
        o.max_nominal_foot_error[engaged] = torch.maximum(o.max_nominal_foot_error[engaged],foot_error[engaged])
        o.margin[engaged] = self.margin[engaged]
        o.quat_target[engaged] = self.quat[engaged]
        o.support_moment_residual[engaged] = torch.cross(feet-com[:,None],vectors,dim=2).sum(dim=1)[engaged]
        o.support_force_vector[engaged] = vectors[engaged]
        o.support_force[engaged] = vectors[engaged,:,2]
        normalized = (target-robot.data.default_joint_pos[:,o.joint_ids])/o.action.cfg.scale
        normalized[:,12:] = 0.
        return engaged, normalized
