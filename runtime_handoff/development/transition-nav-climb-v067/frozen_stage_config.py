"""Extract exact frozen CLIMB action configuration without running its evaluator.

Only the original action configuration block is applied. Physical reset events,
state banks, source weights, runtime histories and simulator state are untouched.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def extract(source_file, jobs_file, expected_source_sha256):
    source = Path(source_file).read_bytes()
    if hashlib.sha256(source).hexdigest() != expected_source_sha256:
        raise ValueError('Frozen evaluator hash mismatch')
    tree = ast.parse(source)
    parser = argparse.ArgumentParser(add_help=False)
    flags = {}
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute) or ast.unparse(call.func) != 'parser.add_argument':
            continue
        if not call.args or not isinstance(call.args[0], ast.Constant):
            continue
        flag = call.args[0].value
        if not isinstance(flag, str) or not flag.startswith('--climb-') or flag == '--climb-stage-bank':
            continue
        kwargs = {}
        for kw in call.keywords:
            if kw.arg in ('action', 'default', 'choices', 'nargs', 'required'):
                kwargs[kw.arg] = ast.literal_eval(kw.value)
            elif kw.arg == 'type':
                if not isinstance(kw.value, ast.Name) or kw.value.id not in ('float', 'int', 'str'):
                    raise ValueError('Unexpected CLIMB argument type')
                kwargs['type'] = {'float': float, 'int': int, 'str': str}[kw.value.id]
        parser.add_argument(flag, **kwargs)
        flags[flag] = kwargs
    job, = json.loads(Path(jobs_file).read_text())
    command = job['command']
    arguments = []
    for i, flag in enumerate(command):
        if flag in flags:
            arguments.append(flag)
            if flags[flag].get('action') != 'store_true':
                arguments.append(command[i + 1])
    args = parser.parse_args(arguments)
    if not args.climb_stage_guidance:
        raise ValueError('Frozen job has no stage guidance')
    main, = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main']
    block, = [node for node in main.body if isinstance(node, ast.If) and ast.unparse(node.test) == 'args.climb_stage_guidance']
    result = {}
    for node in block.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            raise ValueError('Unexpected stage configuration statement')
        target = ast.unparse(node.targets[0])
        prefix = 'config.actions.joint_pos.'
        if not target.startswith(prefix):
            raise ValueError('Configuration writes outside action contract')
        value = node.value
        if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id == 'args':
            value = getattr(args, value.attr)
        else:
            value = ast.literal_eval(value)
        result[target[len(prefix):]] = value
    return result


def apply(action_cfg, values):
    for name, value in values.items():
        if not hasattr(action_cfg, name):
            raise ValueError('Stage action field missing: ' + name)
        setattr(action_cfg, name, value)
