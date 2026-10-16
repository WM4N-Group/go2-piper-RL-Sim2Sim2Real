"""Verify a completed CLIMB edge-stage regression without changing its report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(values) -> float:
    return math.sqrt(sum(value * value for value in values))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--baseline-verification", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new verification output path")

    plan = json.loads((args.candidate / "plan.json").read_text())
    source_hashes = {
        relative: sha256(args.candidate / "train" / relative)
        for relative in plan["source_sha256"]
    }
    if source_hashes != plan["source_sha256"] or len(source_hashes) != 12:
        raise ValueError("CLIMB candidate source hash mismatch")
    with args.report.open() as stream:
        report = json.load(stream)
    terminal_states = {item["env_id"]: item for item in report["terminal_states"]}
    if (report["seed"] != args.seed or report["num_envs"] != 32
            or report["completed_episodes"] != 32 or report["incomplete_episodes"] != 0
            or len(terminal_states) != 32 or set(terminal_states) != set(range(32))):
        raise ValueError("Missing or duplicate terminal states")
    manifest = {Path(relative).name: digest for relative, digest in source_hashes.items()}
    if (report["evaluation_sha256"] != manifest["evaluate_box_skills.py"]
            or report["actor_policy_sha256"] != plan["actor_sha256"]
            or report["actual_physics"]["climb_stage_bank_sha256"] != plan["stage_bank_sha256"]
            or any(digest != manifest[name] for name, digest in report["control_sha256"].items()
                   if name in manifest)):
        raise ValueError("Reported source, actor or reset bank differs from the candidate")

    mass = report["actual_physics"]["stage_mass_provenance"]
    if mass["cached_at_end"] != mass["actual_at_end"] or mass["actual_at_end"] != mass["actual_after_startup"]:
        raise ValueError("Cached and actual PhysX mass differ")
    weights = [sum(body_masses) * 9.81 for body_masses in mass["actual_at_end"]]
    ascent = [index for index, count in enumerate(report["max_supported_feet"]) if count == 4]
    extension = [index for index, state in terminal_states.items()
                 if state["platform_extension_completed"] == 2]
    comfortable = []
    release_count = reload_count = 0
    violations = []
    stage_times = {}
    for env_id in range(32):
        rows = report[f"trace_env{env_id}"]
        first_mass = next((row["step"] for row in rows
                           if abs(row["guidance_cached_weight_n"] - weights[env_id]) < 0.001), None)
        if first_mass is None or first_mass > 1 or any(
            abs(row["guidance_cached_weight_n"] - weights[env_id]) >= 0.001
            for row in rows if row["step"] >= first_mass
        ):
            raise ValueError(f"Env {env_id} has stale guidance mass")
        last = rows[-1]
        remaining = [max(0.0, last["platform_final_goal"][axis]
                         - last["guidance_body_target"][axis]) if axis != 1 else 0.0
                     for axis in range(3)]
        tracking = [target - actual for target, actual in zip(
            last["guidance_body_target"], last["robot_position"])]
        if (env_id in extension and norm(remaining) <= 0.002
                and last["guidance_reference_age"] >= 3.0 and norm(tracking) < 0.01
                and min(last["foot_contact_force_z"]) >= 8.0
                and norm(last["robot_velocity"]) < 0.025
                and norm(last["robot_angular_velocity"]) < 0.1
                and max(last["guidance_command_limit_excess"]) < 1e-6):
            comfortable.append(env_id)
        release_events = []
        for index in range(1, len(rows)):
            current, previous = rows[index], rows[index - 1]
            leg = current["crawl_leg_index"]
            if current["crawl_phase"] > 0 and previous["crawl_phase"] == 0:
                forces = [row["foot_contact_force_z"][leg]
                          for row in rows[max(0, index - 10):index]]
                release_count += 1
                release_events.append((current["step"] * 0.02, leg))
                if len(forces) != 10 or max(forces) > 5.00001:
                    violations.append([env_id, "release", current["step"] * 0.02])
            if (previous["crawl_phase"] >= 1.0 and
                    (current["crawl_phase"] == 0 or leg != previous["crawl_leg_index"]
                     or current["platform_extension_completed"] > previous["platform_extension_completed"]
                     or (current["platform_hold_active"] and not previous["platform_hold_active"]))):
                old_leg = previous["crawl_leg_index"]
                reload_count += 1
                if not (previous["guidance_reload"] >= 0.999
                        and previous["guidance_loaded_age"] >= 0.19999
                        and previous["foot_contact_force_z"][old_leg] >= 8.0):
                    violations.append([env_id, "reload", current["step"] * 0.02])
        for index, (start, leg) in enumerate(release_events):
            end = release_events[index + 1][0] if index + 1 < len(release_events) else math.inf
            if not any(start <= row["step"] * 0.02 < end
                       and row["crawl_leg_index"] == leg and row["crawl_phase"] >= 1.0
                       and row["guidance_reload"] >= 0.999
                       and row["guidance_loaded_age"] >= 0.19999
                       and row["foot_contact_force_z"][leg] >= 8.0 for row in rows):
                violations.append([env_id, "no_recorded_reload", start])
        stage_times[env_id] = {
            "first_hold_s": next((row["step"] * 0.02 for row in rows
                                  if row["platform_hold_active"]), None),
            "extension_finished_s": next((row["step"] * 0.02 for row in rows
                                          if row["platform_extension_completed"] == 2), None),
            "final_stable_s": terminal_states[env_id]["platform_final_stable"],
        }

    gait = report["climb_gait_quality"]
    baseline = json.loads(args.baseline_verification.read_text())["quality"]
    old_comfortable = set(baseline["comfortable"])
    new_comfortable = set(comfortable)
    result = {
        "scope": "Used-seed 280s box-edge stage regression; not original-start acceptance",
        "seed": args.seed,
        "report_sha256": sha256(args.report),
        "report_bytes": args.report.stat().st_size,
        "candidate_source_sha256": source_hashes,
        "quality": {
            "ascent": ascent, "extension": extension, "comfortable": sorted(comfortable),
            "terminal_count": 32, "missing_terminals": 0,
            "old_center_goal_successes": report["successful_episodes"],
            "termination_reasons": report["termination_reasons"],
            "tripod_fraction": sum(count * fraction for count, fraction in zip(
                gait["samples"], gait["at_least_three_feet_fraction"])) / sum(gait["samples"]),
            "max_airtime_s": max(gait["max_continuous_airtime_s"]),
            "max_abs_vertical_speed_mps": max(gait["max_abs_base_vertical_speed"]),
            "max_single_foot_force_n": max(gait["max_single_foot_force_n"]),
            "torque_saturation_s_including_initialization": max(max(values) for values in
                report["joint_motion"]["torque_saturation_seconds_per_env_joint"]),
        },
        "release_reload": {"release_count": release_count, "reload_count": reload_count,
                           "violations": violations},
        "same_seed_baseline": {"retained": sorted(old_comfortable & new_comfortable),
                               "lost": sorted(old_comfortable - new_comfortable),
                               "new": sorted(new_comfortable - old_comfortable)},
        "stage_times": stage_times,
        "geometry_audit_pending": True,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    (args.output.parent / "actual-physics.json").write_text(
        json.dumps(report["actual_physics"], indent=2) + "\n"
    )
    (args.output.parent / "planning-inputs.json").write_text(
        json.dumps({key: value for key, value in report.items() if "inputs" in key}, indent=2) + "\n"
    )
    print(json.dumps({"comfortable": len(comfortable), "baseline_lost": len(old_comfortable - new_comfortable),
                      "release_reload_violations": len(violations), "output": str(args.output)}))


if __name__ == "__main__":
    main()
