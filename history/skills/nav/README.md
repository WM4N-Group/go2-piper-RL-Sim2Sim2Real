# NAV：全身运动策略及当前限矩入口

## 文件作用

| 文件／目录 | 用途 |
|---|---|
| policy.pt | 唯一冻结 NAV actor，210→18；SHA256 为 72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8 |
| runtime/train/ | 独立配套源码和机器人资产；由此前借用的冻结树原样复制，运行不再读取CLIMB目录 |
| run.py、verify.py、SHA256SUMS | 本技能独立启动、文件校验及清单 |
| entry-v039/probe.py | 当前限矩下的原生入口与有限行走诊断 |
| video-v038/probe.py | 录像入口，统一运行器当前选择此版本 |
| 各目录 plan.json | 对配套模块逐项绑定哈希，不能混用版本 |
| 各目录其他 .py／JSON | 入口姿态、初始化、审计及录像依赖，不是另一套 NAV 权重 |

210维输入是按观测项分组拼接的3帧历史，包含角速度、重力、关节角／速度、动作、速度和末端指令。输出18轴相对默认角的位置动作。不能直接当力矩或只执行12腿动作。目标导航还需要上层定位和速度指令生成。

## 运行和输出

从仓库根激活 `conda activate go2-piper`，先 `python skills/nav/verify.py`，然后：

```bash
python skills/nav/run.py --isaac-python "$CONDA_PREFIX/bin/python" --gpu 0 --output-dir "$PWD/outputs/nav-001" --execute
```

省略 `--execute` 只准备运行计划。目录必须不存在。默认开发种子3703；新结果在 result/，包含原速录像；公共 run-plan.json/run.log/exit-status.json 在输出根。入口含准备与10秒原生行走，末端工作点0.45/0/0.45，不代表原默认工作点、完整到点或正式安全验收通过。

旧消费契约、参数及历史98/100结果保留在 [旧交接包](../../archive/legacy_sim2real/go2-piper-low-level-policy-handoff/README_CN.md)。当前进展以 [总交接](../../docs/AGENT_HANDOFF_CN.md) 为准。

也可直接 `cd skills/nav` 后执行 `python verify.py` 和 `python run.py --output-dir /绝对路径/新输出目录 --execute`。已激活Isaac环境时无需指定--isaac-python，默认当前Python。
