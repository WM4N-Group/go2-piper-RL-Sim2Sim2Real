import gymnasium as gym

gym.register(id="Isaac-Nav-Skill2-Go2-Piper-v0",
    entry_point=f"{__name__}.nav_skill2_env:NavSkill2Env",disable_env_checker=True,
    kwargs={"env_cfg_entry_point":f"{__name__}.nav_skill2_env_cfg:NavSkill2EnvCfg"})
