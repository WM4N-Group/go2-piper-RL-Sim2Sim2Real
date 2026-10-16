"""Isolated box-edge CLIMB curriculum; shortened starts are never acceptance."""
import json
from pathlib import Path
import torch
from isaaclab.envs.mdp.actions import JointPositionAction
from isaaclab.utils import configclass
from .box_climb_crawl import CrawlJointAction, CrawlJointActionCfg
from .crawl_gait import limit_reference, swing_reference, PlatformFrontExtension
from .climb_stage_math import choose_stage_leg, next_stage_foothold_x, supported_lift_scores, outer_reach_margin, limit_front_followup_x, limit_rear_ascent_x, prepare_rear_edge_x


def reset_climb_stages(env, env_ids):
    if not getattr(env.cfg, 'climb_stage_bank', ''):
        raise ValueError('Stage training requires an explicit provenance-recorded pose bank')
    robot = env.scene['robot']
    if not hasattr(env, '_climb_stage_bank'):
        bank = json.loads(Path(env.cfg.climb_stage_bank).read_text())
        if bank['scope'] != 'training_curriculum_only' or bank['box_height_m'] != .20:
            raise ValueError('Expected an isolated20cm climbing curriculum')
        order = [bank['joint_names'].index(n) for n in robot.joint_names]
        env._climb_stage_bank = {k:torch.tensor([s[k] for s in bank['states']],device=env.device)
                                 for k in ('root_pose','joint_position')}
        env._climb_stage_bank['joint_position'] = env._climb_stage_bank['joint_position'][:,order]
        if all('joint_position_target' in s for s in bank['states']):
            env._climb_stage_bank['joint_position_target'] = torch.tensor(
                [s['joint_position_target'] for s in bank['states']], device=env.device)[:,order]
            env.climb_stage_joint_target = robot.data.joint_pos.clone()
        env.climb_stage_start_id = torch.zeros(env.num_envs,dtype=torch.long,device=env.device)
        env.climb_stage_loaded_reference = bool(bank.get('initialize_loaded_reference',False))
    ids = torch.as_tensor(env_ids,device=env.device,dtype=torch.long)
    index = torch.randint(len(env._climb_stage_bank['root_pose']),(len(ids),),device=env.device)
    env.climb_stage_start_id[ids] = index
    pose = env._climb_stage_bank['root_pose'][index].clone()
    pose[:,:3] += env.scene.env_origins[ids]
    q = env._climb_stage_bank['joint_position'][index]
    limits=robot.data.soft_joint_pos_limits[ids]
    q=torch.maximum(torch.minimum(q,limits[:,:,1]-.01),limits[:,:,0]+.01)
    if 'joint_position_target' in env._climb_stage_bank:
        target = env._climb_stage_bank['joint_position_target'][index]
        env.climb_stage_joint_target[ids] = torch.maximum(
            torch.minimum(target, limits[:,:,1]), limits[:,:,0])
    robot.write_root_pose_to_sim(pose,env_ids=ids)
    robot.write_root_velocity_to_sim(torch.zeros((len(ids),6),device=env.device),env_ids=ids)
    robot.write_joint_state_to_sim(q,torch.zeros_like(q),env_ids=ids)
    initial_target = env.climb_stage_joint_target[ids] if (
        env.climb_stage_loaded_reference and hasattr(env,'climb_stage_joint_target')) else q
    robot.set_joint_position_target(initial_target,env_ids=ids)
    robot.set_joint_velocity_target(torch.zeros_like(q),env_ids=ids)


