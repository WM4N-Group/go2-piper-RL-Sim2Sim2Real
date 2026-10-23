"""Isaac Lab task registration. Configuration is resolved after AppLauncher starts."""
import gymnasium as gym

gym.register(
    id="Isaac-Climb-Skill-Go2-Piper-v0",
    entry_point=f"{__name__}.climb_skill_env:ClimbSkillEnv",
    disable_env_checker=True,
    kwargs={"env_cfg_entry_point": f"{__name__}.climb_skill_env_cfg:ClimbSkillEnvCfg"},
)
