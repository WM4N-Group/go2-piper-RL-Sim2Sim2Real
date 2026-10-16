"""Read-only, fixed-time PUSH consequence observer for Isaac traces."""

import hashlib
import json
import math
from pathlib import Path


FEATURE_NAMES = ["box_length_m", "box_width_m", "box_height_m", "goal_distance_m", "contact_0p4s_progress_m"]


def predict(fitted, features, goal):
    names = fitted["feature_names"]
    if names != FEATURE_NAMES[:len(names)]:
        raise ValueError("Unexpected frozen PUSH features")
    normalized = [(value - mean) / scale for value, mean, scale in
                  zip(features, fitted["input_mean"], fitted["input_scale"], strict=False)]
    if len(normalized) != len(names) or not all(math.isfinite(value) for value in normalized):
        raise ValueError("Invalid shadow features")
    output = [fitted["target_mean"][index] + sum(
        normalized[feature] * fitted["coefficients"][feature][index]
        for feature in range(len(names))) for index in (0, 1)]
    return {"terminal_progress_m": max(0.0, min(goal, output[0])),
            "push_success_probability": max(0.0, min(1.0, output[1]))}


class PushShadowObserver:
    def __init__(self, model_path, box_size, goal, control_dt, gate_path=None):
        model_path = Path(model_path)
        data = model_path.read_bytes()
        self.model_sha256 = hashlib.sha256(data).hexdigest()
        self.model = json.loads(data)
        if self.model.get("schema_version") != 1 or self.model.get("query_after_contact_s") != 0.4:
            raise ValueError("Unexpected frozen PUSH model contract")
        self.gate = None
        self.gate_sha256 = None
        if gate_path is not None:
            gate_data = Path(gate_path).read_bytes()
            self.gate_sha256 = hashlib.sha256(gate_data).hexdigest()
            self.gate = json.loads(gate_data)["gate"]
            if (self.gate.get("schema_version") != 1
                    or self.gate.get("execution_authority") != "none"
                    or self.gate.get("query_after_contact_s") != [0.4, 0.6]):
                raise ValueError("Unexpected read-only response gate contract")
        self.box_size = list(box_size)
        self.goal = float(goal)
        self.control_dt = float(control_dt)
        if len(self.box_size) != 3 or not all(math.isfinite(value) and value > 0 for value in self.box_size):
            raise ValueError("Invalid visible box geometry")
        if not math.isfinite(self.goal) or self.goal <= 0 or not math.isfinite(self.control_dt) or self.control_dt <= 0:
            raise ValueError("Invalid goal or control period")
        self.initial_box_x = None
        self.first_contact_step = None
        self.query = None
        self.extra_query = None

    def observe(self, sample):
        step = sample["step"]
        if self.initial_box_x is None:
            if step != 0:
                raise ValueError("Shadow trace must begin before execution")
            self.initial_box_x = sample["box_position"][0]
        if sample["hand_contact"] and self.first_contact_step is None:
            self.first_contact_step = step
        if self.first_contact_step is None:
            return
        if self.query is None and step >= self.first_contact_step + round(0.4 / self.control_dt):
            progress = sample["box_position"][0] - self.initial_box_x
            features = [*self.box_size, self.goal, progress]
            self.query = {
                "step": step, "time_s": step * self.control_dt,
                "box_progress_m": progress,
                "predictions": {name: predict(entry["model"], features, self.goal)
                                for name, entry in self.model["models"].items()},
            }
        if (self.gate is not None and self.query is not None and self.extra_query is None
                and step >= self.first_contact_step + round(0.6 / self.control_dt)):
            self.extra_query = {"step": step, "time_s": step * self.control_dt,
                                "box_progress_m": sample["box_position"][0] - self.initial_box_x}

    def result(self, terminal_time_s):
        lead = None if self.query is None else terminal_time_s - self.query["time_s"]
        result = {
            "scope": "Piper Isaac PUSH stage; read-only online shadow",
            "model_sha256": self.model_sha256,
            "query_after_contact_s": 0.4,
            "first_contact_step": self.first_contact_step,
            "query": self.query,
            "query_to_terminal_s": lead,
            "valid_actionable_query": lead is not None and lead >= 1.0,
            "abstention_reason": "online_decision_policy_not_calibrated",
            "execution_authority": "none",
        }
        if self.gate is not None:
            early = self.query
            extra = self.extra_query
            gate_decision = "unavailable"
            decision_time_s = None
            if early is not None and terminal_time_s - early["time_s"] >= 1.0:
                if early["box_progress_m"] >= self.gate["early_mobile_progress_threshold_m"]:
                    gate_decision = "mobile_evidence"
                    decision_time_s = early["time_s"]
                elif extra is not None and terminal_time_s - extra["time_s"] >= 1.0:
                    gate_decision = ("mobile_evidence_after_extra_observation"
                                     if extra["box_progress_m"] - early["box_progress_m"]
                                     >= self.gate["additional_mobile_delta_threshold_m"] else "unresolved")
                    decision_time_s = extra["time_s"]
            result["response_gate"] = {
                "gate_sha256": self.gate_sha256,
                "extra_query": extra,
                "decision": gate_decision,
                "decision_time_s": decision_time_s,
                "decision_to_terminal_s": None if decision_time_s is None else terminal_time_s - decision_time_s,
                "execution_authority": "none",
            }
        return result
