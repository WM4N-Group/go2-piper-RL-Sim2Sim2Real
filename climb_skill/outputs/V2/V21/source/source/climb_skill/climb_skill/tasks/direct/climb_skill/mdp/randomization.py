"""实际质量、摩擦与腿部PD随机化。"""

import torch
from ..task_parameters import JOINT_NAMES


def randomize_physics(env):
    """Randomize once per environment and expose the actual parameters to the teacher."""
    cfg = env.task
    view = env.robot.root_physx_view
    ids_cpu = torch.arange(env.num_envs, dtype=torch.int32)
    # 此函数在环境创建时调用一次，不在每回合reset调用；先读真实USD质量，再加随机负载。
    mass = view.get_masses().clone()
    inertia = view.get_inertias().clone()
    base_ids, _ = env.robot.find_bodies("base")
    base = base_ids[0]
    added = torch.empty(env.num_envs).uniform_(*cfg.added_mass_range) if cfg.randomization else torch.zeros(env.num_envs)
    old_mass = mass[:, base].clone()
    mass[:, base] += added.to(mass.device)
    # 这里只把base惯量按新旧质量比整体缩放，未另行模拟负载COM偏移。
    inertia[:, base] *= (mass[:, base] / old_mass).unsqueeze(-1)
    view.set_masses(mass, ids_cpu)
    view.set_inertias(inertia, ids_cpu)
    # 29维特权量：[0]附加质量，[1:4]COM偏移为0，[4]机器人静摩擦，[5:17]Kp乘数减1，[17:29]Kd乘数减1。
    env.privileged[:, 0] = added.to(env.device)
    # COM offsets are zero in this first task; no fictional privileged randomization.
    mu = torch.empty(env.num_envs).uniform_(*cfg.friction_range) if cfg.randomization else torch.full((env.num_envs,), 0.8)
    material = view.get_material_properties().clone()
    material[..., 0] = mu.to(material.device)[:, None]
    material[..., 1] = 0.75 * mu.to(material.device)[:, None]
    material[..., 2] = 0.
    view.set_material_properties(material, ids_cpu)
    env.privileged[:, 4] = mu.to(env.device)
    actuator = env.robot.actuators["legs"]
    kp = torch.ones(env.num_envs, 12, device=env.device)
    kd = kp.clone()
    if cfg.randomization:
        kp.uniform_(*cfg.motor_scale_range)
        kd.uniform_(*cfg.motor_scale_range)
    actuator.stiffness[:] *= kp
    actuator.damping[:] *= kd
    actuator_names = [env.robot.joint_names[i] for i in actuator.joint_indices]
    order = [actuator_names.index(n) for n in JOINT_NAMES[:12]]
    env.privileged[:, 5:17] = kp[:, order] - 1.
    env.privileged[:, 17:29] = kd[:, order] - 1.

