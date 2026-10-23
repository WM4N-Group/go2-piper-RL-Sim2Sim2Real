"""与Climb一致的默认姿态、PD、实际限矩；共用只读USD。"""
import os
from pathlib import Path
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import DelayedPDActuatorCfg

def robot_usd():
    candidate=next((p/'asset/go2_piper/go2_piper.usd' for p in Path(__file__).resolve().parents if (p/'asset/go2_piper/go2_piper.usd').is_file()),None)
    path=Path(os.environ.get('ROBOT_USD',os.environ.get('CLIMB_ROBOT_USD',str(candidate)))).resolve()
    if not path.is_file(): raise FileNotFoundError(f'Missing robot USD: {path}; set ROBOT_USD')
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

