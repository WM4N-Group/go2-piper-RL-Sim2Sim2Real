"""Replay the two recorded s38 PUSH cases with isolated Isaac self-collision."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path("/opt/go2-piper/artifacts/go2-piper")
WORLD = Path("/opt/go2-piper-world-model")
SOURCE_PLAN = WORLD / "push-observed-geometry-v1/control/plan.json"
ISOLATED = ROOT / "sim2sim-current-20261008-a/push-self-collision-diagnostic-v1"
TRAIN = ISOLATED / "train"
ORIGINAL = ROOT / "push-ramptrain-20261001-aa/train"
CANDIDATE = ROOT / "push-loadprobe-20261001-ac/selected-candidate"
OUTPUT = ROOT / "sim2sim-current-20261008-a/push-s38-self-collision-v2"
ASSET = Path("source/LeggedManip_Lab/LeggedManip_Lab/assets/go2_piper/go2_piper_articulation_cfg.py")
CHECKPOINT_SHA256 = "b1ebb8abb5370dcd98debab85d70e05a004bb1e59b5b00710460f575174c7721"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_argument(command: list[str], flag: str, value: str) -> None:
    command[command.index(flag) + 1] = value


def main() -> None:
    source = (ORIGINAL / ASSET).read_text()
    original_line = "enabled_self_collisions=False,"
    assert source.count(original_line) == 1
    assert (TRAIN / ASSET).read_text() == source.replace(
        original_line, "enabled_self_collisions=True,"
    )
    assert digest(CANDIDATE / "model_199.pt") == CHECKPOINT_SHA256
    snapshot_hashes = {}
    for path in (CANDIDATE / "source-snapshot").rglob("*.py"):
        relative = path.relative_to(CANDIDATE / "source-snapshot")
        assert digest(path) == digest(TRAIN / relative), relative
        snapshot_hashes[str(relative)] = digest(path)

    source_plan = json.loads(SOURCE_PLAN.read_text())
    assert digest(Path(source_plan["evaluator_path"])) == source_plan["evaluation_sha256"]
    assert source_plan["checkpoint_sha256"] == CHECKPOINT_SHA256
    cases = [case for case in source_plan["cases"] if case["case_id"] in {
        "s38-m6-f35", "s38-m8-f25"
    }]
    assert len(cases) == 2
    if OUTPUT.exists():
        raise FileExistsError(f"Use a new output directory: {OUTPUT}")
    OUTPUT.mkdir(parents=True)

    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = "0"
    environment["PYTHONPATH"] = str(TRAIN / "source/LeggedManip_Lab")
    environment["PIPER_SOURCE_ROOT"] = str(TRAIN)
    for case in cases:
        case_dir = OUTPUT / case["case_id"]
        case_dir.mkdir()
        command = list(case["argv"])
        assert command[1] == source_plan["evaluator_path"]
        replace_argument(command, "--output-json", str(case_dir / "report.json"))
        replace_argument(command, "--video-path", str(case_dir / "video.mp4"))
        (case_dir / "plan.json").write_text(json.dumps({
            "scope": "s38 matched-seed Isaac self-collision diagnostic; not acceptance",
            "source_plan_sha256": digest(SOURCE_PLAN),
            "source_report_sha256": digest(Path(case["output_dir"]) / "report.json"),
            "source_snapshot_sha256": snapshot_hashes,
            "original_asset_sha256": digest(ORIGINAL / ASSET),
            "diagnostic_asset_sha256": digest(TRAIN / ASSET),
            "checkpoint_sha256": CHECKPOINT_SHA256,
            "physical_gpu": 0,
            "command": command,
        }, indent=2) + "\n")
        with (case_dir / "run.log").open("x") as log:
            result = subprocess.run(
                ["timeout", "-k", "15s", "900s", *command],
                cwd=TRAIN, env=environment, stdout=log, stderr=subprocess.STDOUT,
                check=False,
            )
        report = case_dir / "report.json"
        (case_dir / "exit-status.json").write_text(json.dumps({
            "returncode": result.returncode,
            "report_exists": report.is_file(),
            "report_sha256": digest(report) if report.is_file() else None,
        }, indent=2) + "\n")
        if result.returncode != 0 or not report.is_file():
            raise RuntimeError(f"{case['case_id']} failed; inspect {case_dir / 'run.log'}")


if __name__ == "__main__":
    main()
