"""真实物理承重初始化和录像标注。"""
import json
from pathlib import Path
import time

def settle(base, report_path):
    import torch
    robot = base.scene['robot']
    ids, _ = robot.find_bodies('.*_foot')
    targets = robot.data.joint_pos.clone()
    start = robot.data.root_pos_w.clone()
    # 从原USD读取足底球半径和局部中心，不猜初始机身高度。
    from pxr import Usd, UsdGeom
    from isaaclab.utils.math import quat_apply
    stage = Usd.Stage.Open(robot.cfg.spawn.usd_path)
    root = stage.GetDefaultPrim()
    offsets, radii = [], []
    cache = UsdGeom.XformCache()
    for body_id in ids:
        foot = stage.GetPrimAtPath(str(root.GetPath()) + '/' + robot.body_names[body_id])
        sphere = stage.GetPrimAtPath(str(foot.GetPath()) + '/collisions/mesh_0/sphere')
        if not sphere or not sphere.IsA(UsdGeom.Sphere):
            raise ValueError('Unsupported foot collision geometry; cannot ground startup safely')
        transform, _ = cache.ComputeRelativeTransform(sphere, foot)
        offsets.append(list(transform.ExtractTranslation()))
        radii.append(UsdGeom.Sphere(sphere).GetRadiusAttr().Get())
    offset = torch.tensor(offsets, device=base.device).expand(base.num_envs, -1, -1)
    center = robot.data.body_pos_w[:, ids] + quat_apply(robot.data.body_quat_w[:, ids], offset)
    bottom = center[:, :, 2] - torch.tensor(radii, device=base.device)
    gap = (bottom - base.scene.env_origins[:, 2:3]).min(dim=1).values
    # 仅初始化：最低足底放在地面上方2mm，保留水平位置和关节姿态。
    pose = robot.data.root_state_w[:, :7].clone()
    pose[:, 2] -= (gap - .002).clamp_min(0)
    robot.write_root_pose_to_sim(pose)
    robot.write_root_velocity_to_sim(torch.zeros_like(robot.data.root_state_w[:, 7:]))
    grounded_root = pose[:, :3].clone()
    stable_age = torch.zeros(base.num_envs, device=base.device)
    physics_dt = base.physics_dt
    began = time.perf_counter()
    maximum_speed = 0.0
    # 不重置状态、不锁根部、不施加外力；原PD真实承重。
    for step in range(round(5.0 / physics_dt)):
        robot.set_joint_position_target(targets)
        base.scene.write_data_to_sim()
        base.sim.step(render=False)
        base.scene.update(physics_dt)
        speed = robot.data.root_lin_vel_w.norm(dim=-1)
        omega = robot.data.root_ang_vel_w.norm(dim=-1)
        forces = base.scene['contact_forces'].data.net_forces_w
        sensor_ids, _ = base.scene['contact_forces'].find_bodies('.*_foot')
        loaded = (forces[:, sensor_ids].norm(dim=-1) > 3.0).all(dim=-1)
        good = (speed < .035) & (omega < .12) & loaded
        stable_age = torch.where(good, stable_age + physics_dt, 0.0)
        maximum_speed = max(maximum_speed, float(speed.max()))
        if step * physics_dt >= .5 and bool((stable_age >= .3).all()):
            break
    ok = bool((stable_age >= .3).all())
    # 承重准备属于reset；保留承重关节状态，将XY放回原任务起点。
    # 箱子/目标不移动，防止准备期漂移改变狗-箱初始距离。
    if ok:
        pose = robot.data.root_state_w[:, :7].clone()
        pose[:, :2] = start[:, :2]
        robot.write_root_pose_to_sim(pose)
        robot.write_root_velocity_to_sim(torch.zeros_like(robot.data.root_state_w[:, 7:]))
        for _ in range(round(.5 / physics_dt)):
            robot.set_joint_position_target(targets)
            base.scene.write_data_to_sim()
            base.sim.step(render=False)
            base.scene.update(physics_dt)
        speed = robot.data.root_lin_vel_w.norm(dim=-1)
        omega = robot.data.root_ang_vel_w.norm(dim=-1)
        forces = base.scene['contact_forces'].data.net_forces_w
        loaded = (forces[:, sensor_ids].norm(dim=-1) > 3.0).all(dim=-1)
        xy_error = (robot.data.root_pos_w[:, :2] - start[:, :2]).norm(dim=-1)
        ok = bool(((speed < .035) & (omega < .12) & loaded & (xy_error < .01)).all())
    result = dict(stable=ok, simulation_seconds=(step+1)*physics_dt + .5,
                  wall_seconds=time.perf_counter()-began,
                  initial_root=start.tolist(), grounded_root=grounded_root.tolist(), initial_foot_gap=gap.tolist(), foot_radii=radii, settled_root=robot.data.root_pos_w.tolist(),
                  peak_speed=maximum_speed, final_speed=speed.tolist(),
                  final_omega=omega.tolist(), four_feet_loaded=loaded.tolist(),
                  scope='Startup physical settling only; not task success or arm-motion stability')
    Path(report_path).write_text(json.dumps(result, indent=2)+'\n')
    if not ok:
        raise RuntimeError('Startup did not settle in 5 seconds; see startup-report.json')
    # 任务计时从承重初始化完成后开始，不重置箱子。
    base.action_manager.reset()
    base.observation_manager.reset()
    base.episode_length_buf.zero_()
    base.observation_manager.compute(update_history=True)
    return result

def frame(rgb, seconds):
    from PIL import Image, ImageDraw
    import numpy as np
    global _video_size
    canvas = Image.fromarray(rgb).convert('RGB')
    _video_size = canvas.size
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas.width, 40), fill=(15, 20, 30))
    draw.text((12, 12), f'RUNNING | simulation t={seconds:.2f}s | task success requires report', fill='white')
    return np.asarray(canvas)

def result_card(seconds, completed, successful, reasons, size=(1280, 720)):
    from PIL import Image, ImageDraw
    import numpy as np
    size = globals().get('_video_size', size)
    canvas = Image.new('RGB', size, (15, 20, 30))
    draw = ImageDraw.Draw(canvas)
    lines = ['RESULT CARD - STATIC (not simulated motion)',
             f'Last recorded simulation time: {seconds:.2f}s',
             f'Completed per environment: {completed}',
             f'Successful per environment: {successful}',
             'Batch termination counts:']
    lines += [f'{name}: {count}' for name, count in reasons.items() if count]
    if sum(completed) == 0:
        lines.append('INCOMPLETE: no finished episode; inspect report.json')
    elif sum(successful) < sum(completed):
        lines.append('FAILED episodes exist. Video ended because evaluation ended.')
    else:
        lines.append('Finished episodes succeeded; inspect report for missing episodes.')
    for i, line in enumerate(lines):
        draw.text((25, 25 + i * 30), line, fill='white')
    return np.asarray(canvas)
