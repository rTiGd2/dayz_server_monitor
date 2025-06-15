# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: monitor.py
# Purpose: Main entry point for running the mod check process
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
from config_loader import load_config
from logger import setup_logging
from mod_checker import run_mod_check

def main():
    try:
        config = load_config("config.yaml")
    except Exception as e:
        print(f"[FATAL] Failed to load config.yaml: {e}")
        return

    try:
        setup_logging(config)
    except Exception as e:
        print(f"[FATAL] Failed to initialize logging: {e}")
        return

    logging.info("=== DayZ Server Monitor Started ===")

    try:
        run_mod_check(config)
    except Exception as e:
        logging.exception("Unhandled exception during mod check")

    logging.info("=== DayZ Server Monitor Finished ===")

if __name__ == "__main__":
    main()