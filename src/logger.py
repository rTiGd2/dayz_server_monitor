# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: logger.py
# Purpose: Setup logging system including log level and log splitting
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

class LevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level
    def filter(self, record):
        return record.levelno == self.level

def setup_logging(config):
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

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    for level_name, filename in log_files.items():
        level = getattr(logging, level_name.upper(), None)
        if level is None:
            continue
        filepath = log_dir / filename
        handler = RotatingFileHandler(filepath, maxBytes=5_000_000, backupCount=3)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        handler.addFilter(LevelFilter(level))
        logger.addHandler(handler)

    logging.info("Logging initialized.")
