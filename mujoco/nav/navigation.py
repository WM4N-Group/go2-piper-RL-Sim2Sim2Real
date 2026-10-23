"""纯导航决策：无MuJoCo/ROS依赖，仿真和真机使用相同状态机。"""
from dataclasses import asdict, dataclass, field, replace
import numpy as np
from control_profiles import get_profile


def wrap_angle(angle):
    """角误差折回[-pi,pi)，例如179°到-179°只差2°。"""
    return float((angle + np.pi) % (2*np.pi) - np.pi)


@dataclass(frozen=True)
class NavConfig:
    """配置层：米、秒、弧度；指令边界由选定的WBC部署配置校验。"""
    max_speed: float = .50
    min_speed: float = .40
    max_lateral_speed: float = .40
    min_lateral_speed: float = .40
    max_yaw_rate: float = .50
    min_yaw_rate: float = .40
    position_tolerance: float = .13
    yaw_tolerance: float = .25
    position_stop_ratio: float = .5
    yaw_stop_ratio: float = .6
    position_command_deadband: float = .035
    stopped_speed: float = .06
    stopped_yaw_rate: float = .15
    ee_position_tolerance: float = .05
    ee_orientation_tolerance: float = .15
    ee_feedback_gain: float = 1.2
    ee_feedback_limit: float = .08
    arm_stopped_speed: float = .20
    arm_joint_tolerance: float = .10
    max_tilt: float = .35
    hold_seconds: float = 1.
    warmup_seconds: float = 2.
    timeout_seconds: float = 60.
    position_gain: float = 2.
    heading_gain: float = 2.
    turn_in_place_angle: float = .65

    def __post_init__(self):
        values = np.array(list(asdict(self).values()))
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError('All navigation config values must be finite and positive')
        if self.max_speed > 1. or self.max_lateral_speed > 1. or self.max_yaw_rate > .9:
            raise ValueError('Navigation speed exceeds tested WBC deployment bounds')
        if (self.min_speed > self.max_speed or self.min_lateral_speed > self.max_lateral_speed
                or self.min_yaw_rate > self.max_yaw_rate):
            raise ValueError('Minimum command must not exceed maximum command')
        if self.timeout_seconds <= self.warmup_seconds + self.hold_seconds:
            raise ValueError('Timeout must allow warmup and arrival hold')
        if self.position_stop_ratio > 1. or self.yaw_stop_ratio > 1.:
            raise ValueError('Stop ratios must be in (0,1]')


@dataclass
class NavState:
    """状态层：上层只需提供定位、速度、机械臂状态，无MuJoCo依赖。"""
    time: float
    xy: np.ndarray
    yaw: float
    velocity: np.ndarray  # [body_vx,body_vy,world_wz]
    arm_q: np.ndarray
    arm_qd: np.ndarray
    tilt: float
    ee_pose: np.ndarray = field(default_factory=lambda: np.array([0.,0.,0.,1.,0.,0.,0.]))


def profile_nav_config(profile_name, config=None):
    """导航先完成固定姿态PD启动，再在零速下让策略预热。"""
    profile = get_profile(profile_name)
    cfg = config or (NavConfig(max_speed=.6,max_lateral_speed=.4,max_yaw_rate=.9,min_yaw_rate=.8,
                              position_tolerance=.13,yaw_tolerance=.25,turn_in_place_angle=.6,
                              position_stop_ratio=.5,yaw_stop_ratio=.3)
                     if profile_name == 'skills' else NavConfig())
    if np.any(np.array([cfg.max_speed,cfg.max_lateral_speed,cfg.max_yaw_rate])
              > np.array(profile.wbc_velocity_limits)+1e-8):
        raise ValueError('Navigation config exceeds selected control profile velocity limits')
    return replace(cfg, warmup_seconds=max(cfg.warmup_seconds,
                   profile.startup_pd_seconds+profile.policy_warmup_seconds))


def pose_error(actual, target):
    """位置误差(m)与四元数最短角误差(rad)，q与-q表示同一姿态。"""
    position = float(np.linalg.norm(actual[:3]-target[:3]))
    dot = abs(float(np.dot(actual[3:], target[3:])))
    return position, float(2*np.arccos(np.clip(dot, 0., 1.)))


def effective_velocity(error, gain, minimum, maximum, deadband):
    """死区内为零；死区外使用带最低幅值的比例速度，不添加漂移补偿。"""
    if abs(error) <= deadband:
        return 0.
    return float(np.copysign(np.clip(abs(gain*error), minimum, maximum), error))


