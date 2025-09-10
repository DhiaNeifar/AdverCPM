from __future__ import annotations

import math
import numpy as np
from collections import defaultdict
from typing import Dict, Any, Iterable
from .base_attack import Attack


class DriftAttack(Attack):
    """
    Drift Attack:
    Gradual cumulative position shift, causing divergence over time.

    Modes:
        - linear: deterministic drift along a direction
        - biased: drift + Gaussian noise (random walk style)

    Parameters:
        drift_rate (float): drift speed (meters per frame).
        direction (str): cardinal direction (N, S, E, W, NE, NW, SE, SW).
        apply_to_all (bool): if True, apply drift to all vehicles. (default: True)
        target_id: single vehicle id to target (ignored if apply_to_all=True).
        yaw_drift_deg_per_frame (float): optional yaw drift per frame.
        mode (str): "linear" or "biased".
        sigma (float): noise std deviation for biased mode.
    """

    _DIRECTION_VECTORS = {
        "N": (0.0, 1.0),
        "S": (0.0, -1.0),
        "E": (1.0, 0.0),
        "W": (-1.0, 0.0),
        "NE": (math.sqrt(0.5), math.sqrt(0.5)),
        "NW": (-math.sqrt(0.5), math.sqrt(0.5)),
        "SE": (math.sqrt(0.5), -math.sqrt(0.5)),
        "SW": (-math.sqrt(0.5), -math.sqrt(0.5)),
    }

    def __init__(self, parameters: Dict[str, Any]):
        super().__init__(parameters)
        self.drift_rate: float = float(parameters.get("drift_rate", 0.5))
        direction = str(parameters.get("direction", "NE")).upper()
        self.dx, self.dy = self._DIRECTION_VECTORS.get(direction, (0.0, 0.0))

        # FIX: default to all vehicles unless explicitly narrowed
        self.apply_to_all: bool = bool(parameters.get("apply_to_all", True))
        self.target_id = parameters.get("target_id", None)

        # Naming clarified: per *frame*
        self.yaw_drift_per_frame: float = float(parameters.get("yaw_drift_deg_per_frame",
                                                               parameters.get("yaw_drift_deg_per_s", 0.0)))

        self.mode: str = str(parameters.get("mode", "linear")).lower()
        self.sigma: float = float(parameters.get("sigma", 0.1))

        # Each vehicle keeps its own drift counter across frames
        self.vehicle_steps = defaultdict(int)

    def _select_targets(self, vehicles: Dict[Any, Any]) -> Iterable[Any]:
        if not vehicles:
            return []
        if self.apply_to_all or self.target_id is None:
            return list(vehicles.keys())
        # try exact id, else try str casting fallback
        if self.target_id in vehicles:
            return [self.target_id]
        tid_str = str(self.target_id)
        return [k for k in vehicles.keys() if str(k) == tid_str]

    def _apply_shift_to_location(self, vehicle: Dict[str, Any], sx: float, sy: float) -> None:
        if "location" not in vehicle:
            return
        loc = vehicle["location"]
        # dict format: {"x":..., "y":..., "z":...}
        if isinstance(loc, dict):
            if "x" in loc: loc["x"] = float(loc["x"]) + sx
            if "y" in loc: loc["y"] = float(loc["y"]) + sy
            return
        # list/tuple format: [x, y, z?]
        if isinstance(loc, tuple):
            loc = list(loc)
            vehicle["location"] = loc
        if isinstance(loc, list) and len(loc) >= 2:
            loc[0] = float(loc[0]) + sx
            loc[1] = float(loc[1]) + sy

    def _apply_yaw_drift(self, vehicle: Dict[str, Any], yaw_delta: float) -> None:
        if abs(yaw_delta) < 1e-12:
            return
        ang = vehicle.get("angle")
        if ang is None:
            return
        # dict format: {"roll":..., "pitch":..., "yaw":...}
        if isinstance(ang, dict) and "yaw" in ang:
            ang["yaw"] = float(ang["yaw"]) + yaw_delta
            return
        # list/tuple format; try to treat index 2 as yaw if present, else index 1 (legacy)
        if isinstance(ang, tuple):
            ang = list(ang)
            vehicle["angle"] = ang
        if isinstance(ang, list):
            if len(ang) >= 3:
                ang[2] = float(ang[2]) + yaw_delta
            elif len(ang) >= 2:
                ang[1] = float(ang[1]) + yaw_delta

    def apply(self, cpm_frame: Dict[str, Any]) -> Dict[str, Any]:
        vehicles = cpm_frame.get("vehicles", {})
        if not vehicles:
            return cpm_frame

        target_ids = self._select_targets(vehicles)
        if not target_ids:
            # No valid targets; do nothing
            return cpm_frame

        for vid in target_ids:
            if vid not in vehicles:
                continue

            # increment step counter for this vehicle
            self.vehicle_steps[vid] += 1
            step = self.vehicle_steps[vid]

            # compute drift (cumulative over frames)
            base_shift_x = self.dx * self.drift_rate * step
            base_shift_y = self.dy * self.drift_rate * step

            if self.mode == "biased":
                shift_x = base_shift_x + np.random.normal(0.0, self.sigma)
                shift_y = base_shift_y + np.random.normal(0.0, self.sigma)
            else:
                shift_x, shift_y = base_shift_x, base_shift_y

            vehicle = vehicles[vid]
            self._apply_shift_to_location(vehicle, shift_x, shift_y)
            self._apply_yaw_drift(vehicle, self.yaw_drift_per_frame)

        return cpm_frame
