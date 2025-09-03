import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from omegaconf import DictConfig


class LoggerSetup:
    """
    Centralized logging setup for AdverCPM.

    - Configures console and file logging
    - Supports timestamped log directories
    - Applies module-level log overrides
    """

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg.logging
        self.experiment_name = getattr(cfg.experiment, "name", "run")

    def setup(self) -> Path:
        """Configure logging according to the provided config."""
        root = logging.getLogger()
        root.setLevel(self._get_level(self.cfg.level))

        # Clear old handlers (avoid duplicates if reinitialized)
        for h in list(root.handlers):
            root.removeHandler(h)

        # Compute log directory
        log_dir = self._build_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Formatter
        formatter = logging.Formatter(
            fmt=self.cfg.fmt.format,
            datefmt=self.cfg.fmt.datefmt,
        )

        # Console handler
        if self.cfg.handlers.console.enabled:
            ch = logging.StreamHandler()
            ch.setLevel(self._get_level(self.cfg.handlers.console.level))
            ch.setFormatter(formatter)
            root.addHandler(ch)

        # File handler
        if self.cfg.handlers.file.enabled:
            fh = self._create_file_handler(log_dir, formatter)
            root.addHandler(fh)

        # Module-level overrides
        for logger_name, lvl in self.cfg.level_overrides.items():
            logging.getLogger(logger_name).setLevel(self._get_level(lvl))

        # Misc
        logging.captureWarnings(self.cfg.capture_warnings)
        root.propagate = bool(self.cfg.propagate)

        return log_dir

    # ----------------------
    # Internal helpers
    # ----------------------

    def _build_log_dir(self) -> Path:
        """Construct log directory as <base>/<experiment>_<YYYY-MM-DD-HH-MM-SS>."""
        log_dir = Path(self.cfg.handlers.file.dir)

        # always include experiment name
        folder_name = self.experiment_name

        # use human-readable timestamp
        if self.cfg.use_timestamp_subdir:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            folder_name = f"{folder_name}_{timestamp}"

        return log_dir / folder_name

    def _create_file_handler(self, log_dir: Path, formatter: logging.Formatter):
        """Create a rotating or time-based file handler."""
        fh_path = log_dir / self.cfg.handlers.file.filename

        if self.cfg.handlers.file.rotation == "time":
            fh = logging.handlers.TimedRotatingFileHandler(
                filename=str(fh_path),
                when=self.cfg.handlers.file.when,
                backupCount=self.cfg.handlers.file.backup_count,
                utc=self.cfg.handlers.file.utc,
                delay=self.cfg.handlers.file.delay,
                encoding="utf-8",
            )
        else:  # size-based rotation
            fh = logging.handlers.RotatingFileHandler(
                filename=str(fh_path),
                maxBytes=int(self.cfg.handlers.file.max_bytes),
                backupCount=int(self.cfg.handlers.file.backup_count),
                delay=self.cfg.handlers.file.delay,
                encoding="utf-8",
            )

        fh.setLevel(self._get_level(self.cfg.handlers.file.level))
        fh.setFormatter(formatter)
        return fh

    @staticmethod
    def _get_level(level: str) -> int:
        """Convert string log level to logging constant."""
        return getattr(logging, str(level).upper(), logging.INFO)
