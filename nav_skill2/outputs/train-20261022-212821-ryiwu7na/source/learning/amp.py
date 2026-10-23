"""按方向/速度条件匹配腿部AMP；保持V3数据读取以供旧配置检查。"""
import hashlib,json
from pathlib import Path
import torch
from torch import nn
from .motion_reference import MotionReference,mirror_transitions
from ..tasks.direct.nav_skill2.parameters import LEG_NAMES
from ..tasks.direct.nav_skill2.commands import MODES

class AMP:
    def __init__(self,cfg,dataset,device):
        self.cfg=cfg;self.speed_conditioned=cfg.amp_speed_conditioning
        raw=Path(dataset).read_bytes();data=json.loads(raw)
        expected='nav_amp_modes_speed_v2' if self.speed_conditioned else 'nav_amp_modes_v1'
        if data['format']!=expected or data['joint_order']!=list(LEG_NAMES) or data['dt']!=.02 or data['modes']!=list(MODES):raise ValueError('AMP data contract mismatch')
        self.dataset_sha256=hashlib.sha256(raw).hexdigest();self.manifest={k:v for k,v in data.items() if k not in ('pairs','labels','reference_speeds')}
        expert=torch.tensor(data['pairs'],device=device,dtype=torch.float32)
        labels=torch.tensor(data['labels'],device=device,dtype=torch.long)
        if expert.ndim!=2 or expert.shape[1]!=60 or len(labels)!=len(expert) or not torch.isfinite(expert).all() or set(labels.cpu().tolist())!=set(range(1,7)):raise ValueError('Invalid labeled AMP transitions')
        speeds=torch.tensor(data['reference_speeds'],device=device) if self.speed_conditioned else torch.zeros(len(expert),device=device)
        if speeds.shape!=labels.shape or not torch.isfinite(speeds).all() or (self.speed_conditioned and (speeds<=0).any()):raise ValueError('Invalid expert speed labels')
        reflected=torch.tensor([0,1,2,4,3,6,5],device=device)[labels]
        self.expert=torch.cat((expert,mirror_transitions(expert)),0)
        self.labels=torch.cat((labels,reflected));self.expert_speeds=torch.cat((speeds,speeds))
        keys=sorted(set(zip(self.labels.cpu().tolist(),self.expert_speeds.cpu().tolist())))
        self.group_modes=torch.tensor([0]+[m for m,_ in keys],device=device)
        self.group_speeds=torch.tensor([0.]+[v for _,v in keys],device=device)
        self.groups={i:torch.where((self.labels==m)&(self.expert_speeds==v))[0] for i,(m,v) in enumerate(keys,1)}
        self.references={i:MotionReference(self.expert[ids],.35,4.) for i,ids in self.groups.items()}
        self.features=torch.tensor(list(range(12))+list(range(18,30)),device=device)
        states=self.expert.reshape(-1,30)[:,self.features]
        self.mean=states.mean(0);self.std=torch.maximum(states.std(0,unbiased=False),states.new_tensor([.1]*12+[1.]*12))
        self.discriminator=nn.Sequential(nn.Linear(48+7+int(self.speed_conditioned),512),nn.ReLU(),nn.Linear(512,256),nn.ReLU(),nn.Linear(256,1)).to(device)
        self.optimizer=torch.optim.Adam(self.discriminator.parameters(),lr=cfg.amp_learning_rate)
        self.replay=torch.empty(cfg.replay_capacity,60,device=device)
        self.replay_modes=torch.empty(cfg.replay_capacity,dtype=torch.long,device=device)
        self.replay_groups=torch.empty_like(self.replay_modes);self.size=self.cursor=0;self.logs={}

    def select_groups(self,modes,speeds=None):
        if not self.speed_conditioned:return modes
        if speeds is None:raise ValueError('Speed-conditioned AMP requires command amplitude')
        distance=(speeds[:,None]-self.group_speeds[None,1:]).abs()
        distance=distance.masked_fill(modes[:,None]!=self.group_modes[None,1:],float('inf'))
        return distance.argmin(-1)+1

    def normalize(self,pairs,modes,speeds=None):
        state=pairs.reshape(-1,2,30)[:,:,self.features]
        state=((state-self.mean)/self.std).clamp(-10,10).flatten(1)
        features=[state,torch.nn.functional.one_hot(modes,7).to(state.dtype)]
        if self.speed_conditioned:
            if speeds is None:raise ValueError('Missing AMP speed condition')
            features.append(speeds[:,None].to(state.dtype))
        return torch.cat(features,-1)

    @torch.no_grad()
    def transition(self,before,after,g0,g1,done,dt):
        if abs(dt-.02)>1e-8:raise ValueError('AMP needs50Hz')
        if self.speed_conditioned and (g0.shape[1]<4 or g1.shape[1]<4):raise ValueError('AMP needs command speed metadata')
        modes=g0[:,2].long()
        groups=self.select_groups(modes,g0[:,3] if self.speed_conditioned else None)
        next_groups=self.select_groups(g1[:,2].long(),g1[:,3] if self.speed_conditioned else None)
        valid=(modes>0)&(modes==g1[:,2].long())&(groups==next_groups)&~done
        gate=torch.minimum(g0[:,0],g1[:,0])*valid
        response=torch.minimum(g0[:,1],g1[:,1]);valid&=gate>.01
        reward=torch.zeros_like(gate);reference=reward.clone()
        if valid.any():
            pairs=torch.cat((before[valid],after[valid]),-1);labels=modes[valid];selected=groups[valid]
            score=self.discriminator(self.normalize(pairs,labels,self.group_speeds[selected])).squeeze(-1)
            reward[valid]=self.cfg.amp_reward*dt*(1-.25*(score-1).square()).clamp_min(0)*gate[valid]*response[valid]
            cost=pairs.new_zeros(len(pairs))
            for group,ref in self.references.items():
                ids=selected==group
                if ids.any():cost[ids]=ref.cost(pairs[ids])[0]
            reference[valid]=self.cfg.reference_weight*dt*cost*gate[valid]
            pairs=pairs[-len(self.replay):];labels=labels[-len(self.replay):];selected=selected[-len(self.replay):];n=len(pairs)
            ids=(torch.arange(n,device=pairs.device)+self.cursor)%len(self.replay)
            self.replay[ids]=pairs;self.replay_modes[ids]=labels;self.replay_groups[ids]=selected
            self.cursor=(self.cursor+n)%len(self.replay);self.size=min(self.size+n,len(self.replay))
        self.logs={'amp_reward':float(reward.mean()),'amp_reference_cost':float(reference.mean()),'amp_gate':float(gate.mean()),'amp_actual_response':float((response*valid).mean())}
        return reward-reference

    def update(self):
        if not self.size:return {'amp_loss':0.}
        losses=[];device=self.expert.device
        for _ in range(self.cfg.amp_updates):
            ids=torch.randint(self.size,(self.cfg.amp_batch_size,),device=device)
            fake=self.replay[ids];labels=self.replay_modes[ids];selected=self.replay_groups[ids]
            # 同方向、同速度组配对；不能靠指令类别或速度分布判断真假。
            real=torch.empty_like(fake)
            for key,group in self.groups.items():
                mask=selected==key;n=int(mask.sum())
                if n:real[mask]=self.expert[group[torch.randint(len(group),(n,),device=device)]]
            speed=self.group_speeds[selected]
            real=self.normalize(real,labels,speed).detach().requires_grad_(True)
            r=self.discriminator(real);f=self.discriminator(self.normalize(fake,labels,speed))
            grad=torch.autograd.grad(r.sum(),real,create_graph=True)[0]
            loss=.5*((r-1).square().mean()+(f+1).square().mean())+self.cfg.amp_gradient_penalty*grad[:,:48].square().sum(-1).mean()
            if not torch.isfinite(loss):raise FloatingPointError('AMP nonfinite loss')
            self.optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(self.discriminator.parameters(),1.);self.optimizer.step();losses.append(float(loss.detach()))
        return {'amp_loss':sum(losses)/len(losses),'amp_replay':self.size,**self.logs}

    def state_dict(self):
        return dict(dataset_sha256=self.dataset_sha256,speed_conditioned=self.speed_conditioned,discriminator=self.discriminator.state_dict(),optimizer=self.optimizer.state_dict(),replay=self.replay[:self.size].clone(),replay_modes=self.replay_modes[:self.size].clone(),replay_groups=self.replay_groups[:self.size].clone(),cursor=self.cursor,mean=self.mean,std=self.std)

    def load_state_dict(self,state):
        if state['dataset_sha256']!=self.dataset_sha256 or state.get('speed_conditioned',False)!=self.speed_conditioned:raise ValueError('AMP dataset/conditioning changed')
        self.discriminator.load_state_dict(state['discriminator']);self.optimizer.load_state_dict(state['optimizer'])
        self.size=len(state['replay']);self.replay[:self.size]=state['replay'];self.replay_modes[:self.size]=state['replay_modes']
        self.replay_groups[:self.size]=state.get('replay_groups',state['replay_modes']);self.cursor=state['cursor'];self.mean.copy_(state['mean']);self.std.copy_(state['std'])
