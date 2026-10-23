"""本地 Go2Piper WBC train 入口；调用本目录上游脚本。"""
import os
from pathlib import Path
import runpy
import sys
ROOT = Path(__file__).resolve().parent
os.environ.setdefault('CLIMB_ROBOT_USD', str(ROOT.parent/'asset/go2_piper/go2_piper.usd'))
sys.path[:0] = [str(ROOT/'source/LeggedManip_Lab'), str(ROOT/'scripts/rsl_rl')]
os.chdir(ROOT)
if '--task' not in sys.argv:
    sys.argv += ['--task', 'GO2-PIPER-WBC']
runpy.run_path(str(ROOT/'scripts/rsl_rl/train.py'), run_name='__main__')
