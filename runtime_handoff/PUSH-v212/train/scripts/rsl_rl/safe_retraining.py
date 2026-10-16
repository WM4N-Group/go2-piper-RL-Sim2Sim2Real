"""v117 arm-only training: frozen original leg features and outputs, post-face residual."""
from pathlib import Path
import os
import hashlib
import json
import math
import torch
from isaaclab.managers import RewardTermCfg as RewTerm, SceneEntityCfg
from isaaclab.utils.math import quat_apply_inverse, yaw_quat
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.residual_push_actions import ResidualPushAction

ROOT = Path(os.environ["PIPER_HANDOFF_ROOT"])
SETTINGS = dict(episode_length_s=48.0, push_ik_clearance_minimum=.10,
    push_ik_joint_limit_solve=True, push_ik_orientation_weight=.5,
    push_ik_height_weight=2., push_goal_hold_pose=True,
    push_press_on_legal_contact=True, push_stop_distance=.11,
    push_press_depth=.08, push_hand_height_offset=0., push_contact_memory_s=.1,
    push_leg_release_ramp_s=.7, push_leg_contact_ramp_s=.2,
    push_forward_command_gain=2., push_geometry_minimum=.035,
    push_joint4_floor=.8, push_approach_height_gate=True, push_distance=.60)
def legal_progress(env, asset_cfg):
    # Original measured, goal-directed box progress with original legal contact.
    return box_push.push_progress_reward(env, asset_cfg) * (~box_push.push_control_at_goal(env)).float()

def arm_load_cost(env):
    c = env.action_manager.get_term('joint_pos').controller
    r = env.scene['robot']
    ratio = r.data.applied_torque[:, c.joint_ids].abs() / r.data.joint_effort_limits[:, c.joint_ids].clamp_min(1e-6)
    return ((ratio - .65)/.33).clamp(0., 2.).square().amax(1)

def clearance_cost(env):
    c = env.action_manager.get_term('joint_pos').controller
    return ((.055-physical_sample(env)["clearance"])/.020).clamp(0., 3.).square()

def catchup_cost(env):
    c = env.action_manager.get_term('joint_pos').controller
    robot, box = env.scene['robot'], env.scene['box']
    rot = yaw_quat(robot.data.root_quat_w)
    gap = quat_apply_inverse(rot, box_push.front_face(env)-robot.data.root_pos_w)[:, 0]
    closing = quat_apply_inverse(rot, robot.data.root_lin_vel_w-box.data.root_lin_vel_w)[:, 0]
    return closing.clamp_min(0.).square() * (gap < .48).float() * c.approach_face_ready.float()

def active_time(env):
    return torch.ones(env.num_envs, device=env.device)  # count waiting during approach too

def configure(cfg, args, *, training=True):
    for k,v in SETTINGS.items():
        if k != 'episode_length_s' or training:
            setattr(cfg,k,v)
    cfg.push_geometry_root = Path(os.environ["PIPER_GEOMETRY_ROOT"])
    cfg.actions.joint_pos.class_type = ResidualPushAction
    cfg.actions.joint_pos.hand_pitch = 1.0
    cfg.observations.policy.enable_corruption = False
    cfg.events.box_mass = cfg.events.box_material = None
    cfg.box_size = (1.2,1.2,.20)
    cfg.scene.box.spawn.size = cfg.box_size
    cfg.scene.box.init_state.pos = (*cfg.scene.box.init_state.pos[:2], .1)
    cfg.scene.box.spawn.mass_props.mass = 1.
    cfg.scene.box.spawn.physics_material.static_friction = .15
    cfg.scene.box.spawn.physics_material.dynamic_friction = .15
    assert cfg.scene.robot.spawn.articulation_props.enabled_self_collisions is True
    assert cfg.terminations.arm_body_clearance.params['min_distance'] == .08
    assert not cfg.actions.joint_pos.lock_arm_on_contact
    if training:
        # Keep original failure/completion rewards and every termination unchanged.
        cfg.rewards.track_lin_vel_xy_exp.weight = 1.
        cfg.rewards.end_effector_position_tracking_exp.weight = 0.  # remove reward for stationary partial approach
        cfg.rewards.hand_contact.weight = 0.
        cfg.rewards.box_progress = RewTerm(func=legal_progress, weight=40., params={'asset_cfg':SceneEntityCfg('robot',body_names='end_effector')})
        cfg.rewards.safe_arm_load = RewTerm(func=arm_load_cost, weight=-4.)
        cfg.rewards.safe_clearance = RewTerm(func=clearance_cost, weight=-10.)
        cfg.rewards.safe_catchup = RewTerm(func=catchup_cost, weight=-5.)
        cfg.rewards.safe_active_time = RewTerm(func=active_time, weight=-.1)

# v195: this source is part of the runtime contract, including the frozen leg hook.
from isaaclab.managers import TerminationTermCfg as DoneTerm
import runpy
LEG_CHECKPOINT=Path(os.environ["PIPER_LEG_CHECKPOINT"])
LEG_SHA='b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721'

