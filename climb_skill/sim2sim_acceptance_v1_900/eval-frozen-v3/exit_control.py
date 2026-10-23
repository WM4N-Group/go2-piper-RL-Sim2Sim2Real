"""Candidate v1: explicit post-ascent braking, sequential front stance, COM alignment.

Only joint position targets change. PD, effort/delay/gravity contracts remain intact.
The original actor success is an entry event, never full stationary success.
"""
import numpy as np
from scipy.optimize import minimize, LinearConstraint, Bounds

EXIT_SPEC = dict(version='v3-wrench-exit-evaluation-candidate', brake_seconds=.8, settle_seconds=.6,
                 front_seconds=.7, com_seconds=.8, stationary_seconds=1.,
                 max_root_speed=.05, max_angular_speed=.10, max_joint_speed=.25,
                 max_foot_speed=.04, max_tilt=.12, max_arm_error=.08,
                 support_margin=.02, front_hip=.18, front_thigh=.72,
                 front_min_displacement=.01, max_exit_seconds=19.)
EXIT_SPEC.update(shift_seconds=1.2,swing_height=.025,front_forward=.025,front_outward=.22,lower_com_m=.09)


def polygon_margin(points, xy):
    """Signed distance to a counterclockwise convex hull; positive is inside."""
    points=sorted(set(map(tuple,np.asarray(points))))
    def cross(a,b,c):return np.cross(np.subtract(b,a),np.subtract(c,a))
    lower=[];upper=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    hull=lower[:-1]+upper[:-1]
    if len(hull)<3:return -1.
    return float(min(cross(a,b,xy)/max(np.linalg.norm(np.subtract(b,a)),1e-12)
                     for a,b in zip(hull,hull[1:]+hull[:1])))


def smooth(t):
    t=float(np.clip(t,0,1))
    return t**3*(10-15*t+6*t*t)


def support_center(points):
    points=np.asarray(points)
    if len(points)==3:
        lengths=np.linalg.norm(points-np.roll(points,1,axis=0),axis=1)
        weights=np.roll(lengths,1)
        return (weights[:,None]*points).sum(0)/weights.sum()
    return points.mean(0)


