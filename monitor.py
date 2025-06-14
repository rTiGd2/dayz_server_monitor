# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
from config_loader import load_config
from logger import setup_logging
from mod_checker import run_mod_check

def main():
    config = load_config("config.yaml")
    setup_logging(config)

    run_mod_check(config)

if __name__ == "__main__":
    main()