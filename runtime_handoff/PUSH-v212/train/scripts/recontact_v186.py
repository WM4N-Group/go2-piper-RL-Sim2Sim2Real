"""Actual legal recontact after the validated full-start free-body transfer."""
from pathlib import Path
import hashlib,json,os
import torch
from isaaclab.utils.math import compute_pose_error,quat_mul,quat_conjugate,quat_apply
from support_math_v128 import triangle_margin
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
class Recontact:
    def __init__(self,env,quota,body_transfer):
        self.env,self.quota,self.b=env,quota,body_transfer
        self.h=self.b.hold;self.w=self.b.w;self.c=self.h.c;self.robot=self.h.robot
        self.old_apply=self.c.apply;self.c.apply=self.apply
        bank_path=Path(os.environ['PUSH_RECONTACT_BANK']);self.bank=json.loads(bank_path.read_text());self.bank_hash=hashlib.sha256(bank_path.read_bytes()).hexdigest()
        assert self.bank['joint_names']==list(self.robot.joint_names)
        self.tables={x['env_id']:{k:torch.tensor(x[k],device=env.device) for k in ('arm','hand','quaternion','blend')} for x in self.bank['entries']}
        n=env.num_envs;dev=env.device;self.started=False;self.start_match=None;self.start_time=None
        self.index=torch.zeros(n,dtype=torch.long,device=dev);self.count=self.index.clone();self.three=self.index.clone();self.air=self.index.clone()
        self.halted=torch.zeros(n,dtype=torch.bool,device=dev);self.locked=self.halted.clone()
        self.age=torch.zeros(n,device=dev);self.max_age=self.age.clone();self.first_contact=torch.full_like(self.age,-1.)
        self.max_ratio=self.age.clone();self.min_clear=torch.full_like(self.age,float('inf'));self.max_force=self.age.clone();self.max_drift=self.age.clone();self.max_vz=self.age.clone();self.max_foot=self.age.clone();self.max_total=self.age.clone()
        self.trace=[];self.creep_age=self.age.clone();self.endpoint_age=self.age.clone();self.creep_distance=self.age.clone()
    def apply(self,actions):
        r,h,w,c=self.robot,self.h,self.w,self.c;dt=self.env.step_dt;now=self.env.episode_length_buf*dt;active=self.quota.active
        force=self.env.scene['contact_forces'].data.net_forces_w[:,h.sensor_ids];fz=force[:,:,2]
        hand_force=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2));hand_norm=hand_force.norm(dim=1)
        legal=box_push.hand_contact(self.env,self.b.transfer.hand)
        ratio=(r.data.applied_torque.abs()/r.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        calm=(r.data.root_lin_vel_w.norm(dim=1)<.025)&(r.data.root_ang_vel_w.norm(dim=1)<.1)&(r.data.projected_gravity_b[:,2]<-.96)
        if not self.started:
            ready=active&(now>=145.)&(self.b.age>=2.)&~self.b.halted&w.released&~w.halted&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(hand_norm<=1.)&~legal
            if not ready.all():return self.old_apply(actions)
            tensor=lambda key:torch.tensor([x[key] for x in self.bank['snapshots']],device=self.env.device,dtype=r.data.joint_pos.dtype)
            pe=(r.data.root_pos_w-self.env.scene.env_origins-tensor('robot_position')).norm(dim=1);qe=(r.data.joint_pos-tensor('robot_joint_position')).abs().amax(1);be=(self.env.scene['box'].data.root_pos_w-self.env.scene.env_origins-tensor('box_position')).norm(dim=1)
            self.start_match=dict(root_error_m=pe.cpu().tolist(),joint_error_rad=qe.cpu().tolist(),box_error_m=be.cpu().tolist())
            if not ((pe<.005)&(qe<.02)&(be<.001)).all():return self.old_apply(actions)
            self.hand_offset=torch.zeros((self.env.num_envs,3),device=self.env.device);self.quat_offset=torch.zeros((self.env.num_envs,4),device=self.env.device)
            for i,t in self.tables.items():
                p=t['hand'][0]+self.env.scene.env_origins[i];q=t['quaternion'][0]
                ep,er=compute_pose_error(r.data.body_pos_w[i:i+1,c.hand_id],r.data.body_quat_w[i:i+1,c.hand_id],p[None],q[None],rot_error_type='axis_angle')
                if ep.norm()>.005 or er.norm()>.05:return self.old_apply(actions)
                self.hand_offset[i]=r.data.body_pos_w[i,c.hand_id]-p;self.quat_offset[i]=quat_mul(r.data.body_quat_w[i,c.hand_id],quat_conjugate(q))
            self.started=True;self.start_time=now.clone();self.b.recontact_handover=True
            axis=torch.zeros((self.env.num_envs,3),device=self.env.device);axis[:,0]=1.;self.box_axis=quat_apply(self.env.scene['box'].data.root_quat_w,axis)
            self.anchors=r.data.body_pos_w[:,h.feet].clone();self.locked_reference=w.reference.clone();self.last_arm=w.reference.clone()
        drift=(r.data.body_pos_w[:,h.feet]-self.anchors).norm(dim=2).amax(1)
        com=(r.data.body_com_pos_w*h.mass[:,:,None]).sum(1)/h.mass.sum(1)[:,None]
        margin=triangle_margin(com[:,:2],r.data.body_pos_w[:,h.feet][:,[0,1,3,2],:2])[0].amin(1)
        unsafe=(ratio>=.98)|(c.geometry_clearance<.055)|(c.clearance_distance<.10)|(drift>.010)|(hand_norm>20.)|w.halted|~torch.isfinite(r.data.joint_pos).all(1)
        self.halted|=active&unsafe
        new=active&legal&~self.locked&~self.halted
        self.locked_reference=torch.where(new[:,None],w.reference,self.locked_reference);self.locked|=new;self.first_contact=torch.where(new,now,self.first_contact)
        target_hand=r.data.body_pos_w[:,c.hand_id].clone();target_quat=r.data.body_quat_w[:,c.hand_id].clone();nominal=w.reference.clone();finished=torch.zeros_like(active)
        for i,t in self.tables.items():
            k=min(int(self.index[i]),len(t['arm'])-1);blend=t['blend'][k]
            target_hand[i]=t['hand'][k]+self.env.scene.env_origins[i]+(1-blend)*self.hand_offset[i]
            off=self.quat_offset[i].clone();off=torch.where(off[0]<0,-off,off);off=(1-blend)*off+blend*torch.tensor([1.,0.,0.,0.],device=self.env.device);off/=off.norm()
            target_quat[i]=quat_mul(off,t['quaternion'][k]);nominal[i]=t['arm'][k];finished[i]=k==len(t['arm'])-1
        u=(self.creep_age/8.).clamp(0.,1.);self.creep_distance=.003*u**3*(10.-15.*u+6.*u*u)
        target_hand+=self.creep_distance[:,None]*self.box_axis
        pe,re=compute_pose_error(r.data.body_pos_w[:,c.hand_id],r.data.body_quat_w[:,c.hand_id],target_hand,target_quat,rot_error_type='axis_angle');ep=pe.norm(dim=1);er=re.norm(dim=1)
        jac=r.root_physx_view.get_jacobians()[:,c.jacobian_body][:,:,c.jacobian_columns];weights=torch.tensor([1.,1.,1.,.25,.25,.25],device=self.env.device)
        j=jac*weights[None,:,None];error=torch.cat((pe,re),1)*weights;identity=torch.eye(6,device=self.env.device)[None].expand(self.env.num_envs,-1,-1)
        inv=torch.linalg.solve(j@j.transpose(1,2)+.0025**2*identity,identity);pinv=j.transpose(1,2)@inv;actual=r.data.joint_pos[:,c.joint_ids]
        delta=(pinv@error[:,:,None]).squeeze(2)+((identity-pinv@j)@(nominal-actual)[:,:,None]).squeeze(2);delta*= (.04/delta.abs().amax(1).clamp_min(.04))[:,None]
        desired=torch.where(self.locked[:,None],self.locked_reference,actual+delta);desired=torch.where(self.halted[:,None],self.last_arm,desired)
        w.external_arm_target=desired;w.external_arm_active=active
        result=self.old_apply(actions);self.last_arm=w.reference.clone();self.halted|=w.halted
        advance=active&~self.halted&~self.locked&(fz>8.).all(1)&(margin>=.025)&(ep<.004)&(er<.04)&calm&h.valid
        endpoint_ready=advance&finished&(ep<.0005)&(er<.01)&(hand_norm<1.)
        self.endpoint_age=torch.where(endpoint_ready,self.endpoint_age+dt,0.)
        self.creep_age+=dt*(endpoint_ready&(self.endpoint_age>=.2))
        self.index+=advance&~finished
        body_error=(r.data.root_pos_w-h.body_goal).norm(dim=1)
        healthy=active&self.locked&legal&~self.halted&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(margin>=.025)&(body_error<.010)&(drift<.010)&(hand_norm<=20.)&h.valid
        self.age=torch.where(active,torch.where(healthy,self.age+dt,0.),self.age);self.max_age=torch.maximum(self.max_age,self.age)
        self.count+=active;self.three+=active&((fz>8.).sum(1)>=3);self.air+=active&(fz<=2.).all(1)
        self.max_ratio=torch.maximum(self.max_ratio,torch.where(active,ratio,0.));self.min_clear=torch.where(active,torch.minimum(self.min_clear,c.geometry_clearance),self.min_clear)
        self.max_force=torch.maximum(self.max_force,torch.where(active,hand_norm,0.));self.max_drift=torch.maximum(self.max_drift,torch.where(active,drift,0.));self.max_vz=torch.maximum(self.max_vz,torch.where(active,r.data.root_lin_vel_w[:,2].abs(),0.));self.max_foot=torch.maximum(self.max_foot,torch.where(active,force.norm(dim=2).amax(1),0.));self.max_total=torch.maximum(self.max_total,torch.where(active,force.sum(1).norm(dim=1),0.))
        for i in torch.where(active)[0].tolist():self.trace.append(dict(env_id=i,time_s=float(now[i]),index=int(self.index[i]),finished=bool(finished[i]),locked_on_measured_contact=bool(self.locked[i]),legal_contact=bool(legal[i]),hand_force_N=float(hand_norm[i]),healthy_s=float(self.age[i]),halted=bool(self.halted[i]),geometry_m=float(c.geometry_clearance[i]),torque_ratio=float(ratio[i]),foot_force_z_N=fz[i].cpu().tolist(),foot_drift_m=float(drift[i]),body_error_m=float(body_error[i]),support_margin_m=float(margin[i]),creep_distance_m=float(self.creep_distance[i]),world_hand_error_m=float(ep[i]),world_orientation_error_rad=float(er[i])))
        return result
    def summary(self):
        (Path(os.environ['SUPPORT_TRACE_PATH']).parent/'recontact-trace.json').write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(creep_distance_m=self.creep_distance,index=self.index,locked=self.locked,halted=self.halted,first_legal_contact_s=self.first_contact,final_healthy_s=self.age,maximum_healthy_s=self.max_age,control_samples=self.count,three_support_samples=self.three,airborne_samples=self.air,maximum_torque_ratio=self.max_ratio,maximum_hand_force_N=self.max_force,maximum_foot_drift_m=self.max_drift,maximum_abs_vz_m_s=self.max_vz,maximum_foot_resultant_N=self.max_foot,maximum_total_foot_vector_norm_N=self.max_total)
        return dict(scope='Original-start used3701/8env170s legal recontact-and-hold diagnostic after validated v179 free transfer. No sustained pushing or full task acceptance. 3mm bounded8s quintic normal approach after stable endpoint, stop advancing on measured contact;20N additional contact-force stop; native35mm shield/55mm support, PD/delay, measured contact and physical failures retained. Control-rate telemetry, not substep peaks.',started=self.started,start_time_s=self.start_time.cpu().tolist() if self.started else None,start_match=self.start_match,helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),bank_sha256=self.bank_hash,minimum_geometry_m=[float(x) if self.count[i] else None for i,x in enumerate(self.min_clear)],**{k:v.cpu().tolist() for k,v in fields.items()})
