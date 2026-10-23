"""Experimental crawl-conditioned CLIMB; joint limits do not certify motor safety."""

import torch
from isaaclab.envs.mdp.actions import JointPositionAction, JointPositionActionCfg
from isaaclab.utils import configclass
from .crawl_gait import CrawlClock, limit_reference, swing_reference
from .box_climb import box_target_delta


class CrawlJointAction(JointPositionAction):
    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        terrain = env.cfg.scene.terrain.terrain_generator.sub_terrains["box"]
        if (tuple(terrain.box_height_range) != (.20, .20)
                or (terrain.approach_distance, terrain.box_length, terrain.box_width) != (.75, 1.2, 1.2)
                or terrain.approach_height != 0 or terrain.following_platform_height != 0):
            raise ValueError("Experimental crawl foot references require the fixed 20 cm box and ground approach")
        self.clock = CrawlClock(env.num_envs, env.device, cfg.transfer_s, cfg.swing_s, cfg.settle_s)
        names = ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]
        self.feet_ids = self._asset.find_bodies(names, preserve_order=True)[0]
        self.sensor_ids = env.scene["contact_forces"].find_bodies(names, preserve_order=True)[0]
        joint_names = [self._asset.joint_names[i] for i in self._joint_ids]
        arm = torch.tensor([name.startswith("joint") for name in joint_names], device=env.device)
        self.max_velocity = torch.where(arm, cfg.arm_rate, cfg.leg_rate)[None, :]
        self.max_acceleration = torch.where(arm, cfg.arm_acceleration, cfg.leg_acceleration)[None, :]
        self.reference = self._asset.data.joint_pos[:, self._joint_ids].clone()
        self.reference_velocity = torch.zeros_like(self.reference)
        self.pending = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
        self.start = torch.zeros((env.num_envs, 3), device=env.device)
        self.landing = torch.zeros_like(self.start)
        self.foot_reference = torch.zeros_like(self.start)
        self.rows = torch.arange(env.num_envs, device=env.device)

    def contacts(self):
        return self._env.scene["contact_forces"].data.net_forces_w[:, self.sensor_ids, 2] > 2.

    def feet_positions(self):
        return self._asset.data.body_pos_w[:, self.feet_ids]

    def walking(self):
        feet = self.feet_positions() - self._env.scene.env_origins[:, None, :]
        on_top = ((feet[:, :, 0] > .79) & (feet[:, :, 0] < 1.91) & (feet[:, :, 1].abs() < .56) & (feet[:, :, 2] >= .19)).all(dim=1)
        return ~((box_target_delta(self._env)[:, :2].norm(dim=1) < .15) & on_top)

    def process_actions(self, actions):
        super().process_actions(actions)
        active = self.walking()
        feet = self.feet_positions()
        selected = feet[self.rows, self.clock.leg]
        contacts = self.contacts()
        high = torch.maximum(self.start[:, 2], self.landing[:, 2]) + self.cfg.foot_clearance
        raised = selected[:, 2] >= high - self.cfg.lift_tolerance
        lift_ready = raised & ~contacts[self.rows, self.clock.leg]
        traverse_ready = raised & ((selected[:, :2] - self.landing[:, :2]).norm(dim=1) <= self.cfg.landing_xy_tolerance)
        advance = self.clock.update(contacts, active & ~self.pending, self._env.step_dt,
                                    lift_ready=lift_ready, traverse_ready=traverse_ready)
        refresh = advance | self.pending
        selected = feet[self.rows, self.clock.leg]
        self.start[refresh] = selected[refresh]
        self.landing[refresh] = selected[refresh]
        self.landing[refresh, 0] += self.cfg.stride
        # Fixed 20 cm box in this task; sole center offset matches GO2 geometry.
        local_x = self.landing[:, 0] - self._env.scene.env_origins[:, 0]
        top = (local_x > .79) & (local_x < 1.91)
        self.landing[refresh, 2] = self._env.scene.env_origins[refresh, 2] + torch.where(top[refresh], .2225, .0225)
        self.foot_reference[:] = swing_reference(self.start, self.landing, self.clock.progress, self.cfg.foot_clearance)
        self.reference[self.pending] = self._asset.data.joint_pos[:, self._joint_ids][self.pending]
        self.reference_velocity[self.pending] = 0
        self.pending[:] = False
        limits = self._asset.data.soft_joint_pos_limits[:, self._joint_ids]
        self.reference[:], self.reference_velocity[:] = limit_reference(
            self.reference, self.reference_velocity, self._processed_actions,
            limits[..., 0], limits[..., 1], self.max_velocity, self.max_acceleration, self._env.step_dt,
        )
        self._processed_actions[:] = self.reference

    def reset(self, env_ids=None):
        super().reset(env_ids)
        ids = slice(None) if env_ids is None else env_ids
        self.clock.reset(env_ids)
        self.pending[ids] = True
        self.reference_velocity[ids] = 0
        self.start[ids] = 0
        self.landing[ids] = 0
        self.foot_reference[ids] = 0


