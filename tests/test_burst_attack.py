import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from advercpm.data.yaml_parser import parse_yaml
from advercpm.attacks.burst import BurstAttack


def run_burst_experiment(sim_path: str, lam=0.1, max_jitter=5.0):
    sim_dir = Path(sim_path)
    yaml_files = sorted(sim_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files in {sim_dir}")

    attack = BurstAttack({"lambda": lam, "max_jitter": max_jitter})

    effects = []
    for f in yaml_files:
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

    return effects


def compare_burst_params(sim_path: str, lambdas=[0.001, 0.01, 0.1], jitters=[2, 5, 10]):
    """
    Compare BurstAttack effects for different lambda and max_jitter values.
    """
    fig, axes = plt.subplots(len(lambdas), len(jitters), figsize=(15, 10), sharex=True, sharey=True)

    for i, lam in enumerate(lambdas):
        for j, jitter in enumerate(jitters):
            effects = run_burst_experiment(sim_path, lam=lam, max_jitter=jitter)

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
        print("⚠️ Skipping test_burst_param_sensitivity (SIM_PATH not set)")
        return

    compare_burst_params(sim_path)
