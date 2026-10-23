"""GO2-PIPER WBC 的 MuJoCo 适配：模型、210维历史、18轴PD执行。

机器人转换沿用 climb 的已验证模型流程；导航运行不导入或修改 climb。
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from control_profiles import get_profile

ROOT = Path(__file__).resolve().parent
CONTRACT = json.loads((ROOT/'policy/contract.json').read_text(encoding='utf-8'))
C = CONTRACT['constants']
JOINTS = list(C['WBC_JOINT_NAMES'])
PHYSICS_DT = C['PHYSICS_DT']
DECIMATION = C['WBC_DECIMATION']
KP = np.array([30.]*12+[50.,50.,80.,30.,30.,20.])
KD = np.array([.6]*12+[3.,2.,3.,3.,2.5,1.])
EFFORT = np.array([23.7,23.7,45.43]*4+[20.,20.,15.,7.,5.,5.])
SPEED = np.array([30.1,30.1,15.7]*4+[3.]*6)
REFERENCE = np.array([-.1,.8,-1.5,.1,.8,-1.5,-.1,1.,-1.5,.1,1.,-1.5]+[0.]*6)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_actor(device, policy_path=None):
    import torch
    path = ROOT/'policy/actor.pt' if policy_path is None else Path(policy_path)
    if policy_path is None and sha(path) != CONTRACT['actor_sha256']:
        raise ValueError('WBC policy hash mismatch')
    actor = torch.jit.load(str(path), map_location=device).eval()
    # 自选模型也必须符合相同的210维观测和18维动作接口。
    with torch.inference_mode():
        output = actor(torch.zeros((1,210),device=device))
    if not isinstance(output,torch.Tensor) or output.shape != (1,18) or not torch.isfinite(output).all():
        raise ValueError('Policy must be a finite 210-input / 18-output TorchScript Actor')
    return actor


def build_model(friction=.6, added_mass=0., control_profile='isaac'):
    """将公共USD对应profile应用到独立XML，不更改源USD/XML。"""
    directory = ROOT/'robot'
    actuator_profile = get_profile(control_profile)
    profile = json.loads((directory/'piper_robot_profile.json').read_text(encoding='utf-8'))
    collision = json.loads((directory/'piper_collision_profile.json').read_text(encoding='utf-8'))
    # 规范mesh相对路径，兼容Windows和Linux，不依赖cwd。
    xml = ET.parse(directory/'source_robot.xml')
    compiler = xml.getroot().find('compiler')
    compiler.set('meshdir', str((directory/'assets').resolve()))
    for mesh in xml.findall('.//asset/mesh'):
        mesh.set('file', Path(mesh.get('file')).name)
    spec = mujoco.MjSpec.from_string(ET.tostring(xml.getroot(), encoding='unicode'))
    for entry in profile['bodies']:
        body = spec.body(entry['name'])
        if 'position' in entry:
            body.pos, body.quat = entry['position'], entry['quaternion']
        body.explicitinertial = True
        body.mass, body.ipos = entry['mass'], entry['center_of_mass']
        body.inertia = np.zeros(3)
        tensor = np.array(entry['inertia']).reshape(3, 3)
        body.fullinertia = tensor[[0, 1, 2, 0, 0, 1], [0, 1, 2, 1, 2, 2]]
        if entry['name'] == 'base_link':
            ratio = (body.mass + added_mass) / body.mass
            body.mass += added_mass
            body.fullinertia *= ratio
    for name in ('link7', 'link8'):
        body = spec.body(name)
        body.explicitinertial = True
        body.mass, body.inertia = 0., np.zeros(3)
    for entry in profile['joints']:
        joint = spec.joint(entry['name'])
        joint.axis, joint.range = entry['axis'], entry['range']
        joint.damping = actuator_profile.passive_damping[JOINTS.index(entry['name'])]
        joint.armature, joint.frictionloss = .01, actuator_profile.frictionloss
    # 删除旧简化碰撞，替换为公共USD的形状。相同collision bit隔离机器人内部自碰撞。
    for geom in list(spec.geoms):
        if geom.contype or geom.conaffinity:
            if geom.type == mujoco.mjtGeom.mjGEOM_MESH:
                # The original arm meshes serve both rendering and collision.
                # Retain their visuals when replacing physics with USD shapes.
                geom.contype = geom.conaffinity = 0
                geom.group = 2
                geom.density = 0.
            else:
                geom.delete()
    types = {'Cube': mujoco.mjtGeom.mjGEOM_BOX, 'Sphere': mujoco.mjtGeom.mjGEOM_SPHERE,
             'Cylinder': mujoco.mjtGeom.mjGEOM_CYLINDER, 'Mesh': mujoco.mjtGeom.mjGEOM_MESH}
    for i, shape in enumerate(collision['shapes']):
        options = dict(name=shape['name'], type=types[shape['kind']], pos=shape['position'],
                       quat=shape['quaternion'], contype=1, conaffinity=2, group=3,
                       density=0., friction=[friction, 0., 0.], condim=3, margin=0.,
                       rgba=[.4, .45, .5, 1.])
        if shape['kind'] == 'Mesh':
            name = f'usd_collision_mesh_{i}'
            spec.add_mesh(name=name, uservert=np.asarray(shape['vertices']).ravel().tolist())
            options['meshname'] = name
        else:
            options['size'] = list(shape['size']) + [0.]*(3-len(shape['size']))
        spec.body(shape['body']).add_geom(**options)
    for name in JOINTS:
        i = JOINTS.index(name)
        actuator = next(a for a in spec.actuators if a.target == name)
        actuator.ctrlrange = [-EFFORT[i], EFFORT[i]]
        actuator.ctrllimited = True
        actuator.forcerange = [-EFFORT[i], EFFORT[i]]
        actuator.forcelimited = True
    base = spec.body('base_link')
    base.pos, base.quat = [0., 0., .35], [1., 0., 0., 0.]
    # 清除底稿中的keyframe，它不是本任务的起点。
    for key in list(spec.keys):
        key.delete()
    spec.option.timestep = PHYSICS_DT
    spec.option.gravity = [0., 0., -9.81]
    spec.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    spec.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    spec.option.iterations = 50
    world = spec.worldbody
    surface = dict(contype=2, conaffinity=1, condim=3, friction=[friction, 0., 0.],
                   margin=0., rgba=[.3, .4, .55, 1.])
    world.add_geom(name='ground', type=mujoco.mjtGeom.mjGEOM_PLANE, size=[8., 4., .1], **surface)
    spec.visual.global_.offwidth, spec.visual.global_.offheight = 960, 540
    return spec.compile(), spec


class NavBridge:
    """单回合状态；所有关节数组始终使用策略的FR/FL/RR/RL顺序。"""

    def __init__(self, model, seed=42001, delay_ms=None, arm_zero=False, control_profile='isaac'):
        self.model = model
        self.control_profile = control_profile
        self.profile = get_profile(control_profile)
        self.kp, self.kd = np.array(self.profile.kp), np.array(self.profile.kd)
        self.arm_zero = bool(arm_zero)
        self.data = mujoco.MjData(model)
        self.rng = np.random.default_rng(seed)
        self.jids = np.array([model.joint(name).id for name in JOINTS])
        self.qids = model.jnt_qposadr[self.jids]
        self.dids = model.jnt_dofadr[self.jids]
        self.aids = np.array([next(i for i in range(model.nu)
                                  if model.actuator_trnid[i, 0] == joint) for joint in self.jids])
        self.base_id = model.body('base_link').id
        self.ee_id = model.body('end_effector').id
        self.data.qpos[:3] = [0., 0., .35]
        self.data.qpos[3:7] = [1., 0., 0., 0.]
        self.data.qpos[self.qids] = REFERENCE
        mujoco.mj_forward(model, self.data)
        # 原执行器：腿共用一组0..4步延迟，机械臂每轴独立采样。
        delays = self.rng.integers(0, 5, 7)
        self.delays = np.r_[np.repeat(delays[0], 12), delays[1:]]
        delay_ms = self.profile.default_delay_ms if delay_ms is None else delay_ms
        if delay_ms is not None:
            if delay_ms not in (0, 5, 10, 15, 20):
                raise ValueError('delay_ms must be 0, 5, 10, 15 or 20')
            self.delays[:] = delay_ms//5
        self.target_queue = deque(maxlen=5)
        self.history = None
        self.previous_action = np.zeros(18)
        self.targets = REFERENCE.copy()
        if self.arm_zero:
            self.targets[12:] = 0.
        self.base_command = np.zeros(3)
        self.ee_command = np.r_[C['EE_NOMINAL'], C['EE_QUATERNION_WXYZ']].astype(float)
        self.raw_torque = np.zeros(18)
        self.torque = np.zeros(18)
        self.peak_torque = np.zeros(18)
        self.peak_speed = np.zeros(18)
        self.saturation_steps = np.zeros(18, dtype=int)
        self.speed_exceeded_steps = np.zeros(18, dtype=int)
        self.angle_violation = np.zeros(18)
        self.physics_steps = self.policy_ticks = 0

    def set_command(self, velocity, ee_position):
        """10Hz调用；物理量→原6维归一化动作→原限速映射。

        velocity: [vx,vy,wz]，EE: [link0相对x,y,世界绝对z]。
        超过原动作边界直接报错，避免悄悄裁剪用户命令。
        """
        velocity = np.asarray(velocity, dtype=float)
        ee_position = np.asarray(ee_position, dtype=float)
        if velocity.shape != (3,) or ee_position.shape != (3,):
            raise ValueError('velocity and ee_position must each have three elements')
        action = np.r_[velocity/np.asarray(C['VELOCITY_SCALE']),
                       (ee_position-C['EE_NOMINAL'])/np.asarray(C['EE_OFFSET_SCALE'])]
        if not np.isfinite(action).all() or np.any(abs(action)>1.+1e-8):
            raise ValueError('Command outside original go2_push action bounds')
        self.base_command += np.clip(velocity-self.base_command,
                                     -np.asarray(C['VELOCITY_RATE_LIMIT']), C['VELOCITY_RATE_LIMIT'])
        self.ee_command[:3] += np.clip(ee_position-self.ee_command[:3],
                                      -np.asarray(C['EE_RATE_LIMIT']), C['EE_RATE_LIMIT'])

    def state(self):
        rotation = self.data.xmat[self.base_id].reshape(3, 3)
        gravity = rotation.T@np.array([0., 0., -1.])
        yaw = float(np.arctan2(rotation[1, 0], rotation[0, 0]))
        tilt = float(np.arccos(np.clip(-gravity[2], -1., 1.)))
        return rotation, gravity, yaw, tilt

    def set_wbc_command(self, velocity, ee_pose):
        """直接发送WBC物理命令；不经过推箱任务的末端XYZ范围映射。

        ee_pose=[link0相对x/y,世界z,link0相对四元数wxyz]。
        采用所选部署配置的速度边界/命令变化率；任意末端位姿不代表在训练分布内。
        """
        velocity, pose = np.asarray(velocity, dtype=float), np.asarray(ee_pose, dtype=float)
        if velocity.shape != (3,) or pose.shape != (7,) or not np.isfinite(np.r_[velocity, pose]).all():
            raise ValueError('WBC command requires finite velocity(3) and EE pose(7)')
        if np.any(abs(velocity) > np.asarray(self.profile.wbc_velocity_limits) + 1e-8):
            raise ValueError('Velocity exceeds selected WBC deployment bounds')
        norm = np.linalg.norm(pose[3:])
        if norm < 1e-8:
            raise ValueError('EE quaternion must be nonzero')
        if self.profile.command_slew:
            self.base_command += np.clip(velocity-self.base_command,
                                         -np.asarray(C['VELOCITY_RATE_LIMIT']), C['VELOCITY_RATE_LIMIT'])
            self.ee_command[:3] += np.clip(pose[:3]-self.ee_command[:3],
                                          -np.asarray(C['EE_RATE_LIMIT']), C['EE_RATE_LIMIT'])
        else:
            self.base_command[:] = velocity
            self.ee_command[:3] = pose[:3]
        self.ee_command[3:] = pose[3:]/norm

    def ee_pose(self, data=None):
        """读取WBC混合坐标位姿；USD的link0在本MJCF中命名为Piper。"""
        data = self.data if data is None else data
        root_id = self.model.body('Piper').id
        rotation = data.xmat[root_id].reshape(3, 3)
        local = rotation.T @ (data.xpos[self.ee_id]-data.xpos[root_id])
        relative_rotation = rotation.T @ data.xmat[self.ee_id].reshape(3, 3)
        quat = np.empty(4)
        mujoco.mju_mat2Quat(quat, relative_rotation.ravel())
        return np.r_[local[:2], data.xpos[self.ee_id, 2], quat]

    def zero_arm_ee_pose(self):
        """只在独立MjData中计算六关节零位FK，不改正在运行的机器人。"""
        reference = mujoco.MjData(self.model)
        reference.qpos[:] = self.data.qpos
        reference.qpos[self.qids[12:]] = 0.
        mujoco.mj_forward(self.model, reference)
        return self.ee_pose(reference)

    def velocity(self):
        """根线速度从世界系转到机体系；MuJoCo freejoint角速度本就在机体系。"""
        rotation = self.state()[0]
        linear_body = rotation.T@self.data.qvel[:3]
        angular_world = rotation@self.data.qvel[3:6]
        return np.r_[linear_body[:2], angular_world[2]]

    def ee_position(self):
        rotation = self.state()[0]
        local = rotation.T@(self.data.xpos[self.ee_id]-self.data.qpos[:3])
        return np.r_[local[:2], self.data.xpos[self.ee_id, 2]]

    def observation(self):
        """仅在50Hz tick调用一次：每个term独立保留3帧，再拼成210维。

        7个历史数组的形状依次为(3,3),(3,3),(3,18),(3,18),
        (3,18),(3,3),(3,7)，每个数组oldest→newest。
        """
        terms = (self.data.qvel[3:6]*.2, self.state()[1],
                 self.data.qpos[self.qids]-REFERENCE,
                 self.data.qvel[self.dids]*.05, self.previous_action,
                 self.base_command, self.ee_command)
        if self.history is None:
            self.history = [np.tile(term, (3, 1)) for term in terms]
        else:
            for history, term in zip(self.history, terms):
                history[:-1] = history[1:]
                history[-1] = term
        observation = np.concatenate([history.ravel() for history in self.history]).astype(np.float32)
        if observation.shape != (210,) or not np.isfinite(observation).all():
            raise FloatingPointError('Invalid WBC observation')
        if self.profile.observation_limit is not None:
            observation = np.clip(observation, -self.profile.observation_limit, self.profile.observation_limit)
        return observation

    @property
    def policy_active(self):
        return self.physics_steps >= round(self.profile.startup_pd_seconds/PHYSICS_DT)

    def set_action(self, action):
        action = np.asarray(action)
        if action.shape != (18,) or not np.isfinite(action).all():
            raise ValueError('WBC output must be finite (18,)')
        if not self.policy_active:
            return
        if self.profile.action_limit is not None:
            action = np.clip(action, -self.profile.action_limit, self.profile.action_limit)
        self.previous_action = action.astype(float).copy()
        # 默认执行全部18轴残差；独立零位模式在下方覆盖机械臂六轴。
        self.targets = REFERENCE+C['ACTION_SCALE']*self.previous_action
        # 实验模式：仅覆盖机械臂目标，经原延迟、PD和力矩限幅执行。
        # 历史动作必须对应实际执行的目标，不能回传被覆盖的机械臂动作。
        if self.arm_zero:
            self.targets[12:] = 0.
            self.previous_action[12:] = (self.targets[12:]-REFERENCE[12:])/C['ACTION_SCALE']
        self.policy_ticks += 1

    def physics_step(self):
        """200Hz延迟PD→力矩限幅→motor；独立零位臂增加模型偏置力补偿。"""
        if not self.target_queue:
            self.target_queue.extend([self.targets.copy() for _ in range(5)])
        else:
            self.target_queue.append(self.targets.copy())
        delayed = np.array([self.target_queue[-1-int(lag)][i]
                            for i, lag in enumerate(self.delays)])
        self.raw_torque = self.kp*(delayed-self.data.qpos[self.qids])-self.kd*self.data.qvel[self.dids]
        if self.arm_zero:
            # Joint position control needs feedforward against gravity. MuJoCo's
            # bias also includes velocity-dependent terms; no leg compensation.
            self.raw_torque[12:] += self.data.qfrc_bias[self.dids[12:]]
        self.torque = np.clip(self.raw_torque, -EFFORT, EFFORT)
        self.data.ctrl[self.aids] = self.torque
        mujoco.mj_step(self.model, self.data)
        mujoco.mj_fwdPosition(self.model, self.data)
        mujoco.mj_fwdVelocity(self.model, self.data)
        if not np.isfinite(self.data.qpos).all() or not np.isfinite(self.data.qvel).all():
            raise FloatingPointError('Nonfinite simulation state')
        self.physics_steps += 1
        self.peak_torque = np.maximum(self.peak_torque, abs(self.torque))
        self.peak_speed = np.maximum(self.peak_speed, abs(self.data.qvel[self.dids]))
        self.saturation_steps += abs(self.raw_torque)>=EFFORT
        self.speed_exceeded_steps += abs(self.data.qvel[self.dids])>SPEED
        q, limits = self.data.qpos[self.qids], self.model.jnt_range[self.jids]
        self.angle_violation = np.maximum(self.angle_violation,
                                          np.maximum(limits[:, 0]-q, q-limits[:, 1]))

    def failure(self):
        if self.data.qpos[2]<.16:
            return 'low_posture'
        if self.state()[3]>np.deg2rad(55.):
            return 'bad_orientation'
        return ''

