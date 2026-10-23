# GO2-PIPER Sim-to-Real

Re-NAV 的 GO2-PIPER 底层技能训练、仿真验证与 Sim-to-Real 控制开发。世界模型组已在PIPER/Isaac开展连续任务研究，reachability组研究固定版本的技能接管资格；本仓库保留ARX5历史工具，接入必须匹配本体、策略与控制契约。

## 从这里开始

| 文档 | 用途 |
| --- | --- |
| [从零入门清单](docs/PROJECT_ONBOARDING_CN.md) | 概念、代码阅读顺序、技能逻辑、运行和录像练习 |
| [总交接](docs/AGENT_HANDOFF_CN.md) | 当前工作范围、接手检查、公共路径和文档导航 |
| [项目计划](docs/PROJECT_PLAN_CN.md) | 技能边界、验收标准和交付要求 |
| [CLIMB](docs/CLIMB_CRAWL_STATUS_20261001_CN.md) | 最新结果、运行状态、提速计划、源码与视频证据 |
| [PUSH](docs/PUSH_CURRENT_HANDOFF_CN.md) | 用户认可的v212仿真版、接收清单、复现命令和已知边界 |
| [安装与标定](docs/GO2_PIPER_MOUNTING_CN.md) | 固定安装模型、实物标定与硬件验证 |

当前首要任务为**NAV/PUSH/CLIMB之间的平稳切换**，主线为NAV→CLIMB→NAV的多起点鲁棒性，保留NAV→PUSH→NAV既有开发基线。PUSH v212保持为跨组仿真基线；CLIMB整链已有同版多起点开发成功，但扩展起点仍有执行器力矩失败，尚未发布统一SDK或完成正式验收。CLIMB已跑通逐脚登台、前脚展开和稳定承重，后续到目标点由NAV负责；效率与跨仿真状态见技能页。不重训平地NAV；当前在原策略参数域内验证当前限矩下的原生行走、真实准备和退出，初始化与原生行走已有开发达标证据，实际到点和连续场景仍待验证。实机接入／标定按2026-10-19安排启动，当前尚无实机执行结果。新小组从总交接的分工、接收清单和首次核对开始。

历史实验和旧待办已去重合并至[历史实验档案](docs/archive/EXPERIMENT_HISTORY_CN.md)，按原文件名索引追溯。当前成功率、候选、运行状态只在对应技能页维护，避免多个入口出现不同版本。

## CLIMB 版本管理（2026-10-19）

两个训练项目已合并为唯一目录 **[climb_skill](climb_skill/README.md)**，`climb_skill2` 已移除。源码已并入主仓库，完整旧历史通过随项目交付的 Git bundle 保留，当前为 V1；实际生效版本见 [VERSION.json](climb_skill/VERSION.json)。

- **V1**：截图中的 AMP + 后腿参考基线恢复版，原始完整源码快照和权重已经缺失，不能声称逐字节原版。
- **V2**：原 climb_skill 的30cm课程与前腿软限制版；V21、V22分别保留两次训练，V2默认V22。
- **V3**：原 climb_skill2 的脚级跨沿质量课程版，统一此前混用的内部版本名，保留旧课程与修正后续训两份结果。

[训练、保存与切换命令](climb_skill/README.md) · [版本配置差异](climb_skill/docs/VERSIONS_CN.md) · [当前完整参数](climb_skill/docs/CONFIG_CN.md) · [训练结果对应表](climb_skill/versions/registry.json) · [检查记录](climb_skill/validation/current.json)。

进入项目并激活 go2-piper 后，`cd climb_skill && source scripts/env.sh`，再运行 `python scripts/manage.py switch V1`（或V2/V21/V22/V3）。有未保存修改或正在训练会拒绝切换。源码切换不会删除共享outputs；修改前用manage.py save保存新的标签。权重和录像均保持字节不变，本次上传最近10份checkpoint；历史run.json不改写旧路径，通过对应表定位新目录。

