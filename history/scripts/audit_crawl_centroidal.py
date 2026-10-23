"""Replay recorded Isaac geometry and audit an offline route's static loading."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from crawl_centroidal import ArticulatedModel, three_contact_forces
from plan_crawl_route import Geometry, rotation, foot_path, body_path, polygon_margin


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_model(usd, snapshot):
    authored = ArticulatedModel.from_usd(usd)
    if sha(usd) != snapshot['usd_sha256']:
        raise ValueError('Snapshot USD hash differs')
    mass = np.array(snapshot['default_masses']); com = np.array(snapshot['local_com_transforms_xyzw'])[:,:,:3]
    np.testing.assert_allclose(mass,np.broadcast_to(mass[:1],mass.shape),atol=1e-8,rtol=0)
    np.testing.assert_allclose(com,np.broadcast_to(com[:1],com.shape),atol=1e-8,rtol=0)
    model = authored.with_runtime_properties(snapshot['body_names'],mass[0],com[0])
    actual = np.array(snapshot['actual_masses'])
    inferred = model.masses_from_total(actual.sum(1))
    ids = [model.body_index[n] for n in snapshot['body_names']]
    np.testing.assert_allclose(inferred[:,ids],actual,atol=1e-6,rtol=0)
    delta=actual[:,snapshot['body_names'].index(model.data['root'])]-mass[0,snapshot['body_names'].index(model.data['root'])]
    assert delta.min()>=-1.-1e-6 and delta.max()<=3.+1e-6
    initial = model.forward(snapshot['joint_position'],snapshot['joint_names'],snapshot['root_position'],
                            snapshot['root_quaternion_wxyz'],inferred)
    body_error=np.linalg.norm(initial['position'][:,ids]-snapshot['body_position'],axis=-1).max()
    com_error=np.linalg.norm(initial['body_com'][:,ids]-snapshot['body_com_position'],axis=-1).max()
    assert body_error<1e-5 and com_error<1e-5
    changes=[dict(body=n,usd_mass=float(authored.mass[authored.body_index[n]]),runtime_mass=float(model.mass[model.body_index[n]]))
             for n in model.names if abs(authored.mass[authored.body_index[n]]-model.mass[model.body_index[n]])>1e-6]
    return authored,model,dict(body_position_error_m_max=float(body_error),body_com_position_error_m_max=float(com_error),
                               base_mass_delta_range_kg=[float(delta.min()),float(delta.max())],mass_changes=changes)


def replay(model, authored, path):
    d=json.loads(path.read_text());trace=next(v for k,v in d.items() if k.startswith('trace_env'))
    env=d['inspect_env_index'];q=np.array([s['joint_position'] for s in trace])
    pos=np.array([s['robot_position'] for s in trace]);quat=np.array([s['root_quaternion'] for s in trace])
    expected=np.array([s['com_position'] for s in trace]);feet=np.array([s['feet_position'] for s in trace])
    errors={}
    for label,m in [('usd_only',authored),('runtime_properties',model)]:
        state=m.forward(q,d['joint_names'],pos,quat,m.masses_from_total([d['robot_mass_kg'][env]]))
        err=np.linalg.norm(state['com']-expected,axis=-1)
        foot_ids=[m.body_index[leg+'_foot'] for leg in ('FL','FR','RL','RR')]
        errors[label]=dict(com_error_m_max=float(err.max()),com_error_m_median=float(np.median(err)),
                           foot_error_m_max=float(np.linalg.norm(state['position'][:,foot_ids]-feet,axis=-1).max()))
    assert errors['runtime_properties']['com_error_m_max']<1e-5
    assert errors['runtime_properties']['foot_error_m_max']<1e-5
    return dict(report=str(path),sha256=sha(path),env_id=env,frames=len(trace),errors=errors)


def audit_route(model, snapshot, route_report, original):
    env=original['inspect_env_index']
    route=next(r for r in route_report['routes'] if r['env_id']==env)
    trace=next(v for k,v in original.items() if k.startswith('trace_env'))
    v=np.array(route['initial_snapshot'])
    frame=min(trace,key=lambda s:np.linalg.norm(np.array(s['robot_position'])-v[:3]))
    np.testing.assert_allclose(frame['robot_position'],v[:3],atol=1e-9)
    full_q=np.array(frame['joint_position']);names=original['joint_names']
    leg_slots=np.array([[names.index(leg+'_'+part+'_joint') for part in ('hip','thigh','calf')]
                        for leg in ('FL','FR','RL','RR')])
    np.testing.assert_allclose(full_q[leg_slots],v[22:34].reshape(4,3),atol=1e-7)
    initial_rot=Rotation.from_quat(v[[4,5,6,3]]).as_matrix()
    offset=initial_rot.T@(v[7:10]-v[:3])
    feet=v[10:22].reshape(4,3).copy();u=np.linspace(0,1,385)
    leg_model=Geometry(original['leg_geometry']);results=[]
    force_limits=np.array(snapshot['joint_effort_limits'])
    np.testing.assert_allclose(force_limits,np.broadcast_to(force_limits[:1],force_limits.shape),atol=1e-6)
    effort=np.array([force_limits[0,snapshot['joint_names'].index(n)] for n in model.joint_names])
    foot_names=[leg+'_foot' for leg in ('FL','FR','RL','RR')]
    for step in route['steps']:
        if not step['valid']:break
        leg=('FL','FR','RL','RR').index(step['leg']);body=body_path(np.array(step['body_knots']),u)
        target=np.array(step['target']);f=np.tile(feet,(len(u),1,1));f[:,leg]=foot_path(feet[leg],target,u)
        qleg,_,_=leg_model.inverse(f,body);q=np.tile(full_q,(len(u),1));q[:,leg_slots]=qleg
        xyzw=Rotation.from_euler('xyz',body[:,[4,3,5]]).as_quat()
        state=model.forward(q,names,body[:,:3],xyzw[:,[3,0,1,2]],model.masses_from_total([original['robot_mass_kg'][env]]))
        frozen=body[:,:3]+np.einsum('nij,j->ni',rotation(body),offset)
        exact_margin=polygon_margin(state['com'][:,:2],np.delete(feet,leg,axis=0)).min()
        forces=three_contact_forces(f,state['com'],state['masses'].sum(1),leg)
        torque=model.static_torque(state,foot_names,forces)
        ratio=abs(torque)/effort
        arg=np.unravel_index(ratio.argmax(),ratio.shape)
        support=[i for i in range(4) if i!=leg]
        results.append(dict(step=step['index'],leg=step['leg'],com_frozen_error_m_max=float(np.linalg.norm(state['com']-frozen,axis=-1).max()),
            com_frozen_xy_error_m_max=float(np.linalg.norm(state['com'][:,:2]-frozen[:,:2],axis=-1).max()),
            articulated_com_margin_m=float(exact_margin),frozen_com_margin_m=step['frozen_com_support_margin_m'],
            minimum_stance_force_n=float(forces[:,support,2].min()),maximum_stance_force_n=float(forces[:,support,2].max()),
            peak_static_effort_ratio=float(ratio.max()),peak_static_effort_joint=model.joint_names[arg[1]]))
        feet[leg]=target
    return dict(env_id=env,initial_trace_step=frame['step'],steps=results,
                scope='Replay accepted cn swing geometry only. Arm held at measured initial joints. Actual model COM, but static vertical forces: no acceleration/inertia/impact/friction test; NOT measured contact or torque.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--usd',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--reports',type=Path,nargs='+',required=True);p.add_argument('--route',type=Path)
    p.add_argument('--route-source',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():p.error('Output exists')
    if bool(args.route)!=bool(args.route_source):p.error('Route and its source are required together')
    snapshot=json.loads(args.snapshot.read_text())
    authored,model,check=runtime_model(args.usd,snapshot)
    out=dict(scope='Offline replay of remote snapshots and existing trajectories, no new skill evaluation',
             snapshot_sha256=sha(args.snapshot),usd_sha256=sha(args.usd),initialized_model_check=check,
             source_sha256={name:sha(Path(__file__).with_name(name)) for name in
                            ('audit_crawl_centroidal.py','crawl_centroidal.py','plan_crawl_route.py')},
             replays=[replay(model,authored,r) for r in args.reports],runtime_model=model.data)
    if args.route:
        route=json.loads(args.route.read_text());source=json.loads(args.route_source.read_text())
        assert route['input_sha256']==sha(args.route_source)
        out['route_sha256']=sha(args.route);out['route_static_audit']=audit_route(model,snapshot,route,source)
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('runtime_model','route_static_audit')},indent=2))


if __name__=='__main__':main()
