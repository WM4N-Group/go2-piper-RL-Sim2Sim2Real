"""原控制器所需的数学及接口类型；不加载Isaac或伪造物理状态。

四元数一律wxyz。MuJoCo世界雅可比与此处的世界姿态误差配套使用。
"""
from types import SimpleNamespace
import re
import torch


def quat_mul(a, b):
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    return torch.stack((aw*bw-ax*bx-ay*by-az*bz, aw*bx+ax*bw+ay*bz-az*by,
                        aw*by-ax*bz+ay*bw+az*bx, aw*bz+ax*by-ay*bx+az*bw),dim=-1)


def quat_conjugate(q):
    return torch.cat((q[..., :1],-q[..., 1:]),dim=-1)


def quat_apply(q, v):
    xyz, v = torch.broadcast_tensors(q[..., 1:],v)
    t = 2*torch.cross(xyz,v,dim=-1)
    return v+q[..., :1]*t+torch.cross(xyz,t,dim=-1)


def quat_apply_inverse(q, v):
    return quat_apply(quat_conjugate(q),v)


def quat_from_euler_xyz(roll,pitch,yaw):
    cr,sr = torch.cos(roll/2),torch.sin(roll/2)
    cp,sp = torch.cos(pitch/2),torch.sin(pitch/2)
    cy,sy = torch.cos(yaw/2),torch.sin(yaw/2)
    return torch.stack((cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,
                        cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy),dim=-1)


def yaw_quat(q):
    w,x,y,z = q.unbind(-1)
    yaw = torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
    zeros = torch.zeros_like(yaw)
    return quat_from_euler_xyz(zeros,zeros,yaw)


def compute_pose_error(position,quaternion,target_position,target_quaternion,rot_error_type='axis_angle'):
    error = quat_mul(target_quaternion,quat_conjugate(quaternion))
    error = torch.where(error[..., :1]<0,-error,error)
    norm = torch.linalg.vector_norm(error[..., 1:],dim=-1,keepdim=True)
    angle = 2*torch.atan2(norm,error[..., :1])
    scale = torch.where(norm>1e-7,angle/norm.clamp_min(1e-9),2*torch.ones_like(norm))
    return target_position-position,error[..., 1:]*scale


class SceneEntityCfg:
    def __init__(self,name,body_names=None,body_ids=None,**kwargs):
        self.name,self.body_names,self.body_ids = name,body_names,body_ids

    def resolve(self,scene):
        if self.body_ids is None:
            self.body_ids = scene[self.name].find_bodies(self.body_names)[0]


class ManagerTermBase:
    def __init__(self,cfg,env):
        self.cfg,self._env = cfg,env


class DifferentialIKControllerCfg(SimpleNamespace):
    pass


class DifferentialIKController:
    def __init__(self,cfg,num_envs,device):
        self.cfg = cfg

    def set_command(self,command,ee_quat=None):
        self.command = command

    def compute(self,position,quaternion,jacobian,joints):
        if self.cfg.command_type == 'pose':
            pos,rot = compute_pose_error(position,quaternion,self.command[:, :3],self.command[:, 3:])
            error = torch.cat((pos,rot),dim=-1)
        else:
            jacobian,error = jacobian[:, :3],self.command-position
        jt = jacobian.transpose(-1,-2)
        matrix = jacobian@jt+self.cfg.ik_params['lambda_val']**2*torch.eye(
            jacobian.shape[1],device=jacobian.device,dtype=jacobian.dtype)
        return joints+(jt@torch.linalg.solve(matrix,error.unsqueeze(-1))).squeeze(-1)


def matching_ids(patterns,names,preserve_order=False):
    patterns = [patterns] if isinstance(patterns,str) else patterns
    if preserve_order:
        result = [i for pattern in patterns for i,name in enumerate(names) if re.fullmatch(pattern,name)]
    else:
        result = [i for i,name in enumerate(names) if any(re.fullmatch(p,name) for p in patterns)]
    result = list(dict.fromkeys(result))
    return result,[names[i] for i in result]
