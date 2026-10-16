"""Run the fixed PUSH precontact detour diagnostic on recorded failure states."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--exclude-env", type=int, nargs="*", default=())
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("Output directory already exists")
    source = json.loads(args.source_report.read_text())
    envs = sorted({row["env_id"] for row in source["failure_histories"]} - set(args.exclude_env))
    if not envs:
        parser.error("No failure environments remain")
    root = Path(__file__).resolve().parent
    static_runner = root / "diagnose_push_failure_detour.py"
    pd_runner = root / "validate_push_failure_detour_pd.py"
    args.output_dir.mkdir(parents=True)
    summary = {
        "schema_version": 1, "kind": "used_seed_local_precontact_diagnostic",
        "source_report_sha256": digest(args.source_report),
        "static_runner_sha256": digest(static_runner), "pd_runner_sha256": digest(pd_runner),
        "batch_runner_sha256": digest(Path(__file__)), "python": sys.executable,
        "requested_envs": envs, "excluded_envs": list(args.exclude_env), "results": [],
        "limitations": "Recorded precontact states only; no box contact, NAV control, full PUSH task or independent acceptance.",
    }

    def save():
        pending = args.output_dir / "summary.pending.json"
        pending.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        pending.replace(args.output_dir / "summary.json")

    def run(command, timeout):
        start = time.monotonic()
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return {"returncode": completed.returncode, "stdout": completed.stdout[-2000:],
                    "stderr": completed.stderr[-2000:], "wall_seconds": time.monotonic() - start}
        except subprocess.TimeoutExpired as exc:
            return {"returncode": None, "timed_out": True,
                    "stdout": (exc.stdout or b"")[-2000:].decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")[-2000:],
                    "stderr": (exc.stderr or b"")[-2000:].decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")[-2000:],
                    "wall_seconds": time.monotonic() - start}

    save()
    for env in envs:
        row = {"env": env, "static_attempts": []}
        static_path = None
        for name, extra in (
            ("default", []),
            ("expanded", ["--candidate-count", "12", "--max-iterations", "160", "--orientation-weight", "0.08"]),
        ):
            path = args.output_dir / f"env{env}-{name}-static.json"
            command = [sys.executable, str(static_runner), "--report", str(args.source_report),
                       "--output", str(path), "--clearance", "0.020", "--env", str(env), *extra]
            execution = run(command, 180)
            attempt = {"name": name, "command": command, "execution": execution,
                       "report": str(path) if path.is_file() else None}
            row["static_attempts"].append(attempt)
            if path.is_file():
                attempt["report_sha256"] = digest(path)
                static = json.loads(path.read_text())
                if static["selected_candidate"] is not None and static["path"] is not None:
                    static_path = path
                    break
            if execution["returncode"] != 0:
                break
        if static_path is not None:
            pd_path = args.output_dir / f"env{env}-pd.json"
            command = [sys.executable, str(pd_runner), "--path-report", str(static_path),
                       "--output", str(pd_path), "--max-rate", "0.2", "--base-mode", "free",
                       "--terminal-correction", "--settle-seconds", "0.1", "--orientation-weight", "0.06"]
            execution = run(command, 120)
            row["pd"] = {"command": command, "execution": execution,
                         "report": str(pd_path) if pd_path.is_file() else None}
            if pd_path.is_file():
                row["pd"]["report_sha256"] = digest(pd_path)
                pd = json.loads(pd_path.read_text())
                row["pd"]["passed"] = pd["passed"]
                row["pd"]["minimum_protected_clearance"] = pd["minimum_protected_clearance"]
                row["pd"]["final_hand_target_error"] = pd["final_hand_target_error"]
                row["pd"]["final_hand_orientation_error"] = pd["final_hand_orientation_error"]
        summary["results"].append(row)
        save()
        print(json.dumps({"env": env, "static_found": static_path is not None,
                          "pd_passed": row.get("pd", {}).get("passed")}), flush=True)


if __name__ == "__main__":
    main()
