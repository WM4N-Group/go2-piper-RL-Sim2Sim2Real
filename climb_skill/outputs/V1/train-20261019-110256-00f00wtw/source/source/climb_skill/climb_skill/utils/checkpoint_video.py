"""Record each saved policy in an isolated Isaac process without resetting training."""

import json
from pathlib import Path
import subprocess
import sys
import time

from .runtime import ROOT, sha256, write_json


def record_checkpoint(checkpoint, *, device, task, seconds=24., episodes=1, seed=42001, timeout=900.,
                      box_height=None, label=None):
    checkpoint = Path(checkpoint).resolve()
    parent = checkpoint.parent / "checkpoint_videos"
    parent.mkdir(exist_ok=True)
    name = checkpoint.stem if label is None else f"{checkpoint.stem}-{label}"
    destination = parent / name
    # play.py creates the destination itself and refuses overwrites.
    # 独立子进程跑1环境确定性评估，不扰动训练RNG；但父进程显存仍驻留，不能按纯单进程估算峰值。
    command = [sys.executable, str(ROOT / "scripts/play.py"), "--headless", "--device", device,
               "--task", task, "--checkpoint", str(checkpoint), "--num-envs", "1",
               "--episodes", str(episodes), "--seed", str(seed), "--video",
               "--video-seconds", str(seconds), "--output", str(destination)]
    if box_height is not None:
        command.extend(["--box-height", str(box_height)])
    result = {"checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
              "command": command, "status": "failed", "formal_acceptance": False,
              "box_height_override": box_height, "log": str(parent / f"{name}.log")}
    start = time.monotonic()
    try:
        with Path(result["log"]).open("x") as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=timeout, check=False)
        result["returncode"] = process.returncode
        if process.returncode:
            raise RuntimeError(f"Checkpoint recording exited {process.returncode}; see {result['log']}")
        # 退出码0还不够：必须有完整报告、相同checkpoint哈希和有效视频；策略失败回合仍可构成有效录像。
        report = json.loads((destination / "report.json").read_text())
        video = destination / "climb.mp4"
        if (report.get("status") != "complete" or report.get("missing_episodes") != 0
                or report.get("completed_episodes") != episodes or report.get("video_frames", 0) < 1
                or report.get("checkpoint_sha256") != result["checkpoint_sha256"]
                or not video.is_file()):
            raise RuntimeError(f"Incomplete or mismatched checkpoint recording: {destination}")
        if box_height is not None and abs(report.get("box_height", -1.) - box_height) > 1e-6:
            raise RuntimeError(f"Checkpoint recording used the wrong box height: {destination}")
        result.update(status="complete", video=str(video), report=str(destination / "report.json"),
                      video_sha256=sha256(video), successful_episodes=report["successful_episodes"],
                      completed_episodes=report["completed_episodes"])
        return result
    except BaseException as exc:
        result["error"] = repr(exc)
        raise
    finally:
        result["wall_seconds"] = time.monotonic() - start
        write_json(parent / f"{name}.json", result)


def checkpoint_due(iteration, final_iteration, interval):
    """Save/video together, including the final incomplete interval."""
    return iteration > 0 and (iteration % interval == 0 or iteration == final_iteration)
