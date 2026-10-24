"""Centralized logging module.

Configures structured logging to console and date-stamped file in `logs/`.
"""

import logging
from pathlib import Path
from typing import Optional


def get_logger(name: str, log_dir: Path | str = "logs", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a logger instance writing to console and logs/ directory.

    Args:
        name: Logger name (module or component).
        log_dir: Directory where log files are stored.
        level: Logging level (default: logging.INFO).

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if directory exists or can be created)
        try:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path / "system.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger
