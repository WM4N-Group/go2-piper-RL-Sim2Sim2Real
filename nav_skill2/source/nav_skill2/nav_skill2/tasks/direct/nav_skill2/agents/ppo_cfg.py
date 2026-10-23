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

    # 缺省关闭以便旧配置回放/单元夹具；V4 JSON显式开启。
    symmetry_weight: float = 0.0
    symmetry_warmup_iterations: int = 200
    exploration_anneal_start: int = 500
    exploration_anneal_end: int = 0
    final_std_max: float = 0.25
    final_entropy_coefficient: float = 0.001
    amp_speed_conditioning: bool = False
    amp_dataset: str = 'amp_pairs.json'

    def validate(self):
        import math
        from dataclasses import fields
        for f in fields(self):
            value=getattr(self,f.name)
            if isinstance(value,(int,float)) and not math.isfinite(value):raise ValueError(f'Nonfinite PPO {f.name}')
        if min(self.iterations,self.steps_per_env,self.epochs,self.minibatches,self.save_interval,self.symmetry_warmup_iterations)<1:raise ValueError('PPO counts must be positive')
        if self.symmetry_weight<0 or self.entropy_coefficient<0 or self.final_entropy_coefficient<0:raise ValueError('Invalid regularization')
        if not .1<=self.initial_std<=1. or not .1<=self.final_std_max<=self.initial_std:raise ValueError('Invalid exploration scale')
        if self.exploration_anneal_end and not 0<=self.exploration_anneal_start<self.exploration_anneal_end:raise ValueError('Invalid exploration schedule')
