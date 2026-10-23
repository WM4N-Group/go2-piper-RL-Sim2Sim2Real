# GO2-PIPER 总交接

更新：2026-10-16。面向新小组的接手入口；具体成绩只在对应技能页维护。本项目对象为**GO2-PIPER**，源项目保留ARX5历史工具。

<a id="当前工作范围"></a>

## 任务、状态与方向

本组负责可复现、可审计的NAV/PUSH/CLIMB底层技能及其平稳切换，最终经过跨仿真筛查与标定进入分级实机。**2026-10-15用户将当前主线调整为同一连续物理回合内NAV→CLIMB→NAV的稳定接管；NAV→PUSH→NAV已有基线和未解决问题继续保留。** 不重训平地NAV，先提高鲁棒性、保留成功路径，再提高效率。

目前NAV使用冻结基线；PUSH v212可供其他小组在明确负载域内复现完整推箱。NAV→CLIMB→NAV已在v062/v064同一控制器的3个已用开发起点全部完整成功，但该版制动臂参考速度交接不连续；修复版v066/v067已在3个起点完整成功并通过该边界平滑审计，但v068扩展的3704在37s触发CLIMB腕部子步力矩上限，余4例未运行；目前同版为已运行4例中3成功/1失败。动态反馈幅度对照均未修复。v078加强地面重载后的实际参考停稳确认，越过原37s失败点，但仍在95.94s触发腕部力矩终止；v079三例未运行，该CLIMB评估和条件队列已结束。该较晚CLIMB瞬态待原生NAV入口合同对齐后继续定位。只读审计另确认当前NAV末端目标与原交接默认值不同，出口NAV活动期持续改写臂输出；下一步先对齐原技能输入/起止边界和执行模式，再做桥接验证。整链仍需约5分钟，鲁棒性、效率、正式未用种子验收和全片原速人工审阅尚未完成。详见CLIMB页，不能把不同版本成绩合并。

NAV→PUSH→NAV的v317同版8/8开发基线保留，有限时长返程NAV候选v319为3/4，另1例腕部子步力矩触发门禁；该线当前不继续试参。显式参考保护介入样本不计原生18轴直通。最新PUSH/CLIMB均未完成来源匹配的正式跨仿真验收，统一切换SDK尚未交付；实机接入／标定线按main的2026-10-19安排启动，当前尚无实机执行结果。**单技能功能跑通、整链任务成功、执行参考平滑、正式验收和实机放行分别记录。**

独立NAV对照确认旧链末端指令、启动、持续臂输出改写及物理条件与原参考不同。当前已取得保持原权重／名义PD、当前限矩下的参数化原生行走段和显式退出开发证据；可用指令工作点为link0系EE=(0.45,0,0.45)。初始化位移已有固定参数开发达标，实际到点及箱前／平台连续场景仍需验证，具体成绩与活动入口见CLIMB页及本地产物`nav-native-entry-current.json`。原参考100Nm录像不作为当前限矩验收。

日常同步按`/opt/project-coordination/反馈与同步/Sim2Real组/`固定三页维护。内部实现、调试和一般进度写进展／计划；需要明确跨组答复或主组决策时，才在唯一问题主记录中登记。本轮没有新增跨组确认请求。

## 五份常用文档

| 文档 | 唯一维护内容 | 接手时重点 |
| --- | --- | --- |
| [总交接](AGENT_HANDOFF_CN.md) | 方向、分工、接收与续跑流程 | 本页先读 |
| [项目计划](PROJECT_PLAN_CN.md) | 目标、合同、验收和交付顺序 | 明确什么才算完成 |
| [PUSH交接](PUSH_CURRENT_HANDOFF_CN.md) | v212基线、切换候选、失败、来源和复现 | PUSH复现及保留的切换基线 |
| [CLIMB交接](CLIMB_CRAWL_STATUS_20261001_CN.md) | iy阶段回归、耗时、边界和迁移 | 当前首要开发入口；登台完成不含后续NAV到点 |
| [安装与标定](GO2_PIPER_MOUNTING_CN.md) | 固定安装假设与后续实机条件 | 无实机接触授权 |

