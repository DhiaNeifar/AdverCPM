import numpy as np
from typing import Dict, Any


class BurstAttack:
    """
    Burst Attack:
    Occasionally injects high-magnitude random perturbations
    in vehicle positions (Poisson-distributed).
    """

    def __init__(self, params: Dict[str, Any]):
        self.lambda_ = params.get("lambda", 0.2)  # Poisson rate
        self.max_jitter = params.get("max_jitter", 5.0)  # meters

    def apply(self, cpm: dict) -> dict:
        vehicles = cpm.get("vehicles", {})

        for vid, v in vehicles.items():
            # sample if a burst occurs for this vehicle
            bursts = np.random.poisson(self.lambda_)
            if bursts > 0:
                jitter = np.random.uniform(-self.max_jitter, self.max_jitter, size=3)
                loc = v["location"]
                new_loc = [loc[i] + jitter[i] for i in range(3)]
                v["location"] = new_loc

        return cpm
