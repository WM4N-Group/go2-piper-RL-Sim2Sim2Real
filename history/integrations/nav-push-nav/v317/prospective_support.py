"""Static look-ahead for support preparation, never a dynamic safety waiver."""
import numpy as np
import torch
from stance_wrench_math import allocate_wrench

def prospective_support(controller,robot,joint_ids,joint_names,*,reserve_for_late_parking=False,nominal_translation_w=None,minimum_shift_m=0.):
    g=controller.geometry_shield
    saved=g.data.qpos.copy()
    try:
        g.data.qpos[:3]=robot.data.root_pos_w[0].cpu().numpy()
        g.data.qpos[3:7]=robot.data.root_quat_w[0].cpu().numpy()
        for name,q in zip(joint_names,robot.data.joint_pos[0,joint_ids].cpu().numpy()):
            g.data.qpos[g.model.joint(name).qposadr[0]]=q
        g.mujoco.mj_forward(g.model,g.data)
        mass=g.model.body_mass
        actual_mass=robot.root_physx_view.get_masses()[0].cpu().numpy()
        if abs(actual_mass.sum()-mass.sum())>.001:raise ValueError('Prospective COM source mass mismatch')
        measured=(robot.data.body_com_pos_w[0].cpu().numpy()*actual_mass[:,None]).sum(0)/actual_mass.sum()
        shadow=(g.data.xipos*mass[:,None]).sum(0)/mass.sum()
        error=float(np.linalg.norm(shadow-measured))
        if error>.0002:raise ValueError('Prospective COM source geometry mismatch')
        names=['FR_foot','FL_foot','RR_foot','RL_foot']
        feet=robot.data.body_pos_w[0,robot.find_bodies(names,preserve_order=True)[0]].cpu().numpy()
        shadow_feet=g.data.xpos[[g.model.body(name).id for name in names]]
        foot_error=float(np.linalg.norm(feet-shadow_feet,axis=1).max())
        if foot_error>.0002:raise ValueError('Prospective foot source geometry mismatch')
        initial=robot.data.joint_pos[0,controller.joint_ids].cpu().numpy()
        goal=controller.safe_approach_waypoints[-1].cpu().numpy()
        com=[]
        for u in np.linspace(0.,1.,41):
            g.data.qpos[g.arm_qpos]=initial+(goal-initial)*u
            g.mujoco.mj_forward(g.model,g.data)
            com.append((g.data.xipos*mass[:,None]).sum(0)/mass.sum()-shadow+measured)
        translation=np.zeros(3) if nominal_translation_w is None else np.asarray(nominal_translation_w,dtype=float)
        if translation.shape!=(3,) or not np.isfinite(translation).all() or np.linalg.norm(translation)>.09:raise ValueError('Invalid nominal support preview translation')
        if nominal_translation_w is not None:com=[v+translation for v in com]
        if not 0.<=minimum_shift_m<=.04:raise ValueError("Box approach needs more than40mm preparation")
        checks=[]
        for shift in np.linspace(0.,.04,9):
            if shift<minimum_shift_m-1e-9:continue
            centers=torch.tensor(np.array(com)-[shift,0.,0.],dtype=torch.float64)
            force=torch.tensor([[0.,0.,float(actual_mass.sum())*9.81]],dtype=torch.float64).repeat(len(centers),1)
            loads,residual=allocate_wrench(torch.tensor(feet[None],dtype=torch.float64).repeat(len(centers),1,1),centers,force,torch.zeros_like(force))
            passed=bool((residual[:,:3].abs()<=.5).all() and (residual[:,3:].abs()<=.1).all())
            checks.append(dict(shift_m=float(shift),passed=passed,max_force_residual=float(residual[:,:3].abs().max()),max_moment_residual=float(residual[:,3:].abs().max())))
            if passed:
                result=dict(shift_m=0. if shift==0. else min(.04,float(shift)+.005),source_com_error_m=error,source_foot_error_m=foot_error,checks=checks,scope='nominal arm-path static support; optional12N reserve after READY, actual gates unchanged')
                if nominal_translation_w is not None:result['nominal_translation_w']=translation.tolist();result['scope']='Translated nominal COM preview only; measured final-pose feasibility must be rechecked before READY'
                result['push_support_shift_m']=result['shift_m']
                if shift==0. or not reserve_for_late_parking or result['shift_m']<.015-1e-9:return result
                reserve_checks=[]
                for reserve_shift in np.linspace(0.,.04,9):
                    if reserve_shift<result['shift_m']-1e-9:continue
                    centers=torch.tensor(np.array(com)-[reserve_shift,0.,0.],dtype=torch.float64)
                    loads,residual=allocate_wrench(torch.tensor(feet[None],dtype=torch.float64).repeat(len(centers),1,1),centers,force,torch.zeros_like(force),minimum_normal=12.)
                    reserve_ok=bool((residual[:,:3].abs()<=.5).all() and (residual[:,3:].abs()<=.1).all())
                    reserve_checks.append(dict(shift_m=float(reserve_shift),passed=reserve_ok,max_force_residual=float(residual[:,:3].abs().max()),max_moment_residual=float(residual[:,3:].abs().max())))
                    if reserve_ok:
                        result.update(push_support_shift_m=min(.04,float(reserve_shift)+.005),push_reserve_checks=reserve_checks)
                        return result
                raise ValueError('No prospective12N push support reserve within40mm bound')
        raise ValueError('No prospective nominal-path support solution within40mm preparation bound')
    finally:
        g.data.qpos[:]=saved
        g.mujoco.mj_forward(g.model,g.data)
