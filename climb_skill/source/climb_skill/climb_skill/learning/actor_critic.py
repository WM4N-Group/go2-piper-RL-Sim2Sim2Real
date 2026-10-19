"""Height-conditioned PPO with history adaptation, following Extreme Parkour's architecture.

New implementation: a box task, 18-axis constrained output, consistent estimated velocity
in rollout/update/inference, and no camera distillation or pre-existing WBC.
"""

import torch
from torch import nn
from torch.distributions import Normal

from ..tasks.direct.climb_skill.task_parameters import EXPLICIT, HISTORY, OBSERVATIONS, PRIVILEGED, PROPRIO, SCAN


def mlp(sizes, last_activation=None):
    layers = []
    for i, (a, b) in enumerate(zip(sizes[:-1], sizes[1:])):
        layers.append(nn.Linear(a, b))
        if i < len(sizes) - 2:
            layers.append(nn.ELU())
    if last_activation is not None:
        layers.append(last_activation)
    return nn.Sequential(*layers)


class HistoryEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        # 历史输入为[N,10,69]；先逐帧压到30维，再沿时间卷积。10→4→3帧，展平为30维，再输出20维。
        self.frame = mlp([PROPRIO, 30], nn.ELU())
        self.temporal = nn.Sequential(nn.Conv1d(30, 20, 4, 2), nn.ELU(),
                                      nn.Conv1d(20, 10, 2, 1), nn.ELU(), nn.Flatten(),
                                      nn.Linear(30, 20), nn.ELU())

    def forward(self, history):
        return self.temporal(self.frame(history.reshape(-1, HISTORY, PROPRIO)).transpose(1, 2))


class ClimbActorCritic(nn.Module):
    def __init__(self, initial_std=1.0):
        super().__init__()
        # 网络分工：132维真实几何高度扫描→32维；29维动力学特权量／10帧历史各→20维latent。
        self.scan_encoder = mlp([SCAN, 128, 64, 32], nn.Tanh())
        self.privileged_encoder = mlp([PRIVILEGED, 64, 20], nn.ELU())
        self.history_encoder = HistoryEncoder()
        self.estimator = mlp([PROPRIO, 128, 64, EXPLICIT])
        # 动作主干输入124=69本体+32高度特征+3估计速度+20动力学特征，只输出12个腿关节均值。
        self.actor = mlp([PROPRIO + 32 + EXPLICIT + 20, 512, 256, 128, 12])
        self.critic = mlp([OBSERVATIONS, 512, 256, 128, 1])
        # 每腿关节一个可学习log标准差；这是动作探索，不是额外18轴控制器。
        self.log_std = nn.Parameter(torch.full((12,), float(initial_std)).log())
        self.apply(self._initialize)
        nn.init.orthogonal_(self.actor[-1].weight, gain=0.01)
        nn.init.zeros_(self.actor[-1].bias)

    @staticmethod
    def _initialize(module):
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=2 ** 0.5)
            nn.init.zeros_(module.bias)

    def privileged_latent(self, obs):
        start = PROPRIO + SCAN + EXPLICIT
        return self.privileged_encoder(obs[:, start:start + PRIVILEGED])

    def history_latent(self, obs):
        return self.history_encoder(obs[:, -PROPRIO * HISTORY:])

    def mean(self, obs, use_history=True):
        proprio = obs[:, :PROPRIO]
        scan = self.scan_encoder(obs[:, PROPRIO:PROPRIO + SCAN])
        # Auxiliary networks have their own optimizers and supervised update after PPO epochs.
        # 估计器预测线速度×2，与监督标签单位一致；detach表示PPO不反向训练估计器。
        explicit = self.estimator(proprio).detach()
        # history分支也从PPO梯度中分离；特权分支不detach，会随主PPO更新。
        latent = self.history_latent(obs).detach() if use_history else self.privileged_latent(obs)
        legs = self.actor(torch.cat((proprio, scan, explicit, latent), -1))
        # 后6维精确补零，含义是臂相对参考角残差为零；不是臂目标角全部强制为零。
        return torch.cat((legs, torch.zeros_like(legs[:, :6])), -1)

    def distribution(self, obs, use_history):
        # A 12-dimensional density avoids entropy/log-prob gradients on ignored arm axes.
        # 只在12维腿空间计算log概率和熵；std在exp(-5)..exp(2)之间，输出均值没有tanh限幅。
        return Normal(self.mean(obs, use_history)[:, :12], self.log_std.clamp(-5., 2.).exp())

    def value(self, obs):
        return self.critic(obs).squeeze(-1)

    def forward(self, obs):
        """Export/deployment always uses history and estimated velocity; output shape is [N,18]."""
        return self.mean(obs, use_history=True)

