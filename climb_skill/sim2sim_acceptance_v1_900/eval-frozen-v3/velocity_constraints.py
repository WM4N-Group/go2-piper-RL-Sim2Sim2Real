"""Velocity bounds represented by unilateral fixed-tendon solver constraints.

These participate in MuJoCo's coupled contact/limit solve. No qvel clipping and
no motor torque modification. This is an explicit PhysX-limit surrogate that
requires controlled validation, not a claim of exact solver equivalence.
"""
import mujoco
import numpy as np
from bridge import ClimbBridge, JOINTS, SPEED, build_model

# Conservative numerical guard, chosen from controlled soft-constraint witnesses.
# The acceptance boundary remains the original SPEED, with no added tolerance.
VELOCITY_GUARD_RAD_S = .005


def constrained_model(cfg,height,friction=.6,added_mass=0.):
    _,spec=build_model(cfg,height,friction,added_mass)
    for name in JOINTS:
        for side in ('upper','lower'):
            t=spec.add_tendon(name='velocity_'+side+'_'+name,limited=True,range=[-100.,100.],margin=.001,
                              stiffness=0.,damping=0.,frictionloss=0.,
                              solimp_limit=[.9999,.9999,.001,.5,2.])
            t.wrap_joint(name,1.)
    return spec.compile(),spec


class VelocityClimbBridge(ClimbBridge):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.tids=np.array([self.model.tendon('velocity_'+side+'_'+n).id for n in JOINTS for side in ('upper','lower')])
        self.velocity_constraint_torque=np.zeros(self.model.nv)
        self.pre_constraint_velocity=self.data.qvel.copy()
        self.free_velocity_prediction=self.data.qvel.copy()

    def integrate(self):
        m,d=self.model,self.data
        mujoco.mj_step1(m,d)
        mujoco.mj_fwdActuation(m,d)
        mujoco.mj_fwdAcceleration(m,d)
        self.pre_constraint_velocity=d.qvel.copy()
        self.free_velocity_prediction=d.qvel+m.opt.timestep*d.qacc_smooth
        direction=np.tile([1.,-1.],18)
        q=np.repeat(d.qpos[self.qids],2)
        # Activate one unilateral row per joint. Its reference acceleration is
        # replaced below by a velocity inequality; no moving position target is
        # integrated or used to change the real joint-position limits.
        m.tendon_range[self.tids,0]=np.where(direction>0,q-100.,q-1e-8)
        m.tendon_range[self.tids,1]=np.where(direction>0,q+1e-8,q+100.)
        mujoco.mj_makeConstraint(m,d)
        mujoco.mj_projectConstraint(m,d)
        mujoco.mj_referenceConstraint(m,d)
        rows=np.flatnonzero(d.efc_type==mujoco.mjtConstraint.mjCNSTR_LIMIT_TENDON)
        assert len(rows)==36
        order={int(t):i//2 for i,t in enumerate(self.tids)}
        for row in rows:
            i=order[int(d.efc_id[row])]
            # J*v_next >= -speed. J is +/- the joint velocity selector.
            d.efc_aref[row]=(-(SPEED[i]-VELOCITY_GUARD_RAD_S)-d.efc_vel[row])/m.opt.timestep
        # step2 recomputes actuation/acceleration and solves all constraints
        # together using the reference acceleration above, then integrates.
        mujoco.mj_step2(m,d)
        jac=d.efc_J.reshape(d.nefc,m.nv)
        self.velocity_constraint_torque=jac[rows].T@d.efc_force[rows]
