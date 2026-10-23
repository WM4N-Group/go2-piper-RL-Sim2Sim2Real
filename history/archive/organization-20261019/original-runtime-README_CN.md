# 独立技能与切换开发运行材料

更新：2026-10-16。此目录交付匹配的控制源码、权重、配置、机器人资产和运行计划。它支持已有功能重放与后续开发；不代表技能切换、跨仿真或实机已经正式验收。

## 1. 接手顺序

1. 阅读仓库根 README、`docs/AGENT_HANDOFF_CN.md` 和 `docs/PROJECT_PLAN_CN.md`。
2. 在仓库根执行 `python3 runtime_handoff/verify_delivery.py`，全部通过后开始工作。
3. 使用已有的独立 Isaac 环境检查依赖，选择下列单技能入口，输出到新的目录。
4. 核对新报告、终态与原速录像，再做控制改动；保留已有成功版本。

仓库根 `SHA256SUMS` 校验全部交付文件，`RELEASE_MANIFEST.json` 记录源版本、文件范围及交付边界。权重和资产以普通 Git 文件交付，无需另行下载模型。环境目录、Isaac 软件本体、巨型历史轨迹、训练日志和中间权重不属于源码交付；它们不作为以下运行入口的文件输入。

## 2. 目录与版本

| 目录 | 交付内容 | 已知边界 |
| --- | --- | --- |
| `PUSH-v212/` | 完整匹配 train、几何运行时、model255、独立腿 model199、运行及录像参数 | 用户认可的轻载推箱基线；不是跨仿真安全认证 |
| `CLIMB-iy/` | 完整匹配 train、304→18 actor、阶段 bank、plan/jobs、12 源 payload | 从箱沿阶段 bank 启动；280s 诊断窗口，约 3～4 分钟；不是普通 reset 独立成品 |
| `development/nav-native-entry-v039/` | 当前限矩下的原生 NAV 入口控制器及三开发种子审计 | 原权重／标称 PD，EE=(0.45,0,0.45)，准备位移约 5.2～6.7cm；未完成整链验证 |
| `development/nav-native-entry-video-v038/` | 与上述同控制逻辑的录像入口和依赖 | 10s 原生18轴行走；含较长准备阶段，不是到点导航；记录字体使用 Pillow 默认字体 |
| `development/transition-nav-climb-v067/` | 保留的 NAV→CLIMB→NAV 控制器、全部配套模块、计划和审计 | 同控制器三起点曾成功；扩展起点腕部失败，NAV 输入／输出合同仍待修正；仅供对照 |
| `development/transition-arm-entry-v317/` | 保留的 NAV→PUSH→NAV 控制器、依赖、开发审计 | 八个已用开发起点通过；未用种子／正式验收未完成 |

NAV 冻结权重在 `../sim2real/go2-piper-low-level-policy-handoff/policies/nav/policy.pt`。旧 `sim2real/` 包中的 PUSH/CLIMB 是九月历史模型，不要替代本目录的 v212/iy。

源码快照与主树同名文件可以不同；统一入口通过匹配快照执行。`plan.json` 绑定本次交付哈希，`upstream_*` 保留路径适配前的来源哈希。PUSH 只将资源定位改为显式环境变量；控制常数、双模型、碰撞、35mm 净空及执行器门禁保持原值。CLIMB bank 只适配来源路径元数据，状态数值保持不变。

## 3. 环境

已记录的运行环境为 Python 3.11.16、Isaac Sim 5.1.0.0、Isaac Lab 0.54.4、isaaclab-rl 0.5.2、isaaclab-tasks 0.11.16、rsl-rl-lib 5.0.1、PyTorch 2.7.0+cu128、NumPy 1.26.0、SciPy 1.15.3、Gymnasium 1.2.1、MuJoCo 3.12.0、Pillow 11.3.0、imageio 2.37.0、imageio-ffmpeg 0.6.0、PyYAML 6.0.2。这是已用环境记录，不是新机器安装锁文件。仓库根 requirements 不能代替 Isaac 环境。

PUSH 虽在 Isaac 执行，几何查询仍导入 MuJoCo Python 库。不要把 MuJoCo 迁移环境和 Isaac 环境的依赖混装到系统 Python。先在已有项目环境运行：

```bash
export ISAAC_PYTHON="/path/to/isaac-environment/bin/python"
"$ISAAC_PYTHON" runtime_handoff/verify_delivery.py --environment
```

