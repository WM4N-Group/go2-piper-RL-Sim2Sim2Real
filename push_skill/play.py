"""单环境 Isaac Lab 推箱回放。保留 v212 双模型和原安全门禁，不需要训练。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'runtime'
# 优先使用本技能配套源码，不导入 Nav 或历史项目的 editable 安装。
sys.path[:0] = [str(RUNTIME / 'source/LeggedManip_Lab'), str(ROOT / 'geometry')]
os.environ['PIPER_GEOMETRY_ROOT'] = str(ROOT / 'geometry')
os.environ['PIPER_HANDOFF_ROOT'] = str(ROOT)
os.environ['PIPER_LEG_CHECKPOINT'] = str(ROOT / 'weights/model_199.pt')
os.environ['PIPER_SOURCE_ROOT'] = str(RUNTIME)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', action='store_true', help='录制完整回合；不会在10秒处截断')
    parser.add_argument('--video-fps', type=int, choices=(5, 10, 25), default=25)
    parser.add_argument('--output', type=Path, help='新目录；默认 outputs/play-时间戳')
    parser.add_argument('--arm-speed', type=float, default=1.5, help='自由空间入场倍率，1恢复原速；接触后不提速')
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if not 1 <= args.arm_speed <= 2:
        parser.error('--arm-speed must be in [1, 2]')
    args.enable_cameras = args.video
    output = (args.output or ROOT / 'outputs' / time.strftime('play-%Y%m%d-%H%M%S')).resolve()
    output.mkdir(parents=True, exist_ok=False)
    expected = {'model_199.pt':'b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721',
                'model_255.pt':'4d1a4616928b4d06002285e870a1d6dd114e27b8cafcdd9a41dbdae1aceed419'}
    for name, value in expected.items():
        if sha(ROOT / 'weights' / name) != value:
            raise ValueError(f'Weight hash mismatch: {name}')
    status = dict(status='incomplete', successful=False, formal_acceptance=False,
                  weights=expected, arm_entry_speed=args.arm_speed, video_fps=args.video_fps,
                  device=args.device, terminal=None)
    began = time.perf_counter()
    app = AppLauncher(args).app
    env = writer = None
    try:
        import torch
        import imageio.v2 as imageio
        from isaaclab.envs import ManagerBasedRLEnv
        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
        from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.config.go2_piper.box_env_cfg import Go2PiperBoxPushTrackingEnvCfg_PLAY
        from control import configure
        from policy import actor_from_state_dict
        from startup import settle, frame, result_card
        torch.set_num_threads(4)
        cfg = Go2PiperBoxPushTrackingEnvCfg_PLAY()
        configure(cfg)
        cfg.scene.num_envs = 1
        cfg.scene.robot.spawn.usd_path = str(Path(os.environ.get('CLIMB_ROBOT_USD', ROOT.parent/'asset/go2_piper/go2_piper.usd')).resolve())
        cfg.seed = 3701
        cfg.sim.device = args.device
        cfg.episode_length_s = 48.
        cfg.play_entry_speed = args.arm_speed
        cfg.viewer.resolution = (640, 480)
        stride = 50 // args.video_fps
        cfg.sim.render_interval = cfg.decimation * stride if args.video else cfg.decimation
        cfg.events.reset_robot_joints.params.update(position_range=(1., 1.), velocity_range=(0., 0.))
        x, y, z = cfg.scene.robot.init_state.pos
        cfg.scene.robot.init_state.pos = (x - .08, y, z)
        base = ManagerBasedRLEnv(cfg=cfg, render_mode='rgb_array' if args.video else None)
        env = RslRlVecEnvWrapper(base, clip_actions=None)
        robot = base.scene['robot']
        terminal = {}
        original = base.recorder_manager.record_pre_reset

        def record_terminal(ids, *positional, **keywords):
            if ids.numel():
                flags = {n:bool(base.termination_manager.get_term(n)[0]) for n in base.termination_manager.active_terms}
                terminal.update(seconds=float(base.episode_length_buf[0] * base.step_dt),
                                flags=flags, torque_ratio=float((robot.data.applied_torque[0].abs()/robot.data.joint_effort_limits[0].clamp_min(1e-6)).max()), box_position=(base.scene['box'].data.root_pos_w[0] - base.scene.env_origins[0]).tolist(),
                                base_position=(robot.data.root_pos_w[0]-base.scene.env_origins[0]).tolist())
                if writer:
                    writer.append_data(frame(base.render(), terminal['seconds']))
            return original(ids, *positional, **keywords)

        # 不调用额外 reset；与已成功的 v212 初始化顺序一致。
        settle(base, output / 'startup-report.json')
        base.recorder_manager.record_pre_reset = record_terminal
        observation = env.get_observations()
        def load(name):
            return actor_from_state_dict(torch.load(ROOT / 'weights' / name, map_location='cpu', weights_only=False)['actor_state_dict'], device=args.device)
        arm_actor, leg_actor = load('model_255.pt'), load('model_199.pt')
        # 原冻结腿 hook 的等价展开：输入相同226维，腿12维取199，余7维取255。
        if args.video:
            writer = imageio.get_writer(str(output/'push.mp4'), fps=args.video_fps, codec='libx264', macro_block_size=2)
            origin = base.scene.env_origins[0].cpu().numpy()
            base.sim.set_camera_view(eye=origin+[.7,3.2,1.5], target=origin+[.9,0.,.3])
        maximum_ratio = torch.zeros((), device=base.device)
        initial_box = (base.scene['box'].data.root_pos_w[0]-base.scene.env_origins[0]).tolist()
        running_began = time.perf_counter()
        with torch.inference_mode():
            for step in range(round(48 / base.step_dt) + 1):
                if writer and step % stride == 0:
                    writer.append_data(frame(base.render(), step * base.step_dt))
                inputs = torch.cat([observation['policy'], observation['box']], dim=-1)
                actions = torch.cat([leg_actor(inputs), arm_actor(inputs)[:,12:]], dim=-1)
                observation, _, done, _ = env.step(actions)
                maximum_ratio = torch.maximum(maximum_ratio, (robot.data.applied_torque.abs()/robot.data.joint_effort_limits.clamp_min(1e-6)).max())
                if (step+1) % 200 == 0:
                    c = base.action_manager.get_term('joint_pos').controller
                    print(f"t={(step+1)*base.step_dt:.2f}s, path={int(c.safe_approach_index[0])}, face_ready={bool(c.approach_face_ready[0])}", flush=True)
                if bool(done[0]):
                    flags = terminal['flags']
                    success = flags['box_settled'] and not any(v for n,v in flags.items() if n not in ('box_settled','time_out'))
                    status.update(status='complete', successful=success, terminal=terminal)
                    break
        seconds = terminal.get('seconds', (step+1)*base.step_dt)
        status.update(initial_box=initial_box, max_control_sample_torque_ratio=max(float(maximum_ratio), terminal.get('torque_ratio', 0.)),
                      simulation_seconds=seconds, playback_wall_seconds=time.perf_counter()-running_began,
                      success_definition='original box_settled + no safety failures; error<0.12m, speed<0.08m/s for0.5s; no retract guarantee')
        if terminal:
            displacement = [b-a for a,b in zip(initial_box, terminal['box_position'])]
            status['box_displacement'] = displacement
            status['goal_error_xy_m'] = ((displacement[0]-.6)**2+displacement[1]**2)**.5
        if writer:
            reasons = {n:int(v) for n,v in terminal.get('flags', {}).items()}
            for _ in range(args.video_fps * 2):
                writer.append_data(result_card(seconds, [int(status['status']=='complete')], [int(status['successful'])], reasons))
        print(json.dumps(status, ensure_ascii=False), flush=True)
    except BaseException as exc:
        import traceback
        traceback.print_exc()
        status.update(status='error', error=repr(exc))
        raise
    finally:
        if writer:
            writer.close()
        status['wall_seconds_including_startup'] = time.perf_counter()-began
        (output/'report.json').write_text(json.dumps(status, indent=2, ensure_ascii=False)+'\n')
        if env is not None:
            env.close()
        app.close()
    return 0 if status['successful'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
