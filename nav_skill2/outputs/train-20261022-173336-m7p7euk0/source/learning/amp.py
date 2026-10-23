"""按行为条件匹配的腿部AMP。正奖励需实际响应，参考成本不因静止而关闭。"""
import hashlib,json
from pathlib import Path
import torch
from torch import nn
from .motion_reference import MotionReference,mirror_transitions
from ..tasks.direct.nav_skill2.parameters import LEG_NAMES
from ..tasks.direct.nav_skill2.commands import MODES

class AMP:
    def __init__(self,cfg,dataset,device):
        self.cfg=cfg
        raw=Path(dataset).read_bytes();data=json.loads(raw)
        if data['format']!='nav_amp_modes_v1' or data['joint_order']!=list(LEG_NAMES) or data['dt']!=.02 or data['modes']!=list(MODES):raise ValueError('AMP data contract mismatch')
        self.dataset_sha256=hashlib.sha256(raw).hexdigest();self.manifest={k:v for k,v in data.items() if k not in ('pairs','labels')}
        expert=torch.tensor(data['pairs'],device=device,dtype=torch.float32)
        labels=torch.tensor(data['labels'],device=device,dtype=torch.long)
        if expert.ndim!=2 or expert.shape[1]!=60 or len(labels)!=len(expert) or not torch.isfinite(expert).all() or set(labels.cpu().tolist())!=set(range(1,7)):raise ValueError('Invalid labeled AMP transitions')
        # 镜像会交换左/右平移与左/右转标签，前进/后退标签保持。
        reflected=torch.tensor([0,1,2,4,3,6,5],device=device)[labels]
        self.expert=torch.cat((expert,mirror_transitions(expert)),0)
        self.labels=torch.cat((labels,reflected))
        self.groups={m:torch.where(self.labels==m)[0] for m in range(1,7)}
        self.references={m:MotionReference(self.expert[ids],.35,4.) for m,ids in self.groups.items()}
        self.features=torch.tensor(list(range(12))+list(range(18,30)),device=device)
        states=self.expert.reshape(-1,30)[:,self.features]
        self.mean=states.mean(0);self.std=torch.maximum(states.std(0,unbiased=False),states.new_tensor([.1]*12+[1.]*12))
        self.discriminator=nn.Sequential(nn.Linear(48+7,512),nn.ReLU(),nn.Linear(512,256),nn.ReLU(),nn.Linear(256,1)).to(device)
        self.optimizer=torch.optim.Adam(self.discriminator.parameters(),lr=cfg.amp_learning_rate)
        self.replay=torch.empty(cfg.replay_capacity,60,device=device)
        self.replay_modes=torch.empty(cfg.replay_capacity,dtype=torch.long,device=device);self.size=self.cursor=0
        self.logs={}

    def normalize(self,pairs,modes):
        state=pairs.reshape(-1,2,30)[:,:,self.features]
        state=((state-self.mean)/self.std).clamp(-10,10).flatten(1)
        return torch.cat((state,torch.nn.functional.one_hot(modes,7).to(state.dtype)),-1)

    @torch.no_grad()
    def transition(self,before,after,g0,g1,done,dt):
        if abs(dt-.02)>1e-8:raise ValueError('AMP needs50Hz')
        modes=g0[:,2].long()
        valid=(modes>0)&(modes==g1[:,2].long())&~done
        gate=torch.minimum(g0[:,0],g1[:,0])*valid
        response=torch.minimum(g0[:,1],g1[:,1])
        valid&=gate>.01
        reward=torch.zeros_like(gate);reference=reward.clone()
        if valid.any():
            pairs=torch.cat((before[valid],after[valid]),-1);labels=modes[valid]
            score=self.discriminator(self.normalize(pairs,labels)).squeeze(-1)
            reward[valid]=self.cfg.amp_reward*dt*(1-.25*(score-1).square()).clamp_min(0)*gate[valid]*response[valid]
            cost=pairs.new_zeros(len(pairs))
            for mode,ref in self.references.items():
                ids=labels==mode
                if ids.any():cost[ids]=ref.cost(pairs[ids])[0]
            reference[valid]=self.cfg.reference_weight*dt*cost*gate[valid]
            pairs=pairs[-len(self.replay):];labels=labels[-len(self.replay):];n=len(pairs)
            ids=(torch.arange(n,device=pairs.device)+self.cursor)%len(self.replay)
            self.replay[ids]=pairs;self.replay_modes[ids]=labels
            self.cursor=(self.cursor+n)%len(self.replay);self.size=min(self.size+n,len(self.replay))
        self.logs={'amp_reward':float(reward.mean()),'amp_reference_cost':float(reference.mean()),'amp_gate':float(gate.mean()),'amp_actual_response':float((response*valid).mean())}
        return reward-reference

    def update(self):
        if not self.size:return {'amp_loss':0.}
        losses=[];device=self.expert.device
        for _ in range(self.cfg.amp_updates):
            ids=torch.randint(self.size,(self.cfg.amp_batch_size,),device=device)
            fake=self.replay[ids];labels=self.replay_modes[ids]
            # 每条策略样本配同类别专家，禁止靠类别频率区分真假。
            real=torch.empty_like(fake)
            for mode,group in self.groups.items():
                mask=labels==mode;n=int(mask.sum())
                if n:real[mask]=self.expert[group[torch.randint(len(group),(n,),device=device)]]
            real=self.normalize(real,labels).detach().requires_grad_(True)
            r=self.discriminator(real);f=self.discriminator(self.normalize(fake,labels))
            grad=torch.autograd.grad(r.sum(),real,create_graph=True)[0]
            loss=.5*((r-1).square().mean()+(f+1).square().mean())+self.cfg.amp_gradient_penalty*grad[:,:48].square().sum(-1).mean()
            if not torch.isfinite(loss):raise FloatingPointError('AMP nonfinite loss')
            self.optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(self.discriminator.parameters(),1.);self.optimizer.step()
            losses.append(float(loss.detach()))
        return {'amp_loss':sum(losses)/len(losses),'amp_replay':self.size,**self.logs}

    def state_dict(self):
        return dict(dataset_sha256=self.dataset_sha256,discriminator=self.discriminator.state_dict(),optimizer=self.optimizer.state_dict(),replay=self.replay[:self.size].clone(),replay_modes=self.replay_modes[:self.size].clone(),cursor=self.cursor,mean=self.mean,std=self.std)

    def load_state_dict(self,state):
        if state['dataset_sha256']!=self.dataset_sha256:raise ValueError('AMP dataset changed')
        self.discriminator.load_state_dict(state['discriminator']);self.optimizer.load_state_dict(state['optimizer'])
        self.size=len(state['replay']);self.replay[:self.size]=state['replay'];self.replay_modes[:self.size]=state['replay_modes'];self.cursor=state['cursor']
        self.mean.copy_(state['mean']);self.std.copy_(state['std'])
