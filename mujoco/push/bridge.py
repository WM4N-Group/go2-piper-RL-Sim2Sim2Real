"""MuJoCo状态→原PUSH控制器接口；观测顺序以Isaac导出契约为准。

控制器在CPU读取真实仿真状态，冻结Actor可以在CUDA推理。所有关节值均
通过名字映射，绝不假定MuJoCo、Isaac和策略动作数组的排列相同。
"""
from collections import deque
import json
from pathlib import Path
from types import SimpleNamespace as NS

import mujoco
import numpy as np
import torch

from compat import matching_ids
from model import ROOT, JOINTS, REFERENCE, KP, KD, EFFORT, SPEED, PHYSICS_DT, build_model
from controller import box_push
from controller.box_push_ik import PushArmIK
from controller.posture_safety import LowPosture
from motor import MotorCommand


def tensor(value):
    return torch.as_tensor(np.asarray(value).copy(),dtype=torch.float32).unsqueeze(0)


class Scene(dict):
    env_origins = torch.zeros((1,3))


class Robot:
    is_fixed_base = False
    num_joints = 18

    def __init__(self,sim,contract):
        self.sim = sim
        self.joint_names,self.body_names = contract['joint_names'],contract['body_names']
        self.jids = np.array([sim.model.joint(n).id for n in self.joint_names])
        self.qids,self.dids = sim.model.jnt_qposadr[self.jids],sim.model.jnt_dofadr[self.jids]
        self.bids = np.array([sim.model.body({'base':'base_link','link0':'Piper'}.get(n,n)).id for n in self.body_names])
        self.data = NS(default_joint_pos=tensor(contract['default_joint_pos']),
                       soft_joint_pos_limits=tensor(contract['soft_joint_limits']))
        self.actuators = {name:NS(stiffness=tensor([KP[JOINTS.index(name)]])) for name in self.joint_names}
        self.root_physx_view = self

    def find_bodies(self,patterns,preserve_order=False):
        return matching_ids(patterns,self.body_names,preserve_order)

    def find_joints(self,patterns,preserve_order=False):
        return matching_ids(patterns,self.joint_names,preserve_order)

    def get_jacobians(self):
        sim = self.sim
        if sim.jacobian_cache is None:
            jac = np.zeros((len(self.bids),6,24))
            for i,body in enumerate(self.bids):
                jp,jr = np.zeros((3,sim.model.nv)),np.zeros((3,sim.model.nv))
                mujoco.mj_jacBodyCom(sim.model,sim.data,jp,jr,int(body))
                jac[i,:,:6] = np.vstack((jp,jr))[:,:6]
                jac[i,:,6:] = np.vstack((jp,jr))[:,self.dids]
            sim.jacobian_cache = tensor(jac)
        return sim.jacobian_cache

    def get_gravity_compensation_forces(self):
        sim = self.sim
        gravity = sim.gravity_data
        gravity.qpos[:] = sim.data.qpos
        gravity.qvel[:] = 0.
        mujoco.mj_forward(sim.model,gravity)
        return tensor(gravity.qfrc_bias[self.dids])

    def refresh(self):
        sim,data = self.sim,self.sim.data
        rotation = data.xmat[sim.base_id].reshape(3,3)
        world_omega = rotation@data.qvel[3:6]
        self.data.joint_pos,self.data.joint_vel = tensor(data.qpos[self.qids]),tensor(data.qvel[self.dids])
        self.data.body_pos_w,self.data.body_quat_w = tensor(data.xpos[self.bids]),tensor(data.xquat[self.bids])
        self.data.root_pos_w,self.data.root_quat_w = tensor(data.qpos[:3]),tensor(data.qpos[3:7])
        self.data.root_lin_vel_w,self.data.root_ang_vel_w = tensor(data.qvel[:3]),tensor(world_omega)
        self.data.root_lin_vel_b,self.data.root_ang_vel_b = tensor(rotation.T@data.qvel[:3]),tensor(data.qvel[3:6])
        self.data.projected_gravity_b = tensor(rotation.T@np.array([0.,0.,-1.]))


