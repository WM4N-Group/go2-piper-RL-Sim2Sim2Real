import torch
from stance_wrench_math import allocate_wrench
feet=torch.tensor([[[.25,-.15,0.],[.25,.15,0.],[-.25,-.15,0.],[-.25,.15,0.]]],dtype=torch.float64)
com=torch.tensor([[.04,0.,.3]],dtype=torch.float64)
for force,moment in [([0.,0.,210.],[0.,0.,0.]),([8.,-6.,210.],[1.,-1.,2.]),([-8.,6.,210.],[-1.,1.,-2.])]:
 f,res=allocate_wrench(feet,com,torch.tensor([force],dtype=torch.float64),torch.tensor([moment],dtype=torch.float64))
 assert res.abs().max()<1e-6,res
 assert (f[:,:,2]>=8).all()
 assert (f[:,:,:2].norm(dim=-1)<=.4*f[:,:,2]+1e-8).all()
 # Independent cross-product verifies wrench sign and column ordering.
 assert torch.allclose(f.sum(1),torch.tensor([force],dtype=torch.float64),atol=1e-6)
 assert torch.allclose(torch.cross(feet-com[:,None],f,dim=-1).sum(1),torch.tensor([moment],dtype=torch.float64),atol=1e-6)
f,res=allocate_wrench(feet,com,torch.tensor([[500.,0.,210.]],dtype=torch.float64),torch.zeros(1,3,dtype=torch.float64))
assert res.abs().max()>10.,'Infeasible wrench must remain visible'
assert (f[:,:,2]>=8.).all() and (f[:,:,:2].norm(dim=-1)<=.4*f[:,:,2]+1e-8).all()
print('4 wrench allocation checks passed: force/moment closure, sign, contact bounds, infeasibility detection')

# Active-constraint regression from v239 seed3702 at4.76s state; old12-iteration
# solver left0.168N force/0.059Nm moment residual despite feasible constraints.
case={'feet': [[[0.10725282962949768, -0.1708417942524704, 0.022393100851340914], [0.17935422854617275, 0.18762714808803524, 0.023127764073873985], [-0.21495014376217797, -0.16141179371261333, 0.022748806278292233], [-0.26389942275448774, 0.13211206436820372, 0.022446961190075387]]], 'com': [[0.08429841697216034, -0.004740423522889614, 0.32631850242614746]], 'force': [[-10.882499694824219, -4.550808429718018, 222.98809814453125]], 'moment': [[1.0540330410003662, -1.1909739971160889, -0.021908778697252274]]}
for dtype in (torch.float32,torch.float64):
    f,res=allocate_wrench(**{k:torch.tensor(v,dtype=dtype) for k,v in case.items()})
    assert res.abs().max()<1e-3,res
    assert (f[:,:,2]>=8.).all()
    assert (f[:,:,:2].norm(dim=-1)<=.4*f[:,:,2]+1e-6).all()
print('Active-constraint regression passed in float32 and float64')