class StageClimbAction(CrawlJointAction):
    def __init__(self,cfg,env):
        super().__init__(cfg,env)
        self.stage_offset = self.reference.clone()
        self.arm_mask = torch.tensor([self._asset.joint_names[i].startswith('joint') for i in self._joint_ids],device=env.device)
        self.last_advance = torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
        self.platform_hold = torch.zeros_like(self.last_advance)
        self.extension = (PlatformFrontExtension(env.num_envs, env.device, cfg.platform_front_extension)
                          if cfg.platform_front_extension is not None else None)
        self.best_lift = torch.zeros(env.num_envs, device=env.device)
        self.swing_inset = torch.zeros(env.num_envs, device=env.device)
        self.mass = self._asset.root_physx_view.get_masses().to(env.device)
        self.reach_body_ids = {
            part: self._asset.find_bodies([leg+'_'+part for leg in ('FL','FR','RL','RR')], preserve_order=True)[0]
            for part in ('hip', 'thigh', 'calf', 'foot')
        }
        self.guidance = None
        if cfg.guidance_enabled:
            from .climb_guidance import StageGuidance
            self.guidance = StageGuidance(self)

    def center_of_mass(self):
        return (self._asset.data.body_com_pos_w*self.mass[:,:,None]).sum(1)/self.mass.sum(1)[:,None]

    def choose_leg(self, feet):
        local=feet-self._env.scene.env_origins[:,None]
        chosen = choose_stage_leg(local,self.contacts(),self.pending,self.clock.leg,
                                  self.cfg.front_followup, self.cfg.front_followup_target)
        if self.extension is not None:
            chosen = torch.where(self.extension.moving, self.extension.completed.clamp(max=1), chosen)
        return chosen

    def process_actions(self,actions):
        if self.pending.any():
            if hasattr(self._env, 'climb_stage_joint_target'):
                target = self._env.climb_stage_joint_target[:,self._joint_ids]
            else:
                # Original-start evaluation uses the same standing reference
                # as the edge curriculum, independent of randomized reset q.
                target = self._asset.data.default_joint_pos[:,self._joint_ids]
            self.stage_offset[self.pending]=target[self.pending]
        JointPositionAction.process_actions(self,actions)
        requested=self.stage_offset+self._scale*self._raw_actions
        requested[:,self.arm_mask]=self.stage_offset[:,self.arm_mask]
        active=self.walking();feet=self.feet_positions();contacts=self.contacts()
        if self.guidance is not None:
            if self.pending.any():
                # Select the actual next foot before constructing its support triangle.
                selected_leg = self.choose_leg(feet)
                inverse = self.clock.order.argsort()
                self.clock.index[self.pending] = inverse[selected_leg[self.pending]]
                self.guidance.reset(self.pending)
            support_ready = self.guidance.support_ready()
            if self.cfg.guidance_preunload:
                # An unloaded foot may already have lost contact; the clock's
                # ordinary four-foot transfer cannot precede lift in this mode.
                release = support_ready & ~self.pending & (self.clock.elapsed < self.clock.transfer)
                self.clock.elapsed[release] = self.clock.transfer
            active = active & ((self.clock.progress > 0) | support_ready)
        selected=feet[self.rows,self.clock.leg]
        high=torch.maximum(self.start[:,2],self.landing[:,2])+self.cfg.foot_clearance
        raised=selected[:,2]>=high-self.cfg.lift_tolerance
        landing_ready = self.guidance.landing_ready() if (
            self.guidance is not None and self.cfg.guidance_landing_contact) else None
        extension_release = torch.zeros_like(self.platform_hold)
        if self.cfg.guidance_platform_hold:
            from .climb_guidance import platform_hold_ready, platform_support_scope
            enter = ~self.platform_hold & platform_hold_ready(
                feet-self._env.scene.env_origins[:, None], contacts,
                self.clock.progress, self.clock.lifted, landing_ready,
                self.clock.stable, self.clock.settle)
            if enter.any():
                if self.extension is not None:
                    self.extension.landed(enter)
                self.platform_hold[enter] = True
                self.guidance.capture_hold(enter)
            if self.extension is not None:
                robot = self._asset.data
                turn_error = 2*torch.acos((self.guidance.target_orientation*robot.root_quat_w).sum(-1).abs().clamp(max=1.))
                ready = (platform_support_scope(feet-self._env.scene.env_origins[:, None], contacts)
                         & self.guidance.valid_legs.all(1) & (self.guidance.age >= 2.)
                         & ((self.guidance.target-robot.root_pos_w).norm(dim=1) < .01)
                         & (turn_error < .025) & (robot.projected_gravity_b[:, 2] < -.94)
                         & (robot.root_lin_vel_w.norm(dim=1) < .025)
                         & (robot.root_ang_vel_w.norm(dim=1) < .1)
                         & (self.guidance.command_limit_excess.amax(1) < 1e-6))
                extension_release = self.extension.release(self.platform_hold, ready, feet,
                                                          self._env.scene.env_origins, self._env.step_dt)
                if extension_release.any():
                    self.platform_hold[extension_release] = False
                    self.clock.reset(torch.where(extension_release)[0])
            # Releasing a hold only requests a new transfer; no lift this frame.
            active &= ~self.platform_hold & ~extension_release
        traverse_xy = self.landing[:, :2]
        if self.cfg.guidance_swing_preview:
            traverse_xy = traverse_xy.clone()
            traverse_xy[:, 1] += self.swing_inset
        advance=self.clock.update(contacts,active&~self.pending,self._env.step_dt,
            lift_ready=raised&~contacts[self.rows,self.clock.leg],
            traverse_ready=raised&((selected[:,:2]-traverse_xy).norm(dim=1)<self.cfg.landing_xy_tolerance),
            settle_ready=landing_ready)
        self.last_advance[:]=advance
        refresh=advance|self.pending|extension_release
        self.best_lift[refresh] = 0.
        chosen=self.choose_leg(feet)
        inverse=self.clock.order.argsort()
        self.clock.index[refresh]=inverse[chosen[refresh]]
        selected=feet[self.rows,self.clock.leg]
        self.start[refresh]=selected[refresh];self.landing[refresh]=selected[refresh]
        local_x=selected[:,0]-self._env.scene.env_origins[:,0]
        next_x=next_stage_foothold_x(local_x,self.cfg.stride)
        if self.cfg.rear_ground_stride is not None:
            # Shorten only the rear ground follow-up while front feet support on top.
            local_feet = feet-self._env.scene.env_origins[:, None]
            front_on_top = ((local_feet[:, :2, 0] > .79)
                            & (local_feet[:, :2, 2] > .19) & contacts[:, :2]).all(1)
            rear_ground = (self.clock.leg >= 2) & (next_x <= .79) & front_on_top
            next_x = torch.where(rear_ground,
                next_stage_foothold_x(local_x, self.cfg.rear_ground_stride), next_x)
        if self.cfg.front_followup_target is not None:
            next_x = limit_front_followup_x(next_x, feet-self._env.scene.env_origins[:, None],
                contacts, self.clock.leg, self.cfg.front_followup_target)
        if self.cfg.rear_ascent_target is not None:
            next_x = limit_rear_ascent_x(next_x, feet-self._env.scene.env_origins[:, None],
                contacts, self.clock.leg, self.cfg.rear_ascent_target)
        if self.cfg.rear_edge_prep:
            next_x = prepare_rear_edge_x(next_x, feet-self._env.scene.env_origins[:, None],
                contacts, self.clock.leg)
        self.landing[refresh,0]=(next_x+self._env.scene.env_origins[:,0])[refresh]
        self.landing[refresh,2]=(self._env.scene.env_origins[:,2]+torch.where(next_x>.79,.2245,.024))[refresh]
        if self.extension is not None:
            extending = refresh & self.extension.moving
            self.landing[extending] = self.extension.goals[
                self.rows[extending], self.extension.completed[extending]]
        if self.cfg.guidance_swing_preview:
            from .climb_guidance import stage_swing_inset
            self.swing_inset[refresh] = stage_swing_inset(self.start, self.landing,
                self.clock.leg, self._env.scene.env_origins, feet, contacts,
                self.cfg.last_rear_swing_inset)[refresh]
        self.foot_reference[:]=swing_reference(self.start,self.landing,self.clock.progress,self.cfg.foot_clearance)
        if self.cfg.guidance_forward_lift:
            from .climb_guidance import edge_lift_reference
            self.foot_reference[:] = edge_lift_reference(self.start,self.landing,
                self.clock.progress,self._env.scene.env_origins,self.cfg.foot_clearance,
                self.swing_inset if self.cfg.guidance_swing_preview else None)
        if self.guidance is not None:
            capture = advance | extension_release
            if capture.any():
                self.guidance.capture(capture)
            if self.cfg.guidance_landing_contact:
                self.foot_reference[:, 2] -= self.guidance.landing_contact.depth
            requested = self.guidance.requested(requested)
        self.reference[self.pending]=self._asset.data.joint_pos[:,self._joint_ids][self.pending]
        if getattr(self._env,'climb_stage_loaded_reference',False):
            self.reference[self.pending]=self.stage_offset[self.pending]
        self.reference_velocity[self.pending]=0;self.pending[:]=False
        limits=self._asset.data.soft_joint_pos_limits[:,self._joint_ids]
        self.reference[:],self.reference_velocity[:]=limit_reference(self.reference,self.reference_velocity,requested,
            limits[...,0],limits[...,1],self.max_velocity,self.max_acceleration,self._env.step_dt)
        self._processed_actions[:]=self.reference

    def reset(self,env_ids=None):
        super().reset(env_ids)
        if hasattr(self,'last_advance'):
            self.last_advance[slice(None) if env_ids is None else env_ids]=False
            self.best_lift[slice(None) if env_ids is None else env_ids]=0.
            self.platform_hold[slice(None) if env_ids is None else env_ids]=False
            if self.extension is not None:
                self.extension.reset(slice(None) if env_ids is None else env_ids)


