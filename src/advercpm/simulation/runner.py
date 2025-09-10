import argparse
import shutil
import logging
from pathlib import Path
from omegaconf import DictConfig


from advercpm.attacks import build_attack
from src.advercpm.config.loader import load_config
from advercpm.utils.logger import LoggerSetup
from advercpm.utils.file_ops import parse_yaml, save_yaml
# ---------------------
# CLI entry-point helper
# ---------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AdverCPM Runner")
    parser.add_argument("--config", type=str, default=None,
                   help="Scenario YAML (e.g. attack_drift.yaml)")
    parser.add_argument("--default", type=str, default="src/advercpm/config/default.yaml",
                   help="Default YAML (always loaded first)")
    # Everything after -- are OmegaConf dotlist overrides, example:
    #   python -m advercpm.simulation.runner --config config/experiments/attack_drift.yaml -- attack.parameters.drift_rate=0.8 logging.level=DEBUG
    parser.add_argument("overrides", nargs=argparse.REMAINDER)
    return parser.parse_args()


def load_from_cli() -> DictConfig:
    args = parse_args()
    # strip leading "--" that argparse keeps in REMAINDER sometimes
    overrides = [o for o in args.overrides if o != "--"]
    return load_config(default_path=args.default, scenario_path=args.config, cli_overrides=overrides)


def main():
    cfg = load_from_cli()
    log_dir = LoggerSetup(cfg).setup()
    logger = logging.getLogger("advercpm.runner")

    logger.info("Logs saved to: %s", log_dir)
    logger.debug("Full config loaded: %s", cfg)

    # --- Resolve roots ---
    sim_root = Path(cfg.data.simulation_path)
    adv_root = Path(cfg.data.adversarial_simulation_path)

    if not sim_root.exists():
        raise FileNotFoundError(f"Simulation path not found: {sim_root}")

    # --- Select one simulation folder under sim_root ---
    # (You can iterate all later if desired.)
    try:
        simulation_folder = next(iter(sorted(p for p in sim_root.iterdir() if p.is_dir())))
    except StopIteration:
        raise RuntimeError(f"No simulation folders found under {sim_root}")

    sim_path = simulation_folder
    adv_path = adv_root / simulation_folder.name
    adv_path.mkdir(parents=True, exist_ok=True)

    logger.info("Selected simulation: %s", sim_path)

    # --- Vehicle folders are inside sim_path (e.g., 649, 650, 659) ---
    vehicle_dirs = [p for p in sim_path.iterdir() if p.is_dir() and p.name.isdigit()]
    if len(vehicle_dirs) < 2:
        raise RuntimeError(
            f"Expected at least 2 vehicle folders in {sim_path}, found {len(vehicle_dirs)}"
        )

    vehicle_ids = sorted(int(p.name) for p in vehicle_dirs)
    ego_id = vehicle_ids[0]
    malicious_id = vehicle_ids[-1] if vehicle_ids[-1] != ego_id else vehicle_ids[1]

    logger.info("Discovered %d vehicles: %s", len(vehicle_ids), vehicle_ids)
    logger.info("Ego vehicle ID: %d", ego_id)
    logger.info("Malicious vehicle ID: %d", malicious_id)

    # --- Build attack instance ---
    attack = build_attack(cfg.attack)
    logger.info("Initialized attack '%s' with params: %s", cfg.attack.type, dict(cfg.attack.parameters))

    # --- Process each vehicle folder ---
    for vid in vehicle_ids:
        v_in = sim_path / str(vid)
        v_out = adv_path / str(vid)
        v_out.mkdir(parents=True, exist_ok=True)

        if vid == malicious_id:
            logger.info("Applying attack to vehicle %d", vid)
        else:
            logger.info("Copying data for vehicle %d (no attack)", vid)

        # Gather files
        files = sorted(v_in.iterdir())
        logger.debug("Vehicle %d: %d files found", vid, len(files))

        for f in files:
            if f.suffix.lower() == ".pcd":
                # Copy PCD unchanged
                dst = v_out / f.name
                shutil.copy2(f, dst)
                logger.debug("PCD copied: %s -> %s", f, dst)

            elif f.suffix.lower() == ".yaml":
                cpm = parse_yaml(f)
                if vid == malicious_id:
                    cpm_attacked = attack.apply(cpm)
                    dst = v_out / f.name
                    save_yaml(cpm_attacked, dst)

                    # Best-effort detailed logging from attack metadata (if provided)
                    meta = getattr(attack, "last_meta", None)
                    if meta:
                        logger.debug(
                            "YAML attacked: %s -> %s | meta=%s",
                            f.name, dst, meta
                        )
                    else:
                        logger.debug("YAML attacked: %s -> %s", f.name, dst)
                else:
                    # Copy YAML unchanged
                    dst = v_out / f.name
                    save_yaml(cpm, dst)
                    logger.debug("YAML copied: %s -> %s", f.name, dst)

            else:
                logger.debug("Skipping non-data file: %s", f.name)

    logger.info("Adversarial simulation saved to: %s", adv_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log = logging.getLogger("advercpm.runner")
        log.warning("Execution interrupted by user (Ctrl+C). Shutting down gracefully...")
        # optional: clean up resources here
        exit(0)

    # Run script
    # python -m advercpm.simulation.runner --config attack_drift.yaml -- attack.parameters.drift_rate=0.8 logging.level=DEBUG
