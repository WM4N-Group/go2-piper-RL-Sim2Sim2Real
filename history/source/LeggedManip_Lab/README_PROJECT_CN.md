# 公共 LeggedManip_Lab

本目录是仓库共享的Isaac Lab扩展，直接在source/LeggedManip_Lab中阅读和开发。根目录的同名快捷链接已移除。

| 位置 | 用途 |
|---|---|
| setup.py、pyproject.toml、config/ | 扩展打包、安装及元数据 |
| LeggedManip_Lab/assets/go2_piper/ | 机器人USD与执行器配置 |
| LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/config/go2_piper/ | GO2-PIPER任务注册、WBC／技能环境与PPO配置 |
| LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/ | 观测、动作、奖励、命令和任务控制组件 |
| ../../scripts/rsl_rl/（从仓库根看scripts/rsl_rl/） | 公共PPO训练、回放与配套工具 |

公共源码用于开发和理解框架；skills/push/v212/train与skills/climb/iy/train是各自冻结版本的完整依赖树。它们可能不同，不能为了去重用公共源码覆盖冻结树。已有项目环境无需因目录整理重装。原WBC Actor使用本体历史及速度／末端指令，Critic额外使用训练状态；它本身不是完整视觉导航系统。
