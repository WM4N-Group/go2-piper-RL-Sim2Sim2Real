# Nav：默认原始策略

本包只含最初的210维WBC `policy/actor.pt`，不含Nav2或候选权重。
在mujoco根目录执行：

```bash
python nav/navigate.py --goal 1 -1 --yaw-deg -90
python nav/navigate.py --goal 1 -1 --yaw-deg -90 --headless --observe-seconds 5
```

目标为世界坐标米/朝向度。默认CUDA、臂零位、skills执行配置及20ms命令延迟。
先朝向目标、前进，到点再调最终朝向；13cm/约14.3°容差及连续1秒停稳。
GUI到达后继续物理，可拖相机；加`--video`录像；无CUDA加`--device cpu`。
导航配置在navigation.py，执行配置在control_profiles.py，适配在bridge.py。
play.py既是底层速度回放入口，也是navigate.py需要导入的运行辅助，不可删除。
无避障/规划，使用仿真真值；有饱和和超速风险，未真机验收。
本精简包不含部署SDK、训练/转换工具、测试或历史outputs。
完整范围、限制与环境见[根说明](../README.md)和[交接](../HANDOFF_CN.md)。
