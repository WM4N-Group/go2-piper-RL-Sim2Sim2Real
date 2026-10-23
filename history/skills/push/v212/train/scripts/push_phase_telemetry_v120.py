"""Read-only per-phase controller-call telemetry, including initialization."""
import hashlib
from pathlib import Path

import torch


class PhaseTelemetry:
    names = ("safe_waypoints", "face_approach", "push", "goal_hold")

    def __init__(self, env, quota, foot_sensor_ids):
        self.env, self.quota = env, quota
        self.robot = env.scene["robot"]
        self.controller = env.action_manager.get_term("joint_pos").controller
        self.foot_sensor_ids = foot_sensor_ids
        self.original = self.controller.apply
        shape = (env.num_envs, len(self.names))
        self.count = torch.zeros(shape, device=env.device, dtype=torch.int64)
        self.below = self.count.clone()
        self.saturated = self.count.clone()
        self.support_under_three = self.count.clone()
        self.airborne = self.count.clone()
        self.minimum = torch.full(shape, float("inf"), device=env.device)
        self.minimum_time = torch.full(shape, -1., device=env.device)
        self.first_time = self.minimum_time.clone()
        self.maximum_torque = torch.zeros(shape, device=env.device)
        self.maximum_vz = torch.zeros_like(self.maximum_torque)
        self.maximum_foot_force = torch.zeros_like(self.maximum_torque)
        self.maximum_hand_force = torch.zeros_like(self.maximum_torque)
        self.minimum_joint_position = torch.zeros((*shape, self.robot.num_joints), device=env.device)
        self.controller.apply = self.apply

    def apply(self, actions):
        c, robot = self.controller, self.robot
        active = self.quota.active.clone()
        phase = torch.where(c.safe_approach_complete, 1, 0)
        phase = torch.where(c.approach_face_ready & c.safe_approach_complete, 2, phase)
        phase = torch.where(c.goal_hold_active, 3, phase)
        output = self.original(actions)
        distance = c.geometry_clearance
        ratio = (robot.data.applied_torque.abs() /
                 robot.data.joint_effort_limits.clamp_min(1e-6)).amax(dim=1)
        force = self.env.scene["contact_forces"].data.net_forces_w[:, self.foot_sensor_ids]
        support = (force[..., 2] > 2.).sum(dim=1)
        foot_force = torch.linalg.vector_norm(force, dim=-1).amax(dim=1)
        hand_force = torch.linalg.vector_norm(
            self.env.scene["box_contact_hand"].data.force_matrix_w.sum(dim=(1, 2)), dim=-1)
        vz = robot.data.root_lin_vel_w[:, 2].abs()
        now = self.env.episode_length_buf * self.env.step_dt
        for index in range(len(self.names)):
            selected = active & (phase == index)
            first = selected & (self.count[:, index] == 0)
            lower = selected & (distance < self.minimum[:, index])
            self.first_time[:, index] = torch.where(first, now, self.first_time[:, index])
            self.minimum_time[:, index] = torch.where(lower, now, self.minimum_time[:, index])
            self.minimum_joint_position[:, index] = torch.where(
                lower[:, None], robot.data.joint_pos, self.minimum_joint_position[:, index])
            self.minimum[:, index] = torch.where(lower, distance, self.minimum[:, index])
            self.count[:, index] += selected
            self.below[:, index] += selected & (distance < .035)
            self.saturated[:, index] += selected & (ratio >= .999)
            self.support_under_three[:, index] += selected & (support < 3)
            self.airborne[:, index] += selected & (support == 0)
            for target, value in ((self.maximum_torque, ratio), (self.maximum_vz, vz),
                                  (self.maximum_foot_force, foot_force),
                                  (self.maximum_hand_force, hand_force)):
                target[:, index] = torch.maximum(target[:, index], torch.where(selected, value, 0.))
        return output

    def summary(self):
        fields = dict(control_samples=self.count, below35mm_samples=self.below,
                      saturated_samples=self.saturated, support_under_three_samples=self.support_under_three,
                      airborne_samples=self.airborne, minimum_geometry_m=self.minimum,
                      minimum_time_s=self.minimum_time, first_time_s=self.first_time,
                      maximum_torque_ratio=self.maximum_torque, peak_abs_vz_m_s=self.maximum_vz,
                      peak_single_foot_resultant_N=self.maximum_foot_force,
                      peak_hand_resultant_N=self.maximum_hand_force,
                      joint_position_at_minimum=self.minimum_joint_position)
        result = {k: v.detach().cpu().tolist() for k, v in fields.items()}
        for env_id, counts in enumerate(result["control_samples"]):
            for phase_id, count in enumerate(counts):
                if count == 0:
                    result["minimum_geometry_m"][env_id][phase_id] = None
        return dict(phases=self.names, control_dt_s=self.env.step_dt,
                    helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    scope="All active environments at controller calls including initialization. Phase is sampled before controller.apply; geometry/forces describe the current physical state. Not physics-substep coverage; final post-step terminal sample is in the original evaluator telemetry.",
                    **result)
