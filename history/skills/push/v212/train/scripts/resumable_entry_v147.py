"""Used-seed path bank diagnostic; paths not a deployable general planner."""
from pathlib import Path
import json,os,torch
from entry_hold_v125 import EntryHold as FrozenEntryHold
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_push_ik

class BatchedWaypoints:
    def __init__(self,values):
        self.values=values
        self.rows=torch.arange(len(values),device=values.device)
    def __len__(self):return self.values.shape[1]
    def __getitem__(self,index):
        if isinstance(index,torch.Tensor):return self.values[self.rows,index]
        return self.values[:,index]

class EntryHold(FrozenEntryHold):
    def __init__(self,*args,**kwargs):
        self.released=False;self.release_times=None;self.pose_match_checks=0;self.last_match=None
        super().__init__(*args,**kwargs)
        root=Path(os.environ['PUSH_PATH_BANK']);bank=json.loads((root/'prepared-pose-bank.json').read_text())
        assert len(bank['terminal_states'])==self.env.num_envs==8
        assert bank['joint_names']==list(self.robot.joint_names)
        self.snapshots=sorted(bank['terminal_states'],key=lambda x:x['env_id'])
        self.paths=[json.loads((root/f'path-env{i}.json').read_text())['path']['nodes'] for i in range(self.env.num_envs)]
        original_rate=box_push_ik.coordinated_joint_target
        def limited(reference,desired,max_delta):
            if self.released:max_delta=torch.clamp(max_delta,max=.25*self.env.step_dt)
            return original_rate(reference,desired,max_delta)
        box_push_ik.coordinated_joint_target=limited
        original_margin=self.c.geometry_shield.linearized_margin
        def margin(actual,active,value):return original_margin(actual,active,max(value,.065) if self.released else value)
        self.c.geometry_shield.linearized_margin=margin
    def apply(self,actions):
        if self.released:return self.original_apply(actions)
        return super().apply(actions)
    def prepared_pose_matches(self):
        device=self.env.device;dtype=self.robot.data.root_pos_w.dtype
        tensor=lambda values:torch.tensor(values,dtype=dtype,device=device)
        targets=tensor([x['robot_position'] for x in self.snapshots])
        position=(self.robot.data.root_pos_w-self.env.scene.env_origins-targets).norm(dim=1)
        quats=tensor([x['robot_quaternion'] for x in self.snapshots]);alignment=(self.robot.data.root_quat_w*quats).sum(1).abs().clamp(0,1)
        box=tensor([x['box_position'] for x in self.snapshots]);boxerror=(self.env.scene['box'].data.root_pos_w-self.env.scene.env_origins-box).norm(dim=1)
        boxquat=tensor([x['box_quaternion'] for x in self.snapshots]);boxalign=(self.env.scene['box'].data.root_quat_w*boxquat).sum(1).abs().clamp(0,1)
        joints=tensor([x['robot_joint_position'] for x in self.snapshots]);jointerror=(self.robot.data.joint_pos-joints).abs().amax(1)
        ok=(position<.005)&(alignment>0.99995)&(boxerror<.001)&(boxalign>0.99995)&(jointerror<.02)
        self.last_match=dict(position_error_m=position.cpu().tolist(),box_error_m=boxerror.cpu().tolist(),joint_error_rad=jointerror.cpu().tolist(),root_quaternion_abs_dot=alignment.cpu().tolist(),box_quaternion_abs_dot=boxalign.cpu().tolist(),passed=ok.cpu().tolist())
        self.pose_match_checks+=1
        return bool(ok.all())
    def release_original_path(self):
        assert not self.released
        count=max(map(len,self.paths));prefix=self.c.safe_approach_waypoints[:14].clone()
        batches=[]
        for path in self.paths:
            nodes=torch.tensor(path+[path[-1]]*(count-len(path)),device=prefix.device,dtype=prefix.dtype)
            batches.append(torch.cat((prefix,nodes),dim=0))
        self.c.safe_approach_waypoints=BatchedWaypoints(torch.stack(batches))
        self.release_times=(self.env.episode_length_buf*self.env.step_dt).clone();self.released=True
    def summary(self):
        result=super().summary()
        result.update(resume_scope='All8 measured v145 preparation holds, elapsed>=100s and observed pose matched to static audit; per-environment waypoint bank, padded final nodes. Native measured waypoint progression/readiness/contact flags retained. Reference rate tightened to0.25rad/s and soft clearance preference65mm. Physical limits and55mm leg hold guard unchanged. USED3701 fixed-bank diagnostic only.',new_path_released=self.released,release_time_s=self.release_times.cpu().tolist() if self.release_times is not None else None,pose_match_checks=self.pose_match_checks,last_pose_match=self.last_match)
        return result
