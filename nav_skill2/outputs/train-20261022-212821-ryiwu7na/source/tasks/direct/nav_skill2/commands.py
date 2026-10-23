"""机身速度指令、真实方向响应奖励和课程；不要求精确的速度RMSE。"""
import torch
MODES=('stand','forward','backward','left','right','turn_left','turn_right')

def command_modes(commands):
    """平移以机身XY主方向选参考；纯转向独立匹配。0为停车，不给运动AMP。"""
    vx,vy,wz=commands.unbind(-1)
    x=vx.abs()>=vy.abs()
    translation=torch.where(x,torch.where(vx>=0,1,2),torch.where(vy>=0,3,4))
    turning=torch.where(wz>=0,5,6)
    return torch.where(commands[:,:2].norm(dim=-1)>.05,translation,torch.where(wz.abs()>.1,turning,0)).long()

def sample_commands(levels,task):
    """按配置采样停车/前进/后退/侧移/纯转/混合；最低速度约束纯方向持续指令。"""
    n=len(levels);d=levels.device
    speed=torch.tensor(task.speed_limits,device=d)[levels]
    lateral=torch.tensor(task.lateral_speed_limits,device=d)[levels]
    back=torch.tensor(task.backward_speed_limits if task.backward_speed_limits is not None else task.speed_limits,device=d)[levels]
    yaw=torch.tensor(task.yaw_rate_limits,device=d)[levels]
    p=torch.rand(n,device=d);bounds=torch.tensor(task.command_fractions,device=d).cumsum(0)
    mode=torch.bucketize(p,bounds)
    sign=torch.where(torch.rand(n,device=d)<.5,-1.,1.)
    vx=task.minimum_forward_speed+torch.rand(n,device=d)*(speed-task.minimum_forward_speed)
    back_min=task.minimum_forward_speed if task.minimum_backward_speed is None else task.minimum_backward_speed
    side_min=task.minimum_forward_speed if task.minimum_lateral_speed is None else task.minimum_lateral_speed
    legacy=task.backward_speed_limits is None and task.minimum_backward_speed is None and task.minimum_lateral_speed is None
    vb=vx if legacy else back_min+torch.rand(n,device=d)*(back-back_min)
    vy=side_min+torch.rand(n,device=d)*(lateral-side_min)
    wz=(task.minimum_yaw_rate+torch.rand(n,device=d)*(yaw-task.minimum_yaw_rate))*sign
    out=torch.zeros(n,3,device=d)
    out[:,0]=torch.where(mode==1,vx,torch.where(mode==2,-vb,0.))
    out[:,1]=torch.where(mode==3,sign*vy,0.)
    out[:,2]=torch.where(mode>=4,wz,0.)
    # 椭圆内部采样，包含斜向/倒退转弯；模式5不会把XY各自上限同时当总速度上限。
    angle=torch.rand(n,device=d)*2*torch.pi
    out[:,0]=torch.where(mode==5,torch.where(angle.cos()>=0,vx,vb)*angle.cos(),out[:,0])
    out[:,1]=torch.where(mode==5,(torch.minimum(vx,lateral) if legacy else vy)*angle.sin(),out[:,1])
    return out

def smooth_commands(current,desired,dt,task):
    rate=current.new_tensor([task.acceleration_limit]*2+[task.yaw_acceleration_limit])
    delta=desired-current;limit=dt[:,None]*rate if dt.ndim else dt*rate
    return current+torch.maximum(torch.minimum(delta,limit),-limit)

def motion_terms(commands,velocity,omega,task=None):
    """Climb/Extreme Parkour形式：实际沿指令的运动/指令幅值，上限1。

    不动得0，反向为负；超过目标速度不会继续增加正奖励。软成本抑制
    横漂、无指令自转和明显超速，不强迫固定步频或逐毫秒精确跟踪。
    """
    speed=commands[:,:2].norm(dim=-1);yaw=commands[:,2]
    linear=speed>.05;turn=yaw.abs()>.1
    direction=commands[:,:2]/speed.clamp_min(.05)[:,None]
    projection=(velocity[:,:2]*direction).sum(-1)
    lin_ratio=(projection/speed.clamp_min(.05)).clamp(-1,1)*linear
    yaw_ratio=(omega[:,2]*yaw.sign()/yaw.abs().clamp_min(.1)).clamp(-1,1)*turn
    side=(velocity[:,:2]-projection[:,None]*direction).square().sum(-1)
    drift=torch.where(linear,side,velocity[:,:2].square().sum(-1))
    drift+=~turn*omega[:,2].square() # 零yaw指令时避免一边前进一边自行绕圈
    linear_slack=.15;yaw_slack=.25
    if task is not None and task.overspeed_tolerance_fraction is not None:
        linear_slack=(speed*task.overspeed_tolerance_fraction).clamp_min(task.overspeed_linear_min)
        yaw_slack=(yaw.abs()*task.overspeed_tolerance_fraction).clamp_min(task.overspeed_yaw_min)
    overspeed=(velocity[:,:2].norm(dim=-1)-speed-linear_slack).clamp_min(0).square()
    overspeed+=(omega[:,2].abs()-yaw.abs()-yaw_slack).clamp_min(0).square()
    response=torch.where(linear&turn,torch.minimum(lin_ratio,yaw_ratio),lin_ratio+yaw_ratio)
    good=(response>=.35)&(drift<.09)
    return dict(velocity=lin_ratio,yaw_velocity=yaw_ratio,direction_drift=drift,overspeed=overspeed),response,good

def tracking_quality(linear_sq,yaw_sq,count,motion_seconds,failed,task,command_energy=None,
                     response_sum=None,response_count=None,good_count=None,stop_bad=None,stop_count=None):
    """RMSE仅诊断。升级需实际响应方向、持续运动和停车稳定，不能靠原地存活。"""
    linear=(linear_sq/count.clamp_min(1)).sqrt();yaw=(yaw_sq/count.clamp_min(1)).sqrt()
    eligible=(count>=task.curriculum_min_samples)&(motion_seconds>=task.curriculum_min_motion_seconds)
    qualified=eligible&~failed
    if response_sum is None:return qualified&False,eligible,linear,yaw
    total=response_count.sum(-1).clamp_min(1)
    qualified&=(response_sum.sum(-1)/total>=task.curriculum_response)
    qualified&=(good_count/total>=task.curriculum_good_fraction)
    # 回合里实际出现且有足够样本的行为都要响应，不能只靠前进掩盖完全不会右转。
    per_mode=response_sum/response_count.clamp_min(1)
    qualified&=((response_count<25)|(per_mode>=task.curriculum_mode_response)).all(-1)
    qualified&=(stop_count<25)|(stop_bad/stop_count.clamp_min(1)<=.3)
    return qualified,eligible,linear,yaw


def startup_action_gain(elapsed,seconds):
    """只在回合入口柔和接入腿部残差；0保持旧合同。端点速度、加速度均为0。"""
    if seconds<=0:return torch.ones_like(elapsed)
    x=(elapsed/seconds).clamp(0,1)
    return x*x*x*(10+x*(-15+6*x))
