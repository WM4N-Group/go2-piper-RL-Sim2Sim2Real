"""Run the two preregistered native groups serially in isolated processes."""
import json,subprocess,sys
from pathlib import Path
frozen=Path.cwd();protocol=json.loads((frozen/'PROTOCOL.json').read_text())
checkpoint='/mnt/miaojigui/zyh/climb_skill/outputs/V1/train-20261019-110256-00f00wtw/model_900.pt'
for group in protocol['groups']:
    name='formal-v3-isaac-'+group['name'];output=frozen.parent/name
    command=[sys.executable,str(frozen/'acceptance/isaac_reference.py'),'--headless','--device','cuda:0',
        '--checkpoint',checkpoint,'--snapshot',str(Path(checkpoint).parent/'source'),
        '--output',str(output),'--exit-control','--episodes','32','--num-envs','32','--seed',str(group['rng_seed'])]
    with (frozen.parent/(name+'.log')).open('w') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    print(json.dumps(dict(group=name,exit_code=result.returncode)),flush=True)
    if result.returncode:raise SystemExit(result.returncode)
