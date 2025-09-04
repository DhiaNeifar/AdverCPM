import argparse
from omegaconf import DictConfig
import logging

from src.advercpm.config.loader import load_config
from advercpm.utils.logger import LoggerSetup

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
    logger.debug("Full config loaded.")

    # TODO: add simulation pipeline here


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log = logging.getLogger("advercpm.runner")
        log.warning("Execution interrupted by user (Ctrl+C). Shutting down gracefully...")
        # optional: clean up resources here
        exit(0)

