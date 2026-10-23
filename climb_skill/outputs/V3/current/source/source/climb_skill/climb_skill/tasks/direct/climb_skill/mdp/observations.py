"""本体、箱子高度图、速度与历史观测。"""

import torch
from isaaclab.utils.math import euler_xyz_from_quat, quat_from_euler_xyz
from ..task_parameters import FOOT_NAMES, HISTORY, JOINT_NAMES, PROPRIO
from .geometry import box_scan, constrained_actions, stable_timer, top_support


def kinematics(env):
    data = env.robot.data
    # 减去并行环境原点后得到各自局部坐标；任务+X与世界+X一致，不能把2048个原点混在一起。
    pos = data.root_pos_w - env.scene.env_origins
    _, _, yaw = euler_xyz_from_quat(data.root_quat_w)
    yaw = torch.atan2(yaw.sin(), yaw.cos())
    feet = data.body_pos_w[:, env.foot_ids] - env.scene.env_origins[:, None, :]
    forces = env.contact.data.net_forces_w[:, env.contact_feet]
    supported = top_support(feet, forces, env.heights, env.task)
    # The route extends beyond the finish line; no slowing or standing at the entry lip.
    delta = torch.stack((env.task.route_goal_x - pos[:, 0], -pos[:, 1]), dim=-1)
    distance = delta.norm(dim=-1)
    command = torch.full_like(distance, env.task.approach_speed)
    if env.task.startup_stand_seconds > 0:
        from .startup import movement_gain
        command *= movement_gain(env)
    # 当前候选heading仍是“指向前方路点的误差”；固定朝+X另有奖励和成功门槛，二者并非同一变量。
    heading = torch.atan2(delta[:, 1], delta[:, 0]) - yaw
    heading = torch.atan2(heading.sin(), heading.cos())
    if env.task.straight_tracking_enabled:
        # Explicit fixed +X heading; lateral goal error remains in the observation.
        heading = -yaw
    return pos, yaw, feet, forces, supported, delta, distance, command, heading


def proprio_scan(env):
    pos, yaw, feet, forces, support, delta, distance, command, heading = env._kinematics()
    q = env.robot.data.joint_pos[:, env.joint_ids]
    qd = env.robot.data.joint_vel[:, env.joint_ids]
    c, s = yaw.cos(), yaw.sin()
    local_delta = torch.stack((c * delta[:, 0] + s * delta[:, 1],
                               -s * delta[:, 0] + c * delta[:, 1]), -1)
    # 69维索引：[0:3]角速度×0.25，[3:6]重力，[6:8]局部目标，[8]heading，[9]速度命令；
    proprio = torch.cat((env.robot.data.root_ang_vel_b * 0.25,
                          env.robot.data.projected_gravity_b,
                          local_delta.clamp(-2., 2.), heading[:, None], command[:, None],
                          # [10:28]18轴角偏差，[28:46]关节速度×0.05，[46:64]本次执行的残差动作，[64:68]接触，[68]箱高。
                          q - env.reference, qd * 0.05, env.actions,
                          (forces[..., 2] > 2.).float() - 0.5, env.heights[:, None]), -1)
    sx, sy = env.sample_xy[:, 0], env.sample_xy[:, 1]
    points = torch.stack((pos[:, 0, None] + c[:, None] * sx - s[:, None] * sy,
                          pos[:, 1, None] + s[:, None] * sx + c[:, None] * sy), -1)
    # 这是已知箱体几何的解析高度查询，不是相机或带噪声的雷达；输入相对高度而非直接台面绝对z。
    scan = (pos[:, 2, None] - 0.3 - box_scan(points, env.heights, env.task)).clamp(-1., 1.)
    return proprio, scan


def build_observation(env):
    proprio, scan = env._proprio_scan()
    # 完整923维布局：69本体+132扫描+3真实速度×2+29特权参数+10×69历史。Actor不直接读全部真值。
    return torch.cat((proprio, scan, env.robot.data.root_lin_vel_b * 2.,
                      env.privileged, env.history.flatten(1)), -1).clamp(-100., 100.)


def get_observations(env):
    proprio, _ = env._proprio_scan()
    history_frame = proprio.clone()
    # 只屏蔽历史中的目标xy与heading三个量；当前本体中的目标、历史速度命令和箱高都保留。
    history_frame[:, 6:9] = 0.  # Mask goal position and heading, retain body/arm response.
    env.history[env.fresh] = history_frame[env.fresh, None].expand(-1, HISTORY, -1)
    env.fresh[:] = False
    # 先拼接旧历史，再将当前帧推入队列；正常步看到的是此前10帧。重置第一帧用重复首帧填满。
    obs = env._build_observation()
    if env.history_step != env.common_step_counter:
        env.history = torch.cat((env.history[:, 1:], history_frame[:, None]), dim=1)
        env.history_step = env.common_step_counter
    if not torch.isfinite(obs).all():
        raise FloatingPointError("Nonfinite CLIMB observation")
    return {"policy": obs}

