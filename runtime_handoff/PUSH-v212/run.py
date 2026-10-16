from pathlib import Path
import hashlib,json,os,subprocess,sys,time
B=Path(__file__).resolve().parent;T=B/'train';plan=json.loads((B/'plan.json').read_text());v=plan['variants'][int(sys.argv[1])];gpu=v['gpu'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for rel,h in plan['source_hashes'].items():assert sha(T/rel)==h,rel
assert sha(Path(v['checkpoint']))==v['checkpoint_sha256']
uuid=subprocess.check_output(['nvidia-smi',f'--id={gpu}','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
while True:
 rows=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],text=True).splitlines()
 blockers=[]
 for pid in sorted(set(row.split(',')[0].strip() for row in rows if uuid in row)):
  try:
   import re
   command=Path('/proc',pid,'cmdline').read_bytes().replace(b'\0',b' ').decode()
   variables=Path('/proc',pid,'environ').read_bytes().split(b'\0')
   visible=next((x.split(b'=',1)[1].decode() for x in variables if x.startswith(b'CUDA_VISIBLE_DEVICES=')),None)
   match=re.search(r'--device(?:=| )cuda:(\d+)',command)
   if match:
    logical=int(match.group(1));mapping=visible.split(',') if visible is not None else ['0','1']
    if logical<len(mapping) and mapping[logical].isdigit() and int(mapping[logical])!=gpu:continue
  except (FileNotFoundError,ProcessLookupError):continue
  blockers.append(pid)
 free=int(subprocess.check_output(['nvidia-smi',f'--id={gpu}','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True))
 if not blockers and free>16000:break
 (B/f'gpu{gpu}-queue.json').write_text(json.dumps(dict(blockers=blockers,time=time.time(),free_mib=free),indent=2)+'\n');time.sleep(30)
def evaluate(seed,num_envs):
 out=B/(v['label']+f'-used{seed}-{num_envs}env-48s');out.mkdir(exist_ok=False)
 cmd=json.loads((B.parent/'push-warmstart-train-v205/eval-trained8051-used3701-8env-48s/plan.json').read_text())['command'].copy()
 cmd[cmd.index('--seed')+1]=str(seed);cmd[cmd.index('--num_envs')+1]=str(num_envs)
 cmd[1]=str(T/'scripts/evaluate_residual_push.py');cmd[cmd.index('--checkpoint')+1]=v['checkpoint'];cmd[cmd.index('--output-json')+1]=str(out/'report.json')
 (out/'plan.json').write_text(json.dumps(dict(command=cmd,source_plan_sha256=sha(B/'plan.json'),checkpoint_sha256=v['checkpoint_sha256'],scope=plan['scope']),indent=2)+'\n')
 env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(gpu),PYTHONPATH=str(T/'source/LeggedManip_Lab')+':'+plan['geometry_root'],PIPER_SOURCE_ROOT=str(T),PYTHONUNBUFFERED='1')
 with (out/'run.log').open('w') as f:
  p=subprocess.Popen(cmd,cwd=T,env=env,stdout=f,stderr=subprocess.STDOUT);(out/'launch.json').write_text(json.dumps(dict(pid=p.pid,gpu=gpu,launcher=os.getpid(),time=time.time()),indent=2)+'\n');rc=p.wait()
 state=dict(returncode=rc,valid=False,end=time.time())
 if rc==0 and (out/'report.json').exists():
  r=json.loads((out/'report.json').read_text());state.update({k:r[k] for k in ('successful_episodes','completed_episodes','incomplete_episodes','termination_reasons','physical_safety_control_samples')});state['valid']=r['completed_episodes']==num_envs and r['incomplete_episodes']==0;state['report_sha256']=sha(out/'report.json');state['terminals']=[{k:s[k] for k in ('env_id','elapsed_seconds','safe_approach_index','box_displacement','box_goal_error','settle_duration','termination_flags')} for s in r['terminal_states']];state['physical_sample_count_matches']=r['physical_safety_control_samples']['samples']==sum(round(s['elapsed_seconds']/.02)+1 for s in r['terminal_states'])
 (out/'result.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))
 
 return state
try:
 state=evaluate(3701,8)
 safety=sum(count for name,count in state.get('termination_reasons',{}).items() if name not in ('time_out','box_settled'))
 if state['valid'] and state['successful_episodes']>=7 and safety==0:
  (B/(v['label']+'-state.json')).write_text(json.dumps(dict(phase='expanded_used2701_diagnostic',time=time.time()),indent=2)+'\n')
  state=evaluate(2701,32)
  phase='completed_diagnostic' if state['valid'] else 'failed'
 else:phase='rejected_before_expansion'
 (B/(v['label']+'-state.json')).write_text(json.dumps(dict(phase=phase,time=time.time(),result=state),indent=2)+'\n')
except Exception as e:
 (B/(v['label']+'-state.json')).write_text(json.dumps(dict(phase='failed',error=str(e),time=time.time()),indent=2)+'\n')
 raise
