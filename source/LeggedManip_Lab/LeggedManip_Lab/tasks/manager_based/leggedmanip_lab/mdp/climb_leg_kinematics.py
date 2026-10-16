"""GO2 leg position kinematics, validated against the active Isaac USD geometry."""

import torch


def rotate_vector(quaternion, vector, inverse=False):
    imaginary = quaternion[..., 1:].expand_as(vector)
    if inverse:
        imaginary = -imaginary
    cross = torch.cross(imaginary, vector, dim=-1)
    return vector + 2 * (quaternion[..., :1] * cross + torch.cross(imaginary, cross, dim=-1))


class LegKinematics:
    legs = ("FL", "FR", "RL", "RR")

    def __init__(self, geometry, device="cpu", dtype=torch.float32):
        self.geometry = geometry
        self.origins = torch.tensor(geometry["hip_origins"], device=device, dtype=dtype)
        self.lateral = torch.tensor(geometry["hip_lateral_offsets"], device=device, dtype=dtype)
        self.lengths = torch.tensor(geometry["link_lengths"], device=device, dtype=dtype)

    def reordered(self, legs):
        """Reorder measured geometry, never reflect the physical robot or actions."""
        if len(legs) != 4 or set(legs) != set(self.legs):
            raise ValueError("Expected each physical leg exactly once")
        indices = [self.legs.index(leg) for leg in legs]
        geometry = {key: [values[i] for i in indices] for key, values in self.geometry.items()}
        model = LegKinematics(geometry, self.origins.device, self.origins.dtype)
        model.legs = tuple(legs)
        return model

    @classmethod
    def from_usd(cls, path, device="cpu", dtype=torch.float32):
        from pxr import Usd, UsdPhysics
        stage = Usd.Stage.Open(str(path))
        joints = {prim.GetName(): prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)}
        geometry = dict(hip_origins=[], hip_lateral_offsets=[], link_lengths=[])

        def close(a, b):
            return all(abs(float(x) - float(y)) < 1e-6 for x, y in zip(a, b))

        def quat(value):
            return [value.GetReal(), *value.GetImaginary()]

        for leg in cls.legs:
            positions = []
            for part, axis, parent in (("hip", "X", "base"), ("thigh", "Y", leg + "_hip"),
                                       ("calf", "Y", leg + "_thigh"), ("foot", None, leg + "_calf")):
                prim = joints[leg + "_" + part + "_joint"]
                get = lambda name: prim.GetAttribute("physics:" + name).Get()
                if axis is not None:
                    assert prim.IsA(UsdPhysics.RevoluteJoint) and get("axis") == axis
                    assert close(quat(get("localRot0")), [1, 0, 0, 0])
                    assert close(quat(get("localRot1")), [1, 0, 0, 0])
                else:
                    assert prim.IsA(UsdPhysics.FixedJoint)
                    assert close(quat(get("localRot0")), quat(get("localRot1")))
                assert close(get("localPos1"), [0, 0, 0])
                assert prim.GetRelationship("physics:body0").GetTargets()[0].name == parent
                assert prim.GetRelationship("physics:body1").GetTargets()[0].name == leg + "_" + part
                positions.append([float(v) for v in get("localPos0")])
            hip, lateral, thigh, calf = positions
            assert close([lateral[0], lateral[2]], [0, 0])
            assert close(thigh[:2], [0, 0]) and close(calf[:2], [0, 0])
            assert thigh[2] < 0 and calf[2] < 0
            geometry["hip_origins"].append(hip)
            geometry["hip_lateral_offsets"].append(lateral[1])
            geometry["link_lengths"].append([-thigh[2], -calf[2]])
        return cls(geometry, device, dtype)

    def forward(self, joints):
        hip, thigh, knee = joints.unbind(dim=-1)
        upper, lower = self.lengths.unbind(dim=-1)
        x = -upper * thigh.sin() - lower * (thigh + knee).sin()
        sagittal_z = -upper * thigh.cos() - lower * (thigh + knee).cos()
        y = self.lateral * hip.cos() - sagittal_z * hip.sin()
        z = self.lateral * hip.sin() + sagittal_z * hip.cos()
        return torch.stack((x, y, z), dim=-1) + self.origins

    def jacobian(self, joints):
        """Foot position derivative in the base frame, columns hip/thigh/calf."""
        hip, thigh, calf = joints.unbind(-1)
        upper, lower = self.lengths.unbind(-1)
        x = -upper*thigh.sin()-lower*(thigh+calf).sin()
        sagittal_z = -upper*thigh.cos()-lower*(thigh+calf).cos()
        y = self.lateral*hip.cos()-sagittal_z*hip.sin()
        z = self.lateral*hip.sin()+sagittal_z*hip.cos()
        h = torch.stack((torch.zeros_like(x), -z, y), -1)
        t = torch.stack((sagittal_z, x*hip.sin(), -x*hip.cos()), -1)
        k = torch.stack((-lower*(thigh+calf).cos(),
                         -lower*(thigh+calf).sin()*hip.sin(),
                         lower*(thigh+calf).sin()*hip.cos()), -1)
        return torch.stack((h,t,k), -1)

    def inverse(self, feet):
        """Return the bent-knee branch; caller must check residual and joint limits."""
        x, y, z = (feet - self.origins).unbind(dim=-1)
        upper, lower = self.lengths.unbind(dim=-1)
        sagittal_z = -(y.square() + z.square() - self.lateral.square()).clamp_min(1e-10).sqrt()
        hip = torch.atan2(z, y) - torch.atan2(sagittal_z, self.lateral)
        hip = torch.atan2(hip.sin(), hip.cos())
        cosine = (x.square() + sagittal_z.square() - upper.square() - lower.square()) / (2 * upper * lower)
        knee = -torch.acos(cosine.clamp(-1, 1))
        thigh = torch.atan2(-x, -sagittal_z) - torch.atan2(lower * knee.sin(), upper + lower * knee.cos())
        return torch.stack((hip, thigh, knee), dim=-1)
