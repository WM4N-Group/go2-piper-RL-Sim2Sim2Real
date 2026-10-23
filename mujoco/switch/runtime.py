"""唯一物理世界、唯一延迟电机队列。技能只能产生命令，不能重置世界。"""
from dataclasses import replace
import numpy as np
import mujoco
import torch

from plugins import Plugin, ROOT


def infer(actor, observation, device):
    with torch.inference_mode():
        return actor(torch.as_tensor(observation, device=device)[None]).cpu().numpy()[0]


class Runtime:
    def __init__(self, scenario, height, distance, delay_ms, seed, device):
        self.device = device
        self.seed=seed
        self.push = Plugin('push', ['bridge', 'model', 'finish', 'balance', 'policy_loader'])
        self.nav = Plugin('nav', ['bridge', 'navigation', 'video'])
        self.climb = Plugin('climb', ['bridge', 'stop'])
        pb, pm = self.push['bridge'], self.push['model']
        with self.push.active():
            sim = pb.PushBridge(seed=seed, delay_ms=delay_ms, push_distance=distance)
        self.sim = sim
        self.scenario=scenario
        box_y = -2. if scenario == 'nav-push-climb' else (0. if scenario in ('nav-push','box-stairs') else 4.)
        self.box_y = box_y
        spec = sim.spec
        spec.body('push_box').pos = [1.1, box_y, .1]
        self.cfg = dict(self.climb['bridge'].load_contract()['configuration']['task'])
        if scenario=='box-stairs':
            from staircase import Staircase,StaircaseConfig
            self.staircase=Staircase(StaircaseConfig(push_distance=distance))
            self.staircase.build(sim)
        elif 'climb' in scenario and height > 0:
            cfg = self.cfg
            spec.worldbody.add_geom(name='platform', type=mujoco.mjtGeom.mjGEOM_BOX,
                pos=[cfg['box_front']+cfg['box_length']/2, 0, height/2],
                size=[cfg['box_length']/2, cfg['box_width']/2, height/2],
                contype=2, conaffinity=3, friction=[.6, 0, 0], condim=3,
                rgba=[.3,.4,.55,1])
        old_model = sim.model
        sim.model = spec.compile()
        # 添加静态地形不会改变自由度/机器人索引。显式检查后才复用 Push 接口。
        assert sim.model.nv == old_model.nv
        assert all(sim.model.joint(n).id == old_model.joint(n).id for n in pm.JOINTS)
        sim.data = mujoco.MjData(sim.model)
        sim.gravity_data = mujoco.MjData(sim.model)
        sim.data.qpos[:3] = [-1., box_y if scenario in ('nav-push','nav-push-climb','box-stairs') else 0., .33]
        sim.data.qpos[3:7] = [1,0,0,0]
        sim.data.qpos[sim.qids] = pm.REFERENCE
        sim.scene['box'].data.default_root_state[0,1] = box_y
        sim.box_push_target[0,1] = box_y
        sim.refresh()
        self.n = self.nav['bridge'].NavBridge(sim.model, seed, delay_ms, True, 'skills')
        # 必须沿用 Nav 独立部署的名义零位FK命令。它不是每次交接时的实测末端高度。
        # 若用沉降后的机身高度重算，会改变 Actor 的任务输入，转弯行为也随之改变。
        self.nav_ee_command = self.n.zero_arm_ee_pose()
        self.n.data = sim.data
        self.n.physics_steps = 10000  # 物理启动由唯一 Runtime 完成，不在技能重入时重置。
        self.c = self.climb['bridge'].ClimbBridge(sim.model, self.cfg, height, seed)
        self.c.data = sim.data
        self.c.forbidden = [i for i in self.c.forbidden if i != sim.box_id]
        # Climb 原QP假设只有机器人自由度；用已有支持自由箱子的同算法实现。
        self.climb['stop'].WholeBodyQP = self.push['balance'].WholeBodyQP
        self.reorder = np.array([self.climb['bridge'].JOINTS.index(n) for n in pm.JOINTS])
        self.inverse = np.argsort(self.reorder)
        self.Command = self.push['finish'].MotorCommand
        self.nav_actor = self.nav['bridge'].load_actor(device)
        with self.push.active():
            self.push_actors = self.push['policy_loader'].load_actors(ROOT/'push/policy', device)
        self.climb_actor = torch.jit.load(str(ROOT/'climb/policy/actor.pt'), map_location=device).eval()
        self.last = self.Command(pm.REFERENCE.copy(), np.zeros(18), pm.KP.copy(), pm.KD.copy(), np.zeros(18))
        self.max_tilt = 0.
        self.angle_violation = np.zeros(18)
        self.step_count = 0
        # 独立参考校准放在打开窗口之前，避免导航结束时暂停物理等待校准。
        if scenario in ('nav-push','nav-push-climb','box-stairs'):
            from push_entry import reference_stance
            self.push_reference = reference_stance(self)

    def step(self, command):
        self.sim.physics_step(command)
        self.last = command
        c, p = self.c, self.sim
        c.forces = p.forces.copy()
        c.force_history.append(c.forces.copy())
        c.applied_torque = p.torque[self.inverse].copy()
        c.raw_torque = p.raw_torque[self.inverse].copy()
        self.step_count += 1
        self.max_tilt = max(self.max_tilt, self.n.state()[3])
        q,limits=p.data.qpos[p.qids],p.model.jnt_range[p.jids]
        self.angle_violation=np.maximum(self.angle_violation,np.maximum(limits[:,0]-q,q-limits[:,1]))
        if self.n.failure():
            raise RuntimeError(self.n.failure())
        # 环境接触正常；机器人机身/臂的非预期接触单独检查。
        for i in range(p.data.ncon):
            contact = p.data.contact[i]
            a,b = map(int,p.model.geom_bodyid[[contact.geom1, contact.geom2]])
            if p.base_id in (a,b):
                f = np.zeros(6)
                mujoco.mj_contactForce(p.model,p.data,i,f)
                if np.linalg.norm(f[:3])>2.:
                    self.failure_contact=dict(time=float(p.data.time),
                        geom_names=[p.model.geom(int(g)).name for g in (contact.geom1,contact.geom2)],
                        body_names=[p.model.body(int(body)).name for body in (a,b)],
                        position=contact.pos.tolist(),force_norm_n=float(np.linalg.norm(f[:3])),
                        distance_m=float(contact.dist))
                    raise RuntimeError('base_collision')

    def nav_command(self):
        ff = np.zeros(18)
        ff[12:] = self.sim.data.qfrc_bias[self.n.dids[12:]]
        return self.Command(self.n.targets.copy(), np.zeros(18), self.n.kp.copy(), self.n.kd.copy(), ff)

    def climb_command(self, command):
        return self.Command(*(a[self.reorder].copy() for a in command.array()))

    def nav_state(self, started):
        n = self.n
        return self.nav['navigation'].NavState(n.data.time-started, n.data.qpos[:2].copy(),
            n.state()[2], n.velocity(), n.data.qpos[n.qids[12:]].copy(),
            n.data.qvel[n.dids[12:]].copy(), n.state()[3], n.ee_pose())

    def reset_nav_history(self, surface_height=0.):
        n = self.n
        n.history = None
        n.previous_action = (self.last.position-self.nav['bridge'].REFERENCE)/self.nav['bridge'].C['ACTION_SCALE']
        n.targets = self.last.position.copy()
        n.base_command[:] = 0
        n.ee_command = self.nav_ee_command.copy()
        n.ee_command[2] += surface_height

    def startup_command(self):
        return self.last

    def push_enter(self):
        p = self.sim
        with self.push.active():
            p.controller.reset(None)
        p.history = None
        p.applied_commands = (self.last.position-self.push['model'].REFERENCE)/.25
        p.targets = self.last.position.copy()
        p.episode_length_buf[:] = 0

    def climb_enter(self, item=None):
        if hasattr(self,'staircase'):
            from staircase import mapped_climb_bridge
            geometry=self.staircase.climb_geometry(self.sim,item['surface'])
            cfg=dict(self.climb['bridge'].load_contract()['configuration']['task'])
            cfg.update(box_front=geometry['front'],box_length=geometry['length'],
                       box_width=geometry['width'],rear_boundary_x=geometry['front']-1.25)
            self.cfg=cfg
            self.c=mapped_climb_bridge(self.climb['bridge'].ClimbBridge,self.sim.model,
                cfg,geometry,self.staircase,self.seed)
            self.c.data=self.sim.data
            self.c.forbidden=[i for i in self.c.forbidden if i!=self.sim.box_id]
            self.c.forces=self.sim.forces.copy()
        c = self.c
        if item is not None and 'startup_ramp_seconds' in item:
            ramp=float(item['startup_ramp_seconds'])
            if not np.isfinite(ramp) or ramp<=0:
                raise ValueError('Climb startup ramp must be positive seconds')
            c.cfg=dict(c.cfg,startup_ramp_seconds=ramp)
        if item is not None and 'approach_speed' in item:
            speed=float(item['approach_speed'])
            if not np.isfinite(speed) or not 0<speed<=.4:
                raise ValueError('Climb approach speed must be in (0,.4] m/s')
            c.cfg=dict(c.cfg,approach_speed=speed)
        c.history = None
        c.actions = (self.last.position[self.inverse]-c.reference)/self.cfg['action_scale']
        c.actions[12:] = 0
        # Nav 已确认停稳；只保留原策略的启动斜坡，无需重复等待初始站立。
        c.ready, c.release_time = True, 0.
        c.elapsed = 0.
        c.force_history.clear()
        self.stop = self.climb['stop'].StopController(c)

    def make_nav(self, item):
        module = self.nav['navigation']
        cfg = replace(module.profile_nav_config('skills'), warmup_seconds=.24)
        return module.NavSkill(item['goal'], item.get('yaw',0.), cfg, arm_zero=True)


def blend_command(command_type, old, new, fraction):
    """平滑完整电机命令；不是混合语义不同的策略动作。端点一阶导数为零。"""
    s = float(np.clip(fraction,0.,1.))
    w = s*s*(3.-2.*s)
    return command_type(*((1.-w)*a+w*b for a,b in zip(old.array(),new.array())))
