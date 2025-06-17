# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: monitor.py
# Purpose: Entrypoint for the monitoring process, with multi-server support, config defaults, required validation, advanced logging/rotation,
#          and persistent tracking of mod changes and per-server performance.
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import sys
import traceback
import logging
from src.config_loader import load_configs, validate_required
from src.logger import setup_logging
import src.mod_checker as mod_checker
from src.templates import TemplateLoader

# Import tracking utilities
from src.server_monitor_tracker import (
    detect_mod_changes,
    update_performance,
    load_performance_stats,
)

def main():
    try:
        # Updated: load_configs now returns (raw_configs, required, validated_pydantic_configs)
        raw_configs, required, pydantic_configs = load_configs("config")

        # Initialize logging once (using the first config, or default if none)
        config_for_logging = raw_configs[0] if raw_configs else {}
        setup_logging(config_for_logging)

        for raw_config, pydantic_config in zip(raw_configs, pydantic_configs):
            # Use raw_config for legacy dict-based code, pydantic_config for new-style attribute access
            server_name = raw_config.get("server_name", raw_config.get("_config_file", "unnamed_server").replace(".yaml", ""))
            if not validate_required(raw_config, required, None):
                logging.error(f"Skipping server {server_name} due to missing required config.")
                continue

            logging.info(f"Starting monitor for {server_name}")

            # Use locale from config (raw or pydantic)
            locale = getattr(pydantic_config, "locale", None) or raw_config.get("locale", "en_GB")
            templates = TemplateLoader(locale)

            try:
                # --- Run mod check and track mods ---
                # Pass raw_config for legacy code. Update to use pydantic_config where possible.
                mod_check_result = mod_checker.run_mod_check(raw_config, templates)
                if isinstance(mod_check_result, tuple) and len(mod_check_result) == 2:
                    current_mod_list, performance_stats = mod_check_result
                else:
                    # Backward compatibility: only mod list returned, or nothing returned
                    current_mod_list = mod_check_result if isinstance(mod_check_result, list) else []
                    performance_stats = {}

                # --- Mod change detection and persistence ---
                added_mods, removed_mods = detect_mod_changes(server_name, current_mod_list)
                if added_mods or removed_mods:
                    logging.info(f"Server {server_name}: Mods changed!")
                    if added_mods:
                        logging.info(f"Added mods: {added_mods}")
                    if removed_mods:
                        logging.info(f"Removed mods: {removed_mods}")
                else:
                    logging.info(f"Server {server_name}: No mod changes detected.")

                # --- Performance tracking and persistence ---
                if performance_stats:
                    update_performance(server_name, performance_stats)
                    last_stats = load_performance_stats(server_name)
                    logging.info(f"Server {server_name} last performance: {last_stats}")

            except Exception as e:
                logging.error("Unhandled exception during mod check")
                logging.error(traceback.format_exc())
                # Continue with next server instead of exiting the whole process

    except Exception as e:
        # If config loading or top-level fails, log to stderr and exit
        print("Critical: unhandled exception during monitor startup", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
