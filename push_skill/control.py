"""v212 回放配置与原安全门禁；不包含训练代码。"""

from pathlib import Path
import os
import torch
from isaaclab.managers import TerminationTermCfg as DoneTerm
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.residual_push_actions import ResidualPushAction

SETTINGS = dict(episode_length_s=48.0, push_ik_clearance_minimum=.10,
    push_ik_joint_limit_solve=True, push_ik_orientation_weight=.5,
    push_ik_height_weight=2., push_goal_hold_pose=True,
    push_press_on_legal_contact=True, push_stop_distance=.11,
    push_press_depth=.08, push_hand_height_offset=0., push_contact_memory_s=.1,
    push_leg_release_ramp_s=.7, push_leg_contact_ramp_s=.2,
    push_forward_command_gain=2., push_geometry_minimum=.035,
    push_joint4_floor=.8, push_approach_height_gate=True, push_distance=.60)

def configure(cfg):
    for k, v in SETTINGS.items():
        if k != 'episode_length_s':
            setattr(cfg, k, v)
    cfg.push_geometry_root = Path(os.environ['PIPER_GEOMETRY_ROOT'])
    cfg.actions.joint_pos.class_type = ResidualPushAction
    cfg.actions.joint_pos.hand_pitch = 1.0
    cfg.observations.policy.enable_corruption = False
    cfg.events.box_mass = cfg.events.box_material = None
    cfg.box_size = (1.2, 1.2, 0.2)
    cfg.scene.box.spawn.size = cfg.box_size
    cfg.scene.box.init_state.pos = (*cfg.scene.box.init_state.pos[:2], 0.1)
    cfg.scene.box.spawn.mass_props.mass = 1.0
    cfg.scene.box.spawn.physics_material.static_friction = 0.15
    cfg.scene.box.spawn.physics_material.dynamic_friction = 0.15
    assert cfg.scene.robot.spawn.articulation_props.enabled_self_collisions is True
    assert cfg.terminations.arm_body_clearance.params['min_distance'] == 0.08
    assert not cfg.actions.joint_pos.lock_arm_on_contact
    cfg.terminations.actual_surface_clearance = DoneTerm(func=unsafe_clearance)
    cfg.terminations.arm_effort_safety = DoneTerm(func=unsafe_arm_effort)
    for name in ('completion', 'physical_failure'):
        term = getattr(cfg.rewards, name)
        term.params['failure_terms'] = (*term.params['failure_terms'], 'actual_surface_clearance', 'arm_effort_safety')

def physical_sample(env):
    # Called after physics by termination manager, before reset; no stale IK measurement.
    stamp=env.common_step_counter
    if getattr(env,'_v195_sample_stamp',None)==stamp:return env._v195_sample
    c=env.action_manager.get_term('joint_pos').controller;r=env.scene['robot']
    q=r.data.joint_pos[:,c.joint_ids].detach().cpu().numpy()
    clearance=torch.tensor([c.geometry_shield.clearance(row) for row in q],device=env.device)
    ratio=r.data.applied_torque.abs()/r.data.joint_effort_limits.clamp_min(1e-6)
    feet_ids=[i for i,n in enumerate(env.scene['contact_forces'].body_names) if n.endswith('_foot')]
    forces=env.scene['contact_forces'].data.net_forces_w[:,feet_ids,:]
    result=dict(clearance=clearance,arm_ratio=ratio[:,c.joint_ids].amax(1),ratio=ratio.amax(1),support=(forces[:,:,2]>2.).sum(1),vz=r.data.root_lin_vel_w[:,2].abs(),force=forces.norm(dim=-1).amax(1),force_sum=forces.sum(1).norm(dim=-1))
    if not hasattr(env,'_v198_effort_violation'):env._v198_effort_violation=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
    env._v198_effort_violation &= env.episode_length_buf>1
    env._v198_effort_violation |= result['arm_ratio']>=.98
    env._v195_sample_stamp=stamp;env._v195_sample=result
    monitor=getattr(env,'_v195_monitor',None)
    if monitor is not None:monitor.sample(result)
    return result

def unsafe_clearance(env):return physical_sample(env)['clearance']<.035

def unsafe_arm_effort(env):return physical_sample(env)['arm_ratio']>=.98
