"""Sampled frozen-path tip envelope, not a dynamic collision certificate."""
import itertools
import numpy as np

def rotation(q):
    w,x,y,z=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def required_standoff(g,joint_names,q,root_position,root_quaternion,box_position,box_quaternion,waypoints,box_size,*,residual_limit,nominal_translation_w=None,forecast_margin_m=0.):
    saved=g.data.qpos.copy()
    try:
        g.data.qpos[:3]=root_position;g.data.qpos[3:7]=root_quaternion
        for name,value in zip(joint_names,q):g.data.qpos[g.model.joint(name).qposadr[0]]=value
        g.mujoco.mj_forward(g.model,g.data)
        hand=g.model.body('end_effector').id
        source=g.data.xpos[hand].copy()
        spheres=[i for i in range(g.model.ngeom) if g.model.geom_bodyid[i]==hand and g.model.geom_type[i]==g.mujoco.mjtGeom.mjGEOM_SPHERE]
        if len(spheres)!=1:raise ValueError('Unknown hand collision sphere geometry')
        radius=float(g.model.geom_size[spheres[0],0])
        if abs(radius-.01)>1e-6:raise ValueError('Unexpected source hand sphere radius')
        half=np.asarray(box_size,dtype=float)*.5
        if half.shape!=(3,) or np.any(half<=0.):raise ValueError('Invalid box size')
        if not 0.<=residual_limit<=.02+1e-7:raise ValueError('Unexpected frozen approach residual envelope')
        translation=np.zeros(3) if nominal_translation_w is None else np.asarray(nominal_translation_w,dtype=float)
        br=rotation(box_quaternion)
        if br[0,0]<.95:raise ValueError('Box standoff outside existing aligned entry domain')
        waypoints=np.asarray(waypoints)
        if waypoints.ndim!=2 or waypoints.shape[1]!=6 or len(waypoints)<2:raise ValueError('Invalid frozen approach path')
        joints=[g.model.joint(f'joint{i}').id for i in range(1,7)];bounds=g.model.jnt_range[joints]
        if not 0.<=forecast_margin_m<=.005:raise ValueError("Invalid forecast standoff reserve")
        inflation=radius+.005+forecast_margin_m
        maximum=None;count=0
        corners=list(itertools.product([-residual_limit,residual_limit],repeat=6))
        for begin,end in zip(waypoints,waypoints[1:]):
            for u in np.linspace(0.,1.,41):
                nominal=begin+u*(end-begin)
                for corner in corners:
                    g.data.qpos[g.arm_qpos]=np.clip(nominal+corner,bounds[:,0],bounds[:,1])
                    g.mujoco.mj_forward(g.model,g.data)
                    local=br.T@(g.data.xpos[hand]+translation-box_position)
                    if abs(local[1])<=half[1]+inflation and abs(local[2])<=half[2]+inflation:
                        maximum=float(local[0]) if maximum is None else max(maximum,float(local[0]));count+=1
        needed=0. if maximum is None else max(0.,(maximum+half[0]+inflation)/br[0,0])
        if needed>.04:raise ValueError('Box approach needs more than40mm preparation')
        return dict(minimum_shift_m=needed,tip_radius_m=radius,planning_margin_m=.005,forecast_margin_m=forecast_margin_m,residual_limit_rad=residual_limit,samples_in_expanded_yz=count,maximum_box_local_x=maximum,source_hand_position_w=source,scope='Static sampled nominal path plus residual corners; excludes tracking/dynamic error; actual gates remain')
    finally:
        g.data.qpos[:]=saved;g.mujoco.mj_forward(g.model,g.data)