class ExitController:
    def __init__(self,reference,cfg):
        self.reference=np.asarray(reference).copy();self.cfg=cfg
        self.phase='ACTIVE';self.phase_time=0.;self.exit_time=0.;self.hold=0.
        self.events=[];self.native_ascent=False;self.front_done=[False,False]
        self.last_target=self.reference.copy();self.start=self.last_target.copy()
        self.goal=self.start.copy();self.front_start=None;self.previous_feet=None
        self.metrics={}
        self.anchors=None;self.com_goal=None;self.yaw_goal=None
        self.swing_start=None;self.swing_goal=None
        self.front_order=[];self.swing_evidence={};self.final_com_goal=None
        self.shift_origin=None
        self.final_com_start=None
        self.previous_physics_feet=None

    def observe_physics(self,state,dt):
        """Accumulate HOLD only from consecutive actual physics substeps."""
        s=EXIT_SPEC;cfg=self.cfg;feet=np.asarray(state['feet']);forces=np.asarray(state['forces'])
        foot_speed=np.inf if self.previous_physics_feet is None else np.linalg.norm((feet-self.previous_physics_feet)/dt,axis=-1).max()
        self.previous_physics_feet=feet.copy()
        inside=((feet[:,0]>=cfg['box_front']+cfg['top_margin']) &
                (feet[:,0]<=cfg['box_front']+cfg['box_length']-cfg['top_margin']) &
                (abs(feet[:,1])<=cfg['box_width']/2-cfg['top_margin']))
        support=inside & (abs(feet[:,2]-state['height']-cfg['foot_radius'])<=cfg['foot_height_tolerance']) & (forces[:,2]>=cfg['support_force'])
        if self.phase.startswith(('FRONT','LAND')):
            index=0 if self.phase.endswith('FL') else 1;others=[i for i in range(4) if i!=index]
            e=self.swing_evidence
            e['unloaded'] |= bool(forces[index,2]<2.)
            e['lifted'] |= bool(feet[index,2]-self.swing_start[2]>.012)
            e['min_support_margin']=min(e['min_support_margin'],polygon_margin(feet[others,:2],state['com'][:2]))
            e['support_preserved'] &= bool(support[others].all())
        stable=bool(support.all() and state['tilt']<s['max_tilt'] and
            np.linalg.norm(state['root_velocity'])<s['max_root_speed'] and
            np.linalg.norm(state['angular_velocity'])<s['max_angular_speed'] and
            abs(state['joint_velocity']).max()<s['max_joint_speed'] and foot_speed<s['max_foot_speed'] and
            state['arm_error']<s['max_arm_error'] and
            polygon_margin(feet[:,:2],state['com'][:2])>=s['support_margin'])
        if self.phase=='HOLD':
            forward=np.array([np.cos(self.yaw_goal),np.sin(self.yaw_goal)])
            stable &= bool(np.linalg.norm(state['com'][:2]-self.final_com_goal)<.015 and
                (state['com'][:2]-self.final_com_start)@forward>=.01)
        self.hold=self.hold+dt if self.phase=='HOLD' and stable and all(self.front_done) else 0.
        return stable

    def transition(self,phase,seconds,target=None):
        self.phase=phase;self.phase_time=0.
        self.start=self.last_target.copy()
        if target is not None:self.goal=np.asarray(target).copy()
        self.events.append(dict(phase=phase,seconds=float(seconds)))

    def update(self,state,native_success,target,dt):
        cfg=self.cfg;s=EXIT_SPEC
        feet=np.asarray(state['feet']);forces=np.asarray(state['forces'])
        foot_speed=0. if self.previous_feet is None else float(np.linalg.norm((feet-self.previous_feet)/dt,axis=-1).max())
        self.previous_feet=feet.copy()
        inside=((feet[:,0]>=cfg['box_front']+cfg['top_margin']) &
                (feet[:,0]<=cfg['box_front']+cfg['box_length']-cfg['top_margin']) &
                (abs(feet[:,1])<=cfg['box_width']/2-cfg['top_margin']))
        support=inside & (abs(feet[:,2]-state['height']-cfg['foot_radius'])<=cfg['foot_height_tolerance']) & (forces[:,2]>=cfg['support_force'])
        margin=polygon_margin(feet[support,:2],state['com'][:2])
        stable=bool(support.all() and state['tilt']<s['max_tilt'] and
                    np.linalg.norm(state['root_velocity'])<s['max_root_speed'] and
                    np.linalg.norm(state['angular_velocity'])<s['max_angular_speed'] and
                    abs(state['joint_velocity']).max()<s['max_joint_speed'] and
                    foot_speed<s['max_foot_speed'] and state['arm_error']<s['max_arm_error'] and
                    margin>=s['support_margin'])
        self.metrics=dict(supported_feet=int(support.sum()),com_margin_m=margin,
                          root_speed=float(np.linalg.norm(state['root_velocity'])),
                          angular_speed=float(np.linalg.norm(state['angular_velocity'])),
                          tilt=float(state['tilt']),arm_error=float(state['arm_error']),
                          joint_speed=float(abs(state['joint_velocity']).max()),
                          foot_speed=foot_speed,stable=stable,hold_seconds=self.hold)
        if self.phase=='ACTIVE':
            self.last_target=np.asarray(target).copy()
            if native_success:
                self.native_ascent=True
            if self.native_ascent and support.all():
                self.anchors=feet.copy();self.com_goal=np.asarray(state['com']).copy()
                self.yaw_goal=state['yaw']
                self.transition('BRAKE',state['seconds'],self.reference)
            return None
        self.phase_time+=dt;self.exit_time+=dt
        if self.phase=='BRAKE' and self.phase_time>=s['brake_seconds']:
            self.transition('SETTLE',state['seconds'],self.reference)
        elif self.phase=='SETTLE' and self.phase_time>=s['settle_seconds'] and stable:
            self.anchors=feet.copy()
            margins=[polygon_margin(np.delete(feet,i,axis=0)[:,:2],state['com'][:2]) for i in (0,1)]
            first=int(np.argmax(margins));self.front_order=[first,1-first]
            self.shift_origin=np.asarray(state['com']).copy()
            self.transition('SHIFT_FL' if first==0 else 'SHIFT_FR',state['seconds'])
        elif self.phase in ('SHIFT_FL','SHIFT_FR'):
            index=0 if self.phase=='SHIFT_FL' else 1
            others=[i for i in range(4) if i!=index]
            safe=(polygon_margin(feet[others,:2],state['com'][:2])>=s['support_margin']+.005
                  and np.linalg.norm(state['com_velocity'])<.025
                  and np.linalg.norm(state['angular_velocity'])<s['max_angular_speed']
                  and foot_speed<s['max_foot_speed'])
            if self.phase_time>=s['shift_seconds'] and safe and support[others].all():
                self.swing_start=feet[index].copy()
                outward=s['front_outward'] if not any(self.front_done) else .02
                c,ss=np.cos(self.yaw_goal),np.sin(self.yaw_goal)
                rotation=np.array([[c,-ss,0],[ss,c,0],[0,0,1]])
                if not any(self.front_done):
                    # Plan enough width for the other front foot's later tripod.
                    # A fixed 2 cm spread can leave the rear feet nearly collinear.
                    for distance in np.linspace(.02,.30,29):
                        candidate=self.swing_start+rotation@np.array([s['front_forward'],distance*(1 if index==0 else -1),0.])
                        triangle=np.r_[candidate[None,:2],feet[2:,:2]]
                        if polygon_margin(triangle,support_center(triangle))>=.04:
                            outward=float(distance);break
                    else:outward=.30
                local=np.array([s['front_forward'],outward*(1 if index==0 else -1),0.])
                self.swing_goal=self.swing_start+rotation@local
                self.front_start=feet[index].copy()
                self.swing_evidence=dict(unloaded=False,lifted=False,min_support_margin=1.,support_preserved=True)
                self.events.append(dict(phase='SWING_PLAN',foot=index,seconds=float(state['seconds']),
                    start=self.swing_start.tolist(),goal=self.swing_goal.tolist()))
                self.transition('FRONT_FL' if index==0 else 'FRONT_FR',state['seconds'],self.goal)
        elif self.phase in ('FRONT_FL','FRONT_FR','LAND_FL','LAND_FR'):
            index=0 if self.phase.endswith('FL') else 1;others=[i for i in range(4) if i!=index]
            e=self.swing_evidence
            e['unloaded'] |= bool(forces[index,2]<2.)
            e['lifted'] |= bool(feet[index,2]-self.swing_start[2]>.012)
            e['min_support_margin']=min(e['min_support_margin'],polygon_margin(feet[others,:2],state['com'][:2]))
            e['support_preserved'] &= bool(support[others].all())
            delta=self.swing_goal[:2]-self.swing_start[:2]
            progress=float((feet[index,:2]-self.swing_start[:2])@delta/np.linalg.norm(delta))
            reached=np.linalg.norm(feet[index,:2]-self.swing_goal[:2])<.012 and progress>=s['front_min_displacement']
            self.metrics.update(swing_evidence=e.copy(),swing_progress_m=progress,swing_goal_error_m=float(np.linalg.norm(feet[index,:2]-self.swing_goal[:2])))
            if self.phase.startswith('FRONT') and self.phase_time>=s['front_seconds']:
                self.transition('LAND_FL' if index==0 else 'LAND_FR',state['seconds'])
            elif self.phase.startswith('LAND') and self.phase_time>=.3 and support.all() and reached and e['unloaded'] and e['lifted'] and e['support_preserved'] and e['min_support_margin']>=s['support_margin']:
                self.front_done[index]=True;self.anchors=feet.copy()
                self.events.append(dict(phase='FOOT_COMPLETE',foot=index,seconds=float(state['seconds']),progress_m=progress,**e))
                if all(self.front_done):
                    self.final_com_goal=self.anchors[:,:2].mean(0)
                    self.final_com_start=np.asarray(state['com'][:2]).copy()
                    forward=np.array([np.cos(self.yaw_goal),np.sin(self.yaw_goal)])
                    advance=float((self.final_com_goal-self.final_com_start)@forward)
                    self.final_com_goal+=max(0.,.02-advance)*forward
                    self.transition('COM_ALIGN',state['seconds'])
                else:
                    self.shift_origin=np.asarray(state['com']).copy()
                    self.transition('SHIFT_FL' if index==1 else 'SHIFT_FR',state['seconds'])
        elif self.phase=='COM_ALIGN' and self.phase_time>=s['com_seconds'] and np.linalg.norm(state['com'][:2]-self.final_com_goal)<.015 and (state['com'][:2]-self.final_com_start)@np.array([np.cos(self.yaw_goal),np.sin(self.yaw_goal)])>=.01:
            self.events.append(dict(phase='COM_COMPLETE',seconds=float(state['seconds']),
                start_xy=self.final_com_start.tolist(),goal_xy=self.final_com_goal.tolist(),actual_xy=state['com'][:2].tolist()))
            self.transition('HOLD',state['seconds'],self.goal)
        duration={'BRAKE':s['brake_seconds'],'FRONT_FL':s['front_seconds'],
                  'FRONT_FR':s['front_seconds'],'COM_ALIGN':s['com_seconds']}.get(self.phase,0.)
        blend=smooth(self.phase_time/duration) if duration else 1.
        self.last_target=self.start+blend*(self.goal-self.start)
        if self.phase=='BRAKE':
            self.last_target=self.reference+(1-blend)*(np.asarray(target)-self.reference)
        self.last_target[12:]=self.reference[12:]
        self.last_target=self.balance_target(state,dt)
        self.metrics['hold_seconds']=self.hold
        if self.hold+1e-9>=s['stationary_seconds']:return 'success'
        if self.exit_time>=s['max_exit_seconds']:return 'exit_not_stable'
        return None

    def balance_target(self,state,dt):
        """Ground-reaction wrench -> original PD position interface, never base forces."""
        s=EXIT_SPEC;feet=np.asarray(state['feet']);com=np.asarray(state['com'])
        goal=self.com_goal.copy()
        if self.phase!='BRAKE':goal[2]-=s['lower_com_m']
        swing=0 if self.phase in ('SHIFT_FL','FRONT_FL','LAND_FL') else 1 if self.phase in ('SHIFT_FR','FRONT_FR','LAND_FR') else None
        stance=[i for i in range(4) if i!=swing] if swing is not None else list(range(4))
        goal[:2]=support_center(feet[stance,:2])
        if self.phase in ('COM_ALIGN','HOLD'):goal[:2]=self.final_com_goal
        if self.phase in ('SHIFT_FL','SHIFT_FR'):
            blend=smooth(self.phase_time/s['shift_seconds'])
            goal[:2]=self.shift_origin[:2]+blend*(goal[:2]-self.shift_origin[:2])
        # Hold the native ascent height, regulate upright posture and braking.
        acceleration=np.array([20.,20.,60.])*(goal-com)-np.array([8.,8.,12.])*state['com_velocity']
        force=state['mass']*(acceleration+np.array([0.,0.,9.81]))
        attitude=np.array([state['roll'],state['pitch'],np.arctan2(np.sin(state['yaw']-self.yaw_goal),np.cos(state['yaw']-self.yaw_goal))])
        moment=-np.array([50.,50.,20.])*attitude-np.array([4.,4.,3.])*state['angular_velocity']
        def skew(r):
            x,y,z=r
            return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        force_stance=stance if self.phase in ('FRONT_FL','FRONT_FR') else list(range(4))
        matrix=np.concatenate([np.r_[np.eye(3),skew(feet[i]-com)] for i in force_stance],axis=1)
        wrench=np.r_[force,moment]
        forces=np.linalg.lstsq(matrix,wrench,rcond=None)[0].reshape(-1,3)
        # Projected descent respects nonnegative support and a conservative cone.
        lipschitz=np.linalg.norm(matrix,2)**2+.01
        for _ in range(30):
            residual=matrix@forces.ravel()-wrench
            forces-=((matrix.T@residual).reshape(-1,3)+.01*forces)/lipschitz
            forces[:,2]=np.clip(forces[:,2],0.,state['mass']*9.81)
            if self.phase.startswith('LAND'):
                forces[swing,2]=max(forces[swing,2],1.1*self.cfg['support_force'])
            length=np.linalg.norm(forces[:,:2],axis=1)
            forces[:,:2]*=np.minimum(1.,.8*state['friction']*forces[:,2]/np.maximum(length,1e-12))[:,None]
        tau=np.asarray(state['gravity_joint']).copy()
        if self.phase.startswith(('FRONT','LAND')):
            q=np.asarray(state['joint_position']);qd=np.asarray(state['joint_velocity'])
            lo=np.maximum(self.reference[:12]-self.cfg['max_position_offset'],state['soft_limits'][:12,0])
            hi=np.minimum(self.reference[:12]+self.cfg['max_position_offset'],state['soft_limits'][:12,1])
            if self.cfg['rear_workspace_enabled']:
                hi[[7,10]]=np.minimum(hi[[7,10]],self.cfg['rear_thigh_max'])
                lo[[8,11]]=np.maximum(lo[[8,11]],self.cfg['rear_calf_min'])
                hi[[8,11]]=np.minimum(hi[[8,11]],self.cfg['rear_calf_max'])
            mapping=np.concatenate([-state['foot_jacobian'][i].T[:12] for i in force_stance],axis=1)
            ids=np.array([j for j in range(12) if j//3!=swing])
            lower=state['kp'][:12]*(lo-q[:12])-state['kd'][:12]*qd[:12]-state['gravity_joint'][:12]
            upper=state['kp'][:12]*(hi-q[:12])-state['kd'][:12]*qd[:12]-state['gravity_joint'][:12]
            cone=[];mu=.8*state['friction']/np.sqrt(2.)
            for i in range(len(force_stance)):
                for axis in (0,1):
                    for sign in (-1,1):
                        row=np.zeros(3*len(force_stance));row[3*i+axis]=sign;row[3*i+2]=-mu;cone.append(row)
            weights=np.array([1.,1.,1.,4.,4.,4.]);a=weights[:,None]*matrix;b=weights*wrench
            def objective(f):
                r=a@f-b
                return .5*(r@r)+.0001*(f@f)
            bounds_lo=np.tile([-np.inf,-np.inf,0.],len(force_stance))
            if self.phase.startswith('LAND'):bounds_lo[3*swing+2]=self.cfg['support_force']*1.1
            result=minimize(objective,forces.ravel(),jac=lambda f:a.T@(a@f-b)+.0002*f,
                method='SLSQP',bounds=Bounds(bounds_lo,np.inf),
                constraints=[LinearConstraint(mapping[ids],lower[ids],upper[ids]),LinearConstraint(np.array(cone),-np.inf,0.)],
                options=dict(maxiter=80,ftol=1e-7))
            if result.success:forces=result.x.reshape(-1,3)
            self.metrics['allocation_success']=bool(result.success)
        for i,f in zip(force_stance,forces):tau-=state['foot_jacobian'][i].T@f
        q=np.asarray(state['joint_position']);qd=np.asarray(state['joint_velocity'])
        target=q+(tau+state['kd']*qd)/state['kp']
        if self.phase in ('FRONT_FL','FRONT_FR','LAND_FL','LAND_FR'):
            u=np.clip(self.phase_time/s['front_seconds'],0.,1.) if self.phase.startswith('FRONT') else 1.
            desired=self.swing_start+smooth(u)*(self.swing_goal-self.swing_start)
            desired[2]+=s['swing_height']*np.sin(np.pi*u)**2
            if self.phase.startswith('LAND'):desired[2]=state['height']+self.cfg['foot_radius']-.003
            ids=np.arange(3*swing,3*swing+3)
            jac=state['foot_jacobian'][swing][:,ids]
            dq=jac.T@np.linalg.solve(jac@jac.T+1e-5*np.eye(3),desired-feet[swing])
            target[ids]=q[ids]+dq+tau[ids]/state['kp'][ids]
        target[12:]=self.reference[12:]
        # Original workspace and torque limits still apply downstream.
        target[:12]=np.clip(target[:12],self.reference[:12]-self.cfg['max_position_offset'],
                             self.reference[:12]+self.cfg['max_position_offset'])
        target[:12]=np.clip(target[:12],state['soft_limits'][:12,0],state['soft_limits'][:12,1])
        if self.cfg['rear_workspace_enabled']:
            target[[7,10]]=np.minimum(target[[7,10]],self.cfg['rear_thigh_max'])
            target[[8,11]]=np.clip(target[[8,11]],self.cfg['rear_calf_min'],self.cfg['rear_calf_max'])
        if self.phase=='BRAKE':
            alpha=smooth(min(self.phase_time/.25,1.))
            target=self.start+alpha*(target-self.start)
        self.metrics['wrench_residual']=float(np.linalg.norm(matrix@forces.ravel()-wrench))
        self.metrics['com_goal']=goal.tolist()
        self.metrics['com_error']=(goal-com).tolist()
        self.metrics['requested_foot_forces']=forces.tolist()
        return target
