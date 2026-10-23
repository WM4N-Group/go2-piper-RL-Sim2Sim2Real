# GO2-PIPER 底层策略交接包

> 2026-10-14交接注：本目录保留2026-09的冻结策略与历史验收，下面的“当前/接受版本”均指本包版本。NAV仍作为冻结参考使用；PUSH与CLIMB已在包外发展出新控制路径，最新版本分别见[当前PUSH](../../docs/PUSH_CURRENT_HANDOFF_CN.md)和[当前CLIMB](../../docs/CLIMB_CRAWL_STATUS_20261001_CN.md)，接收清单见[总交接](../../docs/AGENT_HANDOFF_CN.md)。旧253维CLIMB actor不等于最新逐脚控制器，旧PUSH不能替代v212的226→19残差actor、独立冻结腿hook和配套控制器。文件完整性以包内`SHA256SUMS`核对。单独分发本包时需同时提供主仓库当前docs；相对链接依赖仓库目录结构。 新小组当前主线是技能平稳切换；开发候选尚未成为统一SDK，按主仓库项目计划继续，不从本包旧成功率推断新版本状态。

生成日期：2026-09-18

目标：只交接 GO2-PIPER 的 NAV、PUSH、CLIMB 底层策略及其消费契约，供后续小组完成硬件适配和 Sim-to-Real。
## 1. 当前放行状态

三份策略已经完成 Isaac 原生阶段验收，但**尚未完成实机验收**。NAV 已通过 MuJoCo 平地目标导航；PUSH 和 CLIMB 的接触丰富 MuJoCo 迁移仍未达到放行门槛。因此，本包是 Sim-to-Real 输入，不是可直接给实机上电运行的发布包。

| 技能 | 权重 | 输入 | 输出 | 当前证据 |
| --- | --- | ---: | ---: | --- |
| NAV | `policies/nav/policy.pt` | 210 | 18 | MuJoCo 随机目标 98/100；未实机验证 |
| PUSH | `policies/push/policy.pt` | 226 | 12 | Isaac 原生 31/32、30/32；MuJoCo 未放行 |
| CLIMB | `policies/climb/policy.pt` | 253 | 18 | Isaac 原生 30/32、32/32；MuJoCo 未放行 |

不要混用三份 actor 的输入维度、观测顺序或动作后处理。

2026-09-23 增量说明：主仓库独立的 SAFE_BASE 腿部 checkpoint 在安全臂姿态、零初速
Isaac 定时保持任务上完成四组 `32/32`（每回合 12 s）；它没有验证从 SAFE_APPROACH
到 SAFE_BASE 的切换，也没有验证 PRECONTACT、有效推箱或 MuJoCo。它不在本交接包的
`policies/`、`PACKAGE_MANIFEST.json` 或 `SHA256SUMS` 中。这里的 PUSH `policy.pt` 仍是
冻结的旧 actor，不得把 SAFE_BASE 的定时保持结果当作该 actor 的新验收或实机许可。

策略关节顺序为 `FR, FL, RR, RL` 四条腿各自的 `hip, thigh, calf`，随后是 `joint1` 至 `joint6`。MuJoCo 模型顺序是 `FL, FR, RL, RR` 后接六个臂关节；`PACKAGE_MANIFEST.json` 同时列出两种完整顺序，适配层必须显式重排。

## 2. 策略消费契约

### NAV

- 210 维输入是 3 帧历史观测。
- 排列方式是按观测项分组后跨 3 帧拼接，不是把三个 70 维整帧直接首尾相接：`base_ang_vel(9), projected_gravity(9), joint_pos(54), joint_vel(54), last_action(54), velocity_command(9), ee_command(21)`。
- 每个分组内部按旧帧到新帧排列；关节状态和动作使用上述策略关节顺序。
- 18 维输出对应 12 个 Go2 腿关节和 6 个 PIPER 关节的位置动作。
- 使用 `config/nav_deploy.yaml` 中的默认角、动作缩放、PD 增益、仿真步长和控制降采样配置作为来源参考。
- 实机必须重新核验控制频率、关节顺序、位置零点、方向、限位、延迟和力矩饱和。

### PUSH

