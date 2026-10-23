# CLIMB：两条路线，不能混为同一个模型

| 目录 | 来源和用途 |
|---|---|
| iy/ | 前开发者冻结版本：阶段控制器＋零残差actor，主要用于既有登台和切换对照 |
| [../../climb_skill/](../../climb_skill/README.md) | 用户后续PPO＋AMP训练工程，直接从原目录运行；V1/V2/V3、输出和Git历史保持原位 |

## iy 的文件

| 路径（相对 iy/） | 作用 |
|---|---|
| stand_actor304.pt | 304→18 actor，冻结残差恒为0；不是单独可部署的登台策略 |
| train/scripts/evaluate_box_skills.py | Isaac评估、录像和报告入口 |
| train/source/LeggedManip_Lab/ | 匹配的阶段控制、观测、动作、机器人及任务定义 |
| stage-bank.json | 箱沿阶段初态库；不是普通地面起点，也不允许用于连续切换中途注入 |
| jobs.json | 原始32环境、seed27302、280秒诊断和相机命令 |
| plan.json | 配套源、actor、bank哈希和运行范围 |
| source_payload/、source-payload.tar.gz | 原12源补丁及原包，保留追溯；实际执行使用完整train树 |

## 运行前开发者 iy

仓库根，激活 `go2-piper` 后：

```bash
python skills/climb/verify.py
python skills/climb/run.py --isaac-python "$CONDA_PREFIX/bin/python" --gpu 0 --output-dir "$PWD/outputs/climb-iy-001" --execute
```

省略 `--execute` 只准备。默认原32环境、280秒、env28录像；完整报告可能约3.9GB。输出 report.json/video.mp4 和公共运行记录。阶段完成不能只看旧successful_episodes字段或退出码。iy尚未完成完整MuJoCo移植和正式验收，详见 [CLIMB当前页](../../docs/CLIMB_CRAWL_STATUS_20261001_CN.md)。

## 运行／修改你的 AMP Climb

从仓库根进入 `cd climb_skill`，按 [AMP工程README](../../climb_skill/README.md) 激活环境、`source scripts/env.sh`，再训练或回放。该工程的923维观测、18维输出与iy不兼容，不能共用导出器和MuJoCo适配器。环境直接提供箱高与解析高度扫描，真实感知仍需补齐。当前版本由 VERSION.json 决定，不是这里的iy版本号。

本目录run.py、verify.py和SHA256SUMS分别是独立启动器、校验器和文件清单，无公共tools依赖。也可直接进入本目录运行 `python verify.py`、`python run.py --output-dir /绝对路径/新输出目录 --execute`；已激活Isaac环境时默认使用当前Python。
