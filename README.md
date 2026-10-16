# GO2-PIPER Sim-to-Real

Re-NAV 的 GO2-PIPER 底层技能训练、仿真验证与 Sim-to-Real 控制开发。世界模型组已在PIPER/Isaac开展连续任务研究，reachability组研究固定版本的技能接管资格；本仓库保留ARX5历史工具，接入必须匹配本体、策略与控制契约。

## 从这里开始

| 文档 | 用途 |
| --- | --- |
| [总交接](docs/AGENT_HANDOFF_CN.md) | 当前工作范围、接手检查、公共路径和文档导航 |
| [项目计划](docs/PROJECT_PLAN_CN.md) | 技能边界、验收标准和交付要求 |
| [CLIMB](docs/CLIMB_CRAWL_STATUS_20261001_CN.md) | 最新结果、运行状态、提速计划、源码与视频证据 |
| [PUSH](docs/PUSH_CURRENT_HANDOFF_CN.md) | 用户认可的v212仿真版、接收清单、复现命令和已知边界 |
| [安装与标定](docs/GO2_PIPER_MOUNTING_CN.md) | 固定安装模型、实物标定与硬件验证 |

当前首要任务为**NAV/PUSH/CLIMB之间的平稳切换**，主线为NAV→CLIMB→NAV的多起点鲁棒性，保留NAV→PUSH→NAV既有开发基线。PUSH v212保持为跨组仿真基线；CLIMB整链已有同版多起点开发成功，但扩展起点仍有执行器力矩失败，尚未发布统一SDK或完成正式验收。CLIMB已跑通逐脚登台、前脚展开和稳定承重，后续到目标点由NAV负责；效率与跨仿真状态见技能页。不重训平地NAV；当前在原策略参数域内验证当前限矩下的原生行走、真实准备和退出，初始化与原生行走已有开发达标证据，实际到点和连续场景仍待验证。实机接入／标定按2026-10-19安排启动，当前尚无实机执行结果。新小组从总交接的分工、接收清单和首次核对开始。

历史实验和旧待办已去重合并至[历史实验档案](docs/archive/EXPERIMENT_HISTORY_CN.md)，按原文件名索引追溯。当前成功率、候选、运行状态只在对应技能页维护，避免多个入口出现不同版本。

## 目录

```text
source/       Isaac Lab任务及训练代码
mujoco/       MuJoCo运行时、模型和诊断
scripts/      训练、评估、导出与来源核验
sim2real/     历史部署和训练交接包
runtime_handoff/ 匹配技能、控制器、模型、资产与可迁移运行入口
docs/         五份常用文档
docs/archive/ 去重历史证据
```

最新独立技能运行材料已随仓库交付在 [`runtime_handoff/`](runtime_handoff/README_CN.md)：包含PUSH v212与CLIMB iy的匹配源码、权重、配置、机器人资产，以及当前NAV入口和两条切换开发对照。先运行 `python3 runtime_handoff/verify_delivery.py`，再按该目录命令在独立Isaac环境回放。`sim2real/`保留九月历史冻结包；新开发不要混用不同版本模型和控制器。

本仓库以最新开发快照交付，源版本和文件清单见 [`RELEASE_MANIFEST.json`](RELEASE_MANIFEST.json)，完整性清单为根目录 `SHA256SUMS`。技能成绩与未完成工作仍以当前交接页为准。
