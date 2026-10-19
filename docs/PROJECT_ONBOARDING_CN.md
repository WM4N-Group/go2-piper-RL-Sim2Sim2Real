# 从零看懂 GO2-PIPER：阅读与动手清单

这是一份学习路线，当前候选状态仍以[总交接](AGENT_HANDOFF_CN.md)、[PUSH交接](PUSH_CURRENT_HANDOFF_CN.md)和[CLIMB交接](CLIMB_CRAWL_STATUS_20261001_CN.md)为准。先理解和重放，再考虑训练与修改控制器。

## 1. 先认清项目和版本

- [ ] 阅读[总交接](AGENT_HANDOFF_CN.md)和[项目计划](PROJECT_PLAN_CN.md)，能说清当前目标：GO2四足加PIPER六轴臂的导航、推箱、登台，以及连续物理回合内的技能切换。
- [ ] 区分四层结果：单技能功能跑通、一次整链成功、正式跨仿真验收、实机放行。目前不能由前三者中的单个录像推断实机安全。
- [ ] 记录 `git status --short --branch` 和 `git rev-parse HEAD`。仓库HEAD、训练快照、权重、报告是不同对象；需要共同匹配。
- [ ] 知道本地 `sim2real/` 是2026-09历史交接包。NAV冻结actor已在其中；历史PUSH是model599，历史CLIMB是model200。
- [ ] 知道文档最新PUSH v212需要model255、独立腿model199及完整控制快照；CLIMB iy需要完整train、stand_actor304及初态bank等。仅凭本仓库不能复现这些最新版，不能用历史权重替代后仍称“最新版”。

关于听说的“43秒视频”：PUSH交接中v270的43.68秒是到点制动事件，整链最终门禁通过是47.96秒；该页更新时v270录像尚未完成交付核验。已核验的v261录像是38.34秒，v212推箱录像是16秒。没有实际文件时，不能确认某个43秒视频存在或给它编造复现命令。

## 2. 建立六个基本概念

| 概念 | 在本项目中负责什么 | 你应该能回答的问题 |
| --- | --- | --- |
| Isaac Sim | 物理、碰撞、接触、相机和渲染 | 无窗口运行为什么仍能录视频？因为相机可以离屏渲染。 |
| Isaac Lab | 在Sim上组织并行环境、观测、动作、奖励和终止 | 一个task ID如何找到环境配置？ |
| 场景 | 机器人、地面、箱子、光照、传感器及参数 | 箱子尺寸、质量、摩擦和初始位置在哪里设？ |
| 策略/actor | 用观测计算动作的神经网络及其权重 | 输入输出维数、历史顺序和checkpoint是否匹配？ |
| 控制器 | 对动作作缩放、IK、阶段控制、PD及执行器约束 | 策略输出怎样变成实际关节运动？ |
| 评估器 | 设初态、运行回合、统计终态、输出报告和录像 | 成功是哪个条件判断的？失败和未完成分别是多少？ |

不要把策略理解为整个技能：接触技能同时依赖阶段逻辑、几何、执行器合同和权重。给定速度的NAV诊断也不等于带地图、避障和路径规划的完整导航系统。

## 3. 按这个顺序找代码

以下路径均相对仓库根目录。先沿一个入口读通，暂时不用通读全部历史文件。

| 阅读顺序 | 文件或目录 | 重点 |
| --- | --- | --- |
| 2 | [任务注册](../source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/__init__.py) | `gym.register`将task ID连接到环境和PPO配置。 |
| 3 | [平地配置](../source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/flat_env_cfg.py) | NAV观测、动作、默认姿态、速度命令和物理步长。 |
| 4 | [箱子任务配置](../source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/box_env_cfg.py) | PUSH/CLIMB场景、控制项、奖励、终止和PLAY变体。 |
| 5 | [机器人资产目录](../source/LeggedManip_Lab/LeggedManip_Lab/assets/go2_piper/) | USD几何与碰撞；articulation配置中的关节、执行器、限位与PD。 |
| 6 | [场景几何](../source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/box_terrain.py) | 场景由配置和程序组合生成，并非只有一个“场景文件”。 |
| 7 | [当前通用评估器](../scripts/evaluate_box_skills.py) | CLI参数、checkpoint装载、回合循环、报告、相机录像。 |
| 8 | [冻结训练交接包](../sim2real/go2-piper-low-level-training-handoff/README_CN.md) | 历史权重应使用其匹配脚本与源，不直接假定HEAD兼容。 |

