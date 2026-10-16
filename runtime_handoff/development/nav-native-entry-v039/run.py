from pathlib import Path
import json,hashlib,subprocess,os,time,fcntl,traceback
R=Path('/opt/go2-piper/artifacts/go2-piper');B=R/'sim2sim-current-20261008-a';D=B/'nav-native-entry-v039';P=B/'nav-native-entry-v038';S=R/'climb-swing-time-full-20261007-iy/train'
lock=(D/'runner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not (D/'screen-summary.json').exists();plan=json.loads((D/'plan.json').read_text())
for n,h in plan['files'].items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h,n
state={'status':'waiting_registered_workspace','scope':plan['scope'],'active':[],'entries':[],'not_run':[3702,3703]}
def save():
 state['updated_unix']=time.time();tmp=D/'screen-summary.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(D/'screen-summary.json')
save()
try:
 deadline=time.monotonic()+3600
 while True:
  f=P/'screen-summary.json';parent=json.loads(f.read_text()) if f.exists() else {'status':'initializing'}
  if parent['status']=='candidate_selected':break
  if parent['status'] not in ['initializing','waiting_stop_experiments','waiting_previous_entry_regression','running']:
   state.update(status='prerequisite_not_met',parent_status=parent['status'],reason='No source-validated fixed candidate selected; no extra regression physics');save();raise SystemExit(0)
  assert time.monotonic()<deadline,'Parent wait expired';time.sleep(10)
 selection=json.loads((P/'selection.json').read_text());v=selection['case'];assert v in json.loads((P/'plan.json').read_text())['cases'];assert hashlib.sha256((P/v['name']/'report.json').read_bytes()).hexdigest()==selection['report_sha256'];assert (D/'probe.py').read_bytes()==(P/'probe.py').read_bytes()
 (D/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');state['selection']=selection;save()
 while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
  assert time.monotonic()<deadline,'GPU wait expired';time.sleep(10)
 processes=[];state['status']='running';save()
 for seed,gpu in [(3702,0),(3703,1)]:
  out=D/f'seed{seed}';assert not out.exists();cmd=['timeout','--kill-after=30','900','/opt/isaac/bin/python',str(D/'probe.py'),'--source',str(S),'--policy',str(R/'2026-09-15/eval-t8FO0a/piper-nav-baseline-bundle/policy.pt'),'--output',str(out),'--seed',str(seed),'--ee-x',str(v['ee_x']),'--ee-z',str(v['ee_z']),'--speed','.25','--body-damping',str(v['body_damping']),'--support-min-s',str(v['support_min_s']),'--blend-s','1.','--posture-template',str(D/'nav-posture-template.json'),'--seconds','60','--headless','--device',f'cuda:{gpu}'];env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0,1',PYTHONPATH=str(S/'source/LeggedManip_Lab')+':'+str(D),PYTHONUNBUFFERED='1')
  with (D/f'seed{seed}.log').open('x') as log:proc=subprocess.Popen(cmd,cwd=S,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  job={'seed':seed,'physical_gpu':gpu,'pid':proc.pid,'command':cmd};processes.append((proc,job));state['active'].append(job);state['not_run'].remove(seed);save()
 (D/'launches.json').write_text(json.dumps(state['active'],indent=2)+'\n')
 while processes:
  for proc,job in list(processes):
   rc=proc.poll()
   if rc is None:continue
   f=D/f"seed{job['seed']}"/'report.json';r=json.loads(f.read_text()) if f.exists() else None;state['entries'].append({'seed':job['seed'],'returncode':rc,'missing_report':r is None,'native_and_drift_gate_pass':r is not None and r['outcome']=='completed_native_active_diagnostic' and r['active_samples']==500 and r['active_native18_exact_samples']==500 and r['maximum_preparation_horizontal_excursion_m']<=.08 and r.get('ground_support_event') is not None,'report':r});state['active'].remove(job);processes.remove((proc,job));save()
  if processes:time.sleep(10)
 state['status']='diagnostics_complete';save()
except Exception:state.update(status='runner_error',error=traceback.format_exc());save()
