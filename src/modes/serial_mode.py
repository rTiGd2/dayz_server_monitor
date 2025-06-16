# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: modes/serial_mode.py
# Purpose: Mod metadata lookup in serial mode (single-threaded)
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
import steam_api

def run(config, info, mods):
    logging.info("[SERIAL] Running SERIAL mode with %d mods", len(mods))

    results = []
    for i, mod in enumerate(mods, 1):
        workshop_id = mod.get("workshop_id")
        if not workshop_id:
            logging.warning(f"[SERIAL] Skipping mod with missing ID at index {i}")
            continue

        try:
            logging.debug(f"[SERIAL] Fetching mod info for {workshop_id}")
            mod_info = steam_api.get_mod_info(workshop_id)
            results.append({
                "workshop_id": workshop_id,
                "title": mod_info.get('title', 'Unknown'),
                "time_updated": mod_info.get('time_updated', 0)
            })
        except Exception as e:
            logging.exception(f"[SERIAL] Failed for mod {workshop_id}: {e}")

    logging.info("[SERIAL] Completed %d mods.", len(results))
    return results