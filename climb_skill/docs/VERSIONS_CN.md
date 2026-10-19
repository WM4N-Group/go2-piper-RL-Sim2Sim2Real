# 版本配置与训练结果

| 版本 | 含义 | 相对上一版的主要变化 | 已有结果 |
|---|---|---|---|
| V1 | 截图 AMP + 后腿工作范围基线的恢复版 | 后大腿目标≤1.8rad，后膝目标−2.5～−1.05rad；共享运动参考相位；AMP平地门控 | 原始权重已缺失，不能伪造 |
| V2 | 原 climb_skill 的前腿软限制 / 30cm 课程版，默认 V22 | 最终高度20→30cm、7→11级；自由起步；前大腿−0.30～1.90、前膝−2.65～−0.95rad，软成本权重0.5；保留PPO探索保护 | V21、V22 |
| V21 | V2 的第一次训练 | 额外机身抬头惩罚权重0.5 | outputs/V2/V21 |
| V22 | V2 的第二次训练，也是 V2 默认 | 相对 V21 仅关闭额外机身抬头惩罚：0.5→0 | outputs/V2/V22 |
| V3 | 原 climb_skill2，统一此前混用的版本名 | 回到20cm/7级与原基线起步；起点后移；脚级跨沿检测、净空与落箱奖励、步态和登台质量课程；后续修正课程窗口 | original、current、migration |

V3/original 保留你认可的 model_800；V3/current 是修正课程后的续训；migration 只有迁移权重，不是第三次训练。
本地实际保留四个训练目录（V2两个、V3两个），没有因整理丢弃任何一次结果。每个目录的 `config.json`、`run.json`、`source/` 是该次训练的历史事实，不改写其中的旧路径与旧合同标识。


## 逐参数变化

### V1-to-V2

| 参数 | 之前 | 之后 |
|---|---|---|
| `ppo.entropy_coefficient` | `0.01` | `0.003` |
| `ppo.maximum_learning_rate` | `null` | `0.0005` |
| `ppo.maximum_std` | `null` | `1.0` |
| `ppo.minimum_std` | `null` | `0.05` |
| `task.amp_body_gate` | `true` | `null` |
| `task.amp_enabled` | `true` | `null` |
| `task.approach_quality_enabled` | `false` | `null` |
| `task.box_height` | `0.2` | `0.3` |
| `task.crossing_clearance_min` | `0.005` | `null` |
| `task.crossing_commit_distance` | `0.02` | `null` |
| `task.crossing_failure_penalty` | `0.5` | `null` |
| `task.crossing_guidance_weight` | `0.5` | `null` |
| `task.crossing_intent_distance` | `0.08` | `null` |
| `task.crossing_intent_height` | `0.065` | `null` |
| `task.crossing_intent_ratio` | `0.6` | `null` |
| `task.crossing_quality_enabled` | `false` | `null` |
| `task.crossing_reference_weight` | `1.0` | `null` |
| `task.crossing_return_seconds` | `0.06` | `null` |
| `task.crossing_takeoff_max` | `0.38` | `null` |
| `task.crossing_takeoff_min` | `0.03` | `null` |
| `task.crossing_timeout` | `1.5` | `null` |
| `task.crossing_unsafe_seconds` | `0.08` | `null` |
| `task.crossing_wall_seconds` | `0.08` | `null` |
| `task.curriculum_levels` | `7` | `11` |
| `task.curriculum_only_enabled` | `false` | `null` |
| `task.diagonal_duration_weight` | `0.0` | `null` |
| `task.diagonal_gait_enabled` | `true` | `null` |
| `task.diagonal_max_stance_seconds` | `0.5` | `null` |
| `task.diagonal_max_swing_seconds` | `0.35` | `null` |
| `task.diagonal_pair_weight` | `0.0` | `null` |
| `task.diagonal_sync_weight` | `0.0` | `null` |
| `task.diagonal_transfer_seconds` | `0.06` | `null` |
| `task.flat_ignore_edge_distance` | `true` | `null` |
| `task.flat_stability_blend_width` | `0.1` | `null` |
| `task.flat_stability_margin` | `0.2` | `null` |
| `task.flat_use_body_gate` | `false` | `null` |
| `task.flat_walk_air_variance_weight` | `0.0` | `null` |
| `task.flat_walk_flight_weight` | `0.0` | `null` |
| `task.flat_walk_long_air_weight` | `0.0` | `null` |
| `task.flat_walk_mirror_weight` | `0.0` | `null` |
| `task.flat_walk_start_height` | `0.15` | `null` |
| `task.flat_walk_velocity_tracking` | `false` | `null` |
| `task.flat_walk_vertical_weight` | `0.0` | `null` |
| `task.flat_walking_enabled` | `true` | `null` |
| `task.front_calf_max` | `null` | `-0.95` |
| `task.front_calf_min` | `null` | `-2.65` |
| `task.front_clearance_distance` | `0.22` | `null` |
| `task.front_clearance_margin` | `0.03` | `null` |
| `task.front_clearance_scale` | `0.08` | `null` |
| `task.front_clearance_weight` | `0.5` | `null` |
| `task.front_joint_scale` | `null` | `0.5` |
| `task.front_joint_weight` | `null` | `0.5` |
| `task.front_landing_bonus` | `0.5` | `null` |
| `task.front_landing_seconds` | `0.08` | `null` |
| `task.front_pitch_scale` | `null` | `0.25` |
| `task.front_pitch_soft_max` | `null` | `0.6` |
| `task.front_pitch_weight` | `null` | `0.0` |
| `task.front_thigh_max` | `null` | `1.9` |
| `task.front_thigh_min` | `null` | `-0.3` |
| `task.gait_frame_cost_max` | `0.45` | `null` |
| `task.gait_good_fraction_min` | `0.7` | `null` |
| `task.gait_ground_seconds` | `0.8` | `null` |
| `task.gait_leg_cost_max` | `0.45` | `null` |
| `task.gait_mean_cost_max` | `0.35` | `null` |
| `task.gait_speed_max` | `0.65` | `null` |
| `task.gait_speed_min` | `0.15` | `null` |
| `task.gait_top_seconds` | `0.4` | `null` |
| `task.quality_window_enabled` | `false` | `null` |
| `task.quality_window_required` | `3` | `null` |
| `task.quality_window_size` | `5` | `null` |
| `task.rear_boundary_x` | `-0.5` | `null` |
| `task.rear_workspace_enabled` | `true` | `null` |
| `task.rewards.feet_edge` | `0.0` | `null` |
| `task.startup_angular_tolerance` | `null` | `0.3` |
| `task.startup_linear_tolerance` | `null` | `0.1` |
| `task.startup_stand_seconds` | `1.0` | `0.0` |
| `task.startup_tilt_tolerance` | `null` | `0.1` |
| `task.straight_heading_weight` | `0.5` | `null` |
| `task.straight_lateral_velocity_weight` | `1.0` | `null` |
| `task.straight_path_weight` | `1.0` | `null` |
| `task.straight_tracking_enabled` | `false` | `null` |
| `task.straight_yaw_rate_weight` | `0.3` | `null` |
| `task.walking_clearance_max` | `0.06` | `null` |
| `task.walking_clearance_min` | `0.025` | `null` |
| `task.walking_clearance_scale` | `0.04` | `null` |
| `task.walking_clearance_weight` | `0.0` | `null` |
| `task.walking_early_gain` | `0.25` | `null` |
| `task.walking_pair_ramp_seconds` | `0.03` | `null` |
| `task.walking_refinement_enabled` | `true` | `null` |

