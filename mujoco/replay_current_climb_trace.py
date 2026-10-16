"""Replay a short recorded Isaac CLIMB joint-target window in MuJoCo."""

from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path

import mujoco
import numpy as np

from reconfigurable_navigation.piper_box_runtime import make_episode
from reconfigurable_navigation.piper_locomotion_runtime import JOINT_NAMES
from reconfigurable_navigation.piper_robot_profile import COLLISION_PROFILE_PATH, PROFILE_PATH


ROOT = Path(__file__).resolve().parent
LEGS = ("FL", "FR", "RL", "RR")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_trace(path: Path, end_step: int) -> tuple[list[str], list[dict]]:
    with path.open("rb") as source, mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
        names_start = mapped.rfind(b'"joint_names":')
        trace_start = mapped.find(b'"trace_env0":[')
        if names_start < 0 or trace_start < 0:
            raise ValueError("Missing joint names or env0 trace")
        decoder = json.JSONDecoder()
        names, _ = decoder.raw_decode(mapped[names_start + len(b'"joint_names":'):names_start + 4096].decode())
        position = trace_start + len(b'"trace_env0":[')
        samples = []
        for step in range(end_step + 1):
            sample, used = decoder.raw_decode(mapped[position:position + 131072].decode())
            if sample["step"] != step or sample["env_id"] != 0:
                raise ValueError(f"Nonconsecutive env0 trace at step {step}")
            samples.append(sample)
            position += used + 1
        return names, samples