仓库保留ARX5历史代码；看到 `go2_arx5` 或旧MuJoCo XML时，先确认本体，不能当成当前GO2-PIPER整链场景。

## 4. 分别追踪三个技能

### NAV：速度跟踪

- [ ] 从[原生检查器](../scripts/check_piper_native.py)追踪：启动Sim → 创建Flat任务 → 读取冻结actor → 站稳 → 给速度 → actor推理 → 环境步进 → 报告。
- [ ] 在[策略消费说明](../sim2real/go2-piper-low-level-policy-handoff/README_CN.md)核对NAV的210维观测与18维输出。历史观测按观测项拼接三帧，不能直接改成三个70维整体拼接。
- [ ] 分辨腿12轴与臂6轴；核对关节重排、默认角、动作缩放、PD和延迟。Isaac腿PD 30/0.6不能拿旧MuJoCo YAML 35/0.8直接替换。
- [ ] 能解释报告中的速度跟踪结果为何不等于“绕障到达任意目标点”。

### PUSH：腿策略与推箱控制协作

- [ ] 阅读 `mdp/box_push.py` 的状态、观测与判定，再读 `box_push_actions.py`、`box_push_control.py`、`box_push_ik.py`。
- [ ] 画出机器人/箱子/目标的坐标关系，区分世界坐标、机体坐标和末端目标。
- [ ] 追踪腿动作、机械臂末端目标、IK求关节目标、关节执行、箱子运动与终止条件。
- [ ] 区分历史model599的226→12加IK路径，与最新v212的226→19加独立腿hook路径；维数相似不证明控制代码相同。
- [ ] 阅读[PUSH交接](PUSH_CURRENT_HANDOFF_CN.md)的负载域、初态、完成门禁和失败案例；学习“推到目标”“停止”“收臂”“回到NAV”为什么是不同阶段。

### CLIMB：登台与阶段控制

- [ ] 阅读 `mdp/box_climb.py`、`box_climb_stages.py`、`box_climb_crawl.py` 和 `crawl_gait.py`，再结合 `climb_stage_math.py`、`climb_leg_kinematics.py` 看足端轨迹和几何约束。
- [ ] 从[CLIMB交接](CLIMB_CRAWL_STATUS_20261001_CN.md)找最新候选的实际阶段顺序和门禁，理解逐脚移动、支撑脚、机身净空、前脚展开及稳定承重。
- [ ] 区分历史model200的253→18策略评估与最新iy阶段控制；不要把旧短回合成功当作最新逐脚登台已复现。
- [ ] 理解最新iy不是“给actor输入就会自动爬”：交接中的 `stand_actor304.pt` 末层为零，18维残差恒为零，实际运动由支撑转移、足端/身体规划与接触门禁控制器产生。304维输入还含51维阶段状态后缀；单独拿到actor不够。
- [ ] 能说明登台结束与后续NAV到点的边界，以及为什么阶段超时、支撑不足和接触异常都要记录。

## 5. 走通一次从观测到物理的闭环

- [ ] 选一个技能和一个seed，固定源码、权重与初态。
- [ ] 找到一次 `env.step(action)` 前的观测构造、历史更新和actor调用。
- [ ] 跟踪动作维数、限幅、重排、默认角、IK/阶段覆盖和最终关节目标。
- [ ] 查看仿真步长与控制降采样，算出策略频率；区分仿真时间和真实运行耗时。
- [ ] 找到回合成功、失败、超时、reset的具体判定；查看最终状态而不是只看奖励曲线。
- [ ] 对照报告与视频检查一次接触过程；视频好看不能替代力矩、限位与接触审计。

## 6. 本机运行清单

