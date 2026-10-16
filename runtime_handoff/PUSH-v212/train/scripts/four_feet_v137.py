"""Compose frozen physical-leg single-step controllers: FL, FR, RL, RR."""
from pathlib import Path
import hashlib, os
import torch
from support_transfer_v135 import SupportTransfer as SingleStep
from leg_kinematics_v135 import rotate_vector

class GateQuota:
    def __init__(self, quota, owner, phase):
        self.quota,self.owner,self.phase=quota,owner,phase
    @property
    def active(self):
        return self.quota.active & (self.owner.phase==self.phase)

class PhaseEntry:
    def __init__(self, entry, owner, phase):
        self.entry,self.owner,self.phase=entry,owner,phase
    @property
    def paused(self):
        return self.entry.paused & (self.owner.phase==self.phase)
    @property
    def stable_age(self):
        return torch.where(self.owner.phase==self.phase,2.,0.)

class SupportTransfer:
    def __init__(self,env,quota,entry_hold):
        self.env,self.quota=env,quota
        self.phase=torch.zeros(env.num_envs,dtype=torch.long,device=env.device)
        self.times=torch.full((env.num_envs,3),-1.,device=env.device)
        self.jumps=torch.zeros((env.num_envs,3),device=env.device)
        self.acceleration_jumps=torch.zeros_like(self.jumps)
        self.controllers=[];self.leg_orders=[];self.fk_errors=[]
        canonical=('FL','FR','RL','RR')
        for phase in range(4):
            controller=SingleStep(env,GateQuota(quota,self,phase),entry_hold if phase==0 else PhaseEntry(entry_hold,self,phase))
            order=[phase]+[i for i in range(4) if i!=phase]
            permutation=[3*i+j for i in order for j in range(3)]
            if phase:
                for name in ('ids','slots'):
                    original=getattr(controller,name);setattr(controller,name,[original[i] for i in permutation])
                for name in ('feet','sensor_ids'):
                    original=getattr(controller,name);setattr(controller,name,[original[i] for i in order])
                controller.kin=controller.kin.reordered(tuple(canonical[i] for i in order))
            robot=controller.robot
            fk=rotate_vector(robot.data.root_quat_w[:,None],controller.kin.forward(robot.data.joint_pos[:,controller.ids].reshape(-1,4,3)))+robot.data.root_pos_w[:,None]
            error=float((fk-robot.data.body_pos_w[:,controller.feet]).norm(dim=-1).max())
            assert error<1e-4
            self.fk_errors.append(error);self.controllers.append(controller);self.leg_orders.append([canonical[i] for i in order])
        self.old_apply=self.controllers[-1].c.apply
        self.controllers[-1].c.apply=self.apply

    def apply(self,actions):
        robot=self.controllers[0].robot
        forces=self.env.scene['contact_forces'].data.net_forces_w[:,self.controllers[0].sensor_ids,2]
        calm=(robot.data.root_lin_vel_w.norm(dim=1)<.025)&(robot.data.root_ang_vel_w.norm(dim=1)<.1)
        calm&=robot.data.projected_gravity_b[:,2]<-.96
        ratio=(robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).amax(1)
        transitions=[]
        for target in range(1,4):
            previous,current=self.controllers[target-1:target+1]
            begin=(self.quota.active&(self.phase==target-1)&(previous.step_loaded_age>=2.)
                &(forces>8.).all(1)&calm&previous.valid&(ratio<.98)&(previous.c.geometry_clearance>=.055))
            permutation=[previous.ids.index(j) for j in current.ids]
            transitions.append((begin,previous.reference[:,permutation].clone(),previous.velocity[:,permutation].clone()))
            self.phase=torch.where(begin,target,self.phase)
            self.times[:,target-1]=torch.where(begin,self.env.episode_length_buf*self.env.step_dt,self.times[:,target-1])
        result=self.old_apply(actions)
        for target,(begin,reference,velocity) in enumerate(transitions,1):
            controller=self.controllers[target]
            self.jumps[:,target-1]=torch.where(begin,(controller.reference-reference).abs().amax(1),self.jumps[:,target-1])
            self.acceleration_jumps[:,target-1]=torch.where(begin,((controller.velocity-velocity)/self.env.step_dt).abs().amax(1),self.acceleration_jumps[:,target-1])
        return result

    def summary(self):
        original=os.environ['SUPPORT_TRACE_PATH'];base=Path(original).parent;phases=[]
        try:
            for i,controller in enumerate(self.controllers):
                leg=self.leg_orders[i][0];path=base/f'phase{i}-{leg}-trace.json'
                os.environ['SUPPORT_TRACE_PATH']=str(path);s=controller.summary()
                s.update(physical_leg=leg,leg_order=self.leg_orders[i],trace_file=path.name)
                phases.append(s)
        finally:os.environ['SUPPORT_TRACE_PATH']=original
        return dict(scope='Original-start90s four-foot8cm preparation diagnostic. Frozen v135 physical-leg controller, FL then FR then RL then RR. No box pushing or PUSH acceptance.',
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reordered_fk_errors_m=self.fk_errors,
            final_phase=self.phase.cpu().tolist(),handover_time_s=self.times.cpu().tolist(),
            handover_reference_step_rad=self.jumps.cpu().tolist(),handover_reference_acceleration_rad_s2=self.acceleration_jumps.cpu().tolist(),phases=phases)
