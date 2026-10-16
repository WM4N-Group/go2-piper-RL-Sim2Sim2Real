from pathlib import Path
import hashlib,json,os
import torch
from support_math_v128 import limit_reference
from isaaclab.utils.math import quat_apply_inverse
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
class Withdrawal:
    def __init__(self,env,quota,transfer):
        self.env,self.quota,self.transfer=env,quota,transfer;self.c=transfer.hold.c;self.robot=transfer.robot;self.hold=transfer.hold
        self.bank=json.loads(Path(os.environ['PUSH_WITHDRAW_BANK']).read_text());assert self.bank['joint_names']==list(self.robot.joint_names)
        n=env.num_envs;dev=env.device;self.selected=torch.zeros(n,dtype=torch.bool,device=dev);self.tables={}
        for x in self.bank['entries']:
            self.selected[x['env_id']]=True;self.tables[x['env_id']]=dict(q=torch.tensor(x['arm_reference_samples'],device=dev),blend=torch.tensor(x['phase_blend'],device=dev))
        self.started=False;self.start_time=None;self.offset=torch.zeros((n,6),device=dev);self.reference=self.offset.clone();self.velocity=self.offset.clone()
        self.index=torch.zeros(n,dtype=torch.long,device=dev);self.halted=torch.zeros(n,dtype=torch.bool,device=dev);self.release_age=torch.zeros(n,device=dev);self.healthy_age=self.release_age.clone();self.released=torch.zeros(n,dtype=torch.bool,device=dev)
        self.first_release=torch.full((n,),-1.,device=dev);self.count=self.index.clone();self.three=self.index.clone();self.airborne=self.index.clone();self.max_ratio=self.release_age.clone();self.min_clear=torch.full((n,),float('inf'),device=dev);self.max_step=self.release_age.clone();self.max_accel=self.release_age.clone();self.trace=[];self.start_match=None
        self.old_apply=self.c.apply;self.c.apply=self.apply
    def clear_released_latches(self):
        m=self.released&self.selected&self.quota.active
        for name in ('locked','motion_ready','drive_contact','approach_face_ready','approach_height_aligned'):
            value=getattr(self.c,name,None)
            if isinstance(value,torch.Tensor):value[m]=False
        for name in ('contact_memory_left','contact_duration','approach_gate_advance','approach_face_duration','approach_height_duration'):
            value=getattr(self.c,name,None)
            if isinstance(value,torch.Tensor):value[m]=0.
        if hasattr(self.env,'box_push_approached'):self.env.box_push_approached[m]=False
    def apply(self,actions):
        if self.started:
            sensed=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2)).norm(dim=1);legal_now=box_push.hand_contact(self.env,self.transfer.hand)
            self.released&=(sensed<=1.)&~legal_now
            self.clear_released_latches()
        result=self.old_apply(actions);robot=self.robot;dt=self.env.step_dt;c=self.c
        f=self.env.scene['contact_forces'].data.net_forces_w[:,self.hold.sensor_ids];fz=f[:,:,2];ratio=(robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)&(robot.data.projected_gravity_b[:,2]<-.96)
        if not self.started:
            ready=self.quota.active&(self.transfer.healthy_age>=2.)&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(self.env.episode_length_buf*dt>=120.)
            if not ready.all():return result
            tensor=lambda x:torch.tensor(x,device=self.env.device,dtype=robot.data.joint_pos.dtype)
            snaps=self.bank['snapshots'];p=tensor([x['robot_position'] for x in snaps]);q=tensor([x['robot_joint_position'] for x in snaps]);bp=tensor([x['box_position'] for x in snaps]);rq=tensor([x['robot_quaternion'] for x in snaps]);bq=tensor([x['box_quaternion'] for x in snaps])
            pe=(robot.data.root_pos_w-self.env.scene.env_origins-p).norm(dim=1);qe=(robot.data.joint_pos-q).abs().amax(1);be=(self.env.scene['box'].data.root_pos_w-self.env.scene.env_origins-bp).norm(dim=1);alignment=(robot.data.root_quat_w*rq).sum(1).abs();box_alignment=(self.env.scene['box'].data.root_quat_w*bq).sum(1).abs()
            self.start_match=dict(position_error_m=pe.cpu().tolist(),joint_error_rad=qe.cpu().tolist(),box_error_m=be.cpu().tolist(),quaternion_abs_dot=alignment.cpu().tolist(),box_quaternion_abs_dot=box_alignment.cpu().tolist())
            if not ((pe<.005)&(qe<.02)&(be<.001)&(alignment>.99995)&(box_alignment>.99995)).all():return result
            self.started=True;self.start_time=self.env.episode_length_buf*dt;self.reference=c.reference.clone();self.offset=self.reference-robot.data.joint_pos[:,c.joint_ids]
        active=self.selected&self.quota.active;hand_force=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2));force_norm=hand_force.norm(dim=1);legal=box_push.hand_contact(self.env,self.transfer.hand)
        measured_release=active&(force_norm<=1.)&~legal
        self.release_age=torch.where(active,torch.where(measured_release,self.release_age+dt,0.),self.release_age)
        new=active&(self.release_age>=.2)&~self.released;self.first_release=torch.where(new&(self.first_release<0),self.env.episode_length_buf*dt,self.first_release);self.released|=new;self.clear_released_latches()
        unsafe=active&((ratio>=.98)|(c.geometry_clearance<.055)|(c.clearance_distance<.10)|~torch.isfinite(robot.data.joint_pos).all(1));self.halted|=unsafe
        desired=self.reference.clone();finished=torch.zeros_like(active)
        for i,table in self.tables.items():
            k=min(int(self.index[i]),len(table['q'])-1);desired[i]=table['q'][k]+(1-table['blend'][k])*self.offset[i];finished[i]=k==len(table['q'])-1
        desired=torch.where(self.halted[:,None],self.reference,desired)
        limits=robot.data.soft_joint_pos_limits[:,c.joint_ids].clone();limits[:,3,0]=limits[:,3,0].clamp_min(.8)
        previous=self.reference.clone();old_velocity=self.velocity.clone();next_ref,next_vel=limit_reference(self.reference,self.velocity,desired,limits[...,0],limits[...,1],torch.full_like(self.reference,.25),torch.full_like(self.reference,3.),dt)
        projected,measured,blocked=c.geometry_shield.project(robot.data.joint_pos[:,c.joint_ids].detach().cpu().numpy(),robot.data.joint_vel[:,c.joint_ids].detach().cpu().numpy(),next_ref.detach().cpu().numpy(),torch.maximum(limits[...,0],self.reference-.25*dt).cpu().numpy(),torch.minimum(limits[...,1],self.reference+.25*dt).cpu().numpy(),active.cpu().numpy())
        projected=torch.as_tensor(projected,device=self.env.device,dtype=next_ref.dtype);correction=(projected-next_ref).abs().amax(1);self.halted|=active&(correction>1e-6)
        accept=active&(correction<=1e-6);self.reference=torch.where(accept[:,None],next_ref,self.reference);self.velocity=torch.where(accept[:,None],next_vel,torch.zeros_like(self.velocity))
        c.reference=torch.where(active[:,None],self.reference,c.reference);c.locked_reference=torch.where(active[:,None],self.reference,c.locked_reference)
        gravity=robot.root_physx_view.get_gravity_compensation_forces();columns=c.joint_ids if gravity.shape[1]==robot.num_joints else c.jacobian_columns
        encoded=(self.reference+gravity[:,columns]/c.stiffness-robot.data.default_joint_pos[:,c.joint_ids])/c.scale
        result[:,c.action_slots]=torch.where(active[:,None],encoded,result[:,c.action_slots])
        c.geometry_clearance=torch.where(active,torch.as_tensor(measured,device=self.env.device,dtype=c.geometry_clearance.dtype),c.geometry_clearance)
        c.geometry_blocked=torch.where(active,torch.as_tensor(blocked,device=self.env.device),c.geometry_blocked);c.debug_reference_post_geometry=torch.where(active[:,None],self.reference,c.debug_reference_post_geometry)
        step=(self.reference-previous).abs().amax(1);acc=((self.velocity-old_velocity)/dt).abs().amax(1);self.max_step=torch.maximum(self.max_step,torch.where(active,step,0.));self.max_accel=torch.maximum(self.max_accel,torch.where(active,acc,0.))
        hand=robot.data.body_pos_w[:,self.transfer.hand.body_ids[0]];box=self.env.scene['box'];local=quat_apply_inverse(box.data.root_quat_w,hand-box.data.root_pos_w);backgap=-local[:,0]-self.env.cfg.box_size[0]/2.
        body_error=(robot.data.root_pos_w-self.hold.body_goal).norm(dim=1);healthy=active&finished&self.released&measured_release&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(body_error<.01)&(backgap>=.03)&~self.halted
        self.healthy_age=torch.where(active,torch.where(healthy,self.healthy_age+dt,0.),self.healthy_age);self.count+=active;self.three+=active&((fz>8.).sum(1)>=3);self.airborne+=active&(fz<=2).all(1)
        self.max_ratio=torch.maximum(self.max_ratio,torch.where(active,ratio,0.));self.min_clear=torch.where(active,torch.minimum(self.min_clear,c.geometry_clearance),self.min_clear)
        for i in torch.where(active)[0].tolist():
            self.trace.append(dict(env_id=i,time_s=float(self.env.episode_length_buf[i]*dt),index=int(self.index[i]),finished=bool(finished[i]),released=bool(self.released[i]),healthy_release_s=float(self.healthy_age[i]),hand_force_N=hand_force[i].cpu().tolist(),legal_contact=bool(legal[i]),native_locked=bool(c.locked[i]),native_motion_ready=bool(c.motion_ready[i]),hand_center_backgap_m=float(backgap[i]),geometry_clearance_m=float(c.geometry_clearance[i]),body_error_m=float(body_error[i]),foot_force_z_N=fz[i].cpu().tolist(),torque_ratio=float(ratio[i]),joint_actual=robot.data.joint_pos[i,c.joint_ids].cpu().tolist(),joint_reference=self.reference[i].cpu().tolist(),reference_velocity=self.velocity[i].cpu().tolist(),reference_acceleration_max_rad_s2=float(acc[i]),shield_correction_rad=float(correction[i]),halted=bool(self.halted[i])))
        self.index+=active&~self.halted
        return result
    def summary(self):
        (Path(os.environ['SUPPORT_TRACE_PATH']).parent/'withdrawal-trace.json').write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        return dict(scope='Six prevalidated withdrawal trajectories only; env0/3 retain original contact hold. No body transfer or recontact. Actual force<=1N and legal-contact false for0.2s clears native contact latches; no flags forced true. Native geometry shield reapplied to actual commanded reference; original physics/contact termination unchanged. Reference velocity/acceleration limited, physical PD/delay/gravity compensation retained.',helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),started=self.started,start_time_s=self.start_time.cpu().tolist() if self.started else None,start_match=self.start_match,attempted=self.selected.cpu().tolist(),released=self.released.cpu().tolist(),first_release_s=self.first_release.cpu().tolist(),final_healthy_release_s=self.healthy_age.cpu().tolist(),control_samples=self.count.cpu().tolist(),three_support_samples=self.three.cpu().tolist(),airborne_samples=self.airborne.cpu().tolist(),maximum_torque_ratio=self.max_ratio.cpu().tolist(),minimum_geometry_m=[float(x) if self.count[i] else None for i,x in enumerate(self.min_clear)],max_reference_step_rad=self.max_step.cpu().tolist(),max_reference_acceleration_rad_s2=self.max_accel.cpu().tolist(),halted=self.halted.cpu().tolist())
