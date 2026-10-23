# 开源参考与本项目边界

已实际读取下列固定版本的相关文件，文件SHA256见 [SOURCE_AUDIT.json](SOURCE_AUDIT.json)。新仓库普通git/raw下载超时后改用GitHub contents API获取源码，未把部署README当作完整训练配置。

## Extreme Parkour Onboard

[change-every/Extreme-Parkour-Onboard](https://github.com/change-every/Extreme-Parkour-Onboard)，提交 `6f136271c36e3c9ba8c8f9e4e4205f4e16e2d24c`。

读过 `legged_gym/envs/go2/go2_parkour_config.py`、`envs/base/legged_robot_config.py`、`rsl_rl/rsl_rl/algorithms/ppo.py` 、实际奖励实现 `envs/base/legged_robot.py` 和README。Go2默认腿姿态与本项目Climb相同；相对默认角动作缩放0.25、控制decimation4、物理dt0.005、Actor/Critic[512,256,128]、PPO学习率2e−4、5epoch/4minibatch、KL0.01、gamma0.99/lam0.95是直接可参考的形式。它的Go2腿PD40/1、初始根高度0.42m，不能直接搬到带臂Go2-Piper；这里使用Climb带臂PD30/0.6、真实限矩和实际FK贴地初始化。

V3直接核对 `_reward_tracking_goal_vel` 的实际沿目标方向速度/指令速度、上限1形式，并适配机身任意XY方向；转向使用有符号实际角速度响应，不冒称原版yaw指数奖励。参考动作变化、关节加速度与力矩、非水平和碰撞等奖励思想。这里的具体权重为独立导航配置，不是把跑酷奖励原封不动搬来。没有加入跑酷地形、8个waypoint、扫描编码器、DAGGER特权正则、D435i视觉蒸馏和部署程序。

## WMP Go1/Go2运动与AMP

[haozhang04/wmp_go1](https://github.com/haozhang04/wmp_go1)，沿用此前已固定并审计的提交 `65cf1afd13e4792bce7b9def6f44372ecbb3cdf0`，不是声称本轮拉取了其最新HEAD。

读过 `legged_gym/envs/a1/a1_amp_config.py`、`rsl_rl/algorithms/amp_discriminator.py` 和网络说明。参考LSGAN专家+1/策略−1、`max(1−(D−1)^2/4,0)`风格奖励、专家梯度惩罚10、策略回放和任务奖励合成。该仓库还使用世界模型/深度预测、10Hz RSSM与历史编码；**本Nav2不包含世界模型，也不冒称是完整WMP复现**。

V3按原WMP多类参考思路，实际下载并核对同一固定提交的前进/后退/左移/右移/左转/右转六个原片，符号和源SHA见数据JSON。20ms转换不跨缺口或循环端点，没有拉伸动作时间。数据1181条，带类别镜像扩充；许可随 `data/WMP_LICENSE.txt` 保存。独立转换入口 `scripts/prepare_amp_data.py`，不import Climb。

原WMP配置有多类动作、机身速度特征和[1024,512]判别器。本版用[512,256]腿部判别器加7类条件，另加轻量共享相位软成本；这属于适配，不是原版网络复刻。正AMP奖励借鉴本地Climb的实际运动门控：不动无正风格奖励，参考偏差成本不随实际速度关闭。停车由站立奖励与默认角软成本处理，本版没有静止AMP。混合/斜向使用主平移参考并减权0.6，没有对应精确示范。

原片采集流程及是否真机录制未核实，不能把公开片段称为已验证的真机动作捕捉。裸Go2示范没有Piper负载，需要真实带臂动力学训练适应；尚不能保证与Climb或开源视频同等步态。V2只有前进数据和按指令门控的做法已替换，旧数据/源码可在V2输出与修改前仓库外备份中追溯。

## LeggedSkillDeploy

[haozhang04/LeggedSkillDeploy](https://github.com/haozhang04/LeggedSkillDeploy)，本轮读取提交 `9126dad84708fc2714c6a1158897c86844d0cc1c` 的README和 `src/scripts/rl_sdk.py`。

它是多策略部署框架。值得借鉴的是每策略保存独立模型、观测顺序/历史、PD、动作缩放、控制周期和初始化/输出合同，而不是只交付一个权重。它本身不能给出我们Go2-Piper的训练奖励，也不能替代Isaac训练代码。此前本地审计的 `9bc7329...` 下Go1 WMP配置是历史部署示例，不能等同于本轮最新仓库或本项目Nav2。

Nav2因此每次训练保存配置、源码、资产和数据SHA，导出315→18的actor，并提供无reset的速度更新接口；但本次没有移植部署状态机或修改旧PUSH/CLIMB切换逻辑。默认关节目标一致不等于实际承重状态和动作连续，后续仍须单独验证停稳、首动作、臂状态及观测/延迟队列交接。

## 本地Climb与共同资产

实际复用的是Climb的默认腿/臂姿态、PD/限矩、臂重力补偿形式、运动数据、镜像/共享相位匹配和真实物理参数随机化实现。复制到Nav2独立包，训练时不import Climb。Climb、Push与旧Nav的源码、配置和已有权重保持不变。没有复制Climb登箱逻辑、后腿硬工作范围、跨沿质量门禁或地形观测。

使用Isaac Lab官方 `tools/template/generator.py::generate` 生成External/Direct/single-agent/rsl_rl PPO骨架；仅跳过嵌套Git初始化，交由主仓库管理。再将生成的Cartpole示例替换为本底层速度任务，使用本包PPO+AMP训练器，删除未使用的模板RSL脚本以免两个入口混用。外部包已在go2-piper Conda环境editable安装，系统Python未安装项目依赖。

## 当前任务调整

根据用户要求，本版仅实现速度条件底层行走；目标点上层控制器尚未实现。保留参考来源和数据，不声称复制开源仓库完整训练架构。原目标点Nav2的观测、奖励、课程和18维网络末层已改成315维观测、实际方向响应课程、12维网络末层加6维补零，旧checkpoint不兼容。

## V4参考扩展与镜像

同一WMP固定提交增加前进0.8m/s、左右转0.2rad/s三个原片。V4九原片1879对原始转移、镜像后3758对，前进0.4/0.8、转向0.2/0.5分组。数据JSON保存逐片来源和SHA256，转换器支持`--speed-conditioned`。训练1.0/0.6匹配最近参考，不声称具有精确同速度示范。镜像平均动作损失是本地PPO适配，不声称照搬上述项目实现；按真实USD关节轴审计符号，见SYMMETRY_AXES.json。
