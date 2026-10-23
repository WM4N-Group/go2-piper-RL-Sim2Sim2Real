"""Exact finite-difference candidate pruning for rigid arm/base geometry."""
import numpy as np

def install(shield):
    import types
    shield._unpruned_linearized_margin=shield.linearized_margin
    model=shield.model
    joints=np.array([model.joint(f'joint{i}').id for i in range(1,7)])
    assert np.all(model.jnt_type[joints]==shield.mujoco.mjtJoint.mjJNT_HINGE)
    assert all(int(model.geom_type[g]) in (2,3,4,5,6,7) for g in shield.arm_geoms+shield.base_geoms)
    def descendant(body,parent):
        while body:
            if body==parent:return True
            body=int(model.body_parentid[body])
        return False
    affected=np.array([[descendant(int(model.geom_bodyid[g]),int(model.jnt_bodyid[j])) for g in shield.arm_geoms] for j in joints])
    assert not any(descendant(int(model.geom_bodyid[g]),int(model.jnt_bodyid[j])) for g in shield.base_geoms for j in joints)
    pairs=[(a,b) for a in shield.arm_geoms for b in shield.base_geoms]
    arm_index=np.repeat(np.arange(len(shield.arm_geoms)),len(shield.base_geoms))
    shield._pair_gradient_cache=(joints,affected,pairs,arm_index)
    shield.linearized_margin=types.MethodType(linearized_margin,shield)

def linearized_margin(self,actual,active,margin):
    gradient=np.zeros_like(actual);residual=np.zeros(len(actual));joints,affected,pairs,arm_index=self._pair_gradient_cache
    epsilon=.001;pad=.0001
    for index in range(len(actual)):
        if not active[index]:continue
        q=np.asarray(actual[index],dtype=np.float64)
        self.data.qpos[self.arm_qpos]=q;self.mujoco.mj_forward(self.model,self.data)
        distances=np.array([float(self.mujoco.mj_geomDistance(self.model,self.data,a,b,1.,None)) for a,b in pairs]);distance=float(distances.min())
        if distance>=margin+.015:continue
        radii=self.model.geom_rbound[self.arm_geoms]+np.maximum(0.,self.model.geom_margin[self.arm_geoms])+np.abs(self.model.geom_gap[self.arm_geoms])
        reach=np.linalg.norm(self.data.geom_xpos[self.arm_geoms][None]-self.data.xanchor[joints][:,None],axis=-1)+radii[None]
        bound=2*np.sin(epsilon/2)*reach*affected
        if not np.isfinite(distances).all() or not np.isfinite(bound).all() or distance<=2*bound.max()+pad:
            g,r=self._unpruned_linearized_margin(actual[index:index+1],np.ones(1,dtype=bool),margin);gradient[index]=g[0];residual[index]=r[0];continue
        minimum_index=int(np.argmin(distances));pair_bound=bound[:,arm_index]
        for joint in range(6):
            keep=distances-pair_bound[joint]<=distance+pair_bound[joint,minimum_index]+pad
            moving=keep&affected[joint,arm_index];constant=keep&~affected[joint,arm_index]
            if not moving.any():continue
            constant_min=float(distances[constant].min()) if constant.any() else float('inf')
            selected=np.flatnonzero(moving)
            values=[]
            for sign in (1.,-1.):
                query=q.copy();query[joint]+=sign*epsilon;self.data.qpos[self.arm_qpos]=query;self.mujoco.mj_forward(self.model,self.data)
                value=min(float(self.mujoco.mj_geomDistance(self.model,self.data,*pairs[k],1.,None)) for k in selected)
                values.append(min(constant_min,value))
            gradient[index,joint]=(values[0]-values[1])/(2*epsilon)
        # Preserve the original routine's final private-model configuration.
        q[-1]-=epsilon;self.data.qpos[self.arm_qpos]=q;self.mujoco.mj_forward(self.model,self.data)
        residual[index]=max(0.,margin-distance)
    return gradient,residual
