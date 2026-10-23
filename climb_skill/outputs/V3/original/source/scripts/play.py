"""Evaluate complete ground-start episodes on the fixed target box; optional headless MP4."""

import argparse
from pathlib import Path

from climb_skill.tasks.direct.climb_skill.task_parameters import PPOConfig, TaskConfig, configuration
from climb_skill.utils.runtime import load_checkpoint, output_directory, provenance, sha256, write_json


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="Isaac-Climb-Skill-Go2-Piper-v0")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--num-envs", type=int, default=8)
    parser.add_argument("--episodes", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42001)
    parser.add_argument("--steps", type=int, help="Optional debug cap; unfinished episodes are reported missing")
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--video-seconds", type=float, default=24.)
    parser.add_argument("--box-height", type=float, help="Development evaluation at a specified height; default is the target height")
    parser.add_argument("--output", type=Path)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if not 1 <= args.num_envs <= args.episodes:
        parser.error("Require 1 <= num-envs <= episodes")
    if args.video_seconds <= 0 or (args.steps is not None and args.steps < 1):
        parser.error("Video duration and step limit must be positive")
    saved = load_checkpoint(args.checkpoint)
    task = TaskConfig(**saved["configuration"]["task"])
    target_height = task.box_height
    if args.box_height is not None:
        if not 0 < args.box_height <= target_height:
            parser.error("Evaluation box height must be positive and at most the checkpoint target height")
        task.box_height = args.box_height
        task.curriculum_min_height = min(task.curriculum_min_height, task.box_height)
    # 评估固定箱高、关闭升降级；保留原checkpoint的随机化开关，默认仍有质量／摩擦／PD扰动。
    task.num_envs, task.seed, task.curriculum = args.num_envs, args.seed, False
    task.validate()
    ppo_cfg = PPOConfig(**saved["configuration"]["ppo"])
    if args.video:
        args.enable_cameras = True
    output = output_directory(args.output, "eval")
    print(f"CLIMB evaluation: {output}", flush=True)
    app = AppLauncher(args).app
    env = None
    writer = None
    records = []
    status = {"status": "failed", "requested_episodes": args.episodes, "seed": args.seed,
              "formal_acceptance": False, "checkpoint_sha256": sha256(args.checkpoint)}
    try:
        import torch
        import imageio.v2 as imageio
        import gymnasium as gym
        import climb_skill.tasks
        from climb_skill.tasks.direct.climb_skill.climb_skill_env_cfg import make_env_config
        from climb_skill.learning.actor_critic import ClimbActorCritic
        torch.set_num_threads(4)
        env = gym.make(args.task, cfg=make_env_config(task, args.device),
                       render_mode="rgb_array" if args.video else None).unwrapped
        provenance(output, configuration(task, ppo_cfg), args.checkpoint)
        model = ClimbActorCritic(ppo_cfg.initial_std).to(env.device)
        model.load_state_dict(saved["model"])
        model.eval()
        if task.approach_quality_enabled:
            from climb_skill.tasks.direct.climb_skill.mdp.approach_quality import playback_reference
            env.approach_quality.reference = playback_reference(ppo_cfg.amp, saved['amp']['dataset_sha256'], env.device)
        obs = env.reset()[0]["policy"]
        quotas = [args.episodes // args.num_envs + (i < args.episodes % args.num_envs) for i in range(args.num_envs)]
        counts = [0] * args.num_envs
        limit = args.steps or (max(quotas) * (env.max_episode_length + 1))
        video_stride = 2
        video_frames = round(args.video_seconds / (video_stride * env.step_dt))
        frames = 0
        if args.video:
            writer = imageio.get_writer(output / "climb.mp4", fps=1 / (video_stride * env.step_dt),
                                        codec="libx264", macro_block_size=2)
            limit = max(limit, video_frames * video_stride) if args.steps is None else limit
        max_arm_command_error = 0.
        with torch.no_grad():
            for step in range(limit):
                # 回放使用history网络的确定性均值，不采高斯探索噪声；与训练动作效果可以不同。
                actions = model(obs)
                if actions.shape != (args.num_envs, 18) or torch.count_nonzero(actions[:, 12:]):
                    raise RuntimeError("Actor violated the 18-axis/zero arm residual contract")
                next_obs, reward, terminated, truncated, info = env.step(actions)
                obs = next_obs["policy"]
                max_arm_command_error = max(max_arm_command_error, float((env.targets[:, 12:] - env.reference[:, 12:]).abs().max()))
                for record in info.get("episode_records", []):
                    i = record["env"]
                    if counts[i] < quotas[i]:
                        records.append({"episode": counts[i], **record})
                        counts[i] += 1
                        print(f"episode {len(records)}/{args.episodes}: env={i} {record['reason']}, "
                              f"{record['seconds']:.2f}s, box={record['box_height']:.2f}m", flush=True)
                # 每2个控制步写一帧，即25fps；视频继续到规定时长，成功后可自动reset并出现后续回合。
                if writer and step % video_stride == 0 and frames < video_frames:
                    writer.append_data(env.render())
                    frames += 1
                if len(records) == args.episodes and (not writer or frames >= video_frames):
                    break
        status.update(status="complete" if len(records) == args.episodes else "incomplete",
                      completed_episodes=len(records), successful_episodes=sum(r["success"] for r in records),
                      missing_episodes=args.episodes - len(records), episodes=records,
                      box_height=task.box_height, arm_pose=list(task.arm_pose),
                      training_target_height=target_height,
                      box_length=task.box_length, finish_x=task.finish_x,
                      success_definition="four feet above safe top beyond finish for 0.3s with recent real loading; current support and posture checks",
                      forward_traversal_contract={
                          "heading_required": task.traversal_heading_tolerance > 0,
                          "target_yaw_rad": 0.,
                          "heading_tolerance_rad": task.traversal_heading_tolerance,
                          "lateral_tolerance_m": task.traversal_lateral_tolerance,
                          "confirmation_seconds": task.traversal_seconds,
                          "finish_x": task.finish_x,
                          "route_goal_x": task.route_goal_x},
                      max_arm_command_error_rad=max_arm_command_error, video_frames=frames,
                      policy_branch="history", ground_start=True)
    except BaseException as exc:
        status.update(error=repr(exc), completed_episodes=len(records), episodes=records,
                      missing_episodes=args.episodes - len(records))
        raise
    finally:
        if writer:
            writer.close()
        if (output / "climb.mp4").exists():
            status["video_sha256"] = sha256(output / "climb.mp4")
        write_json(output / "report.json", status)
        if env is not None:
            env.close()
        app.close()
    print(f"Success {status['successful_episodes']}/{args.episodes}, missing {status['missing_episodes']}; {output}")
    return 0 if status["missing_episodes"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

