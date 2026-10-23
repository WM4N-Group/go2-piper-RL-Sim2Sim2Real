"""列出本包Gym注册信息；无需启动Isaac或占用GPU。"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source/nav_skill2'))
import gymnasium as gym
import nav_skill2.tasks
for name,spec in gym.registry.items():
    if name.startswith('Isaac-Nav-Skill2-'):
        print(name)
        print('  environment:',spec.entry_point)
        print('  config:',spec.kwargs['env_cfg_entry_point'])
