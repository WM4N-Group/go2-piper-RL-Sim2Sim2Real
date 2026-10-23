"""独立Push场景：原USD质量/惯量/碰撞，1kg自由箱子与受限motor。"""
from pathlib import Path
from types import SimpleNamespace
import json
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
ROOT = Path(__file__).resolve().parent
JOINTS = [f'{leg}_{joint}_joint' for leg in ('FR','FL','RR','RL') for joint in ('hip','thigh','calf')]+[f'joint{i}' for i in range(1,7)]
EFFORT = np.array([23.7,23.7,45.43]*4+[20.,20.,15.,7.,5.,5.])
SPEED = np.array([30.1,30.1,15.7]*4+[3.]*6)
KP = np.array([30.]*12+[50.,50.,80.,30.,30.,20.])
KD = np.array([.6]*12+[3.,2.,3.,3.,2.5,1.])
REFERENCE = np.array([-.1,.8,-1.5,.1,.8,-1.5,-.1,1.,-1.5,.1,1.,-1.5]+[0.]*6)
PHYSICS_DT = .005

def build_model(friction=.6, added_mass=0., control_profile='isaac'):
    """将公共USD对应profile应用到独立XML，不更改源USD/XML。"""
    directory = ROOT/'robot'
    actuator_profile = SimpleNamespace(passive_damping=np.zeros(18),frictionloss=.01)
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
    # 删除旧简化碰撞，替换为公共USD的形状；保留机器人自碰撞。
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
                       quat=shape['quaternion'], contype=1, conaffinity=3, group=3,
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
    # Push需要真实机器人自碰撞；自由箱子参与地面和机器人接触。
    box = world.add_body(name='push_box',pos=[1.10,0.,.1])
    box.add_freejoint(name='push_box_free')
    box.add_geom(name='push_box_geom',type=mujoco.mjtGeom.mjGEOM_BOX,size=[.6,.6,.1],
                 mass=1.,contype=2,conaffinity=3,condim=3,friction=[.15,0.,0.],
                 priority=2,rgba=[.65,.3,.15,1.])
    # 显式pair保留PhysX的min摩擦组合规则，MuJoCo默认使用max。
    ground = spec.geom('ground')
    ground.conaffinity = 3
    for geom in list(spec.geoms):
        if geom.name == 'push_box_geom' or not (geom.contype or geom.conaffinity):
            continue
        pair = spec.add_pair(geomname1='push_box_geom',geomname2=geom.name,condim=3)
        pair.friction = [.15,.15,0.,0.,0.]
    return spec.compile(), spec

