"""任务参数集中入口；单位m、s、rad。修改后从头训练生效，续训从checkpoint恢复。"""
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from .agents.ppo_cfg import PPOConfig
LEG_NAMES=tuple(f'{leg}_{joint}_joint' for leg in ('FL','FR','RL','RR') for joint in ('hip','thigh','calf'))
JOINT_NAMES=LEG_NAMES+tuple(f'joint{i}' for i in range(1,7))
FOOT_NAMES=tuple(f'{leg}_foot' for leg in ('FL','FR','RL','RR'))
# angvel3 + gravity3 + q18 + qdot18 + executed action18 + body velocity command3
FRAME=63
HISTORY=5
ACTOR_OBS=FRAME*HISTORY
CRITIC_OBS=ACTOR_OBS+3+4+2 # 本体历史 + 特权真实线速度/足接触/附加质量与摩擦
REVISION='nav_skill2_motion_amp_v3'

@dataclass
class TaskConfig:
    seed: int = 1
    num_envs: int = 2048
    spacing: float = 12.0
    physics_dt: float = 0.005
    decimation: int = 4
    episode_seconds: float = 25.0
    arm_pose: tuple = (0.,0.,0.,0.,0.,0.)
    arm_gravity_compensation: bool = True
    actuator_delay_max: int = 4
    action_scale: float = 0.25
    max_position_offset: float = 0.9
    randomization: bool = True
    added_mass_range: tuple = (0.,1.)
    friction_range: tuple = (0.6,1.0)
    motor_scale_range: tuple = (0.9,1.1)
    curriculum: bool = True
    levels: int = 5
    promote_successes: int = 3
    demote_failures: int = 3
    speed_limits: tuple = (0.25,0.3,0.35,0.4,0.45)
    yaw_rate_limits: tuple = (0.35,0.45,0.55,0.65,0.7)
    startup_seconds: float = 0.4 # 指令渐放前短暂承重，不锁腿或机身
    # 旧checkpoint缺省为0，保留原初始化与动作合同；新训练由JSON显式开启。
    reset_settle_seconds: float = 0.0
    startup_action_ramp_seconds: float = 0.0
    command_ramp_seconds: float = 0.6
    acceleration_limit: float = 0.5
    yaw_acceleration_limit: float = 1.0
    lateral_speed_limits: tuple = (.20,.25,.30,.35,.40)
    command_seconds_range: tuple = (4.,6.)
    command_fractions: tuple = (.15,.25,.15,.20,.15,.10) # 停/前/后/侧/纯转/混合，总和1
    minimum_forward_speed: float = 0.15
    minimum_yaw_rate: float = 0.20
    tracking_grace_seconds: float = 1.0
    curriculum_response: float = .45 # 实际沿指令响应比例均值，不是精确速度要求
    curriculum_good_fraction: float = .55
    curriculum_mode_response: float = .30
    curriculum_min_samples: int = 100
    curriculum_min_motion_seconds: float = 2.0
    failure_tilt: float = 0.85
    failure_arm_error: float = 0.35
    failure_arm_seconds: float = 0.3
    contact_failure_force: float = 8.0
    target_base_height: float = 0.30
    rewards: dict = field(default_factory=lambda:dict(
        velocity=3.0, yaw_velocity=1.5, direction_drift=-1.0, overspeed=-2.0,
        stationary=2.0, standing_posture=-1.5,
        upright=-2.0, base_height=-1.0, vertical_velocity=-0.5,
        roll_pitch_rate=-0.1, action_rate=-0.015, joint_acceleration=-2.5e-7,
        torque=-1e-5, foot_slip=-0.3, collision=-1.0,
        joint_limit=-2.0, arm_error=-5.0, flight=-0.5))
    failure_penalty: float = -5.0

    def validate(self):
        import math
        if self.num_envs<1 or self.physics_dt*self.decimation!=0.02:raise ValueError('Requires num_envs>=1 and50Hz control')
        if tuple(self.arm_pose)!=(0.,)*6:raise ValueError('Nav2 arm target must stay zero')
        if self.actuator_delay_max<0 or self.action_scale<=0 or self.max_position_offset<=0:raise ValueError('Invalid action parameters')
        for values in [self.speed_limits,self.yaw_rate_limits,self.lateral_speed_limits]:
            if len(values)!=self.levels or any(v<0 for v in values):raise ValueError('Invalid velocity curriculum limits')
        if len(self.command_fractions)!=6 or any(v<0 for v in self.command_fractions) or abs(sum(self.command_fractions)-1)>1e-6:raise ValueError('Command fractions must sum to1')
        if any(v<self.minimum_forward_speed for v in (*self.speed_limits,*self.lateral_speed_limits)) or any(v<self.minimum_yaw_rate for v in self.yaw_rate_limits):raise ValueError('Minimum command exceeds curriculum limit')
        if not all(0<v<=1 for v in (self.curriculum_response,self.curriculum_good_fraction,self.curriculum_mode_response)):raise ValueError('Invalid directional quality thresholds')
        if min(self.promote_successes,self.demote_failures,self.curriculum_min_samples)<1:raise ValueError('Invalid curriculum count')
        if not 0<self.command_seconds_range[0]<=self.command_seconds_range[1]:raise ValueError('Invalid command duration')
        if any(not math.isfinite(v) or v<0 for v in (self.reset_settle_seconds,self.startup_action_ramp_seconds)):raise ValueError('Invalid startup parameters')
        if self.episode_seconds<=self.startup_action_ramp_seconds:raise ValueError('Startup action ramp exceeds episode')
        if self.episode_seconds<=self.startup_seconds+self.command_ramp_seconds+self.tracking_grace_seconds:raise ValueError('Episode too short')
        if min(self.command_ramp_seconds,self.acceleration_limit,self.yaw_acceleration_limit)<=0:raise ValueError('Invalid smoothing/tracking parameters')
        if not all(math.isfinite(v) for v in self.rewards.values()):raise ValueError('Invalid reward weight')

def load_config(path):
    data=json.loads(Path(path).read_text());task=TaskConfig(**data['task']);ppo=PPOConfig(**data['ppo']);task.validate()
    if min(ppo.iterations,ppo.steps_per_env,ppo.epochs,ppo.minibatches,ppo.save_interval)<1:raise ValueError('PPO counts must be positive')
    return task,ppo

def configuration(task,ppo):return dict(revision=REVISION,task=asdict(task),ppo=asdict(ppo),actor_observations=ACTOR_OBS,critic_observations=CRITIC_OBS,action_dim=18,learned_action_dim=12,joint_order=JOINT_NAMES)
