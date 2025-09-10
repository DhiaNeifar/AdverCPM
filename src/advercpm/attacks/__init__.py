import importlib
from pathlib import Path


def snake_to_pascal(name: str) -> str:
    """Convert snake_case attack name to PascalCase for class lookup."""
    return "".join(part.capitalize() for part in name.split("_"))


def get_attack_class(attack_type: str):
    """
    Dynamically load an attack class from src/advercpm/attacks.
    """
    module_name = f"advercpm.attacks.{attack_type}"
    class_name = f"{snake_to_pascal(attack_type)}Attack"

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        available = available_attacks()
        raise ValueError(
            f"Attack module '{module_name}' not found.\n"
            f"Available attacks: {', '.join(available)}"
        )

    try:
        attack_cls = getattr(module, class_name)
    except AttributeError:
        available = available_attacks()
        raise ValueError(
            f"Attack class '{class_name}' not found in {module_name}.\n"
            f"Available attacks: {', '.join(available)}"
        )

    return attack_cls


def build_attack(cfg):
    """
    Build attack from config (DictConfig or dict).
    """

    attack_cls = get_attack_class(cfg.type)
    return attack_cls(cfg.parameters)


def available_attacks():
    """
    Discover all implemented attacks in src/advercpm/attacks/.
    Returns a list of attack types (snake_case names).
    """
    attacks_dir = Path(__file__).parent
    attack_files = [
        f.stem for f in attacks_dir.glob("*.py")
        if not f.stem.startswith("__") and f.stem not in {"base_attack"}
    ]
    return attack_files
