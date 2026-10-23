"""PPO与AMP参数：正式配置可在configs/nav.json中覆盖。"""
from dataclasses import dataclass

@dataclass
class PPOConfig:
    iterations: int = 15000
    steps_per_env: int = 24
    epochs: int = 5
    minibatches: int = 4
    learning_rate: float = 0.0002
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip: float = 0.2
    value_coefficient: float = 1.0
    entropy_coefficient: float = 0.01
    desired_kl: float = 0.01
    max_gradient_norm: float = 1.0
    initial_std: float = 1.0
    save_interval: int = 100
    amp_enabled: bool = True
    amp_reward: float = 2.0
    reference_weight: float = 0.5
    amp_learning_rate: float = 0.0001
    amp_gradient_penalty: float = 10.0
    amp_batch_size: int = 1024
    amp_updates: int = 4
    replay_capacity: int = 65536