专用环境名为 `go2-piper`，路径 `/mnt/miaojigui/conda/envs/go2-piper`；IsaacLab专用源码在 `/mnt/miaojigui/deps/go2-piper/IsaacLab`。首次安装/验证状态以实际安装记录为准。

2026-10-14已完成本机安装与GPU冒烟验证：`pip check`无冲突，三个技能各1/1通过，PUSH/CLIMB录像完整解码通过。证据保存在项目输出目录 `outputs/isaac/conda-validation-20261014-183447/`；历史技能最大力矩限值比均为1.0，仍不满足安全放行。原始共享Isaac环境保留，旧临时重现环境与旧试跑目录按用户要求清理。

[Isaac依赖清单](../requirements-isaac.txt)与根目录的MuJoCo `requirements.txt`用途不同。外部依赖目录还保留IsaacLab的固定提交与依赖兼容补丁：Sim 5.1的FastAPI要求Starlette低于0.46，因此专用Lab的安装声明使用0.45.3；不涉及仿真控制逻辑。重建环境时需要一起保留源码版本和补丁，不能只依赖一个 `pip freeze` 文件。

```bash
# 新终端若尚未初始化conda，先执行这一行；已初始化可省略。
source /usr/local/miniconda3/etc/profile.d/conda.sh
conda activate go2-piper
cd /mnt/miaojigui/zyh

# 每次开跑先查看共享显卡当前占用，不中止别人的进程。
nvidia-smi
export CUDA_VISIBLE_DEVICES=0

# 当前Climb训练（录像由训练脚本自动记录）
cd climb_skill
source scripts/env.sh
python scripts/train.py --headless --device cuda:0
```

- [ ] `which python` 指向专用环境；不要把依赖装到系统Python，不与MuJoCo混装。
- [ ] 初次回放使用一个环境；训练参数、续训与录像命令见 [Climb README](../climb_skill/README.md)。
- [ ] Climb新训练产物写到 `climb_skill/outputs/当前版本组/` 的新目录，不覆盖旧训练。
- [ ] 检查对应训练的 `config.json`、`run.json` 与checkpoint录像的 `report.json`。每100轮自动保存并录像，录像时训练等待。
- [ ] 历史冻结技能的运行方法以 [原交付说明](../runtime_handoff/README_CN.md) 为准，不使用已删除的本地启动器。
- [ ] 一条成功录像不代表跨仿真验收通过。

## 7. 之后再学训练、切换和验收

- [ ] 阅读[训练入口](../scripts/rsl_rl/train.py)和 `config/go2_piper/agents/rsl_rl_ppo_cfg.py`：环境配置定义任务，PPO配置定义训练算法。先理解奖励和终止，再考虑长时间训练。
- [ ] 阅读[切换合同](../scripts/piper_skill_transition_contract.py)：它描述状态/事件，并不是交付完成的统一执行SDK。
- [ ] 明确连续任务的“无reset”：切换时机器人姿态、关节速度、历史动作、接触状态和箱子状态必须真实延续。
- [ ] 改一个因素，在新输出目录和新报告中做同初态对照；保留来源、seed、版本、执行器合同和完整失败统计。
- [ ] 正式PUSH/CLIMB资格要求Isaac与MuJoCo各两组独立32回合、每组至少30/32，并完成安全审计；本机一回合重放不满足这一条件。
- [ ] 实机验证需要独立分级放行与标定；当前实机暂停。

完成以上清单后，你应该能独立回答：正在跑哪一版、用哪个权重和控制源、场景如何生成、动作如何执行、何时成功/失败、证据存在哪里、还缺哪些最新版交付材料。

## 2026-10-19 统一交付

旧的本地历史技能启动器已删除。Climb完整代码、V1/V2/V3历史bundle、最近10个模型与最近10个录像由主仓库zyh分支交付。环境与日志不上传。以 [Climb README](../climb_skill/README.md) 的训练、回放和版本切换命令为准，清单见 [publication.json](../climb_skill/versions/publication.json)。

本次模型与录像分别按修改时间选最近10个；不足10个取最近5个，不足5个全取。未选中的本地文件不删除。
