"""前腿关节与机身抬头的软成本：超出才罚，不裁剪动作或改机械限位。"""
import torch


def front_soft_cost(q, targets, gravity, movement, cfg):
    indices=[1,2,4,5]  # FL/FR的thigh,calf；hip和后腿不在此项中
    lower=q.new_tensor([cfg.front_thigh_min,cfg.front_calf_min]*2)
    upper=q.new_tensor([cfg.front_thigh_max,cfg.front_calf_max]*2)
    def excess(x):
        return ((lower-x).clamp_min(0)+(x-upper).clamp_min(0)).div(cfg.front_joint_scale).square().mean(-1)
    joint=.5*(excess(q[:,indices])+excess(targets[:,indices]))
    # X向前、Z向上；正值表示鼻端向上，不是直接使用欧拉Y角的符号。
    nose_up=torch.atan2(-gravity[:,0],-gravity[:,2])
    pitch=((nose_up-cfg.front_pitch_soft_max).clamp_min(0)/cfg.front_pitch_scale).square()
    return {'front_joint_soft':movement*joint,'front_pitch_soft':movement*pitch}

