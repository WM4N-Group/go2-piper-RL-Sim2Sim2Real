# GO2-PIPER MuJoCo 三技能与切换

更新：2026-10-23。接手前先读本页，再读 [交接说明](HANDOFF_CN.md)。这是从本机开发工程整理的可迁移运行包，范围只有 **Nav、Climb、Push 和 Switch**；不是 Isaac 训练工程或真机部署包。

## 使用范围与当前状态

| 模块 | 已实现 | 使用边界 |
|---|---|---|
| Nav | 输入目标位置/朝向，先朝向目标、前进、末端调向，连续停稳后报告到达 | 已知地图、仿真真值定位；没有自动避障或路径规划 |
| Climb | V1/900 原 Actor 登台，随后 QP 制动、调整站姿并保持 | 沿世界 +X、居中的已知台面；高度参数 0～20cm，不是任意障碍攀爬 |
| Push | 双 Actor 推箱、安全展开、平滑接近、完成后收臂回零并站稳 | 当前预设箱子、平地、沿 +X 推；距离可调，不代表任意材质/重量均能成功 |
| Switch | 同一世界与机器人内的任务状态机、入口检查、必要准备与命令平滑接管 | 手工安全路点；指定组合曾跑通，尚无通用成功率保证 |

**Nav 仅包含最初默认的 `nav/policy/actor.pt`（210维 WBC）。不含 4999、6400、10100 或其他候选权重，不使用 Nav2 315维入口。** Climb 保留 V1/900，Push 保留 v212 腿/臂两个导出 Actor。未重新训练或修改这四个 Actor。

已知未通过：`box-stairs`（Nav→Push→Climb→Nav→Climb→Nav，20cm活动箱作踏步到40cm高地）。默认流程可能在 Push→Climb 的距离/入口检查拒绝接管；显式 `--near-climb` 的近距离实验会复现机身撞箱沿。不能把它作为成功演示。

## 目录

```text
mujoco/
  README.md              使用入口、依赖和边界
  HANDOFF_CN.md          交接：完成内容、已知问题、维护位置与下一步
  requirements.txt       共用非Torch依赖
  MANIFEST.json          交接包范围、文件数与冻结模型哈希（打包生成）
  SHA256SUMS             逐文件校验（打包生成）
  nav/                   默认210维策略与目标导航
  climb/                 V1/900登台与停止
  push/                  v212推箱与收臂
  switch/                同一世界中的技能组合
```

每个单技能目录都包含运行所需的 `policy/` 与 `robot/`（XML、网格、物理/碰撞配置、来源与许可证）。Switch 直接复用相邻三个目录，不能单独搬走。Push 的 `source/push_skill/runtime/mujoco/deploy/piper_push_safe_approach.json` 是实际运行要读取的收放臂路径配置，不是测试数据，必须保留。

交接包不含 tests、verify/validate/diagnose 工具、既有 outputs、录像、训练检查点、完整源工程快照、真机 deploy、外部参考仓库或 Python 环境。程序以后运行仍会自行生成 outputs；这是正常输出行为。

## 环境准备

本机验证环境：Python 3.9.25、Torch 2.1.0+cu118、MuJoCo 3.3.2、NumPy 1.26.4、SciPy 1.13.1、OSQP 1.1.3。默认 CUDA 推理；MuJoCo 物理和 QP 在 CPU，不是 GPU 物理仿真。

推荐为 MuJoCo 使用独立环境，不要把依赖装进系统 Python 或 Isaac 环境。先检查现有 Torch，避免重复下载：

```bash
conda activate go2-mujoco   # 或你已准备好的独立MuJoCo环境
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -m pip install -r requirements.txt
python -c "import mujoco,numpy,scipy,osqp,torch; print(mujoco.__version__, torch.__version__, torch.cuda.is_available())"
```

`requirements.txt` 有意不安装或升级 Torch。如果 import torch 失败，需要使用者在此独立环境中按显卡驱动选择兼容的 PyTorch；参考上述实测版本，不要把“服务器已有Isaac的Torch”误当成此环境已装好。

Linux 服务器没有桌面时使用 `--headless`。仅 headless、不录像不需要 OpenGL 渲染；需要录像时通常设置 `export MUJOCO_GL=egl`，并提供 NVIDIA/EGL 驱动。没有可用 EGL 时不要据此判定策略失败，先去掉 `--video` 验证物理。若 EGL 不可用，也可配置 OSMesa 软件渲染。交互窗口需要桌面/X 显示，普通 SSH 本身不会显示窗口。

## 运行命令

以下命令都在 **mujoco 根目录**执行，使用当前环境的 `python`。Windows 可将 python 换成本机已有的 `D:\Anaconda\envs\pytorch\python.exe`。

