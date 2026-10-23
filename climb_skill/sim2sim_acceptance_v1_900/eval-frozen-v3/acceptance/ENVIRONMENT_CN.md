# 已有环境复用与验证

本机使用现有 `D:\Anaconda\envs\pytorch\python.exe`，不安装或升级 Torch。
Torch 2.1.0+cu118，MuJoCo 3.3.2，NumPy 1.26.4，SciPy 1.13.1，Python 3.9.25。
Actor 在 RTX 4060 Laptop CUDA 上执行；标准 MuJoCo 物理积分在 CPU 执行。

从 PowerShell 逐字执行以下命令，预期输出 `WITNESS`、`shape: [1, 18]`、
CUDA 设备、Actor 哈希，以及 4 个实际 MuJoCo 子步；退出码为 0：

```powershell
& D:\Anaconda\envs\pytorch\python.exe C:\Users\zyh\Desktop\MuJoCo\climb\sim2sim\acceptance\kernel_witness.py
```

数值接口复核命令（100帧训练快照观测、CPU/CUDA Actor、实际延迟PD映射）：

```powershell
Set-Location C:\Users\zyh\Desktop\MuJoCo\climb\sim2sim
& D:\Anaconda\envs\pytorch\python.exe verify.py --device cuda
```

服务器使用 `/mnt/miaojigui/conda/envs/go2-piper/bin/python`，复用现有 Isaac 环境。
启动所需 `LD_PRELOAD`、`CONDA_PREFIX` 等见保存的 `launch_exit_probe*.sh`。
该服务器还有其他任务，本项目仅运行独立命名 screen 评估，不停止训练。
环境见证只证明可执行，不能替代任务验收。
