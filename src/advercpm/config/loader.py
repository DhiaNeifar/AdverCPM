from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
from omegaconf import OmegaConf, DictConfig


from advercpm.attacks import available_attacks


# ----------------------------
# (Optional) structured schema
# ----------------------------

@dataclass
class DataCfg:
    simulation_path: str = "./experiments/raw simulations"
    adversarial_simulation_path: str = "./experiments/adversarial simulations"
    format: str = "yaml+pcd"            # "yaml", "yaml+pcd"
    overwrite: bool = False
    allow_missing_frames: bool = False
    file_extensions: List[str] = field(default_factory=lambda: ["yaml", "pcd"])


@dataclass
class AttackCfg:
    type: str = "unset"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationCfg:
    batch_size: int = 16
    shuffle: bool = False
    max_frames: Optional[int] = None
    num_workers: int = 0                # data-loading workers (0 = main thread)
    device: str = "cpu"                 # "cpu" or "cuda"
    visualization: bool = False
    save_visualization: bool = False
    deterministic: bool = True


@dataclass
class EvaluationCfg:
    enabled: bool = True
    metrics: List[str] = field(default_factory=lambda: ["MSE_position", "object_count_diff"])
    save_results: bool = True
    results_path: str = "./experiments/results"
    per_frame_csv: bool = True


@dataclass
class LoggingHandlerConsoleCfg:
    enabled: bool = True
    level: str = "INFO"


@dataclass
class LoggingHandlerFileCfg:
    enabled: bool = True
    dir: str = "./logs"
    filename: str = "run.log"
    level: str = "INFO"
    rotation: str = "size"             # "size" or "time"
    max_bytes: int = 10 * 1024 * 1024  # 10 MB (if rotation == size)
    backup_count: int = 5
    when: str = "midnight"             # if rotation == time
    utc: bool = True
    delay: bool = False


@dataclass
class LoggingFmtCfg:
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    json: bool = False                 # if True and you have python-json-logger installed
    colorize: bool = False             # console color (you can wire colorlog later)


@dataclass
class LoggingCfg:
    level: str = "INFO"                # root level
    propagate: bool = False
    capture_warnings: bool = True
    fmt: LoggingFmtCfg = field(default_factory=LoggingFmtCfg)
    handlers: Dict[str, Any] = field(default_factory=lambda: {
        "console": LoggingHandlerConsoleCfg(),
        "file": LoggingHandlerFileCfg(),
    })
    level_overrides: Dict[str, str] = field(default_factory=lambda: {
        "matplotlib": "WARNING",
        "omegaconf": "WARNING"
    })
    use_timestamp_subdir: bool = True
    timestamp_format: str = "%Y%m%d_%H%M%S"
    run_name_in_subdir: bool = True    # create subdir with experiment.name if available


@dataclass
class ExperimentCfg:
    name: str = "baseline"             # NOTE: seed intentionally NOT here (goes in scenario file)
    description: str = ""
    save_logs: bool = True
    seed: Optional[int] = 0


@dataclass
class RootCfg:
    experiment: ExperimentCfg = field(default_factory=ExperimentCfg)
    data: DataCfg = field(default_factory=DataCfg)
    attack: AttackCfg = field(default_factory=AttackCfg)
    simulation: SimulationCfg = field(default_factory=SimulationCfg)
    evaluation: EvaluationCfg = field(default_factory=EvaluationCfg)
    logging: LoggingCfg = field(default_factory=LoggingCfg)


# ------------------------------------
# Loader
# ------------------------------------
from pathlib import Path
from typing import Optional, List
from omegaconf import OmegaConf, DictConfig


def load_config(
    default_path: str = "src/advercpm/config/default.yaml",
    scenario_path: str = None,
    cli_overrides: Optional[List[str]] = None,
) -> DictConfig:

    base = OmegaConf.structured(RootCfg)             # schema defaults
    default_cfg = OmegaConf.load(default_path)       # your default.yaml
    cfg = OmegaConf.merge(base, default_cfg)

    # --- merge with scenario config ---
    if scenario_path is not None:
        scenario_file = Path("src/advercpm/config/experiments") / scenario_path
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario config not found: {scenario_file}")
        scenario_cfg = OmegaConf.load(scenario_file)
        cfg = OmegaConf.merge(cfg, scenario_cfg)
        attack_type = cfg.attack.type
        attacks = available_attacks()
        if attack_type not in attacks:
            raise ValueError(
                f"Attack type '{attack_type}' not recognized.\n"
                f"Available attacks: {', '.join(attacks)}"
            )
    # --- CLI overrides ---
    if cli_overrides:
        dotlist = OmegaConf.from_dotlist(cli_overrides)
        cfg = OmegaConf.merge(cfg, dotlist)

    OmegaConf.set_readonly(cfg, False)  # allow runtime edits (e.g., computed paths)
    return cfg
