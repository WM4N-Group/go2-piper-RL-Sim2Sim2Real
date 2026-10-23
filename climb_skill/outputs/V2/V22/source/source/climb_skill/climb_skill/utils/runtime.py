"""Output directories, source provenance, environment recording and checkpoint contracts."""

from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def output_directory(requested, kind):
    if requested:
        path = Path(requested).resolve()
        path.mkdir(parents=True, exist_ok=False)
    else:
        parent = Path(os.environ.get("CLIMB_OUTPUT_ROOT", ROOT / "outputs")).resolve()
        parent.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(prefix=f"{kind}-{datetime.now():%Y%m%d-%H%M%S}-", dir=parent))
    return path


def provenance(output, configuration, checkpoint=None):
    from ..tasks.direct.climb_skill.climb_skill_env_cfg import robot_usd
    versions = {}
    for package in ("isaacsim", "isaaclab", "torch", "numpy", "rsl-rl-lib"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    sources = {}
    for source in sorted(ROOT.rglob("*.py")):
        if "outputs" in source.relative_to(ROOT).parts or "__pycache__" in source.parts:
            continue
        relative = source.relative_to(ROOT)
        destination = output / "source" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        sources[str(relative)] = sha256(source)
    usd = Path(robot_usd())
    assets = {str(p): sha256(p) for p in sorted(usd.parent.rglob("*.usd"))}
    # An explicit external USD override is recorded, not silently attributed to the default asset.
    result = {
        "command": [sys.executable, *sys.argv], "cwd": os.getcwd(), "pid": os.getpid(),
        "created_at": datetime.now().astimezone().isoformat(), "versions": versions,
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "source_sha256": sources, "robot_usd": str(usd), "asset_sha256": assets,
        "checkpoint": str(checkpoint) if checkpoint else None,
        "checkpoint_sha256": sha256(checkpoint) if checkpoint else None,
    }
    try:
        result["git_head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        result["git_status"] = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
        result["gpu_at_start"] = subprocess.check_output([
            "nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu", "--format=csv"], text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        result["system_query_error"] = str(exc)
    write_json(output / "run.json", result)
    write_json(output / "config.json", configuration)
    return result


def load_checkpoint(path, device="cpu"):
    import torch
    state = torch.load(path, map_location=device, weights_only=False)
    if state.get("format") != "climb_skill_v1":
        raise ValueError("Expected a trusted climb_skill_v1 checkpoint, not an old skill actor")
    from ..tasks.direct.climb_skill.task_parameters import require_implementation
    require_implementation(state["configuration"])
    return state