class NavSkill:
    """决策层：update(state)返回[vx,vy,wz]；arrived是可撤销的到达状态。

    先面朝目标位置，再前进，到点后调整最终朝向；最低有效速度避免原地踏步。
    """
    def __init__(self, goal_xy, goal_yaw, config=None, arm_pose_target=None, arm_zero=False):
        self.arm_zero = bool(arm_zero)
        self.config = config or NavConfig()
        self.goal = np.asarray(goal_xy, dtype=float)
        self.goal_yaw = wrap_angle(goal_yaw)
        self.arm_pose_target = np.asarray(arm_pose_target if arm_pose_target is not None
                                         else [0.,0.,0.,1.,0.,0.,0.], dtype=float)
        if (self.arm_pose_target.shape != (7,) or not np.isfinite(self.arm_pose_target).all()
                or np.linalg.norm(self.arm_pose_target[3:]) < 1e-8):
            raise ValueError('Arm target must be a finite XYZ+wxyz pose')
        self.arm_pose_target[3:] /= np.linalg.norm(self.arm_pose_target[3:])
        if self.goal.shape != (2,) or not np.isfinite(self.goal).all() or not np.isfinite(goal_yaw):
            raise ValueError('Goal must be finite world x,y and yaw')
        self.phase = 'warmup'
        self.arrived = False
        self.hold_started = None
        self.hold_elapsed = 0.
        self.distance = self.yaw_error = 0.
        self.position_reached = self.yaw_reached = False

    def update(self, state):
        cfg = self.config
        self.distance = float(np.linalg.norm(self.goal-state.xy))
        self.yaw_error = wrap_angle(self.goal_yaw-state.yaw)
        if state.time < cfg.warmup_seconds:
            self.phase = 'warmup'
            return np.zeros(3)

        command = np.zeros(3)
        was_position_reached = self.position_reached
        if self.distance > cfg.position_tolerance:
            self.position_reached = False
        elif self.distance <= cfg.position_tolerance*cfg.position_stop_ratio:
            self.position_reached = True
        if not self.position_reached:
            # 路径朝向只由目标位置决定，最终朝向留到到点后处理。
            delta = self.goal-state.xy
            bearing_error = wrap_angle(np.arctan2(delta[1], delta[0])-state.yaw)
            if self.phase != 'drive':
                facing = abs(bearing_error) <= cfg.yaw_tolerance*cfg.yaw_stop_ratio
            else:
                facing = abs(bearing_error) <= cfg.turn_in_place_angle
            self.phase = 'drive' if facing else 'face_target'
            if facing:
                command[0] = effective_velocity(self.distance,cfg.position_gain,cfg.min_speed,
                                                 cfg.max_speed,cfg.position_command_deadband)
            command[2] = effective_velocity(bearing_error,cfg.heading_gain,cfg.min_yaw_rate,
                                             cfg.max_yaw_rate,cfg.yaw_tolerance*cfg.yaw_stop_ratio)
            self.yaw_reached = False
        else:
            if abs(self.yaw_error) > cfg.yaw_tolerance or not was_position_reached:
                self.yaw_reached = False
            if abs(self.yaw_error) <= cfg.yaw_tolerance*cfg.yaw_stop_ratio:
                self.yaw_reached = True
            if not self.yaw_reached:
                command[2] = effective_velocity(self.yaw_error,cfg.heading_gain,cfg.min_yaw_rate,
                                                 cfg.max_yaw_rate,cfg.yaw_tolerance*cfg.yaw_stop_ratio/2)
            self.phase = 'align' if command[2] else 'settle'
        self.observe(state)
        return command

    def stability_checks(self, state):
        """分别报告目标精度与身体停稳，避免把角度略越界称为失稳。"""
        cfg = self.config
        ee_distance, ee_angle = pose_error(state.ee_pose, self.arm_pose_target)
        checks = dict(position=bool(np.linalg.norm(self.goal-state.xy) <= cfg.position_tolerance),
                    yaw=bool(abs(wrap_angle(self.goal_yaw-state.yaw)) <= cfg.yaw_tolerance),
                    planar_speed=bool(np.linalg.norm(state.velocity[:2]) <= cfg.stopped_speed),
                    yaw_rate=bool(abs(state.velocity[2]) <= cfg.stopped_yaw_rate),
                    arm_position=bool(ee_distance <= cfg.ee_position_tolerance),
                    arm_orientation=bool(ee_angle <= cfg.ee_orientation_tolerance),
                    arm_speed=bool(np.max(abs(state.arm_qd)) <= cfg.arm_stopped_speed),
                    tilt=bool(state.tilt <= cfg.max_tilt),
                    zero_command_phase=self.phase in ('settle','arrived'))
        if self.arm_zero:
            # Joint-PD mode accepts actual joint angles, not an unrelated EE pose.
            checks.pop('arm_position')
            checks.pop('arm_orientation')
            checks['arm_joints'] = bool(np.max(abs(state.arm_q)) <= cfg.arm_joint_tolerance)
        return checks

    def observe(self, state):
        """每个物理步核验停稳，不遗漏两次命令更新之间的速度峰值。"""
        cfg = self.config
        self.distance = float(np.linalg.norm(self.goal-state.xy))
        self.yaw_error = wrap_angle(self.goal_yaw-state.yaw)
        # 到达必须已给出零速命令，且实际身体/机械臂均稳定。
        stable = all(self.stability_checks(state).values())
        if stable:
            if self.hold_started is None:
                self.hold_started = state.time
            self.hold_elapsed = state.time-self.hold_started
            if self.hold_elapsed >= cfg.hold_seconds-1e-8:
                self.phase = 'arrived'
                self.arrived = True
        else:
            self.hold_started = None
            self.hold_elapsed = 0.
            self.arrived = False
            if self.phase == 'arrived':
                self.phase = 'settle'


