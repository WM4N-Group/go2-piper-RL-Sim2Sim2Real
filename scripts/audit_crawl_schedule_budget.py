"""Necessary nominal stepping-time budget from saved Isaac traces.

Assumes fixed stance anchors (no progress credited to slip), world-x steps,
constant stride/duration, and the existing20cm task's foot-inside threshold.
This is a lower bound for that schedule, not a physical impossibility result.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def schedule_lower_bound(feet_x, stride, swing_s, box_front=.75, inset=.04):
    if len(feet_x)!=4 or not all(math.isfinite(v) for v in [*feet_x,stride,swing_s,box_front,inset]) or stride <= 0 or swing_s <= 0:
        raise ValueError('Finite geometry and positive stride/swing duration required')
    inside = box_front + inset
    # Strictly inside is required by the original task predicate.
    steps = [max(0,math.floor((inside-x)/stride)+1) for x in feet_x]
    return {'minimum_steps_by_leg':dict(zip(('FL','FR','RL','RR'),steps)),
            'minimum_total_steps':sum(steps), 'swing_time_alone_s':sum(steps)*swing_s,
            'scope':'Nominal fixed stance anchors; ignores all transfers, reloads, settling, vertical clearance and body-centering requirements.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports',type=Path,nargs='+')
    parser.add_argument('--stride',type=float,default=.24)
    parser.add_argument('--swing-s',type=float,default=2.8)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); records=[]
    for path in args.reports:
        data=json.loads(path.read_text())
        if data.get('terrain_approach',{}).get('planned_approach') and 'approach_plan_inputs' in data['terminal_states'][0]:
            measurements=[(s['env_id'],s['approach_plan_inputs'][10:22:3],'First preparation snapshot, before any step')
                          for s in data['terminal_states']]
        else:
            trace=next(value for key,value in data.items() if key.startswith('trace_env'))
            state=next(s for s in trace if s['lift_released_at_s']>=0)
            measurements=[(data['inspect_env_index'],[point[0] for point in state['feet_position']],state['step'])]
        for env_id,feet,measurement in measurements:
            records.append({'report':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'seed':data['seed'],'env_id':env_id,'measurement':measurement,
                            'measured_foot_x_m':feet, **schedule_lower_bound(feet,args.stride,args.swing_s)})
    result={'stride_m':args.stride,'swing_s':args.swing_s,'diagnostic_episode_s':24,'original_episode_s':12,
            'records':records,'conclusion':'If the swing-only bound exceeds24s, this fixed schedule cannot serve the24s task. This does not imply slow stable climbing is physically impossible.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'states':len(records),'minimum_steps_range':[min(r['minimum_total_steps'] for r in records),max(r['minimum_total_steps'] for r in records)],'swing_only_seconds_range':[min(r['swing_time_alone_s'] for r in records),max(r['swing_time_alone_s'] for r in records)]},indent=2))


if __name__=='__main__':main()
