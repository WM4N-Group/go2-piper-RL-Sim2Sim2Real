"""Read-only provenance check for the already executed native candidate."""
from pathlib import Path
import hashlib,json,sys,platform
import importlib.metadata

root=Path('/mnt/miaojigui/zyh/climb_skill/sim2sim_acceptance_v1_900/eval-frozen-v3')
protocol=json.loads((root/'PROTOCOL.json').read_text())
files={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in protocol['files']}
assert files==protocol['files']
versions={}
for name in ('torch','numpy','scipy','isaacsim','isaaclab'):
    try:versions[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:versions[name]='no distribution metadata'
result=dict(frozen_files_unchanged=True,files=files,manifest_sha256=protocol['manifest_sha256'],
    python=sys.version,platform=platform.platform(),versions=versions,executable=sys.executable,
    evaluation_scope='Existing native runtime used for complete physical task rollouts; imports are not the validation witness.')
(root.parent/'REMOTE_PROVENANCE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'}))
