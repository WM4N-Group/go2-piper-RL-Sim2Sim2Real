# V1 配置与调参

生效配置：`configs/V1.json`。完整值已显式展开，避免只看覆盖项误判参数。

距离m、时间s、角度rad。奖励通常按控制周期0.02s积分；一次性成功/失败项看rewards.py的实现。动作12腿学习、6臂保持。

## 先改哪里

- 课程高度：`task.box_height`、`curriculum_min_height`、`curriculum_levels`。
- 前腿软角度范围（仅V2）：`front_thigh_min/max`、`front_calf_min/max`；`front_joint_weight`是软成本强度，不是动作裁剪。
- 后腿目标范围：`rear_thigh_max`、`rear_calf_min/max`；这是目标裁剪，实际关节可能动态超调。
- 行走速度：`approach_speed`；平地超速成本：`flat_speed_limit/weight`。
- 保存录像：`ppo.save_interval=100`，训练默认开启每checkpoint录像。
- AMP数据和风格强度：`ppo.amp.dataset/reward_scale/reference_weight`。

## 奖励与惩罚

`task.rewards`中的正值为奖励权重、负值为成本权重。其他以 `_weight` 命名的成本参数常用正数，实际在rewards.py中相减，不要仅凭配置正负判断方向。

| 项 | 权重 |
|---|---|
| `goal_velocity`（向目标方向速度） | 1.5 |
| `heading`（目标方向） | 0.5 |
| `progress`（缩短目标距离） | 2.0 |
| `lin_vel_z`（垂直速度） | -0.5 |
| `ang_vel_xy`（横滚俯仰角速度） | -0.05 |
| `orientation`（地形相关姿态） | -1.0 |
| `joint_acceleration`（关节加速度） | -2.5e-07 |
| `collision`（非足接触） | -10.0 |
| `action_rate`（动作变化） | -0.1 |
| `delta_torques`（力矩变化） | -1e-07 |
| `torques`（力矩大小） | -1e-05 |
| `hip_position`（髋外展偏差） | -0.5 |
| `joint_error`（关节偏差） | -0.04 |
| `feet_stumble`（足端绊碰） | -1.0 |
| `feet_edge`（沿口项） | 0.0 |
| `flight`（四足全腾空） | -1.0 |
| `arm_error`（机械臂保持误差） | -5.0 |
| `joint_limits`（关节限位） | -2.0 |

## 课程与过程

5→20cm，共7级，每个环境连续3次成功升一级、连续3次失败降一级。原基线起步站立1s、需稳定0.3s、最长3s等待、0.8s渐放。没有新增登台质量升级门槛。

## 全部任务参数

对应 `task_parameters.py:TaskConfig`；场景在climb_skill_env_cfg.py，奖励在mdp/rewards.py，课程在mdp/resets.py；V3质量在mdp/approach_quality.py、crossing_quality.py、quality_window.py。

