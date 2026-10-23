# Climb V1 / model_900：MuJoCo 初步 Sim-to-Sim

这里只迁移你已经训练好的 V1 第900轮策略，不训练、不包含技能切换。原训练源码与配置没有修改。

目标 Windows 目录：`C:\Users\zyh\Desktop\MuJoCo\climb_v1_900`。服务器无法直接读写 Windows C盘，因此先在服务器验证，再将完整 ZIP 复制到本机解压。不要只复制 actor.pt。

## Windows 运行

在 **Anaconda Prompt** 中执行：

```bat
conda env list
```

若有 `mujoco` 环境，就激活并检查：

```bat
conda activate mujoco
python --version
python -c "import mujoco, torch; print(mujoco.__version__, torch.__version__)"
```

本包测试组合是 Python3.11、MuJoCo3.12.0、PyTorch2.7.0 CPU。已有环境若同时装了Isaac，或版本不同，建议创建专用环境：

```bat
conda create -n go2-mujoco python=3.11 -y
conda activate go2-mujoco
```

进入解压后的目录，安装依赖（已有匹配版本会跳过）：

```bat
cd /d C:\Users\zyh\Desktop\MuJoCo\climb_v1_900
python -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python verify.py
python play.py
```

`python play.py` 打开 MuJoCo 窗口，单回合20cm平台。图形窗口使用本机 OpenGL；MuJoCo标准物理在CPU，不需要GPU版Torch。鼠标操作沿用MuJoCo viewer。正常运行到原任务成功、失败或24秒超时退出；退出码0是原V1登台成功，2是失败、超时或调试截断。异常退出码1并写报告。

录像可与窗口同时启用；也可以不打开窗口：

```bat
python play.py --video
python play.py --headless --video
```

默认输出到本包 `outputs/play-时间戳/`。视频960×540、25fps，包含实际模拟到终态的过程，不循环，不在10秒截断。

## 服务器运行

```bash
conda activate go2-mujoco
cd /mnt/miaojigui/zyh/climb_skill/sim2sim
python verify.py
python play.py --headless --video
```

若Conda按名称找不到服务器环境：`conda activate /mnt/miaojigui/conda/envs/go2-mujoco`。服务器默认使用EGL离屏渲染；无EGL的机器可自行选择适合该机器的MuJoCo渲染后端。

## 参数

| 参数 | 含义 |
|---|---|
| `--box-height 0.20` | 台面高度，默认20cm，范围(0,20cm]；不是新课程 |
| `--seed 42001` | 初始X/Y/yaw、腿小扰动和执行器延迟的种子；不同后端同种子不等于同初态 |
| `--episodes 4` | 顺序运行4回合，每回合分别保存录像/轨迹 |
| `--randomize` | 启用训练范围内的附加质量、摩擦、腿PD随机化；默认名义参数对照 |
| `--steps 100` | 只跑100控制步调试；未完成必须标记incomplete，不能算成功 |
| `--device cpu` | 策略推理设备；MuJoCo物理始终CPU |
| `--output 路径` | 指定新的输出目录；拒绝覆盖已有目录 |

起点仍使用原checkpoint的范围：X±0.1m，Y±0.08m，yaw±0.06rad，根高度0.33m；不新增落稳控制器，不修改关节目标。原V1起步地面站稳至少1秒、稳定0.3秒后，0.8秒逐渐放开动作，3秒仍未就绪判失败。

## 迁移内容与文件职责

