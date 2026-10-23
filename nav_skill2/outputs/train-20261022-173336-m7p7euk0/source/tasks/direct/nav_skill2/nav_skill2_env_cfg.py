"""Isaac Lab DirectRLEnv外部任务：平地、完整带臂机器人、真实限矩。"""
import isaaclab.sim as sim_utils
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from .parameters import TaskConfig,ACTOR_OBS
from .robot import robot_config

@configclass
class NavSkill2EnvCfg(DirectRLEnvCfg):
    decimation=4
    episode_length_s=25.
    action_space=18
    observation_space=ACTOR_OBS
    state_space=0
    task: TaskConfig=TaskConfig()
    sim=sim_utils.SimulationCfg(dt=.005,render_interval=4)
    scene=InteractiveSceneCfg(num_envs=2048,env_spacing=12.,replicate_physics=True)
    def __post_init__(self):configure(self,self.task,self.sim.device)

def configure(cfg,task,device):
    task.validate();cfg.task=task;cfg.seed=task.seed
    cfg.scene.num_envs=task.num_envs;cfg.scene.env_spacing=task.spacing
    cfg.episode_length_s=task.episode_seconds;cfg.decimation=task.decimation
    cfg.sim.dt=task.physics_dt;cfg.sim.render_interval=task.decimation;cfg.sim.device=device
    cfg.sim.physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=.8,dynamic_friction=.6,restitution=0.,friction_combine_mode='min',restitution_combine_mode='min')
    cfg.robot=robot_config(task)
    cfg.contact=ContactSensorCfg(prim_path='/World/envs/env_.*/Robot/.*',history_length=4,update_period=task.physics_dt,track_air_time=True)
    cfg.viewer.eye=(3.,3.,2.);cfg.viewer.lookat=(0.,0.,.3)
    cfg.viewer.resolution=(960,540);cfg.viewer.origin_type='env';cfg.viewer.env_index=0
    return cfg

def make_env_config(task,device='cuda:0'):return configure(NavSkill2EnvCfg(),task,device)