@configclass
class CrawlJointActionCfg(JointPositionActionCfg):
    class_type = CrawlJointAction
    transfer_s: float = .10
    swing_s: float = .60
    settle_s: float = .15
    stride: float = .25
    foot_clearance: float = .07
    leg_rate: float = 2.5
    arm_rate: float = .5
    leg_acceleration: float = 15.
    arm_acceleration: float = 3.
    foot_tracking_length_scale: float = .12
    lift_tolerance: float = .02
    landing_xy_tolerance: float = .03


def term(env):
    return env.action_manager.get_term("joint_pos")


def crawl_observation(env):
    action = term(env)
    clock = action.clock
    feet = action.feet_positions()[action.rows, clock.leg]
    # Appended to the unchanged 253-feature CLIMB prefix, including applied reference state.
    return torch.cat((torch.nn.functional.one_hot(clock.leg, 4).float(), clock.progress[:, None],
                      clock.stable.clamp(max=clock.settle)[:, None], clock.lifted[:, None].float(),
                      action.contacts().float(), action.walking()[:, None].float(),
                      torch.where(action.pending[:, None], 0., action.foot_reference - feet),
                      torch.where(action.pending[:, None], 0., action.reference - action._asset.data.joint_pos[:, action._joint_ids]),
                      action.reference_velocity), dim=1)


def crawl_commands(env):
    delta = box_target_delta(env)
    commands = .5 * delta
    commands[:, 0] = commands[:, 0].clamp(-.08, .12)
    commands[:, 1] = commands[:, 1].clamp(-.06, .06)
    commands[:, 2] = 0
    commands[delta[:, :2].norm(dim=1) < .15] = 0
    return commands


def gait_contact_reward(env):
    action = term(env)
    expected = torch.ones_like(action.contacts())
    swing = (action.clock.progress > 0) & (action.clock.progress < 1) & action.walking()
    expected[action.rows[swing], action.clock.leg[swing]] = False
    return (action.contacts() == expected).float().mean(dim=1)


def swing_tracking_reward(env):
    action = term(env)
    actual = action.feet_positions()[action.rows, action.clock.leg]
    distance = (actual - action.foot_reference).norm(dim=1)
    # Retain a useful learning signal when a standing foot is still far from its landing target.
    return torch.exp(-distance / action.cfg.foot_tracking_length_scale) * action.walking() * ~action.pending


def support_deficit(env):
    return (3 - term(env).contacts().sum(dim=1)).clamp_min(0).float().square()


def stance_slip(env):
    action = term(env)
    velocity = action._asset.data.body_lin_vel_w[:, action.feet_ids, :2]
    return (velocity.square().sum(dim=-1) * action.contacts()).sum(dim=1)


def impact_cost(env):
    action = term(env)
    force = env.scene["contact_forces"].data.net_forces_w[:, action.sensor_ids, 2].clamp_min(0)
    mass = action._asset.root_physx_view.get_masses().to(env.device).sum(dim=1)
    return (force / (mass[:, None] * 9.81).clamp_min(1) - .8).clamp_min(0).square().sum(dim=1)


def torque_margin_cost(env):
    robot = env.scene["robot"]
    ratio = robot.data.applied_torque.abs() / robot.data.joint_effort_limits.clamp_min(1e-6)
    return (ratio - .75).clamp_min(0).square().sum(dim=1)


def crawl_velocity_reward(env):
    return torch.exp(-(crawl_commands(env)[:, :2] - env.scene["robot"].data.root_lin_vel_b[:, :2]).square().sum(dim=1) / .2**2)
