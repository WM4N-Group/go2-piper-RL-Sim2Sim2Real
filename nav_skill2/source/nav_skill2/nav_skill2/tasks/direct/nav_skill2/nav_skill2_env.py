"""平地全方向速度条件行走：起步、前后侧移、转向、减速和站稳。没有目标点输入。"""
import re
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.sensors import ContactSensor
from isaaclab.utils.math import quat_from_euler_xyz,quat_apply,quat_mul
from .parameters import JOINT_NAMES,FOOT_NAMES,FRAME,HISTORY
from .commands import sample_commands,smooth_commands,tracking_quality,motion_terms,command_modes,startup_action_gain

class NavSkill2Env(DirectRLEnv):
    def __init__(self,cfg,render_mode=None,**kwargs):
        super().__init__(cfg,render_mode=render_mode,**kwargs)
        self.task=cfg.task
        self.joint_ids,names=self.robot.find_joints(list(JOINT_NAMES),preserve_order=True)
        if tuple(names)!=JOINT_NAMES or self.robot.num_joints!=18:raise ValueError('Robot joint contract differs')
        self.foot_ids,_=self.robot.find_bodies(list(FOOT_NAMES),preserve_order=True)
        self.contact_feet,_=self.contact.find_bodies(list(FOOT_NAMES),preserve_order=True)
        self.forbidden=[i for i,n in enumerate(self.contact.body_names) if not re.fullmatch(r'(?:FL|FR|RL|RR)_(?:foot|hip|thigh|calf)',n)]
        if not self.forbidden:raise ValueError('Base/arm contact links missing')
        z=lambda *s:torch.zeros(self.num_envs,*s,device=self.device)
        self.actions=z(18);self.previous_actions=z(18)
        self.reference=self.robot.data.default_joint_pos[:,self.joint_ids].clone()
        self.targets=self.reference.clone();self.previous_qd=z(18)
        self.commands=z(3);self.desired_commands=z(3)
        self.command_deadline=z();self.command_sample_time=z();self.command_last_elapsed=z()
        self.levels=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        if not self.task.curriculum:self.levels[:]=self.task.levels-1
        self.wins=self.levels.clone()*0;self.losses=self.wins.clone()
        self.success=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        self.failure=self.success.clone();self.standing=self.success.clone();self.arm_bad=z()
        self.episode_return=z();self.linear_error_sq=z();self.yaw_error_sq=z()
        self.tracking_count=z();self.motion_seconds=z();self.command_energy=z()
        self.response_sum=z(7);self.response_count=z(7);self.good_count=z();self.stop_bad=z();self.stop_count=z()
        self.history=z(HISTORY,FRAME);self.fresh=torch.ones_like(self.success);self.obs_stamp=-1
        self.command_stamp=-1;self.state_stamp=-1;self.reward_terms={}
        self.privileged=z(29)
        from .randomization import randomize_physics
        randomize_physics(self)
        # 从本USD的真实足底球和初始化FK推导贴地根高度，避免从0.35m自由落下。
        self.grounded_height=self._grounded_height()
        print(f'[NAV2] Grounded initial base height: {self.grounded_height:.5f}m',flush=True)
        self.manual_commands=False
        self.settled_root=None;self.settled_q=None
        if self.task.reset_settle_seconds>0:self._prepare_settled_reset()

    def _grounded_height(self):
        # 初始化link transform仍可能是USD导入姿态，不能据此计算默认站姿的贴地高度。
        # 先写默认q，在空中推进一个5ms物理步刷新FK；之后reset才是训练回合的起点。
        root_state=self.robot.data.default_root_state.clone()
        root_state[:,:3]+=self.scene.env_origins;root_state[:,2]=self.scene.env_origins[:,2]+.65
        root_state[:,7:]=0.
        q=self.robot.data.default_joint_pos.clone()
        self.robot.write_root_state_to_sim(root_state)
        self.robot.write_joint_state_to_sim(q,torch.zeros_like(q))
        self.robot.set_joint_position_target(q)
        self.scene.write_data_to_sim();self.sim.step(render=False);self.scene.update(self.physics_dt)
        from pxr import Usd,UsdGeom
        stage=Usd.Stage.Open(self.robot.cfg.spawn.usd_path);root=stage.GetDefaultPrim();cache=UsdGeom.XformCache()
        offsets=[];radii=[]
        for body_id in self.foot_ids:
            foot=stage.GetPrimAtPath(str(root.GetPath())+'/'+self.robot.body_names[body_id])
            sphere=stage.GetPrimAtPath(str(foot.GetPath())+'/collisions/mesh_0/sphere')
            if not sphere.IsA(UsdGeom.Sphere):raise ValueError('Unsupported foot collider')
            transform,_=cache.ComputeRelativeTransform(sphere,foot)
            offsets.append(list(transform.ExtractTranslation()));radii.append(UsdGeom.Sphere(sphere).GetRadiusAttr().Get())
        off=torch.tensor(offsets,device=self.device)[None].expand(self.num_envs,-1,-1)
        center=self.robot.data.body_pos_w[:,self.foot_ids]+quat_apply(self.robot.data.body_quat_w[:,self.foot_ids],off)
        bottom=center[:,:,2]-torch.tensor(radii,device=self.device)
        return float(self.robot.data.root_pos_w[0,2]-bottom[0].min()+.002)

    def _prepare_settled_reset(self):
        """一次性用真实PD/重力/随机化参数建立承重平衡，后续reset复用各环境状态。

        不改默认关节目标、不增大力矩、不焊接机身。缓存实际受力后的q而不是把
        默认q与更低的根高度拼接（后者会让足底穿地）。不计入策略回合或奖励。
        """
        root=self.robot.data.default_root_state.clone()
        root[:,:3]+=self.scene.env_origins
        root[:,2]=self.scene.env_origins[:,2]+self.grounded_height;root[:,7:]=0.
        q=self.robot.data.default_joint_pos.clone()
        self.robot.reset();self.robot.write_root_state_to_sim(root)
        self.robot.write_joint_state_to_sim(q,torch.zeros_like(q))
        self.targets.copy_(self.reference)
        settle_steps=round(self.task.reset_settle_seconds/self.physics_dt)
        max_steps=round(self.task.reset_settle_max_seconds/self.physics_dt)
        # 各随机化环境在各自收敛时缓存；不能等所有环境同一时刻安静，
        # 否则已落稳的环境可能在等待另一环境时再次滑移。
        ready=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        cached_root=root.clone();cached_q=q.clone();settle_times=torch.zeros(self.num_envs,device=self.device)
        for step in range(max_steps):
            self._apply_action();self.scene.write_data_to_sim()
            self.sim.step(render=False);self.scene.update(self.physics_dt)
            if (step+1)%200==0:
                print(f'[NAV2] Preparing loaded reset {step+1}/{max_steps} (ready {int(ready.sum())}/{self.num_envs})',flush=True)
            if step+1>=settle_steps and (step+1-settle_steps)%20==0:
                root=self.robot.data.root_state_w.clone();q=self.robot.data.joint_pos.clone()
                tilt=torch.acos((-self.robot.data.projected_gravity_b[:,2]).clamp(-1,1))
                supports=(self.contact.data.net_forces_w[:,self.contact_feet].norm(dim=-1)>3.).sum(-1)
                forbidden_force=self.contact.data.net_forces_w[:,self.forbidden].norm(dim=-1).amax(-1)
                settled=(torch.isfinite(root).all(-1)&torch.isfinite(q).all(-1)
                    &(tilt<self.task.reset_settle_max_tilt)&(self.robot.data.root_lin_vel_w.norm(dim=-1)<.05)
                    &(self.robot.data.joint_vel.abs().amax(-1)<.3)
                    &(root[:,2]-self.scene.env_origins[:,2]>.2)
                    &(supports>=3)&(forbidden_force<=self.task.contact_failure_force))
                new=settled&~ready
                cached_root[new]=root[new];cached_q[new]=q[new];settle_times[new]=(step+1)*self.physics_dt
                ready|=settled
                if bool(ready.all()):break
        self.settle_elapsed_seconds=(step+1)*self.physics_dt
        if not bool(ready.all()):
            bad=~ready
            print(f'[NAV2] Unsettled IDs={bad.nonzero().flatten().tolist()}, tilt={tilt[bad].tolist()}, v={self.robot.data.root_lin_vel_w[bad].norm(dim=-1).tolist()}, qd={self.robot.data.joint_vel[bad].abs().amax(-1).tolist()}, supports={supports[bad].tolist()}, forbidden={forbidden_force[bad].tolist()}',flush=True)
            raise RuntimeError(f'Static reset preparation did not settle: {int(bad.sum())}/{self.num_envs} environments; tilt_max={float(tilt[bad].max()):.4f}, linear_speed_max={float(self.robot.data.root_lin_vel_w[bad].norm(dim=-1).max()):.4f}, joint_speed_max={float(self.robot.data.joint_vel[bad].abs().max()):.4f}, supports_min={int(supports[bad].min())}, forbidden_force_max={float(forbidden_force[bad].max()):.4f}; check PD/asset/randomization')
        root=cached_root;q=cached_q
        print(f'[NAV2] Loaded reset converged per environment in {float(settle_times.min()):.2f}..{float(settle_times.max()):.2f}s',flush=True)
        self.settled_root=root.clone();self.settled_root[:,:3]-=self.scene.env_origins
        self.settled_root[:,7:]=0.;self.settled_q=q.clone()
        print(f'[NAV2] Loaded reset height: {self.settled_root[:,2].min():.5f}..{self.settled_root[:,2].max():.5f}m',flush=True)

    def _setup_scene(self):
        self.robot=Articulation(self.cfg.robot);self.contact=ContactSensor(self.cfg.contact)
        self.scene.articulations['robot']=self.robot;self.scene.sensors['contact']=self.contact
        ground=sim_utils.GroundPlaneCfg(physics_material=self.cfg.sim.physics_material)
        ground.func('/World/ground',ground)
        self.scene.clone_environments(copy_from_source=False)
        self.scene.filter_collisions(global_prim_paths=['/World/ground'])
        light=sim_utils.DomeLightCfg(intensity=2000.,color=(.75,.75,.75));light.func('/World/Light',light)

    def _update_commands(self):
        if self.command_stamp==self.common_step_counter:return
        self.command_stamp=self.common_step_counter
        elapsed=self.episode_length_buf*self.step_dt
        if not self.manual_commands:
            ids=torch.where(elapsed>=self.command_deadline)[0]
            if self.task.terminal_stop_seconds>0:
                ids=ids[elapsed[ids]<self.task.episode_seconds-self.task.terminal_stop_seconds]
            if len(ids):self._resample_commands(ids,elapsed[ids])
            if self.task.terminal_stop_seconds>0:
                stopping=elapsed>=self.task.episode_seconds-self.task.terminal_stop_seconds
                entering=stopping&~self.standing
                self.command_sample_time[entering]=elapsed[entering]
                self.desired_commands[stopping]=0.;self.standing[stopping]=True
        gain=((elapsed-self.task.startup_seconds)/self.task.command_ramp_seconds).clamp(0,1)
        desired=self.desired_commands*gain[:,None]
        dt=(elapsed-self.command_last_elapsed).clamp_min(0)
        self.commands[:]=smooth_commands(self.commands,desired,dt,self.task)
        self.command_last_elapsed.copy_(elapsed)

    def _resample_commands(self,ids,elapsed):
        self.desired_commands[ids]=sample_commands(self.levels[ids],self.task)
        self.standing[ids]=self.desired_commands[ids].abs().sum(-1)==0
        self.command_sample_time[ids]=elapsed
        lo,hi=self.task.command_seconds_range
        self.command_deadline[ids]=elapsed+lo+torch.rand(len(ids),device=self.device)*(hi-lo)

    def set_velocity_command(self,command):
        """持续机身坐标[vx,vy,wz]；不reset，不瞬间跳变。后续上层Nav调用此接口。"""
        value=torch.as_tensor(command,device=self.device,dtype=torch.float32).expand(self.num_envs,3)
        if not torch.isfinite(value).all():raise ValueError('Nonfinite command')
        speed=torch.tensor(self.task.speed_limits,device=self.device)[self.levels]
        yaw=torch.tensor(self.task.yaw_rate_limits,device=self.device)[self.levels]
        backward=torch.tensor(self.task.backward_speed_limits if self.task.backward_speed_limits is not None else self.task.speed_limits,device=self.device)[self.levels]
        lateral=torch.tensor(self.task.lateral_speed_limits,device=self.device)[self.levels]
        if ((value[:,0]>speed+1e-6)|(value[:,0]<-backward-1e-6)).any() or (value[:,1].abs()>lateral+1e-6).any() or (value[:,:2].norm(dim=-1)>speed+1e-6).any() or (value[:,2].abs()>yaw+1e-6).any():raise ValueError('Command outside trained XY/yaw range')
        changed=(value-self.desired_commands).abs().amax(-1)>1e-6
        self.command_sample_time[changed]=self.episode_length_buf[changed]*self.step_dt
        self.desired_commands.copy_(value);self.manual_commands=True
        self.standing[:]=value.abs().sum(-1)==0
        self.command_stamp=-1

    def _pre_physics_step(self,actions):
        if actions.shape!=(self.num_envs,18) or not torch.isfinite(actions).all():raise ValueError('Expected finite18D actions')
        self.extras['episode_records']=[]
        self.previous_actions.copy_(self.actions)
        self.previous_qd.copy_(self.robot.data.joint_vel[:,self.joint_ids])
        self.actions=actions.detach().clone().clamp(-self.task.max_position_offset/self.task.action_scale,self.task.max_position_offset/self.task.action_scale)
        gain=startup_action_gain(self.episode_length_buf*self.step_dt,self.task.startup_action_ramp_seconds)
        self.actions[:,:12]*=gain[:,None]
        self.actions[:,12:]=0.
        self.targets=self.reference+self.task.action_scale*self.actions
        limits=self.robot.data.soft_joint_pos_limits[:,self.joint_ids]
        self.targets[:,:12]=self.targets[:,:12].clamp(limits[:,:12,0],limits[:,:12,1])
        self.targets[:,12:]=0.

    def _apply_action(self):
        self.robot.set_joint_position_target(self.targets,joint_ids=self.joint_ids)
        if self.task.arm_gravity_compensation:
            gravity=self.robot.root_physx_view.get_gravity_compensation_forces()
            if gravity.shape[-1]!=self.robot.num_joints+6:raise ValueError('Unexpected floating-base compensation')
            self.robot.set_joint_effort_target(gravity[:,6:][:,self.joint_ids[12:]],joint_ids=self.joint_ids[12:])

    def _update_status(self):
        if self.state_stamp==self.common_step_counter:return
        self.state_stamp=self.common_step_counter
        vel=self.robot.data.root_lin_vel_b;omega=self.robot.data.root_ang_vel_b
        g=self.robot.data.projected_gravity_b;tilt=torch.acos((-g[:,2]).clamp(-1,1))
        q=self.robot.data.joint_pos[:,self.joint_ids]
        arm=q[:,12:].abs().amax(-1)
        self.arm_bad=torch.where(arm>self.task.failure_arm_error,self.arm_bad+self.step_dt,0.)
        force=self.contact.data.net_forces_w_history[:, :,self.forbidden].norm(dim=-1).amax(dim=(1,2))
        self.failure=(tilt>self.task.failure_tilt)|(self.robot.data.root_pos_w[:,2]-self.scene.env_origins[:,2]<.15)|(force>self.task.contact_failure_force)|(self.arm_bad>self.task.failure_arm_seconds)
        elapsed=self.episode_length_buf*self.step_dt
        valid=(elapsed>=max(self.task.startup_seconds+self.task.command_ramp_seconds,self.task.startup_action_ramp_seconds))&(elapsed-self.command_sample_time>=self.task.tracking_grace_seconds)
        self.linear_error_sq+=valid*(vel[:,:2]-self.commands[:,:2]).square().sum(-1)
        self.yaw_error_sq+=valid*(omega[:,2]-self.commands[:,2]).square()
        self.command_energy+=valid*(self.commands[:,:2].square().sum(-1)+.25*self.commands[:,2].square())
        self.tracking_count+=valid
        moving=(self.commands[:,:2].norm(dim=-1)>.05)|(self.commands[:,2].abs()>.1)
        self.motion_seconds+=valid*moving*self.step_dt
        _,response,good=motion_terms(self.commands,vel,omega,self.task)
        modes=command_modes(self.commands)
        active=valid&moving
        self.response_sum.scatter_add_(1,modes[:,None],(response.clamp(0,1)*active)[:,None])
        self.response_count.scatter_add_(1,modes[:,None],active.float()[:,None])
        self.good_count+=good*active
        stopped=valid&~moving
        self.stop_count+=stopped
        self.stop_bad+=stopped*((vel[:,:2].norm(dim=-1)>.1)|(omega[:,2].abs()>.2))
        self.success[:]=self._quality()[0]

    def _quality(self):
        return tracking_quality(self.linear_error_sq,self.yaw_error_sq,self.tracking_count,self.motion_seconds,self.failure,self.task,self.command_energy,self.response_sum,self.response_count,self.good_count,self.stop_bad,self.stop_count)

    def _get_dones(self):
        self._update_status()
        # 合格是完整回合的课程指标，不是提前reset或一次性成功奖励。
        return self.failure,self.episode_length_buf>=self.max_episode_length-1

    def _get_rewards(self):
        v=self.robot.data.root_lin_vel_b;w=self.robot.data.root_ang_vel_b
        q=self.robot.data.joint_pos[:,self.joint_ids];qd=self.robot.data.joint_vel[:,self.joint_ids]
        forces=self.contact.data.net_forces_w[:,self.contact_feet]
        loaded=forces.norm(dim=-1)>3.
        feet_vel=self.robot.data.body_lin_vel_w[:,self.foot_ids,:2]
        stop=(self.commands[:,:2].norm(dim=-1)<.06)&(self.commands[:,2].abs()<.12)
        limits=self.robot.data.soft_joint_pos_limits[:,self.joint_ids[:12]]
        cost_limits=(limits[...,0]-q[:,:12]).clamp_min(0)+(q[:,:12]-limits[...,1]).clamp_min(0)
        locomotion,_,_=motion_terms(self.commands,v,w,self.task)
        terms=dict(**locomotion,
            stationary=stop*torch.exp(-v[:,:2].square().sum(-1)/.01-w[:,2].square()/.04),
            standing_posture=stop*(q[:,:12]-self.reference[:,:12]).square().mean(-1),
            upright=self.robot.data.projected_gravity_b[:,:2].square().sum(-1),
            base_height=(self.robot.data.root_pos_w[:,2]-self.scene.env_origins[:,2]-self.task.target_base_height).square(),
            vertical_velocity=v[:,2].square(),roll_pitch_rate=w[:,:2].square().sum(-1),
            action_rate=(self.actions[:,:12]-self.previous_actions[:,:12]).square().sum(-1),
            joint_acceleration=((qd[:,:12]-self.previous_qd[:,:12])/self.step_dt).square().sum(-1),
            torque=self.robot.data.applied_torque[:,self.joint_ids[:12]].square().sum(-1),
            foot_slip=(feet_vel.square().sum(-1)*loaded).sum(-1),
            collision=(self.contact.data.net_forces_w_history.norm(dim=-1).amax(1)>8.).float()[:,self.forbidden].sum(-1),
            joint_limit=cost_limits.sum(-1),arm_error=q[:,12:].square().sum(-1),
            flight=(~loaded.any(-1)).float())
        self.reward_terms={k:float((terms[k]*weight).mean()) for k,weight in self.task.rewards.items()}
        reward=sum(terms[k]*weight for k,weight in self.task.rewards.items())*self.step_dt
        reward+=self.failure*self.task.failure_penalty
        self.episode_return+=reward
        # 超时bootstrap必须使用reset前状态；不把下一回合初始状态当作终态。
        self.extras['terminal_critic']=self._get_observations()['critic'].detach().clone()
        return reward

    def _get_observations(self):
        self._update_commands()
        q=self.robot.data.joint_pos[:,self.joint_ids]-self.reference
        qd=self.robot.data.joint_vel[:,self.joint_ids]*.05
        frame=torch.cat((self.robot.data.root_ang_vel_b*.25,self.robot.data.projected_gravity_b,q,qd,self.actions,self.commands),-1).clamp(-10,10)
        if frame.shape[-1]!=FRAME:raise ValueError('Observation dimension mismatch')
        if self.obs_stamp!=self.common_step_counter:
            self.history=torch.roll(self.history,-1,dims=1)
            self.obs_stamp=self.common_step_counter
        # 同一步重复读取观测不推进历史；指令按真实时间平滑。
        self.history[:,-1]=frame
        # reset补齐历史；同一步重复读取不能额外推进历史。
        self.history[self.fresh]=frame[self.fresh,None].expand(-1,HISTORY,-1);self.fresh[:]=False
        actor=self.history.flatten(1)
        loaded=(self.contact.data.net_forces_w[:,self.contact_feet].norm(dim=-1)>3.).float()
        critic=torch.cat((actor,self.robot.data.root_lin_vel_b,loaded,self.privileged[:,[0,4]]),-1)
        return {'policy':actor,'critic':critic}

    def amp_snapshot(self):
        # 指令选真实参考类别；正AMP按实际响应门控，参考成本不能靠不动关闭。
        q=self.robot.data.joint_pos[:,self.joint_ids[:12]];qd=self.robot.data.joint_vel[:,self.joint_ids[:12]]
        state=torch.cat((q,self.robot.data.root_lin_vel_b,self.robot.data.root_ang_vel_b,qd),-1)
        modes=command_modes(self.commands)
        _,response,_=motion_terms(self.commands,self.robot.data.root_lin_vel_b,self.robot.data.root_ang_vel_b,self.task)
        speed=self.commands[:,:2].norm(dim=-1)
        gate=torch.maximum(speed/.15,self.commands[:,2].abs()/.2).clamp(0,1)
        # 混合/斜向没有精确示范，给动力学适应空间。
        mixed=((speed>.05)&(self.commands[:,2].abs()>.1))|((self.commands[:,0].abs()>.05)&(self.commands[:,1].abs()>.05))
        gate*=torch.where(mixed,.6,1.)
        # 新初始化渐入未结束时，不要求被执行层衰减的动作立刻匹配行走参考。
        gate*=(self.episode_length_buf*self.step_dt>=self.task.startup_action_ramp_seconds)
        return state,torch.stack((gate,response.clamp(0,1),modes.float(),torch.where(modes>=5,self.commands[:,2].abs(),speed)),-1)

    def _reset_idx(self,env_ids):
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        if not hasattr(self,'levels'):
            super()._reset_idx(env_ids);return
        completed=self.episode_length_buf[env_ids]>0
        qualified,eligible,linear,yaw_error=self._quality()
        won=qualified[env_ids]&completed&~self.failure[env_ids]
        for i in env_ids[completed].tolist():
            self.extras.setdefault('episode_records',[]).append(dict(success=bool(qualified[i]),failed=bool(self.failure[i]),timeout=not bool(self.failure[i]),level=int(self.levels[i]),standing=not bool(eligible[i]),eligible=bool(eligible[i]),linear_rmse=float(linear[i]),yaw_rmse=float(yaw_error[i]),motion_seconds=float(self.motion_seconds[i]),relative_error=float(((self.linear_error_sq[i]+.25*self.yaw_error_sq[i])/self.command_energy[i].clamp_min(1e-8)).sqrt()),direction_response=float(self.response_sum[i].sum()/self.response_count[i].sum().clamp_min(1)),good_motion_fraction=float(self.good_count[i]/self.response_count[i].sum().clamp_min(1)),mode_response=(self.response_sum[i]/self.response_count[i].clamp_min(1)).tolist(),mode_samples=self.response_count[i].tolist(),return_=float(self.episode_return[i]),seconds=float(self.episode_length_buf[i]*self.step_dt)))
        if self.task.curriculum:
            # 纯站立不升级；运动回合失败计入降级，不能靠摔倒逃避课程统计。
            active=completed&(eligible[env_ids]|self.failure[env_ids])
            self.wins[env_ids]=torch.where(active,torch.where(won,self.wins[env_ids]+1,0),self.wins[env_ids])
            self.losses[env_ids]=torch.where(active,torch.where(~won,self.losses[env_ids]+1,0),self.losses[env_ids])
            up=self.wins[env_ids]>=self.task.promote_successes;down=self.losses[env_ids]>=self.task.demote_failures
            self.levels[env_ids]=(self.levels[env_ids]+up.long()-down.long()).clamp(0,self.task.levels-1)
            self.wins[env_ids]*=~up;self.losses[env_ids]*=~down
        super()._reset_idx(env_ids)
        n=len(env_ids);root=self.robot.data.default_root_state[env_ids].clone();root[:,:3]+=self.scene.env_origins[env_ids]
        root[:,2]=self.scene.env_origins[env_ids,2]+self.grounded_height;root[:,7:]=0.
        yaw=torch.empty(n,device=self.device).uniform_(-3.141593,3.141593)
        root[:,3:7]=quat_from_euler_xyz(yaw*0,yaw*0,yaw)
        q=self.robot.data.default_joint_pos[env_ids].clone()
        if self.settled_root is not None:
            # 随机yaw只旋转已落稳姿态；承重q、根高和PD默认目标保持匹配。
            root[:,2]=self.scene.env_origins[env_ids,2]+self.settled_root[env_ids,2]
            root[:,3:7]=quat_mul(root[:,3:7],self.settled_root[env_ids,3:7])
            q=self.settled_q[env_ids].clone()
        self.robot.write_root_state_to_sim(root,env_ids)
        self.robot.write_joint_state_to_sim(q,torch.zeros_like(q),env_ids=env_ids)
        self.reference[env_ids]=self.robot.data.default_joint_pos[env_ids][:,self.joint_ids];self.targets[env_ids]=self.reference[env_ids]
        self.robot.set_joint_position_target(self.targets[env_ids],joint_ids=self.joint_ids,env_ids=env_ids)
        self.robot.set_joint_effort_target(torch.zeros(n,6,device=self.device),joint_ids=self.joint_ids[12:],env_ids=env_ids)
        self._resample_commands(env_ids,torch.zeros(n,device=self.device))
        for buf in [self.actions,self.previous_actions,self.commands,self.success,self.failure,self.arm_bad,self.episode_return,self.previous_qd,self.linear_error_sq,self.yaw_error_sq,self.tracking_count,self.motion_seconds,self.command_energy,self.command_last_elapsed,self.response_sum,self.response_count,self.good_count,self.stop_bad,self.stop_count]:buf[env_ids]=0
        self.fresh[env_ids]=True;self.command_stamp=-1
