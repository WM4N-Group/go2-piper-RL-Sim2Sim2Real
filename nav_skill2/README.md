# Nav Skill 2：Go2-Piper 速度行走策略

当前新训练版本为 **V4（symmetry_speed）**。先训练底层按机身坐标速度 `[vx, vy, wz]` 行走，上层到目标点和最终朝向的控制器以后实现。Isaac Lab 官方外部项目生成器生成的 DirectRLEnv 包，生成记录见 [docs/TEMPLATE_GENERATION.json](docs/TEMPLATE_GENERATION.json)。本包独立运行，只共享 `../asset/go2_piper/` 机器人资产。

网络内部预测 **12维腿动作，再补6个零**，输出18维相对默认姿态的关节位置残差。机械臂目标为零，但保留实际质量、惯量、PD与重力补偿。Actor输入315维历史本体观测；Critic额外使用训练特权信息，输入324维。没有地形或视觉输入，不训练登箱、避障或技能切换。

## V4优化内容

- **左右镜像一致性损失**：将完整观测历史和速度指令镜像，约束网络平均腿动作相应镜像，权重0.05，前200轮逐步加入。不是强制同一时刻左右腿同步，也不固定小跑节律。真实机械臂不完全对称，因此用软损失。
- **速度课程**：前进下限0.3m/s，上限依次0.4/0.55/0.7/0.85/1.0；纯转向幅值0.2至各级0.3/0.4/0.5/0.6/0.6rad/s。后退0.15～0.45m/s，侧移0.15～0.4m/s，具体上限随课程变化。混合运动的分量投影、起停平滑期间允许低于这些采样下限。
- **转向与停车练习**：原地转向占30%，站立15%；每回合末3秒平滑归零速度，学习减速停稳，不锁腿。
- **探索逐步降低**：初始动作标准差0.6；500～4000轮标准差上限降至0.25、熵系数从0.005降至0.001。减少训练噪声掩盖确定性策略不会走、不会转的问题。
- **AMP按方向和速度匹配**：9个真实参考片段，1879对原始状态转移，镜像后3758对。前进参考0.4/0.8m/s、转向参考0.2/0.5rad/s，训练1.0m/s和0.6rad/s使用最近档参考，未虚构对应精确示范。停车不用运动AMP。
- **起步承重**：创建环境时做至少3秒真实PD承重预计算（未收敛延长，最多10秒），reset恢复受力姿态，策略残差2秒渐入。没有焊接机身或强制站立等待阶段。

PD、真实电机力矩上限、默认姿态、动作顺序、延迟及Climb/Push/旧Nav未改。每个参数、奖励、课程升级条件和文件职责见 [配置说明](docs/CONFIG_CN.md)，版本差异见 [变更记录](docs/CHANGES_CN.md)。以上是训练设计，效果需训练和确定性回放验证。

## 从头训练：建议tmux

```bash
tmux new -s nav2-v4
conda activate go2-piper
cd /mnt/miaojigui/zyh/nav_skill2
python train.py --headless --device cuda:0 --num-envs 2048 --iterations 15000
```

先确认没有另一份4096环境训练占卡。2048为默认建议；4096应根据实际空闲显存决定。退出并保持训练：先按 `Ctrl+B`，松开后按 `D`；恢复会话：`tmux attach -t nav2-v4`。关闭本地电脑不影响服务器tmux内训练。

每 **100轮**保存完整权重、导出TorchScript并自动录像；末轮也保存。训练不开相机。录像暂停训练，默认CPU物理/策略、GPU渲染；有足够显存可加 `--video-device cuda:0`。每次七个案例，各12秒：前后左右、左右转向、前进左转，包含起步和停车，用当前课程中位等级的上限速度测试。录像失败保留checkpoint和错误日志并停止，便于查错。

```text
outputs/train-时间戳-随机后缀/
├── model_100.pt             完整PPO/AMP/优化器/课程/RNG，供续训
├── actor_100.pt             315维输入 → 18维输出，后6维恒零
├── config.json / run.json   生效配置、环境、源码/资产/数据哈希
├── source/ / scripts/       本次训练源码快照
├── metrics.jsonl            逐轮损失、奖励、探索、分行为响应、课程
├── episodes.jsonl           回合质量与升级资格
└── checkpoint_videos/model_100/
    ├── locomotion.mp4
    ├── report.json          每案例速度、超速比例、停车和失败原因
    └── trace.jsonl          指令、实际速度、18维动作/目标/力矩
```

## 续训与回放

V4续训使用完整 `model_*.pt`；`--iterations`表示**额外轮数**，配置从权重恢复，改JSON不会覆盖续训配置。

```bash
python train.py --headless --device cuda:0 \
  --resume outputs/你的V4目录/model_1000.pt --iterations 14000

python play.py --headless --device cuda:0 --suite --seconds 12 \
  --checkpoint outputs/你的V4目录/model_1000.pt
```

回放命令打印独立录像目录。单方向示例：加 `--command 0.3 0 0`（不要同时用 `--suite`），速度必须在所选课程范围内。可以加 `--level 4`测试最终范围，但低等级权重未必具备此能力。

**V3不能直接按V4续训**：判别器条件、数据和奖励合同已变，启动前会拒绝。当前入口支持按权重原配置回放V3；V3缺少新字段时保留旧速度容差、旧参考数据及起停行为。若需继续V3，使用对应冻结源码和原数据，不混用V4配置。

## 文件入口

| 文件/目录 | 用途 |
| --- | --- |
| `configs/nav.json` | 日常调速度、奖励、课程、PPO/AMP/镜像参数 |
| `source/nav_skill2/nav_skill2/tasks/direct/nav_skill2/parameters.py` | 参数定义、缺省值、校验和关节合同 |
| 同目录 `nav_skill2_env.py` | 物理环境、观测、奖励、重置、课程与外部速度接口 |
| 同目录 `commands.py` | 指令采样、平滑、方向响应与超速成本 |
| `source/nav_skill2/nav_skill2/learning/ppo.py` | PPO、12+6零输出、探索退火、镜像损失接入 |
| 同目录 `symmetry.py` / `amp.py` | 镜像映射 / 方向速度条件AMP |
| `data/amp_speed_pairs.json` | V4真实参考及来源哈希；旧`amp_pairs.json`供V3 |
| `scripts/train.py` / `scripts/play.py` | 训练、保存录像 / 确定性回放 |
| `scripts/prepare_amp_data.py` | 从固定上游原片转换AMP数据 |
| `docs/CONFIG_CN.md` | 参数解释、全部奖励权重、课程逻辑 |
| `docs/VALIDATION_CN.md` | 工程检查结果和验证边界 |

资产可用 `ROBOT_USD` 指定，数据可用 `NAV_AMP_DATASET` 指定；覆盖数据必须与版本和checkpoint哈希匹配。不要将环境依赖安装到系统Python。

`completed_without_fall`只表示没跌倒；`motion_and_stop_qualified`增加方向响应、停车和超速检查，也不是步态或真机验收。课程仍使用回合的分行为质量判断，没有把外部七案例录像设为升级硬门禁。技能切换和跨仿真验收另做。