源码、历史、最近10个模型和最近10个录像统一在 `zyh` 分支交付。模型和录像使用 Git LFS；日志、环境、缓存不上传。本地其他录像保留。清单及哈希见 [publication.json](climb_skill/versions/publication.json)。

## 本机 Isaac 开发环境

本机项目专用 Conda 环境为 `go2-piper`（Python 3.11、Isaac Sim 5.1）。
正常激活后使用 `python`，无需旧启动器或手动设置 `PYTHONPATH`：

```bash
conda activate go2-piper
cd /mnt/miaojigui/zyh
cd climb_skill
source scripts/env.sh
python scripts/train.py --headless --device cuda:0
```

旧的历史技能本地启动器已删除。当前 Climb 训练和录像请使用 [Climb 说明](climb_skill/README.md)，历史冻结技能使用 [原交付入口](skills/README.md)。

环境安装记录和依赖快照保存在项目外 `/mnt/miaojigui/deps/go2-piper/`。
2026-10-14本机验证：依赖检查无冲突，NAV/PUSH/CLIMB各一个GPU环境均1/1通过功能检查；
两段历史技能录像完整解码通过。整卡显存采样峰值18177MiB/24564MiB，包含已有约11GB占用。
这不保证其他时刻的共享GPU余量。PUSH/CLIMB最大力矩限值比均为1.0，不作为安全验收。
本次报告和录像：`outputs/isaac/conda-validation-20261014-183447/`（不提交Git）。

## 按技能阅读项目（2026-10-19整理）

```text
skills/
  nav/              冻结NAV权重、当前入口和录像控制器
  push/v212/        最新PUSH匹配源码、双模型、几何与配置
  climb/iy/         前开发者CLIMB完整阶段控制器与模型
integrations/       NAV→PUSH→NAV、NAV→CLIMB→NAV
scripts/            公共训练、回放、导出、测试和诊断工具
source/             公共Isaac Lab扩展
climb_skill/        唯一AMP训练工程及V1/V2/V3版本历史
archive/            旧策略包、早期MuJoCo代码、整理前清单
docs/               当前进展与计划
outputs/            本地运行结果，不因整理移动或删除
```

[三个技能](skills/README.md) · [切换运行](integrations/README.md) · [详细目录与整理计划](docs/PROJECT_LAYOUT_CN.md) · [旧版档案](archive/README.md)。运行前按各技能README执行其自己的verify.py和run.py。旧runtime_handoff链接已移除；sim2real、mujoco路径仍保留兼容链接，不是两份代码。

本仓库以最新开发快照交付，源版本和文件清单见 [`RELEASE_MANIFEST.json`](RELEASE_MANIFEST.json)，完整性清单为根目录 `SHA256SUMS`。技能成绩与未完成工作仍以当前交接页为准。

本次模型与录像分别按修改时间选最近10个；不足10个取最近5个，不足5个全取。未选中的本地文件不删除。

## 单技能直接运行

每个技能有自己的run.py、verify.py和SHA256SUMS，tools目录已移除。激活go2-piper后，从仓库根分别运行（不要同时占用同一GPU）：

```bash
python skills/nav/run.py --gpu 0 --output-dir "$PWD/outputs/nav-001" --execute
python skills/push/run.py --gpu 0 --output-dir "$PWD/outputs/push-001" --execute
python skills/climb/run.py --gpu 0 --output-dir "$PWD/outputs/climb-iy-001" --execute
```

省略--execute只准备计划。你的AMP训练仍在climb_skill，与上述前开发者技能分开。连续任务入口为integrations/nav-push-nav/run.py、integrations/nav-climb-nav/run.py。

## 用户 PUSH 从头训练工程

PUSH V9候选位于 [push_skill](push_skill/README.md)：独立Isaac Lab，移植iy支撑转移、足端IK、接触时钟与限速，增加原限矩内的承重前馈；保留本地机械臂IK、实测承重初始化、9cm中心推点和不蹲身。参考路线AMP关闭，可直接零残差演示，也可训练一个小残差腿PPO；旧纯PPO配置单独保留。正式跨仿真/实机尚未验收。