@configclass
class StageClimbActionCfg(CrawlJointActionCfg):
    class_type = StageClimbAction
    stride: float = .22
    foot_clearance: float = .03
    swing_s: float = 1.2
    transfer_s: float = .35
    guidance_enabled: bool = False
    guidance_residual_scale: float = .2
    guidance_body_gain: float = .5
    guidance_body_damping: float = .08
    guidance_loaded_start: bool = False
    guidance_forward_lift: bool = False
    guidance_body_clearance: float = .34
    guidance_force_balance: bool = False
    guidance_horizontal_balance: bool = False
    guidance_preunload: bool = False
    guidance_front_force_trim: bool = False
    guidance_front_stall_trim: bool = False
    guidance_front_followup_force_trim: bool = False
    guidance_front_followup_preview: bool = False
    guidance_single_front_pose: bool = False
    guidance_retain_infeasible_reference: bool = False
    guidance_pose_fixtures: bool = False
    guidance_refine_height: bool = False
    guidance_endpoint_leg_reserve: bool = False
    guidance_endpoint_body_reserve: bool = False
    guidance_platform_load_reserve: bool = False
    guidance_platform_support_path: bool = False
    guidance_platform_support_recovery: bool = False
    guidance_front_ascent_pose: bool = False
    guidance_landing_contact: bool = False
    guidance_mixed_height: bool = False
    guidance_support_feedback: bool = False
    guidance_support_plane: bool = False
    guidance_plane_fraction: float = 1.
    guidance_feasible_pose: bool = False
    guidance_body_collision: bool = False
    guidance_independent_height: bool = False
    guidance_leg_collision: bool = False
    guidance_primitive_collision: bool = False
    guidance_load_preview: bool = False
    guidance_swing_preview: bool = False
    guidance_swing_transfer: bool = False
    guidance_last_pose_search: bool = False
    guidance_edge_pose_search: bool = False
    guidance_pose_angle_coverage: bool = False
    last_rear_swing_inset: float | None = None
    front_raise_height: float | None = None
    guidance_rotate_com: bool = False
    guidance_platform_pose: bool = False
    guidance_platform_hold: bool = False
    guidance_platform_level: bool = False
    guidance_platform_hold_tracking: bool = False
    guidance_platform_hold_tracking_max_extra: float = .5
    guidance_platform_extension_force_trim: bool = False
    guidance_platform_extension_tracking: bool = False
    guidance_platform_settled_recovery: bool = False
    guidance_platform_final_recovery_rise: bool = False
    platform_front_extension: float | None = None
    platform_front_first: bool = False
    platform_final_adjust: bool = False
    guidance_platform_swing: bool = False
    rear_ground_stride: float | None = None
    front_followup: bool = False
    front_followup_target: float | None = None
    rear_ascent_target: float | None = None
    rear_edge_prep: bool = False