def install_frozen_legs(actor):
    assert hashlib.sha256(LEG_CHECKPOINT.read_bytes()).hexdigest()==LEG_SHA
    loader=runpy.run_path(str(Path(__file__).with_name('initialization.py')))['actor_from_state_dict']
    mlp=getattr(actor,'mlp',actor)
    assert not getattr(mlp,'_v195_frozen_leg_hook',False)
    device=next(mlp.parameters()).device
    frozen=loader(torch.load(LEG_CHECKPOINT,map_location='cpu',weights_only=False)['actor_state_dict'],device=device)
    frozen.requires_grad_(False)
    def output_hook(module,inputs,output):
        with torch.no_grad(): legs=frozen(inputs[0])
        return torch.cat((legs,output[:,12:]),dim=-1)
    mlp.register_forward_hook(output_hook)
    mlp._v195_frozen_leg_hook=True

def initialize_models(actor,critic,*,checkpoint_path=None,**kwargs):
    assert Path(checkpoint_path)==LEG_CHECKPOINT
    source=torch.load(LEG_CHECKPOINT,map_location='cpu',weights_only=False)['actor_state_dict']
    target=actor.state_dict()
    last=max(int(k.split('.')[1]) for k in source if k.startswith('mlp.') and k.endswith('.weight'))
    for k,v in target.items():
        if k.startswith('distribution.'):continue
        if k in (f'mlp.{last}.weight',f'mlp.{last}.bias'):
            assert v.shape[0]==19 and source[k].shape[0]==12
            v.zero_();v[:12].copy_(source[k].to(v.device))
        else:v.copy_(source[k].to(v.device))
    target[f'mlp.{last}.bias'][18] = -1.38629436112  # sigmoid=0.2; policy can learn0..1 of original speed
    actor.load_state_dict(target)
    install_frozen_legs(actor)
    # Hidden layers now belong to the arm path only. Frozen leg outputs bypass them.
    for param in actor.parameters():param.requires_grad_(True)
    with torch.no_grad():
        actor.distribution.log_std_param[:12].fill_(math.log(.0001))
        actor.distribution.log_std_param[12:18].fill_(math.log(.10))
        actor.distribution.log_std_param[18:].fill_(math.log(.30))
    def arm_std_only(g):
        g=g.clone();g[:12]=0.;return g
    actor.distribution.log_std_param.register_hook(arm_std_only)
    return dict(contract='v195 frozen independent legs, trainable arm features+head;full approach',source_sha256=LEG_SHA,critic='fresh',optimizer='fresh')

def verify_physics(env,directory):
    view=env.scene['box'].root_physx_view
    masses=view.get_masses().flatten().tolist();materials=view.get_material_properties().tolist()
    valid=all(abs(x-1.)<1e-6 for x in masses) and all(abs(m[0]-.15)<1e-6 and abs(m[1]-.15)<1e-6 and m[2]==0. for row in materials for m in row)
    d=dict(valid=valid,box_mass_per_env=masses,box_material_per_env=materials,box_size=env.cfg.box_size,push_distance=env.cfg.push_distance,native_selfcollision=env.cfg.scene.robot.spawn.articulation_props.enabled_self_collisions)
    p=Path(directory);p.mkdir(parents=True,exist_ok=True);(p/'startup-physics.json').write_text(json.dumps(d,indent=2)+'\n')
    assert valid and d['native_selfcollision'] and abs(env.cfg.push_distance-.6)<1e-6,'Actual physics contract mismatch'
    return d

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

def unsafe_training_completion(env):
    # An unsafe rollout never earns completion credit; only training postpones reset.
    physical_sample(env)
    return env._v198_effort_violation & env.termination_manager.get_term('box_settled')

def safety_failure_cost(env):return (unsafe_clearance(env)|unsafe_arm_effort(env)).float()

def approach_progress(env):
    c=env.action_manager.get_term('joint_pos').controller
    now=c.safe_approach_index.float()
    previous=getattr(env,'_v195_previous_index',torch.zeros_like(now))
    gain=(now-previous).clamp_min(0.)
    gain=torch.where(env.episode_length_buf<=1,torch.zeros_like(gain),gain)
    env._v195_previous_index=now.clone()
    return gain/env.step_dt

_configure_base=configure

def configure(cfg,args,*,training=True):
    _configure_base(cfg,args,training=training)
    cfg.terminations.actual_surface_clearance=DoneTerm(func=unsafe_clearance)
    cfg.terminations.arm_effort_safety=DoneTerm(func=unsafe_training_completion if training else unsafe_arm_effort)
    for name in ('completion','physical_failure'):
        term=getattr(cfg.rewards,name)
        term.params['failure_terms']=(*term.params['failure_terms'],'actual_surface_clearance','arm_effort_safety')
    if training:
        cfg.rewards.full_safety_failure=RewTerm(func=safety_failure_cost,weight=-250.)
        cfg.rewards.approach_progress=RewTerm(func=approach_progress,weight=.2)

