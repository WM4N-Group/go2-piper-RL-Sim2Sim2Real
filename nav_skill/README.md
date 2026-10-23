# Nav：上游原配置 Go2Piper WBC

来源：[zzzJie-Robot/LeggedManip_Lab](https://github.com/zzzJie-Robot/LeggedManip_Lab)，固定提交 `4e12109d1eccb1d9da2e4a35f189fabea3f13677`。本目录保留上游训练Python、配置、脚本和文档；其他机器人资产和大演示未下载。当前只支持已配置的Go2Piper。

2026-10-21恢复：训练/回放脚本、WBC配置、PPO和奖励全部与该上游提交一致。关闭本地新增速度课程，初始根高度恢复0.35m，移除保存后自动录像。仅保留公共USD路径适配，以及根目录train.py/play.py便利入口；共用USD的五个文件与上游Git blob一致。精确剩余差异见 `LOCAL_CHANGES.patch`，检查结果见 `RESTORE_UPSTREAM_CHECK.json`。

## 2026-10-22 重新拉取与 tmux 从头训练

已从上游重新 fetch `master`，最新提交仍是 `4e12109d1eccb1d9da2e4a35f189fabea3f13677`，没有新提交。重新同步上游 Python、配置、脚本、文字说明及依赖清单；唯一源码适配仍为共用 USD 路径，模型字节与上游一致。重新同步前的代码备份已按用户要求删除；所有旧权重与日志留在原位。核验清单见 `UPSTREAM_REFRESH_20261022.json`。本次未启动训练。

**重要更正：关闭课程不等于一直用 ±0.2 的初始速度。** 原版 `mdp/curriculums.py` 在课程关闭时执行 `cfg.ranges = limit_ranges`，运行时可覆盖保存的初始配置。因此不能仅凭 `params/env.yaml` 的初始 `ranges` 断言整次训练没有高速命令；课程日志 `-1` 也不代表速度为零或课程失败。此前对“9999 轮没有训练过高速”的判断撤回。单独回放的质量仍须用实际指令和物理结果判断。

在服务器 SSH 终端创建新会话（tmux，不是 tmax）：

```bash
tmux new -s nav-upstream
```

进入后运行上游 README 的 WBC 示例，显式选择 GPU，不加恢复参数：

```bash
conda activate go2-piper
cd /mnt/miaojigui/zyh/nav_skill
python train.py --task GO2-PIPER-WBC --headless --device cuda:0 --num_envs 4096 --max_iterations 5000
```

上游 README 使用 5000 轮作为示例；PPO 配置默认上限为 10000。这里命令明确采用 5000。每1000轮保存，默认不录像；5000轮不保证收敛或步态合格。产物写入 `logs/rsl_rl/go2_piper_wbc/新时间戳/`，不覆盖旧训练。

离开并保持训练：按 **Ctrl+B，全部松开，再按 d**。如快捷键失效，在另一个 SSH 终端执行 `tmux detach-client -s nav-upstream`。重新连接用 `tmux attach -t nav-upstream`。不要用 Ctrl+C 离开训练。服务器本身保持运行时，本机休眠或关机不影响已脱离的 tmux 训练。

## 从头训练（自选训练轮数）

```bash
conda activate go2-piper
cd /mnt/miaojigui/zyh/nav_skill
python train.py --headless --device cuda:0 --num_envs 4096 --max_iterations 10000
```

不要加 `--resume`、`--load_run` 或 `--checkpoint`，这样才是从头训练。默认选择 `GO2-PIPER-WBC`。每次在 `logs/rsl_rl/go2_piper_wbc/时间戳/` 创建新目录；保留旧训练权重、日志和录像。每1000轮保存权重，**默认不录像、不启用相机、不启动回放子进程**。不需要另加关闭录像参数，也不要加 `--video`。RSL-RL编号从0开始，可能另有model_0和非1000倍数的最终权重。

原环境 go2-piper 保持不变；显存不足可把4096减为2048，这属于并行数变化。本次重新拉取不自动启动训练，也不停止其他用户进程。

## 原版训练是什么

- 机器人Go2Piper，全身WBC，平地，无高度地形课程。控制50Hz，物理200Hz，回合20秒，默认4096并行。
- **底盘速度与机械臂末端课程都关闭，这是该Go2Piper WBC上游默认。** 公共课程函数在关闭时将采样范围切到 `limit_ranges`，不是永远保持JSON中较小的初始ranges。日志课程值−1表示关闭。
- 底盘训练范围：X±1.0m/s、Y±0.6m/s、yaw±1.0rad/s；10秒重采样，10%静止环境。
- 末端训练范围：X=0.45～0.7m、Y±0.35m、世界Z=0.1～0.8m；roll±π/3、pitch±π/4、yaw±π/6，8～10秒重采样。坐标定义以pose_command_wbc.py为准。
- 上游名义初始根高度0.35m，默认机械臂角全零。reset会随机化实际状态；这不是技能切换接管保证。
- Actor/Critic隐藏层[512,256,128]、ELU；Actor210维观测、18维相对默认姿态关节位置动作，缩放0.25。Actor不使用相机或地形扫描。
- PPO每轮24步，5epoch、4minibatch，学习率5e-4、自适应KL，clip0.2、gamma0.99、lambda0.95、entropy0.005、目标KL0.01、梯度上限1.0、初始std1.0。10000轮，每1000轮保存权重。
- WBC奖励覆盖权重：末端位置4.5、末端姿态−4.0、XY速度3.5、yaw速度2.5、站高0.25（目标0.28m）、非水平−0.5、长腾空−1.0、腾空时间方差−1.5；其余奖励继承公共环境。没有新增调参。

## 旧训练为什么看起来没有进阶

读取TensorBoard日志的结果：`2026-10-20_20-33-23`的X速度/转向课程均从0.2升到1.0；第3039轮仍是1.0。`2026-10-21_10-34-54`续训没有恢复环境课程状态，重从0.2开始，第3148轮到0.35。末端课程一直关闭，−1不是升级失败。旧训练末期线速度跟踪加权奖励约3.20/3.5、转向约2.14/2.5，但奖励不能证明步态自然或接管可靠。

之前的独立Play使用完整命令范围；早期checkpoint可能是在较低速度课程训练的，录像条件与当时训练范围可能不同。自动录像会增加墙钟耗时，现有证据不能证明它导致动作变差。恢复上游用于建立明确对照，不保证原版效果必然更好。

## 训练后单独回放

默认不录像；有可视化桌面时：

```bash
python play.py --device cuda:0 --num_envs 1 --checkpoint /绝对路径/model_1000.pt
```

服务器确实需要录像时再单独运行上游功能：

```bash
python play.py --headless --device cuda:0 --num_envs 1 --checkpoint /绝对路径/model_1000.pt --video --video_length 1200
```

1200控制步约24秒，输出到权重所在目录的 `videos/play/`。上游Play也会导出JIT/ONNX模型，因此需要相应导出依赖；此前本地 `--skip-export`、`--video-output` 参数已撤销。Play随机速度与末端命令，不是固定臂姿态演示。

## 文件与修改位置

下列source路径相对 `source/LeggedManip_Lab/LeggedManip_Lab/`：

| 文件 | 作用 |
|---|---|
| `train.py` / `play.py` | 根目录便利入口，选择本目录源码与Go2Piper WBC任务 |
| `scripts/rsl_rl/train.py` / `play.py` | 原版上游训练、恢复、回放与可选录像脚本 |
| `tasks/manager_based/leggedmanip_lab/config/go2_piper/wbc_env_cfg.py` | WBC任务命令、奖励覆盖、Play配置 |
| `tasks/manager_based/leggedmanip_lab/config/go2_piper/agents/rsl_rl_ppo_cfg.py` | PPO网络、学习率、10000轮与1000轮保存 |
| `tasks/manager_based/leggedmanip_lab/leggedmanip_lab_env_cfg.py` | 公共观测、动作、场景、随机化、奖励与终止 |
| `tasks/manager_based/leggedmanip_lab/mdp/curriculums.py` | 原版课程更新与关闭课程后的完整采样范围 |
| `tasks/manager_based/leggedmanip_lab/mdp/pose_command_wbc.py` | 末端命令和坐标变换 |
| `assets/go2_piper/go2_piper_articulation_cfg.py` | 原版默认角、0.35m高度、PD、延迟；唯一源码差异是公共USD路径 |
| `UPSTREAM.json` / `LOCAL_CHANGES.patch` | 来源、剩余路径适配差异 |
| `ENVIRONMENT_CHECK.json` / `CHECKPOINT_VIDEO_CHECK.json` | **旧配置的历史检查**，不是本次恢复后新训练的结果 |
| `RESTORE_UPSTREAM_CHECK.json` | 本次逐文件上游一致性检查和旧日志诊断 |

## 环境与验证范围

现有go2-piper环境：Python3.11、IsaacSim5.1、IsaacLab0.54.4、rsl-rl-lib5.0.1。公共USD仍在 `../asset/go2_piper/go2_piper.usd`，可用 `CLIMB_ROBOT_USD` 覆盖。没有改动Climb、Push的控制代码。

本次完成源码逐文件对照、语法检查和公共资产哈希检查；未启动新训练，不宣称原版配置已取得新的效果或验收成绩。上游说明在 `README_UPSTREAM.md` / `README_CN_UPSTREAM.md`。

## 2026-10-22 Isaac右转诊断

model9999右前方目标测试、四段录像及指令/支撑/动作记录见[诊断结果](outputs/right-turn-isaac-20261022/RESULTS_CN.md)。本轮未复现翻倒，历史指令重建+零位臂案例达到停稳；条件尚未与Windows MuJoCo完全匹配，不能据此归因或作部署验收。训练配置未改变。
