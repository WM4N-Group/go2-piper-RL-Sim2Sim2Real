"""相位自由的四腿参考匹配，提供判别器奖励接近零时仍可用的密集信号。

不推进固定时钟：每次把实际20ms转换与公开参考的全部连续转换比较，
四条腿共享同一个最佳相位，不能给四条腿各挑一个静止姿态。
"""
import torch


def mirror_transitions(pairs):
    """关于机身XZ平面反射：左右交换，hip变号；线速度是极向量，角速度是轴向量。"""
    state = pairs.reshape(-1, 2, 30)
    out = state.clone()
    order = [1, 0, 3, 2]  # FL<->FR，RL<->RR；不会把前腿换成后腿
    sign = state.new_tensor([-1., 1., 1.])
    out[..., :12] = (state[..., :12].reshape(-1, 2, 4, 3)[:, :, order] * sign).flatten(-2)
    out[..., 18:30] = (state[..., 18:30].reshape(-1, 2, 4, 3)[:, :, order] * sign).flatten(-2)
    out[..., 12:15] = state[..., 12:15] * state.new_tensor([1., -1., 1.])
    out[..., 15:18] = state[..., 15:18] * state.new_tensor([-1., 1., -1.])
    return out.flatten(1)


def leg_features(pairs, position_scale, velocity_scale):
    state = pairs.reshape(-1, 2, 30)
    q = state[..., :12].reshape(-1, 2, 4, 3) / position_scale
    qd = state[..., 18:30].reshape(-1, 2, 4, 3) / velocity_scale
    return torch.cat((q, qd), -1).permute(0, 2, 1, 3).flatten(-2)  # N,4,12


class MotionReference:
    def __init__(self, expert, position_scale=.35, velocity_scale=4.):
        self.expert = leg_features(expert, position_scale, velocity_scale).contiguous()
        self.position_scale, self.velocity_scale = position_scale, velocity_scale

    @torch.no_grad()
    def cost(self, pairs):
        """0..1成本；半数均值+半数最差腿，避免前腿良好掩盖某条后腿失常。

        每个参考候选的四腿误差聚合后才选相位；不强迫同相左右对称。
        分块避免创建[4096,258,4,12]广播张量。没有随机抖腿的独立速度奖励。
        """
        features = leg_features(pairs, self.position_scale, self.velocity_scale)
        best = pairs.new_full((len(pairs),), float('inf'))
        best_legs = pairs.new_zeros((len(pairs), 4))
        for references in self.expert.split(64):
            errors = []
            for leg in range(4):
                x, y = features[:, leg], references[:, leg]
                squared = (x.square().sum(-1, keepdim=True) + y.square().sum(-1)[None]
                           - 2*x @ y.T).clamp_min(0.) / x.shape[-1]
                errors.append(squared)
            errors = torch.stack(errors, -1)  # N,K,4
            aggregate = .5*errors.mean(-1) + .5*errors.amax(-1)
            value, ids = aggregate.min(-1)
            chosen = errors[torch.arange(len(pairs), device=pairs.device), ids]
            improve = value < best
            best_legs = torch.where(improve[:, None], chosen, best_legs)
            best = torch.minimum(best, value)
        return best/(1+best), best_legs/(1+best_legs)
