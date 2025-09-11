import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm  # ✅ Progress bar
from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.burst import BurstAttack


def run_burst_experiment(sim_path: str, lam=0.1, max_jitter=5.0, malicious_id: int = 650):
    """
    Run burst attack on malicious vehicle's YAML files.
    Returns average displacement per frame.
    """
    sim_dir = Path(sim_path)

    print(f"[INFO] Starting Burst experiment")
    print(f"[INFO] Simulation root path = {sim_dir}")

    if not sim_dir.exists():
        raise FileNotFoundError(f"[ERROR] Path does not exist: {sim_dir}")

    # ✅ Look inside malicious vehicle folder only
    malicious_dir = sim_dir / str(malicious_id)
    if not malicious_dir.exists():
        raise FileNotFoundError(f"[ERROR] Malicious folder not found: {malicious_dir}")

    yaml_files = sorted(malicious_dir.glob("*.yaml"))
    print(f"[INFO] Found {len(yaml_files)} YAML files in folder {malicious_id}")

    if not yaml_files:
        raise FileNotFoundError(f"[ERROR] No YAML files in {malicious_dir}")

    attack = BurstAttack({"lambda": lam, "max_jitter": max_jitter})

    effects = []
    for f in tqdm(yaml_files, desc=f"BurstAttack λ={lam}, jitter={max_jitter}"):
        cpm = parse_yaml(f)
        vehicles = cpm.get("vehicles", {})
        if not vehicles:
            effects.append(0.0)
            continue

        # copy before attack
        orig_positions = {vid: v["location"][:] for vid, v in vehicles.items()}

        # apply attack
        cpm_attacked = attack.apply(cpm)
        new_positions = {vid: v["location"][:] for vid, v in cpm_attacked["vehicles"].items()}

        # compute displacements
        displacements = []
        for vid in orig_positions:
            if vid in new_positions:
                ox, oy, oz = orig_positions[vid]
                nx, ny, nz = new_positions[vid]
                d = np.sqrt((nx - ox) ** 2 + (ny - oy) ** 2 + (nz - oz) ** 2)
                displacements.append(d)

        frame_effect = np.mean(displacements) if displacements else 0.0
        effects.append(frame_effect)

    print(f"[RESULT] Processed {len(effects)} frames for λ={lam}, jitter={max_jitter}")
    return effects


def compare_burst_params(sim_path: str, lambdas=[0.001, 0.01, 0.1], jitters=[2, 5, 10], malicious_id: int = 650):
    """
    Compare BurstAttack effects for different lambda and max_jitter values.
    """
    fig, axes = plt.subplots(len(lambdas), len(jitters), figsize=(15, 10), sharex=True, sharey=True)

    for i, lam in enumerate(lambdas):
        for j, jitter in enumerate(jitters):
            effects = run_burst_experiment(sim_path, lam=lam, max_jitter=jitter, malicious_id=malicious_id)

            ax = axes[i, j]
            ax.plot(range(len(effects)), effects, marker=".", linestyle="-", color="red", alpha=0.7)
            ax.set_title(f"λ={lam}, jitter={jitter}")
            ax.grid(True)
            if i == len(lambdas) - 1:
                ax.set_xlabel("Frame index")
            if j == 0:
                ax.set_ylabel("Avg displacement (m)")

    fig.suptitle("Burst Attack Sensitivity to λ and Jitter", fontsize=14)
    plt.tight_layout()
    plt.show()


def test_burst_param_sensitivity(sim_path=None):
    """
    Run BurstAttack parameter sensitivity test.
    """
    sim_path = sim_path or os.getenv("SIM_PATH")
    if not sim_path:
        print("Skipping test_burst_param_sensitivity (SIM_PATH not set)")
        return

    print(f"[TEST] Running BurstAttack with SIM_PATH={sim_path}")
    compare_burst_params(sim_path, malicious_id=650)