class PushBridge:
    def __init__(self,seed=3701,arm_speed=None,friction=.6,delay_ms=None,source_timing=False,push_distance=.6):
        if not np.isfinite(push_distance) or push_distance<=0:
            raise ValueError('Push distance must be finite and positive, in metres')
        from timing import DEFAULT_APPROACH,ISAAC_APPROACH
        timing = ISAAC_APPROACH if source_timing else DEFAULT_APPROACH
        if arm_speed is None:arm_speed = timing.entry_gain
        contract = json.loads((ROOT/'policy/contract.json').read_text(encoding='utf-8'))
        self.model,self.spec = build_model(friction=friction)
        self.data,self.gravity_data = mujoco.MjData(self.model),mujoco.MjData(self.model)
        self.base_id,self.box_id = self.model.body('base_link').id,self.model.body('push_box').id
        self.box_qid = self.model.joint('push_box_free').qposadr[0]
        self.box_did = self.model.joint('push_box_free').dofadr[0]
        self.jids = np.array([self.model.joint(n).id for n in JOINTS])
        self.qids,self.dids = self.model.jnt_qposadr[self.jids],self.model.jnt_dofadr[self.jids]
        self.aids = np.array([next(a for a in range(self.model.nu) if self.model.actuator_trnid[a,0]==j) for j in self.jids])
        self.rng = np.random.default_rng(seed)
        self.delays = np.r_[np.repeat(self.rng.integers(0,5),12),self.rng.integers(0,5,6)]
        if delay_ms is not None:
            self.delays[:] = round(delay_ms/5)
        self.data.qpos[:3],self.data.qpos[3:7] = [-.08,0.,.33],[1.,0.,0.,0.]
        self.data.qpos[self.qids] = REFERENCE
        self.scene = Scene()
        self.robot = Robot(self,contract)
        self.scene['robot'] = self.robot
        self.scene['box'] = NS(data=NS(default_root_state=tensor([1.1,0.,.1,1.,0.,0.,0.,0.,0.,0.,0.,0.,0.])))
        self.scene.sensors = {}
        for name in ('hand',*box_push.NON_HAND_BODIES):
            sensor = NS(data=NS(force_matrix_w=torch.zeros((1,1,1,3)),contact_pos_w=torch.full((1,1,1,3),torch.nan)))
            self.scene.sensors[f'box_contact_{name}'] = sensor
            self.scene[f'box_contact_{name}'] = sensor
        self.scene.sensors['contact_forces'] = NS(data=NS(net_forces_w=torch.zeros((1,len(self.robot.bids),3))))
        self.scene['contact_forces'] = self.scene.sensors['contact_forces']
        self.num_envs,self.device,self.step_dt = 1,'cpu',.02
        self.episode_length_buf = torch.zeros(1,dtype=torch.long)
        settings = dict(contract['settings'])
        settings.update(box_size=(1.2,1.2,.2),push_approach_distance=.03,play_entry_speed=arm_speed,
                        play_alignment_rate=timing.alignment_rate_rad_s,
                        play_approach_confirmation=timing.confirmation_seconds,
                        play_face_advance_speed=timing.face_advance_m_s,
                        play_alignment_velocity=timing.alignment_joint_speed_rad_s,
                        push_leg_release_ramp_s=timing.leg_release_seconds,
                        play_smooth_approach=not source_timing,push_distance=push_distance,
                        push_geometry_root=ROOT/'robot',actions=NS(joint_pos=NS(joint_names=JOINTS,scale=.25)))
        self.cfg = NS(**settings)
        # 固定目标相对箱子初始位置前移指定距离；不能随箱子移动而重新计算。
        self.box_push_target = self.scene['box'].data.default_root_state[:,:3].clone()
        self.box_push_target[:,0] += push_distance
        self.applied_commands = np.zeros(18)
        self.targets = REFERENCE.copy()
        self.queue = deque(maxlen=5)
        self.history = None
        self.jacobian_cache = None
        self.raw_torque,self.torque = np.zeros(18),np.zeros(18)
        self.peak_torque,self.peak_speed = np.zeros(18),np.zeros(18)
        self.saturation,self.speed_exceeded = np.zeros(18,dtype=int),np.zeros(18,dtype=int)
        self.min_clearance,self.max_arm_ratio = float('inf'),0.
        self.refresh()
        path = json.loads((ROOT/'source/push_skill/runtime/mujoco/deploy/piper_push_safe_approach.json').read_text())
        self.controller = PushArmIK(self,hold_legs_until_ready=True,lock_arm_on_contact=False,
            align_hand_orientation=True,hand_pitch=1.,safe_approach_waypoints=path['waypoints'],
            safe_approach_position_tolerance=path['settle_position_tolerance_rad'],
            safe_approach_velocity_tolerance=path['settle_velocity_tolerance_rad_s'])
        self.controller.reset(None)
        self.box_push_arm_residual = torch.zeros((1,6))
        self.box_push_arm_speed_scale = torch.zeros(1)
        self.hand_cfg = self.controller.hand_cfg
        from compat import SceneEntityCfg
        self.mount_cfg = SceneEntityCfg('robot',body_ids=[self.controller.mount_id])
        self.settled = box_push.PushSettled(None,self)
        self.low_posture = LowPosture(None,self)
        from compat import SceneEntityCfg
        self.feet_cfg = SceneEntityCfg('robot',body_names='.*_foot');self.feet_cfg.resolve(self.scene)
        self.sensor_feet_cfg = SceneEntityCfg('contact_forces',body_ids=self.feet_cfg.body_ids)

    def refresh(self):
        mujoco.mj_forward(self.model,self.data)
        self.jacobian_cache = None
        self.robot.refresh()
        data = self.data
        box = self.scene['box'].data
        box.root_pos_w,box.root_quat_w = tensor(data.xpos[self.box_id]),tensor(data.xquat[self.box_id])
        box.root_lin_vel_w = tensor(data.qvel[self.box_did:self.box_did+3])
        self.forces = np.zeros((self.model.nbody,3))
        hand_forces = {name:np.zeros(3) for name in ('hand',*box_push.NON_HAND_BODIES)}
        hand_points = []
        for i in range(data.ncon):
            contact = data.contact[i]
            b1,b2 = self.model.geom_bodyid[contact.geom1],self.model.geom_bodyid[contact.geom2]
            force = np.zeros(6);mujoco.mj_contactForce(self.model,data,i,force)
            world = contact.frame.reshape(3,3).T@force[:3]
            self.forces[b1] -= world;self.forces[b2] += world
            if self.box_id not in (b1,b2):
                continue
            body,force_on_robot = (b2,world) if b1==self.box_id else (b1,-world)
            name = self.model.body(int(body)).name
            name = {'base_link':'base','Piper':'link0'}.get(name,name)
            if name in ('link6','end_effector'):
                hand_forces['hand'] += force_on_robot
                hand_points.append((np.linalg.norm(force_on_robot),contact.pos.copy()))
            elif name in hand_forces:
                hand_forces[name] += force_on_robot
        for name,force in hand_forces.items():
            sensor = self.scene.sensors[f'box_contact_{name}'].data
            sensor.force_matrix_w[:] = tensor(force).reshape(1,1,1,3)
            sensor.contact_pos_w[:] = torch.nan
        if hand_points:
            # Isaac sensor publishes one representative point; use the strongest constraint.
            self.scene.sensors['box_contact_hand'].data.contact_pos_w[:] = tensor(max(hand_points,key=lambda p:p[0])[1]).reshape(1,1,1,3)
        self.scene.sensors['contact_forces'].data.net_forces_w[:] = tensor(self.forces[self.robot.bids])

    def physics_step(self,command=None):
        values = (command or MotorCommand(self.targets,np.zeros(18),KP,KD,np.zeros(18))).array()
        if values.shape!=(5,18) or not np.isfinite(values).all():
            raise ValueError('Invalid motor command')
        if not self.queue:
            self.queue.extend([values.copy() for _ in range(5)])
        else:
            self.queue.append(values.copy())
        delayed = np.stack([self.queue[-1-int(lag)][:,i] for i,lag in enumerate(self.delays)],axis=1)
        self.raw_torque = (delayed[2]*(delayed[0]-self.data.qpos[self.qids])
                           +delayed[3]*(delayed[1]-self.data.qvel[self.dids])+delayed[4])
        self.torque = np.clip(self.raw_torque,-EFFORT,EFFORT)
        self.data.ctrl[self.aids] = self.torque
        mujoco.mj_step(self.model,self.data)
        self.refresh()
        self.peak_torque = np.maximum(self.peak_torque,abs(self.torque))
        self.peak_speed = np.maximum(self.peak_speed,abs(self.data.qvel[self.dids]))
        self.saturation += abs(self.raw_torque)>=EFFORT
        self.speed_exceeded += abs(self.data.qvel[self.dids])>SPEED
        if not np.isfinite(self.data.qpos).all():
            raise FloatingPointError('Nonfinite MuJoCo state')

    def observation(self):
        robot = self.robot.data
        velocity,ee = box_push.push_velocity_commands(self,self.hand_cfg),box_push.push_ee_commands(self,self.mount_cfg)
        terms = [robot.root_ang_vel_b[0].numpy()*.2,robot.projected_gravity_b[0].numpy(),
                 self.data.qpos[self.qids]-REFERENCE,self.data.qvel[self.dids]*.05,
                 self.applied_commands.copy(),velocity[0].numpy(),ee[0].numpy()]
        if self.history is None:
            self.history = [np.tile(term,(3,1)) for term in terms]
        else:
            for history,term in zip(self.history,terms):
                history[:-1] = history[1:];history[-1] = term
        extra = torch.cat((box_push.box_observation(self),self.box_push_pose_override_active[:,None].float(),
                           box_push.hand_contact(self,self.hand_cfg)[:,None].float()),dim=1)[0].numpy()
        observation = np.r_[np.concatenate([h.ravel() for h in self.history]),extra].astype(np.float32)
        if observation.shape!=(226,) or not np.isfinite(observation).all():
            raise ValueError('Push requires finite 226-dimensional observations')
        return observation

    def set_action(self,leg,arm):
        actions = torch.as_tensor(np.r_[leg,arm[12:]],dtype=torch.float32)[None]
        self.box_push_arm_residual[:] = .2*torch.tanh(actions[:,12:18])
        self.box_push_arm_speed_scale = torch.sigmoid(actions[:,18])
        combined = torch.zeros((1,18))
        combined[:,self.controller.leg_slots] = actions[:,:12]
        self.applied_commands = self.controller.apply(combined)[0].numpy().copy()
        self.targets = REFERENCE+.25*np.clip(self.applied_commands,-10.,10.)

    def termination(self):
        c = self.controller
        clear = c.geometry_shield.clearance(self.data.qpos[self.qids[12:]])
        self.min_clearance = min(self.min_clearance,clear)
        ratio = float(np.max(abs(self.torque[12:])/EFFORT[12:]))
        self.max_arm_ratio = max(self.max_arm_ratio,ratio)
        low = bool(self.low_posture(self,self.feet_cfg,self.sensor_feet_cfg)[0])
        flags = dict(box_settled=bool(self.settled(self,self.hand_cfg)[0]),
                     box_contact=bool(box_push.forbidden_box_contact(self)[0]),
                     invalid_hand_contact=bool(box_push.invalid_hand_contact(self,self.hand_cfg)[0]),
                     box_tipped=bool(box_push.box_tipped(self)[0]),
                     arm_body_clearance=bool(box_push.arm_body_clearance_violation(self)[0]),
                     actual_surface_clearance=bool(clear<.035),arm_effort_safety=bool(ratio>=.98),
                     low_posture=low,
                     bad_orientation=bool(float(self.robot.data.projected_gravity_b[0,2])>-np.cos(1.)),
                     base_contact=bool(np.linalg.norm(self.forces[self.base_id])>1.))
        return flags
