# Push：v212推箱、安全收臂与站稳

在mujoco根目录执行：

```bash
python push/play.py --push-distance 0.60
python push/play.py --push-distance 0.30 --headless --observe-seconds 5
```

距离单位米、须大于0，指箱子从初始位置沿+X前移的目标距离。默认0.60、CUDA。
原双Actor + 原IK/接触控制，加入平滑展开/接近、QP支撑、安全逆路径收臂和零位站稳。
推箱达标不等于完整成功，还要完成收臂、连续1秒站稳及3秒验证。
默认箱子1.2×1.2×0.2m、1kg，平地、沿+X，不保证任意箱子/起点适用。
加`--video`录像；无CUDA加`--device cpu`。相机可拖，成功后继续实际物理。
初始化会先实际承重沉降。timing.py与controller/approach.py管展开/接近；finish.py管退出。
source下仅保留piper_push_safe_approach.json原路径，它是运行需要的路点配置，不可删。
测试、Isaac源码快照、历史输出与录像均不包含；许可证和资产来源保留。
完整范围、限制与环境见[根说明](../README.md)和[交接](../HANDOFF_CN.md)。
