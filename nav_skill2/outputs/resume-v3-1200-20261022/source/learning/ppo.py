"""简化PPO+非对称critic；18维均值/执行接口，概率、熵与探索只针对12个腿关节。"""
from pathlib import Path
import copy
import random
import numpy as np
import torch
from torch import nn
from torch.distributions import Normal
from ..tasks.direct.nav_skill2.parameters import ACTOR_OBS,CRITIC_OBS,REVISION

def mlp(inputs,outputs):return nn.Sequential(nn.Linear(inputs,512),nn.ELU(),nn.Linear(512,256),nn.ELU(),nn.Linear(256,128),nn.ELU(),nn.Linear(128,outputs))

class Actor(nn.Module):
    def __init__(self):
        super().__init__();self.network=mlp(ACTOR_OBS,12)
        nn.init.orthogonal_(self.network[-1].weight,gain=.01);nn.init.zeros_(self.network[-1].bias)
    def forward(self,obs):
        legs=3.6*torch.tanh(self.network(obs)/3.6)
        return torch.cat((legs,torch.zeros_like(legs[:,:6])),-1)

class ActorCritic(nn.Module):
    def __init__(self,std=.6):
        super().__init__();self.actor=Actor();self.critic=mlp(CRITIC_OBS,1)
        self.log_std=nn.Parameter(torch.full((12,),float(np.log(std))))
    def distribution(self,obs):return Normal(self.actor(obs)[:,:12],self.log_std.exp().expand(obs.shape[0],-1))
    def value(self,obs):return self.critic(obs).squeeze(-1)