- 226 维输入由 210 维历史策略观测与 16 维箱体/控制器状态组成。
- 前 210 维历史采用与 NAV 相同的按观测项跨帧排列；末尾 16 维依次是 `box_position_b(3), box_velocity_b(3), box_goal_delta_b(3), box_heading_b_xy(2), box_size(3), arm_locked(1), valid_hand_contact(1)`。
- actor 只输出 12 个腿部动作。
- 6 个机械臂目标必须由匹配的 `PushArmIK` / `BoxPushLegAction` 控制路径生成，并将实际施加的 18 维组合命令写入动作历史。
- 接受版本要求末端向下倾角 `0.8 rad`、预接近距离 `0.03 m`、压入深度 `0.02 m`、接触后锁臂，控制周期 `0.02 s`。
- 不能把该 actor 接入旧的 210 维纯策略运行时，也不能把 12 维输出直接当成完整机器人命令。

### CLIMB

- 253 维输入排列为 `base_linear_velocity_b(3), base_angular_velocity_b(3), projected_gravity(3), velocity_command(3), joint_pos(18), joint_vel(18), last_action(18), height_scan(187)`；CLIMB 当前不是三帧历史输入。
- actor 输出完整 18 维腿部与机械臂动作。
- 接受权重是中心化续训的 `model_200` 导出结果，不是训练末尾 checkpoint。
- 高度扫描顺序、基座质心线速度、安装偏移和动作历史必须与训练定义逐项一致。

## 3. 目录结构

```text
policies/
  nav/                         NAV actor、来源 manifest 和验证报告
  push/                        PUSH actor、训练参数、来源 manifest 和验证报告
  climb/                       CLIMB actor、训练参数、来源 manifest 和验证报告
config/
  nav_deploy.yaml              NAV 动作缩放、默认角、PD 和控制周期
  piper_robot_profile.json     训练资产对齐的质量、惯量和安装变换
  piper_collision_profile.json Isaac 碰撞几何导出
robot_model/
  go2piper.xml                 GO2-PIPER MuJoCo 运动链
  scene.xml                    平地场景入口
  assets/                      MJCF 引用的网格
runtime_reference/
  mujoco/                      观测、动作、PD、PUSH IK 和箱体技能参考实现
  isaac_mdp/                   训练时 PUSH/CLIMB 观测和动作定义
validation/
  piper-three-skills-index.json 三技能总索引
  static/                      静态动力学与观测对齐报告
SHA256SUMS                     除自身外所有交接文件的 SHA-256
PACKAGE_MANIFEST.json          机器可读文件清单与策略边界
```

`runtime_reference/` 是接口语义参考，不是现成实机驱动。仓库当前没有完成 Go2 低层 SDK 与 PIPER CAN/SDK 的联合硬件后端。

为使该目录可独立做 MuJoCo 冒烟，参考运行时只做了两类打包适配：资源路径改为包内相对路径；`LocomotionRuntime` 的高层场景环境类型导入改为最小 `Protocol`。观测、动作、PD、IK 和接触控制方程未因打包而改写。

## 4. Sim-to-Real 小组必须补齐

1. 固定 GO2 与 PIPER 的实物型号、固件、机械安装、供电、通信接口和急停链路。
2. 测量安装变换、整机质量/质心、关节零点/方向/限位、控制延迟和实际位置/速度/电流限制。
3. 实现带统一时间戳的 Go2 12 轴与 PIPER 6 轴状态读取，以及分总线的命令下发。
4. 严格复现每个 actor 的观测顺序、缩放、历史缓冲、动作缩放、首命令和失联处理。
5. 依次完成断电回放、悬空低增益、支架测试、平地低速、PUSH 和低台 CLIMB；任何阶段都不得跳过物理急停和软件 watchdog。
6. 用实测参数更新机器人 profile 后重新做同状态推理、FK/Jacobian、重力、限幅和延迟对照。

## 5. 明确不包含

- 世界模型、VLM、视觉理解或学习规划器；
- Oracle、场景图、通道规划、重规划和技能调度；
- N1/N2 快照、候选、回放数据或训练数据集；
- ARX5 权重、模型和运行时；
- 未接受的鲁棒续训、消融或诊断候选权重；
- Go2/PIPER 实机 SDK、CAN 驱动、电源方案和机械安装图。

策略来源、评估边界和文件哈希以各技能的 `manifest.json`、`validation/piper-three-skills-index.json` 和根目录 `SHA256SUMS` 为准。
