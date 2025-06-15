# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: monitor.py
# Purpose: Entrypoint for the monitoring process
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
import sys
import traceback
import config_loader
import mod_checker
from templates import TemplateLoader

def main():
    try:
        config = config_loader.load_config("config.yaml")

        logfile = config.get("logfiles", "monitor.log")
        log_level = config.get("loglevel", "INFO").upper()

        # Remove all handlers associated with the root logger before setting up new configuration
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename=logfile,
            filemode="a"
        )

        locale = config.get("locale", "en_GB")
        templates = TemplateLoader(locale)

        mod_checker.run_mod_check(config, templates)

    except Exception as e:
        logging.error("Unhandled exception during mod check")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
