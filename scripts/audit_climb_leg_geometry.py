"""Audit sampled CLIMB leg-to-platform gaps using the frozen USD geometry."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import mmap
from pathlib import Path
import sys
import types

import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unpack(value):
    if isinstance(value, dict) and set(value) == {"dtype", "data"}:
        return torch.tensor(value["data"], dtype=getattr(torch, value["dtype"]))
    if isinstance(value, dict):
        return {key: unpack(item) for key, item in value.items()}
    if isinstance(value, list):
        return [unpack(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new geometry audit output path")

    mdp = (args.candidate / "train/source/LeggedManip_Lab/LeggedManip_Lab/tasks"
           "/manager_based/leggedmanip_lab/mdp")
    package = types.ModuleType("_climb_audit_math")
    package.__path__ = [str(mdp)]
    sys.modules[package.__name__] = package
    spec = importlib.util.spec_from_file_location(
        "_climb_audit_math.diag", args.candidate / "climb_guidance.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from _climb_audit_math.climb_leg_kinematics import LegKinematics
    from _climb_audit_math.climb_body_clearance import leg_link_poses, primitive_box_gap

    physics = json.loads((args.verification.parent / "actual-physics.json").read_text())
    numeric = json.loads((args.candidate / "geometry-numeric-model.json").read_text())
    usd = mdp.parents[3] / "assets/go2_piper/go2_piper.usd"
    asset_key = "source/LeggedManip_Lab/LeggedManip_Lab/assets/go2_piper/go2_piper.usd"
    if sha256(usd) != physics["robot_asset_sha256"][asset_key] or sha256(usd) != numeric["usd_sha256"]:
        raise ValueError("CLIMB geometry USD hash mismatch")
    for name, expected in numeric["math_source_sha256"].items():
        if sha256(mdp / name) != expected:
            raise ValueError(f"CLIMB geometry math hash mismatch: {name}")
    verification = json.loads(args.verification.read_text())
    if sha256(args.report) != verification["report_sha256"]:
        raise ValueError("CLIMB report differs from the verified run")

    fixtures = json.loads((args.verification.parent / "planning-inputs.json").read_text())[
        "climb_front_ascent_inputs"
    ]
    model = LegKinematics(numeric["geometry"])
    primitives = unpack(numeric["primitives"])
    foot_slots = ((0, 4, 9), (1, 5, 10), (2, 6, 11), (3, 7, 12))
    torch.set_num_threads(2)
    environments = {}
    with args.report.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as report:
        for env_id in range(32):
            key = f'"trace_env{env_id}":'.encode()
            start = report.find(key)
            if start < 0:
                raise ValueError(f"Missing trace for environment {env_id}")
            start += len(key)
            rows, _ = json.JSONDecoder().raw_decode(
                report[start:start + 256 * 1024 * 1024].decode().lstrip()
            )
            fixture = fixtures.get(str(env_id))
            origin = torch.tensor(fixture["swing"]["origins"]) if fixture else torch.zeros(1, 3)
            box = (torch.tensor(fixture["box_bounds"]) if fixture
                   else torch.tensor([[[0.75, -0.6, 0.0], [1.95, 0.6, 0.2]]]))
            gaps = []
            limiting = []
            for begin in range(0, len(rows), 512):
                selected = rows[begin:begin + 512]
                joints = torch.tensor([
                    [[row["joint_position"][joint] for joint in leg] for leg in foot_slots]
                    for row in selected
                ])
                position = torch.tensor([row["robot_position"] for row in selected]) + origin
                orientation = torch.tensor([row["robot_quaternion"] for row in selected])
                link_position, link_orientation = leg_link_poses(model, joints, position, orientation)
                gap = primitive_box_gap(
                    link_position, link_orientation, primitives, box[:, None, None]
                ).flatten(1).min(1)
                gaps.extend(gap.values.tolist())
                limiting.extend(gap.indices.tolist())

            minimum = min(range(len(gaps)), key=gaps.__getitem__)
            link = ("FL", "FR", "RL", "RR")[limiting[minimum] // 3]
            part = ("hip", "thigh", "calf")[limiting[minimum] % 3]
            environments[env_id] = {
                "samples": len(rows),
                "minimum_gap_m": gaps[minimum],
                "minimum_time_s": rows[minimum]["step"] * 0.02,
                "limiting_link": f"{link}_{part}",
                "below_5mm_samples": sum(gap < 0.005 for gap in gaps),
                "negative_gap_samples": sum(gap < 0 for gap in gaps),
            }
            print(env_id, round(gaps[minimum] * 1000, 4), environments[env_id]["below_5mm_samples"], flush=True)

    args.output.write_text(json.dumps({
        "scope": "All 32 sampled 20ms full-stage traces; leg USD primitives only, no physics substeps",
        "report_sha256": verification["report_sha256"],
        "environments": environments,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
