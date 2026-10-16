"""Conservative base collider and sampled support-path geometry; not a safety proof."""
import torch
from .climb_leg_kinematics import rotate_vector


def base_collision_bounds(path, device="cpu"):
    """Enclose the USD base collision mesh in base coordinates, including instances."""
    from pxr import Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(str(path))
    base = stage.GetPrimAtPath("/go2_piper/base")
    cache = UsdGeom.XformCache()
    points = []
    for prim in Usd.PrimRange(base, Usd.TraverseInstanceProxies()):
        if not prim.IsA(UsdGeom.Mesh):
            continue
        ancestor = prim
        collision = False
        while ancestor != base:
            if ancestor.HasAPI(UsdPhysics.CollisionAPI):
                collision |= bool(UsdPhysics.CollisionAPI(ancestor).GetCollisionEnabledAttr().Get())
            ancestor = ancestor.GetParent()
        if collision:
            transform = cache.ComputeRelativeTransform(prim, base)[0]
            points.extend(list(transform.Transform(p)) for p in UsdGeom.Mesh(prim).GetPointsAttr().Get())
    if not points:
        raise ValueError("No base collision mesh found; cannot enable clearance guard")
    points = torch.tensor(points, device=device)
    return torch.stack((points.amin(0), points.amax(0)))


def base_box_gap(position, quaternion, body_bounds, box_bounds):
    """Largest separating-axis gap for oriented base bounds versus the terrain box.

    Negative means intersecting bounding boxes. Positive is a conservative lower
    bound on separation, not the exact distance to the actual convex collider.
    Arbitrary leading pose batch dimensions are supported.
    """
    unit = torch.eye(3, device=position.device, dtype=position.dtype)
    axes = rotate_vector(quaternion[..., None, :], unit.expand(*position.shape[:-1], 3, 3))
    center = position + rotate_vector(quaternion, ((body_bounds[..., 0, :]+body_bounds[..., 1, :])/2).expand_as(position))
    half = (body_bounds[..., 1, :]-body_bounds[..., 0, :])/2
    box_center = (box_bounds[..., 0, :]+box_bounds[..., 1, :])/2
    box_half = (box_bounds[..., 1, :]-box_bounds[..., 0, :])/2
    cross = torch.cross(axes[..., :, None, :].expand(*axes.shape[:-2], 3, 3, 3),
                        unit.expand(*axes.shape[:-2], 3, 3, 3), dim=-1).flatten(-3, -2)
    candidates = torch.cat((unit.expand_as(axes), axes, cross), -2)
    norms = candidates.norm(dim=-1)
    candidates = candidates/norms.clamp_min(1e-8)[..., None]
    delta = ((center-box_center)[..., None, :]*candidates).sum(-1).abs()
    radius = ((candidates[..., :, None, :]*axes[..., None, :, :]).sum(-1).abs()*half[..., None, :]).sum(-1)
    radius += (candidates.abs()*box_half[..., None, :]).sum(-1)
    gap = delta-radius
    return torch.where(norms > 1e-6, gap, torch.full_like(gap, -1e6)).amax(-1)


def support_path_geometry(model, feet, origin, quaternion, positions, rotations,
                          bias, bounds, body_bounds, box_bounds):
    """Check21 points along the same straight/nlerp body path used at runtime.

    Fixed feet and measured torque bias are estimates. Tracking error, changes
    in support force, other links, and between-sample collisions remain unproven.
    """
    t = torch.linspace(0., 1., 21, device=feet.device, dtype=feet.dtype)[None, None, :, None]
    p = torch.lerp(origin[:, None, None], positions[:, :, None], t)
    q = torch.lerp(quaternion[:, None, None], rotations[:, :, None], t)
    q = q/q.norm(dim=-1, keepdim=True).clamp_min(1e-8)
    gap = base_box_gap(p, q, body_bounds, box_bounds[:, None, None]).amin(-1)
    local = rotate_vector(q[..., None, :], feet[:, None, None]-p[..., None, :], inverse=True)
    joints = model.inverse(local)
    command = joints+bias[:, None, None]
    lo, hi = bounds[..., 0][:, None, None], bounds[..., 1][:, None, None]
    margin = torch.minimum(torch.minimum(joints-lo, hi-joints)-.01,
                           torch.minimum(command-lo, hi-command)).amin(dim=(-1, -2, -3))
    error = (model.forward(joints)-local).norm(dim=-1).amax(dim=(-1, -2))
    return gap, margin, error