### V21-to-V22

| 参数 | 之前 | 之后 |
|---|---|---|
| `task.front_pitch_weight` | `0.5` | `0.0` |

### V2-to-V3

| 参数 | 之前 | 之后 |
|---|---|---|
| `ppo.entropy_coefficient` | `0.003` | `0.01` |
| `ppo.iterations` | `15000` | `14700` |
| `ppo.maximum_learning_rate` | `0.0005` | `null` |
| `ppo.maximum_std` | `1.0` | `null` |
| `ppo.minimum_std` | `0.05` | `null` |
| `task.amp_body_gate` | `null` | `true` |
| `task.amp_enabled` | `null` | `true` |
| `task.approach_quality_enabled` | `null` | `true` |
| `task.box_height` | `0.3` | `0.2` |
| `task.crossing_clearance_min` | `null` | `0.005` |
| `task.crossing_commit_distance` | `null` | `0.02` |
| `task.crossing_failure_penalty` | `null` | `0.5` |
| `task.crossing_guidance_weight` | `null` | `0.5` |
| `task.crossing_intent_distance` | `null` | `0.08` |
| `task.crossing_intent_height` | `null` | `0.065` |
| `task.crossing_intent_ratio` | `null` | `0.6` |
| `task.crossing_quality_enabled` | `null` | `true` |
| `task.crossing_reference_weight` | `null` | `1.0` |
| `task.crossing_return_seconds` | `null` | `0.06` |
| `task.crossing_takeoff_max` | `null` | `0.38` |
| `task.crossing_takeoff_min` | `null` | `0.03` |
| `task.crossing_timeout` | `null` | `1.5` |
| `task.crossing_unsafe_seconds` | `null` | `0.08` |
| `task.crossing_wall_seconds` | `null` | `0.08` |
| `task.curriculum_levels` | `11` | `7` |
| `task.curriculum_only_enabled` | `null` | `true` |
| `task.diagonal_duration_weight` | `null` | `0.0` |
| `task.diagonal_gait_enabled` | `null` | `true` |
| `task.diagonal_max_stance_seconds` | `null` | `0.5` |
| `task.diagonal_max_swing_seconds` | `null` | `0.35` |
| `task.diagonal_pair_weight` | `null` | `0.0` |
| `task.diagonal_sync_weight` | `null` | `0.0` |
| `task.diagonal_transfer_seconds` | `null` | `0.06` |
| `task.flat_ignore_edge_distance` | `null` | `true` |
| `task.flat_stability_blend_width` | `null` | `0.1` |
| `task.flat_stability_margin` | `null` | `0.2` |
| `task.flat_use_body_gate` | `null` | `false` |
| `task.flat_walk_air_variance_weight` | `null` | `0.0` |
| `task.flat_walk_flight_weight` | `null` | `0.0` |
| `task.flat_walk_long_air_weight` | `null` | `0.0` |
| `task.flat_walk_mirror_weight` | `null` | `0.0` |
| `task.flat_walk_start_height` | `null` | `0.15` |
| `task.flat_walk_velocity_tracking` | `null` | `false` |
| `task.flat_walk_vertical_weight` | `null` | `0.0` |
| `task.flat_walking_enabled` | `null` | `true` |
| `task.front_calf_max` | `-0.95` | `null` |
| `task.front_calf_min` | `-2.65` | `null` |
| `task.front_clearance_distance` | `null` | `0.22` |
| `task.front_clearance_margin` | `null` | `0.03` |
| `task.front_clearance_scale` | `null` | `0.08` |
| `task.front_clearance_weight` | `null` | `0.5` |
| `task.front_joint_scale` | `0.5` | `null` |
| `task.front_joint_weight` | `0.5` | `null` |
| `task.front_landing_bonus` | `null` | `0.5` |
| `task.front_landing_seconds` | `null` | `0.08` |
| `task.front_pitch_scale` | `0.25` | `null` |
| `task.front_pitch_soft_max` | `0.6` | `null` |
| `task.front_pitch_weight` | `0.0` | `null` |
| `task.front_thigh_max` | `1.9` | `null` |
| `task.front_thigh_min` | `-0.3` | `null` |
| `task.gait_frame_cost_max` | `null` | `0.45` |
| `task.gait_good_fraction_min` | `null` | `0.7` |
| `task.gait_ground_seconds` | `null` | `0.8` |
| `task.gait_leg_cost_max` | `null` | `0.45` |
| `task.gait_mean_cost_max` | `null` | `0.35` |
| `task.gait_speed_max` | `null` | `0.65` |
| `task.gait_speed_min` | `null` | `0.15` |
| `task.gait_top_seconds` | `null` | `0.4` |
| `task.quality_window_enabled` | `null` | `true` |
| `task.quality_window_required` | `null` | `3` |
| `task.quality_window_size` | `null` | `5` |
| `task.rear_boundary_x` | `null` | `-1.6` |
| `task.rear_workspace_enabled` | `null` | `true` |
| `task.reset_x_range` | `[-0.1, 0.1]` | `[-1.1, -0.9]` |
| `task.rewards.feet_edge` | `null` | `0.0` |
| `task.startup_angular_tolerance` | `0.3` | `null` |
| `task.startup_linear_tolerance` | `0.1` | `null` |
| `task.startup_stand_seconds` | `0.0` | `1.0` |
| `task.startup_tilt_tolerance` | `0.1` | `null` |
| `task.straight_heading_weight` | `null` | `0.5` |
| `task.straight_lateral_velocity_weight` | `null` | `1.0` |
| `task.straight_path_weight` | `null` | `1.0` |
| `task.straight_tracking_enabled` | `null` | `false` |
| `task.straight_yaw_rate_weight` | `null` | `0.3` |
| `task.walking_clearance_max` | `null` | `0.06` |
| `task.walking_clearance_min` | `null` | `0.025` |
| `task.walking_clearance_scale` | `null` | `0.04` |
| `task.walking_clearance_weight` | `null` | `0.0` |
| `task.walking_early_gain` | `null` | `0.25` |
| `task.walking_pair_ramp_seconds` | `null` | `0.03` |
| `task.walking_refinement_enabled` | `null` | `true` |

### V3-reference-to-V3

| 参数 | 之前 | 之后 |
|---|---|---|
| `ppo.iterations` | `15000` | `14700` |
| `task.curriculum_only_enabled` | `false` | `true` |
| `task.quality_window_enabled` | `false` | `true` |


### 2026-10-19 上传布局更新

Climb已并入主仓库zyh分支，不再使用嵌套仓库。旧源码完整历史保存在 `climb_skill/versions/source-history.bundle`；通过 `scripts/manage.py` 切换，切换只恢复Climb源码，保存后再切下一版。最近10个模型和最近10个录像通过Git LFS交付，其余录像保留本地。准确清单见Climb的 `versions/publication.json`，当前操作以Climb README为准。训练控制逻辑未变。

本次模型与录像分别按修改时间选最近10个；不足10个取最近5个，不足5个全取。未选中的本地文件不删除。
