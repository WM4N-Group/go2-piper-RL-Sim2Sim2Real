"""地形门控 AMP：独立判别器、固定专家归一化、策略回放及完整续训状态。

特征顺序固定为 q(FL/FR/RL/RR各hip/thigh/calf), v_body, omega_body, qdot。
判别器只在优化器更新时求导；策略通过合成奖励/GAE学习，不能反传穿过物理仿真。
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import torch
from torch import nn


@dataclass
class AMPConfig:
    dataset: str = "${CLIMB_AMP_DATASET}"
    reward_scale: float = 0.5  # 每秒系数；实际每步再乘控制周期0.02
    learning_rate: float = 1e-4
    gradient_penalty: float = 10.0
    batch_size: int = 1024
    updates: int = 4
    replay_capacity: int = 65536

    mirror_reference: bool = False
    reference_weight: float = 0.0  # 每秒负成本；旧AMP默认关闭，避免暗改旧checkpoint
    reference_position_scale: float = 0.35  # rad，给带臂负载留下姿态适配范围
    reference_velocity_scale: float = 4.0  # rad/s，不单独奖励摆腿速度

    def validate(self):
        import math
        if not all(math.isfinite(x) and x > 0 for x in
                   (self.reward_scale, self.learning_rate, self.gradient_penalty,
                    self.reference_position_scale, self.reference_velocity_scale)):
            raise ValueError("AMP coefficients must be finite and positive")
        if not math.isfinite(self.reference_weight) or self.reference_weight < 0:
            raise ValueError("Reference weight must be finite and nonnegative")
        if min(self.batch_size, self.updates, self.replay_capacity) < 1:
            raise ValueError("AMP counts must be positive")


def load_pairs(path, device):
    """只读JSON，不执行外部权重；清单包含原文件哈希与明确的30维顺序。"""
    raw = Path(os.path.expandvars(path)).read_bytes()
    data = json.loads(raw)
    from ..tasks.direct.climb_skill.task_parameters import LEG_NAMES
    if (data['format'] != 'climb_amp_pairs_v1' or data['joint_order'] != list(LEG_NAMES)
            or data.get('feature_order') != ['joint_position_12', 'body_linear_velocity_3',
                'body_angular_velocity_3', 'joint_velocity_12']
            or abs(data['dt'] - .02) > 1e-9):
        raise ValueError('AMP dataset contract mismatch')
    pairs = torch.tensor(data['pairs'], dtype=torch.float32, device=device)
    if pairs.ndim != 2 or pairs.shape[1] != 60 or len(pairs) < 32 or not torch.isfinite(pairs).all():
        raise ValueError('AMP requires >=32 finite 60-dimensional transitions')
    return pairs, hashlib.sha256(raw).hexdigest(), {k: v for k, v in data.items() if k != 'pairs'}


class AMP:
    def __init__(self, cfg, device):
        cfg.validate()
        self.cfg = cfg
        self.expert, self.dataset_sha256, self.manifest = load_pairs(cfg.dataset, device)
        from .motion_reference import MotionReference, mirror_transitions
        if cfg.mirror_reference:
            self.expert = torch.cat((self.expert, mirror_transitions(self.expert)), 0)
        self.reference = MotionReference(self.expert, cfg.reference_position_scale,
            cfg.reference_velocity_scale) if cfg.reference_weight > 0 else None
        states = self.expert.reshape(-1, 30)
        self.mean = states.mean(0)
        # 固定专家统计量，避免在线统计随策略漂移；标准差下限避免静止轴被无限放大。
        floor = states.new_tensor([.1]*12 + [.2]*3 + [.5]*3 + [1.]*12)
        self.std = torch.maximum(states.std(0, unbiased=False), floor)
        self.discriminator = nn.Sequential(nn.Linear(60, 512), nn.ReLU(),
            nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 1)).to(device)
        self.optimizer = torch.optim.Adam(self.discriminator.parameters(), lr=cfg.learning_rate)
        self.replay = torch.empty(cfg.replay_capacity, 60, device=device)
        self.size = self.cursor = 0

    def normalize(self, pairs):
        return ((pairs.reshape(-1, 2, 30) - self.mean) / self.std).clamp(-10, 10).flatten(1)

    @torch.no_grad()
    def transition(self, before, after, before_gate, after_gate, done, dt, movement=None):
        if abs(dt - .02) > 1e-8:
            raise ValueError('AMP reference transitions require a 20ms control period')
        pairs = torch.cat((before, after), -1)
        # 两端都必须属于同一允许阶段；终止/超时不进入回放，绝不把reset拼到上一回合。
        gate = torch.minimum(before_gate, after_gate) * (~done).float()
        # 新候选的gate只表示地形/起步，不能因后腿不动或实际速度低而关闭成本。
        movement = torch.ones_like(gate) if movement is None else movement.clamp(0, 1)
        eligible = gate > 0
        reward = gate.new_zeros(gate.shape)
        reference_cost = torch.zeros_like(gate)
        leg_costs = gate.new_zeros((len(gate), 4))
        if eligible.any():
            selected = pairs[eligible]
            score = self.discriminator(self.normalize(selected)).squeeze(-1)
            reward[eligible] = self.cfg.reward_scale * dt * (1 - .25*(score-1).square()).clamp_min(0) * gate[eligible] * movement[eligible]
            if self.reference is not None:
                cost, per_leg = self.reference.cost(selected)
                reference_cost[eligible] = self.cfg.reference_weight * dt * gate[eligible] * cost
                leg_costs[eligible] = per_leg
            self.insert(selected)
        self.last_diagnostics = {"amp_style_positive": reward.mean(),
            "amp_reference_penalty": reference_cost.mean(),
            **{f"amp_reference/{leg}_cost": leg_costs[:, i].sum()/eligible.sum().clamp_min(1)
               for i, leg in enumerate(("FL", "FR", "RL", "RR"))}}
        return reward-reference_cost, eligible.float().mean()

    @torch.no_grad()
    def insert(self, pairs):
        pairs = pairs[-self.cfg.replay_capacity:]
        count = len(pairs)
        ids = (torch.arange(count, device=pairs.device) + self.cursor) % self.cfg.replay_capacity
        self.replay[ids] = pairs
        self.cursor = (self.cursor + count) % self.cfg.replay_capacity
        self.size = min(self.size + count, self.cfg.replay_capacity)

    def update(self):
        if not self.size:
            return {'amp_discriminator_loss': 0., 'amp_replay_size': 0}
        logs = []
        for _ in range(self.cfg.updates):
            real = self.expert[torch.randint(len(self.expert), (self.cfg.batch_size,), device=self.expert.device)]
            fake = self.replay[torch.randint(self.size, (self.cfg.batch_size,), device=self.expert.device)]
            real = self.normalize(real).detach().requires_grad_(True)
            real_score = self.discriminator(real)
            fake_score = self.discriminator(self.normalize(fake))
            grad = torch.autograd.grad(real_score.sum(), real, create_graph=True)[0]
            loss = .5*((real_score-1).square().mean() + (fake_score+1).square().mean())
            loss = loss + self.cfg.gradient_penalty * grad.square().sum(-1).mean()
            if not torch.isfinite(loss):
                raise FloatingPointError('Nonfinite AMP loss')
            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(self.discriminator.parameters(), 1.)
            self.optimizer.step()
            logs.append(float(loss.detach()))
        return {'amp_discriminator_loss': sum(logs)/len(logs), 'amp_replay_size': self.size}

    def state_dict(self):
        from dataclasses import asdict
        contract = asdict(self.cfg); contract.pop("dataset")
        return dict(dataset_sha256=self.dataset_sha256, manifest=self.manifest, contract=contract,
            discriminator=self.discriminator.state_dict(), optimizer=self.optimizer.state_dict(),
            mean=self.mean, std=self.std, replay=self.replay[:self.size].clone(), cursor=self.cursor)

    def load_state_dict(self, state):
        if state['dataset_sha256'] != self.dataset_sha256:
            raise ValueError('AMP reference dataset changed: resume refused')
        from dataclasses import asdict
        contract = asdict(self.cfg); contract.pop("dataset")
        if state.get("contract") != contract:
            raise ValueError("AMP method configuration changed: start a new run")
        replay = state['replay']
        if len(replay) > self.cfg.replay_capacity:
            raise ValueError('AMP replay capacity differs')
        self.discriminator.load_state_dict(state['discriminator'])
        self.optimizer.load_state_dict(state['optimizer'])
        self.mean.copy_(state['mean']); self.std.copy_(state['std'])
        self.size, self.cursor = len(replay), state['cursor']
        self.replay[:self.size].copy_(replay)
