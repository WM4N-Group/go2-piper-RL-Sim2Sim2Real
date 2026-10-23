# Switch：同一MuJoCo世界中的技能切换

在mujoco根目录执行：

```bash
python switch/play.py --sequence nav-nav
python switch/play.py --sequence nav-climb --box-height 0.20
python switch/play.py --sequence nav-push --push-distance 0.60
python switch/play.py --sequence nav-push-climb
```

默认CUDA、20ms命令延迟。加`--headless --observe-seconds 5`无窗口运行，`--video`录像。
GUI相机可拖；成功后继续物理至关窗或全局步数上限，安全失败终止并记录。
没有独立Actor或机器人资产，必须与nav/climb/push相邻，Nav使用原210维actor.pt。
plans.py配置任务；machine.py负责状态与路由；runtime.py执行唯一物理世界和电机队列。
plugins.py隔离同名模块；push_entry.py以实际电机运动准备Push站姿，再平滑接管。
默认任务使用手工安全路点，没有自动避障。nav-push-climb中间有三个Nav路点，
不是推完箱子原地爬箱。各阶段入口要求实际位置/朝向/速度/臂姿态满足条件。

box-stairs是未通过的实验路线（箱20cm→高地40cm）。默认可能因起爬距离不符被拒绝；
`--near-climb`启用的近距离原地准备实验会复现机身碰箱沿，不能视为成功方案。
本包不含测试、诊断工具、失败录像与历史outputs。成功路线仅有开发样本，不是可靠性认证。
完整范围、限制与环境见[根说明](../README.md)和[交接](../HANDOFF_CN.md)。
