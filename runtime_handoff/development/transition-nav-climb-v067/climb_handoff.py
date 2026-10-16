"""Initialize only CLIMB controller state from continuously measured support."""
import torch
from frozen_stage_config import extract, apply
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.crawl_gait import CrawlClock, PlatformFrontExtension
from ground_entry_guidance import GroundEntryGuidance


def activate(t,source):
 env=t._env;r=t._asset
 assert t.pending.all() and t.guidance is None
 values=extract(source/'scripts/evaluate_box_skills.py',source.parent/'jobs.json','8052ab2a393d9cc3b5ede85b9819a90dc45b3c0eff340d092a971bbf51f00043')
 apply(t.cfg,values)
 t.clock=CrawlClock(env.num_envs,env.device,t.cfg.transfer_s,t.cfg.swing_s,t.cfg.settle_s)
 t.extension=PlatformFrontExtension(env.num_envs,env.device,t.cfg.platform_front_extension)
 t.guidance=GroundEntryGuidance(t)
 t.guidance.entry_output=t.entry_output
 # Logical controller reference only. No root/joint writes or delay/history reset.
 env.climb_stage_joint_target=r.data.joint_pos_target.clone()
 env.climb_stage_loaded_reference=True
 t.reference[:]=r.data.joint_pos_target[:,t._joint_ids]
 t.climb_active=True
 return dict(action_config=values,initial_reference=t.reference[0].tolist(),measured_q=r.data.joint_pos[0,t._joint_ids].tolist(),feet=t.feet_positions()[0].tolist())


def sample(t):
 env=t._env;r=t._asset;g=t.guidance;o=env.scene.env_origins[0]
 return dict(feet_position=(t.feet_positions()[0]-o).tolist(),foot_contact_force_z=env.scene['contact_forces'].data.net_forces_w[0,t.sensor_ids,2].tolist(),platform_final_goal=(g.platform_final_goal[0]-o).tolist(),guidance_body_target=(g.target[0]-o).tolist(),robot_position=(r.data.root_pos_w[0]-o).tolist(),robot_velocity=r.data.root_lin_vel_w[0].tolist(),robot_angular_velocity=r.data.root_ang_vel_w[0].tolist(),guidance_command_limit_excess=g.command_limit_excess[0].tolist(),guidance_reference_age=float(g.age[0]),platform_extension_completed=int(t.extension.completed[0]),platform_extension_moving=bool(t.extension.moving[0]),platform_final_started=bool(g.platform_final_started[0]),platform_hold_active=bool(t.platform_hold[0]),configured_stride=float(t.cfg.stride),leg=int(t.clock.leg[0]),progress=float(t.clock.progress[0]),guidance_engaged=bool(g.engaged[0]),guidance_pose_feasible=bool(g.pose_feasible[0]),guidance_support_loads=g.support_loads[0].tolist(),guidance_reference_velocity=t.reference_velocity[0].tolist(),landing_goal=(t.landing[0]-o).tolist(),selected_foot_reference=(t.foot_reference[0]-o).tolist(),landing_probe_depth=float(g.landing_contact.depth[0]),landing_touch_age=float(g.landing_contact.touch_age[0]),landing_reload=float(g.landing_contact.reload[0]),landing_loaded_age=float(g.landing_contact.loaded_age[0]),guidance_valid_legs=g.valid_legs[0].tolist(),guidance_load_bias=g.load_bias[0].tolist())
