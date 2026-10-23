"""候选的后腿目标工作范围；不是USD机械限位，也不直接改实际关节状态。"""

def rear_target_workspace(targets, cfg):
    result = targets.clone()
    # 明确FL/FR/RL/RR每腿hip/thigh/calf顺序。左右后腿使用同样的矢状面范围。
    # 保留hip外展与前腿动作；大腿仍有约[-0.2,1.8]rad目标空间用于登箱学习。
    result[:, [7, 10]] = result[:, [7, 10]].clamp_max(cfg.rear_thigh_max)
    result[:, [8, 11]] = result[:, [8, 11]].clamp(cfg.rear_calf_min, cfg.rear_calf_max)
    return result
