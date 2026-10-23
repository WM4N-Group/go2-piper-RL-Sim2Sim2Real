"""Continuous NAV / PUSH / stow / NAV development candidate, without physical resets."""
import argparse
import os
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--nav-actor', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--seed', type=int, default=3701)
p.add_argument('--seconds', type=float, default=18.)
from isaaclab.app import AppLauncher
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
if a.output.exists(): p.error('Never overwrite evidence')
a.output.mkdir(parents=True)
launcher = AppLauncher(a)
import torch
import gymnasium as gym
import isaaclab_tasks
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import quat_apply_inverse, quat_mul, quat_conjugate
from stance_wrench_math import allocate_wrench
from native_arm_effort_guard import guard_reference
from stance_wrench_fallback import refine_stance_wrench
from prospective_support import prospective_support
from box_approach_standoff import required_standoff
import LeggedManip_Lab.tasks
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.residual_push_actions import ResidualPushAction
sys.path.insert(0, str(a.source/'scripts/rsl_rl'))
from safe_retraining import configure, verify_physics, physical_sample, install_frozen_legs
from initialization import actor_from_state_dict
from piper_skill_transition_contract import EntryState, Handoff, BoundedReference
from climb_leg_kinematics import LegKinematics, rotate_vector
from stance_load_math import balanced_acceleration_loads

TASK = 'GO2-PIPER-Box-Push-Tracking-Play'
NAV_SHA = '72d9f22c633081e8d4b9693e6fda54dba6cdd036a102f330c1bfe096e43b4da8'

# Candidate-local function overlay; frozen source remains untouched.
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push_ik as _push_ik
_overlay_path=Path(__file__).with_name('push_local_clock_apply.py')
_overlay_namespace={}
exec(compile(_overlay_path.read_text(),str(_overlay_path),'exec'),vars(_push_ik),_overlay_namespace)
_push_ik.PushArmIK.apply=_overlay_namespace['apply']

from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_push import PushSettled

class PushSettledEvent(PushSettled):
    """Preserve original success predicate as an event to continue without reset."""
    def __call__(self,env,asset_cfg=SceneEntityCfg("robot",body_names="end_effector"),hold_time=0.5):
        native=super().__call__(env,asset_cfg=asset_cfg,hold_time=hold_time)
        env.transition_native_push_settled=native.clone()
        return torch.zeros_like(native)

# Extra15mm planning reserve; actual original35mm termination stays unchanged.
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_push_geometry import PiperBaseArmGeometryShield
_original_geometry_project=PiperBaseArmGeometryShield.project
def planning_reserve_project(self,actual,velocity,target,lower,upper,active):
    original_minimum=self.minimum
    assert abs(original_minimum-.035)<1e-9
    try:
        self.minimum=original_minimum+getattr(self,"transition_planning_reserve_m",0.)
        return _original_geometry_project(self,actual,velocity,target,lower,upper,active)
    finally:
        self.minimum=original_minimum
PiperBaseArmGeometryShield.project=planning_reserve_project

def prospective_entry(c,robot,joint_ids,joint_names,*,reserve_for_late_parking=False,nominal_translation_w=None):
    baseline=prospective_support(c,robot,joint_ids,joint_names,reserve_for_late_parking=reserve_for_late_parking,nominal_translation_w=nominal_translation_w)
    box=c.env.scene['box']
    preview=required_standoff(c.geometry_shield,joint_names,robot.data.joint_pos[0,joint_ids].cpu().numpy(),robot.data.root_pos_w[0].cpu().numpy(),robot.data.root_quat_w[0].cpu().numpy(),box.data.root_pos_w[0].cpu().numpy(),box.data.root_quat_w[0].cpu().numpy(),c.safe_approach_waypoints.cpu().numpy(),c.env.cfg.box_size,residual_limit=.5*c.safe_approach_position_tolerance,nominal_translation_w=nominal_translation_w,forecast_margin_m=.005 if nominal_translation_w is not None else 0.)
    measured=robot.data.body_pos_w[0,robot.find_bodies(['end_effector'],preserve_order=True)[0][0]].cpu().numpy()
    if float(__import__('numpy').linalg.norm(measured-preview.pop('source_hand_position_w')))>.0002:raise ValueError('Box-approach hand FK source mismatch')
    minimum=preview['minimum_shift_m']
    plan=baseline if minimum<=baseline['shift_m'] else prospective_support(c,robot,joint_ids,joint_names,reserve_for_late_parking=reserve_for_late_parking,nominal_translation_w=nominal_translation_w,minimum_shift_m=minimum)
    # Extra box standoff is a distinct entry preparation; it does not enable
    # support-only hand-height/after-READY extension changes.
    plan['support_only_shift_m']=baseline['shift_m']
    plan['box_approach_preview']=preview
    return plan

def native_entry_process(self, actions):
        c=self.controller;robot=c.robot
        ids=robot.find_joints(self.cfg.joint_names,preserve_order=True)[0]
        age=float(self._env.episode_length_buf[0])*self._env.step_dt
        current=robot.data.joint_pos_target[:,ids].clone()
        self.native_pass_through=False
        if age<2.:
            # Preserve the recorded safe initialization prefix. This is a
            # preparation state, not claimed as native NAV or PUSH execution.
            ResidualPushAction.process_actions(self,actions)
        elif getattr(self,'native_nav_ready',False):
            self._raw[:]=actions
            self.joint_commands[:]=actions[:,:18]
            if not hasattr(self,'native_arm_pd_parameters'):
                kp=[];kd=[];effort=[]
                for joint in c.joint_ids:
                    actuator=next(v for v in robot.actuators.values() if joint in v.joint_indices)
                    local=list(actuator.joint_indices).index(joint)
                    kp.append(actuator.stiffness[:,local]);kd.append(actuator.damping[:,local]);effort.append(actuator.effort_limit[:,local])
                self.native_arm_pd_parameters=tuple(torch.stack(values,dim=1) for values in (kp,kd,effort))
            kp,kd,effort=self.native_arm_pd_parameters
            native_target=robot.data.default_joint_pos[:,c.joint_ids]+c.scale*actions[:,c.action_slots]
            bounds=robot.data.soft_joint_pos_limits[:,c.joint_ids]
            guarded,details=guard_reference(native_target,robot.data.joint_pos[:,c.joint_ids],robot.data.joint_vel[:,c.joint_ids],kp,kd,effort,bounds[...,0],bounds[...,1])
            self.native_arm_guard=details
            self.native_arm_guard['raw_target']=native_target[0].tolist()
            self.native_arm_guard['guarded_target']=guarded[0].tolist()
            # Preserve raw policy output exactly on axes not changed by the guard.
            replacement=(guarded-robot.data.default_joint_pos[:,c.joint_ids])/c.scale
            self.joint_commands[:,c.action_slots]=torch.where(guarded!=native_target,replacement,actions[:,c.action_slots])
            self.delegate.process_actions(self.joint_commands)
            self.native_pass_through=not details['changed']
        else:
            if not hasattr(self,'nav_entry_reference'):
                self.nav_entry_reference=current.clone()
            self._raw[:]=actions
            native=robot.data.default_joint_pos[:,ids]+c.scale*actions[:,:18]
            u=min(1.,(age-2.)/1.);blend=u**3*(10.-15.*u+6.*u*u)
            desired=self.nav_entry_reference+blend*(native-self.nav_entry_reference)
            # PD feedback targets need not move at the actual joint speed.
            # Blend only the source/target authority envelope, then restore exact
            # native commands. No permanent reference-rate filter on active NAV.
            arm_u=min(1.,(age-2.)/4.);arm_blend=arm_u**3*(10.-15.*arm_u+6.*arm_u*arm_u)
            desired[:,c.action_slots]=self.nav_entry_reference[:,c.action_slots]+arm_blend*(native[:,c.action_slots]-self.nav_entry_reference[:,c.action_slots])
            self.joint_commands[:]=(desired-robot.data.default_joint_pos[:,ids])/c.scale
            self.delegate.process_actions(self.joint_commands)
            self.nav_bridge_error_rad=float((desired-native).abs().max())
            self.native_nav_ready=age>=6.
        self.previous_target=current

def bounded_nav_request(env, requested):
    step=int(env.episode_length_buf[0])
    if not hasattr(env,'nav_request_step'):
        env.nav_request_step=step
        env.nav_request_value=torch.zeros_like(requested)
    elapsed=(step-env.nav_request_step)*env.step_dt
    if elapsed<0.:raise ValueError('NAV request clock reversed')
    if elapsed>0.:
        allowance=torch.tensor([.10,.10,.25],device=env.device)*elapsed
        delta=torch.maximum(torch.minimum(requested-env.nav_request_value,allowance),-allowance)
        env.nav_request_value=env.nav_request_value+delta
        env.nav_request_step=step
    return env.nav_request_value.clone()

