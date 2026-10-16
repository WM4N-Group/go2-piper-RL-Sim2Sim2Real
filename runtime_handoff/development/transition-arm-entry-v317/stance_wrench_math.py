"""Four-contact wrench allocation; explicit unilateral/friction projection audit."""
import torch

def allocate_wrench(feet, com, force, moment, minimum_normal=8., friction=.4):
    lever=feet-com[:,None]
    x,y,z=lever.unbind(-1);zero=torch.zeros_like(x)
    skew=torch.stack((zero,-z,y,z,zero,-x,-y,x,zero),-1).reshape(-1,4,3,3)
    identity=torch.eye(3,device=feet.device,dtype=feet.dtype).expand(feet.shape[0],4,3,3)
    matrix=torch.cat((identity,skew),dim=2).permute(0,2,1,3).reshape(-1,6,12)
    target=torch.cat((force,moment),dim=-1)
    regularizer=1e-7*torch.eye(6,device=feet.device,dtype=feet.dtype)
    inverse=matrix.transpose(1,2)@torch.linalg.solve(matrix@matrix.transpose(1,2)+regularizer,torch.eye(6,device=feet.device,dtype=feet.dtype).expand(feet.shape[0],6,6))
    vector=(inverse@target[:,:,None]).squeeze(-1)
    for iteration in range(128):
        f=vector.reshape(-1,4,3)
        normal=f[:,:,2].clamp_min(minimum_normal)
        tangent=f[:,:,:2];norm=tangent.norm(dim=-1).clamp_min(1e-9)
        tangent=tangent*torch.minimum(torch.ones_like(norm),friction*normal/norm)[:,:,None]
        vector=torch.cat((tangent,normal[:,:,None]),dim=-1).reshape(-1,12)
        residual=target-(matrix@vector[:,:,None]).squeeze(-1)
        # Inspect the projected feasible forces, not just the unconstrained solve.
        if iteration>=11 and bool((residual[:,:3].abs().amax(dim=1)<1e-4).all() and (residual[:,3:].abs().amax(dim=1)<1e-4).all()):
            break
        vector=vector+(inverse@residual[:,:,None]).squeeze(-1)
    # Final output must obey unilateral/friction bounds even if infeasible.
    f=vector.reshape(-1,4,3);normal=f[:,:,2].clamp_min(minimum_normal)
    tangent=f[:,:,:2];norm=tangent.norm(dim=-1).clamp_min(1e-9)
    tangent=tangent*torch.minimum(torch.ones_like(norm),friction*normal/norm)[:,:,None]
    f=torch.cat((tangent,normal[:,:,None]),dim=-1)
    residual=(matrix@f.reshape(-1,12,1)).squeeze(-1)-target
    return f,residual
