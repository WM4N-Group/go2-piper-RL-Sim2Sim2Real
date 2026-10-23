"""Measured release -> planted body transfer with world hand feedback. No recontact."""
from pathlib import Path
import hashlib,json,os
import torch
from isaaclab.utils.math import compute_pose_error,quat_mul,quat_conjugate
from support_math_v128 import triangle_margin
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push
class BodyTransfer:
    def __init__(self,env,quota,transfer,withdrawal):
        self.env,self.quota,self.transfer,self.w=env,quota,transfer,withdrawal
        self.hold=transfer.hold;self.c=self.hold.c;self.robot=self.hold.robot
        n=env.num_envs;dev=env.device;self.started=False
        self.index=torch.zeros(n,dtype=torch.long,device=dev);self.halted=torch.zeros(n,dtype=torch.bool,device=dev)
        self.age=torch.zeros(n,device=dev);self.count=self.index.clone();self.three=self.index.clone();self.air=self.index.clone()
        self.max_ratio=self.age.clone();self.min_clear=torch.full_like(self.age,float('inf'));self.max_hand_error=self.age.clone();self.max_drift=self.age.clone()
        self.max_vz=self.age.clone();self.max_force=self.age.clone();self.max_sumforce=self.age.clone();self.max_leg_step=self.age.clone();self.max_leg_acc=self.age.clone()
        self.trace=[];self.tables={};self.start_time=None;self.start_match=None
        bank=json.loads(Path(os.environ['PUSH_TRANSFER_BANK']).read_text())
        for x in bank['entries']:self.tables[x['env_id']]={k:torch.tensor(x[k],device=dev) for k in ('arm','body','hand','quaternion','blend')}
        self.old_apply=self.c.apply;self.c.apply=self.apply
    def apply(self,actions):
        r=self.robot;h=self.hold;w=self.w;c=self.c;dt=self.env.step_dt
        f=self.env.scene['contact_forces'].data.net_forces_w[:,h.sensor_ids];fz=f[:,:,2]
        hand_force=self.env.scene['box_contact_hand'].data.force_matrix_w.sum(dim=(1,2)).norm(dim=1)
        legal=box_push.hand_contact(self.env,self.transfer.hand)
        ratio=(r.data.applied_torque.abs()/r.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        calm=(r.data.root_lin_vel_w.norm(dim=1)<.025)&(r.data.root_ang_vel_w.norm(dim=1)<.1)&(r.data.projected_gravity_b[:,2]<-.96)
        now=self.env.episode_length_buf*dt
        if not self.started:
            ready=self.quota.active&w.released&(w.healthy_age>=2.)&~w.halted&(fz>8.).all(1)&calm&(ratio<.98)&(c.geometry_clearance>=.055)&(now>=130.)
            if not ready.all():return self.old_apply(actions)
            self.started=True;self.start_time=now.clone();self.anchors=r.data.body_pos_w[:,h.feet].clone()
            self.origin_ref=h.body_ref.clone();self.root_start=r.data.root_pos_w.clone()
            self.hand_offset=torch.zeros((self.env.num_envs,3),device=self.env.device)
            self.quat_offset=torch.zeros((self.env.num_envs,4),device=self.env.device)
            errors=[]
            for i,t in self.tables.items():
                p=t['hand'][0]+self.env.scene.env_origins[i];q=t['quaternion'][0]
                pe,re=compute_pose_error(r.data.body_pos_w[i:i+1,c.hand_id],r.data.body_quat_w[i:i+1,c.hand_id],p[None],q[None],rot_error_type='axis_angle')
                errors.append([float(pe.norm()),float(re.norm())])
                self.hand_offset[i]=r.data.body_pos_w[i,c.hand_id]-p
                self.quat_offset[i]=quat_mul(r.data.body_quat_w[i,c.hand_id],quat_conjugate(q))
                h.body_goal[i]=self.origin_ref[i]+t['body'][-1]-t['body'][0]
                if i!=6:h.body_goal[i]=t['body'][-1]+self.env.scene.env_origins[i]
            self.start_match=errors
            self.halted|=torch.tensor([p>.005 or a>.05 for p,a in errors],device=self.env.device)
            self.last_body=self.origin_ref.clone();self.last_arm=w.reference.clone()
        active=self.quota.active
        feet=r.data.body_pos_w[:,h.feet];drift=(feet-self.anchors).norm(dim=2).amax(1)
        com=(r.data.body_com_pos_w*h.mass[:,:,None]).sum(1)/h.mass.sum(1)[:,None]
        margin=triangle_margin(com[:,:2],feet[:,[0,1,3,2],:2])[0].amin(1)
        unsafe=(ratio>=.98)|(c.geometry_clearance<.055)|(c.clearance_distance<.10)|(hand_force>1.)|legal|(drift>.010)|w.halted|~torch.isfinite(r.data.joint_pos).all(1)
        self.halted|=active&unsafe
        body=self.last_body.clone();target_hand=r.data.body_pos_w[:,c.hand_id].clone();target_quat=r.data.body_quat_w[:,c.hand_id].clone();nominal=w.reference.clone();finished=torch.zeros_like(active)
        for i,t in self.tables.items():
            k=min(int(self.index[i]),len(t['arm'])-1);blend=t['blend'][k]
            body[i]=self.origin_ref[i]+t['body'][k]-t['body'][0]
            if i!=6:body[i]=t['body'][k]+self.env.scene.env_origins[i]+(1-blend)*(self.origin_ref[i]-t['body'][0]-self.env.scene.env_origins[i])
            target_hand[i]=t['hand'][k]+self.env.scene.env_origins[i]+(1-blend)*self.hand_offset[i]
            # Normalized interpolation of small measured-vs-model initial orientation offset.
            off=self.quat_offset[i].clone();off=torch.where(off[0]<0,-off,off)
            off=(1-blend)*off+blend*torch.tensor([1.,0.,0.,0.],device=self.env.device);off/=off.norm()
            target_quat[i]=quat_mul(off,t['quaternion'][k]);nominal[i]=t['arm'][k];finished[i]=k==len(t['arm'])-1
        pe,re=compute_pose_error(r.data.body_pos_w[:,c.hand_id],r.data.body_quat_w[:,c.hand_id],target_hand,target_quat,rot_error_type='axis_angle')
        ep=pe.norm(dim=1);er=re.norm(dim=1)
        # Excess error pauses phase; it never disables stance feedback.
        advance=active&~self.halted&(fz>8.).all(1)&(margin>=.025)&(ep<.004)&(er<.04)&(r.data.root_lin_vel_w.norm(dim=1)<.04)&(r.data.root_ang_vel_w.norm(dim=1)<.1)&h.valid
        jac=r.root_physx_view.get_jacobians()[:,c.jacobian_body][:,:,c.jacobian_columns]
        weights=torch.tensor([1.,1.,1.,.25,.25,.25],device=self.env.device);j=jac*weights[None,:,None];error=torch.cat((pe,re),1)*weights
        inv=torch.linalg.solve(j@j.transpose(1,2)+.0025**2*torch.eye(6,device=self.env.device)[None],torch.eye(6,device=self.env.device)[None].expand(self.env.num_envs,-1,-1))
        pinv=j.transpose(1,2)@inv;actual=r.data.joint_pos[:,c.joint_ids]
        delta=(pinv@error[:,:,None]).squeeze(2)+((torch.eye(6,device=self.env.device)[None]-pinv@j)@(nominal-actual)[:,:,None]).squeeze(2)
        delta*= (.04/delta.abs().amax(1).clamp_min(.04))[:,None]
        desired=actual+delta
        body=torch.where((active&~self.halted)[:,None],body,self.last_body)
        desired=torch.where((active&~self.halted)[:,None],desired,self.last_arm)
        h.external_body_reference=body;h.external_body_active=active
        gain_mask=active.clone();gain_mask[6]=False
        ramp=((now-self.start_time)/1.).clamp(0.,1.);ramp=ramp**3*(10-15*ramp+6*ramp*ramp)
        h.external_position_gain=torch.where(gain_mask,8.*ramp,torch.zeros_like(ramp))
        w.external_arm_target=desired;w.external_arm_active=active
        previous=h.reference.clone();velocity=h.velocity.clone()
        result=self.old_apply(actions)
        self.halted|=w.halted
        self.last_body=h.body_ref.clone();self.last_arm=w.reference.clone()
        self.index+=advance&~self.halted&~finished
        body_error=(r.data.root_pos_w-h.body_goal).norm(dim=1)
        healthy=active&finished&~self.halted&w.released&(hand_force<=1.)&~legal&(fz>8.).all(1)&calm&(margin>=.025)&(drift<.010)&(ep<.004)&(er<.04)&(body_error<.01)&(ratio<.98)&(c.geometry_clearance>=.055)&h.valid
        self.age=torch.where(active,torch.where(healthy,self.age+dt,0.),self.age)
        self.count+=active;self.three+=active&((fz>8.).sum(1)>=3);self.air+=active&(fz<=2).all(1)
        self.max_ratio=torch.maximum(self.max_ratio,torch.where(active,ratio,0.));self.min_clear=torch.where(active,torch.minimum(self.min_clear,c.geometry_clearance),self.min_clear)
        self.max_hand_error=torch.maximum(self.max_hand_error,torch.where(active,ep,0.));self.max_drift=torch.maximum(self.max_drift,torch.where(active,drift,0.))
        self.max_vz=torch.maximum(self.max_vz,torch.where(active,r.data.root_lin_vel_w[:,2].abs(),0.));self.max_force=torch.maximum(self.max_force,torch.where(active,f.norm(dim=2).amax(1),0.));self.max_sumforce=torch.maximum(self.max_sumforce,torch.where(active,f.sum(1).norm(dim=1),0.))
        self.max_leg_step=torch.maximum(self.max_leg_step,torch.where(active,(h.reference-previous).abs().amax(1),0.));self.max_leg_acc=torch.maximum(self.max_leg_acc,torch.where(active,((h.velocity-velocity)/dt).abs().amax(1),0.))
        for i in torch.where(active)[0].tolist():
            self.trace.append(dict(env_id=i,time_s=float(now[i]),index=int(self.index[i]),finished=bool(finished[i]),healthy_hold_s=float(self.age[i]),halted=bool(self.halted[i]),advance=bool(advance[i]),foot_force_z=fz[i].cpu().tolist(),foot_drift_m=float(drift[i]),margin_m=float(margin[i]),hand_error_m=float(ep[i]),hand_orientation_error_rad=float(er[i]),hand_force_N=float(hand_force[i]),legal_contact=bool(legal[i]),body_error_m=float(body_error[i]),body_position=(r.data.root_pos_w[i]-self.env.scene.env_origins[i]).cpu().tolist(),body_reference=(h.body_ref[i]-self.env.scene.env_origins[i]).cpu().tolist(),body_reference_error_m=float((r.data.root_pos_w[i]-h.body_ref[i]).norm()),position_feedback_gain=float(h.external_position_gain[i]),geometry_clearance_m=float(c.geometry_clearance[i]),torque_ratio=float(ratio[i]),leg_feedback_valid=bool(h.valid[i])))
        return result
    def summary(self):
        (Path(os.environ['SUPPORT_TRACE_PATH']).parent/'body-transfer-trace.json').write_text(json.dumps(self.trace,separators=(',',':'))+'\n')
        fields=dict(final_healthy_s=self.age,control_samples=self.count,three_support_samples=self.three,airborne_samples=self.air,maximum_torque_ratio=self.max_ratio,maximum_hand_error_m=self.max_hand_error,maximum_foot_drift_m=self.max_drift,maximum_abs_vz_m_s=self.max_vz,maximum_foot_resultant_N=self.max_force,maximum_total_foot_vector_norm_N=self.max_sumforce,maximum_leg_reference_step_rad=self.max_leg_step,maximum_leg_reference_acceleration_rad_s2=self.max_leg_acc,halted=self.halted,index=self.index)
        return dict(scope='Used3701 original-start145s planted free-body transfer after measured withdrawal. No recontact, no pushing. World hand feedback, unchanged PD/delay/force/geometry gates. Control-rate telemetry only.',helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),started=self.started,start_time_s=self.start_time.cpu().tolist() if self.started else None,start_match_errors=self.start_match,minimum_geometry_m=[float(x) if self.count[i] else None for i,x in enumerate(self.min_clear)],**{k:v.cpu().tolist() for k,v in fields.items()})
