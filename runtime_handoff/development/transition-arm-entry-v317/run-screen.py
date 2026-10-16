"""Two-device development screen; stop scheduling new starts on first failure."""
from pathlib import Path
import concurrent.futures,fcntl,hashlib,json,os,subprocess,time,traceback
D=Path(__file__).resolve().parent;R=D.parent;SRC=R/'push-direct-approach-v212/train'
lock=(D/'screen.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
state_path=D/'screen-summary.json';assert not state_path.exists(),'Never overwrite screen evidence'
plan=json.loads((D/'plan.json').read_text());seeds=[3703,3705,3701,3707,3704,3706,3702,3708]
state=dict(scope='Used-start v317 box-aware frozen approach tip-envelope standoff during existing loaded final centering; nominal path+boundedresidual static preview and measured final recheck, original safety/budgets unchanged; not acceptance',status='starting',plan_sha256=hashlib.sha256((D/'plan.json').read_bytes()).hexdigest(),total_starts=seeds,entries=[],active={},not_run=seeds.copy(),started=time.time())
def save():
 state['updated']=time.time();tmp=state_path.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(state_path)
def verify():
 for name,h in plan['files'].items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h,name
 source_plan=R/'push-direct-approach-v212/plan.json'
 assert hashlib.sha256(source_plan.read_bytes()).hexdigest()==plan['source_plan_sha256']
 for name,h in json.loads(source_plan.read_text())['source_hashes'].items():assert hashlib.sha256((SRC/name).read_bytes()).hexdigest()==h,name

def run(seed,gpu):
 verify()
 out=D/f'seed{seed}-native-entry';assert not out.exists(),out
 cmd=plan['command'].copy();cmd[cmd.index('--seed')+1]=str(seed);cmd[cmd.index('--output')+1]=str(out)
 env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=str(gpu),PYTHONPATH=str(SRC/'source/LeggedManip_Lab')+':'+str(R/'runtime-push-detour-v1/mujoco'),PIPER_SOURCE_ROOT=str(SRC),PYTHONUNBUFFERED='1')
 with (D/f'seed{seed}.log').open('x') as log:
  proc=subprocess.Popen(['timeout','--kill-after=30','1800',*cmd],cwd=SRC,env=env,stdout=log,stderr=subprocess.STDOUT)
  (D/f'launch-seed{seed}.json').write_text(json.dumps(dict(pid=proc.pid,seed=seed,physical_gpu=gpu,command=cmd,started=time.time()),indent=2)+'\n');rc=proc.wait()
 report_path=out/'report.json'
 if not report_path.exists():return dict(seed=seed,physical_gpu=gpu,returncode=rc,terminal_missing=True,outcome='missing_report')
 report=json.loads(report_path.read_text());last=None
 with (out/'control.jsonl').open() as f:
  for line in f:last=json.loads(line)
 return dict(seed=seed,physical_gpu=gpu,returncode=rc,terminal_missing=False,outcome=report['outcome'],end_time_s=last['time_s'] if last else None,terminal=report['terminal'],physical_resets_after_initial=report['physical_resets_after_initial'],minimum_clearance_m=report['minimum_clearance_m'],max_torque_ratio=report['max_torque_ratio'],max_substep_arm_torque_ratio=report['max_substep_arm_torque_ratio'],effort_over_098_samples=report['effort_over_098_samples'],airborne_samples=report['airborne_samples'],under_three_support_samples=report['under_three_support_samples'],max_abs_vz_m_s=report['max_abs_vz_m_s'],max_single_foot_N=report['max_single_foot_N'],max_sum_foot_force_norm_N=report['max_sum_foot_force_norm_N'],report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),error=report.get('error'))
save()
try:
 verify();failed=False
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures={}
  def schedule(gpu):
   seed=state['not_run'].pop(0);state['active'][str(gpu)]=seed
   futures[pool.submit(run,seed,gpu)]=(seed,gpu);save()
  while state['not_run'] and not failed:
   # Isaac renderer may establish contexts on both devices. Drain the entire
   # previous pair before checking global occupancy and scheduling the next.
   apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True)
   assert not apps.strip(),'Devices occupied; no new simulation started'
   for gpu in [0,1]:
    if state['not_run']:schedule(gpu)
   for future in concurrent.futures.as_completed(list(futures)):
    seed,gpu=futures.pop(future);state['active'].pop(str(gpu))
    try:item=future.result()
    except Exception:item=dict(seed=seed,physical_gpu=gpu,outcome='runner_error',error=traceback.format_exc(),terminal_missing=(D/f'seed{seed}-native-entry').exists() and not (D/f'seed{seed}-native-entry/report.json').exists())
    state['entries'].append(item)
    failed |= item['outcome']!='nav_push_stow_nav_target_stable' or item.get('returncode')!=0
    state['status']='draining_after_failure' if failed else 'running'
    save()
 state['status']='stopped_failure' if failed else 'development_screen_complete'
except Exception:state.update(status='runner_error',error=traceback.format_exc())
finally:
 state['successes']=sum(x['outcome']=='nav_push_stow_nav_target_stable' and x.get('returncode')==0 for x in state['entries']);state['missing_terminals']=sum(x['terminal_missing'] for x in state['entries']);save()