class PPO:
    def __init__(self,model,cfg,amp=None):
        self.model=model;self.cfg=cfg;self.amp=amp;self.iteration=0
        self.optimizer=torch.optim.Adam(model.parameters(),lr=cfg.learning_rate)
        self.learning_rate=cfg.learning_rate

    @torch.no_grad()
    def collect(self,env,obs):
        data={k:[] for k in ['obs','critic','action','logp','value','reward','done','next_value','mean','std']};records=[]
        for _ in range(self.cfg.steps_per_env):
            dist=self.model.distribution(obs['policy']);leg=dist.sample()
            action=torch.cat((leg,leg.new_zeros((len(leg),6))),-1)
            value=self.model.value(obs['critic'])
            before,g0=env.amp_snapshot()
            new_obs,task_reward,terminated,truncated,info=env.step(action)
            done=terminated|truncated
            reward=task_reward.clone()
            if self.amp:
                after,g1=env.amp_snapshot()
                reward+=self.amp.transition(before,after,g0,g1,done,env.step_dt)
            next_value=self.model.value(new_obs['critic'])
            # 超时保留终态bootstrap；真正失败/成功终止value为零。
            timeout=truncated&~terminated
            terminal_value=self.model.value(info['terminal_critic'])
            next_value=torch.where(timeout,terminal_value,next_value)
            next_value=torch.where(terminated,0.,next_value)
            values=[obs['policy'],obs['critic'],leg,dist.log_prob(leg).sum(-1),value,reward,done,next_value,dist.mean,dist.stddev]
            for k,v in zip(data,values):data[k].append(v.detach().clone())
            records.extend(info.get('episode_records',[]));obs=new_obs
        data={k:torch.stack(v) for k,v in data.items()}
        advantage=torch.zeros_like(data['reward']);gae=torch.zeros_like(advantage[0])
        for t in reversed(range(self.cfg.steps_per_env)):
            delta=data['reward'][t]+self.cfg.gamma*data['next_value'][t]-data['value'][t]
            gae=delta+self.cfg.gamma*self.cfg.gae_lambda*(~data['done'][t]).float()*gae
            advantage[t]=gae
        data['returns']=advantage+data['value']
        data['advantage']=(advantage-advantage.mean())/advantage.std(unbiased=False).clamp_min(1e-8)
        return obs,{k:v.flatten(0,1) for k,v in data.items()},records,float(data['reward'].mean())

    def update(self,data):
        n=len(data['action']);metrics=[]
        if n<self.cfg.minibatches:raise ValueError('Rollout smaller than minibatch count')
        for _ in range(self.cfg.epochs):
            for ids in torch.randperm(n,device=data['action'].device).tensor_split(self.cfg.minibatches):
                dist=self.model.distribution(data['obs'][ids]);logp=dist.log_prob(data['action'][ids]).sum(-1)
                value=self.model.value(data['critic'][ids])
                ratio=(logp-data['logp'][ids]).exp();adv=data['advantage'][ids]
                surrogate=-torch.minimum(ratio*adv,ratio.clamp(1-self.cfg.clip,1+self.cfg.clip)*adv).mean()
                clipped_value=data['value'][ids]+(value-data['value'][ids]).clamp(-self.cfg.clip,self.cfg.clip)
                vloss=torch.maximum((value-data['returns'][ids]).square(),(clipped_value-data['returns'][ids]).square()).mean()
                entropy=dist.entropy().sum(-1).mean()
                loss=surrogate+self.cfg.value_coefficient*vloss-self.cfg.entropy_coefficient*entropy
                if not torch.isfinite(loss):raise FloatingPointError('PPO nonfinite loss')
                with torch.no_grad():
                    old_mean=data['mean'][ids];old_std=data['std'][ids]
                    kl=(torch.log(dist.stddev/old_std)+(old_std.square()+(old_mean-dist.mean).square())/(2*dist.stddev.square())-.5).sum(-1).mean()
                    if kl>2*self.cfg.desired_kl:self.learning_rate=max(1e-5,self.learning_rate/1.5)
                    elif kl<.5*self.cfg.desired_kl:self.learning_rate=min(5e-4,self.learning_rate*1.5)
                    for group in self.optimizer.param_groups:group['lr']=self.learning_rate
                self.optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(self.model.parameters(),self.cfg.max_gradient_norm);self.optimizer.step()
                with torch.no_grad():self.model.log_std.clamp_(np.log(.1),np.log(1.))
                metrics.append([float(surrogate.detach()),float(vloss.detach()),float(entropy.detach()),float(kl)])
        self.iteration+=1
        logs=dict(zip(['policy_loss','value_loss','entropy','kl'],np.mean(metrics,axis=0).tolist()))
        logs.update(learning_rate=self.learning_rate,std=float(self.model.log_std.exp().mean().detach()))
        if self.amp:logs.update(self.amp.update())
        return logs

    def save(self,path,config,env):
        path=Path(path)
        state=dict(configuration=config,iteration=self.iteration,model=self.model.state_dict(),optimizer=self.optimizer.state_dict(),learning_rate=self.learning_rate,
            curriculum={'levels':env.levels,'wins':env.wins,'losses':env.losses},amp=self.amp.state_dict() if self.amp else None,
            rng={'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],'numpy':np.random.get_state(),'python':random.getstate()})
        temporary=path.with_suffix('.tmp');torch.save(state,temporary);temporary.replace(path)
        # 导出CPU actor，便于CPU/MuJoCo消费；只复制模块，不迁移或扰动训练模型。
        exported=copy.deepcopy(self.model.actor).cpu().eval()
        torch.jit.script(exported).save(str(path.with_name('actor_'+path.stem.removeprefix('model_')+'.pt')))

    def load(self,state,env):
        if state['configuration']['revision']!=REVISION:raise ValueError('Checkpoint revision mismatch')
        self.model.load_state_dict(state['model']);self.optimizer.load_state_dict(state['optimizer'])
        self.iteration=state['iteration'];self.learning_rate=state['learning_rate']
        if bool(self.amp)!=bool(state['amp']):raise ValueError('AMP configuration mismatch')
        if self.amp:self.amp.load_state_dict(state['amp'])
        for k,v in state['curriculum'].items():
            if len(v)!=env.num_envs:raise ValueError('Resume num_envs must match for curriculum state')
            getattr(env,k).copy_(v)
        rng=state['rng'];torch.set_rng_state(rng['torch'].cpu());np.random.set_state(rng['numpy']);random.setstate(rng['python'])
        if rng['cuda'] and torch.cuda.is_available():torch.cuda.set_rng_state_all([v.cpu() for v in rng['cuda']])