| 参数 | 当前值 |
|---|---|
| `curriculum_only_enabled` | `false` |
| `quality_window_enabled` | `false` |
| `quality_window_size` | `5` |
| `quality_window_required` | `3` |
| `crossing_unsafe_seconds` | `0.08` |
| `crossing_commit_distance` | `0.02` |
| `crossing_quality_enabled` | `false` |
| `crossing_intent_height` | `0.065` |
| `crossing_intent_ratio` | `0.6` |
| `crossing_intent_distance` | `0.08` |
| `crossing_takeoff_min` | `0.03` |
| `crossing_takeoff_max` | `0.38` |
| `crossing_clearance_min` | `0.005` |
| `crossing_return_seconds` | `0.06` |
| `crossing_wall_seconds` | `0.08` |
| `crossing_timeout` | `1.5` |
| `crossing_failure_penalty` | `0.5` |
| `crossing_guidance_weight` | `0.5` |
| `crossing_reference_weight` | `1.0` |
| `approach_quality_enabled` | `false` |
| `rear_boundary_x` | `-0.5` |
| `gait_ground_seconds` | `0.8` |
| `gait_top_seconds` | `0.4` |
| `gait_mean_cost_max` | `0.35` |
| `gait_leg_cost_max` | `0.45` |
| `gait_frame_cost_max` | `0.45` |
| `gait_good_fraction_min` | `0.7` |
| `gait_speed_min` | `0.15` |
| `gait_speed_max` | `0.65` |
| `front_clearance_weight` | `0.5` |
| `front_clearance_distance` | `0.22` |
| `front_clearance_margin` | `0.03` |
| `front_clearance_scale` | `0.08` |
| `front_landing_bonus` | `0.5` |
| `front_landing_seconds` | `0.08` |
| `rear_workspace_enabled` | `true` |
| `rear_thigh_max` | `1.8` |
| `rear_calf_min` | `-2.5` |
| `rear_calf_max` | `-1.05` |
| `amp_body_gate` | `true` |
| `amp_enabled` | `true` |
| `seed` | `1` |
| `num_envs` | `4096` |
| `episode_seconds` | `24.0` |
| `physics_dt` | `0.005` |
| `decimation` | `4` |
| `spacing` | `7.0` |
| `box_length` | `2.4` |
| `box_width` | `1.2` |
| `box_height` | `0.2` |
| `box_front` | `0.75` |
| `curriculum` | `true` |
| `curriculum_min_height` | `0.05` |
| `curriculum_levels` | `7` |
| `promote_after` | `3` |
| `demote_after` | `3` |
| `arm_pose` | `[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]` |
| `arm_gravity_compensation` | `true` |
| `action_scale` | `0.25` |
| `max_position_offset` | `1.2` |
| `actuator_delay_max` | `4` |
| `approach_speed` | `0.4` |
| `top_margin` | `0.06` |
| `foot_radius` | `0.02` |
| `foot_height_tolerance` | `0.035` |
| `support_force` | `8.0` |
| `finish_offset` | `1.55` |
| `goal_offset` | `2.0` |
| `traversal_seconds` | `0.3` |
| `top_contact_memory` | `0.75` |
| `traversal_max_tilt` | `0.3` |
| `traversal_arm_error` | `0.08` |
| `minimum_stance_length` | `0.3` |
| `minimum_stance_width` | `0.16` |
| `failure_tilt` | `0.9` |
| `failure_arm_error` | `0.35` |
| `failure_arm_seconds` | `0.3` |
| `contact_failure_force` | `2.0` |
| `randomization` | `true` |
| `added_mass_range` | `[0.0, 1.0]` |
| `friction_range` | `[0.6, 1.0]` |
| `motor_scale_range` | `[0.9, 1.1]` |
| `reset_x_range` | `[-0.1, 0.1]` |
| `reset_y_range` | `[-0.08, 0.08]` |
| `reset_yaw_range` | `[-0.06, 0.06]` |
| `flat_stability_weight` | `4.0` |
| `flat_speed_weight` | `2.5` |
| `flat_speed_limit` | `0.45` |
| `flat_stability_margin` | `0.2` |
| `flat_stability_blend_width` | `0.1` |
| `flat_stability_tolerance` | `0.08` |
| `flat_angular_velocity_weight` | `0.3` |
| `flat_slip_weight` | `0.5` |
| `flat_angular_velocity_tolerance` | `0.4` |
| `flat_slip_tolerance` | `0.08` |
| `flat_slip_scale` | `0.25` |
| `startup_stand_seconds` | `1.0` |
| `startup_stable_seconds` | `0.3` |
| `startup_timeout` | `3.0` |
| `startup_ramp_seconds` | `0.8` |
| `forward_heading_weight` | `2.0` |
| `traversal_heading_tolerance` | `0.17453292519943295` |
| `traversal_lateral_tolerance` | `0.2` |
| `target_curvature_weight` | `0.09` |
| `contact_slip_weight` | `0.3` |
| `flat_use_body_gate` | `false` |
| `flat_ignore_edge_distance` | `true` |
| `flat_walking_enabled` | `true` |
| `flat_walk_start_height` | `0.15` |
| `flat_walk_velocity_tracking` | `false` |
| `path_deviation_weight` | `0.3` |
| `flat_walk_flight_weight` | `0.0` |
| `flat_walk_vertical_weight` | `0.0` |
| `flat_walk_air_variance_weight` | `0.0` |
| `flat_walk_long_air_weight` | `0.0` |
| `flat_walk_mirror_weight` | `0.0` |
| `diagonal_gait_enabled` | `true` |
| `diagonal_pair_weight` | `0.0` |
| `diagonal_sync_weight` | `0.0` |
| `diagonal_duration_weight` | `0.0` |
| `diagonal_transfer_seconds` | `0.06` |
| `diagonal_max_stance_seconds` | `0.5` |
| `diagonal_max_swing_seconds` | `0.35` |
| `walking_refinement_enabled` | `true` |
| `walking_early_gain` | `0.25` |
| `walking_pair_grace_seconds` | `0.015` |
| `walking_pair_ramp_seconds` | `0.03` |
| `walking_clearance_weight` | `0.0` |
| `walking_clearance_min` | `0.025` |
| `walking_clearance_max` | `0.06` |
| `walking_clearance_scale` | `0.04` |
| `straight_tracking_enabled` | `false` |
| `straight_heading_weight` | `0.5` |
| `straight_path_weight` | `1.0` |
| `straight_lateral_velocity_weight` | `1.0` |
| `straight_yaw_rate_weight` | `0.3` |
| `success_bonus` | `20.0` |
| `failure_penalty` | `-10.0` |

## PPO / AMP参数

PPO参数定义在agents/ppo_cfg.py，实现learning/ppo.py；AMP参数和数据处理在learning/amp.py，参考匹配在learning/motion_reference.py。每轮24步，5轮epoch×4个minibatch；iteration不是回合。

| 参数 | 当前值 |
|---|---|
| `amp.dataset` | `"${CLIMB_AMP_DATASET}"` |
| `amp.reward_scale` | `2.0` |
| `amp.learning_rate` | `0.0001` |
| `amp.gradient_penalty` | `10.0` |
| `amp.batch_size` | `1024` |
| `amp.updates` | `4` |
| `amp.replay_capacity` | `65536` |
| `amp.mirror_reference` | `true` |
| `amp.reference_weight` | `1.0` |
| `amp.reference_position_scale` | `0.35` |
| `amp.reference_velocity_scale` | `4.0` |
| `steps_per_env` | `24` |
| `iterations` | `15000` |
| `epochs` | `5` |
| `minibatches` | `4` |
| `learning_rate` | `0.0002` |
| `estimator_learning_rate` | `0.0001` |
| `gamma` | `0.99` |
| `gae_lambda` | `0.95` |
| `clip` | `0.2` |
| `value_coefficient` | `1.0` |
| `entropy_coefficient` | `0.01` |
| `desired_kl` | `0.01` |
| `max_gradient_norm` | `1.0` |
| `initial_std` | `1.0` |
| `history_update_frequency` | `20` |
| `privileged_reg_start` | `2000` |
| `privileged_reg_duration` | `3000` |
| `privileged_reg_max` | `0.1` |
| `save_interval` | `100` |
