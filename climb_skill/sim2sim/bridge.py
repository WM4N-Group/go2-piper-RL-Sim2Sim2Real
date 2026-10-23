"""V1/900的MuJoCo适配：观测历史、显式关节顺序、延迟PD、原任务终止。

MuJoCo动力学在CPU运行；相机渲染可用GPU。此处不包含技能切换或新任务训练。
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent
JOINTS = [f'{leg}_{joint}_joint' for leg in ('FL', 'FR', 'RL', 'RR')
          for joint in ('hip', 'thigh', 'calf')] + [f'joint{i}' for i in range(1, 7)]
FEET = [f'{leg}_foot' for leg in ('FL', 'FR', 'RL', 'RR')]
KP = np.array([30.]*12 + [50., 50., 80., 30., 30., 20.])
KD = np.array([.6]*12 + [3., 2., 3., 3., 2.5, 1.])
EFFORT = np.array([23.7, 23.7, 45.43]*4 + [20., 20., 15., 7., 5., 5.])
SPEED = np.array([30.1, 30.1, 15.7]*4 + [3.]*6)
REFERENCE = np.array([.1, .8, -1.5, -.1, .8, -1.5, .1, 1., -1.5, -.1, 1., -1.5] + [0.]*6)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def robot_directory():
    bundled = ROOT/'robot'
    return bundled if bundled.is_dir() else ROOT.parents[1]/'asset/go2_piper/mujoco'


def load_contract():
    result = json.loads((ROOT/'policy/contract.json').read_text())
    if result['version'] != 'V1' or result['iteration'] != 900:
        raise ValueError('Expected V1 checkpoint 900')
    if sha(ROOT/'policy/actor.pt') != result['actor_sha256']:
        raise ValueError('Actor SHA256 mismatch')
    if list(result['configuration']['joint_order']) != JOINTS:
        raise ValueError('Joint order mismatch')
    return result


def build_model(cfg, height, friction=.6, added_mass=0.):
    """将公共USD对应profile应用到独立XML，不更改源USD/XML。"""
    directory = robot_directory()
    profile = json.loads((directory/'piper_robot_profile.json').read_text())
    collision = json.loads((directory/'piper_collision_profile.json').read_text())
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
        joint.damping = [0., 0., 0.]
        joint.armature, joint.frictionloss = .01, .01
    # 删除旧简化碰撞，替换为公共USD的形状。相同collision bit隔离机器人内部自碰撞。
    for geom in list(spec.geoms):
        if geom.contype or geom.conaffinity:
            spec.delete(geom)
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
    base.pos, base.quat = [0., 0., .33], [1., 0., 0., 0.]
    # 清除底稿中的keyframe，它不是本任务的起点。
    for key in list(spec.keys):
        spec.delete(key)
    spec.option.timestep = cfg['physics_dt']
    spec.option.gravity = [0., 0., -9.81]
    spec.option.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    spec.option.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
    spec.option.iterations = 50
    world = spec.worldbody
    surface = dict(contype=2, conaffinity=1, condim=3, friction=[friction, 0., 0.],
                   margin=0., rgba=[.3, .4, .55, 1.])
    world.add_geom(name='ground', type=mujoco.mjtGeom.mjGEOM_PLANE, size=[8., 4., .1], **surface)
    world.add_geom(name='platform', type=mujoco.mjtGeom.mjGEOM_BOX,
                   pos=[cfg['box_front']+cfg['box_length']/2, 0., height-cfg['box_height']/2],
                   size=[cfg['box_length']/2, cfg['box_width']/2, cfg['box_height']/2], **surface)
    spec.visual.global_.offwidth, spec.visual.global_.offheight = 960, 540
    return spec.compile(), spec


class ClimbBridge:
    def __init__(self, model, cfg, height, seed=42001, randomization=False):
        self.model, self.cfg, self.height = model, cfg, height
        self.data = mujoco.MjData(model)
        self.gravity_data = mujoco.MjData(model)
        self.rng = np.random.default_rng(seed)
        self.jids = np.array([model.joint(n).id for n in JOINTS])
        self.qids = model.jnt_qposadr[self.jids]
        self.dids = model.jnt_dofadr[self.jids]
        self.aids = np.array([next(i for i in range(model.nu) if model.actuator_trnid[i, 0] == j)
                              for j in self.jids])
        self.feet_ids = np.array([model.body(n).id for n in FEET])
        self.base_id = model.body('base_link').id
        self.forbidden = [i for i in range(1, model.nbody)
                          if not re.fullmatch(r'(?:FL|FR|RL|RR)_(?:foot|hip|thigh|calf)', model.body(i).name)]
        self.reference = REFERENCE.copy(); self.reference[12:] = cfg['arm_pose']
        self.kp, self.kd = KP.copy(), KD.copy()
        if randomization:
            self.kp[:12] *= self.rng.uniform(*cfg['motor_scale_range'], 12)
            self.kd[:12] *= self.rng.uniform(*cfg['motor_scale_range'], 12)
        # 每组执行器每回合一个0..4物理步延迟；腿12轴共用一组，臂每轴一组。
        delays = self.rng.integers(0, cfg['actuator_delay_max']+1, 7)
        self.delays = np.r_[np.repeat(delays[0], 12), delays[1:]]
        self.data.qpos[:3] = [self.rng.uniform(*cfg['reset_x_range']),
                             self.rng.uniform(*cfg['reset_y_range']), .33]
        yaw = self.rng.uniform(*cfg['reset_yaw_range'])
        self.data.qpos[3:7] = [np.cos(yaw/2), 0., 0., np.sin(yaw/2)]
        self.data.qpos[self.qids] = self.reference
        self.data.qpos[self.qids[:12]] += self.rng.uniform(-.03, .03, 12)
        mujoco.mj_forward(model, self.data)
        self.soft_limits = model.jnt_range[self.jids].copy()
        mid = self.soft_limits.mean(-1); half = np.diff(self.soft_limits, axis=1)[:, 0] * .45
        self.soft_limits = np.stack([mid-half, mid+half], axis=-1)
        self.actions = np.zeros(18)
        self.targets = self.reference.copy()
        self.history = None
        self.queue = deque(maxlen=cfg['actuator_delay_max']+1)
        self.forces = np.zeros((model.nbody, 3))
        self.force_history = deque(maxlen=cfg['decimation'])
        self.elapsed = self.stable_time = 0.
        self.ready = False; self.release_time = np.inf
        self.hold = self.arm_bad_time = 0.
        self.top_age = np.full(4, np.inf)
        self.ever_top = np.zeros(4, dtype=bool)
        self.max_supported = 0
        self.steps = 0
        self.peak_torque = np.zeros(18); self.saturation_count = np.zeros(18, dtype=int)
        self.speed_exceeded_count = np.zeros(18, dtype=int)
        self.peak_speed = np.zeros(18); self.peak_arm_error = 0.
        self.raw_torque = self.applied_torque = np.zeros(18)
        self.max_root_x = self.data.qpos[0]

    @property
    def dt(self):
        return self.cfg['physics_dt']*self.cfg['decimation']

    @property
    def gain(self):
        if self.cfg['startup_stand_seconds'] <= 0:
            return 1.
        return float(np.clip((self.elapsed-self.release_time)/self.cfg['startup_ramp_seconds'], 0., 1.)) if self.ready else 0.

    def state(self):
        rotation = self.data.xmat[self.base_id].reshape(3, 3)
        gravity = rotation.T @ np.array([0., 0., -1.])
        yaw = np.arctan2(rotation[1, 0], rotation[0, 0])
        return rotation, gravity, yaw, float(np.arccos(np.clip(-gravity[2], -1., 1.)))

    def observation(self):
        cfg = self.cfg
        rotation, gravity, yaw, _ = self.state()
        delta = np.array([cfg['box_front']+cfg['goal_offset']-self.data.qpos[0], -self.data.qpos[1]])
        c, s = np.cos(yaw), np.sin(yaw)
        local_delta = np.array([c*delta[0]+s*delta[1], -s*delta[0]+c*delta[1]])
        heading = -yaw if cfg['straight_tracking_enabled'] else np.arctan2(delta[1], delta[0])-yaw
        heading = np.arctan2(np.sin(heading), np.cos(heading))
        proprio = np.r_[self.data.qvel[3:6]*.25, gravity, np.clip(local_delta, -2., 2.), heading,
                        cfg['approach_speed']*self.gain, self.data.qpos[self.qids]-self.reference,
                        self.data.qvel[self.dids]*.05, self.actions,
                        (self.forces[self.feet_ids, 2]>2.).astype(float)-.5, self.height]
        # torch.cartesian_prod的x外循环、y内循环；不能交换132点顺序。
        sx, sy = np.meshgrid(np.linspace(-.45, 1.2, 12), np.linspace(-.75, .75, 11), indexing='ij')
        x = self.data.qpos[0] + c*sx.ravel()-s*sy.ravel()
        y = self.data.qpos[1] + s*sx.ravel()+c*sy.ravel()
        on_box = (x>=cfg['box_front']) & (x<=cfg['box_front']+cfg['box_length']) & (abs(y)<=cfg['box_width']/2)
        scan = np.clip(self.data.qpos[2]-.3-on_box*self.height, -1., 1.)
        frame = proprio.copy(); frame[6:9] = 0.
        if self.history is None:
            self.history = np.tile(frame, (10, 1))
        # 部署history分支忽略真实速度/29维特权；保留布局占位，不将真值送入Actor。
        obs = np.r_[proprio, scan, np.zeros(32), self.history.ravel()].astype(np.float32)
        self.history = np.concatenate([self.history[1:], frame[None]])
        if obs.shape != (923,) or not np.isfinite(obs).all():
            raise FloatingPointError('Invalid observation')
        return np.clip(obs, -100., 100.)

    def set_action(self, action):
        cfg = self.cfg
        action = np.asarray(action).reshape(18).copy()
        if not np.isfinite(action).all() or np.any(action[12:] != 0):
            raise ValueError('Invalid actor action/arm residual')
        limit = cfg['max_position_offset']/cfg['action_scale']
        self.actions = np.clip(action, -limit, limit)*self.gain
        self.targets = self.reference + cfg['action_scale']*self.actions
        self.targets[:12] = np.clip(self.targets[:12], *self.soft_limits[:12].T)
        if cfg['rear_workspace_enabled']:
            self.targets[[7, 10]] = np.minimum(self.targets[[7, 10]], cfg['rear_thigh_max'])
            self.targets[[8, 11]] = np.clip(self.targets[[8, 11]], cfg['rear_calf_min'], cfg['rear_calf_max'])
        self.targets[12:] = self.reference[12:]

    def contact_forces(self):
        forces = np.zeros_like(self.forces)
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            f = np.zeros(6)
            mujoco.mj_contactForce(self.model, self.data, i, f)
            world = contact.frame.reshape(3, 3).T @ f[:3]
            b1, b2 = self.model.geom_bodyid[[contact.geom1, contact.geom2]]
            forces[b1] -= world; forces[b2] += world
        return forces

    def physics_step(self):
        cfg = self.cfg
        feedforward = np.zeros(18)
        if cfg['arm_gravity_compensation']:
            # 将速度清零，单独求重力，避免把科氏/离心力误当作重力补偿。
            g = self.gravity_data
            g.qpos[:] = self.data.qpos; g.qvel[:] = 0.
            mujoco.mj_fwdPosition(self.model, g)
            mujoco.mj_fwdVelocity(self.model, g)
            gravity = np.zeros(self.model.nv)
            mujoco.mj_rne(self.model, g, 0, gravity)
            feedforward[12:] = gravity[self.dids[12:]]
        command = np.stack([self.targets, feedforward])
        if not self.queue:
            self.queue.extend([command.copy() for _ in range(self.queue.maxlen)])
        else:
            self.queue.append(command)
        delayed = np.stack([self.queue[-1-int(lag)][:, i] for i, lag in enumerate(self.delays)], axis=1)
        self.raw_torque = self.kp*(delayed[0]-self.data.qpos[self.qids])-self.kd*self.data.qvel[self.dids]+delayed[1]
        self.applied_torque = np.clip(self.raw_torque, -EFFORT, EFFORT)
        self.data.ctrl[self.aids] = self.applied_torque
        mujoco.mj_step(self.model, self.data)
        self.forces = self.contact_forces()
        self.force_history.append(self.forces.copy())
        self.peak_torque = np.maximum(self.peak_torque, abs(self.applied_torque))
        self.saturation_count += abs(self.raw_torque) >= EFFORT
        self.peak_speed = np.maximum(self.peak_speed, abs(self.data.qvel[self.dids]))
        self.speed_exceeded_count += abs(self.data.qvel[self.dids]) > SPEED

    def status(self):
        """原V1成功条件；它确认登台，不宣称已经减速停稳。"""
        cfg, d = self.cfg, self.data
        self.steps += 1; self.elapsed += self.dt
        _, _, yaw, tilt = self.state()
        feet, force = d.xpos[self.feet_ids], self.forces[self.feet_ids]
        if cfg['startup_stand_seconds'] > 0:
            grounded = ((force[:, 2]>=cfg['support_force']) &
                        (abs(feet[:, 2]-cfg['foot_radius'])<=cfg['foot_height_tolerance'])).all()
            stable = grounded and tilt<.10 and np.linalg.norm(d.qvel[:3])<.10 and np.linalg.norm(d.qvel[3:6])<.30
            self.stable_time = self.stable_time+self.dt if stable and not self.ready else 0.
            if not self.ready and self.elapsed>=cfg['startup_stand_seconds'] and self.stable_time>=cfg['startup_stable_seconds']:
                self.ready, self.release_time = True, self.elapsed
        arm_error = float(abs(d.qpos[self.qids[12:]]-self.reference[12:]).max())
        self.peak_arm_error = max(self.peak_arm_error, arm_error)
        self.arm_bad_time = self.arm_bad_time+self.dt if arm_error>cfg['failure_arm_error'] else 0.
        bad_contact = max((np.linalg.norm(f[self.forbidden], axis=-1).max() for f in self.force_history), default=0.) > cfg['contact_failure_force']
        reasons = []
        if cfg['startup_stand_seconds']>0 and not self.ready and self.elapsed>=cfg['startup_timeout']: reasons.append('startup_unstable')
        if bad_contact: reasons.append('base_or_arm_contact')
        if tilt>cfg['failure_tilt']: reasons.append('bad_orientation')
        if d.qpos[2]<.16: reasons.append('low_posture')
        if self.arm_bad_time>=cfg['failure_arm_seconds']: reasons.append('arm_hold_lost')
        if abs(d.qpos[1])>1.5 or d.qpos[0]<cfg['rear_boundary_x'] or d.qpos[0]>cfg['box_front']+cfg['box_length']+.5: reasons.append('out_of_bounds')
        inside = ((feet[:, 0]>=cfg['box_front']+cfg['top_margin']) &
                  (feet[:, 0]<=cfg['box_front']+cfg['box_length']-cfg['top_margin']) &
                  (abs(feet[:, 1])<=cfg['box_width']/2-cfg['top_margin']))
        support = inside & (abs(feet[:, 2]-cfg['foot_radius']-self.height)<=cfg['foot_height_tolerance']) & (force[:, 2]>=cfg['support_force'])
        self.top_age = np.where(support, 0., self.top_age+self.dt)
        self.ever_top |= support; self.max_supported = max(self.max_supported, int(support.sum()))
        self.max_root_x = max(self.max_root_x, float(d.qpos[0]))
        geometry = bool((inside & (feet[:, 2]-cfg['foot_radius']>=self.height-cfg['foot_height_tolerance']) &
                         (self.top_age<=cfg['top_contact_memory'])).all() and
                        d.qpos[0]>=cfg['box_front']+cfg['finish_offset'] and
                        np.ptp(feet[:, 0])>=cfg['minimum_stance_length'] and np.ptp(feet[:, 1])>=cfg['minimum_stance_width'])
        if cfg['traversal_heading_tolerance']>0:
            geometry &= abs(yaw)<=cfg['traversal_heading_tolerance'] and abs(d.qpos[1])<=cfg['traversal_lateral_tolerance']
        self.hold = self.hold+self.dt if geometry and not reasons else 0.
        success = bool(self.hold>=cfg['traversal_seconds'] and support.sum()>=2 and tilt<cfg['traversal_max_tilt'] and arm_error<cfg['traversal_arm_error'] and not reasons)
        if reasons: return 'failed', ','.join(reasons)
        if success: return 'success', 'original_v1_ascent_success_not_stationary'
        if self.elapsed+1e-7>=cfg['episode_seconds']: return 'timeout', 'episode_timeout'
        return 'running', ''