class Router(ResidualPushAction):
    """Diagnostic original v212 two second startup, then loaded NAV transfer."""
    def process_actions(self, actions):
        c=self.controller;robot=c.robot
        ids=robot.find_joints(self.cfg.joint_names,preserve_order=True)[0]
        age=float(self._env.episode_length_buf[0])*self._env.step_dt
        current=robot.data.joint_pos_target[:,ids].clone()
        self.native_pass_through=False
        if not getattr(self,'request_hold',False) and not getattr(self,'return_nav_requested',False):
            native_entry_process(self,actions)
            return
        if getattr(self,'return_nav_active',False):
            if not hasattr(self,'return_nav_initial_target'):
                self.return_nav_initial_target=current.clone()
                self.return_nav_start_age=age
                velocity=((current-self.previous_target)/self._env.step_dt)[0,c.action_slots].tolist()
                self.return_arm_limiter=BoundedReference(current[0,c.action_slots].tolist(),velocity,[.45]*6,[1.]*6,self._env.step_dt)
            desired=robot.data.default_joint_pos[:,ids]+c.scale*actions[:,:18]
            u=min(1.,(age-self.return_nav_start_age)/1.0)
            blend=u**3*(10.-15.*u+6.*u*u)
            desired=self.return_nav_initial_target+blend*(desired-self.return_nav_initial_target)
            # Native NAV six-arm output now has control authority, through the
            # explicit bounded transition adapter and original geometry shield.
            limits=robot.data.soft_joint_pos_limits[:,c.joint_ids]
            arm=torch.maximum(torch.minimum(desired[:,c.action_slots],limits[...,1]-.01),limits[...,0]+.01)
            measured=robot.data.joint_pos[:,c.joint_ids]
            velocity=robot.data.joint_vel[:,c.joint_ids]
            shielded,clearance,blocked=c.geometry_shield.project(
                measured.detach().cpu().numpy(),velocity.detach().cpu().numpy(),
                arm.detach().cpu().numpy(),(limits[...,0]+.01).cpu().numpy(),
                (limits[...,1]-.01).cpu().numpy(),torch.ones(self._env.num_envs,dtype=torch.bool).numpy())
            self.return_nav_arm_blocked=bool(blocked[0])
            arm=torch.as_tensor(shielded,device=self._env.device,dtype=arm.dtype)
            desired[:,c.action_slots]=torch.tensor(self.return_arm_limiter.advance(arm[0].tolist()),device=self._env.device)[None]
            self._raw[:]=actions
            self.joint_commands[:]=(desired-robot.data.default_joint_pos[:,ids])/c.scale
            self.delegate.process_actions(self.joint_commands)
        elif getattr(self,'push_legs_taken_over',False):
            super().process_actions(actions)
        elif hasattr(self,'push_release_hold_commands') and not getattr(self,'exit_requested',False):
            # The native contact-qualified gait ramp owns release. A four-foot
            # stationary wrench solve no longer describes its moving contacts.
            # Fade the last verified bounded stance command without retargeting it.
            super().process_actions(actions)
            blend=c.leg_release_blend[:,None].clone()
            self.joint_commands[:,c.leg_slots]+=(1.-blend)*self.push_release_hold_commands
            self.delegate.process_actions(self.joint_commands)
            if bool((blend>=1.-1e-6).all()):self.push_legs_taken_over=True
        elif getattr(self,'request_hold',False):
            if not hasattr(self,'hold_reference'):
                velocity=((current-self.previous_target)/self._env.step_dt)[0].tolist()
                # NAV target derivatives oscillate much faster than the loaded
                # joints. Seed only new hold-reference leg velocity from measured
                # dq, keep issued position and actuator queues. This explicitly
                # does not claim issued-target C1 continuity across capture.
                for slot in c.leg_slots:velocity[slot]=float(robot.data.joint_vel[0,ids[slot]])
                if not getattr(self,'exit_requested',False):
                    # Stopped capture requires arm speed<0.2rad/s; explicitly
                    # pre-READY supported braking admits<0.35rad/s.
                    # Preserve last issued position; initialize the new transition
                    # reference with measured motion, not NAV PD feedback rate.
                    for slot in c.action_slots:velocity[slot]=float(robot.data.joint_vel[0,ids[slot]])
                self.hold_reference=BoundedReference(current[0].tolist(),velocity,[1.]*12+[.45]*6,[4.]*12+[1.]*6,self._env.step_dt)
                self.hold_goal=current.clone()
                self.captured_entry_arm_pose=robot.data.joint_pos[:,c.joint_ids].clone()
                self.prepare_arm=False
                self.stance_model=LegKinematics.from_usd(self._env.cfg.scene.robot.spawn.usd_path,device=self._env.device).reordered(('FR','FL','RR','RL'))
                self.stance_feet=robot.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0]
                self.stance_ids=[ids[i] for i in c.leg_slots]
                self.stance_anchor=robot.data.body_pos_w[:,self.stance_feet].clone()
                self.stance_origin=robot.data.root_pos_w.clone()
                self.stance_orientation=robot.data.root_quat_w.clone()
                measured_q=robot.data.joint_pos[:,self.stance_ids].reshape(1,4,3)
                measured_feet=rotate_vector(self.stance_orientation[:,None],self.stance_anchor-self.stance_origin[:,None],inverse=True)
                self.stance_geometry_error=float((self.stance_model.forward(measured_q)-measured_feet).norm(dim=-1).max())
                if self.stance_geometry_error>5e-5:raise ValueError('Active USD leg geometry mismatch')
                self.stance_bias=current[:,c.leg_slots].reshape(1,4,3)-measured_q
                self.hold_start_age=age
                leg_act=robot.actuators['base_legs']
                assert torch.allclose(leg_act.stiffness,torch.full_like(leg_act.stiffness,30.))
                assert torch.allclose(leg_act.damping,torch.full_like(leg_act.damping,.6))
                self.stance_mass=robot.root_physx_view.get_masses().to(self._env.device)
                self.entry_direct_center=False
                if not getattr(self,'exit_requested',False) and not getattr(self,'return_nav_requested',False):
                    displacement=torch.zeros_like(self.stance_origin)
                    displacement[:,:2]=self._env.scene.env_origins[:,:2]-self.stance_origin[:,:2]
                    if float(displacement[:,:2].norm())<.05:
                        try:
                            preview=prospective_support(c,robot,ids,[robot.joint_names[i] for i in ids],nominal_translation_w=displacement[0].cpu().numpy())
                        except ValueError as error:
                            if str(error)!='No prospective nominal-path support solution within40mm preparation bound':raise
                            preview=dict(scope='Direct-center preview infeasible; retain two-stage entry',shift_m=None)
                        self.entry_direct_center_preview=preview
                        self.entry_direct_center=preview['shift_m']==0.
                # Direct centering is a planning choice only. Every actual force,
                # actuator, contact, stop and final measured path gate remains.


            desired=self.hold_goal.clone()
            nominal=rotate_vector(self.stance_orientation[:,None],self.stance_anchor-self.stance_origin[:,None],inverse=True)
            actual=rotate_vector(robot.data.root_quat_w[:,None],self.stance_anchor-robot.data.root_pos_w[:,None],inverse=True)
            velocity=robot.data.root_lin_vel_b[:,None]+torch.cross(robot.data.root_ang_vel_b[:,None].expand_as(nominal),nominal,dim=-1)
            correction=torch.zeros_like(nominal)
            correction*= (.05/correction.norm(dim=-1).clamp_min(.05))[...,None]
            corrected=nominal+correction
            q=self.stance_model.inverse(corrected)
            if float((self.stance_model.forward(q)-corrected).norm(dim=-1).max())>.001:raise ValueError('Hold stance IK infeasible')
            mass=self.stance_mass;com=(robot.data.body_com_pos_w*mass[:,:,None]).sum(1)/mass.sum(1)[:,None]
            # After force-controller transfer, center within the captured support
            # polygon over 3s. Keep captured height/orientation and all ready gates.
            center_u=max(0.,min(1.,(age-self.hold_start_age-1.5)/3.))
            center_blend=center_u**3*(10.-15.*center_u+6.*center_u*center_u)
            center_rate=30.*center_u**2*(1.-center_u)**2/3.
            center_delta=torch.zeros_like(self.stance_origin)
            center_delta[:,:2]=self._env.scene.env_origins[:,:2]-self.stance_origin[:,:2]
            # Restore original full entry centering before the frozen PUSH path.
            # Late capture uses the same3s quintic and original READY gates.
            if (getattr(self,'exit_hold',False) or getattr(self,'exit_brake_hold',False)):center_delta.zero_()
            if getattr(self,'return_nav_arrival_brake',False):
                # After actual four-contact arrival braking, center only into the
                # inner30mm destination region through the existing3s quintic.
                # Original final50mm goal and all support/stop gates are unchanged.
                center_delta[:,:2]=self.return_nav_goal[:,:2]-self.stance_origin[:,:2]
                distance=center_delta[:,:2].norm(dim=1,keepdim=True)
                center_delta[:,:2]*=(1.-.03/distance.clamp_min(.03)).clamp_min(0.)
            # Supported entry only: stop inside35mm first while retaining NAV
            # arm pose, then convert the arm after real loaded stop. Complete
            # the full centering only after the original PUSH arm pose settles.
            # The35mm offset is intermediate, never the frozen PUSH start pose.
            entry_centering=not getattr(self,'exit_requested',False) and not getattr(self,'return_nav_requested',False)
            final_center_delta=center_delta.clone()
            if entry_centering and not getattr(self,'entry_direct_center',False):
                distance=center_delta[:,:2].norm(dim=1,keepdim=True)
                center_delta[:,:2]*=(1.-.035/distance.clamp_min(.035)).clamp_min(0.)
            self.stance_position_target=self.stance_origin+center_blend*center_delta
            self.stance_velocity_target=center_rate*center_delta
            if entry_centering and hasattr(self,'entry_final_center_start_age'):
                final_duration=4. if getattr(self,'prospective_shift_m',0.)>0. else (0. if getattr(self,'entry_direct_center',False) else 3.)
                final_u=1. if final_duration==0. else max(0.,min(1.,(age-self.entry_final_center_start_age)/final_duration))
                final_blend=final_u**3*(10.-15.*final_u+6.*final_u*final_u)
                final_rate=0. if final_duration==0. else 30.*final_u**2*(1.-final_u)**2/final_duration
                remaining=final_center_delta-center_delta
                remaining[:,0]-=getattr(self,'prospective_shift_m',0.)
                self.stance_position_target+=final_blend*remaining
                self.stance_velocity_target+=final_rate*remaining
            if getattr(self,'prospective_shift_m',0.)>0. and not getattr(self,'exit_requested',False):
                prep_u=max(0.,min(1.,(age-self.prospective_start_age)/4.))
                prep_blend=prep_u**3*(10.-15.*prep_u+6.*prep_u*prep_u)
                prep_rate=30.*prep_u**2*(1.-prep_u)**2/4.
                if not getattr(self,'entry_support_integrated',False):
                    self.stance_position_target[:,0]-=self.prospective_shift_m*prep_blend
                    self.stance_velocity_target[:,0]-=self.prospective_shift_m*prep_rate
                if getattr(self,'push_active',False):
                    push_age=age-self.push_support_start_age
                    push_u=max(0.,min(1.,push_age/4.))
                    push_blend=push_u**3*(10.-15.*push_u+6.*push_u*push_u)
                    push_rate=30.*push_u**2*(1.-push_u)**2/4.
                    extra=self.push_support_shift_m-self.prospective_shift_m
                    self.stance_position_target[:,0]-=extra*push_blend
                    self.stance_velocity_target[:,0]-=extra*push_rate
            acceleration=12.*(self.stance_position_target-robot.data.root_pos_w)+5.*(self.stance_velocity_target-robot.data.root_lin_vel_w)
            acceleration[:,2]=25.*(self.stance_origin[:,2]-robot.data.root_pos_w[:,2])-8.*robot.data.root_lin_vel_w[:,2]
            acceleration=acceleration.clamp(-.5,.5)
            force=mass.sum(1)[:,None]*(acceleration+torch.tensor([0.,0.,9.81],device=self._env.device))
            orientation_target=self.stance_orientation
            angular_velocity_target=torch.zeros_like(robot.data.root_ang_vel_w)
            if not getattr(self,'exit_requested',False) and not getattr(self,'return_nav_requested',False):
                # Explicit supported conversion to the PUSH box-face heading.
                # Keep captured roll/pitch/height, fixed foot anchors and the
                # existing3s quintic center envelope; source NAV stays unchanged.
                if not hasattr(self,'entry_heading_delta'):
                    sw,sx,sy,sz=self.stance_orientation.unbind(-1)
                    bw,bx,by,bz=self._env.scene['box'].data.root_quat_w.unbind(-1)
                    source_yaw=torch.atan2(2.*(sw*sz+sx*sy),1.-2.*(sy*sy+sz*sz))
                    box_yaw=torch.atan2(2.*(bw*bz+bx*by),1.-2.*(by*by+bz*bz))
                    delta=box_yaw-source_yaw
                    self.entry_heading_delta=torch.atan2(torch.sin(delta),torch.cos(delta))
                half_angle=.5*center_blend*self.entry_heading_delta
                yaw_rotation=torch.zeros_like(self.stance_orientation)
                yaw_rotation[:,0]=torch.cos(half_angle);yaw_rotation[:,3]=torch.sin(half_angle)
                orientation_target=quat_mul(yaw_rotation,self.stance_orientation)
                angular_velocity_target[:,2]=center_rate*self.entry_heading_delta
            self.stance_orientation_target=orientation_target
            self.stance_angular_velocity_target=angular_velocity_target
            error=quat_mul(orientation_target,quat_conjugate(robot.data.root_quat_w))
            rotation=2.*error[:,1:]*torch.where(error[:,:1]<0.,-1.,1.)
            moment=(8.*rotation+2.*(angular_velocity_target-robot.data.root_ang_vel_w)).clamp(-4.,4.)
            loads,residual=allocate_wrench(robot.data.body_pos_w[:,self.stance_feet],com,force,moment)
            self.stance_wrench_fallback=None
            if float(residual[:,:3].abs().max())>.5 or float(residual[:,3:].abs().max())>.1:
                fallback,details=refine_stance_wrench(robot.data.body_pos_w[:,self.stance_feet],com,force,moment,loads)
                self.stance_wrench_fallback=details
                if fallback is not None:loads,residual=fallback
            self.stance_wrench_target=torch.cat((force,moment),dim=-1)
            if float(residual[:,:3].abs().max())>.5 or float(residual[:,3:].abs().max())>.1:
                (a.output/'wrench-failure-input.json').write_text(json.dumps(dict(
                    time_s=age,feet=robot.data.body_pos_w[:,self.stance_feet].tolist(),
                    center_of_mass=com.tolist(),force=force.tolist(),moment=moment.tolist(),
                    residual=residual.tolist(),loads=loads.tolist(),fallback=self.stance_wrench_fallback),indent=2)+'\n')
                raise ValueError('Stance wrench allocation did not satisfy original residual bounds')
            self.stance_loads=loads;self.stance_wrench_residual=residual;self.stance_com=com
            jacobians=robot.root_physx_view.get_jacobians();gravity=robot.root_physx_view.get_gravity_compensation_forces()
            offset=0 if robot.is_fixed_base else 6
            load_bias=torch.zeros_like(self.stance_bias)
            for leg,body in enumerate(self.stance_feet):
                jid=self.stance_ids[leg*3:leg*3+3]
                jac=jacobians[:,body-(1 if robot.is_fixed_base else 0),:3][:,:,[i+offset for i in jid]]
                columns=jid if gravity.shape[1]==robot.num_joints else [i+offset for i in jid]
                torque=gravity[:,columns]-(jac.transpose(1,2)@loads[:,leg,:,None]).squeeze(-1)
                cap=.75*robot.data.joint_effort_limits[:,jid]
                load_bias[:,leg]=torch.maximum(torch.minimum(torque,cap),-cap)/30.
            u=min(1.,(age-self.hold_start_age)/.3);blend=u**3*(10.-15.*u+6.*u*u)
            measured=robot.data.joint_pos[:,self.stance_ids].reshape(1,4,3)
            damping=.6*robot.data.joint_vel[:,self.stance_ids].reshape(1,4,3)/30.
            loaded=((1.-blend)*(q+self.stance_bias)+blend*(measured+load_bias+damping)).reshape(1,12)
            limits=robot.data.soft_joint_pos_limits[:,self.stance_ids]
            if bool(((loaded<limits[...,0])|(loaded>limits[...,1])).any()):raise ValueError('Hold stance target violates original soft limits')
            self.stance_desired=loaded.clone();self.stance_correction=correction.clone()
            desired[:,c.leg_slots]=loaded
            if True:  # Preserve captured native arm endpoint until loaded preparation.
                gravity=robot.root_physx_view.get_gravity_compensation_forces()
                columns=c.joint_ids if gravity.shape[1]==robot.num_joints else c.jacobian_columns
                arm_pose=self.exit_arm_pose if (getattr(self,'exit_hold',False) or getattr(self,'exit_brake_hold',False)) else self.captured_entry_arm_pose
                if self.prepare_arm and not getattr(self,'exit_requested',False):
                    # Move only after real loaded stability, using the kinematic
                    # arm pose for geometry planning, before gravity compensation.
                    measured=robot.data.joint_pos[:,c.joint_ids]
                    velocity=robot.data.joint_vel[:,c.joint_ids]
                    if not hasattr(self,'entry_arm_reference'):self.entry_arm_reference=measured.clone()
                    delta=.45*self._env.step_dt
                    limits=robot.data.soft_joint_pos_limits[:,c.joint_ids]
                    lower=torch.maximum(limits[...,0],self.entry_arm_reference-delta)
                    upper=torch.minimum(limits[...,1],self.entry_arm_reference+delta)
                    requested=_push_ik.coordinated_joint_target(self.entry_arm_reference,c.safe_approach_waypoints[0][None],torch.full((1,1),delta,device=self._env.device))
                    shielded,clearance,blocked=c.geometry_shield.project(measured.detach().cpu().numpy(),velocity.detach().cpu().numpy(),requested.detach().cpu().numpy(),lower.detach().cpu().numpy(),upper.detach().cpu().numpy(),torch.ones(self._env.num_envs,dtype=torch.bool).numpy())
                    self.entry_arm_reference=torch.as_tensor(shielded,device=self._env.device,dtype=measured.dtype)
                    self.entry_arm_geometry_blocked=bool(blocked[0])
                    arm_pose=self.entry_arm_reference
                if getattr(self,'exit_retract',False):
                    measured=robot.data.joint_pos[:,c.joint_ids]
                    measured_velocity=robot.data.joint_vel[:,c.joint_ids]
                    if not hasattr(self,'retract_reference'):
                        self.retract_reference=measured.clone()
                        self.retract_waypoints=torch.stack((c.safe_approach_waypoints[-1],c.safe_approach_waypoints[0]))
                        self.retract_index=0
                    goal=self.retract_waypoints[min(self.retract_index,1)][None]
                    if self.retract_index<2 and bool((measured-goal).abs().max()<c.safe_approach_position_tolerance and measured_velocity.abs().max()<c.safe_approach_velocity_tolerance):
                        self.retract_index+=1
                        goal=self.retract_waypoints[min(self.retract_index,1)][None]
                    delta=.45*self._env.step_dt
                    limits=robot.data.soft_joint_pos_limits[:,c.joint_ids]
                    lower=torch.maximum(limits[...,0],self.retract_reference-delta)
                    upper=torch.minimum(limits[...,1],self.retract_reference+delta)
                    requested=_push_ik.coordinated_joint_target(self.retract_reference,goal,torch.full((1,1),delta,device=self._env.device))
                    assert c.geometry_shield is not None
                    shielded,measured_clearance,blocked=c.geometry_shield.project(
                        measured.detach().cpu().numpy(),measured_velocity.detach().cpu().numpy(),
                        requested.detach().cpu().numpy(),lower.detach().cpu().numpy(),upper.detach().cpu().numpy(),
                        torch.ones(self._env.num_envs,dtype=torch.bool,device=self._env.device).cpu().numpy())
                    self.retract_reference=torch.as_tensor(shielded,device=self._env.device,dtype=measured.dtype)
                    self.retract_geometry_blocked=bool(blocked[0])
                    self.retract_geometry_clearance=float(measured_clearance[0])
                    arm_pose=self.retract_reference
                desired[:,c.action_slots]=arm_pose+gravity[:,columns]/c.stiffness
                limits=robot.data.soft_joint_pos_limits[:,c.joint_ids]
                desired[:,c.action_slots]=torch.maximum(torch.minimum(desired[:,c.action_slots],limits[...,1]-.01),limits[...,0]+.01)
            bounded=torch.tensor(self.hold_reference.advance(desired[0].tolist()),device=self._env.device)[None]
            self._raw[:]=actions
            hold_commands=(bounded-robot.data.default_joint_pos[:,ids])/c.scale
            self.joint_commands[:]=hold_commands
            if getattr(self,'push_active',False) and not (getattr(self,'exit_hold',False) or getattr(self,'exit_brake_hold',False)):
                # Native v212 arm, policy and legal-contact release computation.
                # Its leg commands already include original release ramp.
                super().process_actions(actions)
                blend=c.leg_release_blend[:,None].clone()
                if bool((blend>0.).any()) and not hasattr(self,'push_release_hold_commands'):
                    self.push_release_hold_commands=hold_commands[:,c.leg_slots].clone()
                release_hold=self.push_release_hold_commands if hasattr(self,'push_release_hold_commands') else hold_commands[:,c.leg_slots]
                self.joint_commands[:,c.leg_slots]+=(1.-blend)*release_hold
                if bool((blend>=1.-1e-6).all()):self.push_legs_taken_over=True
            self.delegate.process_actions(self.joint_commands)
        elif age < 2.0:
            super().process_actions(actions)
        else:
            if not hasattr(self,'nav_entry_reference'):
                self.nav_entry_reference=current.clone()
                velocity=((current-self.previous_target)/self._env.step_dt)[0,c.action_slots].tolist()
                self.arm_reference_limiter=BoundedReference(current[0,c.action_slots].tolist(),velocity,[.45]*6,[1.]*6,self._env.step_dt)
            self._raw[:]=actions
            desired=robot.data.default_joint_pos[:,ids]+c.scale*actions[:,:18]
            u=min(1.,(age-2.)/1.0);blend=u*u*(3.-2.*u)
            desired=self.nav_entry_reference+blend*(desired-self.nav_entry_reference)
            # Explicit transition adapter: frozen NAV legs, bounded PUSH entry arm.
            # Keep native NAV evaluation/actual 18-axis command history unchanged.
            gravity=robot.root_physx_view.get_gravity_compensation_forces()
            columns=c.joint_ids if gravity.shape[1]==robot.num_joints else c.jacobian_columns
            desired[:,c.action_slots]=c.safe_approach_waypoints[0]+gravity[:,columns]/c.stiffness
            limits=robot.data.soft_joint_pos_limits[:,c.joint_ids]
            desired[:,c.action_slots]=torch.maximum(torch.minimum(desired[:,c.action_slots],limits[...,1]-.01),limits[...,0]+.01)
            bounded=torch.tensor(self.arm_reference_limiter.advance(desired[0,c.action_slots].tolist()),device=self._env.device)
            desired[0,c.action_slots]=bounded
            if age>=8.:
                # Transition-specific loading aid after normal capture failed.
                # Do not filter the other native NAV leg commands or fake contact.
                if not hasattr(self,'load_prepare_model'):
                    self.load_prepare_model=LegKinematics.from_usd(self._env.cfg.scene.robot.spawn.usd_path,device=self._env.device).reordered(('FR','FL','RR','RL'))
                    sensor=self._env.scene['contact_forces']
                    self.load_prepare_contact_ids=sensor.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0]
                    self.load_prepare_foot=int(sensor.data.net_forces_w[0,self.load_prepare_contact_ids,2].argmin())
                    self.load_prepare_depth=0.
                normal=float(self._env.scene['contact_forces'].data.net_forces_w[0,self.load_prepare_contact_ids[self.load_prepare_foot],2])
                rate=max(-.005,min(.005,.0005*(12.-normal)))
                self.load_prepare_depth=max(0.,min(.015,self.load_prepare_depth+rate*self._env.step_dt))
                native_q=desired[:,c.leg_slots].reshape(1,4,3)
                foot_targets=self.load_prepare_model.forward(native_q)
                foot_targets[:,self.load_prepare_foot,2]-=self.load_prepare_depth
                prepared=self.load_prepare_model.inverse(foot_targets)
                if float((self.load_prepare_model.forward(prepared)-foot_targets).norm(dim=-1).max())>.001:
                    raise ValueError('Loading aid IK infeasible')
                # Only the selected leg receives the offset; other leg targets exact.
                native_q[:,self.load_prepare_foot]=prepared[:,self.load_prepare_foot]
                limits=robot.data.soft_joint_pos_limits[:,[ids[i] for i in c.leg_slots]]
                prepared=native_q.reshape(1,12)
                if bool(((prepared<limits[...,0])|(prepared>limits[...,1])).any()):
                    raise ValueError('Loading aid exceeds original soft limits')
                desired[:,c.leg_slots]=prepared
            self.joint_commands[:]=(desired-robot.data.default_joint_pos[:,ids])/c.scale
            self.delegate.process_actions(self.joint_commands)
        self.previous_target=current


