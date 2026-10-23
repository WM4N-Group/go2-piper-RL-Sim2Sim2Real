"""固定WMP提交的六类GO2公开运动片段转换；不旋转关节伪造后退/侧移/转向。"""
import argparse,base64,hashlib,json,urllib.request
from pathlib import Path
import numpy as np
COMMIT='65cf1afd13e4792bce7b9def6f44372ecbb3cdf0'
MODES=('stand','forward','backward','left','right','turn_left','turn_right')
CLIPS=[
 ('go2_forward_0.4mps.txt','48818298b24a808554ce546f24e61c2b106171e433a96f3450d4d240c0eb9b5f'),
 ('go2_backward_0.4mps.txt','c95930eb14fd3dcad02c7a7eda4f27f7ed0114967a8957522f654fc98d08bfc5'),
 ('go2_left_0.5mps.txt','a6819d6226de3d2c40f625553b83f3edd5bd4696417c35d19febe4c9326a5966'),
 ('go2_right_0.5mps.txt','847381f3c597f324c1a277544d9eff9702977055d925646046c32af97fa0b9c0'),
 ('go2_turn_left_0.5radps.txt','ef06673640dd05bf65d2ce68546ac8a74f8f2f79526891a5578e03da8d750267'),
 ('go2_turn_right_0.5radps.txt','540b401bc7ea918aebe9d18a1b451aed9ec5a6586c8d00c15df8c7e902f84b8d')]

def build(source_dir):
 pairs=[];labels=[];sources=[]
 for mode,(name,expected) in enumerate(CLIPS,1):
  raw=(source_dir/name).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError(f'Checksum: {name}')
  data=json.loads(raw);f=np.asarray(data['Frames'],dtype=np.float64)
  if f.ndim!=2 or f.shape[1]!=61 or not np.isfinite(f).all() or data['FrameDuration']!=.02:raise ValueError('61D/50Hz contract')
  toes=f[:,19:31].reshape(-1,4,3)
  if not np.all(np.sign(toes[:,:,:2].mean(0))==[[1,1],[1,-1],[-1,1],[-1,-1]]):raise ValueError('Foot order')
  axis=31 if mode<=2 else 32 if mode<=4 else 36
  sign=1 if mode%2 else -1
  # 保留真实运动段，连续相邻两帧都合格；不跨缺口、循环端点或改变片段速度。
  moving=(sign*f[:,axis]>.2)&(sign*f[:,axis]<.85)
  keep=moving[:-1]&moving[1:]
  state=np.concatenate((f[:,7:19],f[:,31:49]),axis=1)
  p=np.concatenate((state[:-1],state[1:]),axis=1)[keep]
  if len(p)<32:raise ValueError(f'Insufficient data: {name}')
  pairs.extend(p.tolist());labels.extend([mode]*len(p))
  sources.append(dict(mode=MODES[mode],source_url=f'https://github.com/haozhang04/wmp_go1/blob/{COMMIT}/datasets/go2_motion/{name}',source_sha256=expected,original_frames=len(f),retained_transition_indices=np.flatnonzero(keep).tolist(),mean_body_vx_vy_wz=f[:,[31,32,36]].mean(0).tolist()))
 return dict(format='nav_amp_modes_v1',dt=.02,joint_order=[f'{l}_{j}_joint' for l in ('FL','FR','RL','RR') for j in ('hip','thigh','calf')],feature_order=['joint_position_12','body_linear_velocity_3','body_angular_velocity_3','joint_velocity_12'],modes=MODES,source_commit=COMMIT,sources=sources,limitations='Bare GO2 public clips, not Piper demonstrations. No force labels. Mixed/diagonal commands use dominant translation reference with reduced weight; no exact mixed-motion demonstration.',pairs=pairs,labels=labels)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--download',action='store_true');a=p.parse_args()
 if a.download:
  a.source_dir.mkdir(parents=True,exist_ok=True)
  tree=json.load(urllib.request.urlopen(f'https://api.github.com/repos/haozhang04/wmp_go1/git/trees/{COMMIT}?recursive=1',timeout=30))['tree']
  for name,sha in CLIPS:
   dest=a.source_dir/name
   if dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest()==sha:continue
   item=next(x for x in tree if x['path']=='datasets/go2_motion/'+name)
   raw=base64.b64decode(json.load(urllib.request.urlopen(item['url'],timeout=30))['content'])
   if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Download hash mismatch')
   dest.write_bytes(raw)
 data=build(a.source_dir);a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
 print({mode:data['labels'].count(i) for i,mode in enumerate(MODES)},flush=True)
if __name__=='__main__':main()
