"""末端位置反馈：修正发送给WBC的命令，不修改机器人状态或验收目标。

借鉴MujocoSkills抓取阶段的有界比例反馈。这里控制end_effector本身，
不引入它针对grasp_tcp的几何偏置或固定高度偏置。
"""
import numpy as np


def ee_feedback_command(actual_pose, target_pose, gain=1.2, limit=.08):
    """XYZ使用与WBC相同的混合坐标系，四元数保持原安全目标。"""
    command = np.asarray(target_pose, dtype=float).copy()
    command[:3] += np.clip(gain*(command[:3]-np.asarray(actual_pose)[:3]), -limit, limit)
    return command
