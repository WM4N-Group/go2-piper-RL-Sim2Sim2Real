"""Offline whole-route geometry and timing diagnostic using saved Isaac states.

This never controls a simulator. COM is a frozen body-frame approximation; the
sampled geometry, spherical foot envelope and actuator retiming do not certify
contact forces, whole-body collision, motor loads, or task success. In particular,
zero-time contact transitions are only an optimistic timing comparison.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation


def smooth(u):
    return u**3 * (10 + u * (-15 + 6*u))


def rotation(poses):
    # Pose layout: world xyz, pitch, roll, yaw. Preserve measured initial yaw.
    return Rotation.from_euler('xyz', poses[:, [4, 3, 5]]).as_matrix()


class Geometry:
    def __init__(self, geometry):
        self.hip = np.array(geometry['hip_origins'])
        self.lateral = np.array(geometry['hip_lateral_offsets'])
        self.lengths = np.array(geometry['link_lengths'])

    def inverse(self, feet, poses):
        local = np.einsum('nji,nkj->nki', rotation(poses), feet-poses[:, None, :3]) - self.hip
        x, y, z = np.moveaxis(local, -1, 0)
        radial = y*y+z*z-self.lateral**2
        zz = -np.sqrt(np.maximum(radial, 1e-12))
        hip = np.arctan2(z, y)-np.arctan2(zz, self.lateral)
        hip = np.arctan2(np.sin(hip), np.cos(hip))
        cosine = (x*x+zz*zz-(self.lengths**2).sum(1))/(2*self.lengths.prod(1))
        knee = -np.arccos(np.clip(cosine, -1, 1))
        thigh = np.arctan2(-x, -zz)-np.arctan2(self.lengths[:, 1]*np.sin(knee),
                     self.lengths[:, 0]+self.lengths[:, 1]*np.cos(knee))
        return np.stack((hip, thigh, knee), -1), cosine, radial

    def forward(self, joints, poses):
        hip, thigh, knee = np.moveaxis(joints, -1, 0)
        up, low = self.lengths.T
        x = -up*np.sin(thigh)-low*np.sin(thigh+knee)
        sagittal = -up*np.cos(thigh)-low*np.cos(thigh+knee)
        y = self.lateral*np.cos(hip)-sagittal*np.sin(hip)
        z = self.lateral*np.sin(hip)+sagittal*np.cos(hip)
        local = np.stack((x, y, z), -1)+self.hip
        return np.einsum('nij,nkj->nki', rotation(poses), local)+poses[:, None, :3]


def polygon_margin(points, feet):
    hull = ConvexHull(feet[:, :2])
    # SciPy's hull normals have unit length and point outward.
    return -(points @ hull.equations[:, :2].T+hull.equations[:, 2])


def foot_path(origin, target, u):
    """Ground arc, or lift completely above the box before crossing its edge."""
    if abs(target[2]-origin[2]) < .01:
        path = origin+smooth(u)[:, None]*(target-origin)
        path[:, 2] += .045*64*u**3*(1-u)**3
        return path
    high = max(origin[2], target[2])+.03
    waypoints = np.array([origin, [*origin[:2], high], [*target[:2], high], target])
    segment = np.minimum((u*3).astype(int), 2)
    return waypoints[segment]+smooth(u*3-segment)[:, None]*(waypoints[segment+1]-waypoints[segment])


def body_path(knots, u):
    segment = np.minimum((u*3).astype(int), 2)
    return knots[segment]+smooth(u*3-segment)[:, None]*(knots[segment+1]-knots[segment])


def sampled_retime(joints):
    """Uniform normalized path; reported minimum excludes all contact waits.

    Finite differences are a sampled estimate, not a continuous-time lower-bound
    theorem. Include both endpoints, and use a separate 10% duration reserve.
    """
    rate = np.diff(joints, axis=0)*(len(joints)-1)
    acceleration = np.diff(rate, axis=0)*(len(joints)-1)
    nominal = max(abs(rate).max()/2.5, np.sqrt(abs(acceleration).max()/15))
    seconds = max(.02, nominal*1.1)
    return dict(sampled_minimum_s=float(nominal), reserved_s=float(seconds),
                reference_speed_rad_s=float(abs(rate).max()/seconds),
                reference_acceleration_rad_s2=float(abs(acceleration).max()/seconds**2))


def solve_step(model, start, feet, anchor, lower, upper, com_offset, leg, target):
    """Couple body lift/pitch/advance to one foot swing and a four-foot transfer."""
    support = np.delete(feet, leg, axis=0)
    def paths(flat, count):
        knots = flat.reshape(4, 5)
        knots = np.column_stack((knots, np.full(4, start[5])))
        u = np.linspace(0, 1, count)
        swing = body_path(knots, u)
        prep = start+smooth(u)[:, None]*(knots[0]-start)
        f = np.tile(feet, (count, 1, 1))
        f[:, leg] = foot_path(feet[leg], target, u)
        return knots, swing, prep, f

    def measurements(flat, count):
        knots, swing, prep, f = paths(flat, count)
        bodies = np.concatenate((swing, prep))
        feet_path = np.concatenate((f, np.tile(feet, (count, 1, 1))))
        q, cosine, radial = model.inverse(feet_path, bodies)
        com = bodies[:, :3]+np.einsum('nij,j->ni', rotation(bodies), com_offset)
        return dict(knots=knots, swing=swing, prep=prep, feet=f, joints=q,
                    cosine=cosine, radial=radial,
                    joint_margin=np.minimum(q-lower, upper-q),
                    anchor_margin=.7-abs(q-anchor),
                    support_margin=polygon_margin(com[:count, :2], support),
                    preparation_margin=polygon_margin(com[count:, :2], feet),
                    residual=np.linalg.norm(model.forward(q, bodies)-feet_path, axis=-1))

    def constraints(flat):
        a = measurements(flat, 25)
        return np.concatenate(((a['joint_margin']-.03).ravel(), (a['anchor_margin']-.03).ravel(),
               (1-a['cosine']).ravel(), (1+a['cosine']).ravel(), a['radial'].ravel(),
               (a['support_margin']-.032).ravel(), a['preparation_margin'].ravel()))

    desired = np.tile(start[:5], (4, 1))
    desired[:, 0] = np.mean(feet[:, 0])
    desired[:, 1] = support[:, 1].mean()*.5
    desired[:, 2] = max(.29, feet[:, 2].mean()+.27)
    desired[:, 3] = -np.arctan2(feet[:2, 2].mean()-feet[2:, 2].mean(), .4)
    desired[:, 4] = 0
    if target[2] > .15 and feet[leg, 2] < .1:
        desired[:, 2] += .045
        desired[:, 3] += -.12 if leg < 2 else .12

    def cost(flat):
        knots = flat.reshape(4, 5)
        return (np.sum((knots-desired)**2*np.array([1, 2, 2, .05, .1]))
                +2*np.sum(np.diff(knots, axis=0)**2)+.2*np.sum((knots[0]-start[:5])**2))

    bounds = [(start[0]-.1, start[0]+.3), (-.3, .3), (.21, .57), (-.42, .42), (-.22, .22)]*4
    seeds = [desired]
    for height in (.35, .40, .45):
        guess = desired.copy(); guess[:, 2] = height; guess[:, 3] = 0
        seeds.append(guess)
    best = None
    for seed in seeds:
        init = np.clip(seed.ravel(), np.array(bounds)[:, 0], np.array(bounds)[:, 1])
        result = minimize(cost, init, method='SLSQP', constraints={'type': 'ineq', 'fun': constraints},
                          bounds=bounds, options={'maxiter': 120, 'ftol': 1e-9})
        score = float(constraints(result.x).min())
        if best is None or score > best[0]:
            best = score, result
        if score > -1e-7:
            break
    score, result = best
    dense = measurements(result.x, 385)
    margin = min(dense['joint_margin'].min(), dense['anchor_margin'].min())
    nearest_box = np.clip(dense['feet'], [.75, -.6, 0], [1.95, .6, .2])
    foot_box_clearance = np.linalg.norm(dense['feet']-nearest_box, axis=-1).min()-.024
    valid = (score > -1e-7 and margin >= .025 and dense['support_margin'].min() >= .03
             and dense['preparation_margin'].min() >= -1e-6 and dense['residual'].max() < 1e-6
             and foot_box_clearance >= -1e-6)
    summary = dict(valid=bool(valid), optimizer_message=str(result.message),
        optimizer_min_constraint=score, joint_margin_rad=float(margin),
        frozen_com_support_margin_m=float(dense['support_margin'].min()),
        frozen_com_preparation_margin_m=float(dense['preparation_margin'].min()),
        foot_sphere_box_clearance_m=float(foot_box_clearance),
        fk_residual_m=float(dense['residual'].max()),
        transfer=sampled_retime(dense['joints'][385:]), swing=sampled_retime(dense['joints'][:385]),
        body_knots=dense['knots'].tolist(), target=target.tolist(),
        end_joints=dense['joints'][384].tolist(),
        pitch_range_rad=[float(dense['swing'][:, 3].min()), float(dense['swing'][:, 3].max())])
    return summary


def plan_route(report, env_id, stride=.20):
    state = next(s for s in report['terminal_states'] if s['env_id'] == env_id)
    values = np.array(state['approach_plan_inputs'])
    if values.shape != (59,) or not np.isfinite(values).all() or not 0 < stride <= .3:
        raise ValueError('Expected a finite measured 59-value snapshot and stride in (0,.3]')
    roll, pitch, yaw = Rotation.from_quat(values[[4, 5, 6, 3]]).as_euler('xyz')
    pose = np.r_[values[:3], pitch, roll, yaw]
    com_offset = rotation(pose[None])[0].T @ (values[7:10]-pose[:3])
    feet = values[10:22].reshape(4, 3).copy()
    joints, lower, upper = [values[a:a+12].reshape(4, 3) for a in (22, 34, 46)]
    model = Geometry(report['leg_geometry'])
    steps = []
    complete = False
    for index in range(40):
        leg = (0, 3, 1, 2)[index % 4]
        target = feet[leg].copy()
        target[0] = min(target[0]+(.1 if index < 2 else stride), 1.35+(.23 if leg < 2 else -.23))
        if .69 < target[0] < .83:
            target[0] = .69 if feet[leg, 0] < .58 else .83
        target[2] = .2245 if target[0] > .75 else feet[leg, 2]
        result = solve_step(model, pose, feet, joints, lower, upper, com_offset, leg, target)
        result.update(index=index, leg=('FL', 'FR', 'RL', 'RR')[leg], origin=feet[leg].tolist())
        steps.append(result)
        if not result['valid']:
            break
        pose = np.array(result['body_knots'][-1]); feet[leg] = target
        joints = np.array(result['end_joints'])
        complete = bool((feet[:, 0] > .79).all() and (feet[:, 0] < 1.91).all()
                        and (abs(feet[:, 1]) < .56).all() and (feet[:, 2] > .22).all()
                        and np.linalg.norm(pose[:2]-[1.35, 0]) < .18
                        and rotation(pose[None])[0, 2, 2] > .94)
        if complete:
            break
    valid_steps = [s for s in steps if s['valid']]
    minimum = sum(s[k]['sampled_minimum_s'] for s in valid_steps for k in ('transfer', 'swing'))
    reserved = sum(s[k]['reserved_s'] for s in valid_steps for k in ('transfer', 'swing'))
    return dict(env_id=env_id, initial_snapshot=values.tolist(), steps=steps,
                geometric_route_complete=complete, valid_steps=len(valid_steps),
                final_body_pose=pose.tolist(), final_feet=feet.tolist(),
                nominal_motion_sampled_minimum_s=minimum, nominal_motion_reserved_s=reserved,
                optimistic_with_final_hold_s=reserved+1 if complete else None,
                fits_24s_even_without_contact_waits=bool(complete and reserved+1 <= 24),
                exclusions=['Initial settling/takeover', 'Unloading and reloading',
                            'Real contact/force/velocity gates', 'Final posture correction if needed'],
                dynamics_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--env-ids', type=int, nargs='+', default=[0])
    parser.add_argument('--stride', type=float, default=.20)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; keep experiment reports immutable')
    report = json.loads(args.report.read_text())
    routes = []
    for env in args.env_ids:
        route = plan_route(report, env, args.stride); routes.append(route)
        print(json.dumps({k: route[k] for k in ('env_id', 'valid_steps', 'geometric_route_complete',
              'optimistic_with_final_hold_s', 'fits_24s_even_without_contact_waits')}), flush=True)
    args.output.write_text(json.dumps(dict(
        scope='Offline sampled reference design, NOT an Isaac rollout or acceptance result',
        input_report=str(args.report), input_sha256=hashlib.sha256(args.report.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        stride_m=args.stride, box_front_m=.75, box_height_m=.20,
        joint_speed_limit_rad_s=2.5, joint_acceleration_limit_rad_s2=15,
        per_segment_duration_reserve=1.1, optimizer_samples=25, audit_samples=385,
        com_model='Measured initial whole-body COM offset, frozen in body frame; NOT articulated COM',
        collision_scope='Foot-only conservative sphere radius .024m (including .002m offset); NOT body/arm/calf meshes',
        routes=routes), indent=2)+'\n')


if __name__ == '__main__':
    main()
