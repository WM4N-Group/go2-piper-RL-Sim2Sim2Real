"""与Climb相同的18轴位置/速度/增益/前馈统一电机接口。"""
from dataclasses import dataclass
import numpy as np


@dataclass
class MotorCommand:
    position: np.ndarray
    velocity: np.ndarray
    kp: np.ndarray
    kd: np.ndarray
    feedforward: np.ndarray

    def array(self):
        return np.stack((self.position,self.velocity,self.kp,self.kd,self.feedforward))
