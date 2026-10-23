# GO2-PIPER CLIMB：V1 / V2 / V3

唯一项目目录是 `/mnt/miaojigui/zyh/climb_skill`，内部 Python 包仍叫 `climb_skill`。
代码、配置、测试现在由主仓库统一管理，没有嵌套 Git 仓库。完整旧源码历史随 `versions/source-history.bundle` 交付，版本管理器会自动读取，不需要另找旧目录。
本次交付为每个训练版本／运行仅保留最后一个checkpoint及对应录像、配置和源码快照，通过Git LFS存储；V3迁移权重和运行必需的冻结actor单独保留。其他权重、录像和训练日志保留在本地但不上传。准确清单与SHA256见 `versions/publication.json` 和根目录 `PUBLICATION.json`。
V1原始历史权重缺失，但现有恢复代码已经重新训练，结果在 `outputs/V1/`；不能把新权重称为原始截图权重。

首次克隆主仓库的 `zyh` 分支后，在仓库根目录执行 `git lfs install`、`git lfs pull` 下载模型和录像。

| 版本 | 含义 | 相对上一版的主要变化 | 已有结果 |
|---|---|---|---|
| V1 | 截图 AMP + 后腿工作范围基线的恢复版 | 后大腿目标≤1.8rad，后膝目标−2.5～−1.05rad；共享运动参考相位；AMP平地门控 | 原始权重缺失；恢复代码重新训练的结果在 outputs/V1 |
| V2 | 原 climb_skill 的前腿软限制 / 30cm 课程版，默认 V22 | 最终高度20→30cm、7→11级；自由起步；前大腿−0.30～1.90、前膝−2.65～−0.95rad，软成本权重0.5；保留PPO探索保护 | V21、V22 |
| V21 | V2 的第一次训练 | 额外机身抬头惩罚权重0.5 | outputs/V2/V21 |
| V22 | V2 的第二次训练，也是 V2 默认 | 相对 V21 仅关闭额外机身抬头惩罚：0.5→0 | outputs/V2/V22 |
| V3 | 原 climb_skill2，统一此前混用的版本名 | 回到20cm/7级与原基线起步；起点后移；脚级跨沿检测、净空与落箱奖励、步态和登台质量课程；后续修正课程窗口 | original、current、migration |

V3/original 保留你认可的 model_800；V3/current 是修正课程后的续训；migration 只有迁移权重，不是第三次训练。
本地实际保留五个训练目录（新V1一个、V2两个、V3两个），没有因整理丢弃任何一次结果。每个目录的 `config.json`、`run.json`、`source/` 是该次训练的历史事实，不改写其中的旧路径与旧合同标识。

## 激活环境与切换

```bash
source /usr/local/miniconda3/etc/profile.d/conda.sh
conda activate /mnt/miaojigui/conda/envs/go2-piper
cd /mnt/miaojigui/zyh/climb_skill
source scripts/env.sh
python scripts/manage.py list
python scripts/manage.py status
python scripts/manage.py switch V1
# 也可以 switch V2、V21、V22、V3
```

切换时有未保存源码修改或正在训练/回放会拒绝操作。切换只恢复 Climb 训练源码，在主仓库中形成可审阅的修改；不会回退上游代码或删除 outputs。确认后必须 save 成新版本，才能再次切换。
V1、V2、V3标签固定不覆盖；后续新改动先保存为新的标签：

```bash
python scripts/manage.py save V3-before-next-change --message "记录当前配置和检查结果"
```

也可用普通 Git 查看差异：`git diff refs/climb-history/V1 refs/climb-history/V2`、`git diff refs/climb-history/V2 refs/climb-history/V3`（首次 switch 自动导入历史）；新保存的自定义版本同样用 `python scripts/manage.py switch 标签名` 切换。
本地 Git 防止代码被改丢；硬盘损坏仍需备份源码仓库与 outputs。不要执行 git clean -fdx 清理本项目。

## 训练、续训、录像

`source scripts/env.sh` 自动把当前项目放在 PYTHONPATH 最前面，设置版本化产物根目录；每次切换后建议重新执行。
训练脚本不传 `--config` 时自动读取 `VERSION.json` 指向的本版配置，完整参数均在配置中。

```bash
export CUDA_VISIBLE_DEVICES=0
# env.sh 默认使用随项目交付的 data/amp_pairs.json；可用 CLIMB_AMP_DATASET 覆盖
python scripts/train.py --headless --device cuda:0
```

从头训练默认4096环境、15000轮（V3是14700轮）、每100轮保存并录制当前课程中位高度，最后一轮也保存。录像子进程运行时训练等待。新训练自动在 `outputs/当前版本组/train-时间-随机后缀/（V21/V22归V2组）` 创建新目录。
续训会完整恢复checkpoint的配置与优化器，**不会因切换源码或修改JSON自动改变旧checkpoint配置**。

```bash
# 先切到V3：current目录中的权重才能用本版续训。
python scripts/train.py --resume outputs/V3/current/model_3200.pt --iterations 1000 --headless --device cuda:0
python scripts/play.py --checkpoint outputs/V3/current/model_3200.pt --box-height 0.20 --num-envs 1 --episodes 1 --headless --device cuda:0 --video
# 查看你认可的5cm参考动作：V3源码接受此旧课程合同，play以checkpoint配置为准。
python scripts/play.py --checkpoint outputs/V3/original/model_800.pt --box-height 0.05 --num-envs 1 --episodes 1 --headless --device cuda:0 --video
```

V21权重配V21源码，V22权重配V2/V22源码；不可把不同版本权重混作同一次训练。V3的旧课程内部revision标识为 `climb_skill_v3_foot_crossing_quality_v2`，修正课程为 `climb_skill_v3_model800_curriculum_v4`；这些是checkpoint兼容合同，保留原名以免破坏加载，公共版本名统一为V3。
`scripts/migrate_curriculum.py` 用于V3课程迁移，用于保留学习状态并修正旧课程元数据，严格禁止顺带改变奖励。

## 文件职责与进一步说明

| 文件 / 目录 | 作用 |
|---|---|
| VERSION.json | 当前公共版本与默认配置 |
| configs/ | 本版真正可用配置；其他版本通过Git切换获取 |
| docs/VERSIONS_CN.md | 版本差异、课程和旧结果对应关系 |
| docs/CONFIG_CN.md | 当前完整参数值、奖励与惩罚、修改位置 |
| versions/registry.json | 权重目录和历史路径映射 |
| versions/configuration-differences.json | 逐参数精确前后差异 |
| scripts/train.py / play.py | 训练与回放录像 |
| scripts/manage.py / env.sh | 保存、切换版本与设置环境 |
| source/climb_skill/climb_skill/tasks/direct/climb_skill/task_parameters.py | 任务参数结构、校验和checkpoint合同 |
| source/climb_skill/climb_skill/tasks/direct/climb_skill/mdp/ | 动作、奖励、观测、终止与课程 |
| source/climb_skill/climb_skill/learning/ | PPO、Actor/Critic、AMP、参考相位匹配 |
| tests/ | CPU行为回归；config_cases.py是旧功能回归测试数据，不是可运行训练配置 |
| validation/SHA256SUMS | 当前源码完整性清单 |

18维执行目标包含12维学习腿残差和固定为零的6维臂残差；机械臂保持初始关节位置。没有更改质量、PD、力矩能力、动作或观测顺序。
本次整理没有改动奖励、课程、观测、动作、PD或训练网络。已有训练结果不等于正式跨仿真验收通过。

本次模型与录像分别按修改时间选最近10个；不足10个取最近5个，不足5个全取。未选中的本地文件不删除。