def support_shift_reward(env):
    a=env.action_manager.get_term('joint_pos');feet=a.feet_positions()
    indices=torch.tensor([[j for j in range(4) if j!=i] for i in range(4)],device=env.device)[a.clock.leg]
    triangle=feet.gather(1,indices[:,:,None].expand(-1,-1,3))[:,:,:2]
    edge=triangle.roll(-1,1)-triangle
    sign=(edge[:,0,0]*edge[:,1,1]-edge[:,0,1]*edge[:,1,0]).sign()
    relative=a.center_of_mass()[:,None,:2]-triangle
    margin=((edge[:,:,0]*relative[:,:,1]-edge[:,:,1]*relative[:,:,0])*sign[:,None]/edge.norm(dim=2).clamp_min(1e-6)).amin(1)
    return torch.exp(-((.035-margin).clamp_min(0)/.05).square())*a.walking()


def stage_pose_reward(env):
    a=env.action_manager.get_term('joint_pos');feet=a.feet_positions()
    anticipated=feet[:,:,2].clone()
    anticipated[a.rows,a.clock.leg]=.5*(a.start[:,2]+a.landing[:,2])
    pitch=-torch.atan2(anticipated[:,:2].mean(1)-anticipated[:,2:].mean(1),torch.full_like(a.clock.progress,.3868)).clamp(-.35,.35)
    desired_gravity=torch.stack((pitch.sin(),torch.zeros_like(pitch),-pitch.cos()),dim=1)
    height=anticipated.mean(1)-.0225+.30
    error=((a._asset.data.root_pos_w[:,2]-height)/.07).square()
    error+=((a._asset.data.projected_gravity_b-desired_gravity)/.20).square().sum(1)
    return torch.exp(-error)


