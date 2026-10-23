"""Isaac Lab scene; import only after AppLauncher starts Isaac Sim.

Robot parameters follow the project's Apache-2.0 GO2-PIPER asset and box robot configuration.
The USD asset is reused read-only; no old skill environment/controller is imported.
"""

import os
from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import DelayedPDActuatorCfg
from isaaclab.assets import ArticulationCfg, RigidObjectCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from .task_parameters import OBSERVATIONS, TaskConfig


def robot_usd():
    relative = Path("source/LeggedManip_Lab/LeggedManip_Lab/assets/go2_piper/go2_piper.usd")
    default = next((parent / relative for parent in Path(__file__).resolve().parents if (parent / relative).is_file()), Path("go2_piper.usd"))
    path = Path(os.environ.get("CLIMB_ROBOT_USD", default)).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Robot USD missing: {path}; set CLIMB_ROBOT_USD")
    return str(path)


def robot_config(task):
    # 显式DelayedPD：腿和每个臂关节组均使用原执行器；max_delay单位是5ms物理步。
    common = dict(armature=0.01, friction=0.01, min_delay=0, max_delay=task.actuator_delay_max)
    effort = {".*_hip_joint": 23.7, ".*_thigh_joint": 23.7, ".*_calf_joint": 45.43}
    speed = {".*_hip_joint": 30.1, ".*_thigh_joint": 30.1, ".*_calf_joint": 15.7}
    actuators = {"legs": DelayedPDActuatorCfg(
        joint_names_expr=[".*_hip_joint", ".*_thigh_joint", ".*_calf_joint"],
        stiffness=30.0, damping=0.6, effort_limit=effort, effort_limit_sim=effort,
        velocity_limit=speed, velocity_limit_sim=speed, **common)}
    for i, (kp, kd, torque) in enumerate(zip((50., 50., 80., 30., 30., 20.),
                                            (3., 2., 3., 3., 2.5, 1.),
                                            (20., 20., 15., 7., 5., 5.)), 1):
        actuators[f"arm{i}"] = DelayedPDActuatorCfg(
            joint_names_expr=[f"joint{i}"], stiffness=kp, damping=kd,
            effort_limit=torque, effort_limit_sim=torque, velocity_limit=3., velocity_limit_sim=3., **common)
    positions = {"[FR]L_hip_joint": 0.1, "[FR]R_hip_joint": -0.1,
                 "F._thigh_joint": 0.8, "R._thigh_joint": 1.0, ".*_calf_joint": -1.5}
    positions.update({f"joint{i}": q for i, q in enumerate(task.arm_pose, 1)})
    return ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=robot_usd(), activate_contact_sensors=True,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False, retain_accelerations=False,
                linear_damping=0., angular_damping=0., max_linear_velocity=1000., max_angular_velocity=1000.,
                max_depenetration_velocity=1.),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False, solver_position_iteration_count=8, solver_velocity_iteration_count=2)),
        init_state=ArticulationCfg.InitialStateCfg(pos=(0., 0., 0.33), joint_pos=positions, joint_vel={".*": 0.}),
        soft_joint_pos_limit_factor=0.9, actuators=actuators)


@configclass
class ClimbSkillEnvCfg(DirectRLEnvCfg):
    decimation = 4
    episode_length_s = 24.
    action_space = 18
    observation_space = OBSERVATIONS
    state_space = 0
    task: TaskConfig = TaskConfig()

    def __post_init__(self):
        configure_scene(self, self.task, self.sim.device)

    sim = sim_utils.SimulationCfg(dt=0.005, render_interval=4)
    scene = InteractiveSceneCfg(num_envs=256, env_spacing=5., replicate_physics=True)


def make_env_config(task: TaskConfig, device="cuda:0"):
    task.validate()
    cfg = ClimbSkillEnvCfg()
    return configure_scene(cfg, task, device)


def configure_scene(cfg, task, device):
    cfg.task = task
    cfg.seed = task.seed
    cfg.scene.num_envs = task.num_envs
    cfg.scene.env_spacing = task.spacing
    cfg.episode_length_s = task.episode_seconds
    cfg.decimation = task.decimation
    cfg.sim.dt = task.physics_dt
    cfg.sim.render_interval = task.decimation
    cfg.sim.device = device
    # 地面／箱体静摩擦0.8、动摩擦0.6；min混合使接触有效系数受较小一侧限制。
    cfg.sim.physics_material = sim_utils.RigidBodyMaterialCfg(
        static_friction=0.8, dynamic_friction=0.6, restitution=0.,
        friction_combine_mode="min", restitution_combine_mode="min")
    cfg.robot = robot_config(task)
    cfg.box = RigidObjectCfg(
        prim_path="/World/envs/env_.*/Box",
        spawn=sim_utils.CuboidCfg(
            size=(task.box_length, task.box_width, task.box_height),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True, disable_gravity=True),
            collision_props=sim_utils.CollisionPropertiesCfg(), mass_props=sim_utils.MassPropertiesCfg(mass=100.),
            physics_material=cfg.sim.physics_material,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.35, 0.45, 0.65))),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(task.box_front + task.box_length / 2, 0., task.box_height / 2)))
    # 力历史4个物理采样；未显式设置force_threshold，IsaacLab0.54.4默认力模长门槛1N。
    cfg.contact = ContactSensorCfg(prim_path="/World/envs/env_.*/Robot/.*", history_length=4,
                                   update_period=task.physics_dt, track_air_time=task.flat_walking_enabled)
    cfg.viewer.eye = (3.8, 3.8, 2.4)
    cfg.viewer.lookat = (task.box_front + task.box_length / 2, 0.0, 0.3)
    cfg.viewer.origin_type = "env"
    cfg.viewer.env_index = 0
    cfg.viewer.resolution = (960, 540)
    return cfg
