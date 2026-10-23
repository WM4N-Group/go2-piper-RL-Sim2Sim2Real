# 三技能公共机器人资产

入口：`go2_piper/go2_piper.usd`；同目录 `configuration/*.usd` 是它实际引用的几何、物理和传感器分层，必须整体保留。

来源为整理前 `source/LeggedManip_Lab/LeggedManip_Lab/assets/go2_piper/`，原件保存在 `history/source/`。已逐个比较 Push 的配套资产，USD 全部一致，详见 `SOURCE.json`。这是提取原件，没有重新生成机器人、修改质量惯量、碰撞或关节定义。

三个项目均通过 `CLIMB_ROBOT_USD` 指向该文件；Nav 与 Push 默认还会从本项目根目录定位该文件。Climb 文件保持不动，使用它已有的环境变量覆盖接口。

```bash
export CLIMB_ROBOT_USD=/mnt/miaojigui/zyh/asset/go2_piper/go2_piper.usd
```

PD、力矩限制、延迟和初始关节角属于各技能环境配置，不在 USD 路径统一时擅自修改。共用 USD 也不自动意味着各技能控制合同完全相同。
