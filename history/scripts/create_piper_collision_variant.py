"""Create a PIPER USD overlay with selective articulation self-collisions."""

import argparse
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path

from pxr import Sdf, Usd, UsdGeom, UsdPhysics


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/LeggedManip_Lab/LeggedManip_Lab/assets/go2_piper/go2_piper.usd"
ARM_BODIES = frozenset((*[f"link{index}" for index in range(7)], "end_effector"))


def create_variant(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    original = Usd.Stage.Open(str(source))
    if original is None:
        raise ValueError(f"Cannot open robot USD: {source}")
    root = original.GetDefaultPrim()
    bodies = {prim.GetName(): prim.GetPath() for prim in original.Traverse() if prim.HasAPI(UsdPhysics.RigidBodyAPI)}
    if not ARM_BODIES.issubset(bodies) or "base" not in bodies:
        raise ValueError("Expected the native GO2-PIPER articulation body names")
    adjacent = set()
    for prim in original.Traverse():
        if prim.IsA(UsdPhysics.Joint):
            joint = UsdPhysics.Joint(prim)
            first, second = joint.GetBody0Rel().GetTargets(), joint.GetBody1Rel().GetTargets()
            if first and second:
                adjacent.add(frozenset((first[0].name, second[0].name)))
    excluded = []
    for first, second in combinations(sorted(bodies), 2):
        if frozenset((first, second)) in adjacent or (first not in ARM_BODIES and second not in ARM_BODIES):
            excluded.append((first, second))
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(output))
    robot = stage.DefinePrim(root.GetPath(), root.GetTypeName())
    robot.GetReferences().AddReference(os.path.relpath(source, output.parent), root.GetPath())
    stage.SetDefaultPrim(robot)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.GetStageUpAxis(original))
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.GetStageMetersPerUnit(original))
    roots = [prim.GetPath() for prim in original.Traverse() if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
    if not roots:
        raise ValueError("Robot has no articulation root")
    for path in roots:
        stage.GetPrimAtPath(path).CreateAttribute(
            "physxArticulation:enabledSelfCollisions", Sdf.ValueTypeNames.Bool, custom=False,
        ).Set(True)
    for name, path in bodies.items():
        prim = stage.GetPrimAtPath(path)
        filtering = UsdPhysics.FilteredPairsAPI.Apply(prim)
        targets = set(filtering.GetFilteredPairsRel().GetTargets())
        for first, second in excluded:
            if name == first:
                targets.add(bodies[second])
            elif name == second:
                targets.add(bodies[first])
        filtering.CreateFilteredPairsRel().SetTargets(sorted(targets))
    preserved = 0
    for prim in original.Traverse():
        candidate = stage.GetPrimAtPath(prim.GetPath())
        for attribute in prim.GetAttributes():
            name = attribute.GetName()
            if name == "physxArticulation:enabledSelfCollisions":
                continue
            if candidate.GetAttribute(name).Get() != attribute.Get():
                raise ValueError(f"Unexpected robot property change: {prim.GetPath()}.{name}")
            preserved += 1
    stage.GetRootLayer().Save()
    return {
        "schema_version": 1, "robot": "go2_piper", "diagnostic_only": True,
        "source_usd": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output_usd": str(output), "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "body_count": len(bodies), "articulation_roots": [str(path) for path in roots],
        "enabled_self_collisions": True, "excluded_body_pairs": excluded,
        "preserved_attributes": preserved,
    }


def unmatched_contact_force(total, allowed):
    import torch

    if total.shape != allowed.shape or total.ndim != 3 or total.shape[-1] != 3:
        raise ValueError("Contact histories must have matching environment, time and xyz dimensions")
    return torch.linalg.vector_norm(total - allowed, dim=-1).amax(dim=1)


def unexpected_hand_contact(env, threshold=1.0):
    contacts = env.scene["contact_forces"]
    hand = env.scene["box_contact_hand"]
    if not hasattr(env, "piper_hand_contact_body_ids"):
        env.piper_hand_contact_body_ids = contacts.find_bodies(hand.body_names, preserve_order=True)[0]
        if not env.piper_hand_contact_body_ids:
            raise ValueError("Cannot match hand contact bodies to robot contacts")
    total = contacts.data.net_forces_w_history[:, :, env.piper_hand_contact_body_ids].sum(dim=2)
    allowed = hand.data.force_matrix_w_history.sum(dim=(2, 3))
    return unmatched_contact_force(total, allowed) > threshold


def configure_collision_candidate(
    config, usd_path, staged_precontact=False, contact_servo=False, contact_action_ramp_time=None,
):
    from isaaclab.envs.mdp import illegal_contact
    from isaaclab.managers import SceneEntityCfg, TerminationTermCfg

    usd_path = Path(usd_path).resolve()
    stage = Usd.Stage.Open(str(usd_path))
    if stage is None or stage.GetDefaultPrim().GetName() != "go2_piper":
        raise ValueError("Collision candidate must be a GO2-PIPER USD")
    roots = [prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
    if not roots or not all(prim.GetAttribute("physxArticulation:enabledSelfCollisions").Get() for prim in roots):
        raise ValueError("Collision candidate must enable articulation self-collisions")
    config.scene.robot.spawn.usd_path = str(usd_path)
    config.scene.robot.spawn.articulation_props.enabled_self_collisions = True
    config.scene.lazy_sensor_update = False
    config.scene.contact_forces.history_length = max(config.scene.contact_forces.history_length, config.decimation + 1)
    config.terminations.arm_contact = TerminationTermCfg(
        func=illegal_contact,
        params={"threshold": 1.0, "sensor_cfg": SceneEntityCfg("contact_forces", body_names="link[0-5]")},
    )
    failure_terms = ["arm_contact"]
    hand_other_contact = hasattr(config.scene, "box_contact_hand")
    if hand_other_contact:
        config.scene.box_contact_hand.history_length = config.scene.contact_forces.history_length
        config.terminations.hand_other_contact = TerminationTermCfg(func=unexpected_hand_contact, params={"threshold": 1.0})
        failure_terms.append("hand_other_contact")
    if contact_action_ramp_time is not None and not 0.0 < contact_action_ramp_time < float("inf"):
        raise ValueError("Contact action ramp time must be finite and positive")
    if contact_action_ramp_time is not None and not staged_precontact:
        raise ValueError("Contact action ramp time requires staged precontact")
    if staged_precontact:
        config.push_approach_distance = 0.08
        config.push_precontact_heights = (0.45, 0.45, 0.25, 0.10, 0.0)
        config.push_preapproach_hold_time = 0.5
        config.push_precontact_ik_gain = 0.2
        config.push_precontact_velocity_feedback_time = 0.02
        config.push_contact_hold_time = 0.10
        config.push_contact_action_ramp_time = contact_action_ramp_time or 0.50
        config.push_contact_approach_speed = 0.025
    if contact_servo:
        if not staged_precontact:
            raise ValueError("Contact servo requires staged precontact")
        config.actions.joint_pos.lock_arm_on_contact = False
        config.push_contact_force_target = 8.0
        config.push_contact_force_gain = 0.001
    for name in ("completion", "physical_failure"):
        reward = getattr(config.rewards, name, None)
        if reward is not None and "failure_terms" in reward.params:
            reward.params["failure_terms"] = (*reward.params["failure_terms"], *failure_terms)
    return {
        "usd_path": str(usd_path), "usd_sha256": hashlib.sha256(usd_path.read_bytes()).hexdigest(),
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "enabled_self_collisions": True, "arm_contact_threshold_n": 1.0,
        "arm_contact_body_pattern": "link[0-5]",
        "hand_other_contact_enabled": hand_other_contact,
        "hand_other_contact_threshold_n": 1.0 if hand_other_contact else None,
        "contact_history_length": config.scene.contact_forces.history_length,
        "lazy_sensor_update": config.scene.lazy_sensor_update,
        "staged_precontact": staged_precontact,
        "precontact_heights": list(config.push_precontact_heights) if staged_precontact else [],
        "precontact_position_only_stages": 2 if staged_precontact else 0,
        "precontact_ik_gain": config.push_precontact_ik_gain if staged_precontact else None,
        "precontact_velocity_feedback_time": config.push_precontact_velocity_feedback_time if staged_precontact else None,
        "contact_hold_time": config.push_contact_hold_time if staged_precontact else None,
        "contact_action_ramp_time": config.push_contact_action_ramp_time if staged_precontact else None,
        "approach_distance": config.push_approach_distance if staged_precontact else None,
        "contact_approach_speed": config.push_contact_approach_speed if staged_precontact else None,
        "contact_servo": contact_servo,
        "contact_force_target_n": config.push_contact_force_target if contact_servo else None,
        "contact_force_gain": config.push_contact_force_gain if contact_servo else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-usd", type=Path, default=SOURCE)
    parser.add_argument("--output-usd", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    if args.output_usd.exists() or args.output_json.exists():
        parser.error("Output USD and report must be new files")
    report = create_variant(args.source_usd, args.output_usd)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
    print(json.dumps({key: report[key] for key in ("body_count", "preserved_attributes", "enabled_self_collisions", "output_usd", "output_sha256")}))


if __name__ == "__main__":
    main()