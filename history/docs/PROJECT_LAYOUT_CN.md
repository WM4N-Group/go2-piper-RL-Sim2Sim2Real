# 按技能独立组织项目（2026-10-19）

## 最终目录

```text
skills/
  nav/                  NAV独立run.py、verify.py、SHA256SUMS、权重及配套runtime/train
  push/                 PUSH独立run.py、verify.py、SHA256SUMS及v212完整版本
  climb/                前开发者CLIMB独立run.py、verify.py、SHA256SUMS及iy完整版本
integrations/
  nav-push-nav/          本链独立run.py、verify.py及v317控制器
  nav-climb-nav/         本链独立run.py、verify.py及v067控制器
source/LeggedManip_Lab/  公共开发框架和原机器人资产
scripts/                公共开发用训练、测试、导出和诊断
climb_skill/            用户AMP工程的唯一目录，V1/V2/V3及结果保持原位
archive/                旧三技能、早期MuJoCo、整理前来源记录
outputs/                用户已有运行结果，不移动或删除
```

公共tools目录及runtime_handoff、根LeggedManip_Lab、skills/climb/amp快捷入口均已移除。sim2real和mujoco旧链接仍保留给历史导入／文档使用，它们的实体在archive，不是重复文件。

## 为什么保留配套源码

每个前开发者技能独立拥有启动和校验代码，不调用另一个技能的启动器。NAV此前借用iy的匹配train树，现在将同一份冻结内容复制到nav/runtime/train，拥有自己的运行依赖。PUSH和CLIMB保持各自原有train树。它们和source中的公共开发版本可能不同，不能直接去重覆盖。

两条连续链各自有入口，但任务本身必须消费组成它的技能模型和源码，因此仍显式引用skills/nav和对应PUSH／CLIMB。它们没有公共tools依赖。用户AMP训练仍直接进入climb_skill运行。

## 各文件职责

| 文件 | 作用 |
|---|---|
| 各技能run.py | 只准备／运行本技能；复制匹配运行树，设置GPU和导入路径，记录计划、日志和退出状态 |
| 各技能verify.py | 仅核对自身目录SHA256SUMS，不要求其他技能存在；--environment可查看当前解释器依赖 |
| 各技能SHA256SUMS | 本目录代码、模型、配置和资产的当前完整性清单 |
| 各版本plan.json／jobs.json | 原配套冻结合同、源码哈希和记录批次 |
| 各技能README | 模型、配置、脚本职责、运行方法、输出及已知边界 |
| integrations/*/run.py | 单条连续任务的独立准备和执行入口 |
| scripts/ | 公共开发工具分类见SCRIPT_INDEX_CN.md，不是单技能默认启动入口 |

## 使用

激活conda activate go2-piper后，进入目标技能目录：

```bash
cd /mnt/miaojigui/zyh/skills/push
python verify.py
python run.py --gpu 0 --output-dir /mnt/miaojigui/zyh/outputs/push-review-001
```

默认使用当前Python，也支持--isaac-python。省略--execute仅准备计划；核对run-plan.json后，换一个新的输出目录加--execute运行。目录不可覆盖已有结果。具体批次、场景、录像和完成条件见每个技能README。

## 整理和验证计划

1. 保留旧版至archive；冻结控制源码、权重、bank和用户结果保持内容不变。
2. 每个技能和切换链分别提供独立启动、独立校验；移除公共tools。
3. 同步根README、各技能说明、交接页与发布／校验清单。
4. 分别验证五条入口准备、与原命令参数等价、NAV不依赖CLIMB目录、旧冻结文件哈希一致。记录在archive/organization-20261019。
5. 本次不启动物理仿真或训练；后续用户选择GPU和新输出目录运行，检查报告和全片原速录像。

目录整理不代表真实感知、完整sim2sim或硬件SDK缺口已解决。正式验收仍要求Isaac和MuJoCo各两组独立32回合每组至少30/32。模型导出、文件校验或单条成功录像不能替代验收。
