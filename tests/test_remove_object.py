import os
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.patches import Polygon
import math
from tqdm import tqdm

from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.remove_object import RemoveObjectAttack


def run_remove_object_experiment(sim_path: str, mode="targeted", omitted_id=650):
    """
    Run RemoveObject attack across frames from the malicious vehicle's folder.
    """
    sim_dir = Path(sim_path)
    print(f"[INFO] Starting RemoveObject experiment")
    print(f"[INFO] Simulation root path = {sim_dir}")

    if not sim_dir.exists():
        raise FileNotFoundError(f"[ERROR] Path does not exist: {sim_dir}")

    malicious_dir = sim_dir / str(omitted_id)
    if not malicious_dir.exists():
        raise FileNotFoundError(f"[ERROR] Malicious folder not found: {malicious_dir}")

    yaml_files = sorted(malicious_dir.glob("*.yaml"))
    print(f"[INFO] Found {len(yaml_files)} YAML files in folder {omitted_id}")

    if not yaml_files:
        raise FileNotFoundError(f"[ERROR] No YAML files in {malicious_dir}")

    attacked_frames = []
    attack = RemoveObjectAttack({"mode": mode, "omitted_id": omitted_id})

    for f in tqdm(yaml_files, desc=f"RemoveObjectAttack (omitted_id={omitted_id})"):
        cpm = parse_yaml(f)
        cpm_attacked = attack.apply(cpm)
        attacked_frames.append(cpm_attacked)

    print(f"[RESULT] Total attacked frames = {len(attacked_frames)}")
    return attacked_frames


def plot_remove_object_example(cpm_frame, ego_id: int = 641):
    """
    Plot vehicles from CPM:
    - Ego vehicle in blue
    - Removed vehicle(s) marked in black
    - Other vehicles in green
    """
    print("[INFO] Plotting RemoveObject example frame...")
    fig, ax = plt.subplots(figsize=(8, 8))
    vehicles = cpm_frame.get("vehicles", {})
    removed = cpm_frame.get("_removed", [])

    for vid, v in vehicles.items():
        x, y, _ = v["location"]
        length, width, _ = v["extent"]

        yaw = v["angle"][1] if "angle" in v else 0.0
        dx, dy = length / 2, width / 2
        corners = [(-dx, -dy), (-dx, dy), (dx, dy), (dx, -dy)]
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        rotated = [(x + cx * cos_y - cy * sin_y, y + cx * sin_y + cy * cos_y) for cx, cy in corners]

        if vid == ego_id:
            color, label = "blue", "Ego"
        else:
            color, label = "green", None

        poly = Polygon(rotated, closed=True, edgecolor=color,
                       facecolor="none", linewidth=2, label=label)
        ax.add_patch(poly)

    # Mark removed vehicles
    if removed:
        ax.annotate("REMOVED", (0.02, 0.95), xycoords="axes fraction",
                    fontsize=10, color="black", weight="bold")
        ax.plot([], [], color="black", label="Removed")

    xs = [v["location"][0] for v in vehicles.values()]
    ys = [v["location"][1] for v in vehicles.values()]
    ax.set_xlim(min(xs) - 20, max(xs) + 20)
    ax.set_ylim(min(ys) - 20, max(ys) + 20)

    ax.set_title("RemoveObject Attack Example")
    ax.set_xlabel("X position")
    ax.set_ylabel("Y position")
    ax.legend()
    ax.grid(True)
    ax.set_aspect("equal")
    plt.show()


def test_remove_object_attack(sim_path=None):
    """
    Test RemoveObject attack and plot one example.
    """
    sim_path = sim_path or os.getenv("SIM_PATH")
    if not sim_path:
        print("Skipping test_remove_object_attack (SIM_PATH not set)")
        return

    print(f"[TEST] Running RemoveObjectAttack with SIM_PATH={sim_path}")
    attacked_frames = run_remove_object_experiment(sim_path, mode="targeted", omitted_id=650)
    assert attacked_frames, "No attacked frames produced"

    print("[TEST] Plotting first attacked frame for verification...")
    plot_remove_object_example(attacked_frames[0])
