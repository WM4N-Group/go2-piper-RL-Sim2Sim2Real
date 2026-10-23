"""A single fixed box, a complete GO2-PIPER, and no old CLIMB controller hooks."""

import re

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.envs import DirectRLEnv
from isaaclab.sensors import ContactSensor

from .task_parameters import FOOT_NAMES, HISTORY, JOINT_NAMES, PROPRIO
from .mdp import actions, observations, rewards, terminations, resets, randomization


class ClimbSkillEnv(DirectRLEnv):
    def __init__(self, cfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode=render_mode, **kwargs)
        self.task = cfg.task
        # 不能假定USD内部关节顺序：按FL/FR/RL/RR各hip/thigh/calf，再joint1..6显式查索引。
        self.joint_ids, names = self.robot.find_joints(list(JOINT_NAMES), preserve_order=True)
        if tuple(names) != JOINT_NAMES or self.robot.num_joints != 18:
            raise ValueError(f"Unexpected robot joint contract: {names}")
        self.foot_ids, names = self.robot.find_bodies(list(FOOT_NAMES), preserve_order=True)
        if tuple(names) != FOOT_NAMES:
            raise ValueError(f"Unexpected foot contract: {names}")
        self.contact_feet, _ = self.contact.find_bodies(list(FOOT_NAMES), preserve_order=True)
        self.nonfeet = [i for i, n in enumerate(self.contact.body_names) if n not in FOOT_NAMES]
        # All non-leg links (including the complete arm) must not touch the environment.
        self.forbidden = [i for i, n in enumerate(self.contact.body_names)
                          if not re.fullmatch(r"(?:FL|FR|RL|RR)_(?:foot|hip|thigh|calf)", n)]
        if not self.forbidden:
            raise ValueError("No base/arm contact bodies resolved")
        z = lambda *shape: torch.zeros(*shape, device=self.device)
        self.actions = z(self.num_envs, 18)
        self.previous_actions = self.actions.clone()
        self.targets = self.robot.data.default_joint_pos[:, self.joint_ids].clone()
        self.reference = self.targets.clone()
        self.previous_targets = self.targets.clone()
        self.previous_previous_targets = self.targets.clone()
        self.arm_gravity_torque = torch.zeros(self.num_envs, 6, device=self.device)
        self.history = z(self.num_envs, HISTORY, PROPRIO)
        self.fresh = torch.ones(self.num_envs, device=self.device, dtype=torch.bool)
        self.history_step = -1
        self.hold = z(self.num_envs)  # 安全箱顶几何/近期承重/朝向连续确认计时，不要求静止。
        self.top_contact_age = torch.full((self.num_envs, 4), float("inf"), device=self.device)
        self.ever_top_support = torch.zeros(self.num_envs, 4, dtype=torch.bool, device=self.device)
        self.max_supported_feet = z(self.num_envs)
        self.max_root_x = z(self.num_envs)
        self.arm_bad_time = z(self.num_envs)
        self.previous_torques = z(self.num_envs, 18)
        self.previous_distance = z(self.num_envs)
        self.episode_return = z(self.num_envs)
        self.levels = torch.zeros(self.num_envs, device=self.device, dtype=torch.long)
        self.success_streak = self.levels.clone()
        self.failure_streak = self.levels.clone()
        self.heights = torch.full((self.num_envs,), self.task.box_height, device=self.device)
        self.privileged = z(self.num_envs, 29)
        # 12×11=132个高度点，机身局部x=-0.45..1.2m、y=-0.75..0.75m，再随yaw转到世界XY。
        self.sample_xy = torch.cartesian_prod(torch.linspace(-0.45, 1.2, 12, device=self.device),
                                              torch.linspace(-0.75, 0.75, 11, device=self.device))
        self.success = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.failure = self.success.clone()
        self.startup_elapsed = z(self.num_envs)
        self.startup_stable_time = z(self.num_envs)
        self.startup_ready = torch.zeros(self.num_envs, device=self.device, dtype=torch.bool)
        self.startup_release_time = torch.full((self.num_envs,), float("inf"), device=self.device)
        self.reward_terms = {}
        self.peak_arm_error = z(self.num_envs)
        self.peak_contact_force = z(self.num_envs)
        self._randomize_physics()

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot)
        self.box = RigidObject(self.cfg.box)
        self.contact = ContactSensor(self.cfg.contact)
        self.scene.articulations["robot"] = self.robot
        self.scene.rigid_objects["box"] = self.box
        self.scene.sensors["contact"] = self.contact
        ground = sim_utils.GroundPlaneCfg(physics_material=self.cfg.sim.physics_material)
        ground.func("/World/ground", ground)
        self.scene.clone_environments(copy_from_source=False)
        self.scene.filter_collisions(global_prim_paths=["/World/ground"])
        light = sim_utils.DomeLightCfg(intensity=2000., color=(0.75, 0.75, 0.75))
        light.func("/World/Light", light)

    def _randomize_physics(self):
        return randomization.randomize_physics(self)

    def _pre_physics_step(self, action_tensor):
        return actions.pre_physics_step(self, action_tensor)

    def _apply_action(self):
        self.robot.set_joint_position_target(self.targets, joint_ids=self.joint_ids)
        if self.task.arm_gravity_compensation:
            # Full floating-base gravity compensation is [base wrench (6), joints].
            # The deprecated joint-only getter returned near-zero arm values in
            # this floating-base asset's runtime check; use the full compensation.
            # 浮动基座返回6维基座wrench+18维关节补偿；只取臂6轴，绝不给机身施加悬浮外力。
            gravity = self.robot.root_physx_view.get_gravity_compensation_forces()
            if gravity.shape != (self.num_envs, self.robot.num_joints + 6):
                raise RuntimeError(f"Unexpected floating-base gravity-force shape: {gravity.shape}")
            # Apply only arm torques. The base wrench and all leg entries remain unused.
            self.arm_gravity_torque.copy_(gravity[:, 6:][:, self.joint_ids[12:]])
        else:
            self.arm_gravity_torque.zero_()
        # Called every physics step. DelayedPD delays this effort command and
        # clips PD + feedforward to the original actuator effort limits.
        self.robot.set_joint_effort_target(self.arm_gravity_torque, joint_ids=self.joint_ids[12:])

    def _kinematics(self):
        return observations.kinematics(self)

    def _proprio_scan(self):
        return observations.proprio_scan(self)

    def _build_observation(self):
        return observations.build_observation(self)

    def _get_observations(self):
        return observations.get_observations(self)

    def _get_dones(self):
        return terminations.get_dones(self)

    def _get_rewards(self):
        return rewards.get_rewards(self)

    def _reset_idx(self, env_ids):
        return resets.reset_idx(self, env_ids)
