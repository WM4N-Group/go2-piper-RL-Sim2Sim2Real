"""对比训练快照的真实观测函数，检查模型映射、力矩裁剪、history Actor和文件完整性。"""
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
import mujoco
from bridge import ROOT, ClimbBridge, JOINTS, EFFORT, build_model, load_contract, sha


def verify():
    torch.set_num_threads(2)
    manifest = ROOT/'SHA256SUMS'
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            digest, name = line.split('  ', 1)
            if sha(ROOT/name) != digest:
                raise ValueError(f'文件完整性检查失败: {name}')
    contract = load_contract()
    cfg = contract['configuration']['task']
    model, _ = build_model(cfg, .2)
    sim = ClimbBridge(model, cfg, .2)
    actor = torch.jit.load(str(ROOT/'policy/actor.pt')).eval()
    assert model.nu == 18 and model.nv == 24
    assert list(model.joint(i).name for i in sim.jids) == JOINTS
    assert abs(model.body_mass.sum()-21.765000641345978)<1e-5
    # 执行训练快照中的原函数，仅替换Isaac依赖；公式和历史写入逻辑保持不动。
    code = (ROOT/'policy/observations_reference.py.txt').read_text()
    code = code.replace('from isaaclab.utils.math import euler_xyz_from_quat', '')
    code = code.replace('from ..task_parameters import HISTORY', '')
    code = code.replace('from .geometry import box_scan, constrained_actions, stable_timer, top_support', '')
    code = code.replace('from .startup import movement_gain', 'pass')
    def euler(quat):
        w,x,y,z = quat.unbind(-1)
        yaw = torch.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))
        return torch.zeros_like(yaw), torch.zeros_like(yaw), yaw
    def scan(xy, height, task):
        on = (xy[...,0]>=task.box_front)&(xy[...,0]<=task.box_front+task.box_length)&(xy[...,1].abs()<=task.box_width/2)
        return on*height[:,None]
    scope = dict(torch=torch, HISTORY=10, euler_xyz_from_quat=euler, box_scan=scan,
                 top_support=lambda *a:None, movement_gain=lambda e:torch.tensor([sim.gain]))
    exec(compile(code, 'training_snapshot_observations', 'exec'), scope)
    task=SimpleNamespace(**cfg); task.route_goal_x=cfg['box_front']+cfg['goal_offset']
    ref=SimpleNamespace(task=task, history=torch.zeros(1,10,69), fresh=torch.tensor([True]),
                        history_step=-1, common_step_counter=0)
    t=lambda a:torch.as_tensor(np.array(a),dtype=torch.float32)
    max_error=0.
    for frame in range(12):
        rotation, gravity, _, _ = sim.state()
        data=SimpleNamespace(root_pos_w=t(sim.data.qpos[:3])[None], root_quat_w=t(sim.data.qpos[3:7])[None],
                             body_pos_w=t(sim.data.xpos[sim.feet_ids])[None], root_ang_vel_b=t(sim.data.qvel[3:6])[None],
                             projected_gravity_b=t(gravity)[None], root_lin_vel_b=t(rotation.T@sim.data.qvel[:3])[None],
                             joint_pos=t(sim.data.qpos[sim.qids])[None], joint_vel=t(sim.data.qvel[sim.dids])[None])
        ref.robot=SimpleNamespace(data=data)
        ref.scene=SimpleNamespace(env_origins=torch.zeros(1,3))
        ref.foot_ids=ref.contact_feet=list(range(4));ref.joint_ids=list(range(18))
        ref.contact=SimpleNamespace(data=SimpleNamespace(net_forces_w=t(sim.forces[sim.feet_ids])[None]))
        ref.heights=t([.2]);ref.reference=t(sim.reference)[None];ref.actions=t(sim.actions)[None]
        ref.sample_xy=torch.cartesian_prod(torch.linspace(-.45,1.2,12),torch.linspace(-.75,.75,11))
        ref.privileged=torch.zeros(1,29)
        ref._kinematics=lambda:scope['kinematics'](ref)
        ref._proprio_scan=lambda:scope['proprio_scan'](ref)
        ref._build_observation=lambda:scope['build_observation'](ref)
        reference=scope['get_observations'](ref)['policy'].numpy()[0]
        # 201:204为原真速度占位，部署Actor不消费，适配器显式写零。
        reference[201:204]=0.
        actual=sim.observation()
        np.testing.assert_allclose(actual, reference, rtol=1e-5, atol=2e-6)
        max_error=max(max_error,float(abs(actual-reference).max()))
        with torch.inference_mode():
            result=actor(torch.from_numpy(actual)[None])
            assert result.shape==(1,18) and torch.isfinite(result).all() and not result[:,12:].count_nonzero()
            changed=torch.from_numpy(actual)[None].clone();changed[:,201:233]=100.
            torch.testing.assert_close(result, actor(changed), rtol=0, atol=0)
        sim.set_action(np.full(18,0.) )
        for _ in range(cfg['decimation']): sim.physics_step()
        sim.status();ref.common_step_counter+=1
    sim.ready=True;sim.release_time=0.;sim.elapsed=2.
    sim.set_action(np.r_[np.full(12, 1000.), np.zeros(6)])
    for _ in range(8): sim.physics_step()
    assert np.all(abs(sim.applied_torque)<=EFFORT+1e-9)
    assert np.all(sim.targets[[7,10]]<=cfg['rear_thigh_max'])
    assert np.all(sim.targets[12:]==sim.reference[12:])
    result=dict(status='passed', checkpoint_sha256=contract['checkpoint_sha256'],
                actor_sha256=contract['actor_sha256'], observation_reference_frames=12,
                observation_max_absolute_error=max_error, bodies=model.nbody,
                robot_mass_kg=float(model.body_mass.sum()),joint_order=JOINTS,
                checks=['snapshot observations/history match','ignored privileged slots invariant',
                        '18-axis output with zero arm residual','joint/actuator mapping',
                        'effort clipping and rear workspace'], formal_acceptance=False)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__': verify()
