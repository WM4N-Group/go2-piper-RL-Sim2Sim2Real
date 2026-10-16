# GO2-PIPER 底层策略训练交接包

> 2026-10-14交接注：本包是2026-09冻结训练基线，不是最新PUSH/CLIMB可复现候选。以下“当前”及命令属于历史包边界；最新候选与任务范围见[总交接](../../docs/AGENT_HANDOFF_CN.md)、[PUSH](../../docs/PUSH_CURRENT_HANDOFF_CN.md)、[CLIMB](../../docs/CLIMB_CRAWL_STATUS_20261001_CN.md)。当前不重训平地NAV，近期CLIMB改进来自冻结actor与控制器；PUSH与CLIMB的MuJoCo诊断已恢复，PUSH的Isaac安全优化已恢复，本次跨组接收v212；实机仍暂停，不能按本包旧训练步骤直接恢复。文件完整性以包内`SHA256SUMS`核对。独立转交本包时同时交付主仓库当前docs。 新小组当前主线是技能平稳切换；开发候选尚未成为统一SDK，按主仓库项目计划继续，不从本包旧成功率推断新版本状态。

生成日期：2026-09-21

本包供 Sim-to-Real 小组继续优化 GO2-PIPER 的底层 PUSH、CLIMB 策略及其低层控制。

## 当前边界

| 技能 | 可继续训练基线 | 训练输入/输出 | 原生验收 | MuJoCo 状态 |
| --- | --- | ---: | --- | --- |
| PUSH | `checkpoints/push/model_599.pt` | `226 -> 12` 腿部动作，IK 合成 6 轴机械臂目标 | `31/32`、`30/32` | 未放行 |
| CLIMB | `checkpoints/climb/model_200.pt` | `253 -> 18` 联合关节动作 | `30/32`、`32/32` | 未放行 |

PUSH 与 CLIMB 的完整 PPO checkpoint 均包含 actor、critic、optimizer 与训练迭代号。两项技能当前都不能直接上实机；优化后的候选也不得覆盖这里的冻结基线。

## SAFE_BASE 增量状态（2026-09-23）

主仓库中的 SAFE_BASE 独立腿部任务已训练至 `model_99.pt`，checkpoint SHA-256 为
`85a3981d595170d3b224a9fdc45890217e9fbdf7aa3561f81702c58d42b02980`。
在 SAFE_BASE Play 配置、零初始底座速度、固定安全臂姿态下，seed `100..103` 各 32
环境均保持满 12 s，合计 `128/128` 到时且无其他终止。逐环境 JSON 在主仓库根目录
的 `../artifacts/go2-piper/safe-base-2026-09-23/`（不是相对于本交接包）；评估入口为
`scripts/evaluate_safe_base.py`，原始四组评估脚本 SHA-256 为
`b15d544646bf0bc5fc8a2f7f2f894adb89fd5424562172f0be5eacf96934935d`。
单独重跑的 seed `100` 分时段诊断记录在同目录的 `eval_window_seed_100.json`，
显示速度峰值集中在起始 `0–2 s`，不能说明
SAFE_APPROACH 到 SAFE_BASE 切换已安全。本交接包**未纳入**这个 checkpoint、评估脚本
或 JSON，不能使用包内冻结 PUSH 启动器冒充其验收。待完成真实切换初态和 MuJoCo 对照后，
再生成新的来源匹配交接包；不得用该增量改写本包策略来源清单或基线。

NAV 只作为部署交接包中的冻结参考 actor，不在本包提供继续训练 checkpoint。需要 NAV 契约时，使用同级 `go2-piper-low-level-policy-handoff`。

## 目录

```text
checkpoints/                   选定 PUSH/CLIMB 完整 RSL-RL checkpoint 和训练 YAML
source/LeggedManip_Lab/        PIPER 箱体任务及必要的共享任务/MDP 训练源码
scripts/                       训练、评估、导出和来源校验脚本
scripts/launch/                可移植训练/评估启动器
evaluation/                    两组来源匹配的原生验收报告
metadata/                      训练边界、门禁和复现要求
PACKAGE_MANIFEST.json          机器可读策略及 checkpoint 身份
SHA256SUMS                     全包完整性清单
```

`source/` 保留 PIPER 资产、PIPER 箱体任务以及任务所需的共享箱体定义。

## 前提

使用与原训练兼容的 Isaac Lab/Isaac Sim 环境和 `rsl-rl-lib>=3.0.1`。本包不打包 Isaac Lab 或 NVIDIA 运行时；它们应由接手小组在独立环境中安装并版本锁定。

将 Isaac Lab Python 启动器传给 `ISAAC_PYTHON`，例如：

```bash
export ISAAC_PYTHON=/path/to/isaac-python
```

启动器会自动将包内 `source/LeggedManip_Lab` 加入 `PYTHONPATH`。执行目录固定在本包根目录，新的日志会写到 `logs/rsl_rl/`，该目录不应提交 Git。

## 继续训练

从冻结 checkpoint 热启动 actor/critic，并重置优化器和训练计数：

```bash
scripts/launch/train_skill.sh push --device cuda:0 --num_envs 2048 --max_iterations 300 --seed 70
scripts/launch/train_skill.sh climb --device cuda:0 --num_envs 2048 --max_iterations 300 --seed 71
```

这适用于引入新的实物标定、延迟、限幅、接触课程或奖励后重新优化。`--init_checkpoint` 的语义是 actor/critic 热启动，**不会**恢复旧 optimizer 或 iteration state。

若实验需要严格恢复 optimizer，应先将原 checkpoint 放在新工作副本的 `logs/rsl_rl/<experiment>/<run>/` 中，然后通过底层 `scripts/rsl_rl/train.py --resume --load_run <run> --checkpoint model_*.pt` 启动。不要同时传入 `--resume` 和 `--init_checkpoint`。

## 评估与导出门禁

每次候选至少要执行两组独立原生 Isaac 评估：

```bash
scripts/launch/evaluate_skill.sh push results/push-seed206.json --seed 206
scripts/launch/evaluate_skill.sh push results/push-seed207.json --seed 207
scripts/launch/evaluate_skill.sh climb results/climb-seed208.json --seed 208
scripts/launch/evaluate_skill.sh climb results/climb-seed209.json --seed 209
```

原生门槛为每组至少 `30/32`，不得有未完成回合，也不得使用诊断覆盖。通过后还必须用来源匹配的控制代码完成两组独立 MuJoCo 评估，各至少 `30/32`，才能导出新的候选 actor。PUSH 的 `226 -> 12` actor 必须经包内 `PushArmIK` 合成 6 轴目标，不能直接将 12 维输出写入 18 个关节。

当前已知问题是接触丰富任务的 MuJoCo/PhysX 约束与接触时序不一致。不得通过降低接触、姿态或落稳门槛来提高成功率。

## 交接限制

- 安装位姿、质量、质心、关节零点、关节方向、力矩/速度/电流限制及延迟都仍是待实物标定项。
- 本包没有 Go2 SDK、PIPER SDK/CAN 驱动、机械安装、电源、急停或硬件安全状态机。
- `requirements-training-reference.txt` 是环境约束说明，不是可用 pip requirements；不要将 Isaac Sim 依赖安装进 MuJoCo 部署环境。
- 新实验必须新建输出目录并记录源 checkpoint、控制代码和物理参数哈希。

详细边界见 [metadata/TRAINING_BOUNDARY_CN.md](metadata/TRAINING_BOUNDARY_CN.md)。
