"""Explicit v96 runtime contract and control-step training diagnostics."""
from pathlib import Path
import os
import json
import math
import torch

ROOT = Path(os.environ["PIPER_HANDOFF_ROOT"])
SETTINGS = dict(
    episode_length_s=24.0, push_ik_clearance_minimum=.10,
    push_ik_joint_limit_solve=True, push_ik_orientation_weight=.5,
    push_ik_height_weight=2.0, push_goal_hold_pose=True,
    push_press_on_legal_contact=True, push_stop_distance=.11,
    push_press_depth=.08, push_hand_height_offset=0.0,
    push_contact_memory_s=.1, push_leg_release_ramp_s=.7,
    push_leg_contact_ramp_s=.2, push_forward_command_gain=2.0,
    push_geometry_minimum=.035, push_joint4_floor=.8,
    push_approach_height_gate=True, push_distance=.60,
)

def configure(cfg, args):
    assert args.task == 'GO2-PIPER-Box-Push-Tracking'
    assert args.push_action_sampling == 'active'
    for key, value in SETTINGS.items():
        setattr(cfg, key, value)
    cfg.push_geometry_root = Path(os.environ["PIPER_GEOMETRY_ROOT"])
    cfg.actions.joint_pos.hand_pitch = 1.0
    cfg.observations.policy.enable_corruption = False
    cfg.events.box_mass = None
    cfg.events.box_material = None
    cfg.box_size = (1.2,1.2,.20)
    cfg.scene.box.spawn.size = cfg.box_size
    cfg.scene.box.init_state.pos = (*cfg.scene.box.init_state.pos[:2],.1)
    cfg.scene.box.spawn.mass_props.mass = 5.0
    cfg.scene.box.spawn.physics_material.static_friction = .4
    cfg.scene.box.spawn.physics_material.dynamic_friction = .4
    assert cfg.scene.robot.spawn.articulation_props.enabled_self_collisions is True
    assert cfg.terminations.arm_body_clearance.params['min_distance'] == .08
    assert not cfg.actions.joint_pos.lock_arm_on_contact

class Monitor:
    def __init__(self, env, log_dir):
        self.env = env
        self.path = Path(log_dir)/'matched-training-monitor.json'
        self.controller = env.action_manager.get_term('joint_pos').controller
        assert self.controller.geometry_shield is not None
        assert self.controller.geometry_shield.minimum == .035
        assert self.controller.approach_height_gate
        self.steps = self.active = self.observed = self.below = self.saturated = 0
        self.minimum = math.inf
        self.max_torque = 0.0
        self.completed = False
        self.original = self.controller.apply
        self.controller.apply = self.apply
        self.write()

    def apply(self, actions):
        result = self.original(actions)
        c = self.controller
        assert torch.isfinite(result).all(), 'Nonfinite commands'
        assert torch.isfinite(c.geometry_clearance).all(), 'Nonfinite geometry'
        self.steps += 1
        self.observed += self.env.num_envs
        self.active += int(c.motion_ready.sum().item())
        self.below += int((c.geometry_clearance < .035).sum().item())
        self.minimum = min(self.minimum,float(c.geometry_clearance.min().item()))
        robot = self.env.scene['robot']
        ratio = robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)
        assert torch.isfinite(ratio).all(), 'Nonfinite torque'
        self.max_torque = max(self.max_torque,float(ratio.max().item()))
        self.saturated += int((ratio >= .999).any(dim=1).sum().item())
        if self.steps % 64 == 0:
            self.write()
        return result

    def write(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        payload = dict(scope='Training telemetry only; pre-physics control-step torque including first call; no substep safety claim', completed=self.completed, control_calls=self.steps, num_envs=self.env.num_envs, active_env_steps=self.active, geometry_observed_env_steps=self.observed, geometry_below_35mm_env_steps=self.below, min_geometry_m=self.minimum if math.isfinite(self.minimum) else None, max_torque_ratio=self.max_torque, saturation_env_steps=self.saturated, settings=SETTINGS, native_self_collision=True, noise=False, original_rewards=True)
        tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
        tmp.replace(self.path)

    def finish(self):
        self.completed=True
        self.write()


def install_monitor(env, log_dir):
    return Monitor(env, log_dir)
