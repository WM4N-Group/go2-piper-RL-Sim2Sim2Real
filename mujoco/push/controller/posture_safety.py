"""原通用低姿态终止条件，不变更门槛。"""
import torch
from compat import ManagerTermBase, SceneEntityCfg
from .box_rewards import support_clearance

class LowPosture(ManagerTermBase):
    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        self.duration = torch.zeros(env.num_envs, device=env.device)

    def reset(self, env_ids=None):
        self.duration[slice(None) if env_ids is None else env_ids] = 0.0

    def __call__(self, env, asset_cfg: SceneEntityCfg, sensor_cfg: SceneEntityCfg, min_clearance=0.18, grace_time=0.4, duration=0.2):
        robot = env.scene[asset_cfg.name]
        clearance = support_clearance(
            robot.data.root_pos_w[:, 2], robot.data.body_pos_w[:, asset_cfg.body_ids, 2],
            env.scene.sensors[sensor_cfg.name].data.net_forces_w[:, sensor_cfg.body_ids, 2],
        )
        low = (clearance < min_clearance) & (env.episode_length_buf * env.step_dt >= grace_time)
        self.duration = torch.where(low, self.duration + env.step_dt, 0.0)
        return self.duration >= duration
