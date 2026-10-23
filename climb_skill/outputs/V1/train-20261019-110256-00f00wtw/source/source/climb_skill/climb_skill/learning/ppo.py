"""PPO, terminal-state bootstrapping, estimator supervision and historical adaptation."""

from dataclasses import asdict
import random
import numpy as np
import torch
from torch import nn

from ..tasks.direct.climb_skill.task_parameters import EXPLICIT, PROPRIO, SCAN, require_implementation


def gae(rewards, values, dones, last_value, gamma, lam):
    """Timeout value has already been added to reward from the pre-reset terminal observation."""
    advantages = torch.zeros_like(rewards)
    carry = torch.zeros_like(last_value)
    for t in reversed(range(rewards.shape[0])):
        following = last_value if t == rewards.shape[0] - 1 else values[t + 1]
        live = (~dones[t]).float()
        delta = rewards[t] + gamma * live * following - values[t]
        carry = delta + gamma * lam * live * carry
        advantages[t] = carry
    return advantages, advantages + values


class PPO:
    def __init__(self, model, cfg, amp=None):
        self.amp = amp
        self.model, self.cfg = model, cfg
        self.iteration = 0
        self.learning_rate = cfg.learning_rate
        # 三个Adam分工：主优化器更新actor/critic/scan/privileged/log_std；另两个只更新估计器和历史编码器。
        self.main_parameters = [p for n, p in model.named_parameters()
                                if not n.startswith(("estimator.", "history_encoder."))]
        self.optimizer = torch.optim.Adam(self.main_parameters, lr=self.learning_rate)
        self.estimator_optimizer = torch.optim.Adam(model.estimator.parameters(), lr=cfg.estimator_learning_rate)
        self.history_optimizer = torch.optim.Adam(model.history_encoder.parameters(), lr=cfg.learning_rate)

    @torch.no_grad()
    def collect(self, env, obs):
        # 索引0、20、40…用history采样并更新history；其余轮用特权latent。整轮采样与PPO更新保持同一分支。
        use_history = self.iteration % self.cfg.history_update_frequency == 0
        batch = {k: [] for k in ("obs", "actions", "logp", "values", "rewards", "dones", "mu", "std")}
        records = []
        diagnostics = {}
        raw_return = 0.
        for _ in range(self.cfg.steps_per_env):
            distribution = self.model.distribution(obs, use_history)
            legs = distribution.sample()
            actions = torch.cat((legs, torch.zeros_like(legs[:, :6])), -1)
            value = self.model.value(obs)
            if self.amp is not None:
                from ..tasks.direct.climb_skill.mdp.amp import snapshot
                amp_before, amp_gate = snapshot(env)
            next_obs, reward, terminated, truncated, info = env.step(actions)
            if self.amp is not None:
                task_reward = reward.clone()
                movement = None
                if env.task.amp_body_gate:
                    # 从重置前机身速度算正风格奖励参与度；参考成本不乘实际速度。
                    # body特征没有世界速度，所以由环境同时保留世界+X分量。
                    movement = (info["amp_terminal_forward_speed"] / env.task.approach_speed).clamp(0, 1)
                style, eligible = self.amp.transition(amp_before, info["amp_terminal_state"],
                    amp_gate, info["amp_terminal_gate"], terminated | truncated, env.step_dt, movement=movement)
                reward = task_reward + style
                for name, val in (("amp_style_reward", style.mean()), ("amp_eligible_fraction", eligible),
                                  ("task_step_reward", task_reward.mean())):
                    diagnostics[name] = diagnostics.get(name, 0.) + val.detach()
                for name, val in self.amp.last_diagnostics.items():
                    diagnostics[name] = diagnostics.get(name, 0.) + val.detach()
            raw_return += float(reward.mean())
            # The reset observation must never be used as a time-limit bootstrap state.
            # 环境可能自动reset；超时的价值自举必须取reset之前的终态，不能误用下一回合起点。
            corrected = reward.clone()
            if truncated.any():
                terminal_value = self.model.value(info["terminal_observations"])
                corrected += self.cfg.gamma * terminal_value * truncated.float()
            values = (obs, legs, distribution.log_prob(legs).sum(-1), value, corrected,
                      terminated | truncated, distribution.mean, distribution.stddev)
            for key, tensor in zip(batch, values):
                batch[key].append(tensor.detach().clone())
            records.extend(info.get("episode_records", []))
            for key, value in info.get("diagnostics", {}).items():
                diagnostics[key] = diagnostics.get(key, 0.) + value.detach()
            obs = next_obs["policy"]
        batch = {k: torch.stack(v) for k, v in batch.items()}
        advantage, returns = gae(batch["rewards"], batch["values"], batch["dones"],
                                 self.model.value(obs), self.cfg.gamma, self.cfg.gae_lambda)
        batch["advantages"], batch["returns"] = advantage, returns
        # 维度由[24,2048,…]展成[49152,…]；回合可以横跨多个rollout，GAE遇到done会截断。
        batch = {k: v.flatten(0, 1) for k, v in batch.items()}
        # 整批优势标准化：均值0、标准差1；这不等于观测归一化或把环境回报截成非负。
        batch["advantages"] = (batch["advantages"] - batch["advantages"].mean()) / (
            batch["advantages"].std(unbiased=False) + 1e-8)
        self.rollout_diagnostics = {k: float(v / self.cfg.steps_per_env) for k, v in diagnostics.items()}
        return obs, batch, use_history, records, raw_return / self.cfg.steps_per_env

    def update(self, batch, use_history):
        cfg, model = self.cfg, self.model
        total = len(batch["obs"])
        if total < cfg.minibatches:
            raise ValueError("Rollout is smaller than minibatch count")
        # 特权latent向历史latent靠拢的系数：索引2000前为0，再用3000轮线性增到0.1。
        regularization = cfg.privileged_reg_max * min(max(
            (self.iteration - cfg.privileged_reg_start) / max(cfg.privileged_reg_duration, 1), 0.), 1.)
        logs = {k: [] for k in ("policy_loss", "value_loss", "entropy", "kl", "estimator_loss", "history_loss")}
        for _ in range(cfg.epochs):
            for ids in torch.tensor_split(torch.randperm(total, device=batch["obs"].device), cfg.minibatches):
                obs = batch["obs"][ids]
                dist = model.distribution(obs, use_history)
                logp = dist.log_prob(batch["actions"][ids]).sum(-1)
                with torch.no_grad():
                    old_mu, old_std = batch["mu"][ids], batch["std"][ids]
                    kl = (torch.log(dist.stddev / old_std) +
                          (old_std.square() + (old_mu - dist.mean).square()) / (2 * dist.stddev.square()) - 0.5).sum(-1).mean()
                    # 按每个minibatch的新旧高斯KL调主Adam学习率；不是KL过大就提前终止epoch。
                    if kl > 2 * cfg.desired_kl:
                        self.learning_rate = max(1e-5, self.learning_rate / 1.5)
                    elif 0 < kl < cfg.desired_kl / 2:
                        self.learning_rate = min(1e-2, self.learning_rate * 1.5)
                    for group in self.optimizer.param_groups:
                        group["lr"] = self.learning_rate
                # PPO核心：新策略对旧动作的概率比，结合优势做0.8..1.2裁剪，限制单次策略变化。
                ratio = (logp - batch["logp"][ids]).exp()
                advantage = batch["advantages"][ids]
                policy_loss = torch.maximum(-advantage * ratio, -advantage * ratio.clamp(1 - cfg.clip, 1 + cfg.clip)).mean()
                value = model.value(obs)
                clipped = batch["values"][ids] + (value - batch["values"][ids]).clamp(-cfg.clip, cfg.clip)
                value_loss = torch.maximum((value - batch["returns"][ids]).square(),
                                            (clipped - batch["returns"][ids]).square()).mean()
                entropy = dist.entropy().sum(-1).mean()
                # 这里是20维latent差的L2范数均值，不是平方误差；detach历史端，因此该正则只推动特权编码器。
                reg = (model.privileged_latent(obs) - model.history_latent(obs).detach()).norm(dim=-1).mean()
                # 熵项减号鼓励探索；value/latent项是训练loss，不是环境给机器人的奖励。
                loss = policy_loss + cfg.value_coefficient * value_loss - cfg.entropy_coefficient * entropy + regularization * reg
                if not torch.isfinite(loss):
                    raise FloatingPointError("Nonfinite PPO loss")
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.main_parameters, cfg.max_gradient_norm)
                self.optimizer.step()
                for name, value in (("policy_loss", policy_loss), ("value_loss", value_loss), ("entropy", entropy), ("kl", kl)):
                    logs[name].append(float(value.detach()))
        # 先完成全部主PPO epochs，再改估计器／历史网络，避免同一批PPO更新期间辅助输入持续漂移。
        # Keep estimated velocity and history features fixed throughout each PPO update.
        for _ in range(cfg.epochs):
            for ids in torch.tensor_split(torch.randperm(total, device=batch["obs"].device), cfg.minibatches):
                obs = batch["obs"][ids]
                estimate = model.estimator(obs[:, :PROPRIO])
                # 监督标签为观测201:204，即真实机身系线速度×2；估计器并不接收这段真值作为输入。
                loss = (estimate - obs[:, PROPRIO + SCAN:PROPRIO + SCAN + EXPLICIT]).square().mean()
                self.estimator_optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.estimator.parameters(), cfg.max_gradient_norm)
                self.estimator_optimizer.step()
                logs["estimator_loss"].append(float(loss.detach()))
                # history仅在指定轮次做监督适配，目标来自detach后的特权latent；回放始终走history。
                if use_history:
                    loss = (model.history_latent(obs) - model.privileged_latent(obs).detach()).norm(dim=-1).mean()
                    self.history_optimizer.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.history_encoder.parameters(), cfg.max_gradient_norm)
                    self.history_optimizer.step()
                    logs["history_loss"].append(float(loss.detach()))
        amp_logs = self.amp.update() if self.amp is not None else {}
        self.iteration += 1
        return {**{k: sum(v) / max(len(v), 1) for k, v in logs.items()},
                "learning_rate": self.learning_rate, "privileged_reg_coefficient": regularization, **amp_logs}

    def save(self, path, configuration, curriculum_levels=None):
        # 保存三个优化器、全部网络、轮次、学习率、随机数状态和课程等级；不保存完整PhysX世界状态。
        payload = {"format": "climb_skill_v1", "model": self.model.state_dict(),
                   "optimizer": self.optimizer.state_dict(), "estimator_optimizer": self.estimator_optimizer.state_dict(),
                   "history_optimizer": self.history_optimizer.state_dict(), "iteration": self.iteration,
                   "learning_rate": self.learning_rate, "configuration": configuration,
                   "torch_rng": torch.get_rng_state(), "python_rng": random.getstate(), "numpy_rng": np.random.get_state(),
                   "curriculum_levels": curriculum_levels}
        if self.amp is not None:
            payload["amp"] = self.amp.state_dict()
        if torch.cuda.is_available():
            payload["cuda_rng"] = torch.cuda.get_rng_state_all()
        temporary = path.with_suffix(".tmp")
        torch.save(payload, temporary)
        temporary.replace(path)

    def load(self, path):
        # Checkpoints are local training artifacts; never load untrusted pickle files.
        state = torch.load(path, map_location=next(self.model.parameters()).device, weights_only=False)
        if state.get("format") != "climb_skill_v1":
            raise ValueError("Not a climb_skill checkpoint; old NAV/CLIMB weights are incompatible")
        require_implementation(state["configuration"])
        if (self.amp is not None) != ("amp" in state):
            raise ValueError("AMP checkpoint/optimizer mismatch")
        if self.amp is not None:
            self.amp.load_state_dict(state["amp"])
        self.model.load_state_dict(state["model"])
        for name in ("optimizer", "estimator_optimizer", "history_optimizer"):
            getattr(self, name).load_state_dict(state[name])
        self.iteration, self.learning_rate = state["iteration"], state["learning_rate"]
        torch.set_rng_state(state["torch_rng"].cpu())
        random.setstate(state["python_rng"])
        np.random.set_state(state["numpy_rng"])
        if "cuda_rng" in state and torch.cuda.is_available():
            torch.cuda.set_rng_state_all([x.cpu() for x in state["cuda_rng"]])
        return state
