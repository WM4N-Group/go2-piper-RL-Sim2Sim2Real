"""Train the single-box GO2-PIPER skill in the active Isaac Lab Conda environment."""

import argparse
from collections import Counter, deque
from dataclasses import asdict
import json
from pathlib import Path
import time

from climb_skill.tasks.direct.climb_skill.task_parameters import PPOConfig, TaskConfig, configuration, load_config
from climb_skill.utils.runtime import load_checkpoint, output_directory, provenance, write_json
from climb_skill.utils.checkpoint_video import record_checkpoint, checkpoint_due


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="Isaac-Climb-Skill-Go2-Piper-v0")
    parser.add_argument("--config", type=Path, help="JSON with task and ppo sections")
    parser.add_argument("--num-envs", type=int)
    parser.add_argument("--iterations", type=int, help="Additional iterations, including when resuming")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--resume", type=Path, help="Trusted checkpoint; restores all three optimizers")
    parser.add_argument("--output", type=Path, help="New directory; existing results are never overwritten")
    parser.add_argument("--save-interval", type=int, help="Save every N PPO iterations, and always at the end")
    parser.add_argument("--checkpoint-video", action=argparse.BooleanOptionalAction, default=True,
                        help="Record every saved checkpoint (default on); --no-checkpoint-video disables it")
    parser.add_argument("--video-seconds", type=float, default=24.)
    parser.add_argument("--video-episodes", type=int, default=1, help="Complete evaluation episodes per height per checkpoint")
    parser.add_argument("--video-seed", type=int, default=42001, help="Fixed development seed, not a held-out acceptance seed")
    parser.add_argument("--video-timeout", type=float, default=900., help="Maximum wall seconds per recording; failure stops training with checkpoint retained")
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.video_seconds <= 0 or args.video_episodes < 1 or args.video_timeout <= 0:
        parser.error("Video duration, episode count and timeout must be positive")
    # 续训从checkpoint完整配置恢复；若再给JSON，要求与checkpoint一致，不能借resume暗换奖励。
    if args.resume:
        saved = load_checkpoint(args.resume)
        task = TaskConfig(**saved["configuration"]["task"])
        ppo_cfg = PPOConfig(**saved["configuration"]["ppo"])
        if args.config:
            supplied_task, supplied_ppo = load_config(args.config)
            if asdict(supplied_task) != asdict(task) or asdict(supplied_ppo) != asdict(ppo_cfg):
                parser.error("Resume configuration must match checkpoint; use CLI count/seed overrides")
    else:
        task, ppo_cfg = load_config(args.config)
    # Resumed runs use the current cadence unless explicitly overridden.
    if args.resume and args.save_interval is None:
        ppo_cfg.save_interval = 100
    for name in ("num_envs", "seed"):
        if getattr(args, name) is not None:
            setattr(task, name, getattr(args, name))
    if args.iterations is not None:
        ppo_cfg.iterations = args.iterations
    if args.save_interval is not None:
        ppo_cfg.save_interval = args.save_interval
    task.validate()
    ppo_cfg.validate()
    if not ppo_cfg.amp:
        parser.error("Current CLIMB requires ppo.amp configuration")
    from climb_skill.learning.amp import AMPConfig, load_pairs
    load_pairs(AMPConfig(**ppo_cfg.amp).dataset, "cpu")  # 启动Isaac前先检查数据
    output = output_directory(args.output, "train")
    print(f"CLIMB output: {output}", flush=True)
    app = AppLauncher(args).app
    env = None
    status = {"status": "failed", "kind": "training", "output": str(output)}
    try:
        import torch
        import gymnasium as gym
        import climb_skill.tasks
        from climb_skill.tasks.direct.climb_skill.climb_skill_env_cfg import make_env_config
        from climb_skill.learning.actor_critic import ClimbActorCritic
        from climb_skill.learning.ppo import PPO
        torch.set_num_threads(4)
        env = gym.make(args.task, cfg=make_env_config(task, args.device)).unwrapped
        # 保存补齐默认值、应用CLI后的完整生效配置；只看JSON不足以知道这次训练的全部参数。
        config = configuration(task, ppo_cfg)
        provenance(output, config, args.resume)
        model = ClimbActorCritic(ppo_cfg.initial_std).to(env.device)
        amp = None
        from climb_skill.learning.amp import AMP, AMPConfig
        amp = AMP(AMPConfig(**ppo_cfg.amp), env.device)
        write_json(output / "amp_dataset.json", {"sha256": amp.dataset_sha256, **amp.manifest})
        algorithm = PPO(model, ppo_cfg, amp=amp)
        if args.resume:
            algorithm.load(args.resume)
        obs = env.reset()[0]["policy"]
        if args.resume and "curriculum_levels" in saved and len(saved["curriculum_levels"]) == task.num_envs:
            env.levels[:] = torch.tensor(saved["curriculum_levels"], device=env.device)
            obs = env.reset()[0]["policy"]
        recent_episodes = deque(maxlen=1000)
        with (output / "metrics.jsonl").open("w") as metrics, (output / "episodes.jsonl").open("w") as episodes:
            target_iteration = algorithm.iteration + ppo_cfg.iterations
            while algorithm.iteration < target_iteration:
                start = time.monotonic()
                # 一次iteration=采24步并行轨迹，再做5×4次主更新与5×4次辅助更新；不是一个完整回合。
                obs, batch, history, records, reward = algorithm.collect(env, obs)
                logs = algorithm.update(batch, history)
                logs.update(algorithm.rollout_diagnostics)
                recent_episodes.extend(records)
                recent_success = (sum(r["success"] for r in recent_episodes) / len(recent_episodes)
                                  if recent_episodes else None)
                logs.update(iteration=algorithm.iteration, mean_step_reward=reward,
                            history_rollout=history, completed_episodes=len(records),
                            successful_episodes=sum(x["success"] for x in records),
                            mean_box_height=float(env.heights.mean()), seconds=time.monotonic() - start)
                logs.update(recent_episode_count=len(recent_episodes), recent_success_rate=recent_success,
                            recent_failure_reasons=dict(Counter(r["reason"] for r in recent_episodes if not r["success"])),
                            curriculum_counts=torch.bincount(env.levels, minlength=task.curriculum_levels).tolist())
                metrics.write(json.dumps(logs, allow_nan=False) + "\n")
                metrics.flush()
                for record in records:
                    episodes.write(json.dumps({"iteration": algorithm.iteration, **record}, allow_nan=False) + "\n")
                episodes.flush()
                print(f"iteration {algorithm.iteration}: reward={reward:.4f}, "
                      f"success={logs['successful_episodes']}/{len(records)}, "
                      f"recent={recent_success if recent_success is not None else 'no completed episodes'}, "
                      f"height={logs['mean_box_height']:.3f}, {logs['seconds']:.2f}s", flush=True)
                if checkpoint_due(algorithm.iteration, target_iteration, ppo_cfg.save_interval):
                    path = output / f"model_{algorithm.iteration}.pt"
                    algorithm.save(path, config, curriculum_levels=env.levels.tolist())
                    print(f"Checkpoint: {path}", flush=True)
                    status["checkpoint"] = str(path)
                    if args.checkpoint_video:
                        # Separate process preserves training RNG, rollout, curriculum and physics state.
                        # Training waits here, but its CUDA allocation stays resident.
                        print(f"Recording checkpoint {algorithm.iteration}; training is waiting", flush=True)
                        # 录像选择当前并行环境课程等级的下中位数，对应实际课程高度，不是均值或强制最终30cm。
                        middle_level = float(env.levels.float().median())
                        current_height = task.curriculum_min_height + middle_level / (task.curriculum_levels - 1) * (
                            task.box_height - task.curriculum_min_height) if task.curriculum else task.box_height
                        evaluation = record_checkpoint(
                            path, device=args.device, task=args.task, seconds=args.video_seconds,
                            episodes=args.video_episodes, seed=args.video_seed, timeout=args.video_timeout,
                            box_height=current_height)
                        print(f"Curriculum video ({current_height:.3f}m): {evaluation['video']}; success "
                              f"{evaluation['successful_episodes']}/{args.video_episodes}", flush=True)
        status.update(status="complete", iterations=algorithm.iteration,
                      checkpoint=str(path), note="Training execution completed; this is not task acceptance")
    except BaseException as exc:
        status["error"] = repr(exc)
        raise
    finally:
        write_json(output / "status.json", status)
        if env is not None:
            env.close()
        app.close()


if __name__ == "__main__":
    main()

