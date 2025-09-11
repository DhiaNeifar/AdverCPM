import os
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.patches import Polygon
import math
from tqdm import tqdm

from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.add_object import AddObjectAttack


def run_add_object_experiment(sim_path: str, ego_id: int = 641, malicious_id: int = 650):
    sim_dir = Path(sim_path)

    print(f"[INFO] Starting AddObject experiment")
    print(f"[INFO] Simulation root path = {sim_dir}")

    if not sim_dir.exists():
        raise FileNotFoundError(f"[ERROR] Path does not exist: {sim_dir}")

    # Recursively search for YAML files inside all subfolders
    yaml_files = sorted(sim_dir.rglob("*.yaml"))
    print(f"[INFO] Found {len(yaml_files)} YAML files (recursive search).")

    if not yaml_files:
        raise FileNotFoundError(f"[ERROR] No YAML files under {sim_dir}")

    attacked_frames = []

    for f in tqdm(yaml_files, desc="Processing YAML files"):
        cpm = parse_yaml(f)
        vehicles = cpm.get("vehicles", {})
        vehicle_ids = list(vehicles.keys())

        if ego_id not in vehicles or malicious_id not in vehicles:
            # Don’t spam tqdm, just skip silently
            continue

        ego_extent = vehicles[ego_id]["extent"]

        attack = AddObjectAttack({
            "ego_id": ego_id,
            "malicious_id": malicious_id,
            "object_id": 9999,
            "distance_ahead": 10.0,
            "vel": 2.5,
            "extent": ego_extent,
        })

        cpm_attacked = attack.apply(cpm)
        attacked_frames.append(cpm_attacked)

    print(f"[RESULT] Total attacked frames = {len(attacked_frames)}")
    return attacked_frames


def plot_add_object_example(cpm_frame, ego_id: int = 641, fake_id: int = 9999, malicious_id: int = None):
    """
    Plot vehicles from CPM:
    - Ego vehicle in blue
    - Malicious vehicle in red
    - Fabricated object in black (inherits ego's orientation)
    - Other vehicles in green
    """
    print("[INFO] Plotting AddObject example frame...")
    fig, ax = plt.subplots(figsize=(8, 8))
    vehicles = cpm_frame.get("vehicles", {})

    for vid, v in vehicles.items():
        x, y, _ = v["location"]
        length, width, _ = v["extent"]

        yaw = v["angle"][1] if "angle" in v else 0.0
        if vid == fake_id and ego_id in vehicles:
            yaw = vehicles[ego_id]["angle"][1]

        dx, dy = length / 2, width / 2
        corners = [(-dx, -dy), (-dx, dy), (dx, dy), (dx, -dy)]
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        rotated = [(x + cx * cos_y - cy * sin_y,
                    y + cx * sin_y + cy * cos_y) for cx, cy in corners]

        if vid == ego_id:
            color, label = "blue", "Ego"
        elif malicious_id is not None and vid == malicious_id:
            color, label = "red", "Malicious"
        elif vid == fake_id:
            color, label = "black", "Fabricated"
        else:
            color, label = "green", None

        poly = Polygon(rotated, closed=True, edgecolor=color,
                       facecolor="none", linewidth=2, label=label)
        ax.add_patch(poly)

    xs = [v["location"][0] for v in vehicles.values()]
    ys = [v["location"][1] for v in vehicles.values()]
    ax.set_xlim(min(xs) - 20, max(xs) + 20)
    ax.set_ylim(min(ys) - 20, max(ys) + 20)

    ax.set_title("AddObject Attack Example")
    ax.set_xlabel("X position")
    ax.set_ylabel("Y position")
    ax.legend()
    ax.grid(True)
    ax.set_aspect("equal")
    plt.show()


def test_add_object_attack(sim_path):
    """
    Test AddObject attack across frames and plot one example.
    """
    malicious_id = 650
    print(f"[TEST] Running test_add_object_attack with SIM_PATH={sim_path}")
    attacked_frames = run_add_object_experiment(sim_path, ego_id=641, malicious_id=malicious_id)

    assert attacked_frames, "No attacked frames produced"

    print("[TEST] Plotting first attacked frame for verification...")
    plot_add_object_example(attacked_frames[0], ego_id=641,
                            fake_id=9999, malicious_id=malicious_id)
