"""All task and learning parameters; distances in m, angles in rad, time in s."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from .agents.ppo_cfg import PPOConfig

IMPLEMENTATION_REVISION = "climb_skill_v3_forward_ascent"
FLAT_STABILITY_REVISION = "climb_skill_v3_flat_posture_candidate"
FLAT_SPEED_REVISION = "climb_skill_v3_flat_posture_speed_candidate"
FLAT_DAMPING_REVISION = "climb_skill_v3_flat_damping_slip_candidate"
STARTUP_REVISION = "climb_skill_v3_standing_start_candidate"
GAIT_HEADING_REVISION = "climb_skill_v3_forward_heading_gait_candidate"
STRONG_HEADING_REVISION = "climb_skill_v3_heading_strong_no_edge_candidate"
FLAT_WALK_REVISION = "climb_skill_v3_flat_walk_straight_candidate"
FORWARD_RECOVERY_REVISION = "climb_skill_v3_forward_recovery_candidate"
DIAGONAL_GAIT_REVISION = "climb_skill_v3_terrain_diagonal_gait_candidate"
WALKING_REFINEMENT_REVISION = "climb_skill_v3_airborne_speed_swing_candidate"

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
    curriculum_only_enabled: bool = False  # 保留model_800/v2奖励与跨步检测，仅改变课程资格
    quality_window_enabled: bool = False
    quality_window_size: int = 5
    quality_window_required: int = 3
    crossing_unsafe_seconds: float = 0.08
    crossing_commit_distance: float = 0.02
    crossing_quality_enabled: bool = False
    crossing_intent_height: float = 0.065
    crossing_intent_ratio: float = 0.6
    crossing_intent_distance: float = 0.08
    crossing_takeoff_min: float = 0.03
    crossing_takeoff_max: float = 0.38
    crossing_clearance_min: float = 0.005
    crossing_return_seconds: float = 0.06
    crossing_wall_seconds: float = 0.08
    crossing_timeout: float = 1.5
    crossing_failure_penalty: float = 0.5
    crossing_guidance_weight: float = 0.5
    crossing_reference_weight: float = 1.0
    # 独立候选默认关闭；恢复版沿用原课程。距离m、时间s、成本0..1。
    approach_quality_enabled: bool = False
    rear_boundary_x: float = -0.5
    gait_ground_seconds: float = 0.8
    gait_top_seconds: float = 0.4
    gait_mean_cost_max: float = 0.35
    gait_leg_cost_max: float = 0.45
    gait_frame_cost_max: float = 0.45
    gait_good_fraction_min: float = 0.7
    gait_speed_min: float = 0.15
    gait_speed_max: float = 0.65
    front_clearance_weight: float = 0.5
    front_clearance_distance: float = 0.22
    front_clearance_margin: float = 0.03
    front_clearance_scale: float = 0.08
    front_landing_bonus: float = 0.5
    front_landing_seconds: float = 0.08
    rear_workspace_enabled: bool = False  # 新候选的目标工作范围；旧模型默认关闭
    rear_thigh_max: float = 1.8  # rad，限制大腿目标过度前折；实际角仍可有PD动态超调
    rear_calf_min: float = -2.5  # rad，避免把后膝目标压到极端折叠
    rear_calf_max: float = -1.05  # rad，避免后膝长期近伸直拖行
    amp_body_gate: bool = False  # 新候选：名义机身覆盖面判地形，不受异常脚位置影响
    amp_enabled: bool = False  # 只影响训练奖励，推理不需要数据或判别器
    # 全局随机种子；Isaac环境创建时播种。种子相同不保证GPU物理逐位一致。
    seed: int = 1
    # 同时模拟的独立机器人／箱体数量；不是训练回合数。JSON覆盖类默认256。
    num_envs: int = 256
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
    box_height: float = 0.20
    # 箱体前沿局部x，m；末沿=box_front+box_length=3.15m。
    box_front: float = 0.75
    # 按每个环境独立的成功／失败序列调节实际箱高；评估脚本强制关闭。
    curriculum: bool = True
    # 课程最低露出地面高度，m；机器人始终从地面开始。
    curriculum_min_height: float = 0.05
    # 高度级数；0..6共7级，间隔2.5cm。
    curriculum_levels: int = 7
    # Success-driven per-environment curriculum; never inject an elevated robot start.
    # 本环境连续成功达到该次数升一级；升级后清成功计数，封顶20cm。
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
    # 完成线相对箱前沿的距离，m；当前finish_x=0.75+1.55=2.30m。
    finish_offset: float = 1.2
    # 前进路点相对箱前沿的距离，m；当前route_goal_x=2.75m，在完成线之后。
    goal_offset: float = 2.0
    # 四脚安全几何、近期承重与朝向／横向条件需连续成立的秒数；不是全程四脚同时着地。
    traversal_seconds: float = 0.3
    # 每脚最近一次真实台面承重的最大允许年龄，s；摆动脚可短暂不接触。
    top_contact_memory: float = 0.75

    # 提交成功那一刻的机身总倾角上限，rad；不是各欧拉角分别小于此值。
    traversal_max_tilt: float = 0.30
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
    # 18个基础密集项的权重字典；直接替换整个默认字典，不是逐项合并。完整公式见奖励章节。
    rewards: dict = field(default_factory=lambda: {
        "goal_velocity": 1.5, "heading": 0.5, "progress": 2.0,
        "lin_vel_z": -0.5, "ang_vel_xy": -0.05, "orientation": -1.0,
        "joint_acceleration": -2.5e-7, "collision": -10.0,
        "action_rate": -0.1, "delta_torques": -1e-7, "torques": -1e-5,
        "hip_position": -0.5, "joint_error": -0.04,
        "feet_stumble": -1.0, "feet_edge": -1.0,
        "flight": -1.0, "arm_error": -5.0, "joint_limits": -2.0,
    })
    # Optional flat-surface refinements. Both zero reproduce the original v3 rewards exactly.
    # 额外平面倾斜成本权重；实现时取负号并乘dt。全局orientation成本仍存在。
    flat_stability_weight: float = 0.0
    # 平面超速平方成本权重；同一gate下还将progress上限降到flat_speed_limit。
    flat_speed_weight: float = 0.0
    # 平面水平速度模长参考阈值，m/s；软成本，可超过，且gate关闭时不加此成本。
    flat_speed_limit: float = 0.6
    # 旧边沿距离门槛，m；当前flat_ignore_edge_distance=True时不使用。
    flat_stability_margin: float = 0.20
    # 旧边沿距离平滑带宽，m；当前被忽略，但保留以兼容旧配置。
    flat_stability_blend_width: float = 0.10
    # 重力投影分量成本的容差角，rad；实现使用sin(此值)，不是直接比较pitch。
    flat_stability_tolerance: float = 0.08
    # 平面roll/pitch角速度超容差平方成本；不处罚yaw角速度。
    flat_angular_velocity_weight: float = 0.0
    # 平面承重足水平世界滑速成本；与全阶段contact_slip在平面可能叠加。
    flat_slip_weight: float = 0.0
    # roll/pitch角速度分量死区，rad/s。
    flat_angular_velocity_tolerance: float = 0.4
    # 承重足世界水平滑速死区，m/s；摆动足不在此成本中。
    flat_slip_tolerance: float = 0.08
    # 滑速超死区后平方前的归一化尺度，m/s；0.33m/s滑速对应单足原始成本1。
    flat_slip_scale: float = 0.25
    # 起步至少经过此秒数才允许释放策略；不是固定睡眠，不稳定时继续等。
    startup_stand_seconds: float = 0.0
    # 释放前四脚地面承重、姿态／速度合格必须连续保持的秒数。
    startup_stable_seconds: float = 0.3
    # 达到此秒数仍未满足站稳条件就失败；释放以后不再用此超时。
    startup_timeout: float = 3.0
    # 释放后策略动作与速度命令由0线性到1所需秒数。
    startup_ramp_seconds: float = 0.8
    # 全程朝世界+X的额外成本权重，公式1-cos(yaw)，起步按gain渐放。
    forward_heading_weight: float = 0.0
    # 连续登箱确认要求的绝对偏航容差，rad；当前10度。0表示关闭朝向与横向完成条件。
    traversal_heading_tolerance: float = 0.0
    # 连续登箱确认要求的中心线误差上限，m；当前|y|<=0.2。
    traversal_lateral_tolerance: float = 0.2
    # 实际裁剪后的腿位置目标二阶差分成本权重，按0.1rad归一化并对12轴取均值。
    target_curvature_weight: float = 0.0
    # 跨阶段承重足滑移成本权重；不依赖平面gate，但要求真实承重与正确表面高度。
    contact_slip_weight: float = 0.0
    # 旧距离门控是否额外查询机身XY；当前ignore_edge_distance分支提前返回，此字段不影响当前gate。
    flat_use_body_gate: bool = False
    # 当前True：取消20～30cm距离门槛；仍要求同一平面、脚不低于台面和至少两脚承重。
    flat_ignore_edge_distance: bool = False
    # 启用几何平面步态分支和ContactSensor接触／腾空计时；不等于强制某个步态。
    flat_walking_enabled: bool = False
    # 旧分支的启用高度；refinement对角分支则在此达到全量权重，低课程已有early_gain。
    flat_walk_start_height: float = 0.0
    # 当前False：不替换恢复后的原速度奖励；True才启用旧指数速度跟踪替换。
    flat_walk_velocity_tracking: bool = True
    # 全程中心线偏差成本权重；3cm死区，超出后除0.20m再平方，起步按gain渐放。
    path_deviation_weight: float = 0.0
    # 平面额外四脚腾空成本，叠加原全局flight；按课程门槛与startup gain启用。
    flat_walk_flight_weight: float = 6.0
    # 当前0，额外世界竖直速度平方成本不参与回报；全局机身系lin_vel_z仍有效。
    flat_walk_vertical_weight: float = 2.0
    # 当前0，历史腾空／接触时间方差成本不参与回报；传感器仍会更新计时。
    flat_walk_air_variance_weight: float = 1.5
    # 当前0，单足连续腾空超0.5s平方成本不参与回报。
    flat_walk_long_air_weight: float = 1.0
    # 当前0，对角腿关节偏移相等成本不参与回报；新步态用接触时序，不用此项强制前后腿同角。
    flat_walk_mirror_weight: float = 0.15
    # Optional contact-timing gait, no clock or observation/action contract change.
    # 当前True，增加3项软接触时序成本；不改动作、不接管落脚、不保证硬性固定小跑。
    diagonal_gait_enabled: bool = False
    # 前两脚或后两脚同时腾空均超宽容时间的成本权重；四脚腾空也计入，原始成本上限1。
    diagonal_pair_weight: float = 1.5
    # 同组对角腿一脚腾空、一脚支撑且两种状态均超宽容时间的成本；两组取均值。
    diagonal_sync_weight: float = 0.5
    # 单脚持续支撑／腾空过久的渐增成本权重；防止长期不换步，四脚平均且上限1。
    diagonal_duration_weight: float = 0.25
    # 离地和落地状态的宽容时间，s；允许短暂三／四脚支撑与对角落脚先后。
    diagonal_transfer_seconds: float = 0.06
    # 连续接触超此秒数才开始软罚；再超0.25s达到单足上限，不是硬切腿时刻。
    diagonal_max_stance_seconds: float = 0.5
    # 连续腾空超此秒数才开始软罚；再超0.20s达到单足上限。
    diagonal_max_swing_seconds: float = 0.35
    # 新候选专用开关；False保留旧checkpoint的奖励计算，不暗改旧版本。
    walking_refinement_enabled: bool = False
    # 最低课程的步态权重比例，线性升到flat_walk_start_height处的1.0。
    walking_early_gain: float = 0.25
    # 成对离地单独使用更短宽限；对角同步仍使用原diagonal_transfer_seconds。
    walking_pair_grace_seconds: float = 0.015
    # 两脚均离地超过宽限后，在此时长内把pair成本平滑升到1。
    walking_pair_ramp_seconds: float = 0.03
    # 平面摆脚高度带成本，逐足平均、上限1；不奖励关节功或猛蹬地。
    walking_clearance_weight: float = 0.3
    # 脚底离当前平面高度带，m；只在成熟摆动中作用，不约束登箱跨高差。
    walking_clearance_min: float = 0.025
    walking_clearance_max: float = 0.06
    # 高度误差除以此长度再平方并封顶；摆动前60ms不罚，再经60ms逐渐放开。
    walking_clearance_scale: float = 0.04
    # 当前False：不启用归一化偏航、横向速度与转向速度跟踪，也不把heading观测改为固定-yaw。
    straight_tracking_enabled: bool = False
    # 分支关闭，当前不生效；旧项按10度将1-cos(yaw)归一化。
    straight_heading_weight: float = 0.5
    # 分支关闭，当前不生效；当前中心线成本由独立path_deviation_weight控制。
    straight_path_weight: float = 1.0
    # 分支关闭，当前不生效；旧项跟踪clip(-y,-0.2,0.2)的横向速度。
    straight_lateral_velocity_weight: float = 1.0
    # 分支关闭，当前不生效；旧项跟踪clip(-1.5*yaw,-0.6,0.6)的偏航角速度。
    straight_yaw_rate_weight: float = 0.3
    # 成功一次性加分，直接加在每步密集回报后，不乘dt；成功后立即重置。
    success_bonus: float = 20.0
    # 失败一次性罚分，不乘dt；单纯24秒超时不加这个终止罚分。
    failure_penalty: float = -10.0

    @property
    def finish_x(self):
        return self.box_front + self.finish_offset

    @property
    def route_goal_x(self):
        return self.box_front + self.goal_offset

    def validate(self):
        if self.curriculum_only_enabled and not self.quality_window_enabled:
            raise ValueError('Curriculum-only candidate requires quality window')
        if self.quality_window_enabled:
            if not self.crossing_quality_enabled:
                raise ValueError('Window requires crossing quality')
            if not isinstance(self.quality_window_size, int) or not isinstance(self.quality_window_required, int) or not 1 <= self.quality_window_required <= self.quality_window_size:
                raise ValueError('Invalid quality window')
            if not 0 < self.crossing_unsafe_seconds < float('inf') or not 0 < self.crossing_commit_distance < self.crossing_intent_distance:
                raise ValueError('Invalid crossing confirmation')
        if self.crossing_quality_enabled:
            import math
            if not (self.approach_quality_enabled and self.amp_enabled):
                raise ValueError('Crossing quality requires approach quality and AMP')
            values = (self.crossing_intent_height, self.crossing_intent_ratio, self.crossing_intent_distance,
                      self.crossing_takeoff_min, self.crossing_takeoff_max,
                      self.crossing_clearance_min, self.crossing_return_seconds,
                      self.crossing_wall_seconds, self.crossing_timeout)
            if not all(math.isfinite(x) and x > 0 for x in values):
                raise ValueError('Crossing geometry/timers must be finite and positive')
            if self.crossing_takeoff_min >= self.crossing_takeoff_max or self.crossing_intent_ratio > 1:
                raise ValueError('Invalid crossing takeoff band or intent ratio')
            if not all(math.isfinite(x) and x >= 0 for x in (self.crossing_failure_penalty,
                       self.crossing_guidance_weight, self.crossing_reference_weight)):
                raise ValueError('Crossing weights must be finite and nonnegative')
        if self.approach_quality_enabled:
            import math
            if not self.amp_body_gate:
                raise ValueError('Approach quality requires AMP reference candidate')
            positive = (self.gait_ground_seconds, self.gait_top_seconds, self.front_clearance_distance,
                        self.front_clearance_margin, self.front_clearance_scale, self.front_landing_seconds)
            if not all(math.isfinite(x) and x > 0 for x in positive):
                raise ValueError('Quality lengths and durations must be finite and positive')
            for x in (self.gait_mean_cost_max, self.gait_leg_cost_max, self.gait_frame_cost_max, self.gait_good_fraction_min):
                if not math.isfinite(x) or not 0 < x < 1:
                    raise ValueError('Quality costs and fraction must be in (0, 1)')
            if not 0 < self.gait_speed_min < self.gait_speed_max < float('inf'):
                raise ValueError('Invalid gait speed band')
            if not all(math.isfinite(x) and x >= 0 for x in (self.front_clearance_weight, self.front_landing_bonus)):
                raise ValueError('Front guidance weights must be nonnegative')
            if not (math.isfinite(self.rear_boundary_x) and self.rear_boundary_x < self.reset_x_range[0]
                    < self.reset_x_range[1] < self.box_front - .45):
                raise ValueError('Approach starts must fit behind box and inside rear boundary')
        if self.rear_workspace_enabled:
            import math
            if not self.amp_body_gate:
                raise ValueError("Rear workspace belongs to new AMP reference candidate")
            if not all(math.isfinite(x) for x in (self.rear_thigh_max, self.rear_calf_min, self.rear_calf_max)):
                raise ValueError("Rear workspace must be finite")
            if not (0 < self.rear_thigh_max <= 2.2 and -2.7 <= self.rear_calf_min < self.rear_calf_max <= -.93):
                raise ValueError("Invalid rear target workspace")
        if self.amp_body_gate and not self.amp_enabled:
            raise ValueError("Body-gated reference candidate requires AMP")
        if self.amp_enabled and not self.walking_refinement_enabled:
            raise ValueError("AMP candidate requires geometric walking-refinement gates")
        import math
        if self.walking_refinement_enabled and not (self.diagonal_gait_enabled and self.flat_walking_enabled):
            raise ValueError("Walking refinement requires diagonal gait and contact timers")
        if not math.isfinite(self.walking_early_gain) or not 0 < self.walking_early_gain <= 1:
            raise ValueError("Walking early gain must be in (0, 1]")
        positive = (self.walking_pair_grace_seconds, self.walking_pair_ramp_seconds,
                    self.walking_clearance_min, self.walking_clearance_max, self.walking_clearance_scale)
        if not all(math.isfinite(v) and v > 0 for v in positive):
            raise ValueError("Walking refinement durations and lengths must be finite and positive")
        if self.walking_clearance_max <= self.walking_clearance_min:
            raise ValueError("Walking clearance max must exceed min")
        if not math.isfinite(self.walking_clearance_weight) or self.walking_clearance_weight < 0:
            raise ValueError("Walking clearance weight must be finite and nonnegative")
        diagonal_weights = (self.diagonal_pair_weight, self.diagonal_sync_weight,
                            self.diagonal_duration_weight)
        if not all(math.isfinite(v) and v >= 0 for v in diagonal_weights):
            raise ValueError("Diagonal gait weights must be finite and nonnegative")
        times = (self.diagonal_transfer_seconds, self.diagonal_max_stance_seconds,
                 self.diagonal_max_swing_seconds)
        if not all(math.isfinite(v) and v > 0 for v in times) or min(times[1:]) <= times[0]:
            raise ValueError("Diagonal gait durations must exceed a positive transfer window")
        if self.diagonal_gait_enabled and not self.flat_walking_enabled:
            raise ValueError("Diagonal gait requires flat walking contact timers")
        # Checkpoint videos can lower box_height below this threshold. In that
        # case quality costs simply stay off; recording must remain valid.
        if not math.isfinite(self.flat_walk_start_height) or not 0 <= self.flat_walk_start_height <= .5:
            raise ValueError("Walking quality start height must be in [0, .5] m")
        if not math.isfinite(self.path_deviation_weight) or self.path_deviation_weight < 0:
            raise ValueError("Path deviation weight must be nonnegative")
        walk_weights = (self.flat_walk_flight_weight, self.flat_walk_vertical_weight,
            self.flat_walk_air_variance_weight, self.flat_walk_long_air_weight, self.flat_walk_mirror_weight,
            self.straight_heading_weight, self.straight_path_weight,
            self.straight_lateral_velocity_weight, self.straight_yaw_rate_weight)
        if not all(math.isfinite(v) and v >= 0 for v in walk_weights):
            raise ValueError("Invalid flat walking/straight tracking weights")
        gait = (self.forward_heading_weight, self.traversal_heading_tolerance,
                self.traversal_lateral_tolerance, self.target_curvature_weight, self.contact_slip_weight)
        if not all(math.isfinite(v) and v >= 0 for v in gait):
            raise ValueError("Invalid heading/gait parameters")
        if self.traversal_heading_tolerance > .5 or self.traversal_lateral_tolerance <= 0:
            raise ValueError("Invalid forward traversal tolerances")
        startup = (self.startup_stand_seconds, self.startup_stable_seconds,
                   self.startup_timeout, self.startup_ramp_seconds)
        if not all(math.isfinite(v) and v >= 0 for v in startup):
            raise ValueError("Invalid startup timing")
        if self.startup_stand_seconds > 0 and (self.startup_stable_seconds <= 0
                or self.startup_timeout <= max(self.startup_stand_seconds, self.startup_stable_seconds)
                or self.startup_timeout >= self.episode_seconds or self.startup_ramp_seconds <= 0):
            raise ValueError("Startup needs a positive stability window/ramp and sufficient timeout")
        refinements = (self.flat_angular_velocity_weight, self.flat_slip_weight,
                       self.flat_angular_velocity_tolerance, self.flat_slip_tolerance,
                       self.flat_slip_scale)
        if not all(math.isfinite(v) and v >= 0 for v in refinements) or self.flat_slip_scale == 0:
            raise ValueError("Invalid optional flat damping/slip parameters")
        if self.flat_speed_weight < 0 or self.flat_speed_limit <= 0:
            raise ValueError("Flat speed weight must be nonnegative and limit positive")
        if self.flat_stability_weight < 0 or self.flat_stability_margin < 0 or self.flat_stability_blend_width <= 0:
            raise ValueError("Invalid optional flat posture parameters")
        if not 0 <= self.flat_stability_tolerance < 0.5:
            raise ValueError("Flat posture tolerance must be in [0, .5) radians")
        if self.num_envs < 1 or self.decimation < 1 or self.physics_dt <= 0:
            raise ValueError("Invalid environment count or simulation timestep")
        if not 0 < self.curriculum_min_height <= self.box_height <= 0.5:
            raise ValueError("Require 0 < curriculum_min_height <= box_height <= 0.5 m")
        if self.curriculum_levels < 2 or min(self.promote_after, self.demote_after) < 1:
            raise ValueError("Invalid curriculum")
        if len(self.arm_pose) != 6 or self.actuator_delay_max < 0:
            raise ValueError("arm_pose must contain six angles; delay must be nonnegative")
        if min(self.box_length, self.box_width) <= 2 * self.top_margin:
            raise ValueError("Box has no safe top surface")
        if self.spacing <= 2 * (self.box_front + self.box_length):
            raise ValueError("Environment spacing is too small for independent boxes")
        if not 0 < self.traversal_seconds < self.episode_seconds:
            raise ValueError("Episode must exceed the positive traversal confirmation time")
        if not self.top_margin < self.finish_offset < self.goal_offset < self.box_length - self.top_margin:
            raise ValueError("Finish and forward goal must lie in order inside the safe platform")
        if self.top_contact_memory <= 0 or self.approach_speed <= 0:
            raise ValueError("Contact memory and approach speed must be positive")




def load_config(path=None):
    if path is None:
        root = Path(__file__).resolve().parents[6]
        path = root / json.loads((root / "VERSION.json").read_text())["config"]
    data = json.loads(Path(path).read_text())
    task = TaskConfig(**data.get("task", {}))
    ppo = PPOConfig(**data.get("ppo", {}))
    task.validate()
    ppo.validate()
    return task, ppo


def configuration(task, ppo):
    return {"task": asdict(task), "ppo": asdict(ppo), "upstream_commit": UPSTREAM_COMMIT,
            "implementation_revision": task_revision(asdict(task)),
            "observation_dimensions": {"proprio": PROPRIO, "scan": SCAN, "explicit": EXPLICIT,
                                       "privileged": PRIVILEGED, "history": HISTORY, "total": OBSERVATIONS},
            "joint_order": JOINT_NAMES, "action_dimension": 18, "learned_action_dimension": 12}



def reward_revision(posture_weight, speed_weight, angular_weight=0.0, slip_weight=0.0, startup_seconds=0.0):
    if startup_seconds > 0:
        return STARTUP_REVISION
    if angular_weight > 0 or slip_weight > 0:
        return FLAT_DAMPING_REVISION
    if speed_weight > 0:
        return FLAT_SPEED_REVISION
    return FLAT_STABILITY_REVISION if posture_weight > 0 else IMPLEMENTATION_REVISION


def task_revision(task):
    if task.get('curriculum_only_enabled', False):
        return 'climb_skill_v3_model800_curriculum_v4'
    if task.get('quality_window_enabled', False):
        return 'climb_skill_v3_quality_window_v3'
    if task.get('crossing_quality_enabled', False):
        return 'climb_skill_v3_foot_crossing_quality_v2'
    if task.get('approach_quality_enabled', False):
        return 'climb_skill_v3_approach_gait_curriculum_candidate'
    if task.get("amp_body_gate", False):
        return "climb_skill_v3_amp_reference_balance_candidate"
    if task.get("amp_enabled", False):
        return "climb_skill_v3_flat_amp_candidate"
    if task.get('walking_refinement_enabled', False):
        return WALKING_REFINEMENT_REVISION
    if task.get('diagonal_gait_enabled', False):
        return DIAGONAL_GAIT_REVISION
    if (task.get('flat_walk_start_height', 0.) > 0 or not task.get('flat_walk_velocity_tracking', True)
            or task.get('path_deviation_weight', 0.) > 0):
        return FORWARD_RECOVERY_REVISION
    if task.get('flat_walking_enabled', False) or task.get('straight_tracking_enabled', False):
        return FLAT_WALK_REVISION
    if task.get('flat_ignore_edge_distance', False):
        return STRONG_HEADING_REVISION
    if any(task.get(k, 0) for k in ('forward_heading_weight', 'traversal_heading_tolerance',
                                  'target_curvature_weight', 'contact_slip_weight', 'flat_use_body_gate')):
        return GAIT_HEADING_REVISION
    return reward_revision(task.get('flat_stability_weight', 0.), task.get('flat_speed_weight', 0.),
        task.get('flat_angular_velocity_weight', 0.), task.get('flat_slip_weight', 0.),
        task.get('startup_stand_seconds', 0.))


def require_implementation(config):
    """A new task contract: old standing-task checkpoints cannot silently resume here."""
    task = config.get("task", {})
    expected = task_revision(task)
    if config.get("implementation_revision") != expected:
        raise ValueError("Checkpoint task differs from its declared v3 reward contract. Start a matching run; "
                         "replay older checkpoints with their archived matching source.")
