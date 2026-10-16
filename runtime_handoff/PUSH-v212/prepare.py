from pathlib import Path
import json,shutil,hashlib,time
B=Path(__file__).resolve().parent;R=B.parent;P=R/'push-fixed-validation-v210';T=B/'train'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=json.loads((P/'plan.json').read_text())
for rel,h in parent['source_hashes'].items():assert sha(P/'train'/rel)==h,rel
static=json.loads((R/'push-path-shortcut-audit-v211/result.json').read_text())
assert static['direct']['passes_static55mm']
if not T.exists():shutil.copytree(P/'train',T,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
else:
 for rel,h in parent['source_hashes'].items():assert sha(T/rel)==h,rel
f=T/'mujoco/deploy/piper_push_safe_approach.json';old=json.loads(f.read_text());pathsha=sha(f)
assert pathsha==static['source_path_sha256']
new={k:old[k] for k in ('schema_version','robot','settle_position_tolerance_rad','settle_velocity_tolerance_rad_s')}
new.update(purpose='Original-start direct nominal approach dynamic diagnostic,not validated',waypoints=[old['waypoints'][0],old['waypoints'][-1]],v212_provenance=dict(parent_sha256=pathsha,static_audit_sha256=sha(R/'push-path-shortcut-audit-v211/result.json'),scope=static['scope']))
f.write_text(json.dumps(new,indent=2)+'\n')
v=dict(parent['variants'][0]);v.update(label='trained8052direct',gpu=0);v.pop('seed')
plan=dict(scope='Used development3701/8 then2701/32 original reset48s diagnostic. Only21-point nominal path replaced by same first/final2 points. All speed,smoothing,arrival,actual collision,clearance,effort,contact and settle gates unchanged;not heldout or original12s acceptance.',parent_plan_sha256=sha(P/'plan.json'),geometry_root=parent['geometry_root'],variants=[v],source_hashes={rel:sha(T/rel) for rel in parent['source_hashes']},time=time.time())
changed=[rel for rel,h in plan['source_hashes'].items() if h!=parent['source_hashes'][rel]]
assert changed==['mujoco/deploy/piper_push_safe_approach.json'],changed
(B/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=sha(B/'plan.json'),changed=changed)))
