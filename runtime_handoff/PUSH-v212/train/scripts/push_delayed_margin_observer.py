"""Streaming, read-only terminal-error observer for frozen Piper PUSH traces."""

import hashlib
import json
import math
from pathlib import Path


FEATURES = ("box_length_m", "box_width_m", "box_height_m", "goal_m", "progress_0p4_m", "progress_1p2_m")


class PushDelayedMarginObserver:
    def __init__(self, model_path, box_size, goal_m, control_dt, expected_model_sha256=None):
        data = Path(model_path).read_bytes()
        self.model_sha256 = hashlib.sha256(data).hexdigest()
        if expected_model_sha256 is not None and self.model_sha256 != expected_model_sha256:
            raise ValueError("Frozen delayed model hash changed")
        model = json.loads(data)
        self.names = tuple(model["feature_names"])
        fitted = model["model"]
        if (model.get("schema_version") != 1
                or model.get("scope") != "Piper Isaac PUSH delayed terminal error; shadow only"
                or model.get("query_after_contact_s") != 1.2
                or self.names not in (FEATURES[:5], FEATURES[0:4] + FEATURES[5:6], FEATURES)
                or fitted.get("output") != "terminal_goal_error_m"
                or fitted.get("goal_tolerance_m") != 0.12):
            raise ValueError("Unexpected delayed model contract")
        self.mean = fitted["input_mean"]
        self.scale = fitted["input_scale"]
        self.coefficients = fitted["coefficients"]
        self.target_mean = fitted["target_mean"]
        if not (len(self.names) == len(self.mean) == len(self.scale) == len(self.coefficients)
                and all(math.isfinite(x) for x in (*self.mean, *self.scale, *self.coefficients, self.target_mean))
                and all(value > 0 for value in self.scale)):
            raise ValueError("Invalid delayed model coefficients")
        self.box_size = tuple(float(value) for value in box_size)
        self.goal_m = float(goal_m)
        self.control_dt = float(control_dt)
        if (len(self.box_size) != 3 or not all(math.isfinite(value) and value > 0 for value in self.box_size)
                or not math.isfinite(self.goal_m) or self.goal_m <= 0
                or not math.isfinite(self.control_dt) or self.control_dt <= 0):
            raise ValueError("Invalid visible scene or control period")
        self.initial_box_x = None
        self.first_contact_step = None
        self.last_step = -1
        self.early_query = None
        self.delayed_query = None

    def observe(self, point):
        step = point["step"]
        if step <= self.last_step:
            raise ValueError("Trace steps must be strictly increasing")
        self.last_step = step
        if self.initial_box_x is None:
            if step != 0:
                raise ValueError("Observer needs pre-execution step zero")
            self.initial_box_x = point["box_position"][0]
        if point["hand_contact"] and self.first_contact_step is None:
            self.first_contact_step = step
        if self.first_contact_step is None:
            return
        progress = point["box_position"][0] - self.initial_box_x
        if self.early_query is None and step >= self.first_contact_step + round(0.4 / self.control_dt):
            self.early_query = {"step": step, "time_s": step * self.control_dt, "progress_m": progress}
        if self.delayed_query is None and step >= self.first_contact_step + round(1.2 / self.control_dt):
            if self.early_query is None or step <= self.early_query["step"]:
                raise ValueError("Delayed observation precedes early observation")
            values = dict(zip(FEATURES[:4], (*self.box_size, self.goal_m), strict=True))
            values["progress_0p4_m"] = self.early_query["progress_m"]
            values["progress_1p2_m"] = progress
            prediction = self.target_mean + sum(
                (values[name] - self.mean[index]) / self.scale[index] * self.coefficients[index]
                for index, name in enumerate(self.names)
            )
            if not math.isfinite(prediction):
                raise ValueError("Non-finite delayed prediction")
            prediction = max(0.0, prediction)
            self.delayed_query = {"step": step, "time_s": step * self.control_dt,
                                  "progress_m": progress, "terminal_goal_error_m": prediction,
                                  "goal_margin_m": 0.12 - prediction}

    def result(self, terminal_time_s):
        lead = None if self.delayed_query is None else terminal_time_s - self.delayed_query["time_s"]
        valid = lead is not None and lead >= 1.0
        return {"scope": "Piper Isaac PUSH delayed terminal-error shadow replay",
                "model_sha256": self.model_sha256, "first_contact_step": self.first_contact_step,
                "early_query": self.early_query, "delayed_query": self.delayed_query,
                "query_to_terminal_s": lead, "valid_actionable_query": valid,
                "abstention_reason": None if valid else ("no_1p2s_query" if lead is None else "insufficient_terminal_lead"),
                "execution_authority": "none"}
