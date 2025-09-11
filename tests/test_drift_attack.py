import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm

from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.drift import DriftAttack


def run_drift_experiment(sim_path: str, drift_rate: float, direction: str = "NE", malicious_id: int = 650):
    """
    Run drift attack ONLY on the malicious vehicle's YAML folder.
    Returns average drift across all vehicles in those frames.
    """
    sim_dir = Path(sim_path)

    print(f"[INFO] Starting Drift experiment")
    print(f"[INFO] Simulation root path = {sim_dir}")

    if not sim_dir.exists():
        raise FileNotFoundError(f"[ERROR] Path does not exist: {sim_dir}")

    malicious_dir = sim_dir / str(malicious_id)
    if not malicious_dir.exists():
        raise FileNotFoundError(f"[ERROR] Malicious folder not found: {malicious_dir}")

    yaml_files = sorted(malicious_dir.glob("*.yaml"))
    print(f"[INFO] Found {len(yaml_files)} YAML files in malicious folder {malicious_id}.")

    if not yaml_files:
        raise FileNotFoundError(f"[ERROR] No YAML files in {malicious_dir}")

    attack = DriftAttack({"drift_rate": drift_rate, "direction": direction})
    per_frame_drifts = []

    for f in tqdm(yaml_files, desc=f"Applying DriftAttack (rate={drift_rate}, dir={direction})"):
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

        # Compute average drift across all vehicles (in malicious frame only)
        diffs = []
        for vid in orig_positions:
            ox, oy = orig_positions[vid]
            dx, dy = drifted_positions[vid]
            diffs.append(np.linalg.norm([dx - ox, dy - oy]))
        if diffs:
            per_frame_drifts.append(np.mean(diffs))

    print(f"[RESULT] Total frames processed (drift_rate={drift_rate}) = {len(per_frame_drifts)}")
    return np.array(per_frame_drifts)


def test_drift_attack_multi_rates(sim_path):
    """
    Compare drift attack with different drift rates (malicious-only).
    """
    print(f"[TEST] Running DriftAttack with SIM_PATH={sim_path}")
    drift_rates = [0.1, 0.5, 1.0]  # small, medium, large drift
    results = {}

    for rate in drift_rates:
        results[rate] = run_drift_experiment(sim_path, drift_rate=rate, malicious_id=650)

    # Plot results
    print("[TEST] Plotting results...")
    plt.figure(figsize=(8, 6))
    for rate, drifts in results.items():
        frames = np.arange(len(drifts))
        plt.plot(frames, drifts, label=f"Drift rate = {rate}")

    plt.xlabel("Simulation progress (frames → time)")
    plt.ylabel("Average drift distance (m)")
    plt.title("Effect of Drift Rate on Divergence (malicious only)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
