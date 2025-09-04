import numpy as np
from typing import Dict, Any


class WhiteNoiseAttack:
    """
    White Noise Attack:
    Adds zero-mean Gaussian noise to vehicle positions (and optionally velocity).
    """

    def __init__(self, params: Dict[str, Any]):
        self.sigma = params.get("sigma", 0.5)  # meters
        self.apply_velocity = params.get("apply_velocity", False)

    def apply(self, cpm: dict) -> dict:
        vehicles = cpm.get("vehicles", {})

        for vid, v in vehicles.items():
            # --- add Gaussian noise to position ---
            loc = v["location"]
            noise = np.random.normal(0, self.sigma, size=3)
            v["location"] = [loc[i] + noise[i] for i in range(3)]

            # --- optionally perturb velocity ---
            if self.apply_velocity and "speed" in v:
                v["speed"] = float(v["speed"] + np.random.normal(0, self.sigma))

        return cpm