def leg_collision_bounds(path, device="cpu"):
    """Conservatively enclose each hip/thigh/calf primitive in its link frame."""
    from pxr import Usd, UsdGeom, UsdPhysics, Gf
    from itertools import product
    stage = Usd.Stage.Open(str(path))
    cache = UsdGeom.XformCache()
    legs = []
    for leg in ("FL", "FR", "RL", "RR"):
        parts = []
        for part in ("hip", "thigh", "calf"):
            body = stage.GetPrimAtPath("/go2_piper/"+leg+"_"+part)
            points = []
            for prim in Usd.PrimRange(body, Usd.TraverseInstanceProxies()):
                if not prim.HasAPI(UsdPhysics.CollisionAPI):
                    continue
                if not UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get():
                    continue
                if prim.IsA(UsdGeom.Cube):
                    half = [float(UsdGeom.Cube(prim).GetSizeAttr().Get())/2]*3
                elif prim.IsA(UsdGeom.Cylinder):
                    cylinder = UsdGeom.Cylinder(prim)
                    half = [float(cylinder.GetRadiusAttr().Get())]*3
                    half["XYZ".index(cylinder.GetAxisAttr().Get())] = float(cylinder.GetHeightAttr().Get())/2
                else:
                    raise ValueError(f"Unsupported leg collider: {prim.GetPath()}")
                transform = cache.ComputeRelativeTransform(prim, body)[0]
                points.extend(list(transform.Transform(Gf.Vec3d(*(sign[i]*half[i] for i in range(3)))))
                              for sign in product((-1, 1), repeat=3))
            if not points:
                raise ValueError(f"No primitive collision geometry for {leg}_{part}")
            points = torch.tensor(points, device=device)
            parts.append(torch.stack((points.amin(0), points.amax(0))))
        legs.append(torch.stack(parts))
    return torch.stack(legs)


def multiply_quaternion(a, b):
    aw, av, bw, bv = a[..., :1], a[..., 1:], b[..., :1], b[..., 1:]
    vector = aw*bv+bw*av+torch.cross(av.expand_as(bv), bv, dim=-1)
    return torch.cat((aw*bw-(av*bv).sum(-1, keepdim=True), vector), -1)


def leg_link_poses(model, joints, position, quaternion):
    """World hip/thigh/calf frame poses, matching the audited GO2 joint chain."""
    hip, thigh, calf = joints.unbind(-1)
    zeros = torch.zeros_like(hip)
    rx = torch.stack(((hip/2).cos(), (hip/2).sin(), zeros, zeros), -1)
    ry = torch.stack(((thigh/2).cos(), zeros, (thigh/2).sin(), zeros), -1)
    ryk = torch.stack((((thigh+calf)/2).cos(), zeros, ((thigh+calf)/2).sin(), zeros), -1)
    rt, rc = multiply_quaternion(rx, ry), multiply_quaternion(rx, ryk)
    hp = model.origins.expand_as(joints)
    lateral = torch.stack((zeros, model.lateral.expand_as(zeros), zeros), -1)
    tp = hp+rotate_vector(rx, lateral)
    down = torch.stack((zeros, zeros, -model.lengths[:, 0].expand_as(zeros)), -1)
    cp = tp+rotate_vector(rt, down)
    local_position = torch.stack((hp, tp, cp), -2)
    local_rotation = torch.stack((rx, rt, rc), -2)
    rotation = multiply_quaternion(quaternion[..., None, None, :].expand_as(local_rotation), local_rotation)
    position = position[..., None, None, :]+rotate_vector(quaternion[..., None, None, :], local_position)
    return position, rotation


def leg_path_gap(model, feet, origin, quaternion, positions, rotations, link_bounds, box_bounds):
    """Minimum hip/thigh/calf bounding-box gap over the21 nominal pose samples."""
    t = torch.linspace(0., 1., 21, device=feet.device, dtype=feet.dtype)[None, None, :, None]
    p = torch.lerp(origin[:, None, None], positions[:, :, None], t)
    q = torch.lerp(quaternion[:, None, None], rotations[:, :, None], t)
    q = q/q.norm(dim=-1, keepdim=True).clamp_min(1e-8)
    local = rotate_vector(q[..., None, :], feet[:, None, None]-p[..., None, :], inverse=True)
    joints = model.inverse(local)
    link_position, link_rotation = leg_link_poses(model, joints, p, q)
    if isinstance(link_bounds, dict):
        gap = primitive_box_gap(link_position, link_rotation, link_bounds, box_bounds[:, None, None, None, None])
    else:
        gap = base_box_gap(link_position, link_rotation, link_bounds, box_bounds[:, None, None, None, None])
    return gap.amin(dim=(-1, -2, -3))


