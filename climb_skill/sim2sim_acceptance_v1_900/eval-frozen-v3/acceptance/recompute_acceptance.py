"""Independent, raw-trajectory acceptance accounting for both engines.

No controller class or its success predicate is imported. SciPy hull halfspaces
provide an independent implementation of support margin.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull

ROOT=Path(__file__).resolve().parents[1]
SPEED=np.array([30.1,30.1,15.7]*4+[3.]*6)
EFFORT=np.array([23.7,23.7,45.43]*4+[20.,20.,15.,7.,5.,5.])


def margins(feet,com):
    result=[]
    for f,c in zip(feet,com):
        try:
            equations=ConvexHull(f[:,:2]).equations
            result.append(float(np.min(-(equations[:,:2]@c[:2]+equations[:,2]))))
        except Exception:result.append(-np.inf)
    return np.array(result)


def audit_episode(folder,record,engine,cfg,spec):
    i=record['episode'] if engine=='mujoco' else record['env']
    if engine=='mujoco':
        z=np.load(folder/f'trace_{i:03d}.npz');meta=json.loads((folder/f'initial_{i:03d}.json').read_text())
        q=z['qpos'][:,meta['joint_qids']];qd=z['qvel'][:,meta['joint_dids']]
        root=z['qpos'][:,:7];velocity=z['qvel'][:,:3];omega=z['qvel'][:,3:6]
        feet=z['feet'];forces=z['forces'][:,meta['feet_ids']];forbidden=z['forces'][:,meta['forbidden']]
        torque=z['actuator_force'][:,meta['joint_dids']];target=z['targets'];com=z['com']
        ref=np.array([.1,.8,-1.5,-.1,.8,-1.5,.1,1.,-1.5,-.1,1.,-1.5]+cfg['arm_pose'])
        pre=z['command_state'];delayed=z['delayed_command']
        expected=np.array(meta['kp'])*(delayed[:,0]-pre[:,:18])-np.array(meta['kd'])*pre[:,18:]+delayed[:,1]
        pd_error=float(np.max(abs(expected-z['raw_torque'])))
        applied_error=float(np.max(abs(np.clip(expected,-EFFORT,EFFORT)-torque)))
        warnings=int(z['warnings'].max())
        delayed_target_error=0.
        for j,lag in enumerate(meta['delays']):
            history=target[np.maximum(0,np.arange(len(target))-lag),j]
            delayed_target_error=max(delayed_target_error,float(np.max(abs(history-delayed[:,0,j]))))
    else:
        z=np.load(folder/f'exit_trace_{i:03d}.npz');meta=json.loads((folder/'exit_metadata.json').read_text())
        q=z['q'];qd=z['qd'];root=z['root'][:,:7].copy();root[:,:3]-=meta['origins'][i]
        velocity=z['root_velocity'];omega=z['root'][:,10:13]
        feet=z['body_pos'][:,meta['foot_ids']]-np.array(meta['origins'][i])
        forces=z['forces'][:,meta['contact_feet']];forbidden=z['forces'][:,meta['forbidden']]
        torque=z['torque'];target=z['target'];com=z['com'];ref=np.array(meta['reference'][i])
        kp=np.zeros(18);kd=kp.copy()
        for a in meta['actuators'].values():
            for j,raw_id in enumerate(a['joint_indices']):
                ordered=meta['joint_ids'].index(raw_id)
                kp[ordered]=a['stiffness'][i][j];kd[ordered]=a['damping'][i][j]
        expected=kp*(z['delayed_position']-z['pd_position'])+kd*(z['delayed_velocity']-z['pd_velocity'])+z['delayed_effort']
        pd_error=float(np.max(abs(expected-z['computed_effort'])))
        applied_error=float(np.max(abs(np.clip(expected,-EFFORT,EFFORT)-torque)))
        warnings=None;delayed_target_error=0.
        for a in meta['actuators'].values():
            lag=a['delays'][i]
            for raw_id in a['joint_indices']:
                j=meta['joint_ids'].index(raw_id)
                delayed_target_error=max(delayed_target_error,float(np.max(abs(target[np.maximum(0,np.arange(len(target))-lag),j]-z['delayed_position'][:,j]))))
    t=z['time'];dt=.005;ph=z['phase'];errors=[]
    finite=all(np.isfinite(v).all() for v in (q,qd,root,velocity,omega,feet,forces,torque,target,com))
    if not finite:errors.append('nonfinite_state')
    speed_excess=float(np.max(abs(qd)-SPEED));torque_excess=float(np.max(abs(torque)-EFFORT))
    bad_contact=float(np.max(np.linalg.norm(forbidden,axis=-1)))
    tilt=np.arccos(np.clip(1-2*(root[:,4]**2+root[:,5]**2),-1,1))
    if speed_excess>0:errors.append('joint_speed_limit')
    if torque_excess>1e-5:errors.append('torque_limit')
    if bad_contact>cfg['contact_failure_force']:errors.append('forbidden_contact')
    if tilt.max()>cfg['failure_tilt']:errors.append('failure_tilt')
    if root[:,2].min()<.16:errors.append('low_posture')
    if pd_error>(1e-9 if engine=='mujoco' else 1e-4) or applied_error>(1e-9 if engine=='mujoco' else 1e-4):errors.append('pd_recompute')
    if delayed_target_error>1e-6:errors.append('delay_recompute')
    if warnings:errors.append('solver_warning')
    inside=((feet[:,:,0]>=cfg['box_front']+cfg['top_margin']) & (feet[:,:,0]<=cfg['box_front']+cfg['box_length']-cfg['top_margin']) & (abs(feet[:,:,1])<=cfg['box_width']/2-cfg['top_margin']))
    support=inside & (abs(feet[:,:,2]-.2-cfg['foot_radius'])<=cfg['foot_height_tolerance']) & (forces[:,:,2]>=cfg['support_force'])
    foot_speed=np.r_[np.inf,np.linalg.norm(np.diff(feet,axis=0)/dt,axis=-1).max(-1)]
    margin=margins(feet,com)
    stable=(support.all(-1) & (tilt<spec['max_tilt']) & (np.linalg.norm(velocity,axis=-1)<spec['max_root_speed']) &
        (np.linalg.norm(omega,axis=-1)<spec['max_angular_speed']) & (abs(qd).max(-1)<spec['max_joint_speed']) &
        (foot_speed<spec['max_foot_speed']) & (abs(q[:,12:]-ref[12:]).max(-1)<spec['max_arm_error']) & (margin>=spec['support_margin']))
    events=record.get('events',[]);foot_checks=[]
    for foot in (0,1):
        plans=[e for e in events if e['phase']=='SWING_PLAN' and e['foot']==foot]
        completions=[e for e in events if e['phase']=='FOOT_COMPLETE' and e['foot']==foot]
        ok=False;detail={}
        if len(plans)==1 and len(completions)==1:
            plan=plans[0];end=completions[0]['seconds'];mask=(t>plan['seconds']+1e-8)&(t<=end+1e-8)
            others=[j for j in range(4) if j!=foot]
            if mask.any():
                start=np.array(plan['start']);goal=np.array(plan['goal']);delta=goal[:2]-start[:2]
                current=feet[mask,foot];progress=float((current[-1,:2]-start[:2])@delta/np.linalg.norm(delta))
                error=float(np.linalg.norm(current[-1,:2]-goal[:2]));lift=float((current[:,2]-start[2]).max())
                unloaded=bool((forces[mask,foot,2]<2.).any());preserved=bool(support[mask][:,others].all())
                tripod_margin=float(margins(feet[mask][:,others],com[mask]).min())
                ok=bool(error<.012 and progress>=spec['front_min_displacement'] and lift>.012 and unloaded and preserved and tripod_margin>=spec['support_margin'])
                detail=dict(progress_m=progress,goal_error_m=error,lift_m=lift,unloaded=unloaded,support_preserved=preserved,tripod_margin_m=tripod_margin)
        foot_checks.append(dict(foot=foot,passed=ok,**detail))
    completion=[e for e in events if e['phase']=='COM_COMPLETE'];com_ok=False
    if len(completion)==1:
        event=completion[0];yaw=2*np.arctan2(root[0,6],root[0,3])
        # Protected controller retains entry yaw, recover it from BRAKE entry.
        brake=np.flatnonzero(ph=='BRAKE')
        if len(brake):
            w,x,y,zz=root[brake[0],3:7];yaw=np.arctan2(2*(w*zz+x*y),1-2*(y*y+zz*zz))
        forward=np.array([np.cos(yaw),np.sin(yaw)])
        stable &= (np.linalg.norm(com[:,:2]-event['goal_xy'],axis=-1)<.015) & (((com[:,:2]-event['start_xy'])@forward)>=.01)
        com_ok=True
    else:stable[:]=False
    run=best=0
    for valid in stable & (ph=='HOLD'):
        run=run+1 if valid else 0;best=max(best,run)
    longest=best*dt
    claimed=record.get('state')=='success' if engine=='mujoco' else record['success']
    accepted=bool(claimed and not errors and all(f['passed'] for f in foot_checks) and com_ok and longest>=1.-1e-9 and t[-1]<24.)
    return dict(episode=i,claimed_success=bool(claimed),accepted=accepted,source_reason=record['reason'],phase=record['phase'],
        safety_findings=errors,peak_speed_excess_rad_s=speed_excess,peak_torque_excess_nm=torque_excess,
        max_forbidden_force_n=bad_contact,pd_error_nm=pd_error,applied_error_nm=applied_error,
        delayed_target_error_rad=delayed_target_error,physics_samples=len(t),longest_stationary_hold_s=longest,feet=foot_checks)


def main():
    p=argparse.ArgumentParser();p.add_argument('folders',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    cfg=json.loads((ROOT/'policy/contract.json').read_text())['configuration']['task'];groups=[]
    for folder in args.folders:
        report=json.loads((folder/'report.json').read_text());engine='mujoco' if 'inference_device' in report else 'isaac'
        spec=report.get('exit_spec') or json.loads((folder/'exit_metadata.json').read_text())['exit_spec']
        episodes=[audit_episode(folder,e,engine,cfg,spec) for e in report['episodes']]
        successes=sum(e['accepted'] for e in episodes);missing=report['started_missing_terminal'];not_run=report['not_run']
        group=dict(path=str(folder.resolve()),engine=engine,total=32,successes=successes,normal_failures=len(episodes)-successes,
            started_missing_terminal=missing,not_run=not_run,passed=bool(successes>=30 and missing==0 and not_run==0 and len(episodes)==32),
            reasons=dict(Counter(e['source_reason'] for e in episodes)),phases=dict(Counter(e['phase'] for e in episodes)),episodes=episodes)
        groups.append(group)
    result=dict(verdict='PASSED' if len(groups)==4 and all(g['passed'] for g in groups) else 'REJECTED',formal_acceptance=bool(len(groups)==4 and all(g['passed'] for g in groups)),groups=groups)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='groups'}));print([(g['engine'],g['successes'],g['normal_failures'],g['started_missing_terminal'],g['not_run']) for g in groups])
if __name__=='__main__':main()
