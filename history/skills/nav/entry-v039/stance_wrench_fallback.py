"""Conservative LP fallback for an already rejected stationary wrench solve.

Keeps original0.5N/0.1Nm acceptance bounds; the internal margins are tighter.
Never used for capture eligibility or passed primary allocations.
"""
import numpy as np
import torch
from scipy.optimize import linprog


def refine_stance_wrench(feet, com, force, moment, primary, minimum_normal=8., friction=.4):
    if feet.shape[0]!=1:
        raise ValueError('Stationary diagnostic fallback requires one environment')
    feet_np=feet[0].detach().cpu().double().numpy()
    com_np=com[0].detach().cpu().double().numpy()
    blocks=[]
    for x,y,z in feet_np-com_np:
        blocks.append(np.vstack((np.eye(3),np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]]))))
    matrix=np.concatenate(blocks,axis=1)
    target=np.concatenate((force[0].detach().cpu().double().numpy(),moment[0].detach().cpu().double().numpy()))
    reference=primary[0].detach().cpu().double().numpy().reshape(12)
    # Minimize L1 change from the projected primary forces, rather than choose
    # arbitrary internally opposed forces. Rectangular pyramid is inscribed
    # in the circular Coulomb cone; acceptance still checks the true cone.
    objective=np.r_[np.zeros(12),np.ones(12)]
    inequalities=[];rhs=[]
    for i in range(4):
        for axis in (0,1):
            for sign in (-1.,1.):
                row=np.zeros(24);row[3*i+axis]=sign
                row[3*i+2]=-friction/np.sqrt(2.)
                inequalities.append(row);rhs.append(0.)
    margin=np.array([.49]*3+[.095]*3)
    for sign in (-1.,1.):
        inequalities.extend(np.c_[sign*matrix,np.zeros((6,12))]);rhs.extend(sign*target+margin)
        inequalities.extend(np.c_[sign*np.eye(12),-np.eye(12)]);rhs.extend(sign*reference)
    bounds=[(None,None),(None,None),(minimum_normal+1e-4,None)]*4+[(0.,None)]*12
    solved=linprog(objective,A_ub=np.asarray(inequalities),b_ub=np.asarray(rhs),bounds=bounds,method='highs',options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
    if not solved.success:
        return None,dict(status='no_conservative_feasible_solution',solver_status=int(solved.status))
    loads=torch.as_tensor(solved.x[:12].reshape(1,4,3),device=feet.device,dtype=feet.dtype)
    # Recompute in actual runtime dtype; never trust solver status alone.
    net=loads.sum(dim=1)
    torque=torch.cross(feet-com[:,None],loads,dim=-1).sum(dim=1)
    residual=torch.cat((net-force,torque-moment),dim=-1)
    valid=bool(torch.isfinite(loads).all() and (loads[:,:,2]>=minimum_normal).all() and (loads[:,:,:2].norm(dim=-1)<=friction*loads[:,:,2]+1e-6).all() and residual[:,:3].abs().max()<=.5 and residual[:,3:].abs().max()<=.1)
    details=dict(status='verified' if valid else 'rejected_after_dtype_check',l1_force_change_N=float((loads-primary).abs().sum()),max_force_residual_N=float(residual[:,:3].abs().max()),max_moment_residual_Nm=float(residual[:,3:].abs().max()),minimum_normal_N=float(loads[:,:,2].min()),max_friction_ratio=float((loads[:,:,:2].norm(dim=-1)/loads[:,:,2]).max()),solver='HiGHS conservative friction pyramid with L1 proximity')
    return (loads,residual) if valid else None,details