def leg_collision_primitives(path, device="cpu"):
    """Keep USD cylinder radii and primitive frames instead of enclosing boxes."""
    from pxr import Usd, UsdGeom, UsdPhysics, Gf
    stage = Usd.Stage.Open(str(path))
    cache = UsdGeom.XformCache()
    centers, rotations, halves, cylinders = [], [], [], []
    for leg in ("FL", "FR", "RL", "RR"):
        for part in ("hip", "thigh", "calf"):
            body = stage.GetPrimAtPath("/go2_piper/"+leg+"_"+part)
            colliders = [p for p in Usd.PrimRange(body, Usd.TraverseInstanceProxies())
                         if p.HasAPI(UsdPhysics.CollisionAPI)
                         and UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get()]
            if len(colliders) != 1:
                raise ValueError("Expected exactly one GO2 leg primitive per link")
            prim = colliders[0]
            transform = Gf.Transform(cache.ComputeRelativeTransform(prim, body)[0])
            scale = list(transform.GetScale())
            rotation = transform.GetRotation().GetQuat()
            centers.append(list(transform.GetTranslation()))
            rotations.append([rotation.GetReal(), *rotation.GetImaginary()])
            cylinder = prim.IsA(UsdGeom.Cylinder)
            if cylinder:
                shape = UsdGeom.Cylinder(prim)
                if shape.GetAxisAttr().Get() != "Z" or abs(scale[0]-scale[1]) > 1e-6:
                    raise ValueError("Expected a circular Z cylinder in its primitive frame")
                radius = float(shape.GetRadiusAttr().Get())
                half = [radius, radius, float(shape.GetHeightAttr().Get())/2]
            elif prim.IsA(UsdGeom.Cube):
                half = [float(UsdGeom.Cube(prim).GetSizeAttr().Get())/2]*3
            else:
                raise ValueError("Unsupported leg collision shape")
            halves.append([half[i]*scale[i] for i in range(3)])
            cylinders.append(cylinder)
    return dict(center=torch.tensor(centers, device=device).reshape(4, 3, 3),
                rotation=torch.tensor(rotations, device=device).reshape(4, 3, 4),
                half=torch.tensor(halves, device=device).reshape(4, 3, 3),
                cylinder=torch.tensor(cylinders, device=device).reshape(4, 3))


def primitive_box_gap(link_position, link_rotation, primitives, box_bounds):
    """Conservative separating-axis gap with exact primitive support radii.

    A positive gap proves separation on that axis. The finite axis set may still
    reject separated shapes, but does not substitute square corners for a cylinder.
    """
    position = link_position + rotate_vector(link_rotation,
        primitives["center"].expand_as(link_position))
    quaternion = multiply_quaternion(link_rotation,
        primitives["rotation"].expand_as(link_rotation))
    unit = torch.eye(3, device=position.device, dtype=position.dtype)
    axes = rotate_vector(quaternion[..., None, :], unit.expand(*position.shape[:-1], 3, 3))
    center = (box_bounds[..., 0, :]+box_bounds[..., 1, :])/2
    half_box = (box_bounds[..., 1, :]-box_bounds[..., 0, :])/2
    cross = torch.cross(axes[..., :, None, :].expand(*axes.shape[:-2], 3, 3, 3),
                        unit.expand(*axes.shape[:-2], 3, 3, 3), dim=-1).flatten(-3, -2)
    # Extra center-to-box directions help find separating planes near edges.
    nearest = torch.maximum(torch.minimum(position, box_bounds[..., 1, :]), box_bounds[..., 0, :])
    directions = torch.cat((unit.expand_as(axes), axes, cross, (position-nearest)[..., None, :]), -2)
    norms = directions.norm(dim=-1)
    directions = directions/norms.clamp_min(1e-8)[..., None]
    projection = (directions[..., :, None, :]*axes[..., None, :, :]).sum(-1)
    half = primitives["half"]
    box_radius = (projection.abs()*half[..., None, :]).sum(-1)
    cylinder_radius = (projection[..., :2].norm(dim=-1)*half[..., 0, None]
                       + projection[..., 2].abs()*half[..., 2, None])
    radius = torch.where(primitives["cylinder"][..., None], cylinder_radius, box_radius)
    radius += (directions.abs()*half_box[..., None, :]).sum(-1)
    gap = ((position-center)[..., None, :]*directions).sum(-1).abs()-radius
    return torch.where(norms > 1e-6, gap, torch.full_like(gap, -1e6)).amax(-1)
