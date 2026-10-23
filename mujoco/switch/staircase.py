"""箱子作为活动踏步的场景：低地0m、自由箱顶0.2m、高地0.4m。

只提供地形、已知地图查询和任务验收，不改Actor或实际机器人状态。
尺寸集中在StaircaseConfig；原单技能和其他切换场景不依赖本模块。
"""
from dataclasses import asdict, dataclass
import mujoco
import numpy as np


@dataclass(frozen=True)
class StaircaseConfig:
    box_length: float = 2.4
    box_width: float = 1.2
    box_height: float = .2
    box_initial_front: float = .5
    push_distance: float = .6
    upper_height: float = .4
    upper_length: float = 5.
    upper_width: float = 4.
    docking_gap: float = .005

    @property
    def upper_front(self):
        return self.box_initial_front+self.box_length+self.push_distance

    @property
    def initial_center(self):
        return self.box_initial_front+self.box_length/2


class Staircase:
    def __init__(self, config=None):
        self.config=config or StaircaseConfig()
        self.dock_age=0.

    def build(self, sim):
        """只在创建世界时设置尺寸/初始位置；之后箱子保留自由关节。"""
        c,spec=self.config,sim.spec
        spec.body('push_box').pos=[c.initial_center,0.,c.box_height/2]
        spec.geom('push_box_geom').size=[c.box_length/2,c.box_width/2,c.box_height/2]
        # 专用地图组只包含地面、箱子、高地，射线不命中机器人或可视化mesh。
        # 组1默认可见；将可能使用组1的机器人视觉几何移到视觉组2。
        for geom in spec.geoms:
            if geom.name not in ('ground','push_box_geom') and geom.group==1:
                geom.group=2
        spec.geom('push_box_geom').group=1
        spec.geom('ground').group=1
        spec.worldbody.add_geom(name='upper_ground',type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[c.upper_front+c.upper_length/2,0.,c.upper_height/2],
            size=[c.upper_length/2,c.upper_width/2,c.upper_height/2],
            contype=2,conaffinity=3,condim=3,friction=[.6,0.,0.],group=1,
            rgba=[.28,.42,.55,1.])
        pair=spec.add_pair(geomname1='push_box_geom',geomname2='upper_ground',condim=3)
        pair.friction=[.15,.15,0.,0.,0.]
        sim.cfg.box_size=(c.box_length,c.box_width,c.box_height)
        sim.scene['box'].data.default_root_state[0,:3]=sim.box_push_target.new_tensor(
            [c.initial_center,0.,c.box_height/2])
        sim.box_push_target[0,:3]=sim.box_push_target.new_tensor(
            [c.initial_center+c.push_distance,0.,c.box_height/2])

    def height_at(self, sim, x, y):
        """已知几何地图+当前箱姿态，向下查询表面；不把假单台阶输入Actor。"""
        result=np.empty(np.shape(x))
        group=np.array([0,1,0,0,0,0],dtype=np.uint8)
        geom=np.zeros(1,dtype=np.int32)
        for i,(px,py) in enumerate(zip(np.ravel(x),np.ravel(y))):
            distance=mujoco.mj_ray(sim.model,sim.data,np.array([px,py,3.]),
                np.array([0.,0.,-1.]),group,1,-1,geom)
            if distance<0:
                raise RuntimeError('known_map_has_no_surface')
            result.flat[i]=3.-distance
        return result

    def dock_metrics(self, sim):
        c,d=self.config,sim.data
        rotation=d.xmat[sim.box_id].reshape(3,3)
        extent=np.abs(rotation)@np.array([c.box_length/2,c.box_width/2,c.box_height/2])
        gap=c.upper_front-(d.xpos[sim.box_id,0]+extent[0])
        box_geom=sim.model.geom('push_box_geom').id
        wall_geom=sim.model.geom('upper_ground').id
        contact=False
        for i in range(d.ncon):
            item=d.contact[i]
            if {int(item.geom1),int(item.geom2)}=={box_geom,wall_geom} and item.dist<=.002:
                contact=True
        yaw=float(np.arctan2(rotation[1,0],rotation[0,0]))
        return dict(gap_m=float(gap),wall_contact=contact,box_yaw_rad=yaw,
            box_position=d.xpos[sim.box_id].tolist(),
            box_speed_m_s=float(np.linalg.norm(d.qvel[sim.box_did:sim.box_did+3])))

    def push_ready(self, sim, original_settled):
        m=self.dock_metrics(sim)
        good=(original_settled and m['wall_contact'] and -.005<=m['gap_m']<=self.config.docking_gap
              and abs(m['box_yaw_rad'])<np.deg2rad(5.) and m['box_speed_m_s']<.08)
        self.dock_age=self.dock_age+.02 if good else 0.
        return self.dock_age>=.3

    def climb_geometry(self, sim, surface):
        c=self.config
        if surface=='box':
            rotation=sim.data.xmat[sim.box_id].reshape(3,3)
            yaw=abs(np.arctan2(rotation[1,0],rotation[0,0]))
            if yaw>np.deg2rad(5.):
                raise RuntimeError('climb_box_not_aligned')
            return dict(front=float(sim.data.xpos[sim.box_id,0]-c.box_length/2),
                        length=c.box_length,width=c.box_width,base_height=0.,top=c.box_height)
        return dict(front=c.upper_front,length=c.upper_length,width=c.upper_width,
                    base_height=c.box_height,top=c.upper_height)

    def report(self, sim):
        return dict(configuration=asdict(self.config),upper_front=self.config.upper_front,
            box_mass_kg=float(sim.model.body_mass[sim.box_id]),box_fixed=False,
            map_source='known geometry and exact current box pose; no robot ray hits',
            final_docking=self.dock_metrics(sim))


def mapped_climb_bridge(base_class, model, cfg, geometry, scene, seed):
    """世界高度用于接触/停止；Actor高度项始终是本次相对抬升20cm。"""
    class MappedClimb(base_class):
        def observation(self):
            world_top=self.height
            try:
                self.height=geometry['top']-geometry['base_height']
                observation=super().observation()
            finally:
                self.height=world_top
            sx,sy=np.meshgrid(np.linspace(-.45,1.2,12),np.linspace(-.75,.75,11),indexing='ij')
            yaw=self.state()[2]
            x=self.data.qpos[0]+np.cos(yaw)*sx.ravel()-np.sin(yaw)*sy.ravel()
            y=self.data.qpos[1]+np.sin(yaw)*sx.ravel()+np.cos(yaw)*sy.ravel()
            heights=scene.height_at(self,x,y)
            observation[69:201]=np.clip(self.data.qpos[2]-.3-heights,-1.,1.)
            return observation

        def status(self):
            state,reason=super().status()
            if self.data.qpos[2]<geometry['base_height']+.16:
                return 'failed','low_posture_relative_to_start_surface'
            return state,reason

    return MappedClimb(model,cfg,geometry['top'],seed)
