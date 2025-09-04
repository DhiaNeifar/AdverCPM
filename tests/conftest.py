import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def sim_path():
    """
    Ensure a simulation path is available for tests.
    - Uses $SIM_PATH if set
    - Otherwise falls back to ./datasets/original
    """
    path = os.getenv("SIM_PATH")

    if not path:
        # fallback to local datasets/original relative to repo root
        repo_root = Path(__file__).resolve().parents[1]
        path = repo_root / "datasets" / "original"

    if not Path(path).exists():
        pytest.skip(f"Simulation path not found: {path}")

    return str(path)
