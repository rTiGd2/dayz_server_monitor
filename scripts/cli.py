# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: cli.py
# Purpose: Command-line interface for running the monitor with options
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import argparse
from src.config_loader import load_config
from src.logger import setup_logging
import logging
from src.mod_checker import run_mod_check

def parse_args():
    parser = argparse.ArgumentParser(description="DayZ Server Monitor CLI")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Run without Discord/output write")
    parser.add_argument("--mode", choices=["async", "threaded", "serial"], help="Force mod check mode")
    return parser.parse_args()

def main():
    args = parse_args()
    config = load_config(args.config)
    if args.dry_run:
        config["output"]["to_file"] = False
        config["output"]["to_discord"] = False
    if args.mode:
        config["mod_check_mode"] = args.mode

    setup_logging(config)
    logging.info("Starting monitor (CLI mode)")
    run_mod_check(config)

if __name__ == "__main__":
    main()
