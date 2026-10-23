# Climb：V1/900登台并停止

在mujoco根目录执行：

```bash
python climb/play.py --box-height 0.20
python climb/play.py --box-height 0.10 --headless --observe-seconds 5
```

高度单位米，范围0～0.20，默认0.20；0为平地基线。默认CUDA与finish-mode stop。
保留V1/900 Actor；登台后QP制动，平滑调整腿部到接近Nav静止的弯曲程度并站稳。
`--finish-mode ascent`是原持续前行模式，不会完成新增停稳。
加`--video`录像；无CUDA加`--device cpu`。GUI相机可拖，成功后继续真实物理。
运行/模型适配在play.py与bridge.py；停止参数和状态机在stop.py。
仅沿世界+X、已知台面；接管对站姿、距离、接触有要求。近距离箱沿起爬未通过。
有限矩但仍可能饱和/超速，未正式跨仿真或真机验收。
本包不携带测试、Isaac源码快照或历史outputs。
完整范围、限制与环境见[根说明](../README.md)和[交接](../HANDOFF_CN.md)。
