"""Sampled joint/body preflight for a ground approach step, not terrain clearance.

The original actuator limits and measured support/contact gates remain required.
A feasible sampled reference is not a dynamics, collision or motor safety proof.
"""
import torch
from crawl_leg_kinematics import rotate_vector
from crawl_support import flat_swing_arc, smooth_fraction, level_orientation
from crawl_cycle import path_support_shift, next_support_preparation, triangle_margin, transfer_duration, level_transfer_duration


def plan_ground_approach(kinematics, base, quat, com, feet, captured_q, lower, upper,
                         leg, stride, duration, first=False, support_search=False):
    n, device = len(base), base.device
    # Simultaneous body advance is chosen from geometry, not stride/4 by fiat.
    advances = torch.linspace(.02, .12, 11, device=device, dtype=base.dtype)
    count = len(advances)
    repeat = lambda value: value.repeat_interleave(count, dim=0)
    b, q, c, f = map(repeat, (base, quat, com, feet))
    anchor, lo, hi = map(repeat, (captured_q, lower, upper))
    legs = repeat(leg)
    a = advances.repeat(n)
    rows = torch.arange(len(b), device=device)
    all_orders = torch.tensor([[k]+[j for j in range(4) if j != k] for k in range(4)], device=device)
    order = all_orders[legs]
    triangle = f.gather(1, order[:, 1:, None].expand(-1, -1, 3))[:, :, :2]
    advance = torch.zeros_like(c[:, :2]); advance[:, 0] = a
    if first:
        predicted = f.clone(); predicted[:, 0, 0] += stride
        delta_xy = next_support_preparation(c[:, :2], triangle, advance, predicted[:, [0, 1, 2], :2])
        goal_q = level_orientation(q, torch.ones_like(a))
        shift_duration = level_transfer_duration(delta_xy.norm(dim=1), q)
    else:
        delta_xy = path_support_shift(c[:, :2], triangle, advance)
        goal_q = q
        shift_duration = transfer_duration(delta_xy.norm(dim=1))
    if support_search:
        # Search within the triangle eroded by both the desired margin and the
        # upcoming body advance. All coordinates here are relative to the COM.
        local_triangle = triangle-c[:,None,:2]
        edge = local_triangle.roll(-1,1)-local_triangle
        area = edge[:,0,0]*edge[:,1,1]-edge[:,0,1]*edge[:,1,0]
        normal = torch.stack((-edge[...,1],edge[...,0]),dim=-1)
        normal *= area.sign()[:,None,None]/edge.norm(dim=-1).clamp_min(1e-8)[...,None]
        offset = (normal*local_triangle).sum(-1)+.03+(-(normal*advance[:,None]).sum(-1)).clamp_min(0)
        other, other_offset = normal.roll(-1,1),offset.roll(-1,1)
        det=normal[...,0]*other[...,1]-normal[...,1]*other[...,0]
        safe=torch.where(det.abs()>1e-8,det,torch.ones_like(det))
        vertices=torch.stack((offset*other[...,1]-normal[...,1]*other_offset,
                              normal[...,0]*other_offset-offset*other[...,0]),dim=-1)/safe[...,None]
        centroid=vertices.mean(dim=1)
        close=path_support_shift(c[:,:2],triangle,advance)
        proposals=torch.cat((delta_xy[:,None],close[:,None],centroid[:,None],
                             (vertices+centroid[:,None])/2),dim=1)
        placements=proposals.shape[1]
        expand=lambda value:value.repeat_interleave(placements,dim=0)
        b,q,c,f,anchor,lo,hi,legs,a,triangle,advance,goal_q=map(expand,(b,q,c,f,anchor,lo,hi,legs,a,triangle,advance,goal_q))
        delta_xy=proposals.reshape(-1,2)
        shift_duration=(level_transfer_duration(delta_xy.norm(dim=1),q) if first
                        else transfer_duration(delta_xy.norm(dim=1)))
        count*=placements
        rows=torch.arange(len(b),device=device)
    delta = torch.cat((delta_xy, torch.zeros_like(a[:, None])), dim=1)
    path_margin = torch.minimum(triangle_margin(c[:, :2]+delta_xy, triangle),
                               triangle_margin(c[:, :2]+delta_xy+advance, triangle))
    u = torch.linspace(0., 1., 65, device=device, dtype=base.dtype)
    s = smooth_fraction(u)
    shift_b = b[:, None]+delta[:, None]*s[None, :, None]
    shift_q = (level_orientation(q[:, None].expand(-1,len(u),-1).reshape(-1,4),u[None].expand(len(b),-1).reshape(-1)).reshape(len(b),len(u),4)
               if first else q[:, None].expand(-1,len(u),-1))
    local_shift = rotate_vector(shift_q[:, :, None], f[:, None]-shift_b[:, :, None], inverse=True)
    joints_shift = kinematics.inverse(local_shift)
    shift_margin = torch.minimum(joints_shift-(anchor-.7)[:,None],(anchor+.7)[:,None]-joints_shift).amin(dim=(1,2,3))
    # First step recaptures the measured loaded stance after preparation, as
    # in the established controller. Others retain their pre-transfer anchor.
    swing_anchor = joints_shift[:, -1] if first else anchor
    body = (b+delta)[:, None].expand(-1,len(u),-1).clone()
    body[:, :, 0] += a[:, None]*s[None]
    targets = f[:, None].expand(-1,len(u),-1,-1).clone()
    targets[rows, :, legs] += flat_swing_arc(u, stride)[None]
    local = rotate_vector(goal_q[:,None,None],targets-body[:,:,None],inverse=True)
    joints = kinematics.inverse(local)
    swing_margin = torch.minimum(joints-(swing_anchor-.7)[:,None],(swing_anchor+.7)[:,None]-joints).amin(dim=(1,2,3))
    soft_margin = torch.minimum(torch.minimum(joints-lo[:,None],hi[:,None]-joints).amin(dim=(1,2,3)),
                                torch.minimum(joints_shift-lo[:,None],hi[:,None]-joints_shift).amin(dim=(1,2,3)))
    residual = torch.maximum((kinematics.forward(joints)-local).norm(dim=-1).amax(dim=(1,2)),
                             (kinematics.forward(joints_shift)-local_shift).norm(dim=-1).amax(dim=(1,2)))
    # Include the retained3mm contact search endpoint in position feasibility.
    probe = targets[:, -1].clone(); probe[rows, legs, 2] -= .003
    probe_local = rotate_vector(goal_q[:,None],probe-body[:,-1,None],inverse=True)
    probe_j = kinematics.inverse(probe_local)
    swing_margin = torch.minimum(swing_margin,torch.minimum(probe_j-(swing_anchor-.7),(swing_anchor+.7)-probe_j).amin(dim=(1,2)))
    soft_margin = torch.minimum(soft_margin,torch.minimum(probe_j-lo,hi-probe_j).amin(dim=(1,2)))
    residual = torch.maximum(residual,(kinematics.forward(probe_j)-probe_local).norm(dim=-1).amax(dim=1))
    def rates(path, seconds):
        velocity = path.diff(dim=1)*(len(u)-1)/seconds[:,None,None,None]
        acceleration = velocity.diff(dim=1)*(len(u)-1)/seconds[:,None,None,None]
        return velocity.abs().amax(dim=(1,2,3))*1.1, acceleration.abs().amax(dim=(1,2,3))*1.1
    v, acc = rates(joints,torch.full_like(a,duration)); sv, sa = rates(joints_shift,shift_duration)
    v, acc = torch.maximum(v,sv), torch.maximum(acc,sa)
    margin = torch.minimum(torch.minimum(shift_margin,swing_margin),soft_margin)
    feasible = ((margin >= .025) & (residual < .001) & (path_margin >= .03-1e-5)
                & (delta_xy.norm(dim=1) <= .14) & (v <= 1.) & (acc <= 5.) & (1.875*a/duration <= .075)
                & (5.774*a/duration**2 <= .133))
    # Keep body movement small and favor the established stride/4 advance when
    # it is feasible. Every chosen candidate must pass the sampled preflight.
    cost = (a-stride/4).square()+.1*delta_xy.square().sum(dim=1)
    cost = cost.masked_fill(~feasible,float('inf')).reshape(n,count)
    choice = cost.argmin(dim=1)+torch.arange(n,device=device)*count
    valid = feasible.reshape(n,count).any(dim=1)
    return dict(feasible=valid, advance=torch.where(valid,a[choice],0.),
                delta=torch.where(valid[:,None],delta[choice],0.),
                duration=shift_duration[choice], joint_margin=margin[choice],
                joint_speed=v[choice],joint_acceleration=acc[choice],
                fk_residual=residual[choice],support_margin=path_margin[choice],
                feasible_candidates=feasible.reshape(n,count).sum(dim=1))
