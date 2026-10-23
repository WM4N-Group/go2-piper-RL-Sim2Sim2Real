"""Seeded CUDA Actor and MuJoCo integration witness; no package installation."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
import mujoco
import scipy
from scipy.optimize import minimize
from bridge import ROOT,load_contract
from velocity_constraints import constrained_model,VelocityClimbBridge

torch.manual_seed(20261020);np.random.seed(20261020)
assert torch.cuda.is_available()
torch.backends.cuda.matmul.allow_tf32=False
c=load_contract();m,_=constrained_model(c['configuration']['task'],.2)
s=VelocityClimbBridge(m,c['configuration']['task'],.2,20261020)
a=torch.jit.load(str(ROOT/'policy/actor.pt'),map_location='cuda').eval()
o=torch.from_numpy(s.observation())[None].cuda()
with torch.inference_mode():y=a(o)
assert y.shape==(1,18) and torch.isfinite(y).all() and torch.all(y[:,12:]==0)
for _ in range(4):s.physics_step()
assert np.isfinite(s.data.qpos).all()
r=minimize(lambda x:float((x*x).sum()),np.array([1.,-2.]),method='SLSQP')
assert r.success and np.linalg.norm(r.x)<1e-5
print('WITNESS '+json.dumps(dict(shape=list(y.shape),device=str(y.device),gpu=torch.cuda.get_device_name(),
    torch=torch.__version__,mujoco=mujoco.__version__,numpy=np.__version__,scipy=scipy.__version__,python=sys.version,
    actor_sha256=c['actor_sha256'],output_sha256=hashlib.sha256(y.cpu().numpy().tobytes()).hexdigest(),
    physics_steps=4,physics_device='CPU',seed=20261020)))
