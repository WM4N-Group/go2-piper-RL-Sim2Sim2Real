from pathlib import Path
import sys,runpy
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'source/nav_skill2'))
if __name__=='__main__':runpy.run_path(str(root/'scripts/play.py'),run_name='__main__')
