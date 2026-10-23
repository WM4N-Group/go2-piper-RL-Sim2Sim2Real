"""Optional PPO sampling at controllable PUSH states; no simulator shortcuts."""

from types import SimpleNamespace

import torch


def active_storage_view(storage, active):
    """Build a training-only view; full trajectory returns remain untouched."""
    indices = active.flatten().nonzero(as_tuple=False).flatten()
    if indices.numel() < 2:
        raise ValueError("At least two active samples are needed for normalization")

    def select(value):
        return value.flatten(0, 1)[indices].unsqueeze(0)

    view = SimpleNamespace(
        training_type=storage.training_type, device=storage.device,
        num_envs=indices.numel(), num_transitions_per_env=1,
        observations=select(storage.observations), actions=select(storage.actions),
        values=select(storage.values), returns=select(storage.returns),
        actions_log_prob=select(storage.actions_log_prob),
        distribution_params=tuple(select(p) for p in storage.distribution_params),
    )
    advantage = view.returns - view.values
    view.advantages = (advantage - advantage.mean()) / (advantage.std() + 1e-8)
    return view


def install_push_action_sampling(algorithm, *, active_only):
    """Adapt the installed feedforward PPO without editing its package or models.

    Both actor and critic minibatches, including entropy, use the selected states.
    GAE is still computed on the complete physical trajectory before selection.
    """
    if (algorithm.actor.is_recurrent or algorithm.critic.is_recurrent
            or algorithm.symmetry or algorithm.rnd or algorithm.is_multi_gpu
            or algorithm.normalize_advantage_per_mini_batch):
        raise ValueError("PUSH sampling requires plain feedforward single-GPU PPO")
    storage = algorithm.storage
    active = torch.zeros_like(storage.values[..., 0], dtype=torch.bool)
    original_step = algorithm.process_env_step
    original_update = algorithm.update
    original_generator = storage.mini_batch_generator

    def process_env_step(obs, rewards, dones, extras):
        mask = extras["push_policy_action_active"]
        if mask.dtype != torch.bool or mask.shape != active.shape[1:]:
            raise ValueError("Invalid applied-action activity mask")
        active[storage.step].copy_(mask)
        original_step(obs, rewards, dones, extras)

    def update():
        if storage.step != active.shape[0]:
            raise ValueError("Incomplete rollout for PUSH sampling")
        count = int(active.sum().item())
        minimum = max(2, algorithm.num_mini_batches)
        if active_only and count < minimum:
            # Do not step Adam on inactive samples, including its stored momentum.
            storage.clear()
            losses = {"value": 0.0, "surrogate": 0.0, "entropy": 0.0}
            skipped = 1.0
        else:
            if active_only:
                view = active_storage_view(storage, active)
                storage.mini_batch_generator = lambda *args, **kwargs: original_generator.__func__(view, *args, **kwargs)
            try:
                losses = original_update()
            finally:
                storage.mini_batch_generator = original_generator
            skipped = 0.0
        losses.update(push_active_fraction=count / active.numel(), push_skipped_update=skipped)
        print(f"[PUSH_SAMPLING] mode={'active' if active_only else 'all'} active={count}/{active.numel()} skipped={int(skipped)}", flush=True)
        active.zero_()
        return losses

    algorithm.process_env_step = process_env_step
    algorithm.update = update
