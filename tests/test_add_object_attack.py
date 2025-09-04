import os
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.patches import Rectangle
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


from advercpm.data.yaml_parser import parse_yaml
from advercpm.attacks.add_object import AddObjectAttack


def run_add_object_experiment(sim_path: str, ego_id: int = 641, malicious_id: int = 650):
    sim_dir = Path(sim_path)
    yaml_files = sorted(sim_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files in {sim_dir}")

    attacked_frames = []

    for f in yaml_files:
        cpm = parse_yaml(f)

        if ego_id not in cpm.get("vehicles", {}) or malicious_id not in cpm.get("vehicles", {}):
            continue

        ego_extent = cpm["vehicles"][ego_id]["extent"]

        attack = AddObjectAttack({
            "ego_id": ego_id,
            "malicious_id": malicious_id,  # 👈 pass it
            "object_id": 9999,
            "distance_ahead": 10.0,
            "vel": 2.5,
            "extent": ego_extent,
        })

        cpm_attacked = attack.apply(cpm)
        attacked_frames.append(cpm_attacked)

    return attacked_frames



def plot_add_object_example(cpm_frame, ego_id: int = 641, fake_id: int = 9999, malicious_id: int = None):
    """
    Plot vehicles from CPM:
    - Ego vehicle in blue
    - Malicious vehicle in red
    - Fabricated object in black (inherits ego's orientation)
    - Other vehicles in green
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    vehicles = cpm_frame.get("vehicles", {})

    for vid, v in vehicles.items():
        x, y, _ = v["location"]
        length, width, _ = v["extent"]

        # Use yaw (we're in 2D XY, so roll/pitch are ignored)
        yaw = v["angle"][1] if "angle" in v else 0.0

        # --- ensure fake object uses ego's yaw ---
        if vid == fake_id and ego_id in vehicles:
            yaw = vehicles[ego_id]["angle"][1]

        # compute rotated rectangle corners
        dx, dy = length / 2, width / 2
        corners = [(-dx, -dy), (-dx, dy), (dx, dy), (dx, -dy)]
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        rotated = [(x + cx * cos_y - cy * sin_y, y + cx * sin_y + cy * cos_y) for cx, cy in corners]

        # --- assign colors ---
        if vid == ego_id:
            color, label = "blue", "Ego"
        elif malicious_id is not None and vid == malicious_id:
            color, label = "red", "Malicious"
        elif vid == fake_id:
            color, label = "black", "Fabricated"
        else:
            color, label = "green", None

        poly = Polygon(rotated, closed=True, edgecolor=color, facecolor="none",
                       linewidth=2, label=label)
        ax.add_patch(poly)

    # set plot limits
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
    attacked_frames = run_add_object_experiment(sim_path, ego_id=641, malicious_id=malicious_id)

    assert attacked_frames, "No attacked frames produced"

    # Plot one frame
    plot_add_object_example(attacked_frames[0], ego_id=641, fake_id=9999, malicious_id=malicious_id)
