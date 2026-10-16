"""Candidate-only full-path planning for all-ground CLIMB entry."""
import json
import torch
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import StageGuidance, feasible_support_pose, swing_path_preview, swing_preview_ready, expanded_front_ascent_pose, predicted_tripod_margin

class EntryPlanningRejected(Exception):
    pass

class GroundEntryGuidance(StageGuidance):
    def reserve_front_ascent_pose(self, mask):
        super().reserve_front_ascent_pose(mask)
        self.reserve_second_front_landing(mask)
        a=self.a; robot=a._asset; feet=a.feet_positions()
        local=feet-a._env.scene.env_origins[:,None]
        selected=(mask & (a.clock.progress==0)
            & (local[...,2]<.10).all(1) & (local[...,0]<.75).all(1)
            & a.contacts().all(1))
        if not selected.any(): return
        slots=torch.tensor(a._joint_ids,device=a._env.device)[self.slots]
        gravity=robot.root_physx_view.get_gravity_compensation_forces()
        offset=0 if gravity.shape[1]==robot.num_joints else 6
        bounds=robot.data.soft_joint_pos_limits[:,slots][selected]
        bias=robot.data.applied_torque[:,slots][selected]/30.
        load=dict(com=a.center_of_mass()[selected],leg=a.clock.leg[selected],
            weight=a.mass.sum(1)[selected]*9.81,gravity=gravity[:,slots+offset][selected],
            effort=robot.data.joint_effort_limits[:,slots][selected],
            orientation=self.orientation[selected],rotation_active=torch.ones_like(a.clock.leg[selected],dtype=torch.bool),
            four_support_path=torch.ones_like(a.clock.leg[selected],dtype=torch.bool))
        swing=dict(start=a.start[selected],landing=a.landing[selected],
            origins=a._env.scene.env_origins[selected],leg=a.clock.leg[selected],gravity=load['gravity'],
            clearance=a.cfg.foot_clearance,inset=a.swing_inset[selected],
            active=torch.ones_like(load['leg'],dtype=torch.bool),allow_partial_transfer=False,
            landing_probe_depth=torch.full_like(load['weight'],.015),landing_com=load['com'],
            landing_origin=self.origin[selected],landing_weight=load['weight'],landing_effort=load['effort'],
            landing_orientation=self.orientation[selected],landing_rotation_active=load['rotation_active'])
        pose,rotation,margin,feasible=feasible_support_pose(self.model,feet[selected],self.target[selected],
            self.origin[selected],self.orientation[selected],bias,bounds,a.cfg.guidance_body_clearance,
            self.body_bounds,self.box_bounds[selected],True,self.link_bounds,load,swing,
            height_samples=65,full_load_reserve=.03)
        # Preserve every feasible original search. Expand orientation only on
        # rejected all-ground entry plans, using the existing frozen path gates.
        retry=~feasible
        fallback_applied=torch.zeros_like(feasible)
        if retry.any():
            backup=expanded_front_ascent_pose(self.model,feet[selected][retry],self.origin[selected][retry],
                self.orientation[selected][retry],bias[retry],bounds[retry],self.body_bounds,
                self.box_bounds[selected][retry],self.link_bounds,
                {k:v[retry] for k,v in load.items()},
                {k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()})
            rows=torch.where(retry)[0][backup[3]]
            pose[rows],rotation[rows],margin[rows]=(v[backup[3]] for v in backup[:3])
            feasible[rows]=True;fallback_applied[rows]=True
        partial_applied=torch.zeros_like(feasible)
        retry=~feasible
        if retry.any():
            partial_swing={k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()}
            partial_swing['allow_partial_transfer']=True
            partial_load={k:v[retry] for k,v in load.items()}
            backup=feasible_support_pose(self.model,feet[selected][retry],self.target[selected][retry],
                self.origin[selected][retry],self.orientation[selected][retry],bias[retry],bounds[retry],
                a.cfg.guidance_body_clearance,self.body_bounds,self.box_bounds[selected][retry],True,
                self.link_bounds,partial_load,partial_swing,height_samples=65)
            # Partial four-contact preparation is never permission to unload.
            # Demand actual geometric progress toward the selected support triangle.
            pm=predicted_tripod_margin(feet[selected][retry],self.origin[selected][retry],
                backup[0][:,None],backup[1][:,None],partial_load)[:,0]
            cm=predicted_tripod_margin(feet[selected][retry],self.origin[selected][retry],
                self.origin[selected][retry,None],self.orientation[selected][retry,None],partial_load)[:,0]
            accept=backup[3] & (pm>cm+.002)
            rows=torch.where(retry)[0][accept]
            pose[rows],rotation[rows],margin[rows]=(v[accept] for v in backup[:3])
            partial_applied[rows]=True
        sm,se,sg=swing_path_preview(self.model,feet[selected],pose[:,None],rotation[:,None],
            bounds,swing,self.link_bounds,self.box_bounds[selected])
        ready=feasible & swing_preview_ready(sm,se,sg,swing)[:,0]
        def item(v):
            if torch.is_tensor(v):return v.detach().cpu().tolist()
            if isinstance(v,dict):return {k:item(x) for k,x in v.items()}
            return v
        record=dict(time_s=float(a._env.episode_length_buf[0])*a._env.step_dt,
            feet=feet[selected],origin=self.origin[selected],quaternion=self.orientation[selected],
            target=self.target[selected],target_quaternion=self.target_orientation[selected],
            bias=bias,bounds=bounds,body_bounds=self.body_bounds,box_bounds=self.box_bounds[selected],
            load=load,swing=swing,result=dict(pose=pose,rotation=rotation,margin=margin,feasible=feasible,
                swing_margin=sm,swing_error=se,swing_gap=sg,ready=ready,fallback_applied=fallback_applied,partial_applied=partial_applied))
        with (self.entry_output/'ground-entry-plans.jsonl').open('a') as f:f.write(json.dumps(item(record))+'\n')
        self.pose_feasible[selected]=ready|partial_applied;self.swing_path_ready[selected]=ready
        if not bool((ready|partial_applied).all()):
            raise EntryPlanningRejected('No complete all-ground support/swing/probe/reload plan; stopped before unloading')
        self.target[selected]=pose;self.target_orientation[selected]=rotation;self.pose_margin[selected]=margin
        self.swing_path_margin[selected]=sm[:,0];self.swing_path_gap[selected]=sg[:,0]
        self.com_rotation_active[selected]=True

    def reserve_second_front_landing(self,mask):
        from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import single_front_support_scope
        from front_landing_reserve import expanded_front_landing_reserve,selected_swing_path_preview
        a=self.a;robot=a._asset;feet=a.feet_positions();local=feet-a._env.scene.env_origins[:,None]
        selected=(mask & single_front_support_scope(local,a.contacts(),a.clock.leg)
            & (a.clock.progress==0) & self.pose_feasible & (a.landing[:,2]-a.start[:,2]>.1))
        if not selected.any():return
        slots=torch.tensor(a._joint_ids,device=a._env.device)[self.slots]
        gravity=robot.root_physx_view.get_gravity_compensation_forces();offset=0 if gravity.shape[1]==robot.num_joints else 6
        bounds=robot.data.soft_joint_pos_limits[:,slots][selected];bias=robot.data.applied_torque[:,slots][selected]/30.
        load=dict(com=a.center_of_mass()[selected],leg=a.clock.leg[selected],weight=a.mass.sum(1)[selected]*9.81,
            gravity=gravity[:,slots+offset][selected],effort=robot.data.joint_effort_limits[:,slots][selected],
            orientation=self.orientation[selected],rotation_active=torch.ones_like(a.clock.leg[selected],dtype=torch.bool))
        swing=dict(start=a.start[selected],landing=a.landing[selected],origins=a._env.scene.env_origins[selected],
            leg=a.clock.leg[selected],gravity=load['gravity'],clearance=a.cfg.foot_clearance,inset=a.swing_inset[selected],
            active=torch.ones_like(load['leg'],dtype=torch.bool),allow_partial_transfer=False,
            landing_probe_depth=torch.full_like(load['weight'],.015),landing_com=load['com'],landing_origin=self.origin[selected],
            landing_weight=load['weight'],landing_effort=load['effort'],landing_orientation=self.orientation[selected],landing_rotation_active=load['rotation_active'],minimum_gap=torch.full_like(load['weight'],.005))
        sm,se,sg=swing_path_preview(self.model,feet[selected],self.target[selected,None],self.target_orientation[selected,None],bounds,swing,self.link_bounds,self.box_bounds[selected])
        _,_,selected_gap=selected_swing_path_preview(self.model,feet[selected],self.target[selected,None],self.target_orientation[selected,None],bounds,swing,self.link_bounds,self.box_bounds[selected])
        retry=~(swing_preview_ready(sm,se,sg,swing)[:,0] & (selected_gap[:,0]>=.012))
        if not retry.any():return
        ids=torch.where(selected)[0][retry]
        result=expanded_front_landing_reserve(self.model,feet[ids],self.origin[ids],self.orientation[ids],bias[retry],bounds[retry],self.body_bounds,self.box_bounds[ids],self.link_bounds,
            {k:v[retry] for k,v in load.items()},{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()})
        pose,rot,margin,valid=result
        sm2,se2,sg2=swing_path_preview(self.model,feet[ids],pose[:,None],rot[:,None],bounds[retry],{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},self.link_bounds,self.box_bounds[ids])
        _,_,selected_gap2=selected_swing_path_preview(self.model,feet[ids],pose[:,None],rot[:,None],bounds[retry],{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},self.link_bounds,self.box_bounds[ids])
        valid &= swing_preview_ready(sm2,se2,sg2,{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()})[:,0] & (selected_gap2[:,0]>=.012)
        landing_adjustment=torch.zeros_like(margin)
        # A shorter top landing can clear the calf while remaining inside the
        # original platform domain. Replan only before unloading; no live swing edits.
        for delta in (-.01,-.02):
            failed=~valid
            if not failed.any():break
            alt_swing={k:v[retry][failed].clone() if torch.is_tensor(v) else v for k,v in swing.items()}
            alt_swing['landing'][:,0]+=delta
            inside=(alt_swing['landing'][:,0]-alt_swing['origins'][:,0]>.80)
            backup=expanded_front_landing_reserve(self.model,feet[ids[failed]],self.origin[ids[failed]],self.orientation[ids[failed]],bias[retry][failed],bounds[retry][failed],self.body_bounds,self.box_bounds[ids[failed]],self.link_bounds,{k:v[retry][failed] for k,v in load.items()},alt_swing)
            accepted=backup[3]&inside
            rows=torch.where(failed)[0][accepted]
            pose[rows],rot[rows],margin[rows]=(v[accepted] for v in backup[:3])
            selected_rows=torch.where(retry)[0][rows]
            swing['landing'][selected_rows]=alt_swing['landing'][accepted]
            a.landing[ids[rows]]=alt_swing['landing'][accepted]
            valid[rows]=True;landing_adjustment[rows]=delta
        partial=torch.zeros_like(valid)
        if (~valid).any():
            from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.climb_guidance import inset_support_target,mixed_support_body_height
            retry_ids=ids[~valid];part_load={k:v[retry][~valid] for k,v in load.items()}
            part_load['four_support_path']=torch.ones_like(part_load['leg'],dtype=torch.bool)
            part_swing={k:v[retry][~valid] if torch.is_tensor(v) else v for k,v in swing.items()};part_swing['allow_partial_transfer']=True
            triangle=feet[retry_ids].gather(1,self.support_indices[a.clock.leg[retry_ids],:,None].expand(-1,-1,3))[...,:2]
            shift=inset_support_target(part_load['com'][:,:2],triangle)-part_load['com'][:,:2]
            shift*=.08/shift.norm(dim=1).clamp_min(.08)[:,None]
            target=self.origin[retry_ids].clone();target[:,:2]+=shift;target[:,2]=mixed_support_body_height(feet[retry_ids],a.cfg.guidance_body_clearance)
            part=feasible_support_pose(self.model,feet[retry_ids],target,self.origin[retry_ids],self.orientation[retry_ids],bias[retry][~valid],bounds[retry][~valid],a.cfg.guidance_body_clearance,self.body_bounds,self.box_bounds[retry_ids],True,self.link_bounds,part_load,part_swing,height_samples=65)
            pm=predicted_tripod_margin(feet[retry_ids],self.origin[retry_ids],part[0][:,None],part[1][:,None],part_load)[:,0]
            cm=predicted_tripod_margin(feet[retry_ids],self.origin[retry_ids],self.origin[retry_ids,None],self.orientation[retry_ids,None],part_load)[:,0]
            accepted=part[3] & (pm>cm+.002)
            rows=torch.where(~valid)[0][accepted]
            pose[rows],rot[rows],margin[rows]=(v[accepted] for v in part[:3]);partial[rows]=True
            sm2,se2,sg2=swing_path_preview(self.model,feet[ids],pose[:,None],rot[:,None],bounds[retry],{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},self.link_bounds,self.box_bounds[ids])
        sm2,se2,sg2=swing_path_preview(self.model,feet[ids],pose[:,None],rot[:,None],bounds[retry],{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},self.link_bounds,self.box_bounds[ids])
        _,_,selected_gap2=selected_swing_path_preview(self.model,feet[ids],pose[:,None],rot[:,None],bounds[retry],{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},self.link_bounds,self.box_bounds[ids])
        valid &= swing_preview_ready(sm2,se2,sg2,{k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()})[:,0] & (selected_gap2[:,0]>=.012)
        def pack(v):
            if torch.is_tensor(v):return v.detach().cpu().tolist()
            if isinstance(v,dict):return {k:pack(x) for k,x in v.items()}
            return v
        record=dict(time_s=float(a._env.episode_length_buf[0])*a._env.step_dt,leg=a.clock.leg[ids],feet=feet[ids],origin=self.origin[ids],quaternion=self.orientation[ids],bounds=bounds[retry],bias=bias[retry],box_bounds=self.box_bounds[ids],load={k:v[retry] for k,v in load.items()},swing={k:v[retry] if torch.is_tensor(v) else v for k,v in swing.items()},old_swing_margin=sm[retry],old_swing_gap=sg[retry],old_selected_gap=selected_gap[retry],result=dict(pose=pose,rotation=rot,margin=margin,valid=valid,partial_preparation=partial,swing_margin=sm2,swing_error=se2,swing_gap=sg2,selected_gap=selected_gap2,landing_adjustment=landing_adjustment))
        with (self.entry_output/'front-landing-reserve.jsonl').open('a') as f:f.write(json.dumps(pack(record))+'\n')
        self.pose_feasible[ids]=valid|partial;self.swing_path_ready[ids]=valid
        if not bool((valid|partial).all()):raise EntryPlanningRejected('Second front ascent has no checked12mm nominal landing reserve; no lift')
        self.target[ids]=pose;self.target_orientation[ids]=rot;self.pose_margin[ids]=margin
        self.swing_path_margin[ids]=sm2[:,0];self.swing_path_gap[ids]=sg2[:,0]
        self.pose_capture_com[ids]=load['com'][retry];self.com_rotation_active[ids]=True