def stage_step_reward(env):
    return env.action_manager.get_term('joint_pos').last_advance.float()/env.step_dt


def stage_reach_reward(env):
    a = env.action_manager.get_term('joint_pos')
    points = [a._asset.data.body_pos_w[:, a.reach_body_ids[part]][a.rows, a.clock.leg]
              for part in ('hip', 'thigh', 'calf', 'foot')]
    target = a.landing.clone()
    target[:, 2] = torch.maximum(a.start[:, 2], a.landing[:, 2]) + a.cfg.foot_clearance
    margin = outer_reach_margin(*points, target)
    return torch.exp(-((-margin).clamp_min(0.) / .04).square()) * a.walking() * ~a.pending


def lift_scores(env):
    a = env.action_manager.get_term('joint_pos')
    phase = a.clock.progress
    force = env.scene['contact_forces'].data.net_forces_w[:, a.sensor_ids, 2]
    high = torch.maximum(a.start[:, 2], a.landing[:, 2]) + a.cfg.foot_clearance
    active = a.walking() & ~a.pending & (phase > 0) & (phase <= .75)
    return supported_lift_scores(force, a.clock.leg,
        a.feet_positions()[a.rows, a.clock.leg, 2], a.start[:, 2], high, active)


def stage_unload_reward(env):
    return lift_scores(env)[0]


def stage_lift_height_reward(env):
    # Pay once for each new height reached within this footstep. Holding aloft
    # or repeatedly raising/lowering the same foot cannot farm height reward.
    a = env.action_manager.get_term('joint_pos')
    score = lift_scores(env)[1]
    increment = (score - a.best_lift).clamp_min(0.)
    a.best_lift[:] = torch.maximum(a.best_lift, score)
    return increment / env.step_dt


def stage_swing_contact_reward(env):
    a = env.action_manager.get_term('joint_pos')
    phase = a.clock.progress
    transfer = ((phase <= 0) | (phase >= 1)) & a.walking() & ~a.pending
    return lift_scores(env)[2] + (a.contacts().all(1) & transfer).float()
