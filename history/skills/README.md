# 三个技能的入口

这里按功能组织，不按交接批次组织。先读各技能 README，再执行命令。

| 技能 | 当前前开发者版本 | 代码和模型 | 运行性质 |
|---|---|---|---|
| [NAV](nav/README.md) | 冻结 actor＋入口 v039／录像 v038 | nav/ | 限矩下原生行走诊断，不是完整自主到点 |
| [PUSH](push/README.md) | v212 | push/v212/ | 双策略＋IK，原轻载推箱场景 |
| [CLIMB](climb/README.md) | iy | climb/iy/ | 零残差 actor＋阶段控制器，从阶段 bank 起步 |
| 用户的 AMP Climb | V1/V2/V3 | [../../climb_skill/](../climb_skill/README.md) | 仓库唯一 climb_skill，属于另一条训练路线 |

每个技能独立运行：`python skills/nav/run.py ...`、`python skills/push/run.py ...`、`python skills/climb/run.py ...`。各自的verify.py只校验本技能目录，无需tools。
配套冻结源码不能直接替换成公共 LeggedManip_Lab；同名文件并不代表控制逻辑相同。
