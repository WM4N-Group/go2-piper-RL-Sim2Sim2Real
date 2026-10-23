"""Initial physical standing phase; never gates foot switching during locomotion."""
import torch


def movement_gain(env):
    if env.task.startup_stand_seconds <= 0:
        return torch.ones(env.num_envs, device=env.device)
    return ((env.startup_elapsed - env.startup_release_time)
            / env.task.startup_ramp_seconds).clamp(0., 1.) * env.startup_ready


def standing_transition(elapsed, stable_time, ready, release_time, stable, cfg, dt):
    elapsed = elapsed + dt
    stable_time = torch.where(stable & ~ready, stable_time + dt, torch.zeros_like(stable_time))
    release = ~ready & (elapsed >= cfg.startup_stand_seconds) & (stable_time >= cfg.startup_stable_seconds)
    release_time = torch.where(release, elapsed, release_time)
    ready = ready | release
    failed = ~ready & (elapsed >= cfg.startup_timeout)
    return elapsed, stable_time, ready, release_time, failed


def update_startup(env, feet, forces):
    if env.task.startup_stand_seconds <= 0:
        return torch.zeros(env.num_envs, device=env.device, dtype=torch.bool)
    data = env.robot.data
    # Four real ground contacts are required only for initial standing, never in the climb.
    grounded = ((forces[..., 2] >= env.task.support_force)
        & ((feet[..., 2] - env.task.foot_radius).abs() <= env.task.foot_height_tolerance)).all(-1)
    tilt = torch.acos((-data.projected_gravity_b[:, 2]).clamp(-1., 1.))
    # 仅起步站稳要求四脚承重、总倾角<0.10rad、根速度<0.10m/s、角速度模长<0.30rad/s。
    stable = grounded & (tilt < .10) & (data.root_lin_vel_w.norm(dim=-1) < .10) \
        & (data.root_ang_vel_b.norm(dim=-1) < .30)
    (env.startup_elapsed, env.startup_stable_time, env.startup_ready,
     env.startup_release_time, failed) = standing_transition(
        env.startup_elapsed, env.startup_stable_time, env.startup_ready,
        env.startup_release_time, stable, env.task, env.step_dt)
    return failed
