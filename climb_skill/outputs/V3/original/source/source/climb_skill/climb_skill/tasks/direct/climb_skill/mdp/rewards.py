"""登箱奖励及动作平滑、碰撞惩罚。"""

import torch
from isaaclab.utils.math import euler_xyz_from_quat, quat_from_euler_xyz
from ..task_parameters import FOOT_NAMES, HISTORY, JOINT_NAMES, PROPRIO
from .geometry import forward_tracking_rewards


def get_rewards(env):
    cfg = env.task
    pos, yaw, feet, forces, support, delta, distance, command, heading = env.state
    data = env.robot.data
    direction = delta / distance.clamp_min(1e-5)[:, None]
    forward = (data.root_lin_vel_w[:, :2] * direction).sum(-1)
    goal_velocity, heading_reward = forward_tracking_rewards(forward, command, heading)
    torque = data.applied_torque[:, env.joint_ids]
    q = data.joint_pos[:, env.joint_ids]
    limits = data.soft_joint_pos_limits[:, env.joint_ids]
    edge_dist = torch.minimum((feet[..., 0] - cfg.box_front).abs(),
                              (feet[..., 0] - cfg.box_front - cfg.box_length).abs())
    edge_dist = torch.minimum(edge_dist, (feet[..., 1].abs() - cfg.box_width / 2).abs())
    # 普通接触使用竖直力>2N；新步态传感器计时使用默认力模长>1N，台面承重另用竖直力>=8N。
    contacts = forces[..., 2] > 2.
    limit_violation = (limits[..., 0] - q).clamp_min(0.) + (q - limits[..., 1]).clamp_min(0.)
    # 这里构造未乘权重的原始项；下面按条件追加成本，最后统一乘控制周期dt。
    env.reward_terms = {
        "goal_velocity": goal_velocity,
        "heading": heading_reward,
        "progress": ((env.previous_distance - distance) / env.step_dt).clamp(-1., 1.),
        "lin_vel_z": data.root_lin_vel_b[:, 2].square(),
        "ang_vel_xy": data.root_ang_vel_b[:, :2].square().sum(-1),
        "orientation": data.projected_gravity_b[:, :2].square().sum(-1),
        "joint_acceleration": data.joint_acc[:, env.joint_ids].square().sum(-1),
        "collision": (env.contact.data.net_forces_w[:, env.nonfeet].norm(dim=-1) > 1.).float().sum(-1),
        "action_rate": (env.actions - env.previous_actions).norm(dim=-1),
        "delta_torques": (torque - env.previous_torques).square().sum(-1),
        "torques": torque.square().sum(-1),
        "hip_position": (q[:, [0, 3, 6, 9]] - env.reference[:, [0, 3, 6, 9]]).square().sum(-1),
        "joint_error": (q[:, :12] - env.reference[:, :12]).square().sum(-1),
        "feet_stumble": (forces[..., :2].norm(dim=-1) > 4 * forces[..., 2].abs().clamp_min(1.)).any(-1).float(),
        "feet_edge": ((edge_dist < 0.05) & contacts & (feet[..., 2] > env.heights[:, None] - 0.02)).float().sum(-1),
        "flight": (~contacts.any(-1)).float(),
        "arm_error": (q[:, 12:] - env.reference[:, 12:]).square().sum(-1),
        "joint_limits": limit_violation[:, :12].sum(-1),
    }
    weights = cfg.rewards
    if cfg.startup_stand_seconds > 0:
        from .startup import movement_gain
        gain = movement_gain(env)
        for name in ("goal_velocity", "heading", "progress"):
            env.reward_terms[name] *= gain
    flat_gate = None
    speed_gate = None
    # 平面稳定／软限速gate与后面的步态几何mask不同：此gate要求至少两足实际承重。
    if any(w > 0 for w in (cfg.flat_stability_weight, cfg.flat_speed_weight,
                          cfg.flat_angular_velocity_weight, cfg.flat_slip_weight)):
        from .flat_stability import flat_posture_cost, flat_surface_gate, flat_speed_terms, flat_motion_costs
        weights = dict(cfg.rewards)
        if cfg.flat_stability_weight > 0:
            env.reward_terms["flat_posture"], flat_gate = flat_posture_cost(
                feet, forces, data.projected_gravity_b, env.heights, cfg, pos[:, :2])
            weights["flat_posture"] = -cfg.flat_stability_weight
        else:
            flat_gate = flat_surface_gate(feet, forces, env.heights, cfg, pos[:, :2])
        if cfg.flat_speed_weight > 0:
            speed_gate = flat_gate
            if cfg.walking_refinement_enabled:
                from .walking_refinement import settled_flat_mask
                # 平面腾空不再关闭超速成本和进度封顶；姿态/滑移仍用原承重gate。
                speed_gate = settled_flat_mask(pos, feet, env.heights, env.ever_top_support, cfg)
                if cfg.amp_body_gate:
                    from .amp import body_plane_gate
                    # 新候选与风格学习共用名义覆盖面：某脚拖到身后不能顺带关掉平地限速。
                    speed_gate = body_plane_gate(pos, env.heights, cfg)
            env.reward_terms["flat_overspeed"], env.reward_terms["progress"] = flat_speed_terms(
                data.root_lin_vel_w[:, :2].norm(dim=-1), env.reward_terms["progress"], speed_gate, cfg)
            weights["flat_overspeed"] = -cfg.flat_speed_weight
        if cfg.flat_angular_velocity_weight > 0 or cfg.flat_slip_weight > 0:
            angular, slip = flat_motion_costs(feet, forces, data.body_lin_vel_w[:, env.foot_ids],
                data.root_ang_vel_b, env.heights, flat_gate, cfg)
            env.reward_terms["flat_angular_velocity"] = angular
            env.reward_terms["flat_loaded_slip"] = slip
            weights["flat_angular_velocity"] = -cfg.flat_angular_velocity_weight
            weights["flat_loaded_slip"] = -cfg.flat_slip_weight
    if any(w > 0 for w in (cfg.forward_heading_weight, cfg.target_curvature_weight, cfg.contact_slip_weight)):
        from .gait_quality import target_curvature, contact_slip
        from .startup import movement_gain
        weights = dict(weights)
        gain = movement_gain(env)
        env.reward_terms["forward_heading_error"] = gain * (1. - yaw.cos())
        env.reward_terms["target_curvature"] = target_curvature(
            env.targets, env.previous_targets, env.previous_previous_targets)
        env.reward_terms["contact_slip"] = gain * contact_slip(
            feet, forces, data.body_lin_vel_w[:, env.foot_ids], env.heights, cfg)
        weights.update(forward_heading_error=-cfg.forward_heading_weight,
                       target_curvature=-cfg.target_curvature_weight, contact_slip=-cfg.contact_slip_weight)
    walk_mask = None
    if cfg.flat_walking_enabled or cfg.straight_tracking_enabled:
        from .flat_walking import (flat_walking_mask, flat_walking_costs,
                                   flat_velocity_tracking, straight_tracking_costs, walking_quality_curriculum)
        from .startup import movement_gain
        weights = dict(weights)
        gain = movement_gain(env)
        if cfg.flat_walking_enabled:
            walk_mask = flat_walking_mask(pos, feet, env.heights, cfg)
            walk_mask = walking_quality_curriculum(walk_mask, env.heights, cfg)
            sensor = env.contact.data
            walk_terms = flat_walking_costs(walk_mask, forces, data.root_lin_vel_w[:,2],
                q-env.reference, sensor.last_air_time[:,env.contact_feet],
                sensor.last_contact_time[:,env.contact_feet], sensor.current_air_time[:,env.contact_feet])
            env.reward_terms.update({k:gain*v for k,v in walk_terms.items()})
            weights.update(flat_walk_flight=-cfg.flat_walk_flight_weight,
                flat_walk_vertical=-cfg.flat_walk_vertical_weight,
                flat_walk_air_variance=-cfg.flat_walk_air_variance_weight,
                flat_walk_long_air=-cfg.flat_walk_long_air_weight,
                flat_walk_mirror=-cfg.flat_walk_mirror_weight)
            if cfg.flat_walk_velocity_tracking:
                tracking = flat_velocity_tracking(data.root_lin_vel_w[:,:2], command)
                env.reward_terms['goal_velocity'] = ((1.-walk_mask)*env.reward_terms['goal_velocity']
                                                    + walk_mask*gain*tracking)
        if cfg.straight_tracking_enabled:
            env.reward_terms.update({k:gain*v for k,v in straight_tracking_costs(
                pos,yaw,data.root_lin_vel_w[:,1],data.root_ang_vel_b[:,2]).items()})
            weights.update(straight_heading=-cfg.straight_heading_weight,
                straight_path=-cfg.straight_path_weight,
                straight_lateral_velocity=-cfg.straight_lateral_velocity_weight,
                straight_yaw_rate=-cfg.straight_yaw_rate_weight)
    # 新对角步态只新增软成本；不会重写策略动作、触发IK或禁止某条腿抬起。
    diagonal_mask = None
    if cfg.diagonal_gait_enabled:
        from .diagonal_gait import diagonal_walking_mask, diagonal_gait_costs
        from .startup import movement_gain
        diagonal_mask = diagonal_walking_mask(pos, feet, env.heights, env.ever_top_support, cfg)
        sensor = env.contact.data
        terms = diagonal_gait_costs(diagonal_mask,
            sensor.current_air_time[:, env.contact_feet],
            sensor.current_contact_time[:, env.contact_feet], cfg)
        # Apply fully only after the startup policy ramp, so settling has no gait cost.
        gait_gain = (movement_gain(env) >= 1.).float()
        env.reward_terms.update({k:gait_gain*v for k,v in terms.items()})
        weights = dict(weights)
        weights.update(diagonal_pair=-cfg.diagonal_pair_weight,
                       diagonal_sync=-cfg.diagonal_sync_weight,
                       diagonal_duration=-cfg.diagonal_duration_weight)
        if cfg.walking_refinement_enabled:
            from .walking_refinement import swing_clearance_cost
            env.reward_terms['walking_clearance'] = gait_gain * swing_clearance_cost(
                diagonal_mask, feet, env.heights, sensor.current_air_time[:, env.contact_feet], cfg)
            weights['walking_clearance'] = -cfg.walking_clearance_weight
    if cfg.path_deviation_weight > 0:
        from .flat_walking import path_deviation_cost
        from .startup import movement_gain
        weights = dict(weights)
        env.reward_terms['path_deviation'] = movement_gain(env)*path_deviation_cost(pos)
        weights['path_deviation'] = -cfg.path_deviation_weight
    # 密集回报乘dt=0.02；成功+20、失败-10不乘dt。负回报保留，不做非负截断。
    reward = sum(weights[k] * v for k, v in env.reward_terms.items()) * env.step_dt
    if cfg.approach_quality_enabled:
        reward -= cfg.front_clearance_weight * env.approach_quality.clearance * env.step_dt
        reward += cfg.front_landing_bonus * env.approach_quality.new_landing.sum(-1)
    if cfg.crossing_quality_enabled:
        crossing = env.approach_quality
        reward -= (cfg.crossing_guidance_weight * crossing.guidance
                   + cfg.crossing_reference_weight * crossing.mixed_cost) * env.step_dt
        reward -= cfg.crossing_failure_penalty * crossing.new_failure.sum(-1)
    # Unlike the running task, retain negative failures and use explicit terminal success.
    reward += cfg.success_bonus * env.success.float() + cfg.failure_penalty * env.failure.float()
    env.previous_distance.copy_(distance)
    env.previous_torques.copy_(torque)
    # The held arm pose lies on some hard limits; leg learning must not pay an
    # unavoidable arm soft-limit penalty. Arm tracking/failure checks remain separate.
    efforts = data.joint_effort_limits[:, env.joint_ids[:12]].clamp_min(1e-6)
    # 日志中的reward/*已经是加权且乘dt后的均值；不能再乘一次权重。
    env.extras["diagnostics"] = {
        "task/root_x": pos[:, 0].mean(),
        "task/forward_speed": data.root_lin_vel_w[:, 0].mean(),
        "task/forward_heading_error_rad": torch.atan2(yaw.sin(), yaw.cos()).abs().mean(),
        "task/top_supported_feet": support.float().sum(-1).mean(),
        "task/recent_top_feet": (env.top_contact_age <= cfg.top_contact_memory).float().sum(-1).mean(),
        "task/rear_top_supported": support[:, 2:].float().sum(-1).mean(),
        "task/traversal_hold_seconds": env.hold.mean(),
        "control/leg_saturation_fraction": (data.computed_torque[:, env.joint_ids[:12]].abs() >= .99 * efforts).float().mean(),
        "control/leg_tracking_error_rad": (env.targets[:, :12] - q[:, :12]).abs().mean(),
        "control/arm_tracking_error_rad": (q[:, 12:] - env.reference[:, 12:]).abs().mean(),
        "control/arm_gravity_feedforward_Nm": env.arm_gravity_torque.abs().mean(),
        "control/arm_saturation_fraction": (data.computed_torque[:, env.joint_ids[12:]].abs()
            >= .99 * data.joint_effort_limits[:, env.joint_ids[12:]]).float().mean(),
        **{f"joint_limit/{name}": limit_violation[:, i].mean() for i, name in enumerate(JOINT_NAMES[:12])},
        **{f"reward/{k}": weights[k] * v.mean() * env.step_dt for k, v in env.reward_terms.items()},
    }
    if flat_gate is not None:
        env.extras["diagnostics"]["stability/flat_gate"] = flat_gate.mean()
    if cfg.walking_refinement_enabled:
        from .walking_refinement import settled_flat_mask
        geometry = settled_flat_mask(pos, feet, env.heights, env.ever_top_support, cfg) * gait_gain
        denominator = geometry.sum().clamp_min(1.)
        air = env.contact.data.current_air_time[:, env.contact_feet]
        loaded = (forces[..., 2] >= cfg.support_force).float()
        env.extras['diagnostics'].update({
            'gait/refinement_geometry_fraction': geometry.mean(),
            'gait/rear_pair_air_fraction': (geometry*(air[:,2:] > cfg.walking_pair_grace_seconds).all(-1)).sum()/denominator,
            'gait/front_pair_air_fraction': (geometry*(air[:,:2] > cfg.walking_pair_grace_seconds).all(-1)).sum()/denominator,
            'gait/flat_forward_speed': (geometry*data.root_lin_vel_w[:,0]).sum()/denominator,
            **{f'gait/{name}_loaded_fraction': (geometry*loaded[:,i]).sum()/denominator
               for i,name in enumerate(('FL','FR','RL','RR'))},
        })
        if speed_gate is not None:
            env.extras['diagnostics']['speed/geometry_gate_fraction'] = speed_gate.mean()
    if cfg.amp_body_gate:
        from .amp import body_plane_gate
        geometry = body_plane_gate(pos, env.heights, cfg) * (gait_gain > 0).float()
        denominator = geometry.sum().clamp_min(1.)
        qd_legs = data.joint_vel[:, env.joint_ids[:12]].reshape(-1, 4, 3)
        power = (torque[:, :12].reshape(-1, 4, 3) * qd_legs).sum(-1)
        for i, leg in enumerate(('FL', 'FR', 'RL', 'RR')):
            env.extras['diagnostics'].update({
                f'leg/{leg}_thigh_rad': (geometry*q[:,3*i+1]).sum()/denominator,
                f'leg/{leg}_calf_rad': (geometry*q[:,3*i+2]).sum()/denominator,
                f'leg/{leg}_velocity_rms': (geometry*qd_legs[:,i].square().mean(-1)).sum().div(denominator).sqrt(),
                f'leg/{leg}_positive_joint_power_W': (geometry*power[:,i].clamp_min(0)).sum()/denominator,
            })
    if diagonal_mask is not None:
        active = diagonal_mask * gait_gain
        denominator = active.sum().clamp_min(1.)
        env.extras["diagnostics"]["gait/diagonal_active_fraction"] = active.mean()
        for key in ("diagonal_pair", "diagonal_sync", "diagonal_duration"):
            env.extras["diagnostics"][f"gait/{key}_cost_active"] = env.reward_terms[key].sum()/denominator
    if walk_mask is not None:
        walking_samples = walk_mask * (gain >= 1.)
        env.extras["diagnostics"]["gait/flat_geometry_fraction"] = walk_mask.mean()
        env.extras["diagnostics"]["gait/flat_flight_fraction"] = (
            walking_samples*(forces[...,2]<=2.).all(-1)).sum()/walking_samples.sum().clamp_min(1.)
        env.extras["diagnostics"]["gait/flat_vertical_speed_abs"] = (
            walking_samples*data.root_lin_vel_w[:,2].abs()).sum()/walking_samples.sum().clamp_min(1.)
    env.extras["diagnostics"]["task/lateral_error_m"] = pos[:,1].abs().mean()
    if cfg.startup_stand_seconds > 0:
        env.extras["diagnostics"]["startup/ready_fraction"] = env.startup_ready.float().mean()
    if cfg.approach_quality_enabled:
        env.extras['diagnostics'].update({
            'approach/front_clearance_cost': env.approach_quality.clearance.mean(),
            'approach/front_retry_count': env.approach_quality.retries.float().sum(-1).mean(),
            'curriculum/gait_ready_fraction': env.approach_quality.passed().float().mean(),
        })
    env.episode_return += reward
    for record in env.extras["episode_records"]:
        record["return"] = float(env.episode_return[record["env"]])
    return reward

