import os
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.patches import Polygon
import math

from advercpm.utils.file_ops import parse_yaml
from advercpm.attacks.remove_object import RemoveObjectAttack


def run_remove_object_experiment(sim_path: str, mode="targeted", omitted_id=650):
    """
    Run RemoveObject attack across frames.
    """
    sim_dir = Path(sim_path)
    yaml_files = sorted(sim_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files in {sim_dir}")

    attacked_frames = []
    for f in yaml_files:
        cpm = parse_yaml(f)
        attack = RemoveObjectAttack({"mode": mode, "omitted_id": omitted_id})
        cpm_attacked = attack.apply(cpm)
        attacked_frames.append(cpm_attacked)

    return attacked_frames


def plot_remove_object_example(cpm_frame, ego_id: int = 641):
    """
    Plot vehicles from CPM:
    - Ego vehicle in blue
    - Removed vehicle in black outline
    - Other vehicles in green
    """
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

        poly = Polygon(rotated, closed=True, edgecolor=color, facecolor="none",
                       linewidth=2, label=label)
        ax.add_patch(poly)

    # Show removed ones in black
    for rid in removed:
        ax.annotate("REMOVED", (0.02, 0.95), xycoords="axes fraction",
                    fontsize=10, color="black", weight="bold")
        # just mark in legend, we already popped them
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
        print("⚠️ Skipping test_remove_object_attack (SIM_PATH not set)")
        return

    attacked_frames = run_remove_object_experiment(sim_path, mode="targeted", omitted_id=650)
    assert attacked_frames, "No attacked frames produced"

    plot_remove_object_example(attacked_frames[0])
