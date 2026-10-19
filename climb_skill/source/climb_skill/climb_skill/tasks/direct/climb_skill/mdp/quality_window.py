"""每环境最近5回合，至少3次质量合格；换高度后清空。"""
import torch


def update_window(env, ids, completed, won):
    size = env.task.quality_window_size
    if not hasattr(env, 'quality_history'):
        env.quality_history = torch.zeros(env.num_envs, size, device=env.device, dtype=torch.bool)
        env.quality_count = torch.zeros(env.num_envs, device=env.device, dtype=torch.long)
        env.quality_cursor = torch.zeros_like(env.quality_count)
    valid = ids[completed]
    env.quality_history[valid, env.quality_cursor[valid]] = won[completed]
    env.quality_cursor[valid] = (env.quality_cursor[valid] + 1) % size
    env.quality_count[valid] = (env.quality_count[valid] + 1).clamp_max(size)
    return (completed & won & (env.quality_count[ids] >= size)
            & (env.quality_history[ids].sum(-1) >= env.task.quality_window_required))
