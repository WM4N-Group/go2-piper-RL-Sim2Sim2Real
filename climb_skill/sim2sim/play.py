"""独立MuJoCo运行V1/900。Windows默认窗口；服务器用--headless --video。"""
import argparse
from datetime import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--box-height', type=float, default=.20)
    parser.add_argument('--seed', type=int, default=42001)
    parser.add_argument('--episodes', type=int, default=1)
    parser.add_argument('--device', default='cpu', help='Actor推理设备；MuJoCo物理始终CPU')
    parser.add_argument('--randomize', action='store_true', help='启用训练范围质量/摩擦/腿PD随机化')
    parser.add_argument('--steps', type=int, help='调试控制步上限；截断不算失败或成功')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not 0 < args.box_height <= .20 or args.episodes<1 or (args.steps is not None and args.steps<1):
        parser.error('高度须在(0,0.20]，回合与steps为正整数')
    if args.headless and sys.platform.startswith('linux'):
        os.environ.setdefault('MUJOCO_GL', 'egl')
    import numpy as np
    import torch
    import mujoco
    from bridge import ClimbBridge, build_model, load_contract, robot_directory, ROOT as SOURCE_ROOT, sha
    torch.set_num_threads(2)
    contract = load_contract()
    cfg = contract['configuration']['task']
    actor = torch.jit.load(str(ROOT/'policy/actor.pt'), map_location=args.device).eval()
    output = args.output or ROOT/'outputs'/datetime.now().strftime('play-%Y%m%d-%H%M%S-%f')
    output = output.resolve(); output.mkdir(parents=True, exist_ok=False)
    print(f'Output: {output}', flush=True)
    report = dict(status='running', formal_acceptance=False, version='V1', iteration=900,
                  checkpoint_sha256=contract['checkpoint_sha256'], actor_sha256=contract['actor_sha256'],
                  requested_episodes=args.episodes, box_height=args.box_height, seed=args.seed,
                  randomization=args.randomize, inference_device=args.device, physics_device='CPU',
                  source_sha256={p.name: sha(p) for p in ROOT.glob('*.py')},
                  robot_sha256={str(p.relative_to(robot_directory())): sha(p) for p in robot_directory().rglob('*') if p.is_file()},
                  versions={n: importlib.metadata.version(n) for n in ('mujoco', 'torch', 'numpy')},
                  task_scope='Original V1 walking ascent, not stationary finish or skill switching',
                  sensor_scope='Analytic oracle height map and exact box height; not camera perception',
                  differences=['MuJoCo contact solver differs from PhysX; single sliding friction approximates dynamic min-combine friction.',
                               'Nominal mass/friction/PD by default; --randomize samples within training ranges, not identical Isaac RNG.',
                               'Motor effort limits are enforced; velocity limits monitored, not a PhysX-equivalent solver hard constraint.',
                               'No stop controller added; success uses original V1 ascent criterion.'],
                  episodes=[])
    (output/'run.json').write_text(json.dumps(vars(args), default=str, indent=2)+'\n')
    writer = renderer = viewer = None
    began = time.perf_counter()
    try:
        for episode in range(args.episodes):
            rng = np.random.default_rng(args.seed+episode)
            friction = min(.6, .75*rng.uniform(*cfg['friction_range'])) if args.randomize else .6
            mass = float(rng.uniform(*cfg['added_mass_range'])) if args.randomize else 0.
            model, spec = build_model(cfg, args.box_height, friction=friction, added_mass=mass)
            sim = ClimbBridge(model, cfg, args.box_height, args.seed+episode, args.randomize)
            # 保存本回合实际加载模型，路径指向包内mesh。
            (output/f'model_{episode:03d}.xml').write_text(spec.to_xml())
            if args.video:
                import imageio.v2 as imageio
                renderer = mujoco.Renderer(model, height=540, width=960)
                writer = imageio.get_writer(output/f'climb_{episode:03d}.mp4', fps=25, codec='libx264', macro_block_size=2)
            if not args.headless:
                import mujoco.viewer
                viewer = mujoco.viewer.launch_passive(model, sim.data)
                viewer.cam.distance = 3.4; viewer.cam.azimuth = 135.; viewer.cam.elevation = -22.
                viewer.cam.lookat[:] = [1.2, 0., .35]
            cam = mujoco.MjvCamera()
            cam.distance = 3.4; cam.azimuth = 135.; cam.elevation = -22.
            cam.lookat[:] = [1.2, 0., .35]
            state, reason = 'running', ''
            trace = {k: [] for k in ('time', 'root_pose', 'joint_position', 'joint_velocity', 'target', 'torque', 'raw_torque')}
            obs = sim.observation()
            start = time.perf_counter()
            for step in range(args.steps or round(cfg['episode_seconds']/sim.dt)):
                if viewer is not None and not viewer.is_running():
                    state, reason = 'incomplete', 'viewer_closed'; break
                with torch.inference_mode():
                    action = actor(torch.from_numpy(obs).unsqueeze(0).to(args.device)).cpu().numpy()[0]
                sim.set_action(action)
                for _ in range(cfg['decimation']):
                    sim.physics_step()
                    trace['time'].append(float(sim.data.time))
                    trace['root_pose'].append(sim.data.qpos[:7].copy())
                    trace['joint_position'].append(sim.data.qpos[sim.qids].copy())
                    trace['joint_velocity'].append(sim.data.qvel[sim.dids].copy())
                    trace['target'].append(sim.targets.copy())
                    trace['torque'].append(sim.applied_torque.copy())
                    trace['raw_torque'].append(sim.raw_torque.copy())
                if not np.isfinite(sim.data.qpos).all() or not np.isfinite(sim.data.qvel).all():
                    raise FloatingPointError('Nonfinite simulation state')
                state, reason = sim.status()
                obs = sim.observation()
                if writer is not None and step%2 == 0:
                    renderer.update_scene(sim.data, camera=cam)
                    writer.append_data(renderer.render())
                if viewer is not None:
                    viewer.sync()
                    remaining = (step+1)*sim.dt-(time.perf_counter()-start)
                    if remaining>0: time.sleep(remaining)
                if step%100==0: print(f'episode={episode} t={sim.elapsed:.2f}s x={sim.data.qpos[0]:.3f} top={sim.max_supported} ready={sim.ready}', flush=True)
                if state!='running': break
            if state=='running': state, reason = 'incomplete', 'debug_step_limit'
            np.savez_compressed(output/f'trace_{episode:03d}.npz', **trace)
            record = dict(episode=episode, state=state, reason=reason, seconds=sim.elapsed,
                          root_position=sim.data.qpos[:3].tolist(), max_root_x=sim.max_root_x,
                          max_supported_feet=sim.max_supported, ever_top_support=sim.ever_top.tolist(),
                          peak_arm_error_rad=sim.peak_arm_error, peak_torque_nm=sim.peak_torque.tolist(),
                          saturation_physics_steps=sim.saturation_count.tolist(),
                          peak_joint_speed_rad_s=sim.peak_speed.tolist(),
                          speed_exceeded_physics_steps=sim.speed_exceeded_count.tolist(),
                          actuator_delays_physics_steps=sim.delays.tolist(), friction=friction, added_mass_kg=mass,
                          robot_mass_kg=float(model.body_mass.sum()), wall_seconds=time.perf_counter()-start)
            report['episodes'].append(record)
            print(json.dumps(record, ensure_ascii=False), flush=True)
            if writer is not None: writer.close(); writer=None
            if renderer is not None: renderer.close(); renderer=None
            if viewer is not None: viewer.close(); viewer=None
        report['status']='complete'
    except BaseException as exc:
        report['status']='error'; report['error']=repr(exc); traceback.print_exc()
        raise
    finally:
        if writer is not None: writer.close()
        if renderer is not None: renderer.close()
        if viewer is not None: viewer.close()
        report['wall_seconds']=time.perf_counter()-began
        report['successes']=sum(e['state']=='success' for e in report['episodes'])
        (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    return 0 if report['successes']==args.episodes else 2


if __name__ == '__main__':
    raise SystemExit(main())
