"""Rank MuJoCo contact candidates against provenance-matched Isaac target replays."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from check_piper_startup import sha256
from compare_piper_control_traces import compare
from trace_piper_climb import trace_episode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--targets", type=Path, nargs="+", required=True)
    parser.add_argument("--native", type=Path, nargs="+", required=True)
    parser.add_argument("--time-constants", type=float, nargs="+", required=True)
    parser.add_argument("--damping-ratios", type=float, nargs="+", required=True)
    parser.add_argument("--impedances", type=float, nargs="+", default=[0.9])
    parser.add_argument("--widths", type=float, nargs="+", default=[0.001])
    parser.add_argument("--constraint-substeps", type=int, choices=(1, 2), default=1)
    parser.add_argument("--contact-margin", type=float, default=0.001)
    parser.add_argument("--comparison-seconds", type=float, default=0.5)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    if len(args.targets) != len(args.native) or not args.targets or args.output_json.exists():
        parser.error("Require equal nonempty target/native lists and a new output")
    if any(value < 0.01 or not np.isfinite(value) for value in args.time_constants):
        parser.error("Time constants must be finite and at least 0.01 s")
    if any(value <= 0.0 or not np.isfinite(value) for value in args.damping_ratios):
        parser.error("Damping ratios must be positive and finite")
    if any(not 0.0 < value < 0.95 or not np.isfinite(value) for value in args.impedances):
        parser.error("Impedances must be finite and between 0 and 0.95")
    if any(not 0.0 < value <= 0.05 or not np.isfinite(value) for value in args.widths):
        parser.error("Widths must be finite and between 0 and 0.05 m")
    if not np.isfinite(args.comparison_seconds) or args.comparison_seconds <= 0.0:
        parser.error("Comparison duration must be positive and finite")
    torch.set_num_threads(1)
    cases = []
    for target_path, native_path in zip(args.targets, args.native):
        target = json.loads(target_path.read_text())
        target["input_sha256"] = sha256(target_path)
        native = json.loads(native_path.read_text())
        seed = target["result"]["seed"]
        if native["trace_sha256"] != target["input_sha256"]:
            raise ValueError(f"Native trace does not match target for seed {seed}")
        cases.append((seed, target_path, target, native_path, native))
    candidates = []
    for time_constant in args.time_constants:
        for damping_ratio in args.damping_ratios:
            for impedance in args.impedances:
                for width in args.widths:
                    per_seed = []
                    for seed, target_path, target, native_path, native in cases:
                        local = trace_episode(
                            args.policy,
                            seed,
                            velocity_mode="coupled-bounds",
                            targets=target,
                            constraint_substeps=args.constraint_substeps,
                            contact_time_constant=time_constant,
                            contact_damping_ratio=damping_ratio,
                            contact_impedance=impedance,
                            contact_width=width,
                            contact_margin=args.contact_margin,
                        )
                        analysis = compare(local, native, target["input_sha256"])
                        limit = min(len(local["steps"]), max(1, round(args.comparison_seconds / local["physics_dt"])))
                        root = []
                        joints = []
                        for left, right in zip(local["steps"][:limit], native["steps"][:limit]):
                            root.append(np.linalg.norm(np.asarray(left["root_pose"][:3]) - right["root_pose"][:3]))
                            joints.append(np.max(np.abs(np.asarray(left["limited_positions"]) - right["solver_positions"])))
                        per_seed.append({
                            "seed": seed, "target_sha256": target["input_sha256"], "native_sha256": sha256(native_path),
                            "root_rmse_m": float(np.sqrt(np.mean(np.square(root)))),
                            "joint_rmse_rad": float(np.sqrt(np.mean(np.square(joints)))),
                            "root_error_final_m": float(root[-1]), "joint_error_final_rad": float(joints[-1]),
                            "first_divergence": analysis["first_divergence"],
                        })
                    candidates.append({
                        "contact_time_constant": time_constant, "contact_damping_ratio": damping_ratio,
                        "contact_impedance": impedance, "contact_width": width,
                        "mean_root_rmse_m": float(np.mean([row["root_rmse_m"] for row in per_seed])),
                        "mean_joint_rmse_rad": float(np.mean([row["joint_rmse_rad"] for row in per_seed])),
                        "per_seed": per_seed,
                    })
                    print(f"CONTACT_SWEEP tc={time_constant} damping={damping_ratio} impedance={impedance} width={width} root_rmse={candidates[-1]['mean_root_rmse_m']:.6f} joint_rmse={candidates[-1]['mean_joint_rmse_rad']:.6f}", flush=True)
    candidates.sort(key=lambda row: (row["mean_root_rmse_m"], row["mean_joint_rmse_rad"]))
    report = {
        "schema_version": 1, "diagnostic_only": True, "policy_sha256": sha256(args.policy),
        "script_sha256": sha256(Path(__file__)), "comparison_seconds": args.comparison_seconds,
        "constraint_substeps": args.constraint_substeps,
        "contact_margin": args.contact_margin, "cases": [
            {"seed": seed, "target": str(target_path), "target_sha256": target["input_sha256"],
             "native": str(native_path), "native_sha256": sha256(native_path)}
            for seed, target_path, target, native_path, native in cases
        ], "candidates": candidates,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x") as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
    print(json.dumps({"best": candidates[0]}, indent=2))


if __name__ == "__main__":
    main()