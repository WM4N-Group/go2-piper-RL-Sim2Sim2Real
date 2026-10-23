"""原 ELU actor 结构；双策略拼接保持 v212 契约。"""
import torch

def actor_from_state_dict(state, device="cpu"):
    if any(not name.startswith(("mlp.", "distribution.")) for name in state):
        raise ValueError("Only the project's unnormalized ELU actor is supported")
    weights = sorted(
        (int(name.split(".")[1]), value)
        for name, value in state.items() if name.startswith("mlp.") and name.endswith(".weight")
    )
    if not weights or [index for index, _value in weights] != list(range(0, 2 * len(weights), 2)):
        raise ValueError("Unsupported actor layer layout")
    layers = []
    for position, (_index, weight) in enumerate(weights):
        layers.append(torch.nn.Linear(weight.shape[1], weight.shape[0]))
        if position + 1 < len(weights):
            layers.append(torch.nn.ELU())
    actor = torch.nn.Sequential(*layers)
    actor.load_state_dict({name.removeprefix("mlp."): value for name, value in state.items() if name.startswith("mlp.")})
    return actor.to(device).eval()


def load_actors(directory,device):
    """加载已导出的两个冻结Actor，并核对当前契约中的哈希。"""
    import hashlib
    import json
    from pathlib import Path
    directory = Path(directory)
    contract = json.loads((directory/'contract.json').read_text(encoding='utf-8'))
    actors = []
    for name in ('leg_actor.pt','arm_actor.pt'):
        path = directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=contract['actor_sha256'][name]:
            raise ValueError(f'Actor hash mismatch: {name}')
        actors.append(torch.jit.load(str(path),map_location=device).eval())
    return actors
