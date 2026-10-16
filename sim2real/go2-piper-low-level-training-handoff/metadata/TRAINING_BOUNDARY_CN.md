# 训练边界与验收门禁

> 本页约束2026-09历史训练包，2026-10-14已复核其版本边界。最新执行范围与验收目标见[总交接](../../../docs/AGENT_HANDOFF_CN.md)及[项目计划](../../../docs/PROJECT_PLAN_CN.md)。以下允许优化的范围是历史技术边界，不表示目前授权启动暂停任务；最新逐脚CLIMB结果不能归入本包旧model_200。

## 冻结基线

- PUSH：`checkpoints/push/model_599.pt`，SHA-256 `aaff6614b641238ab4579c11fff8329b566904163f04d5e20cc4dab6b1ec891a`。
- CLIMB：`checkpoints/climb/model_200.pt`，SHA-256 `5cbdb0d8523a10b7f6a4870a3385afdd8289d5d87bc93408ac5c7b404ac7b548`。
- PUSH 的训练配置为 `checkpoints/push/params/`；CLIMB 的训练配置为 `checkpoints/climb/params/`。

保留原 checkpoint 不变。每项新实验必须使用新的 `experiment_name` 或 `run_name`，不得写回基线目录。

2026-09-23 的 SAFE_BASE `model_99.pt` 是主仓库独立实验，不在本包的 `checkpoints/`、
`PACKAGE_MANIFEST.json` 或 `SHA256SUMS` 中；它的四组零速重置 Isaac 定时保持为
`128/128`，并不等同 PUSH 推箱成功。SAFE_APPROACH 切换初态、静稳速度阈值、MuJoCo
回放和在线 PRECONTACT 尚未验收。不得以 SAFE_BASE 结果替换冻结 PUSH 基线或绕过以下门禁。

## 可以优化的低层范围

- 任务奖励、课程、随机化、初始状态与实物辨识参数；
- 动作缩放、PD 参数、延迟模型、关节速度/力矩限制和状态滤波；
- PUSH 的姿态 IK、接触准备、末端可达性和接触面约束；
- CLIMB 的接触课程、足端/机身碰撞与稳定性反馈；
- 实机只读数据回灌后的质量、质心、安装变换和执行器模型更新。

## 禁止的安全与验收捷径

- 通过运动学搬运物体伪造成功；
- 降低四足落稳、指定接触、机身碰撞、姿态或终态速度门槛；
- 未经过离线、悬空和急停验证直接将新 actor 下发到实机。

## 必需记录

每个候选必须保存：源 checkpoint SHA-256、源码 Git 提交、训练 YAML、随机种子、物理参数、训练日志、两组原生报告、两组 MuJoCo 报告、导出 actor SHA-256 和明确的失败原因统计。

只有四组验收都达到每组至少 `30/32` 后，候选才可进入实机控制器的分级验证；这不是实机放行本身。
