from __future__ import annotations

import math
from typing import Dict, Any
from .attack import Attack


class DriftAttack(Attack):
    """
    Drift Attack:
    Gradual cumulative position shift, causing divergence over time.

    Parameters:
        target_id (int, optional): Vehicle ID to drift. If None, drift all vehicles.
        drift_rate (float): Drift speed (meters per frame).
        direction (str): Cardinal direction (N, S, E, W, NE, NW, SE, SW).
    """

    # Map cardinal directions to unit vectors
    _DIRECTION_VECTORS = {
        "N": (0, 1),
        "S": (0, -1),
        "E": (1, 0),
        "W": (-1, 0),
        "NE": (math.sqrt(0.5), math.sqrt(0.5)),
        "NW": (-math.sqrt(0.5), math.sqrt(0.5)),
        "SE": (math.sqrt(0.5), -math.sqrt(0.5)),
        "SW": (-math.sqrt(0.5), -math.sqrt(0.5)),
    }

    def __init__(self, parameters: Dict[str, Any]):
        super().__init__(parameters)
        self.target_id: int | None = parameters.get("target_id", None)
        self.drift_rate: float = parameters.get("drift_rate", 0.5)
        direction = parameters.get("direction", "NE")
        self.dx, self.dy = self._DIRECTION_VECTORS.get(direction, (0, 0))
        self.step_counter = 0  # keeps track of cumulative drift

    def apply(self, cpm_frame: Dict[str, Any]) -> Dict[str, Any]:
        vehicles = cpm_frame.get("vehicles", {})
        if not vehicles:
            return cpm_frame  # nothing to drift

        # Drift grows with every call
        self.step_counter += 1
        shift_x = self.dx * self.drift_rate * self.step_counter
        shift_y = self.dy * self.drift_rate * self.step_counter

        # Decide whether to drift one vehicle or all
        target_ids = [self.target_id] if self.target_id is not None else vehicles.keys()

        for vid in target_ids:
            if vid not in vehicles:
                continue

            vehicle = vehicles[vid]

            # Modify position
            if "location" in vehicle and len(vehicle["location"]) >= 2:
                vehicle["location"][0] += shift_x
                vehicle["location"][1] += shift_y

            # Modify yaw orientation if available
            if "angle" in vehicle and len(vehicle["angle"]) >= 2:
                vehicle["angle"][1] += math.degrees(math.atan2(self.dy, self.dx)) * 0.01

        return cpm_frame
