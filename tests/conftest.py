import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def sim_path():
    """
    Ensure a simulation path is available for tests.
    - Uses $SIM_PATH if set
    - Otherwise falls back to ./experiments/raw simulations
    """
    path = os.getenv("SIM_PATH")

    if path:
        print(f"[INFO] Using SIM_PATH from environment: {path}")
    else:
        repo_root = Path(__file__).resolve().parents[1]
        path = repo_root / "experiments" / "raw simulations"
        print(f"[INFO] SIM_PATH not set, falling back to default: {path}")

    if not Path(path).exists():
        pytest.skip(f"[SKIP] Simulation path not found: {path}")

    return str(path)

