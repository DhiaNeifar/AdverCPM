import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.drift import DriftAttack


def run_drift_experiment(sim_path: str, drift_rate: float, direction: str = "NE"):
    """
    Run drift attack on a dataset with given drift rate.
    Returns average drift across all vehicles per frame.
    """
    sim_dir = Path(sim_path)
    yaml_files = sorted(sim_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files in {sim_dir}")

    attack = DriftAttack({"drift_rate": drift_rate, "direction": direction})

    per_frame_drifts = []

    for f in yaml_files:
        cpm = parse_yaml(f)
        vehicles = cpm.get("vehicles", {})
        if not vehicles:
            continue

        # Save originals
        orig_positions = {vid: v["location"][:2] for vid, v in vehicles.items()}

        # Apply attack
        cpm = attack.apply(cpm)

        # Save drifted
        drifted_positions = {vid: v["location"][:2] for vid, v in vehicles.items()}

        # Compute average drift across all vehicles
        diffs = []
        for vid in orig_positions:
            ox, oy = orig_positions[vid]
            dx, dy = drifted_positions[vid]
            diffs.append(np.linalg.norm([dx - ox, dy - oy]))
        if diffs:
            per_frame_drifts.append(np.mean(diffs))

    return np.array(per_frame_drifts)


def test_drift_attack_multi_rates(sim_path):
    """
    Compare drift attack with different drift rates.
    """
    drift_rates = [0.1, 0.5, 1.0]  # small, medium, large drift
    results = {}

    for rate in drift_rates:
        results[rate] = run_drift_experiment(sim_path, drift_rate=rate)

    # Plot results
    plt.figure(figsize=(8, 6))
    for rate, drifts in results.items():
        frames = np.arange(len(drifts))
        plt.plot(frames, drifts, label=f"Drift rate = {rate}")

    plt.xlabel("Simulation progress (frames → time)")
    plt.ylabel("Average drift distance (m)")
    plt.title("Effect of Drift Rate on Divergence")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
