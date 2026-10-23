# GO2-PIPER 三技能项目

当前工作区整理为以下七个目录（共用 `asset/`，新建 `nav_skill2/` 保留旧Nav作对照）：

| 目录 | 内容与入口 |
| --- | --- |
| `asset/` | 三技能共用的 GO2-PIPER USD 与分层文件，来源、校验见本目录说明 |
| `climb_skill/` | 你的 Climb 训练项目，内容保持不动；训练与版本切换沿用其 README |
| `push_skill/` | 原 v212 双权重的精简 Isaac 回放，`play.py` 看效果、录完整回合 |
| `nav_skill/` | 指定上游原配置Go2Piper WBC，课程默认关闭，每1000轮保存权重，默认不录像 |
| `nav_skill2/` | 新的Isaac Lab外部底层速度训练包：12维预测补零成18维、臂零位、PPO+AMP，每100轮保存录像，见本目录README |
| `history/` | 前开发者代码、冻结技能、切换实验和已有成功对照；已确认失败的回放产物删除 |
| `mujoco/` | 独立的Nav/Climb/Push与切换仿真项目；按本目录README配置隔离环境 |

## 环境与公共机器人

```bash
conda activate go2-piper
cd /mnt/miaojigui/zyh
export CLIMB_ROBOT_USD="$PWD/asset/go2_piper/go2_piper.usd"
```

本机已配置 Conda 激活钩子设置该变量；移动项目后，先设置 `GO2_PROJECT_ROOT` 再激活环境，或手动执行上面的 export。没有修改 Climb 的资产加载代码；它原本就支持 `CLIMB_ROBOT_USD`。公共 USD 的分层文件也要一起保留，不能只复制最外层文件。

## Push 看效果

```bash
cd /mnt/miaojigui/zyh/push_skill
python play.py --headless --device cuda:0 --video
```

结果在 `push_skill/outputs/play-时间戳/`。默认单环境，录像跟随回合直至成功、失败或48秒超时，不在10秒截断。`--arm-speed 1` 恢复原伸臂速度；`--video-fps 10` 减少渲染；省略 `--video` 不启用虚拟摄像机。

## 初始姿态与后续切换

已核对 Climb 当前 V1 配置和 Push v212：机械臂 `joint1…joint6` 的**默认初始目标均为 `[0,0,0,0,0,0] rad`**，腿默认姿态相同：左/右髋 `+0.1/-0.1`、前大腿 `0.8`、后大腿 `1.0`、小腿 `-1.5 rad`，Climb/Push配置根高度均 `0.33 m`；Nav恢复上游初始根高度 `0.35 m`。Push 独立回放起点比原点后退8cm，并先真实承重落稳；Climb 的实际 reset、随机化和起点保持原样。因此默认目标相同不代表实际物理接管状态相同。

Push 伸臂后是推箱姿态，当前完成条件没有收臂要求。Nav WBC 在训练中会随机末端命令、主动改变机械臂姿态。**本次只统一资产并核对初始目标，不实现技能切换，也未将这些运行末态说成可直接接管。** 后续需要单独实现停稳、收臂和连续接管验证。

## 历史与验证边界

整理前的文件都在 `history/`，其中 `skills/push/v212/` 是完整冻结来源，`outputs/push-original-entry-backoff-20261020-c/` 是此前已成功的开发对照（该历史输出仅保留在本地，不在本次上传清单中）。旧文档中的根目录命令属于旧布局，不能直接照搬。失败实验删除记录见 `history/CLEANUP.json`。

新回放的精简与提速属于候选；单次录像不能代替批量验收。实机仍需遵守 `AGENTS.md` 的跨仿真验收要求。训练由你启动，本次不启动长训练。

## 新Nav2训练

```bash
conda activate go2-piper
cd /mnt/miaojigui/zyh/nav_skill2
python train.py --headless --device cuda:0 --num-envs 2048 --iterations 15000
```

Nav2采用与Climb/Push相同的默认关节目标，机械臂保持零位，从训练开始不学习机械臂动作；18维接口的后六维恒零。V4采用Climb式真实方向运动奖励，加入软左右镜像、方向与速度条件AMP、前进0.3～1.0/转向0.2～0.6的课程和探索退火，训练前后左右/斜向移动、左右转向、减速与默认站姿；每100轮录像；本阶段不训练目标点导航。原Nav保留用于对照；新任务、课程、AMP、回放、续训与tmux命令见[Nav2说明](nav_skill2/README.md)。仅完成工程冒烟检查，正式训练由用户启动，尚未验证技能切换。

## GitHub交付：2026-10-23

本仓库`zyh`分支包含`asset/`、`climb_skill/`、`push_skill/`、`nav_skill/`、`nav_skill2/`、`mujoco/`与`history/`。每次训练／版本只发布最后一个checkpoint、同轮导出actor（如有）及对应录像，保留配置和源码快照。Push的腿／臂双模型、MuJoCo冻结actor是运行依赖，不按checkpoint编号互相替代。历史源码版本通过Climb的bundle保留。

克隆后先下载Git LFS文件：

```bash
git clone --branch zyh https://github.com/WM4N-Group/go2-piper-RL-Sim2Sim2Real.git
cd go2-piper-RL-Sim2Sim2Real
git lfs install
git lfs pull
```

权重的准确路径、对应训练目录、录像和SHA256见[发布清单](PUBLICATION.json)。Nav1最新续训权重为`nav_skill/logs/rsl_rl/go2_piper_wbc/2026-10-23_10-26-37_resume_4999/model_9998.pt`；Nav2新V4为`nav_skill2/outputs/train-20261022-212821-ryiwu7na/model_6400.pt`。旧V3的10100轮录像为停止时中断的21.7秒片段，没有完成报告，不作为完整成功证据。

其他中间checkpoint、录像、训练日志、缓存和环境不上传，本地全部保留。训练源码和候选权重仅供开发复现，尚未完成统一跨仿真或真机验收。各运行的历史参数和源码快照不随当前代码改写；回放旧版本应使用匹配源码。运行环境仍需按各技能说明单独配置。
