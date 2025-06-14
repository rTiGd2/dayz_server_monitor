# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: logger.py
# Purpose: Centralized logger setup.
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import logging
import os

def setup_logging(config):
    if not config.get("logging", {}).get("enabled", True):
        return

    log_dir = os.path.dirname(config['logging']['file'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=config['logging']['file'],
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info("Logging system initialized")