class Monitor:
    def __init__(self,env,log_dir):
        self.env=env;self.path=Path(log_dir)/'safe-training-monitor.json'
        verify_physics(env,log_dir)
        self.steps=self.active=self.below=self.saturated=self.airborne=self.under3=0
        self.max_episode_step=self.max_approach_index=self.post_face_steps=0
        self.minimum=math.inf;self.max_torque=self.max_vz=self.max_force=self.max_sum=0.
        self.completed=False;env._v195_monitor=self
        self.episodes=self.safe_successes=self.native_goal_reaches=self.unsafe_episodes=0
        self.original_step=env.step;env.step=self.step
        # Initial state also counted, even if actuator target history is not yet initialized.
        env._v195_sample_stamp=None
        self.failures=[]
        self.sample_initial=physical_sample(env)
        self.write()
    def step(self,actions):
        result=self.original_step(actions)
        done=self.env.reset_buf.bool()
        at_goal=self.env.termination_manager.get_term('box_settled')
        good=at_goal.clone()
        for name in self.env.termination_manager.active_terms:
            if name not in ('box_settled','time_out'):good &= ~self.env.termination_manager.get_term(name)
        good &= ~self.env._v198_effort_violation
        self.episodes+=int(done.sum())
        self.native_goal_reaches+=int((done & at_goal).sum())
        self.safe_successes+=int((done & good).sum())
        self.unsafe_episodes+=int((done & self.env._v198_effort_violation).sum())
        return result
    def sample(self,v):
        self.steps+=1
        c=self.env.action_manager.get_term('joint_pos').controller
        self.active+=int((~c.goal_hold_active & ~c.locked).sum().item())
        self.max_episode_step=max(self.max_episode_step,int(self.env.episode_length_buf.max()))
        self.max_approach_index=max(self.max_approach_index,int(c.safe_approach_index.max()))
        self.post_face_steps+=int(c.approach_face_ready.sum())
        self.below+=int((v['clearance']<.035).sum().item())
        self.minimum=min(self.minimum,float(v['clearance'].min().item()))
        self.max_torque=max(self.max_torque,float(v['ratio'].max().item()))
        self.saturated+=int((v['ratio']>=.999).sum().item())
        self.airborne+=int((v['support']==0).sum().item());self.under3+=int((v['support']<3).sum().item())
        self.max_vz=max(self.max_vz,float(v['vz'].max().item()))
        self.max_force=max(self.max_force,float(v['force'].max().item()));self.max_sum=max(self.max_sum,float(v['force_sum'].max().item()))
        if len(self.failures)<32:
            r=self.env.scene['robot']
            for i in torch.where((v['arm_ratio']>=.98)|(v['clearance']<.035))[0].tolist():
                if len(self.failures)>=32:break
                self.failures.append(dict(env_id=i,episode_step=int(self.env.episode_length_buf[i]),clearance=float(v['clearance'][i]),arm_ratio=float(v['arm_ratio'][i]),arm_q=r.data.joint_pos[i,c.joint_ids].tolist(),arm_qd=r.data.joint_vel[i,c.joint_ids].tolist(),arm_target=r.data.joint_pos_target[i,c.joint_ids].tolist(),arm_torque=r.data.applied_torque[i,c.joint_ids].tolist(),approach_index=int(c.safe_approach_index[i])))
        if self.steps%64==0:self.write()
    def write(self):
        d=dict(scope='All environments,post-physics20ms control samples incl initial;not substep acceptance',completed=self.completed,control_calls=self.steps,num_envs=self.env.num_envs,active_env_steps=self.active,geometry_below_35mm_env_steps=self.below,min_geometry_m=self.minimum if math.isfinite(self.minimum) else None,max_torque_ratio=self.max_torque,saturation_env_steps=self.saturated,airborne_env_steps=self.airborne,under_three_support_env_steps=self.under3,max_abs_vertical_velocity=self.max_vz,max_single_foot_resultant_N=self.max_force,max_sum_foot_force_norm_N=self.max_sum,full_task_distance_m=.6,mass_kg=1.,friction=.15,contract='v202;226->19 frozen legs+arm residual+speed;60ms final-command filter;approach shield active',safety_passed=False)
        d.update(completed_training_episodes=self.episodes,safe_full_task_successes=self.safe_successes,native_goal_reaches=self.native_goal_reaches,effort_unsafe_episodes=self.unsafe_episodes,training_effort_rule='per-step penalty and episode latch;no completion credit after violation;native effort limits unchanged;evaluation immediately terminates at0.98')
        d['first_safety_failures']=self.failures
        d.update(max_episode_step=self.max_episode_step,max_approach_index=self.max_approach_index,post_face_env_steps=self.post_face_steps,contract='v197:226->19 frozen legs+6arm residual+1arm speed;48s full-task training')
        self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');tmp.replace(self.path)
    def finish(self):self.completed=True;self.write()

def install_monitor(env,log_dir):return Monitor(env,log_dir)