def foot_loads(runtime) -> np.ndarray:
    loads = np.zeros(4)
    feet = {runtime.model.body(f"{leg}_foot").id: index for index, leg in enumerate(LEGS)}
    wrench = np.zeros(6)
    for contact_index, contact in enumerate(runtime.data.contact[:runtime.data.ncon]):
        first, second = int(contact.geom1), int(contact.geom2)
        first_body = int(runtime.model.geom_bodyid[first])
        second_body = int(runtime.model.geom_bodyid[second])
        if first in runtime.terrain_geom_ids:
            foot_index = feet.get(second_body)
        elif second in runtime.terrain_geom_ids:
            foot_index = feet.get(first_body)
        else:
            continue
        if foot_index is None:
            continue
        mujoco.mj_contactForce(runtime.model, runtime.data, contact_index, wrench)
        loads[foot_index] += abs((contact.frame.reshape(3, 3).T @ wrench[:3])[2])
    return loads


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isaac-report", required=True, type=Path)
    parser.add_argument("--expected-isaac-sha256", required=True)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--stage-bank", required=True, type=Path)
    parser.add_argument("--start-step", type=int, default=200)
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--control-mode", choices=("joint-target", "recorded-torque", "recorded-substep-torque", "source-substep-leg-pd"), default="joint-target")
    parser.add_argument("--torque-shift", type=int, choices=(0, 1), default=1)
    parser.add_argument("--isaac-substeps", type=Path)
    parser.add_argument("--expected-substeps-sha256")
    parser.add_argument("--leg-delay-steps", type=int, choices=range(5), default=4)
    parser.add_argument("--contact-margin-m", type=float, default=0.0)
    parser.add_argument("--contact-time-constant-s", type=float)
    parser.add_argument("--terrain-sliding-friction", type=float)
    parser.add_argument("--match-actual-base-mass", action="store_true")
    parser.add_argument("--match-actual-base-inertia", action="store_true")
    parser.add_argument("--record-substeps", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.start_step < 2 or args.steps < 1:
        parser.error("Use a new output path, start step >= 2 and positive step count")
    if args.record_substeps and args.control_mode != "source-substep-leg-pd":
        parser.error("Substep comparison requires source-substep-leg-pd mode")
    if args.terrain_sliding_friction is not None and (not np.isfinite(args.terrain_sliding_friction)
                                                       or args.terrain_sliding_friction <= 0):
        parser.error("Terrain sliding friction must be finite and positive")
    if args.match_actual_base_inertia and not args.match_actual_base_mass:
        parser.error("Base inertia scaling requires matching the actual base mass")
    report_sha256 = sha256(args.isaac_report)
    if report_sha256 != args.expected_isaac_sha256:
        parser.error("Isaac report SHA256 mismatch")
    plan = json.loads((args.candidate / "plan.json").read_text())
    if sha256(args.policy) != plan["actor_sha256"] or sha256(args.stage_bank) != plan["stage_bank_sha256"]:
        parser.error("Frozen actor or stage bank does not match the candidate")
    actual_physics_path = args.candidate / "actual-physics.json"
    actual_physics = json.loads(actual_physics_path.read_text())
    mass_provenance = actual_physics["stage_mass_provenance"]
    source_base_mass = mass_provenance["actual_after_startup"][0][mass_provenance["body_names"].index("base")]
    bank = json.loads(args.stage_bank.read_text())
    names, samples = load_trace(args.isaac_report, args.start_step + args.steps)
    if names != bank["joint_names"] or len(names) != 18 or len(samples[0]["joint_position"]) != 18:
        parser.error("Isaac joint order differs from the frozen stage bank")
    source_substeps = None
    substeps_sha256 = None
    if args.control_mode in ("recorded-substep-torque", "source-substep-leg-pd"):
        if args.isaac_substeps is None or args.expected_substeps_sha256 is None:
            parser.error("Substep torque replay requires --isaac-substeps and --expected-substeps-sha256")
        substeps_sha256 = sha256(args.isaac_substeps)
        if substeps_sha256 != args.expected_substeps_sha256:
            parser.error("Isaac substeps SHA256 mismatch")
        source_substeps = json.loads(args.isaac_substeps.read_text())
        trace = source_substeps["trace"]
        if (source_substeps["joint_names"] != names or source_substeps["seed"] != 27302
                or source_substeps["physics_dt"] != 0.005
                or source_substeps["control_decimation"] != 4):
            parser.error("Substep source contract mismatch")
        for step in range(args.start_step, args.start_step + args.steps):
            block = trace[(step - 200) * 4:(step - 199) * 4]
            if len(block) != 4 or [(v["step"], v["substep"]) for v in block] != [(step, i) for i in range(4)]:
                parser.error(f"Missing substep block for step {step}")
            if block[-1]["joint_position"] != samples[step + 1]["joint_position"]:
                parser.error(f"Substep/report phase mismatch at step {step}")

    runtime = make_episode("climb", args.policy, 27302, native_collisions=True,
                           contact_margin=args.contact_margin_m,
                           contact_time_constant=args.contact_time_constant_s)
    runtime.actuator_delay_steps[:12] = args.leg_delay_steps
    model, data = runtime.model, runtime.data
    if args.terrain_sliding_friction is not None:
        for name in ("floor", "support_box"):
            model.geom_friction[model.geom(name).id, 0] = args.terrain_sliding_friction
    base_id = model.body("base_link").id
    model_base_mass_before = float(model.body_mass[base_id])
    model_base_inertia_before = model.body_inertia[base_id].copy()
    if args.match_actual_base_mass:
        model.body_mass[base_id] = source_base_mass
        if args.match_actual_base_inertia:
            model.body_inertia[base_id] *= source_base_mass / model_base_mass_before
        mujoco.mj_setConst(model, data)
    initial = samples[args.start_step]
    position = dict(zip(names, initial["joint_position"], strict=True))
    velocity = dict(zip(names, initial["joint_velocity"], strict=True))
    data.qpos[:7] = [*initial["robot_position"], *initial["robot_quaternion"]]
    data.qvel[:6] = [*initial["robot_velocity"], *initial["robot_angular_velocity"]]
    data.qpos[runtime.joint_qpos_adr] = [position[name] for name in JOINT_NAMES]
    data.qvel[runtime.joint_dof_adr] = [velocity[name] for name in JOINT_NAMES]
    initial_torque = dict(zip(names, initial["applied_torque"], strict=True))
    data.ctrl[:] = [initial_torque[name] for name in JOINT_NAMES]
    mujoco.mj_forward(model, data)
    source_feet = np.asarray(initial["feet_position"])
    foot_body_ids = [model.body(f"{leg}_foot").id for leg in LEGS]
    initial_foot_error = np.linalg.norm(data.xpos[foot_body_ids] - source_feet, axis=1)

    runtime.target_history.clear()
    for step in (args.start_step - 2, *([args.start_step - 1] * 4)):
        target = dict(zip(names, samples[step]["joint_position_target"], strict=True))
        runtime.target_history.append(np.asarray([target[name] for name in JOINT_NAMES]))
    runtime._fresh_targets = False
    substeps = {"count": 0, "leg_torque_saturation": 0, "arm_torque_saturation": 0,
                "peak_foot_contact_force_n": 0.0, "peak_base_vertical_speed_mps": 0.0}

    def on_physics_step() -> None:
        substeps["count"] += 1
        substeps["leg_torque_saturation"] += int(np.any(np.isclose(data.ctrl[:12], runtime.ctrl_low[:12])
                                                       | np.isclose(data.ctrl[:12], runtime.ctrl_high[:12])))
        substeps["arm_torque_saturation"] += int(np.any(np.isclose(data.ctrl[12:], runtime.ctrl_low[12:])
                                                       | np.isclose(data.ctrl[12:], runtime.ctrl_high[12:])))
        substeps["peak_foot_contact_force_n"] = max(substeps["peak_foot_contact_force_n"],
                                                     float(foot_loads(runtime).max()))
        substeps["peak_base_vertical_speed_mps"] = max(substeps["peak_base_vertical_speed_mps"],
                                                        abs(float(data.qvel[2])))

    runtime.on_physics_step = on_physics_step
    substep_rows = []

    def simulate_recorded_torque(efforts: list[np.ndarray], leg_targets: list[np.ndarray] | None = None,
                                 source_rows: list[dict] | None = None) -> None:
        for index, effort in enumerate(efforts):
            if leg_targets is not None:
                effort = effort.copy()
                effort[:12] = (30.0 * (leg_targets[index] - data.qpos[runtime.joint_qpos_adr[:12]])
                               - 0.6 * data.qvel[runtime.joint_dof_adr[:12]])
            data.ctrl[:] = np.clip(effort, runtime.ctrl_low, runtime.ctrl_high)
            previous_joint_position = data.qpos[runtime.joint_qpos_adr].copy()
            mujoco.mj_step(model, data)
            limited_joint_velocity = np.clip(data.qvel[runtime.joint_dof_adr],
                                             -runtime.joint_velocity_limits, runtime.joint_velocity_limits)
            data.qvel[runtime.joint_dof_adr] = limited_joint_velocity
            data.qpos[runtime.joint_qpos_adr] = previous_joint_position + limited_joint_velocity * model.opt.timestep
            mujoco.mj_forward(model, data)
            runtime.on_safety_step()
            on_physics_step()
            if source_rows is not None:
                source_row = source_rows[index]
                substep_rows.append({
                    "step": source_row["step"], "substep": source_row["substep"],
                    "root_position_error_xyz_m": (data.qpos[:3] - source_row["root_position"]).tolist(),
                    "root_quaternion_mujoco": data.qpos[3:7].tolist(),
                    "root_quaternion_isaac": source_row["root_quaternion"],
                    "joint_position_max_error_rad": float(np.max(np.abs(
                        data.qpos[runtime.joint_qpos_adr]
                        - [dict(zip(names, source_row["joint_position"], strict=True))[name]
                           for name in JOINT_NAMES]))),
                    "isaac_foot_force_z_n": source_row["foot_contact_force_z"],
                    "mujoco_foot_loads_n": foot_loads(runtime).tolist(),
                    "isaac_feet_position_m": source_row["feet_position"],
                    "mujoco_feet_position_m": data.xpos[foot_body_ids].tolist(),
                    "isaac_leg_torque_nm": [dict(zip(names, source_row["applied_torque"], strict=True))[name]
                                             for name in JOINT_NAMES[:12]],
                    "mujoco_leg_torque_nm": data.ctrl[:12].tolist(),
                })

    trace = []
    stop_reason = "window_complete"
    simulated_steps = 0
    for step in range(args.start_step, args.start_step + args.steps):
        source = samples[step]
        target = dict(zip(names, source["joint_position_target"], strict=True))
        source_position = dict(zip(names, source["joint_position"], strict=True))
        measured = data.qpos[runtime.joint_qpos_adr]
        expected = np.asarray([source_position[name] for name in JOINT_NAMES])
        loads = foot_loads(runtime)
        trace.append({
            "step": step, "time_s": step * runtime.control_dt,
            "isaac_crawl_phase": source["crawl_phase"],
            "isaac_crawl_lifted": source["crawl_lifted"],
            "isaac_contacts": source["crawl_contacts"],
            "isaac_foot_force_z_n": source["foot_contact_force_z"],
            "isaac_feet_position_m": source["feet_position"],
            "mujoco_feet_position_m": data.xpos[foot_body_ids].tolist(),
            "isaac_root_position_m": source["robot_position"],
            "mujoco_root_position_m": data.qpos[:3].tolist(),
            "root_position_error_xyz_m": (data.qpos[:3] - source["robot_position"]).tolist(),
            "mujoco_foot_loads_n": loads.tolist(),
            "mujoco_loaded_feet_2n": int((loads > 2.0).sum()),
            "root_position_error_m": float(np.linalg.norm(data.qpos[:3] - source["robot_position"])),
            "joint_position_max_error_rad": float(np.max(np.abs(measured - expected))),
            "joint_position_error_rad": (measured - expected).tolist(),
            "isaac_applied_torque_nm": source["applied_torque"],
            "mujoco_previous_substep_torque_nm": data.ctrl.tolist(),
            "self_collision": runtime.self_collision,
            "base_contact": runtime.base_contacts_terrain(),
        })
        if runtime.self_collision is not None or runtime.base_contacts_terrain():
            stop_reason = "self_collision" if runtime.self_collision is not None else "base_contact"
            break
        if args.control_mode == "joint-target":
            runtime._simulate_target(np.asarray([target[name] for name in JOINT_NAMES]))
        elif args.control_mode == "recorded-torque":
            recorded = dict(zip(names, samples[step + args.torque_shift]["applied_torque"], strict=True))
            effort = np.asarray([recorded[name] for name in JOINT_NAMES])
            simulate_recorded_torque([effort] * runtime.decimation)
        else:
            block = source_substeps["trace"][(step - 200) * 4:(step - 199) * 4]
            efforts = [
                np.asarray([dict(zip(names, sample["applied_torque"], strict=True))[name]
                            for name in JOINT_NAMES]) for sample in block
            ]
            if args.control_mode == "source-substep-leg-pd":
                leg_targets = [np.asarray([dict(zip(names, sample["joint_position_target"], strict=True))[name]
                                           for name in JOINT_NAMES[:12]]) for sample in block]
                simulate_recorded_torque(efforts, leg_targets, block if args.record_substeps else None)
            else:
                simulate_recorded_torque(efforts)
        simulated_steps += 1

    final_source = samples[args.start_step + simulated_steps]
    final_position = dict(zip(names, final_source["joint_position"], strict=True))
    final_self_collision = runtime.self_collision
    final_base_contact = runtime.base_contacts_terrain()
    if stop_reason == "window_complete" and (final_self_collision is not None or final_base_contact):
        stop_reason = "self_collision" if final_self_collision is not None else "base_contact"
    result = {
        "scope": "Source-matched recorded-control MuJoCo CLIMB window; not a port of StageGuidance or skill acceptance",
        "source_report_sha256": report_sha256,
        "source_substeps_sha256": substeps_sha256,
        "source_candidate_plan_sha256": sha256(args.candidate / "plan.json"),
        "source_actual_physics_sha256": sha256(actual_physics_path),
        "actor_sha256": sha256(args.policy), "stage_bank_sha256": sha256(args.stage_bank),
        "mujoco_xml_sha256": sha256(ROOT / "robots/go2_piper/go2piper.xml"),
        "mujoco_profile_sha256": sha256(PROFILE_PATH),
        "mujoco_collision_profile_sha256": sha256(COLLISION_PROFILE_PATH),
        "script_sha256": sha256(Path(__file__)),
        "start_step": args.start_step, "requested_steps": args.steps,
        "control_mode": args.control_mode, "torque_shift": args.torque_shift,
        "leg_delay_steps": args.leg_delay_steps,
        "contact_margin_m": args.contact_margin_m,
        "contact_time_constant_s": args.contact_time_constant_s,
        "terrain_sliding_friction": args.terrain_sliding_friction,
        "match_actual_base_mass": args.match_actual_base_mass,
        "match_actual_base_inertia": args.match_actual_base_inertia,
        "source_base_mass_kg": source_base_mass,
        "model_base_mass_before_kg": model_base_mass_before,
        "model_base_mass_after_kg": float(model.body_mass[base_id]),
        "model_base_inertia_before_kg_m2": model_base_inertia_before.tolist(),
        "model_base_inertia_after_kg_m2": model.body_inertia[base_id].tolist(),
        "record_substeps": args.record_substeps,
        "initial_foot_position_error_m": initial_foot_error.tolist(),
        "stop_reason": stop_reason, "substeps": substeps, "trace": trace,
        "substep_rows": substep_rows,
        "final_state": {
            "source_step": final_source["step"],
            "root_position_error_m": float(np.linalg.norm(data.qpos[:3] - final_source["robot_position"])),
            "joint_position_max_error_rad": float(np.max(np.abs(
                data.qpos[runtime.joint_qpos_adr]
                - [final_position[name] for name in JOINT_NAMES]))),
            "loaded_feet_2n": int((foot_loads(runtime) > 2.0).sum()),
            "self_collision": final_self_collision,
            "base_contact": final_base_contact,
        },
        "limitations": ["The initial contact solver state and actuator delays are reconstructed from samples.",
                        "The recorded joint targets bypass the 304-input actor and StageGuidance.",
                        "The 50Hz recorded-torque mode holds one torque sample for four physics steps; the substep mode replays measured 5ms torques without PD feedback to MuJoCo state.",
                        "The source-substep-leg-pd mode closes the leg PD loop around MuJoCo state using recorded effective targets; arm torques remain recorded and stage guidance is not ported.",
                        "A short window cannot establish full-stage CLIMB sim2sim success."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"stop_reason": stop_reason, "steps": len(trace), "initial_foot_error_m": max(initial_foot_error)}))


if __name__ == "__main__":
    main()
