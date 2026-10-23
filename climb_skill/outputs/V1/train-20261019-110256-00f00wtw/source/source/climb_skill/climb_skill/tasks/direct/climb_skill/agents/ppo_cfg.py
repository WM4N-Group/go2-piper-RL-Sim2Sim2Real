"""PPO and history-adaptation hyperparameters. No Isaac Sim import required."""
from dataclasses import dataclass, field

@dataclass
class PPOConfig:
    amp: dict = field(default_factory=dict)  # 空字典保持历史PPO行为
    # 每轮每环境收集的控制步数；24步=0.48s，不是必须收完整回合才更新。
    steps_per_env: int = 24
    # 从头训练的PPO更新轮数；续训时是额外轮数，不是最终绝对轮号。
    iterations: int = 15000
    # 每批rollout重复优化次数；PPO与后续辅助网络循环各5次。
    epochs: int = 5
    # 每次epoch把整批随机切成几份；49152/4=12288样本一份。
    minibatches: int = 4
    # PPO主Adam初始学习率，同时作为history Adam固定学习率；主优化器后续按KL自适应。
    learning_rate: float = 2e-4
    # 速度估计器独立Adam学习率，固定，不随主KL自适应变化。
    estimator_learning_rate: float = 1e-4
    # 每控制步折扣因子；不是每物理步或每PPO轮折扣。
    gamma: float = 0.99
    # GAE优势估计递推系数，与gamma共同控制偏差／方差。
    gae_lambda: float = 0.95
    # PPO概率比裁剪半径，同时用于价值预测裁剪；概率比范围0.8..1.2。
    clip: float = 0.2
    # 主loss中价值回归损失系数；价值目标是GAE return。
    value_coefficient: float = 1.0
    # 主loss减去该系数乘12维高斯熵，以保留探索；不是环境奖励项。
    entropy_coefficient: float = 0.01
    # 主学习率自适应目标KL；超0.02减lr，0<KL<0.005增lr。
    desired_kl: float = 0.01
    # 三个优化器各自反向传播后裁剪总梯度范数的上限。
    max_gradient_norm: float = 1.0
    # 12轴原始高斯动作初始标准差；动作缩放前的1.0，通常对应约0.25rad目标扰动。
    initial_std: float = 1.0
    # 每20个PPO轮使用一轮history rollout并训练history网络；其余轮使用privileged latent。
    history_update_frequency: int = 20
    # 从更新索引2000开始逐步增加特权／历史latent正则系数，之前系数0。
    privileged_reg_start: int = 2000
    # 正则系数线性增长用的更新轮数；索引5000达到最大。
    privileged_reg_duration: int = 3000
    # 主loss中的latent L2范数匹配最大系数；history端detach，梯度推动privileged端。
    privileged_reg_max: float = 0.1
    # 每N个已完成PPO轮保存模型并录像；最后一轮无论整除与否也保存。
    save_interval: int = 100

    def validate(self):
        if self.amp:
            from climb_skill.learning.amp import AMPConfig
            AMPConfig(**self.amp).validate()
        if min(self.steps_per_env, self.iterations, self.epochs, self.minibatches,
               self.history_update_frequency, self.save_interval) < 1:
            raise ValueError("Training counts must be positive")