```bash
# Nav：世界坐标(米)，最终朝向(度)，默认原始actor、机械臂零位、CUDA
python nav/navigate.py --goal 1 -1 --yaw-deg -90

# Climb：默认登台后停止，障碍高20cm
python climb/play.py --box-height 0.20
# 高度范围0～0.20米；0表示平地基线
python climb/play.py --box-height 0.10

# Push：箱子沿世界+X前移0.6米，之后收臂并站稳
python push/play.py --push-distance 0.60

# 同世界中的切换
python switch/play.py --sequence nav-nav
python switch/play.py --sequence nav-climb --box-height 0.20
python switch/play.py --sequence nav-push --push-distance 0.60
python switch/play.py --sequence nav-push-climb
```

`nav-push-climb` 的实际任务列表是 Nav→Push→Nav→Nav→Nav→Climb，包含绕行用的人工导航点，不是推动箱子后直接爬箱。路线在 `switch/plans.py`。

四个入口默认 CUDA；没有 CUDA 时加 `--device cpu`。默认不录像，加 `--video` 才保存 MP4。交互窗口可拖动相机；任务成功后继续真实物理与当前保持控制，关闭窗口退出。安全失败会按各入口的保护流程记录/终止，不能期待失败后继续正常任务。Switch 还有全局步数上限，并非无限运行服务。

### 无窗口运行与录像

```bash
python nav/navigate.py --goal 1 -1 --yaw-deg -90 --headless --observe-seconds 5
python climb/play.py --box-height 0.20 --headless --observe-seconds 5
python push/play.py --push-distance 0.60 --headless --observe-seconds 5
python switch/play.py --sequence nav-climb --headless --observe-seconds 5

# Linux无显示器录制，先确认EGL可用
export MUJOCO_GL=egl
python switch/play.py --sequence nav-push --headless --observe-seconds 5 --video
```

`--observe-seconds` 是成功/回合后的额外观察时长，不是总任务时长。每次打印 `Output:` 路径，生成自己的报告和轨迹；可用 `--output /绝对路径/本次新目录` 指定位置。Nav 报告主要看 `episode`，Climb 看 `episodes`（或实际报告中的回合字段），Push 看推箱与退出阶段，Switch 看 `successful`、`reason`、`events`、`results`。进程正常退出不必然表示任务成功，应读取报告。

### 已知失败场景（仅供研究复现）

```bash
python switch/play.py --sequence box-stairs --headless --observe-seconds 5
python switch/play.py --sequence box-stairs --near-climb --headless --observe-seconds 5
```

## 参数、控制与安全边界

- Nav 默认 `skills` profile：前进0.4～0.6m/s、转速0.8～0.9rad/s；位置容差13cm，朝向容差约14.3°，连续停稳1秒。参数为当前原始策略的开发配置，不沿用新Nav2的参数。上层先转向再前进，不主动侧移。
- Climb 高度 `--box-height` 单位米、范围0～0.20；默认 `--finish-mode stop`，`ascent` 是不停步的原策略对照。
- Push 距离 `--push-distance` 单位米且须大于0，默认0.6；不是机器人自身行程。推箱达标不等于完整成功，还必须收臂并站稳。
- Nav/Switch 默认20ms执行器命令延迟；Climb/Push 未指定时沿用各自种子下的原延迟设置。显式固定延迟用 `--delay-ms`，可选值见各入口 `--help`。它们没有模拟真实传感器/定位滞后。
- 统一控制形式为 motor + 延迟PD + 必要前馈力矩，再按原电机限值限幅。腿每条的力矩限值为23.7/23.7/45.43Nm；臂为20/20/15/7/5/5Nm。力矩限幅不等于不会碰撞、超速、过热或摔倒。
- 三份机器人沿用约21.765kg的USD对应质量/惯量和电机限制。单技能的主动PD、被动阻力等并不完全相同；Switch 使用固定的Push/Climb物理世界、Nav的skills主动PD，不在接管时切换质量或惯量。不要宣称三个入口动力学逐项相同。

当前使用精确MuJoCo状态与已知地图/解析地形信息。已知地图可以供地形查询，但真实运行仍需要定位、地图配准、速度/姿态估计与时钟同步。本包没有传感器噪声、读数延迟、丢包、真实电机带宽、电池/温度、柔性与标定验证，**不能直接作为真机部署或正式跨仿真验收通过的交付**。

详细完成项、历史验证的解释、当前问题与下一步见 [HANDOFF_CN.md](HANDOFF_CN.md)。本次交接按要求不携带历史测试证据，历史结论不能代替接收者在目标环境中的重新验证。