def nav_command(env):
    term=env.action_manager.get_term('joint_pos')
    if getattr(term,'return_nav_requested',False):
        if not getattr(term,'return_nav_active',False) or float(env.episode_length_buf[0])*env.step_dt-term.return_nav_requested_age<1.06:
            return torch.zeros((env.num_envs,3),device=env.device)
        robot=env.scene['robot'];w,x,y,z=robot.data.root_quat_w.unbind(-1)
        yaw=torch.atan2(2*(w*z+x*y),1.-2*(y*y+z*z))
        error=term.return_nav_goal[:,:2]-robot.data.root_pos_w[:,:2]
        relative=quat_mul(quat_conjugate(term.return_nav_orientation),robot.data.root_quat_w)
        yaw_error=2.*torch.atan2(relative[:,3],relative[:,0])
        # Separate development diagnosis of the small-command static equilibrium.
        # Preserve zero-command takeover, then ramp velocity request at0.10m/s^2.
        elapsed=max(0.,float(env.episode_length_buf[0])*env.step_dt-term.return_nav_requested_age-1.06)
        cap=min(.25,.10*elapsed)
        # Same bounded integral used by the validated NAV entry controller.
        # Integrate actual target error once per physical control step; logs may
        # call this function again without changing the command history/state.
        step=int(env.episode_length_buf[0])
        if not hasattr(term,'return_position_integral'):
            term.return_position_integral=torch.zeros_like(error)
            term.return_integral_step=step
        near=error.norm(dim=1)<.04
        if step>term.return_integral_step:
            term.return_position_integral=(term.return_position_integral+.4*error*env.step_dt).clamp(-.08,.08)
            term.return_position_integral[near]=0.
            term.return_integral_step=step
        world=1.2*error+term.return_position_integral
        vx=world[:,0]*torch.cos(yaw)+world[:,1]*torch.sin(yaw)
        vy=-world[:,0]*torch.sin(yaw)+world[:,1]*torch.cos(yaw)
        return torch.stack((torch.where(near,0.,vx.clamp(-cap,cap)),torch.where(near,0.,vy.clamp(-.08,.08)),torch.where(yaw_error.abs()<.04,0.,(-yaw_error*1.2).clamp(-.25,.25))),dim=1)
    if not getattr(term,'native_nav_ready',False):return torch.zeros((env.num_envs,3),device=env.device)
    r=env.scene['robot'];pos=r.data.root_pos_w-env.scene.env_origins
    w,x,y,z=r.data.root_quat_w.unbind(-1)
    yaw=torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
    world=-pos[:,:2]
    c,s=torch.cos(yaw),torch.sin(yaw)
    step=int(env.episode_length_buf[0])
    if not hasattr(env,'nav_position_integral'):
        env.nav_position_integral=torch.zeros_like(world);env.nav_integral_step=step
    if step>env.nav_integral_step and step>100:
        env.nav_position_integral=(env.nav_position_integral+.4*world*env.step_dt).clamp(-.08,.08)
    env.nav_integral_step=step
    trim=env.nav_position_integral
    vx=(world[:,0]*c+world[:,1]*s)*1.2+trim[:,0]*c+trim[:,1]*s
    vy=(-world[:,0]*s+world[:,1]*c)*1.2-trim[:,0]*s+trim[:,1]*c
    # Approach planner lateral deadband uses the original50mm entry region.
    # Exact final XY norm, four-foot/wrench capture, and READY gates remain.
    vy=torch.where(pos[:,1].abs()<.05,torch.zeros_like(vy),vy)
    # Begin explicit braking on entry into the existing80mm parking domain.
    # Preserve rate limits, intermediate90mm capture and final50mm READY.
    if not getattr(env.action_manager.get_term('joint_pos'),'request_hold',False) and not hasattr(env,'late_stop_requested') and float(world.norm())<.08:
        env.late_stop_requested=True
    if getattr(env,'late_stop_requested',False):
        return bounded_nav_request(env,torch.stack((torch.zeros_like(yaw),torch.zeros_like(yaw),torch.where(yaw.abs()<.12,0.,(-yaw*1.2).clamp(-.25,.25))),dim=1))
    near=world.norm(dim=1)<.04
    # Approach-level braking envelope from existing0.10m/s^2 request slew.
    # Begin reducing forward request before the original40mm stop domain.
    # Native18 feedback, physical gates and the slew limiter remain unchanged.
    forward_distance=world[:,0]*c+world[:,1]*s
    forward_cap=torch.sqrt(2.*.10*(forward_distance-.04).clamp(min=0.)).clamp(max=.20)
    vx=torch.minimum(vx,forward_cap)
    return bounded_nav_request(env,torch.stack((torch.where(near,0.,vx.clamp(-.15,.20)),
                        torch.where(near,0.,vy.clamp(-.12,.12)),
                        torch.where(yaw.abs()<.04,0.,(-yaw*1.2).clamp(-.25,.25))),dim=1))


