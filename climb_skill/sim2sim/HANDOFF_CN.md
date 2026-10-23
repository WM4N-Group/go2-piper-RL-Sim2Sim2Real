# 本机 MuJoCo 对话交接

用户要求：在 Windows 本机 `C:\Users\zyh\Desktop\MuJoCo` 完成 GO2-PIPER Climb 的初步 Sim-to-Sim，使用 V1 第900轮权重。优先在本机开发/测试，不要继续在服务器安装或运行。当前对话的执行端是远程Linux，不能直接访问C盘。Codex项目列表已确认本机MuJoCo项目存在，hostId=local，projectId=cf538a7e-916e-42d0-a503-96cbd432446a。

## 权重与来源

服务器项目：`/mnt/miaojigui/zyh`，SSH主机项目标签：`180.97.68.228`。具体SSH用户名/端口以用户已有连接配置为准，不猜测。

- 原checkpoint：`climb_skill/outputs/V1/train-20261019-110256-00f00wtw/model_900.pt`
- checkpoint SHA256：`cb741d772d6b90b7bd25107758b9715bb6faf674c5e3b1856e53fcd0a325f424`
- 同次训练代码快照：该训练目录的 `source/`。
- V1/900对应20cm平台，原任务是持续前行登台，不是登台后停稳。
- 当前三个策略没有现成切换实现。历史代码只作参考，不算当前已实现能力。

## 服务器上已生成的内容：未完成、未验证

`/mnt/miaojigui/zyh/climb_skill/sim2sim/`：

- `prepare.py`：从900轮原checkpoint和其源码快照导出部署Actor；已成功运行，JIT与原网络一致、臂后6维为零、特权占位不影响部署输出。
- `policy/actor.pt`、`policy/contract.json`：已导出，约3.6MB，绑定上述原checkpoint SHA。
- `policy/observations_reference.py.txt`：训练时真实观测函数，供数值对照。
- `bridge.py`、`play.py`：MuJoCo观测/动作/PD/延迟/重力补偿/终止/录像的初稿。只检查过Python语法，尚未完成MuJoCo模型编译及动力学运行，不可标成迁移成功。
- `verify.py`：拟对照快照观测、历史、映射和力矩裁剪，尚未实际运行。
- `package.py`：独立ZIP制作初稿，尚未验证/运行。
- `README.md`、`requirements.txt`：Windows/Linux命令初稿。Python3.11/MuJoCo3.12.0/Torch2.7CPU是目标组合，不是完整实测通过组合。
- 公共MuJoCo资产初稿在 `/mnt/miaojigui/zyh/asset/go2_piper/mujoco/`，约19MB。完整复制到本机sim2sim入口旁 `robot/` 即可走本地路径，无需整个Isaac仓库。

公共资产包含原XML、实际引用的STL、两个USD来源profile和PROVENANCE.json。profile的五个USD哈希与当前公共USD逐个一致。只使用历史几何作为转换底稿，运行不导入历史策略/控制器/切换代码。

## 本机下一步

1. 确认当前终端确实在Windows本机，再查看MuJoCo目录和 `conda env list`。用户猜环境名是mujoco，尚未确认。
2. 通过用户已有SSH/SFTP/远程资源浏览器，取得上述sim2sim目录及公共MuJoCo资产；本机放在MuJoCo项目的独立子目录，资产放子目录的robot/。若无法访问服务器，说明具体缺少的文件，不假装已迁移。
3. 不必下载28MB训练checkpoint即可测试导出的actor；若需重新导出/核验训练代码，再取得原checkpoint和源码快照。
4. 使用与Isaac隔离的本机Python环境，核对MuJoCo/torch版本。先运行verify.py，修复MjSpec API兼容或映射错误，再运行短回合、完整回合和录像。
5. 保留原V1行为，不加入技能切换、停稳新奖励、PD调参或新的训练。先验证观测、关节顺序、动作、模型和力矩。
6. 更新README和验证报告，报告必须区分真正登台成功、失败、超时、调试截断。单条视频不作为正式验收。

## 迁移合同

- 物理200Hz、策略50Hz；923维观测；132点解析高度扫描，含直接箱高，不是视觉感知。
- Actor用history分支与估计速度：3速度+29特权占位不参与部署分支；10帧69维历史。
- 显式顺序FL/FR/RL/RR，每腿hip/thigh/calf，然后joint1..6。
- 输出18维：12腿残差+6个零臂残差，目标=默认角+0.25*动作；保留腿软限位和后腿工作范围。
- 腿PD30/0.6；臂Kp[50,50,80,30,30,20]，Kd[3,2,3,3,2.5,1]。
- 腿限矩[23.7,23.7,45.43]每腿；臂[20,20,15,7,5,5]；PD与补偿相加后裁剪。
- 延迟0..4物理步，腿同组、臂各关节独立；仅臂重力补偿。
- 原V1有地面站稳起步逻辑和箱顶持续前行成功条件；这不是无缝技能切换。

服务器新建的go2-mujoco环境此前仅完成Conda Python创建，pip下载Torch CPU时被停止；不应说依赖安装完成。用户现有Isaac训练未被停止或更改。
