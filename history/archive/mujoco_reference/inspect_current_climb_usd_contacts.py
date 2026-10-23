"""Inspect provenance-matched CLIMB USD contact and material opinions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from isaaclab.app import AppLauncher


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-physics", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    actual = json.loads(args.actual_physics.read_text())
    assets = actual["robot_asset_sha256"]
    for relative, expected in assets.items():
        if sha256(args.source_root / relative) != expected:
            parser.error(f"Asset SHA256 mismatch: {relative}")
    app = AppLauncher(headless=True).app
    try:
        from pxr import PhysxSchema, Usd, UsdPhysics

        stages = {}
        for relative in assets:
            if not relative.endswith(("go2_piper.usd", "go2_piper_selective_collision.usd",
                                      "go2_piper_physics.usd")):
                continue
            stage = Usd.Stage.Open(str(args.source_root / relative))
            if stage is None:
                raise RuntimeError(f"Could not open source USD: {relative}")
            details = []
            def inspect_prim(prim, source_instance_path=None):
                path = str(prim.GetPath())
                collision_schema = PhysxSchema.PhysxCollisionAPI(prim)
                contact_offset = collision_schema.GetContactOffsetAttr()
                rest_offset = collision_schema.GetRestOffsetAttr()
                attributes = {
                    attr.GetName(): str(attr.Get()) for attr in prim.GetAttributes()
                    if any(term in attr.GetName().lower()
                           for term in ("contactoffset", "restoffset", "staticfriction", "dynamicfriction", "restitution"))
                }
                relationships = {
                    rel.GetName(): [str(target) for target in rel.GetTargets()]
                    for rel in prim.GetRelationships() if "material" in rel.GetName().lower()
                }
                return {
                    "path": path,
                    "source_instance_path": source_instance_path,
                    "type": prim.GetTypeName(),
                    "active": prim.IsActive(),
                    "loaded": prim.IsLoaded(),
                    "instance": prim.IsInstance(),
                    "instance_proxy": prim.IsInstanceProxy(),
                    "prototype_path": str(prim.GetPrototype().GetPath()) if prim.IsInstance() else None,
                    "children": [child.GetName() for child in prim.GetAllChildren()],
                    "applied_api_schemas": list(prim.GetAppliedSchemas()),
                    "contact_material_attributes": attributes,
                    "collision_api_values": {
                        "physics_collision_api": prim.HasAPI(UsdPhysics.CollisionAPI),
                        "physx_collision_api": prim.HasAPI(PhysxSchema.PhysxCollisionAPI),
                        "contact_offset": contact_offset.Get(),
                        "contact_offset_authored": contact_offset.HasAuthoredValueOpinion(),
                        "rest_offset": rest_offset.Get(),
                        "rest_offset_authored": rest_offset.HasAuthoredValueOpinion(),
                    } if prim.HasAPI(UsdPhysics.CollisionAPI) else None,
                    "material_relationships": relationships,
                }

            for prim in stage.TraverseAll():
                item = inspect_prim(prim)
                if "foot" in item["path"].lower() or item["contact_material_attributes"] or item["material_relationships"]:
                    details.append(item)
                if prim.IsInstance() and "foot/collisions" in item["path"].lower():
                    details.extend(inspect_prim(child, item["path"])
                                   for child in Usd.PrimRange(prim.GetPrototype()))
            stages[relative] = {
                "used_layers": [layer.identifier for layer in stage.GetUsedLayers()],
                "prims": details,
            }
        report = {
            "kind": "composed_climb_usd_contact_opinions",
            "scope": "Composed source USD only; not live PhysX effective contact values",
            "actual_physics_sha256": sha256(args.actual_physics),
            "asset_sha256": assets,
            "script_sha256": sha256(Path(__file__)),
            "stages": stages,
            "limitations": [
                "Task-level terrain material and runtime PhysX defaults are not resolved by this USD inspection.",
                "An unauthored offset does not establish a zero effective PhysX contact or rest offset.",
            ],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"stage_prim_counts": {name: len(value["prims"]) for name, value in stages.items()},
                          "output": str(args.output)}))
    finally:
        app.close()


if __name__ == "__main__":
    main()
