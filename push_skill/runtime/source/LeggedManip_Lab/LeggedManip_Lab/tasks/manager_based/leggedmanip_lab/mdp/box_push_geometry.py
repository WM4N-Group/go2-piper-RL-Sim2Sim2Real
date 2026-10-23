"""Optional source-matched MuJoCo geometry shield for Isaac PUSH diagnostics."""

from pathlib import Path

import numpy as np


class PiperBaseArmGeometryShield:
    observation_scope = "all_controller_steps_including_approach"

    def __init__(self, model_root: Path, minimum: float):
        import mujoco
        from reconfigurable_navigation.piper_robot_profile import (
            apply_piper_collision_profile, apply_piper_robot_profile,
        )

        self.mujoco = mujoco
        model_root = Path(model_root)
        spec = mujoco.MjSpec.from_file(str(model_root / "robots/go2_piper/go2piper.xml"))
        for mesh in spec.meshes:
            mesh.file = str(model_root / "robots/go2_piper/assets" / Path(mesh.file).name)
        apply_piper_robot_profile(spec)
        apply_piper_collision_profile(spec)
        self.model = spec.compile()
        self.data = mujoco.MjData(self.model)
        self.arm_qpos = np.asarray([int(self.model.joint(f"joint{index}").qposadr[0])
                                    for index in range(1, 7)])
        base = self.model.body("base_link").id
        arms = {self.model.body(f"link{index}").id for index in range(1, 7)}
        self.base_geoms = [index for index in range(self.model.ngeom) if self.model.geom_bodyid[index] == base]
        self.arm_geoms = [index for index in range(self.model.ngeom) if self.model.geom_bodyid[index] in arms]
        if not self.base_geoms or not self.arm_geoms:
            raise ValueError("Source-matched PUSH collision geometry is incomplete")
        self.minimum = minimum

    def clearance(self, joints: np.ndarray) -> float:
        self.data.qpos[self.arm_qpos] = joints
        self.mujoco.mj_kinematics(self.model, self.data)
        return min(float(self.mujoco.mj_geomDistance(self.model, self.data, arm, base, 1.0, None))
                   for arm in self.arm_geoms for base in self.base_geoms)

    def linearized_margin(self, actual: np.ndarray, active: np.ndarray, margin: float):
        """Local nominal-IK preference; the final collision shield remains required."""
        gradient = np.zeros_like(actual)
        residual = np.zeros(len(actual))
        for index in range(len(actual)):
            if not active[index]:
                continue
            distance = self.clearance(actual[index])
            if distance >= margin + 0.015:
                continue
            for joint in range(6):
                offset = np.zeros(6)
                offset[joint] = 0.001
                gradient[index, joint] = (self.clearance(actual[index] + offset)
                                          - self.clearance(actual[index] - offset)) / 0.002
            residual[index] = max(0.0, margin - distance)
        return gradient, residual

    def project(self, actual: np.ndarray, velocity: np.ndarray, target: np.ndarray,
                lower: np.ndarray, upper: np.ndarray, active: np.ndarray
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        output = target.copy()
        actual_clearance = np.zeros(len(target))
        blocked = np.zeros(len(target), dtype=bool)
        self.last_predicted_clearance = np.zeros(len(target))
        for index in range(len(target)):
            actual_clearance[index] = self.clearance(actual[index])
            self.last_predicted_clearance[index] = actual_clearance[index]
            # Observation remains enabled while reference intervention is gated off.
            if not active[index]:
                continue
            candidate = output[index].copy()
            predicted = actual[index] + 0.10 * velocity[index]
            self.last_predicted_clearance[index] = self.clearance(predicted)
            if self.last_predicted_clearance[index] < self.minimum + 0.015:
                gradient = np.empty(6)
                for joint in range(6):
                    offset = np.zeros(6)
                    offset[joint] = 0.001
                    gradient[joint] = (self.clearance(predicted + offset)
                                       - self.clearance(predicted - offset)) / 0.002
                norm = float(np.linalg.norm(gradient))
                if norm > 1.0e-4:
                    braking = np.clip(actual[index] - 0.10 * velocity[index]
                                      + 0.06 * gradient / norm, lower[index], upper[index])
                    corner = np.where(gradient > 0.01, upper[index],
                                      np.where(gradient < -0.01, lower[index], candidate))
                    for proposal in (braking, corner):
                        if self.clearance(proposal) > self.clearance(candidate) + 1.0e-5:
                            candidate = proposal
                            blocked[index] = True
            distance = self.clearance(candidate)
            if distance >= self.minimum:
                output[index] = candidate
                continue
            blocked[index] = True
            for _ in range(4):
                gradient = np.empty(6)
                for joint in range(6):
                    offset = np.zeros(6)
                    offset[joint] = 0.001
                    gradient[joint] = (self.clearance(candidate + offset)
                                       - self.clearance(candidate - offset)) / 0.002
                norm = float(gradient @ gradient)
                if norm < 1.0e-8:
                    break
                candidate = np.clip(candidate + (self.minimum + 0.002 - distance) * gradient / norm,
                                    lower[index], upper[index])
                updated = self.clearance(candidate)
                if updated <= distance + 1.0e-6:
                    break
                distance = updated
                if distance >= self.minimum:
                    break
            if distance < self.minimum:
                old = actual[index]
                if self.clearance(old) >= self.minimum:
                    for fraction in np.linspace(0.9, 0.0, 10):
                        proposal = np.clip(old + fraction * (target[index] - old), lower[index], upper[index])
                        if self.clearance(proposal) >= self.minimum:
                            candidate = proposal
                            break
                else:
                    # A rate-limited step may improve an unsafe pose without reaching
                    # the full margin immediately. Keep that recovery progress.
                    hold = np.clip(old, lower[index], upper[index])
                    if self.clearance(hold) > self.clearance(candidate):
                        candidate = hold
            output[index] = candidate
        return output, actual_clearance, blocked
