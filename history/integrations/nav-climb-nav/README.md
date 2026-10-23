# nav-climb-nav 独立入口

本目录run.py和verify.py是自身的启动器与校验器，不依赖公共tools。版本控制模块位于 v067/。

在仓库根激活go2-piper后：

```bash
python integrations/nav-climb-nav/verify.py
python integrations/nav-climb-nav/run.py --gpu 0 --seed 3701 --output-dir "$PWD/outputs/nav-climb-nav-001" --execute
```

也可进入本目录执行python run.py。省略--execute只准备；输出目录必须是新目录。默认当前解释器，可用--isaac-python显式指定。连续链必然消费skills中的NAV及对应PUSH／CLIMB模型和源码；这属于任务组合，不通过公共启动器。开发证据与已知失败见上级README和总交接，不代表正式验收。
