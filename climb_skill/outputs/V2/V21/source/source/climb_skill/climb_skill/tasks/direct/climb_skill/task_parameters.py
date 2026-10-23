"""All task and learning parameters; distances in m, angles in rad, time in s."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from .agents.ppo_cfg import PPOConfig

IMPLEMENTATION_REVISION = "climb_skill_v6_forward_baseline_front_soft30"

UPSTREAM_COMMIT = "d2ffe27ba59a3229fad22a9fc94c38010bb1f519"
LEG_NAMES = tuple(f"{leg}_{joint}_joint" for leg in ("FL", "FR", "RL", "RR")
                  for joint in ("hip", "thigh", "calf"))
ARM_NAMES = tuple(f"joint{i}" for i in range(1, 7))
JOINT_NAMES = LEG_NAMES + ARM_NAMES
FOOT_NAMES = tuple(f"{leg}_foot" for leg in ("FL", "FR", "RL", "RR"))
PROPRIO = 69
SCAN = 132
EXPLICIT = 3
PRIVILEGED = 29
HISTORY = 10
OBSERVATIONS = PROPRIO + SCAN + EXPLICIT + PRIVILEGED + HISTORY * PROPRIO


@dataclass
class TaskConfig:
    front_thigh_min: float = -0.3  # rad，前大腿软下界
    front_thigh_max: float = 1.9  # rad，约109度；比后腿1.8宽，超出只产生软成本
    front_calf_min: float = -2.65  # rad，前膝过度折叠软界
    front_calf_max: float = -0.95  # rad，前膝过度伸直软界
    front_joint_scale: float = 0.5  # rad，超出此量约为单位误差
    front_joint_weight: float = 0.5
    front_pitch_soft_max: float = 0.6  # rad，约34度后才产生软成本，不设登箱俯仰硬裁剪
    front_pitch_scale: float = 0.25  # rad，抬头超限的归一化尺度
    front_pitch_weight: float = 0.5
    startup_tilt_tolerance: float = 0.1  # rad，释放起步前的站稳判定
    startup_linear_tolerance: float = 0.1  # m/s
    startup_angular_tolerance: float = 0.3  # rad/s
    rear_thigh_max: float = 1.8  # rad，限制大腿目标过度前折；实际角仍可有PD动态超调
    rear_calf_min: float = -2.5  # rad，避免把后膝目标压到极端折叠
    rear_calf_max: float = -1.05  # rad，避免后膝长期近伸直拖行
    # 全局随机种子；Isaac环境创建时播种。种子相同不保证GPU物理逐位一致。
    seed: int = 1
    # 同时模拟的独立机器人／箱体数量；不是训练回合数。JSON覆盖类默认4096。
    num_envs: int = 4096
    # 每回合最长仿真秒数，包含起步站稳和动作渐放；当前1200个控制步。
    episode_seconds: float = 24.0
    # 每个物理步的秒数；0.005s对应200Hz。
    physics_dt: float = 0.005
    # 每个策略控制步包含的物理步数；控制周期=physics_dt×decimation=0.02s。
    decimation: int = 4
    # 并行环境原点间距，单位m；克隆隔离碰撞，局部任务坐标需减环境原点。
    spacing: float = 7.0
    # 箱体沿世界+X的长度，m；不是爬升高度。
    box_length: float = 2.4
    # 箱体沿Y的宽度，m，关于y=0对称。
    box_width: float = 1.2
    # 最终目标高度兼物理箱体厚度，m；课程通过下移箱体改变露出地面高度。
    box_height: float = 0.3
    # 箱体前沿局部x，m；末沿=box_front+box_length=3.15m。
    box_front: float = 0.75
    # 按每个环境独立的成功／失败序列调节实际箱高；评估脚本强制关闭。
    curriculum: bool = True
    # 课程最低露出地面高度，m；机器人始终从地面开始。
    curriculum_min_height: float = 0.05
    # 高度级数；0..10共11级，间隔2.5cm。
    curriculum_levels: int = 11
    # Success-driven per-environment curriculum; never inject an elevated robot start.
    # 本环境连续成功达到该次数升一级；升级后清成功计数，封顶30cm。
    promote_after: int = 3
    # 本环境连续失败或超时达到该次数降一级；降级后清失败计数。
    demote_after: int = 3
    # 按joint1..joint6排序的初始臂关节角，rad；保持关节相对位置，不保持世界末端位姿。
    arm_pose: tuple = (0., 0., 0., 0., 0., 0.)
    # 每个物理步读取PhysX重力补偿，只将臂6轴分量加到原PD；仍经过延迟与力矩限幅。
    arm_gravity_compensation: bool = True
    # 无量纲策略动作乘此系数转成rad关节偏移；不是力矩缩放。
    action_scale: float = 0.25
    # 策略腿目标相对参考角的最大偏移绝对值，rad；先裁动作到±4.8，再裁腿软关节限位。
    max_position_offset: float = 1.2
    # These are PHYSICS-step delays in the existing GO2-PIPER actuator, not an additional queue.
    # 原DelayedPD最大命令延迟，单位物理步；0..4整数，即0..20ms。每次重置重新抽样。
    actuator_delay_max: int = 4
    # 朝路点方向的速度奖励参考命令，m/s；启动时乘渐放系数，不是物理硬限速。
    approach_speed: float = 0.4
    # 成功判定中足端距箱顶XY边界的安全内缩，m；保留的成功几何，不是已取消的边沿距离惩罚。
    top_margin: float = 0.06
    # 足端link中心到近似足底的半径，m；足底高度=足端z减此值。
    foot_radius: float = 0.02
    # 识别脚在地面／台面接触高度的容差，m。
    foot_height_tolerance: float = 0.035
    # 识别真实台面承重和起步站稳的足底竖直力门槛，N；与普通接触2N门槛不同。
    support_force: float = 8.0
    # 原成功基线的登箱完成线；根坐标至少box_front+1.55=2.30m。
    finish_offset: float = 1.55
    # 原基线连续几何确认时间，不要求连续四脚着地或停稳。
    traversal_seconds: float = 0.3
    traversal_max_tilt: float = 0.30  # rad，提交成功时总倾角
    traversal_heading_tolerance: float = 0.17453292519943295  # rad，10度
    traversal_lateral_tolerance: float = 0.2  # m，原基线朝+X路径条件
    # 前进路点在完成线之后；完成时允许继续行走，不添加减速/停车。
    goal_offset: float = 2.0
    # 每脚最近一次真实台面承重的最大允许年龄，s；摆动脚可短暂不接触。
    top_contact_memory: float = 0.75
    # 提交成功那一刻6个臂关节中的最大绝对误差上限，rad。
    traversal_arm_error: float = 0.08
    # 四脚XY包围盒前后跨度下限，m；不要求固定落脚点。
    minimum_stance_length: float = 0.30
    # 四脚XY包围盒左右跨度下限，m。
    minimum_stance_width: float = 0.16
    # 机身总倾角超过此rad立即失败；0.9rad约51.57度。
    failure_tilt: float = 0.9
    # 臂最大关节误差超过此rad时开始累计丢失时间。
    failure_arm_error: float = 0.35
    # 臂误差连续超阈值达到此秒数失败；中途恢复则计时清零。
    failure_arm_seconds: float = 0.3
    # 禁止碰撞的机身／臂link接触力模长门槛，N；查4帧物理接触历史，不包括腿link。
    contact_failure_force: float = 2.0
    # 控制创建环境时的附加质量、机器人材质、腿Kp/Kd随机化；不关闭重置位姿扰动或执行器延迟抽样。
    randomization: bool = True
    # 每个环境base附加质量均匀范围，kg；base惯量按质量比缩放，完整机械臂质量仍来自USD。
    added_mass_range: tuple = (0.0, 1.0)
    # 机器人所有材质静摩擦系数的均匀范围；动摩擦=0.75×静摩擦；地面／箱体材质另设0.8/0.6。
    friction_range: tuple = (0.6, 1.0)
    # 腿每关节Kp、Kd各自独立的乘数范围；不改变力矩上限。一次创建后保持，不是每回合重抽。
    motor_scale_range: tuple = (0.9, 1.1)
    # 每回合根位置x扰动，m；以局部默认x=0为中心。
    reset_x_range: tuple = (-0.10, 0.10)
    # 每回合根位置y扰动，m。
    reset_y_range: tuple = (-0.08, 0.08)
    # 每回合根偏航扰动，rad；roll、pitch重置为0。
    reset_yaw_range: tuple = (-0.06, 0.06)
    # 密集奖励权重；乘控制周期dt，终止奖励另算。
    rewards: dict = field(default_factory=lambda: {'goal_velocity': 1.5, 'heading': 0.5, 'progress': 2.0, 'lin_vel_z': -0.5, 'ang_vel_xy': -0.05, 'orientation': -1.0, 'joint_acceleration': -2.5e-07, 'collision': -10.0, 'action_rate': -0.1, 'delta_torques': -1e-07, 'torques': -1e-05, 'hip_position': -0.5, 'joint_error': -0.04, 'feet_stumble': -1.0, 'flight': -1.0, 'arm_error': -5.0, 'joint_limits': -2.0})
    # 额外平面倾斜成本权重；实现时取负号并乘dt。全局orientation成本仍存在。
    flat_stability_weight: float = 4.0
    # 平面超速平方成本权重；同一gate下还将progress上限降到flat_speed_limit。
    flat_speed_weight: float = 2.5
    # 平面水平速度模长参考阈值，m/s；软成本，可超过，且gate关闭时不加此成本。
    flat_speed_limit: float = 0.45
    # 重力投影分量成本的容差角，rad；实现使用sin(此值)，不是直接比较pitch。
    flat_stability_tolerance: float = 0.08
    # 平面roll/pitch角速度超容差平方成本；不处罚yaw角速度。
    flat_angular_velocity_weight: float = 0.3
    # 平面承重足水平世界滑速成本；与全阶段contact_slip在平面可能叠加。
    flat_slip_weight: float = 0.5
    # roll/pitch角速度分量死区，rad/s。
    flat_angular_velocity_tolerance: float = 0.4
    # 承重足世界水平滑速死区，m/s；摆动足不在此成本中。
    flat_slip_tolerance: float = 0.08
    # 滑速超死区后平方前的归一化尺度，m/s；0.33m/s滑速对应单足原始成本1。
    flat_slip_scale: float = 0.25
    # 默认0：自由起步，不等待站稳、不渐放动作。大于0仅用于明确启用的实验。
    startup_stand_seconds: float = 0.0
    # 释放前四脚地面承重、姿态／速度合格必须连续保持的秒数。
    startup_stable_seconds: float = 0.5
    # 达到此秒数仍未满足站稳条件就失败；释放以后不再用此超时。
    startup_timeout: float = 4.5
    # 释放后策略动作与速度命令由0平滑到1所需秒数。
    startup_ramp_seconds: float = 1.2
    # 全程朝世界+X的额外成本权重，公式1-cos(yaw)，起步按gain渐放。
    forward_heading_weight: float = 2.0
    # 实际裁剪后的腿位置目标二阶差分成本权重，按0.1rad归一化并对12轴取均值。
    target_curvature_weight: float = 0.09
    # 跨阶段承重足滑移成本权重；不依赖平面gate，但要求真实承重与正确表面高度。
    contact_slip_weight: float = 0.3
    # 全程中心线偏差成本权重；3cm死区，超出后除0.20m再平方，起步按gain渐放。
    path_deviation_weight: float = 0.3
    # 仅用于日志统计成对离地的宽限时间；不产生奖励或动作门控。
    walking_pair_grace_seconds: float = 0.015
    # 成功一次性加分，直接加在每步密集回报后，不乘dt；成功后立即重置。
    success_bonus: float = 20.0
    # 失败一次性罚分，不乘dt；单纯24秒超时不加这个终止罚分。
    failure_penalty: float = -10.0

    @property
    def control_dt(self):
        return self.physics_dt * self.decimation

    @property
    def finish_x(self):
        return self.box_front+self.finish_offset

    @property
    def route_goal_x(self):
        return self.box_front + self.goal_offset

    def validate(self):
        import math
        if self.num_envs < 1 or self.decimation < 1 or self.physics_dt <= 0:
            raise ValueError("Invalid environment count or timestep")
        if not 0 < self.curriculum_min_height <= self.box_height <= .5:
            raise ValueError("Invalid curriculum height")
        if self.curriculum_levels < 2 or min(self.promote_after,self.demote_after) < 1:
            raise ValueError("Invalid curriculum levels")
        if not (self.front_thigh_min < self.front_thigh_max and self.front_calf_min < self.front_calf_max):
            raise ValueError("Invalid front soft bounds")
        if not (0 < self.rear_thigh_max <= 2.2 and -2.7 <= self.rear_calf_min < self.rear_calf_max <= -.93):
            raise ValueError("Invalid rear workspace")
        if not self.top_margin < self.finish_offset < self.goal_offset < self.box_length-self.top_margin:
            raise ValueError("Approach route must lie inside platform")
        if len(self.arm_pose)!=6 or self.actuator_delay_max < 0:
            raise ValueError("Invalid arm pose or delay")
        if self.spacing <= 2*(self.box_front+self.box_length):
            raise ValueError("Environment spacing too small")
        if not (0 < self.startup_stable_seconds and self.startup_timeout > max(self.startup_stand_seconds,self.startup_stable_seconds)
                and self.startup_timeout < self.episode_seconds):
            raise ValueError("Invalid startup timing")
        for name in ('front_joint_scale','front_pitch_scale','startup_ramp_seconds','traversal_seconds',
                     'traversal_max_tilt','flat_speed_limit',
                     'flat_slip_scale','startup_tilt_tolerance','startup_linear_tolerance','startup_angular_tolerance'):
            if not math.isfinite(getattr(self,name)) or getattr(self,name)<=0:
                raise ValueError(f"{name} must be finite and positive")
        for name,value in vars(self).items():
            if isinstance(value,float) and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            if name.endswith('_weight') and value<0:
                raise ValueError(f"{name} must be nonnegative")

def load_config(path=None):
    data = json.loads(Path(path).read_text()) if path else json.loads((Path(__file__).resolve().parents[6] / "configs/climb30.json").read_text())
    task = TaskConfig(**data.get("task", {}))
    ppo = PPOConfig(**data.get("ppo", {}))
    task.validate()
    ppo.validate()
    return task, ppo


def configuration(task, ppo):
    return {"task": asdict(task), "ppo": asdict(ppo), "upstream_commit": UPSTREAM_COMMIT,
            "implementation_revision": IMPLEMENTATION_REVISION,
            "observation_dimensions": {"proprio": PROPRIO, "scan": SCAN, "explicit": EXPLICIT,
                                       "privileged": PRIVILEGED, "history": HISTORY, "total": OBSERVATIONS},
            "joint_order": JOINT_NAMES, "action_dimension": 18, "learned_action_dimension": 12}



def require_implementation(config):
    """只支持当前版续训；旧训练实现与本版奖励/停止逻辑不兼容。"""
    if config.get("implementation_revision") != IMPLEMENTATION_REVISION:
        raise ValueError("Checkpoint is not from the current CLIMB implementation; start a new run")
