from pathlib import Path
import json,subprocess,os,hashlib,fcntl,time,traceback
D=Path(__file__).resolve().parent;R=D.parent;root=R.parent;src=root/'climb-swing-time-full-20261007-iy/train'
lock=(D/'screen.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (D/'screen-summary.json').exists();p=json.loads((D/'plan.json').read_text())
for n,h in p['files'].items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h,n
state=dict(status='waiting',scope=p['scope'],active=[],entries=[],not_run=list(p['seeds']))
def save():
 state['updated']=time.time();tmp=D/'screen-summary.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(D/'screen-summary.json')
save()
try:
 deadline=time.monotonic()+7200
 while True:
  try:prior=json.loads((R/'transition-nav-climb-v066/screen-summary.json').read_text())
  except (FileNotFoundError,json.JSONDecodeError):prior={'status':'waiting'}
  if prior['status'] not in ['waiting','running']:
   assert prior['status']=='diagnostics_complete' and len(prior['entries'])==1
   e=prior['entries'][0]
   if e['returncode']!=0 or e['missing_report'] or e['report']['outcome']!='nav_climb_nav_platform_target_stable':
    state.update(status='predecessor_not_complete',reason='v066 full-chain success required; no regression physics launched');save();raise SystemExit(0)
   f=R/'transition-nav-climb-v066/terminal-audit.json'
   if f.exists():
    try:audit=json.loads(f.read_text())
    except json.JSONDecodeError:audit=None
    if audit is not None:
     c=audit['counts'];assert c['full_chain_success']==1 and c['missing_terminal']==0 and c['invalid_evidence']==0
     if not all(e.get('brake_reference_smoothness',{}).get('passed',False) for e in audit['entries']):
      state.update(status='predecessor_not_complete',reason='v066 reference smoothness gate failed; no regression physics launched');save();raise SystemExit(0)
     break
  assert time.monotonic()<deadline,'Parent wait expired'
  time.sleep(15)
 state['status']='running';save()
 assert hashlib.sha256((src.parent/'plan.json').read_bytes()).hexdigest()==p['source_plan_sha256']
 for n,h in json.loads((src.parent/'plan.json').read_text())['source_sha256'].items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,n
 for seed in p['seeds']:
  uuids=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader'],text=True);gpu={int(x.split(',')[0]):x.split(',')[1].strip() for x in uuids.splitlines()}[0]
  jobs=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],text=True)
  for line in jobs.splitlines():
   pid,uuid,memory=(v.strip() for v in line.split(','))
   if uuid!=gpu:continue
   args=subprocess.run(['ps','-p',pid,'-o','args='],capture_output=True,text=True).stdout
   assert str(R/'transition-nav-climb-video-v062/probe.py') in args and '--device cuda:1' in args and int(memory.split()[0])<=512,'GPU0 occupied'

  out=D/f'seed{seed}';cmd=['timeout','--kill-after=30','2400','/opt/isaac/bin/python',str(D/'probe.py'),'--source',str(src),'--nav-actor',str(root/'2026-09-15/eval-t8FO0a/piper-nav-baseline-bundle/policy.pt'),'--output',str(out),'--seed',str(seed),'--seconds','420','--headless','--device','cuda:0']
  env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0',PYTHONPATH=str(src/'source/LeggedManip_Lab')+':'+str(D),PYTHONUNBUFFERED='1')
  state['active']=[seed];state['not_run'].remove(seed);save()
  with (D/f'seed{seed}.log').open('x') as log:
   proc=subprocess.Popen(cmd,cwd=src,env=env,stdout=log,stderr=subprocess.STDOUT);(D/f'launch-{seed}.json').write_text(json.dumps(dict(pid=proc.pid,gpu=0,command=cmd),indent=2));rc=proc.wait()
  f=out/'report.json';report=json.loads(f.read_text()) if f.exists() else None
  state['entries'].append(dict(seed=seed,returncode=rc,missing_report=report is None,report=report));state['active']=[];save()
  if rc!=0 or report is None or report['outcome']!='nav_climb_nav_platform_target_stable':break
 state['status']='diagnostics_complete';save()
except Exception:state.update(status='runner_error',error=traceback.format_exc());save()
