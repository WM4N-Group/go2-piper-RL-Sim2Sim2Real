"""末端接近：冻结一次目标，位置/姿态同步平滑过渡，避免分段换目标。"""
import torch


class PoseApproach:
    duration = .8
    ik_gain = .4
    velocity_feedback_time = .08
    entry_minimum_seconds = 3.2
    entry_peak_rad_s = 1.5
    entry_tracking_rad_s = 1.8

    def __init__(self,count,device):
        self.started = torch.zeros(count,dtype=torch.bool,device=device)
        self.elapsed = torch.zeros(count,device=device)
        self.release_elapsed = torch.zeros(count,device=device)
        self.start = torch.zeros((count,7),device=device)
        self.goal = torch.zeros_like(self.start)
        self.joint_started = torch.zeros_like(self.started)
        self.joint_elapsed = torch.zeros_like(self.elapsed)
        self.joint_start = torch.zeros((count,6),device=device)
        self.joint_goal = torch.zeros_like(self.joint_start)
        self.joint_duration = torch.full_like(self.elapsed,3.2)

    def reset(self,selected):
        self.started[selected] = False
        self.elapsed[selected] = 0.
        self.release_elapsed[selected] = 0.
        self.joint_started[selected] = False
        self.joint_elapsed[selected] = 0.

    def target(self,active,position,quaternion,goal,dt):
        newly = active & ~self.started
        self.start[newly] = torch.cat((position,quaternion),dim=1)[newly]
        self.goal[newly] = goal[newly]
        # q与-q表示同一个旋转，先统一符号，防止插值走远路或穿过零四元数。
        opposite = (self.start[:,3:]*self.goal[:,3:]).sum(dim=1)<0
        self.goal[newly & opposite,3:] *= -1
        self.started |= newly
        u = (self.elapsed/self.duration).clamp(0.,1.)
        blend = (u**3*(10.-15.*u+6.*u*u))[:,None]
        result = self.start+blend*(self.goal-self.start)
        result[:,3:] = result[:,3:]/torch.linalg.vector_norm(result[:,3:],dim=1,keepdim=True).clamp_min(1.e-9)
        self.elapsed += active.float()*dt
        return result

    def residual_blend(self,ready,dt):
        self.release_elapsed = torch.where(ready,self.release_elapsed+dt,0.)
        u = (self.release_elapsed/.4).clamp(0.,1.)
        return (u*u*(3.-2.*u))[:,None]

    def joint_target(self,active,position,goal,dt,speed_gain=4.):
        """自由空间展开也用零端点速度/加速度的曲线，避免突然刹停激起机身晃动。"""
        newly = active & ~self.joint_started
        self.joint_start[newly] = position[newly]
        self.joint_goal[newly] = goal[newly]
        distance = (goal-position).abs().amax(dim=1)
        speed_scale = speed_gain/4.
        self.joint_duration[newly] = (1.875*distance[newly]/(self.entry_peak_rad_s*speed_scale)).clamp_min(
            self.entry_minimum_seconds/speed_scale)
        self.joint_started |= newly
        u = (self.joint_elapsed/self.joint_duration).clamp(0.,1.)
        blend = (u**3*(10.-15.*u+6.*u*u))[:,None]
        target = self.joint_start+blend*(self.joint_goal-self.joint_start)
        self.joint_elapsed += active.float()*dt
        return target
