"""Confirm real four-foot ascent while walking forward, with failure/timeout checks."""

import math
import torch
from isaaclab.utils.math import euler_xyz_from_quat, quat_from_euler_xyz
from ..task_parameters import FOOT_NAMES, HISTORY, JOINT_NAMES, PROPRIO
from .geometry import stable_timer, update_top_contact_age, platform_ascent_geometry, ascent_confirmation


def get_dones(env):
    cfg = env.task
    pos, yaw, feet, forces, support, delta, distance, command, heading = env._kinematics()
    from .startup import update_startup
    startup_failed = update_startup(env, feet, forces)
    # Refresh ramped command after advancing the phase clock.
    if cfg.startup_stand_seconds > 0:
        from .startup import movement_gain
        command = torch.full_like(distance, cfg.approach_speed) * movement_gain(env)
    env.state = (pos, yaw, feet, forces, support, delta, distance, command, heading)
    tilt = torch.acos((-env.robot.data.projected_gravity_b[:, 2]).clamp(-1., 1.))
    arm_error = (env.robot.data.joint_pos[:, env.joint_ids[12:]] - env.reference[:, 12:]).abs().amax(-1)
    # 4帧5ms接触历史检查机身／臂碰撞，避免漏过两个策略步之间的短碰撞。腿触碰只在奖励中处理。
    history_forces = env.contact.data.net_forces_w_history.norm(dim=-1).amax(dim=1)
    forbidden_contact = history_forces[:, env.forbidden].amax(-1) > cfg.contact_failure_force
    env.arm_bad_time = stable_timer(env.arm_bad_time, arm_error > cfg.failure_arm_error, env.step_dt)
    out_of_bounds = ((pos[:, 1].abs() > 1.5) | (pos[:, 0] < cfg.rear_boundary_x)
                     | (pos[:, 0] > cfg.box_front + cfg.box_length + 0.5))
    low = pos[:, 2] < 0.16
    env.failure_reasons = {
        "startup_unstable": startup_failed,
        "base_or_arm_contact": forbidden_contact,
        "bad_orientation": tilt > cfg.failure_tilt, "low_posture": low,
        "arm_hold_lost": env.arm_bad_time >= cfg.failure_arm_seconds,
        "out_of_bounds": out_of_bounds,
    }
    env.failure = torch.stack(list(env.failure_reasons.values())).any(0)
    env.top_contact_age[:] = update_top_contact_age(env.top_contact_age, support, env.step_dt)
    # 曾承重是每脚布尔历史，用于新步态落箱判定；成功还要查0.75s内的近期承重，不能只凭曾经。
    if cfg.approach_quality_enabled:
        env.approach_quality.update(env, pos, feet, forces, support)
    env.ever_top_support |= support
    env.max_supported_feet[:] = torch.maximum(env.max_supported_feet, support.sum(-1))
    env.max_root_x[:] = torch.maximum(env.max_root_x, pos[:, 0])
    geometry_ready = platform_ascent_geometry(feet, env.top_contact_age, pos[:, 0], cfg, env.heights)
    from .gait_quality import forward_pose_ready
    geometry_ready &= forward_pose_ready(pos, yaw, cfg)
    # 连续0.3秒确认的是安全几何／近期承重／朝向；当前>=2足支撑、倾角和臂误差仅在提交成功时检查。
    env.hold, env.success = ascent_confirmation(
        env.hold, geometry_ready, support, tilt, arm_error, env.failure, cfg, env.step_dt)
    terminated = env.failure | env.success
    timeout = (env.episode_length_buf >= env.max_episode_length) & ~terminated
    env.peak_arm_error = torch.maximum(env.peak_arm_error, arm_error)
    env.peak_contact_force = torch.maximum(env.peak_contact_force, forces.norm(dim=-1).amax(-1))
    # 在自动reset之前留终态观测，给超时自举；真正失败或成功不跨回合接价值。
    env.extras["terminal_observations"] = env._build_observation().detach().clone()
    if cfg.amp_enabled:
        from .amp import snapshot
        env.extras["amp_terminal_state"], env.extras["amp_terminal_gate"] = snapshot(env)
        env.extras["amp_terminal_forward_speed"] = env.robot.data.root_lin_vel_w[:, 0].detach().clone()
    records = []
    for i in (terminated | timeout).nonzero().flatten().tolist():
        reasons = [k for k, v in env.failure_reasons.items() if bool(v[i])]
        records.append({"env": i, "success": bool(env.success[i]),
            "reason": "success" if env.success[i] else ",".join(reasons) or "timeout",
            "seconds": float(env.episode_length_buf[i] * env.step_dt),
            "box_height": float(env.heights[i]), "curriculum_level": int(env.levels[i]),
            "traversal_seconds": float(env.hold[i]), "supported_feet": int(support[i].sum()),
            "supported_foot_names": [name for j, name in enumerate(FOOT_NAMES) if bool(support[i, j])],
            "ever_top_supported_foot_names": [name for j, name in enumerate(FOOT_NAMES) if bool(env.ever_top_support[i, j])],
            "top_contact_age_s": [v if math.isfinite(v) else None for v in env.top_contact_age[i].tolist()],
            "max_supported_feet": int(env.max_supported_feet[i]), "max_root_x": float(env.max_root_x[i]),
            "foot_positions": feet[i].tolist(),
            "peak_arm_error_rad": float(env.peak_arm_error[i]),
            "final_arm_error_rad": float(arm_error[i]),
            "arm_joint_error_rad": (env.robot.data.joint_pos[i, env.joint_ids[12:]] - env.reference[i, 12:]).tolist(),
            "peak_foot_contact_N": float(env.peak_contact_force[i]),
            "root_position": pos[i].tolist()})
        if cfg.approach_quality_enabled:
            records[-1].update(env.approach_quality.record(i))
            records[-1]['curriculum_qualified'] = bool(env.success[i] and env.approach_quality.passed()[i])
        records[-1]["yaw_rad"] = float(yaw[i])
        records[-1]["forward_heading_error_rad"] = float(torch.atan2(yaw[i].sin(), yaw[i].cos()).abs())
    env.extras["episode_records"] = records
    return terminated, timeout

