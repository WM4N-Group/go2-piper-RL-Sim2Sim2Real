# 三个独立技能运行材料接收索引

更新：2026-10-16。

匹配源码、模型、资产、计划、运行命令和已知边界统一维护在[运行材料](../skills/README.md)，文件逐项校验见仓库根 `SHA256SUMS`。

- NAV：冻结权重、当前限矩原生入口、录像控制脚本和依赖已交付；完整到点导航与整链接管仍在开发。
- PUSH：v212完整运行树、双模型、匹配几何运行时和录像参数已交付。
- CLIMB：iy完整运行树、actor、阶段bank、plan/jobs与12源payload已交付；属于阶段起点重放，独立完成验收器尚未补齐。
- 切换：v317、v067开发对照源码及依赖已交付，不代表稳定SDK。

首次接收执行 分别执行 `python skills/nav/verify.py`、`python skills/push/verify.py`、`python skills/climb/verify.py`，再按运行材料在自己的Isaac环境产生新报告和原速录像。接收环境未执行前不声称物理复现完成。