逐版诊断、旧PID和过时待办收在[历史实验档案](archive/EXPERIMENT_HISTORY_CN.md)，不作为当前运行状态。保留这五个入口，避免继续新增重复“最新状态”文档。

## 新小组分工与当前可推进事项

| 负责方 | 现在可以做 | 交付/边界 |
| --- | --- | --- |
| 底层技能/本组接手者 | 推进真实NAV台前停靠、CLIMB完成信号与连续入口/出口，保留既有PUSH整链及CLIMB登台路径 | 冻结来源、技能/过渡状态、完成/失败码、执行器历史和安全证据；不把不同候选成绩拼起来 |
| reachability | 消费固定版本的真实READY状态；继续资格公式、离线配对、校准与caller适配 | 明确`t_plus/s_plus`、资格有效期与删失标签；目前真实正例资格仍abstain，尚无正式在线放行策略 |
| world-model | 维护场景与目标可行性、Oracle/caller、50Hz因果数据和版本化对照 | 模型保持shadow；旧PIPER整链正例不覆盖本组新PUSH/过渡版本 |
| 三方共同 | 对齐对象/目标、坐标、历史、18轴权限、无reset、时间预算与失败出口 | 同初态配对回归，区分技能改善、控制改善与模型收益 |

其他两组可并行推进，并非必须等底层全部完成；但不能使用未冻结的新候选扩大安全结论。2026-10-14只读核对：world-model分支`go2-piper-worldmodel`提交`4fadaa3`，主文档`docs/PIPER_SKILL_SOURCE_CN.md`；reachability分支`feature/go2-piper-reachability-p0`提交`362f3cf`，主文档`docs/AGENT_HANDOFF_CN.md`。更早交接的来源和设计理由见[项目计划](PROJECT_PLAN_CN.md#平稳切换改进方案2026-10-13待实施验证)。本次未修改其他组代码或替其开启实验。

## 新小组接收清单

新开发仓库为 `WM4N-Group/go2-piper-RL-Sim2Sim2Real`，默认分支 `main`。开发来源为 `GO2-ARX5-MUJOCO` 的 `feature/go2-piper-sim2real` 及本地已提交的最新更新；具体提交见根目录 `RELEASE_MANIFEST.json`。

| 接收内容 | 本仓库位置与核对方式 |
| --- | --- |
| 完整开发源码与说明 | 根目录source、scripts、mujoco、sim2real、docs；清点范围见发布清单，未提交诊断不混入 |
| NAV冻结权重与当前原生入口 | 历史策略包的NAV policy.pt；`skills/nav/entry-v039`和本技能run.py入口 |
| PUSH v212 | `skills/push/v212/`的完整train、双模型、几何依赖、计划和录像参数 |
| CLIMB iy | `skills/climb/iy/`的完整train、actor、bank、plan/jobs和12源payload |
| 切换开发对照 | `integrations/`下v317与v067，保留成功路径和已知边界，尚非稳定SDK |
| 文件与环境检查 | 分别执行 `python skills/nav/verify.py`、`python skills/push/verify.py`、`python skills/climb/verify.py`；环境版本和命令见[运行材料](../skills/README.md) |

每条技能在新输出目录执行。生成的报告、录像和环境目录不提交Git。历史大报告及iv/ix逐值对照不作为单技能重放输入；已有开发证据不等于接收环境已复现。Isaac环境、驱动和资产扩展需要接收方自行具备，本次未交付一键系统安装包。

## 公共路径和原始基线

- 运行环境由`SIM_HOST`选择；产物根目录根据接收方的文件布局配置。
- 当前PUSH/切换/迁移根：`/path/to/artifacts/go2-piper/sim2sim-current-20261008-a/`。
- 本地仓库外产物根：`/path/to/workspace/artifacts/go2-piper/`；这里只按需保存，不保证远端完整镜像。
- Isaac启动器：`/path/to/bin/isaac-python`，环境`/path/to/envs/isaac/`。MuJoCo使用各自原诊断记录的隔离环境，不能混装。
- 本地静态/数学工具环境：`../.envs/go2-arx5-nav/bin/python`；训练、物理评估和录像全部在既有远端执行。
- NAV actor远端：`/path/to/artifacts/go2-piper/2026-09-15/eval-t8FO0a/piper-nav-baseline-bundle/policy.pt`，SHA256 `72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8`。
- 仓库通用入口：`scripts/evaluate_box_skills.py`、`scripts/rsl_rl/train.py`及`source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/`；实际重放使用技能页匹配快照，不能以仓库HEAD代替。

<a id="开始或恢复工作"></a>

## 环境与首次核对

2026-10-07读取的远端环境参考：Python3.11.16、Isaac Sim5.1.0.0、Isaac Lab0.54.4、isaaclab_rl0.5.2、isaaclab_tasks0.11.16、rsl-rl-lib5.0.1、PyTorch2.7.0+cu128、NumPy1.26.0、Gymnasium1.2.1。版本来自分发元数据，不代替依赖锁定；仓库`requirements.txt`是MuJoCo工具要求，不是Isaac安装清单。

以下只读检查不启动仿真：

```bash
git status --short --branch
git rev-parse HEAD
ssh -o BatchMode=yes -o ConnectTimeout=15 "${SIM_HOST:?请设置运行环境}" \
  'pgrep -af "[p]robe.py|[r]un-push-screen.py|[r]un-screen.py|[r]un-remaining.py|[r]un-pair.py|[r]un-and-audit.py|[v]ideo-after-screen.py|[f]ollowup-after-diagnostics.py|[v]ideo-after-stow.py|[e]valuate_residual_push.py|[e]valuate_box_skills.py|[s]cripts/rsl_rl/train.py|[v]erify-after.py|[a]udit-after.py|[r]un.py"; nvidia-smi'
```

用`nvidia-smi`核对设备编号和实际占用。设置`CUDA_VISIBLE_DEVICES`后进程内`cuda:0`不等于物理GPU0。同一实验只由一个负责人启动；监督器/录像观察器也要查，避免评估刚结束又被重复拉起。

首次接手按顺序完成：

1. 查分支、现有改动、GPU/进程、候选计划与实际报告；旧PID/摘要/心跳不证明运行或成功。
2. 收齐对应版本和依赖，逐项核对哈希、控制合同、物理参数与资产。先复现已知开发起点，输出到新目录，核对报告与来源。
3. 对当前失败点做与已成功版本同初态的对照，固定一个改动因素；保留成功基线，不重放固定路径覆盖证据。
4. 记录完整命令、cwd、环境、GPU、种子、PID、退出码与终态。进程退出0不等于成功，缺失终态与正常失败分别计数。
5. 改动只更新对应技能当前页；稳定里程碑集中提交Git。按用户要求正常同步本地小型产物，减少GitHub冗余推送。

## NAV消费契约及尚未交付的接口

NAV历史MuJoCo随机目标证据98/100（2次超时）见历史包索引，不能代替当前切换验收。输入210维按观测项分组拼接3帧，输出18维覆盖腿12轴/臂6轴；不能按3个70维向量简单串联，也不能只接12腿后假定原生全身行为不变。切换历史必须记录实际组合执行命令。

历史包[消费契约](../sim2real/go2-piper-low-level-policy-handoff/README_CN.md#nav)与`config/nav_deploy.yaml`描述旧部署侧配置；当前Isaac冻结源腿PD为30/0.6，髋默认角FL/RL +0.1、FR/RR −0.1。旧MuJoCo YAML中的35/0.8不能直接当作Isaac参数。新caller应以匹配源和实测`actuator-contract.json`核对关节顺序、默认角、缩放、PD、限位与延迟，参数不同必须显式建版本。

统一SDK尚未发布；独立CLIMB在线完成信号已有连续物理开发正例，完整NAV↔CLIMB及重复PUSH对象重绑定仍需验证/实现。其他组旧PIPER整链正例与ARX5旧executor都不覆盖本组新候选。调用方负责目标/对象/坐标与预算，本组负责控制适配、真实完成/失败及经验证的保持/退出；双方共同验证首命令、历史和无reset。详细合同见[项目计划](PROJECT_PLAN_CN.md)。

## 当前sim2sim入口

[mujoco/diagnose_current_piper_sim2sim.py](../mujoco/diagnose_current_piper_sim2sim.py)是早期迁移诊断入口，使用旧PUSH226→12和CLIMB短窗口，**不能直接运行最新v212的226→19加独立腿hook，也未移植完整逐脚阶段控制器**。最新功能、诊断和迁移待办分别在PUSH/CLIMB页；静态FK或短窗口无碰撞不能当完整任务通过。MuJoCo作为任务级独立风险筛查，不要求与Isaac每步轨迹一致，但未解释的碰撞、失稳、超限和停止失败必须解决。

<a id="后续如何维护"></a>

## 产物保留与文档维护

按`../artifacts/go2-piper/LOCAL_STORAGE_POLICY.md`按需保存。2026-10-10已核对远端SHA后删除164份本地历史大报告/日志、释放126.1GiB；这是历史清理结果，不是今日磁盘使用率。清单和恢复工具位于`../artifacts/storage-cleanup-20261010/`。不要递归同步历史巨型JSON/日志/中间权重；保留当前候选、必要回退、摘要、源码、视频和证据索引。缺少旧本地报告时按清单恢复单文件，远端原件不因本地清理删除。

<a id="本次文档审计范围"></a>

本次审计覆盖README、五份当前文档、历史归档入口、ARX5原型说明、两份历史包README及训练边界；上游行为准则/贡献规范/版本日志保持原用途。文件完整性以本分发包的校验清单为准。未将未提交候选代码混入交接。交接链接与包校验和已经检查；物理新结果引用远端现有实验，文档更新本身不等于重新验收。


## 用户训练分支 zyh（2026-10-19）

Climb训练源码已并入主仓库，历史bundle随源码交付，无嵌套仓库。用户要求的最近10个模型与最近10个录像通过Git LFS上传，日志和环境不提交；此项是用户训练档案交付，不改变上述冻结策略与验收结论。清单见 `climb_skill/versions/publication.json`，操作见 `climb_skill/README.md`。

本次模型与录像分别按修改时间选最近10个；不足10个取最近5个，不足5个全取。未选中的本地文件不删除。

## 2026-10-19目录整理

正式阅读和运行入口改为 [skills](../skills/README.md)、[integrations](../integrations/README.md) 和 [目录计划](PROJECT_LAYOUT_CN.md)。前开发者PUSH v212、CLIMB iy及NAV入口已分开，用户AMP工程保留唯一climb_skill；旧包移入archive，runtime_handoff链接已移除；sim2real和mujoco旧路径暂保留兼容链接。冻结内容和已有验收结论未改变。

2026-10-19独立入口调整：tools已移除，skills/nav、skills/push、skills/climb各有独立run.py、verify.py和SHA256SUMS；两条integrations也各有独立入口。NAV获得原配套运行树的独立副本，不再借用CLIMB目录。用户AMP工程不改。


## 用户 PUSH 重训工作范围（2026-10-19）

本地 `zyh` 分支新增独立 [push_skill](../push_skill/README.md) 候选，采用单腿策略+确定性IK，关注接触前足点不动与承重稳定。旧v212/原Climb不修改。任务参数和当前验证维护在 [PUSH交接](PUSH_CURRENT_HANDOFF_CN.md) 与工程README，不把技术smoke当稳定性结论。用户负责长时间训练；新候选无实机部署授权。