def nav_pose(env):
    if hasattr(env,'transition_arm_pose_command'):return env.transition_arm_pose_command
    return torch.tensor((.5,0.,.2,1.,0.,0.,0.),device=env.device).repeat(env.num_envs,1)

class TerminalStop(Exception): pass

def main():
    assert hashlib.sha256(a.nav_actor.read_bytes()).hexdigest()==NAV_SHA
    cfg=load_cfg_from_registry(TASK,'env_cfg_entry_point')
    cfg.scene.num_envs=1;cfg.seed=a.seed;cfg.sim.device=a.device
    cfg.episode_length_s=a.seconds
    configure(cfg,a,training=False)
    original_arm_effort_gate=cfg.terminations.arm_effort_safety.func
    def arm_effort_with_substeps(env):
        return original_arm_effort_gate(env) | getattr(env,'transition_substep_effort_violation',torch.zeros(env.num_envs,dtype=torch.bool,device=env.device))
    cfg.terminations.arm_effort_safety.func=arm_effort_with_substeps
    cfg.actions.joint_pos.class_type=Router
    assert cfg.terminations.box_settled.func is PushSettled
    cfg.terminations.box_settled.func=PushSettledEvent
    cfg.scene.robot.init_state.pos=(-.25,0.,.33)
    cfg.observations.nav_policy=copy.deepcopy(cfg.observations.policy)
    cfg.observations.nav_policy.velocity_commands.func=nav_command
    cfg.observations.nav_policy.velocity_commands.params={}
    cfg.observations.nav_policy.pos_commands.func=nav_pose
    cfg.observations.nav_policy.pos_commands.params={}
    # Rewards are not used in this observation/control probe; do not run reward-only state updates.
    for name in vars(cfg.rewards):
        term=getattr(cfg.rewards,name)
        if hasattr(term,'weight'):term.weight=0.
    env=gym.make(TASK,cfg=cfg);b=env.unwrapped
    obs,_=env.reset(seed=a.seed)
    verify_physics(b,a.output)
    term=b.action_manager.get_term('joint_pos');c=term.controller;r=b.scene['robot']
    # Consistent NAV task request for the persistent PUSH entry arm posture.
    # Capture after real reset; never use observation shape-inference state.
    mount=r.find_bodies('link0')[0][0];hand=r.find_bodies('end_effector')[0][0]
    position=quat_apply_inverse(r.data.body_quat_w[:,mount],r.data.body_pos_w[:,hand]-r.data.body_pos_w[:,mount])
    orientation=quat_mul(quat_conjugate(r.data.root_quat_w),r.data.body_quat_w[:,hand])
    orientation=torch.where(orientation[:,:1]<0.,-orientation,orientation)
    b.transition_arm_pose_command=torch.tensor((.5,0.,.2,1.,0.,0.,0.),device=b.device).repeat(b.num_envs,1)
    assert torch.allclose(r.data.joint_pos[:,c.joint_ids],c.safe_approach_waypoints[0][None],atol=1e-5)
    (a.output/'nav-arm-pose-command.json').write_text(json.dumps(dict(command=b.transition_arm_pose_command.tolist()),indent=2)+'\n')
    ids=r.find_joints(cfg.actions.joint_pos.joint_names,preserve_order=True)[0]
    feet=SceneEntityCfg('contact_forces',body_names='.*_foot');feet.resolve(b.scene)
    joint_names=tuple(r.joint_names[i] for i in ids)
    leg_ids=[ids[i] for i in c.leg_slots]
    def serial(v):
        return v.tolist() if hasattr(v,'tolist') else str(v)
    audit=dict(joint_names=r.joint_names,default_joint_pos=serial(r.data.default_joint_pos),soft_joint_limits=serial(r.data.soft_joint_pos_limits),actuators={})
    for key,act in r.actuators.items():
        audit['actuators'][key]={k:serial(getattr(act,k,None)) for k in ('joint_indices','stiffness','damping','effort_limit','velocity_limit')}
    (a.output/'actuator-contract.json').write_text(json.dumps(audit,indent=2)+'\n')
    checkpoint=Path(os.environ["PIPER_PUSH_CHECKPOINT"])
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='4d1a4616928b4d06002285e870a1d6dd114e27b8cafcdd9a41dbdae1aceed419'
    actor=actor_from_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=False)['actor_state_dict'],device=a.device)
    install_frozen_legs(actor)
    nav_actor=torch.jit.load(str(a.nav_actor),map_location=a.device).eval()
    report=dict(scope='Used-start v317 box-aware frozen approach tip-envelope standoff during existing loaded final centering; nominal path+boundedresidual static preview and measured final recheck, original safety/budgets unchanged; not acceptance',
                seed=a.seed,source=str(a.source),nav_sha256=NAV_SHA,
                robot_initial_position=list(cfg.scene.robot.init_state.pos),
                control_dt=b.step_dt,events=[],terminal={},physical_resets_after_initial=0,
                native_safety_terms=list(b.termination_manager.active_terms),joint_names=joint_names,body_names=b.scene['contact_forces'].body_names,
                outcome='incomplete',samples=0,max_target_step_rad=0.,
                minimum_clearance_m=None,max_torque_ratio=0.,max_substep_arm_torque_ratio=0.,
                airborne_samples=0,under_three_support_samples=0,max_abs_vz_m_s=0.,
                max_single_foot_N=0.,max_sum_foot_force_norm_N=0.,effort_over_098_samples=0,
                source_inventory_verified=True)
    gates_required=('controller_transfer_complete','position','orientation','velocity','four_loaded_feet','joint_speed','arm_entry','soft_limits','clearance','effort')
    handoff=Handoff('NAV','PUSH-v212',gates_required)
    capture_mass=r.root_physx_view.get_masses().to(b.device)
    capture_feet=r.find_bodies(['FR_foot','FL_foot','RR_foot','RL_foot'],preserve_order=True)[0]
    nav_stable=0.
    retract_stable=0.
    exit_stable=0.
    capture_stable=0.
    hold_stable=0.
    entry_arm_settled=0.
    stable=0.;previous_target=r.data.joint_pos_target[0,ids].clone()
    def snapshot():
        v=physical_sample(b)
        pos=r.data.root_pos_w[0]-b.scene.env_origins[0];w,x,y,z=r.data.root_quat_w[0]
        yaw=torch.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
        limits=r.data.soft_joint_pos_limits[0,ids];targets=r.data.joint_pos_target[0,ids]
        forces=b.scene['contact_forces'].data.net_forces_w[0,feet.body_ids]
        gates=dict(controller_transfer_complete=bool(hasattr(term,'hold_start_age') and int(b.episode_length_buf[0])*b.step_dt-term.hold_start_age>=4.5),
                   position=bool(pos[:2].norm()<.05),
                   orientation=bool(yaw.abs()<.12 and r.data.projected_gravity_b[0,2]<-.98),
                   velocity=bool(r.data.root_lin_vel_w[0].norm()<.025 and r.data.root_ang_vel_w[0].norm()<.1),
                   four_loaded_feet=bool((forces[:,2]>=8.).all()),
                   joint_speed=bool(r.data.joint_vel[0,leg_ids].abs().max()<.35 and r.data.joint_vel[0,c.joint_ids].abs().max()<.2),
                   arm_entry=bool((r.data.joint_pos[0,c.joint_ids]-c.safe_approach_waypoints[0]).abs().max()<.1),
                   soft_limits=bool(((targets>=limits[:,0])&(targets<=limits[:,1])).all()),
                   clearance=bool(v['clearance'][0]>=.035),effort=bool(v['arm_ratio'][0]<.98))
        row=dict(step=int(b.episode_length_buf[0]),time_s=int(b.episode_length_buf[0])*b.step_dt,
                 root_position=pos.tolist(),root_quaternion=r.data.root_quat_w[0].tolist(),
                 root_velocity=r.data.root_lin_vel_w[0].tolist(),root_angular_velocity=r.data.root_ang_vel_w[0].tolist(),
                 q=r.data.joint_pos[0,ids].tolist(),dq=r.data.joint_vel[0,ids].tolist(),
                 pd_target=targets.tolist(),torque=r.data.applied_torque[0,ids].tolist(),
                 foot_forces=forces.tolist(),gates=gates,clearance_m=float(v['clearance'][0]),
                 torque_ratio=float(v['ratio'][0]),body_forces=b.scene['contact_forces'].data.net_forces_w[0].tolist(),history_valid_frames=min(3,int(b.episode_length_buf[0])+1))
        report['samples']+=1
        report['minimum_clearance_m']=min(row['clearance_m'],report['minimum_clearance_m'] if report['minimum_clearance_m'] is not None else row['clearance_m'])
        report['max_torque_ratio']=max(report['max_torque_ratio'],row['torque_ratio'])
        report['airborne_samples']+=int(v['support'][0]==0);report['under_three_support_samples']+=int(v['support'][0]<3)
        report['effort_over_098_samples']+=int(v['ratio'][0]>=.98)
        report['max_abs_vz_m_s']=max(report['max_abs_vz_m_s'],float(v['vz'][0]))
        report['max_single_foot_N']=max(report['max_single_foot_N'],float(v['force'][0]))
        report['max_sum_foot_force_norm_N']=max(report['max_sum_foot_force_norm_N'],float(v['force_sum'][0]))
        return row
    def entry(row):
        return EntryState(row['step'],row['time_s'],joint_names,tuple(row['q']),tuple(row['dq']),
                          tuple(row['pd_target']),tuple(row['torque']),row['history_valid_frames'],
                          'v212-nav-legs-push-entry-arm-v317','box0',row['gates'],stable)
    def stop_before_reset(env_ids,*args,**kwargs):
        if len(env_ids):
            report['terminal']={name:bool(b.termination_manager.get_term(name)[0]) for name in b.termination_manager.active_terms}
            raise TerminalStop()
    b.recorder_manager.record_pre_reset=stop_before_reset
    original_update=b.scene.update
    def measured_update(dt):
        original_update(dt)
        ratio=(r.data.applied_torque[0,c.joint_ids].abs()/r.data.joint_effort_limits[0,c.joint_ids]).max()
        report['max_substep_arm_torque_ratio']=max(report['max_substep_arm_torque_ratio'],float(ratio))
        report['physics_samples']=report.get('physics_samples',0)+1
        if float(ratio)>=.98:
            b.transition_substep_effort_violation=torch.ones(b.num_envs,dtype=torch.bool,device=b.device)
            if 'first_substep_arm_effort_violation' not in report:
                actual=r.data.applied_torque[0,c.joint_ids]
                report['first_substep_arm_effort_violation']=dict(physics_sample=report['physics_samples'],physical_elapsed_s=report['physics_samples']*dt,control_step=int(b.episode_length_buf[0]),joint_names=[r.joint_names[i] for i in c.joint_ids],q=r.data.joint_pos[0,c.joint_ids].tolist(),dq=r.data.joint_vel[0,c.joint_ids].tolist(),pd_target=r.data.joint_pos_target[0,c.joint_ids].tolist(),torque=actual.tolist(),effort_limits=r.data.joint_effort_limits[0,c.joint_ids].tolist(),ratio=float(ratio))
    b.scene.update=measured_update
    log=(a.output/'control.jsonl').open('x')
    first=snapshot();handoff.begin(entry(first))
    log.write(json.dumps(first)+'\n')
    try:
        with torch.inference_mode():
            for step in range(round(a.seconds/b.step_dt)):
                assert obs['policy'].shape==(1,210)
                if getattr(term,'return_nav_requested',False) and not getattr(term,'return_nav_arrival_brake',False) and step*b.step_dt-term.return_nav_requested_age>=.06:
                    if not getattr(term,'return_nav_active',False):
                        term.return_nav_active=True
                        report.setdefault('control_events',[]).append(dict(event='return_nav_activated_after_three_real_history_frames',step=step,time_s=step*b.step_dt))
                    native=nav_actor(obs['nav_policy']).clamp(-10.,10.)
                    assert native.shape==(1,18)
                    action=torch.zeros((1,19),device=a.device);action[:,:18]=native
                elif step < 100 or getattr(term,'push_active',False):
                    native=actor(torch.cat((obs['policy'],obs['box']),dim=-1))
                    assert native.shape==(1,19)
                    action=native
                else:
                    native=nav_actor(obs['nav_policy']).clamp(-10.,10.)
                    assert native.shape==(1,18)
                    action=torch.zeros((1,19),device=a.device);action[:,:18]=native
                entry_nav_input=obs['nav_policy'][0].tolist()
                nav_input=obs['nav_policy'][0].tolist() if getattr(term,'return_nav_requested',False) else None
                terminal=False
                try:obs,_,_,_,_=env.step(action)
                except TerminalStop:terminal=True
                row=snapshot();row['native_action']=native[0].tolist();row['phase']='native_nav' if term.native_pass_through else 'nav_initialization_transition';row['applied_joint_command']=term.joint_commands[0].tolist()
                if nav_input is not None:row['return_nav_actor_input']=nav_input;row['return_nav_velocity_request']=nav_command(b)[0].tolist()
                if hasattr(term,'native_arm_guard') and not getattr(term,'request_hold',False) and not getattr(term,'return_nav_requested',False):
                    row['entry_nav_actor_input']=entry_nav_input
                    row['native_arm_effort_guard']=getattr(term,'native_arm_guard',None)
                    row['native_command_error']=float((native[0,:18]-term.joint_commands[0]).abs().max())
                    if row['native_arm_effort_guard'] and row['native_arm_effort_guard']['changed']:
                        row['phase']='native_nav_with_arm_effort_guard'
                    assert torch.equal(native[0,c.leg_slots],term.joint_commands[0,c.leg_slots])
                if term.native_pass_through:
                    row['entry_nav_actor_input']=entry_nav_input
                    row['native_command_error']=float((native[0,:18]-term.joint_commands[0]).abs().max())
                    assert row['native_command_error']==0.
                row['entry_arm_geometry_blocked']=getattr(term,'entry_arm_geometry_blocked',False)
                target=r.data.joint_pos_target[0,ids].clone()
                report['max_target_step_rad']=max(report['max_target_step_rad'],float((target-previous_target).abs().max()))
                reference_speed=float(((target-previous_target)/b.step_dt).abs().max())
                previous_target=target
                base_gates=('position','orientation','velocity','four_loaded_feet','soft_limits','clearance','effort')
                capture_ok=(step>=100 and term.native_pass_through and (row['gates']['position'] or (getattr(b,'late_stop_requested',False) and sum(v*v for v in row['root_position'][:2])<.09**2))
                            and all(row['gates'][k] for k in ('orientation','four_loaded_feet','soft_limits','clearance','effort'))
                            and sum(x*x for x in row['root_velocity'])<.04**2 and sum(x*x for x in row['root_angular_velocity'])<.2**2
                            and min(f[2] for f in row['foot_forces'])>=12.
                            and abs(row['root_velocity'][2])<.025 and abs(row['root_angular_velocity'][2])<.1
                            and max(abs(x) for x in row['dq'][:12])<.95
                            and max(abs(x) for x in row['dq'][12:])<.2 and reference_speed<4.5)
                # Pre-READY supported braking: preserve all other capture checks.
                # Actual arm speed<0.35 leaves margin below reference0.45 limit.
                entry_brake_ok=(not capture_ok) and (step>=100 and term.native_pass_through and (row['gates']['position'] or (getattr(b,'late_stop_requested',False) and sum(v*v for v in row['root_position'][:2])<.09**2))
                            and all(row['gates'][k] for k in ('orientation','four_loaded_feet','soft_limits','clearance','effort'))
                            and sum(x*x for x in row['root_velocity'])<.04**2 and sum(x*x for x in row['root_angular_velocity'])<.2**2
                            and min(f[2] for f in row['foot_forces'])>=12.
                            and abs(row['root_velocity'][2])<.025 and abs(row['root_angular_velocity'][2])<.1
                            and max(abs(x) for x in row['dq'][:12])<.95
                            and max(abs(x) for x in row['dq'][12:])<.35 and reference_speed<4.5)
                native_settled=bool(getattr(b,'transition_native_push_settled',torch.zeros(1,dtype=torch.bool,device=b.device))[0])
                if native_settled and not terminal and getattr(term,'push_active',False) and not getattr(term,'exit_requested',False):
                    term.exit_requested=True
                    # Retraction and NAV retain the v270 geometry contract; the
                    # ingress-only reserve and stance shift must not leak into exit.
                    c.geometry_shield.transition_planning_reserve_m=0.
                    term.exit_request_position=r.data.root_pos_w.clone()
                    term.exit_request_orientation=r.data.root_quat_w.clone()
                    report['push_settled_time_s']=row['time_s']
                    report['push_settled_state']=row
                    report.setdefault('control_events',[]).append(dict(event='native_push_settled_exit_requested',step=row['step'],time_s=row['time_s']))
                if getattr(term,'exit_requested',False) and not getattr(term,'exit_hold',False):
                    relative=quat_mul(quat_conjugate(term.exit_request_orientation),r.data.root_quat_w)
                    relative_yaw=2.*torch.atan2(relative[0,3],relative[0,0])
                    row['exit_capture_gates']=dict(
                        position=bool((r.data.root_pos_w[0,:2]-term.exit_request_position[0,:2]).norm()<.12),
                        orientation=bool(r.data.projected_gravity_b[0,2]<-.98 and relative_yaw.abs()<.12),
                        speed=sum(v*v for v in row['root_velocity'])<.04**2,
                        angular_speed=sum(v*v for v in row['root_angular_velocity'])<.2**2,
                        normal_load=min(f[2] for f in row['foot_forces'])>=12.,
                        vertical_speed=abs(row['root_velocity'][2])<.025,
                        yaw_speed=abs(row['root_angular_velocity'][2])<.1,
                        joint_speed=max(abs(v) for v in row['dq'][:12])<.95 and max(abs(v) for v in row['dq'][12:])<.2,
                        reference_speed=reference_speed<4.5,
                        hand_unloaded=not bool(_push_ik.hand_contact(b,c.hand_cfg)[0]),
                        soft_limits=row['gates']['soft_limits'],clearance=row['gates']['clearance'],effort=row['gates']['effort'])
                    capture_ok=all(row['exit_capture_gates'].values())
                brake_ok=False
                if getattr(term,'exit_requested',False) and not getattr(term,'exit_brake_hold',False) and not getattr(term,'exit_hold',False):
                    gates=row['exit_capture_gates']
                    brake_ok=all(gates[k] for k in ('position','orientation','normal_load','vertical_speed','hand_unloaded','soft_limits','clearance','effort'))
                    # Bounded dynamic braking domain, separate from unchanged READY capture.
                    brake_ok=brake_ok and sum(v*v for v in row['root_velocity'])<.15**2 and sum(v*v for v in row['root_angular_velocity'])<.6**2
                    row['exit_brake_precheck']=brake_ok
                original_capture_ok=capture_ok
                if capture_ok or brake_ok or entry_brake_ok:
                    # Select a low-momentum gait phase only when a braking wrench
                    # has force/friction and actuator reserve at the actual pose.
                    com=(r.data.body_com_pos_w*capture_mass[:,:,None]).sum(1)/capture_mass.sum(1)[:,None]
                    accel=-5.*r.data.root_lin_vel_w
                    accel[:,2]=-8.*r.data.root_lin_vel_w[:,2]
                    force=capture_mass.sum(1)[:,None]*(accel.clamp(-.5,.5)+torch.tensor([0.,0.,9.81],device=b.device))
                    moment=(-2.*r.data.root_ang_vel_w).clamp(-4.,4.)
                    loads,residual=allocate_wrench(r.data.body_pos_w[:,capture_feet],com,force,moment,minimum_normal=12.,friction=.3)
                    feasible=bool(residual[:,:3].abs().max()<=.5 and residual[:,3:].abs().max()<=.1)
                    jacobians=r.root_physx_view.get_jacobians();gravity=r.root_physx_view.get_gravity_compensation_forces()
                    offset=0 if r.is_fixed_base else 6;ratios=[]
                    for leg,body in enumerate(capture_feet):
                        jid=leg_ids[leg*3:leg*3+3]
                        jac=jacobians[:,body-(1 if r.is_fixed_base else 0),:3][:,:,[i+offset for i in jid]]
                        columns=jid if gravity.shape[1]==r.num_joints else [i+offset for i in jid]
                        torque=gravity[:,columns]-(jac.transpose(1,2)@loads[:,leg,:,None]).squeeze(-1)
                        ratios.append((torque.abs()/r.data.joint_effort_limits[:,jid]).max())
                    effort_ratio=float(torch.stack(ratios).max())
                    capture_ok=original_capture_ok and feasible and effort_ratio<.75
                    brake_ok=brake_ok and feasible and effort_ratio<.75
                    entry_brake_ok=entry_brake_ok and feasible and effort_ratio<.75
                    row['capture_wrench_reserve']=dict(feasible=feasible,effort_ratio=effort_ratio,residual=residual[0].tolist(),loads=loads[0].tolist(),center_of_mass=com[0].tolist())
                row['entry_braking_precheck']=entry_brake_ok
                if entry_brake_ok and not getattr(term,'request_hold',False):
                    term.request_hold=True
                    term.entry_brake_hold=True
                    report.setdefault('control_events',[]).append(dict(event='entry_supported_braking_started_not_ready',step=row['step'],time_s=row['time_s']))
                row['entry_brake_hold']=getattr(term,'entry_brake_hold',False)
                if brake_ok:
                    term.exit_brake_hold=True
                    term.push_legs_taken_over=False
                    term.exit_arm_pose=r.data.joint_pos[:,c.joint_ids].clone()
                    if hasattr(term,'hold_reference'):del term.hold_reference
                    report.setdefault('control_events',[]).append(dict(event='exit_four_contact_braking_started_not_ready',step=row['step'],time_s=row['time_s']))
                capture_stable=capture_stable+b.step_dt if capture_ok else 0.
                row['late_stop_requested']=getattr(b,'late_stop_requested',False)
                row['capture_candidate_seconds']=capture_stable
                if capture_stable>=.02 and getattr(term,'exit_requested',False) and not getattr(term,'exit_hold',False):
                    term.exit_hold=True
                    term.push_legs_taken_over=False
                    term.exit_arm_pose=r.data.joint_pos[:,c.joint_ids].clone()
                    if not getattr(term,'exit_brake_hold',False) and hasattr(term,'hold_reference'):del term.hold_reference
                    report.setdefault('control_events',[]).append(dict(event='exit_loaded_hold_requested',step=row['step'],time_s=row['time_s']))
                if capture_stable>=.02 and not getattr(term,'request_hold',False):
                    term.request_hold=True
                    report.setdefault('control_events',[]).append(dict(event='loaded_hold_requested',step=row['step'],time_s=row['time_s'],reference_speed_rad_s=reference_speed))
                if hasattr(term,'hold_reference'):
                    row['phase']='arm_prepare' if term.prepare_arm else 'loaded_hold';row['stance_geometry_error_m']=getattr(term,'stance_geometry_error',None)
                    if hasattr(term,'stance_loads'):row.update(allocated_support_forces=term.stance_loads[0].tolist(),allocated_wrench_residual=term.stance_wrench_residual[0].tolist(),center_of_mass=term.stance_com[0].tolist())
                    row.update(stance_orientation_target=term.stance_orientation_target[0].tolist(),stance_angular_velocity_target=term.stance_angular_velocity_target[0].tolist())
                    row['stance_wrench_fallback']=getattr(term,'stance_wrench_fallback',None)
                    row.update(stance_unbounded_target=term.stance_desired[0].tolist(),stance_cartesian_correction=term.stance_correction[0].tolist(),stance_wrench_target=term.stance_wrench_target[0].tolist(),stance_position_target=term.stance_position_target[0].tolist(),stance_velocity_target=term.stance_velocity_target[0].tolist())
                    initial_center_complete=row['time_s']-term.hold_start_age>=4.5
                    hold_stable=hold_stable+b.step_dt if initial_center_complete and all(row['gates'][k] for k in base_gates+('joint_speed',)) else 0.
                    if hold_stable>=.5 and not term.prepare_arm:
                        term.prepare_arm=True
                        report.setdefault('control_events',[]).append(dict(event='loaded_hold_stable_arm_prepare',step=row['step'],time_s=row['time_s']))
                if hasattr(term,'hold_reference') and not getattr(term,'exit_requested',False) and not getattr(term,'return_nav_requested',False):
                    arm_stopped=term.prepare_arm and initial_center_complete and all(row['gates'][k] for k in base_gates+('joint_speed','arm_entry'))
                    entry_arm_settled=entry_arm_settled+b.step_dt if arm_stopped else 0.
                    if entry_arm_settled>=.5 and not hasattr(term,'entry_final_center_start_age'):
                        # Forecast at the fully centered reference, preserving the
                        # current tracking offset. Source geometry is checked before
                        # this translation; final measured path feasibility is checked
                        # again before READY. This is not itself safety evidence.
                        translation=torch.zeros_like(r.data.root_pos_w)
                        translation[:,:2]=b.scene.env_origins[:,:2]-term.stance_position_target[:,:2]
                        plan=prospective_entry(c,r,ids,joint_names,reserve_for_late_parking=getattr(b,'late_stop_requested',False),nominal_translation_w=translation[0].cpu().numpy())
                        term.prospective_shift_m=plan['shift_m']
                        term.support_extension_required=getattr(b,'late_stop_requested',False) and plan['support_only_shift_m']>=.015-1e-9
                        term.push_support_shift_m=plan['push_support_shift_m'] if term.support_extension_required else term.prospective_shift_m
                        term.entry_support_integrated=True
                        term.prospective_start_age=row['time_s']
                        c.geometry_shield.transition_planning_reserve_m=0.
                        report['planning_reserve_m']=c.geometry_shield.transition_planning_reserve_m
                        if plan['support_only_shift_m']>0.:
                            b.cfg.push_hand_height_offset=-.01
                            report['prepared_stance_hand_height_offset_m']=-.01
                        report['prospective_support_plan']=plan
                        report.setdefault('control_events',[]).append(dict(event='prospective_support_integrated_into_final_center',step=row['step'],time_s=row['time_s'],shift_m=term.prospective_shift_m))
                        term.entry_final_center_start_age=row['time_s']
                        report.setdefault('control_events',[]).append(dict(event='push_arm_loaded_stable_final_center_started',step=row['step'],time_s=row['time_s']))
                    final_center_duration=4. if getattr(term,'prospective_shift_m',0.)>0. else (0. if getattr(term,'entry_direct_center',False) else 3.)
                    final_center_complete=hasattr(term,'entry_final_center_start_age') and row['time_s']-term.entry_final_center_start_age>=final_center_duration
                    row['entry_center_stage']='final_center' if hasattr(term,'entry_final_center_start_age') else 'intermediate_center_arm_conversion'
                    row['entry_arm_settled_seconds']=entry_arm_settled
                    row['entry_direct_center']=getattr(term,'entry_direct_center',False)
                    row['entry_direct_center_preview']=getattr(term,'entry_direct_center_preview',None)
                    row['gates']['controller_transfer_complete']=row['gates']['controller_transfer_complete'] and final_center_complete
                if not getattr(term,'exit_requested',False) and getattr(term,'prospective_shift_m',0.)>0. and row['time_s']-term.prospective_start_age<4.:
                    row['gates']['controller_transfer_complete']=False
                row['prospective_shift_m']=getattr(term,'prospective_shift_m',0.)
                stable=stable+b.step_dt if all(row['gates'].values()) else 0.
                if hasattr(term,'load_prepare_depth'):row['load_preparation']=dict(foot=('FR','FL','RR','RL')[term.load_prepare_foot],depth_m=term.load_prepare_depth)
                row['stable_seconds']=stable
                row['push_active']=getattr(term,'push_active',False)
                row['push_legs_taken_over']=getattr(term,'push_legs_taken_over',False)
                row['release_uses_stance_snapshot']=hasattr(term,'push_release_hold_commands') and not getattr(term,'exit_requested',False)
                if row['push_active']:
                    row['phase']='push_v212' if row['push_legs_taken_over'] else 'push_loaded_stance'
                    box=b.scene['box']
                    row['push']=dict(local_time_s=row['time_s']-report['push_activation_time_s'],
                        safe_approach_complete=bool(c.safe_approach_complete[0]),
                        motion_ready=bool(c.motion_ready[0]),legal_hand_contact=bool(_push_ik.hand_contact(b,c.hand_cfg)[0]),
                        leg_release_blend=float(c.leg_release_blend[0]),
                        box_position=box.data.root_pos_w[0].tolist(),box_velocity=box.data.root_lin_vel_w[0].tolist(),
                        arm_reference=c.reference[0].tolist(),arm_compensated_reference=c.last_compensated_reference[0].tolist())
                if row['push_active']:
                    contact_sensor=b.scene.sensors['box_contact_hand']
                    box=b.scene['box']
                    contact=contact_sensor.data.contact_pos_w[:,0,0]
                    finite=torch.isfinite(contact).all(dim=1)
                    force=contact_sensor.data.force_matrix_w.sum(dim=(1,2))
                    local=quat_apply_inverse(box.data.root_quat_w,torch.nan_to_num(contact)-box.data.root_pos_w)
                    hand_position=r.data.body_pos_w[:,c.hand_cfg.body_ids[0]]
                    relative=quat_apply_inverse(r.data.root_quat_w,hand_position-r.data.root_pos_w)
                    row['box_hand_contact_diagnostic']=dict(
                        force_w=force[0].tolist(),force_norm_N=float(force[0].norm()),
                        contact_w=contact[0].tolist() if bool(finite[0]) else None,
                        contact_box_local=local[0].tolist() if bool(finite[0]) else None,
                        contact_finite=bool(finite[0]),hand_position_w=hand_position[0].tolist(),
                        hand_position_root=relative[0].tolist(),tip_distance_m=float((torch.nan_to_num(contact)-hand_position)[0].norm()) if bool(finite[0]) else None,
                        tip_radius_m=getattr(b.cfg,'push_contact_tip_radius',.07),height_margin_m=getattr(b.cfg,'push_contact_height_margin',.01),
                        box_size=list(b.cfg.box_size),leg_contact_latched=bool(c.leg_contact_ready[0]),
                        motion_ready=bool(c.motion_ready[0]),leg_release_blend=float(c.leg_release_blend[0]))
                if getattr(term,'push_active',False):
                    row['shield_diagnostic']={name:getattr(c,name)[0].tolist() for name in (
                        'debug_reference_pre_geometry','debug_reference_post_geometry','debug_arm_velocity',
                        'debug_predicted_clearance','geometry_clearance','geometry_blocked','clearance_correction',
                        'safe_approach_complete','approach_face_ready','motion_ready','leg_release_blend')}
                row['native_push_settled']=native_settled
                row['exit_requested']=getattr(term,'exit_requested',False)
                row['exit_hold']=getattr(term,'exit_hold',False)
                row['exit_brake_hold']=getattr(term,'exit_brake_hold',False)
                hand_contact_id=b.scene['contact_forces'].find_bodies('end_effector')[0][0]
                row['hand_force_norm_N']=float(b.scene['contact_forces'].data.net_forces_w[0,hand_contact_id].norm())
                row['box_hand_force_norm_N']=float(b.scene.sensors['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2))[0].norm())
                if row['exit_hold'] and hasattr(term,'hold_reference'):
                    row['phase']='exit_loaded_hold_arm_extended'
                    row['exit_stable_gates']=dict(
                        transfer_complete=row['time_s']-term.hold_start_age>=.3,
                        position=bool((r.data.root_pos_w[0,:2]-term.stance_origin[0,:2]).norm()<.05),
                        orientation=bool(r.data.projected_gravity_b[0,2]<-.98),
                        velocity=row['gates']['velocity'],four_loaded_feet=row['gates']['four_loaded_feet'],
                        joint_speed=row['gates']['joint_speed'],soft_limits=row['gates']['soft_limits'],
                        clearance=row['gates']['clearance'],effort=row['gates']['effort'],
                        hand_unloaded=not row['push']['legal_hand_contact'],box_still_settled=native_settled)
                    exit_stable=exit_stable+b.step_dt if all(row['exit_stable_gates'].values()) else 0.
                    row['exit_stable_seconds']=exit_stable
                    if getattr(term,'exit_retract',False):
                        row['phase']='exit_arm_retract'
                        row['retraction']=dict(waypoint=getattr(term,'retract_index',0),reference=getattr(term,'retract_reference',term.exit_arm_pose)[0].tolist(),blocked=getattr(term,'retract_geometry_blocked',False),clearance_m=getattr(term,'retract_geometry_clearance',None))
                        arm_done=bool(getattr(term,'retract_index',0)>=2 and (r.data.joint_pos[0,c.joint_ids]-c.safe_approach_waypoints[0]).abs().max()<c.safe_approach_position_tolerance and r.data.joint_vel[0,c.joint_ids].abs().max()<c.safe_approach_velocity_tolerance)
                        row['retracted_ready']=arm_done and all(row['exit_stable_gates'].values())
                        retract_stable=retract_stable+b.step_dt if row['retracted_ready'] else 0.
                        row['retracted_ready_seconds']=retract_stable
                if getattr(term,'return_nav_requested',False):
                    goal_error=float((r.data.root_pos_w[0,:2]-term.return_nav_goal[0,:2]).norm())
                    travel=float((r.data.root_pos_w[0,:2]-term.return_nav_origin[0,:2]).norm())
                    relative=quat_mul(quat_conjugate(term.return_nav_orientation),r.data.root_quat_w)
                    heading_error=float((2.*torch.atan2(relative[0,3],relative[0,0])).abs())
                    row['phase']='return_nav_arrival_brake' if getattr(term,'return_nav_arrival_brake',False) else 'return_nav'
                    row['return_nav_arm_geometry_blocked']=getattr(term,'return_nav_arm_blocked',False)
                    row['return_nav']=dict(goal=term.return_nav_goal[0].tolist(),goal_error_m=goal_error,travel_m=travel,heading_error_rad=heading_error,active=getattr(term,'return_nav_active',False),arrival_brake=getattr(term,'return_nav_arrival_brake',False))
                    arrival=bool(getattr(term,'return_nav_active',False) and goal_error<.05 and heading_error<.12 and r.data.projected_gravity_b[0,2]<-.98 and travel>=.20 and min(f[2] for f in row['foot_forces'])>=12. and sum(v*v for v in row['root_velocity'])<.15**2 and sum(v*v for v in row['root_angular_velocity'])<.6**2 and all(row['gates'][k] for k in ('soft_limits','clearance','effort')) and not row['push']['legal_hand_contact'])
                    if arrival:
                        com=(r.data.body_com_pos_w*capture_mass[:,:,None]).sum(1)/capture_mass.sum(1)[:,None]
                        accel=-5.*r.data.root_lin_vel_w;accel[:,2]=-8.*r.data.root_lin_vel_w[:,2]
                        force=capture_mass.sum(1)[:,None]*(accel.clamp(-.5,.5)+torch.tensor([0.,0.,9.81],device=b.device))
                        moment=(-2.*r.data.root_ang_vel_w).clamp(-4.,4.)
                        loads,residual=allocate_wrench(r.data.body_pos_w[:,capture_feet],com,force,moment,minimum_normal=12.,friction=.3)
                        jacobians=r.root_physx_view.get_jacobians();gravity=r.root_physx_view.get_gravity_compensation_forces();offset=0 if r.is_fixed_base else 6;ratios=[]
                        for leg,body in enumerate(capture_feet):
                            jid=leg_ids[leg*3:leg*3+3];jac=jacobians[:,body-(1 if r.is_fixed_base else 0),:3][:,:,[i+offset for i in jid]]
                            columns=jid if gravity.shape[1]==r.num_joints else [i+offset for i in jid]
                            torque=gravity[:,columns]-(jac.transpose(1,2)@loads[:,leg,:,None]).squeeze(-1)
                            ratios.append((torque.abs()/r.data.joint_effort_limits[:,jid]).max())
                        effort_ratio=float(torch.stack(ratios).max())
                        arrival=bool(residual[:,:3].abs().max()<=.5 and residual[:,3:].abs().max()<=.1 and effort_ratio<.75)
                        row['return_braking_reserve']=dict(passed=arrival,residual=residual[0].tolist(),effort_ratio=effort_ratio)
                    if arrival:
                        term.return_nav_active=False;term.return_nav_arrival_brake=True
                        term.exit_arm_pose=r.data.joint_pos[:,c.joint_ids].clone()
                        # Start bounded direct fold from actual NAV arm, not stale pre-NAV reference.
                        term.retract_reference=term.exit_arm_pose.clone();term.retract_index=1
                        if hasattr(term,'hold_reference'):del term.hold_reference
                        exit_stable=0.
                        report.setdefault('control_events',[]).append(dict(event='return_nav_arrival_four_contact_braking',step=row['step'],time_s=row['time_s']))
                    final=bool(getattr(term,'return_nav_arrival_brake',False) and goal_error<.05 and heading_error<.12 and travel>=.20 and all(row.get('exit_stable_gates',{'missing':False}).values()) and row.get('retracted_ready',False))
                    nav_stable=nav_stable+b.step_dt if final else 0.
                    row['return_nav_stable_seconds']=nav_stable
                log.write(json.dumps(row)+'\n')
                if terminal:
                    if getattr(term,'push_active',False):
                        report['outcome']='native_termination_during_exit' if getattr(term,'exit_requested',False) else 'native_termination_during_push'
                    else:
                        report['outcome']='entry_timeout' if report['terminal'].get('time_out') and sum(report['terminal'].values())==1 else 'native_termination_before_entry'
                        handoff.fail(entry(row),report['outcome'].upper())
                    break
                if exit_stable>=.5 and not getattr(term,'exit_retract',False):
                    term.exit_retract=True
                    report['exit_loaded_stable_state']=row
                    report.setdefault('control_events',[]).append(dict(event='exit_retraction_started',step=row['step'],time_s=row['time_s']))
                if retract_stable>=.5 and not getattr(term,'return_nav_requested',False):
                    report['stowed_exit_state']=row
                    term.return_nav_requested=True
                    term.return_nav_requested_age=row['time_s']
                    term.return_nav_origin=r.data.root_pos_w.clone()
                    term.return_nav_orientation=r.data.root_quat_w.clone()
                    term.return_nav_goal=term.return_nav_origin.clone()
                    w,x,y,z=r.data.root_quat_w.unbind(-1);yaw=torch.atan2(2*(w*z+x*y),1.-2*(y*y+z*z))
                    term.return_nav_goal[:,0]-=.25*torch.cos(yaw);term.return_nav_goal[:,1]-=.25*torch.sin(yaw)
                    position=quat_apply_inverse(r.data.body_quat_w[:,mount],r.data.body_pos_w[:,hand]-r.data.body_pos_w[:,mount])
                    orientation=quat_mul(quat_conjugate(r.data.root_quat_w),r.data.body_quat_w[:,hand]);orientation=torch.where(orientation[:,:1]<0.,-orientation,orientation)
                    b.transition_arm_pose_command=torch.tensor([[.5,0.,.2,1.,0.,0.,0.]],device=b.device)
                    report.setdefault('control_events',[]).append(dict(event='return_nav_requested_after_stowed_ready',step=row['step'],time_s=row['time_s'],goal=term.return_nav_goal[0].tolist()))
                if nav_stable>=.5:
                    report['outcome']='nav_push_stow_nav_target_stable'
                    report['return_nav_final_state']=row
                    break
                if getattr(term,'return_nav_requested',False) and row['time_s']-term.return_nav_requested_age>=16.:
                    report['outcome']='return_nav_timeout';break
                if getattr(term,'exit_requested',False) and not getattr(term,'return_nav_requested',False) and row['time_s']-report['push_settled_time_s']>=20.:
                    report['outcome']='push_exit_stabilization_timeout';break
                if not getattr(term,'push_active',False) and stable>=.5 and not hasattr(term,'prospective_shift_m'):
                    plan=prospective_entry(c,r,ids,joint_names,reserve_for_late_parking=getattr(b,'late_stop_requested',False))
                    term.prospective_shift_m=plan['shift_m']
                    term.support_extension_required=getattr(b,'late_stop_requested',False) and plan['support_only_shift_m']>=.015-1e-9
                    term.push_support_shift_m=plan['push_support_shift_m'] if term.support_extension_required else term.prospective_shift_m
                    # Preserve original successful approach when no stance preparation
                    # is needed. Reserve applies to the shifted support branch only.
                    c.geometry_shield.transition_planning_reserve_m=0.
                    report['planning_reserve_m']=c.geometry_shield.transition_planning_reserve_m
                    if plan['support_only_shift_m']>0.:
                        b.cfg.push_hand_height_offset=-.01
                        report['prepared_stance_hand_height_offset_m']=-.01
                    term.prospective_start_age=row['time_s']
                    report['prospective_support_plan']=plan
                    if term.prospective_shift_m>0.:
                        stable=0.
                        report.setdefault('control_events',[]).append(dict(event='prospective_support_preparation_started',step=row['step'],time_s=row['time_s'],shift_m=term.prospective_shift_m))
                        continue
                if not getattr(term,'push_active',False) and stable>=.5 and getattr(term,'entry_support_integrated',False) and not hasattr(term,'entry_support_measured_verified'):
                    verified=prospective_entry(c,r,ids,joint_names,reserve_for_late_parking=False)
                    report['measured_final_support_verification']=verified
                    if verified['shift_m']!=0.:raise ValueError('Forecast support reserve insufficient at measured final pose')
                    term.entry_support_measured_verified=True
                    report.setdefault('control_events',[]).append(dict(event='measured_final_support_verified',step=row['step'],time_s=row['time_s']))
                preparation_complete=(getattr(term,'prospective_shift_m',0.)==0. or row['time_s']-term.prospective_start_age>=4.5)
                preparation_complete=preparation_complete and (not getattr(term,'entry_support_integrated',False) or getattr(term,'entry_support_measured_verified',False))
                if not getattr(term,'push_active',False) and preparation_complete and handoff.offer(entry(row)):
                    report['entry_state']=row
                    before=dict(q=r.data.joint_pos.clone(),dq=r.data.joint_vel.clone(),root=r.data.root_state_w.clone(),target=r.data.joint_pos_target.clone())
                    # Reset only controller software, never action term/env/physics.
                    c.reset(None)
                    c.last_compensated_reference[:]=r.data.joint_pos_target[:,c.joint_ids]
                    b.box_push_arm_residual.zero_()
                    b.box_push_activation_step=b.episode_length_buf.clone()
                    assert torch.equal(before['q'],r.data.joint_pos) and torch.equal(before['dq'],r.data.joint_vel)
                    assert torch.equal(before['root'],r.data.root_state_w) and torch.equal(before['target'],r.data.joint_pos_target)
                    report['push_activation_time_s']=row['time_s']
                    report['activation_no_physical_state_or_target_change']=True
                    report['activation_arm_reference']=c.reference[0].tolist()
                    report['activation_compensated_reference']=c.last_compensated_reference[0].tolist()
                    term.push_support_start_age=row['time_s']
                    term.push_active=True
                    report.setdefault('control_events',[]).append(dict(event='push_activated',step=row['step'],time_s=row['time_s']))
                if not getattr(term,'push_active',False) and row['time_s']>=24.:
                    report['outcome']='entry_timeout';handoff.fail(entry(row),'ENTRY_TIMEOUT');break
                if getattr(term,'push_active',False) and not getattr(term,'exit_requested',False) and row['time_s']-report['push_activation_time_s']>=48.:
                    report['outcome']='push_timeout';break
                if (step+1)%100==0:print('ENTRY_PROBE',step+1,row['gates'],flush=True)
            else:
                report['outcome']='total_timeout'
    except Exception:
        report['error']=traceback.format_exc();report['outcome']='runtime_error';raise
    finally:
        log.close();report['events']=handoff.events
        (a.output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print('ENTRY_RESULT',report['outcome'],report['terminal'],flush=True)
        env.close()

try: main()
except Exception:
    traceback.print_exc()
    if not (a.output/'report.json').exists():
        (a.output/'initialization-error.json').write_text(json.dumps(dict(error=traceback.format_exc(),seed=a.seed,terminal_report_missing=True),indent=2)+'\n')
    raise
finally: launcher.app.close()