物理运行需要可用的 NVIDIA GPU、匹配驱动及 Isaac 资产扩展。独立回放包含录像，会启用相机；启动前检查实际显存和已有进程。

## 4. 单技能命令

从仓库根执行；输出路径必须不存在。以下命令默认只校验、复制运行树并写 `run-plan.json`。要执行物理评估，在对应命令后加 `--execute`。已准备过的目录不能重用，防止覆盖证据。

```bash
# 当前限矩下的独立 NAV：准备、有限交接、10秒原生行走和原速录像。
python3 runtime_handoff/run_independent.py nav \
  --isaac-python "$ISAAC_PYTHON" --gpu 0 \
  --output-dir "$PWD/outputs/nav-001" --execute

# PUSH v212：原 seed3701、8环境、48秒窗口与相机参数。
python3 runtime_handoff/run_independent.py push \
  --isaac-python "$ISAAC_PYTHON" --gpu 0 \
  --output-dir "$PWD/outputs/push-001" --execute

# CLIMB iy：原 seed27302、32环境、280秒阶段诊断及env28录像。
python3 runtime_handoff/run_independent.py climb \
  --isaac-python "$ISAAC_PYTHON" --gpu 0 \
  --output-dir "$PWD/outputs/climb-001" --execute
```

独立 PUSH 的箱体为 1.2×1.2×0.2m、质量1kg、静／动摩擦0.15、推进目标0.60m。其226→19模型必须与独立腿 model199 和冻结腿 hook 一起使用。

CLIMB 是零残差 actor 加阶段控制器，不是只加载模型就能执行；从 bank 起点初始化只属于这条独立重放命令，连续切换入口禁止中途注入 bank。32环境完整报告约3.9GB，需预留报告、视频与运行树空间；不要将生成结果提交 Git。

NAV 默认用开发 seed3703，可用 `--seed 3701` 等选择开发起点。使用原权重和当前机械臂力矩上限20/20/15/7/5/5Nm，EE工作点0.45/0/0.45；不能把这段结果写成原默认0.5/0/0.4已完全恢复。旧定速诊断 `scripts/check_piper_native.py` 仍保留，旧参考的100Nm评估录像不作为当前限矩通过证据。

## 5. 切换开发对照入口

以下命令用于复现开发对照，不是已发布的稳定SDK：

```bash
python3 runtime_handoff/run_independent.py nav-push-nav \
  --isaac-python "$ISAAC_PYTHON" --gpu 0 --seed 3701 \
  --output-dir "$PWD/outputs/nav-push-nav-001" --execute

python3 runtime_handoff/run_independent.py nav-climb-nav \
  --isaac-python "$ISAAC_PYTHON" --gpu 0 --seed 3701 \
  --output-dir "$PWD/outputs/nav-climb-nav-001" --execute
```

这两条保留原物理连续回合，没有中途 reset、状态库注入或执行器队列清空。旧监督器和队列脚本保留作开发追溯；新回放使用本页统一入口，避免依赖早期实验目录。

当前开发重点：保留各技能原始输入／输出及起止合同，先分别验证NAV真实到点停稳、CLIMB连续入口和出口，再接回整链；不要把独立NAV初始化直接用于台上中途接管。先保证成功率，再缩短等待和规划耗时。

## 6. 输出与核验边界

每条入口写 `run-plan.json`、`run.log`、`exit-status.json`。PUSH/CLIMB 的报告和视频在输出目录根；NAV及切换开发的报告在 `result/`，NAV原速视频也在该目录。

- PUSH：读取完整终态、失败、缺失、箱体目标误差、速度和持续停稳；目标误差<0.12m、箱速<0.08m/s持续0.5s，并保持合法接触和所有失败门禁。
- NAV：当前入口检查原生执行、准备位移、初始化在内的力矩及10s行走，不宣称完成目标导航。
- CLIMB：旧评估器完整目标成功字段与逐脚登台／展开／承重停稳是不同指标。不得把退出码或旧 `successful_episodes` 单独当作阶段完成结论。本包未新增独立完成验收器；原 iv/ix 全轨迹逐值对照等历史审计不是重放输入。
- 切换：从新报告检查各阶段、真实完成／失败、历史与力矩；开发成功不替代两组未用种子及跨仿真验收。

本次发布检查文件完整性、来源、可迁移命令及静态依赖。接收环境中的完整物理回归和原速全片人工检查仍须实际执行后记录，不能因文件校验通过而声称仿真通过。
