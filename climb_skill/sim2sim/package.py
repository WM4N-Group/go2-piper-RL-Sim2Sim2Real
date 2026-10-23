"""制作无需Isaac/历史目录/训练源码的独立回放ZIP。"""
from pathlib import Path
import hashlib
import zipfile
from bridge import ROOT, robot_directory


def package():
    files = {str(p.relative_to(ROOT)): p for p in ROOT.rglob('*') if p.is_file()
             and not any(part in ('outputs', '__pycache__', 'dist') for part in p.relative_to(ROOT).parts)
             and p.name != 'SHA256SUMS'}
    files.update({'robot/'+str(p.relative_to(robot_directory())): p for p in robot_directory().rglob('*') if p.is_file()})
    files['LICENSE'] = ROOT.parents[1]/'LICENSE'
    manifest = ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+name+'\n' for name,p in sorted(files.items()))
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    dest=output/'climb_v1_900_mujoco.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,p in sorted(files.items()):archive.write(p, 'climb_v1_900/'+name)
        archive.writestr('climb_v1_900/SHA256SUMS',manifest)
    print(dest)
    print('SHA256',hashlib.sha256(dest.read_bytes()).hexdigest())
    return dest


if __name__=='__main__': package()