| 文件 | 作用 |
|---|---|
| `play.py` | GUI/无窗口运行、完整回合录像、保存报告和逐物理步轨迹 |
| `bridge.py` | 模型构建、923维观测/历史、动作映射、延迟PD、重力补偿、原V1终止 |
| `policy/actor.pt` | 从指定model_900严格加载并导出的TorchScript部署分支；推理不需要Isaac、AMP数据或判别器 |
| `policy/contract.json` | 原checkpoint哈希、900轮、配置、关节顺序、Actor来源和导出检查 |
| `policy/observations_reference.py.txt` | 该次训练的真实观测源码快照，仅供verify进行数值对照 |
| `verify.py` | 文件哈希、观测/历史与训练源码数值对照、关节/执行器映射和力矩裁剪检查 |
| `prepare.py` | 在服务器读取原V1 checkpoint和该次训练源码快照，重新导出；普通运行无需执行 |
| `package.py` | 创建独立Windows/Linux ZIP，包含代码、Actor、公共MuJoCo资产、哈希与来源说明 |
| `robot/` | 只在独立ZIP中存在；仓库运行时读取公共 `asset/go2_piper/mujoco/` |
| `SHA256SUMS` | 独立包文件校验清单；本机不依赖服务器绝对路径 |

公共MuJoCo资产由现有机器人XML作视觉/拓扑底稿，使用与**当前共用USD五个文件哈希匹配**的profile替换惯量、质量、关节轴/范围、固定连接与碰撞。机械臂安装高度来自profile为7cm。运行时不调用 `history/`、Push策略、旧规划器或旧切换代码。模型数据首次提取来源保存在公共资产 `PROVENANCE.json`。

## 控制与观测合同

- 物理dt=0.005s（200Hz）、策略每4步推理（50Hz）。显式顺序FL/FR/RL/RR，每腿hip/thigh/calf，再joint1..6。
- 923维：69本体+132解析高度+3速度占位+29特权占位+10×69历史。部署history分支不读取3+29占位，用自身估计器预测速度；verify检查占位变化不影响输出。
- 高度点顺序为12个X（−0.45～1.2m）×11个Y（−0.75～0.75m），按机身yaw变换。高度图和箱高仍来自已知仿真几何，**不是视觉感知**。
- Actor输出18维：前12维腿残差，后6维补零；腿目标=默认角+0.25×动作，不是增量积分。保留±1.2rad偏移、0.9软关节范围、后腿目标工作范围。臂保持本回合参考角。
- 腿Kp=30、Kd=0.6；臂Kp=[50,50,80,30,30,20]，Kd=[3,2,3,3,2.5,1]。只有臂施加重力补偿，不施加基座悬浮力。
- 腿hip/thigh限矩23.7Nm、calf45.43Nm；臂限矩[20,20,15,7,5,5]Nm。PD+补偿合计后裁剪；每个物理步记录原力矩、实际力矩及饱和次数。延迟0～4个物理步，腿同组、每个臂关节独立组。
- 速度能力hip/thigh30.1、calf15.7、臂3rad/s逐步监控；此版没有把MuJoCo速度约束声称为PhysX求解器的等效硬限制。
- 默认名义质量，不给base新增随机负载；滑动摩擦用0.6近似原名义动态min混合值。MuJoCo与PhysX没有完全相同的静/动摩擦切换和接触求解器；`--randomize`也不复现Isaac随机数流。

## 如何判断结果

`report.json` 明确区分success、failed、timeout、incomplete和异常。每回合记录实际延迟、峰值力矩、饱和次数、速度超限次数、峰值臂误差、根位置和登台承重情况。`trace_000.npz`逐5ms保存位置、速度、目标、原始/实际力矩，可用于排查关节顺序、超调与饱和。

**成功语义沿用V1**：四足均在安全顶面、近期承重、机身越过箱沿1.55m等几何条件连续0.3s；提交时至少两足承重、倾角<0.3rad、臂误差<0.08rad。它允许箱顶继续走，不是上台停稳。初步迁移保留这个原任务，尚未实现NAV入口、技能切换或新的停稳任务。

`verify.py`通过说明接口检查通过；单回合录像不是批量验收。正式结果仍需Isaac/MuJoCo各两组独立32回合、每组至少30成功，并核对控制/资产来源；此包不等于可以上真机。
