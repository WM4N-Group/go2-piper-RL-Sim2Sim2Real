"""机身XZ平面的软策略对称：镜像任务对应镜像动作，不规定接触顺序或步频。

63维帧布局：ω3、gravity3、q18、qd18、executed_action18、command3。
ω为轴向量(-,+,-)，gravity/线速度为极向量(+,-,+)。
臂零位轴已核对共享USD：Z/Y/Y/(XZ)/Y/(XZ)，相应关节符号-/+/+/-/+/-。
"""
import torch
from ..tasks.direct.nav_skill2.parameters import FRAME,HISTORY


def mirror_legs(value):
    if value.shape[-1]!=12:raise ValueError('Expected twelve leg joints')
    order=torch.tensor([3,4,5,0,1,2,9,10,11,6,7,8],device=value.device)
    sign=value.new_tensor([-1.,1.,1.]*4)
    return value.index_select(-1,order)*sign


def mirror_joints(value):
    return torch.cat((mirror_legs(value[...,:12]),value[...,12:18]*value.new_tensor([-1.,1.,1.,-1.,1.,-1.])),dim=-1)


def mirror_observations(obs):
    if obs.shape[-1]!=FRAME*HISTORY:raise ValueError('Expected complete actor history')
    frames=obs.reshape(*obs.shape[:-1],HISTORY,FRAME)
    result=frames.clone()
    result[...,:3]=frames[...,:3]*frames.new_tensor([-1.,1.,-1.])
    result[...,3:6]=frames[...,3:6]*frames.new_tensor([1.,-1.,1.])
    for start in (6,24,42):result[...,start:start+18]=mirror_joints(frames[...,start:start+18])
    result[...,60:63]=frames[...,60:63]*frames.new_tensor([1.,-1.,-1.])
    return result.reshape_as(obs)


def mirror_loss(actor,obs,mean=None):
    # 原状态均值作为固定目标；不使用带噪声采样动作，不把镜像样本伪装成PPO轨迹。
    if mean is None:mean=actor(obs)[...,:12]
    expected=mirror_legs(mean.detach())
    return (actor(mirror_observations(obs))[...,:12]-expected).square().mean()


def exploration_schedule(cfg,iteration):
    """按累计训练轮数恢复退火进度；旧配置end=0保持原熵和std上限1。"""
    if not cfg.exploration_anneal_end:return 1.,cfg.entropy_coefficient
    progress=max(0.,min(1.,(iteration-cfg.exploration_anneal_start)/(cfg.exploration_anneal_end-cfg.exploration_anneal_start)))
    cap=cfg.initial_std+(cfg.final_std_max-cfg.initial_std)*progress
    entropy=cfg.entropy_coefficient+(cfg.final_entropy_coefficient-cfg.entropy_coefficient)*progress
    return cap,entropy
