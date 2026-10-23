"""将本地可信v2 checkpoint迁移到仅修改课程的v4，不执行任何训练更新。"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import torch
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, PPOConfig, load_config, configuration, require_implementation)


def migrate(state, task, ppo):
    """只改变配置元数据；网络、优化器、AMP、RNG及课程等级全部原样保留。"""
    require_implementation(state['configuration'])
    if state['configuration']['implementation_revision'] != 'climb_skill_v3_foot_crossing_quality_v2':
        raise ValueError('Migration requires the v2 crossing-quality checkpoint')
    task.validate()
    ppo.validate()
    if not (task.curriculum_only_enabled and task.quality_window_enabled):
        raise ValueError('Target must enable curriculum-only v4')
    # JSON配置使用list，checkpoint可能使用tuple；按相同序列语义比较。
    before = json.loads(json.dumps(asdict(TaskConfig(**state['configuration']['task']))))
    after = json.loads(json.dumps(asdict(task)))
    changed = {k: {'before': before[k], 'after': after[k]} for k in before if before[k] != after[k]}
    allowed = {'curriculum_only_enabled', 'quality_window_enabled', 'quality_window_size', 'quality_window_required'}
    if set(changed) - allowed:
        raise ValueError(f'Non-curriculum changes rejected: {sorted(set(changed) - allowed)}')
    if asdict(PPOConfig(**state['configuration']['ppo'])) != asdict(ppo):
        raise ValueError('PPO/AMP configuration must remain identical')
    required = ('model', 'optimizer', 'estimator_optimizer', 'history_optimizer', 'amp',
                'torch_rng', 'python_rng', 'numpy_rng', 'learning_rate', 'iteration', 'curriculum_levels')
    if any(k not in state for k in required):
        raise ValueError('Checkpoint is missing learning state')
    result = dict(state)
    result['configuration'] = configuration(task, ppo)
    return result, changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory; refuses overwrite')
    args = parser.parse_args()
    state = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    task, ppo = load_config(args.config)
    migrated, changes = migrate(state, task, ppo)
    digest = hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()
    migrated['curriculum_migration'] = dict(source=str(args.checkpoint.resolve()),
                                          source_sha256=digest, changes=changes)
    args.output.mkdir(parents=True, exist_ok=False)
    destination = args.output / f'model_{state["iteration"]}_curriculum.pt'
    torch.save(migrated, destination)
    report = dict(source=str(args.checkpoint.resolve()), source_sha256=digest,
                  destination=str(destination.resolve()),
                  destination_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                  changed_task_fields=changes, optimizer_updates=0,
                  iteration_preserved=state['iteration'], physics_state_restored=False,
                  note='Learning state preserved; episode state and curriculum evidence window reset on resume')
    (args.output / 'migration.json').write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
