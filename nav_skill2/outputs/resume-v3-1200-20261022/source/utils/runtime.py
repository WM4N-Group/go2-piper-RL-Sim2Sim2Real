"""产物、配置快照与哈希。与旧技能没有运行依赖。"""
from pathlib import Path
import hashlib,json,os,tempfile,time,subprocess

def project_root():return Path(__file__).resolve().parents[4]
def write_json(path,data):Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def dataset_path():return Path(os.environ.get('NAV_AMP_DATASET',project_root()/'data/amp_pairs.json'))
def output_directory(path,prefix):
    if path:
        result=Path(path).resolve();result.mkdir(parents=True,exist_ok=False);return result
    root=Path(os.environ.get('NAV_OUTPUT_ROOT',project_root()/'outputs'));root.mkdir(parents=True,exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f'{prefix}-{time.strftime("%Y%m%d-%H%M%S")}-',dir=root))

def provenance(output,config,robot_path):
    import shutil,sys,importlib.metadata
    src=project_root()/'source/nav_skill2/nav_skill2';dst=output/'source'
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(project_root()/'scripts',output/'scripts',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    write_json(output/'config.json',config)
    hashes={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*.py')}
    asset=Path(robot_path)
    for p in asset.parent.rglob('*.usd'):hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    hashes[str(dataset_path())]=hashlib.sha256(dataset_path().read_bytes()).hexdigest()
    versions={n:importlib.metadata.version(n) for n in ['torch','isaaclab','isaacsim','numpy','gymnasium']}
    write_json(output/'run.json',dict(python=sys.executable,argv=sys.argv,versions=versions,robot_usd=str(asset),hashes=hashes,note='Training artifacts are not acceptance evidence'))

def load_checkpoint(path,device='cpu'):
    import torch
    # 项目自己产生且可信的checkpoint包含优化器和NumPy RNG，不加载陌生权重。
    return torch.load(path,map_location=device,weights_only=False)
