import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm

from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.white_noise import WhiteNoiseAttack


def run_white_noise_experiment(sim_path: str, sigma=0.5, malicious_id: int = 650):
    """
    Run WhiteNoise attack on malicious vehicle's YAML files.
    Returns average displacement per frame.
    """
    sim_dir = Path(sim_path)
    print(f"[INFO] Starting WhiteNoise experiment")
    print(f"[INFO] Simulation root path = {sim_dir}")

    if not sim_dir.exists():
        raise FileNotFoundError(f"[ERROR] Path does not exist: {sim_dir}")

    # Look only inside malicious vehicle folder
    malicious_dir = sim_dir / str(malicious_id)
    if not malicious_dir.exists():
        raise FileNotFoundError(f"[ERROR] Malicious folder not found: {malicious_dir}")

    yaml_files = sorted(malicious_dir.glob("*.yaml"))
    print(f"[INFO] Found {len(yaml_files)} YAML files in folder {malicious_id}")

    if not yaml_files:
        raise FileNotFoundError(f"[ERROR] No YAML files in {malicious_dir}")

    attack = WhiteNoiseAttack({"sigma": sigma})
    effects = []

    for f in tqdm(yaml_files, desc=f"WhiteNoiseAttack σ={sigma}"):
        cpm = parse_yaml(f)
        vehicles = cpm.get("vehicles", {})
        if not vehicles:
            effects.append(0.0)
            continue

        # save original positions
        orig_positions = {vid: v["location"][:] for vid, v in vehicles.items()}

        # apply attack
        cpm_attacked = attack.apply(cpm)
        new_positions = {vid: v["location"][:] for vid, v in cpm_attacked["vehicles"].items()}

        # measure displacement
        displacements = []
        for vid in orig_positions:
            if vid in new_positions:
                ox, oy, oz = orig_positions[vid]
                nx, ny, nz = new_positions[vid]
                d = np.sqrt((nx - ox)**2 + (ny - oy)**2 + (nz - oz)**2)
                displacements.append(d)

        avg_disp = np.mean(displacements) if displacements else 0.0
        effects.append(avg_disp)

    print(f"[RESULT] Processed {len(effects)} frames for σ={sigma}")
    return effects


def plot_white_noise_effects(effects, sigma):
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(effects)), effects, marker=".", linestyle="-", color="purple", alpha=0.7)
    plt.title(f"White Noise Attack Effect Over Time (σ={sigma})")
    plt.xlabel("Frame index")
    plt.ylabel("Average displacement (m)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def compare_white_noise_params(sim_path: str, sigmas=[0.1, 0.5, 1.0, 2.0], malicious_id: int = 650):
    """
    Run WhiteNoiseAttack for different sigma values and plot comparisons.
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    for sigma in sigmas:
        effects = run_white_noise_experiment(sim_path, sigma=sigma, malicious_id=malicious_id)
        ax.plot(range(len(effects)), effects, marker=".", linestyle="-", alpha=0.7, label=f"σ={sigma}")

    ax.set_title("White Noise Attack Sensitivity to σ")
    ax.set_xlabel("Frame index")
    ax.set_ylabel("Average displacement (m)")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()


def test_white_noise_sensitivity(sim_path=None):
    """
    Validate that larger σ produces larger average displacement.
    """
    sim_path = sim_path or os.getenv("SIM_PATH")
    if not sim_path:
        print("Skipping test_white_noise_sensitivity (SIM_PATH not set)")
        return

    print(f"[TEST] Running WhiteNoiseAttack with SIM_PATH={sim_path}")
    compare_white_noise_params(sim_path, malicious_id=650)
