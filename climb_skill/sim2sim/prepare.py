"""从可信的本地V1训练快照导出部署Actor，不启动Isaac、不修改训练源码。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
DEFAULT_CHECKPOINT = PROJECT / 'climb_skill/outputs/V1/train-20261019-110256-00f00wtw/model_900.pt'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(checkpoint):
    import torch
    torch.set_num_threads(2)
    saved = torch.load(checkpoint, map_location='cpu', weights_only=False)
    config = saved['configuration']
    if saved['iteration'] != 900 or config['observation_dimensions']['total'] != 923:
        raise ValueError('本入口只绑定V1 model_900及923维观测合同')
    # 读取该训练的源码快照；只替换常量导入，避免注册Isaac/Gym依赖。
    source = checkpoint.parent / 'source/source/climb_skill/climb_skill/learning/actor_critic.py'
    code = source.read_text()
    old = 'from ..tasks.direct.climb_skill.task_parameters import EXPLICIT, HISTORY, OBSERVATIONS, PRIVILEGED, PROPRIO, SCAN'
    if old not in code:
        raise ValueError('Unrecognized snapshot actor import')
    code = code.replace(old, 'EXPLICIT, HISTORY, OBSERVATIONS, PRIVILEGED, PROPRIO, SCAN = 3, 10, 923, 29, 69, 132')
    scope = {'__name__': 'climb_v1_900_snapshot', '__file__': str(source)}
    exec(compile(code, str(source), 'exec'), scope)
    actor = scope['ClimbActorCritic'](config['ppo']['initial_std']).eval()
    actor.load_state_dict(saved['model'], strict=True)
    dest = ROOT / 'policy'
    dest.mkdir(exist_ok=True)
    torch.manual_seed(900)
    with torch.inference_mode():
        traced = torch.jit.trace(actor, torch.zeros(1, 923))
        examples = torch.randn(8, 923)
        torch.testing.assert_close(actor(examples), traced(examples))
        if torch.count_nonzero(traced(examples)[:, 12:]):
            raise ValueError('Arm residual must be zero')
        # 未使用的真速度与特权参数不能影响history部署分支。
        changed = examples.clone(); changed[:, 201:233] += 20
        torch.testing.assert_close(traced(examples), traced(changed), rtol=0, atol=0)
    traced.save(str(dest / 'actor.pt'))
    contract = {'version': 'V1', 'iteration': 900, 'checkpoint_sha256': sha(checkpoint),
                'checkpoint_project_path': str(checkpoint.relative_to(PROJECT)),
                'snapshot_actor_sha256': sha(source), 'actor_sha256': sha(dest/'actor.pt'),
                'policy_branch': 'history', 'configuration': config,
                'export_validation': 'eager/JIT matched; arm residual zero; privileged slots ignored',
                'formal_acceptance': False}
    (dest/'contract.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2)+'\n')
    # 不导入旧控制器，只复制匹配公共USD哈希的几何与惯性数据。
    origin = PROJECT/'push_skill/geometry'
    robot = PROJECT/'asset/go2_piper/mujoco'
    robot.mkdir(exist_ok=True)
    for name in ('piper_robot_profile.json', 'piper_collision_profile.json'):
        profile = json.loads((origin/'deploy'/name).read_text())
        for path, digest in profile['usd_sha256'].items():
            suffix = path.split('assets/go2_piper/', 1)[1]
            if sha(PROJECT/'asset/go2_piper'/suffix) != digest:
                raise ValueError(f'公共USD与profile不匹配: {suffix}')
        shutil.copy2(origin/'deploy'/name, robot/name)
    source_xml = origin/'robots/go2_piper/go2piper.xml'
    shutil.copy2(source_xml, robot/'source_robot.xml')
    (robot/'assets').mkdir(exist_ok=True)
    for mesh in ET.parse(source_xml).findall('.//asset/mesh'):
        filename = Path(mesh.attrib['file']).name
        shutil.copy2(source_xml.parent/'assets'/filename, robot/'assets'/filename)
    provenance = {'source_xml_sha256': sha(source_xml), 'profiles_match_all_shared_usd_hashes': True,
                  'note': 'XML仅作视觉/拓扑底稿；运行时以USD profile替换惯性、位姿、关节和碰撞，不加载旧策略或切换控制器。'}
    (robot/'PROVENANCE.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n')
    print(dest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args()
    export(args.checkpoint.resolve())
