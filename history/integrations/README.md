# 连续技能切换：位于三个单技能之上

这里组合单技能，不训练新的第4个技能。`nav-climb-nav/v067` 保留前开发者NAV→CLIMB→NAV对照；`nav-push-nav/v317` 保留NAV→PUSH→NAV对照。

每个版本的 probe.py 是入口，plan.json 绑定同目录配套模块，其他Python模块负责初始化、交接、阶段／支撑处理和审计。必须整套使用，不能只拿probe.py。旧监督器留在相应冻结目录追溯，新调用使用统一入口。

在仓库根激活go2-piper：

```bash
python integrations/nav-climb-nav/run.py --isaac-python "$CONDA_PREFIX/bin/python" --gpu 0 --seed 3701 --output-dir "$PWD/outputs/nav-climb-nav-001" --execute
python integrations/nav-push-nav/run.py --isaac-python "$CONDA_PREFIX/bin/python" --gpu 0 --seed 3701 --output-dir "$PWD/outputs/nav-push-nav-001" --execute
```

两条命令应分别运行并先检查GPU；省略--execute只准备。输出result/报告及公共运行记录。物理过程连续，无中途reset或bank注入。v067有腕部超限失败与NAV合同问题，v317的8/8是已用开发起点；均非稳定SDK或独立种子验收。具体边界见总交接和对应技能页。
