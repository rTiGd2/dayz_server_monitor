# Project: DayZ Server Monitor
# File: logger.py
# Purpose: Setup logging system including log level and log splitting with strict per-level routing
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

class LevelFilter(logging.Filter):
    """
    Filters (allows through) only records of a specific level.
    """
    def __init__(self, level):
        super().__init__()
        self.level = level
    def filter(self, record):
        return record.levelno == self.level

def setup_logging(config):
    """
    Initialize the logging subsystem using the provided config.
    - One file per log level: debug, info, error, critical.
    - Each file only receives messages of its corresponding level.
    - No message duplication between log files.
    - Console output is at the configured level or higher.
    - Debug log file is only active if loglevel is set to DEBUG.
    """
    if not config.get("logging", {}).get("enabled", False):
        return

    log_config = config["logging"]
    log_dir = Path(log_config.get("log_dir", "logs"))
    log_level = getattr(logging, log_config.get("level", "DEBUG").upper(), logging.DEBUG)
    log_files = log_config.get("files", {
        "debug": "debug.log",
        "info": "info.log",
        "error": "error.log",
        "critical": "critical.log"
    })

    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove all handlers to avoid duplicates on re-init
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    logger.setLevel(log_level)  # Set root logger to configured level

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console handler (level set by config)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # Per-level file handlers (no duplication)
    for level_name, filename in log_files.items():
        level = getattr(logging, level_name.upper(), None)
        if level is None:
            continue

        # Only add debug handler if log_level is DEBUG
        if level_name.lower() == "debug" and log_level != logging.DEBUG:
            continue

        filepath = log_dir / filename
        handler = RotatingFileHandler(filepath, maxBytes=5_000_000, backupCount=3)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        handler.addFilter(LevelFilter(level))
        logger.addHandler(handler)

    logging.info("Logging initialized (per-level, non-duplicating, debug log only if debug level).")
