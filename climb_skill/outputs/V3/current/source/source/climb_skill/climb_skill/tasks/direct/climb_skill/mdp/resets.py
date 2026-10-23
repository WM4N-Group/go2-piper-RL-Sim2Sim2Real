"""从箱前地面重置，并按成功情况调整箱高。"""

import torch
from isaaclab.utils.math import euler_xyz_from_quat, quat_from_euler_xyz
from ..task_parameters import FOOT_NAMES, HISTORY, JOINT_NAMES, PROPRIO
from .geometry import box_scan, constrained_actions, stable_timer, top_support
from isaaclab.envs import DirectRLEnv


def reset_idx(env, env_ids):
    if env_ids is None:
        env_ids = env.robot._ALL_INDICES
    # 每个环境独立升降级：成功连续3次升，失败／超时连续3次降；初始化不算失败。
    if env.task.curriculum:
        completed = env.episode_length_buf[env_ids] > 0
        won = env.success[env_ids] & completed
        if env.task.approach_quality_enabled:
            # 登台成功但步态不合格：清升级计数、保持高度，不记作任务失败。
            won &= env.approach_quality.passed()[env_ids]
        lost = ~env.success[env_ids] & completed
        env.success_streak[env_ids] = torch.where(won, env.success_streak[env_ids] + 1, 0)
        env.failure_streak[env_ids] = torch.where(lost, env.failure_streak[env_ids] + 1, 0)
        up = env.success_streak[env_ids] >= env.task.promote_after
        if env.task.quality_window_enabled:
            from .quality_window import update_window
            up = update_window(env, env_ids, completed, won)
        down = env.failure_streak[env_ids] >= env.task.demote_after
        if env.task.quality_window_enabled:
            changed = env_ids[up | down]
            env.quality_history[changed] = False
            env.quality_count[changed] = 0
            env.quality_cursor[changed] = 0
        env.levels[env_ids] = (env.levels[env_ids] + up.long() - down.long()).clamp(0, env.task.curriculum_levels - 1)
        env.success_streak[env_ids] *= ~up
        env.failure_streak[env_ids] *= ~down
        env.heights[env_ids] = env.task.curriculum_min_height + env.levels[env_ids] / (env.task.curriculum_levels - 1) * (
            env.task.box_height - env.task.curriculum_min_height)
    # 父类重置会清传感器、执行器延迟队列等；下方再写本任务根状态、关节状态和箱高。
    if env.task.approach_quality_enabled:
        env.approach_quality.reset(env_ids)
    DirectRLEnv._reset_idx(env, env_ids)
    root = env.robot.data.default_root_state[env_ids].clone()
    root[:, :3] += env.scene.env_origins[env_ids]
    root[:, 0] += torch.empty(len(env_ids), device=env.device).uniform_(*env.task.reset_x_range)
    root[:, 1] += torch.empty(len(env_ids), device=env.device).uniform_(*env.task.reset_y_range)
    yaw = torch.empty(len(env_ids), device=env.device).uniform_(*env.task.reset_yaw_range)
    root[:, 3:7] = quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
    env.robot.write_root_pose_to_sim(root[:, :7], env_ids)
    env.robot.write_root_velocity_to_sim(root[:, 7:], env_ids)
    q = env.robot.data.default_joint_pos[env_ids].clone()
    # 仅腿的初始实际角加±0.03rad扰动；腿参考角仍是默认站姿，臂参考角捕获实际初始角。
    q[:, env.joint_ids[:12]] += torch.empty(len(env_ids), 12, device=env.device).uniform_(-0.03, 0.03)
    env.robot.write_joint_state_to_sim(q, torch.zeros_like(q), env_ids=env_ids)
    # Capture the actual six initial arm angles; no IK/world-frame compensation.
    env.reference[env_ids] = env.robot.data.default_joint_pos[env_ids][:, env.joint_ids]
    env.reference[env_ids, 12:] = q[:, env.joint_ids[12:]]
    env.targets[env_ids] = env.reference[env_ids]
    env.previous_targets[env_ids] = env.reference[env_ids]
    env.previous_previous_targets[env_ids] = env.reference[env_ids]
    env.arm_gravity_torque[env_ids] = 0.
    env.robot.set_joint_effort_target(env.arm_gravity_torque[env_ids],
        joint_ids=env.joint_ids[12:], env_ids=env_ids)
    b = env.box.data.default_root_state[env_ids].clone()
    b[:, :3] += env.scene.env_origins[env_ids]
    # Keep the full-size kinematic cuboid, hide the lower part under the ground during the curriculum.
    # 箱厚始终0.2m；例如5cm课程把中心移到-0.05m，使箱顶仅露出0.05m。不把机器人放到箱顶。
    b[:, 2] = env.scene.env_origins[env_ids, 2] + env.heights[env_ids] - env.task.box_height / 2
    env.box.write_root_pose_to_sim(b[:, :7], env_ids)
    env.box.write_root_velocity_to_sim(torch.zeros_like(b[:, 7:]), env_ids)
    for buffer in (env.actions, env.previous_actions, env.history, env.hold, env.arm_bad_time,
                   env.previous_torques, env.episode_return, env.peak_arm_error, env.peak_contact_force):
        buffer[env_ids] = 0.
    env.success[env_ids] = False
    env.failure[env_ids] = False
    env.startup_elapsed[env_ids] = 0.
    env.startup_stable_time[env_ids] = 0.
    env.startup_ready[env_ids] = False
    env.startup_release_time[env_ids] = float("inf")
    env.fresh[env_ids] = True
    env.previous_distance[env_ids] = torch.linalg.vector_norm(torch.stack((
        env.task.route_goal_x - (root[:, 0] - env.scene.env_origins[env_ids, 0]),
        -(root[:, 1] - env.scene.env_origins[env_ids, 1])), -1), dim=-1)

    # 只清本次重置的环境；不能把旧回合的承重证据带到新回合，其他环境继续原轨迹。
    env.top_contact_age[env_ids] = float("inf")
    env.ever_top_support[env_ids] = False
    env.max_supported_feet[env_ids] = 0
    env.max_root_x[env_ids] = root[:, 0] - env.scene.env_origins[env_ids, 0]
