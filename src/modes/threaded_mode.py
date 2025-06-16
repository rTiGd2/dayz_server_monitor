# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: modes/threaded_mode.py
# Purpose: Mod metadata lookup using multithreading for parallelism
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
import concurrent.futures
from src import steam_api

def fetch(mod):
    workshop_id = mod.get('workshop_id')
    if not workshop_id:
        logging.warning("[THREADED] Skipping mod with missing ID")
        return None
    try:
        mod_info = steam_api.get_mod_info(workshop_id)
        return {
            "workshop_id": workshop_id,
            "title": mod_info.get("title", "Unknown"),
            "time_updated": mod_info.get("time_updated", 0)
        }
    except Exception as e:
        logging.exception(f"[THREADED] Error for mod {workshop_id}: {e}")
        return None

def run(config, info, mods):
    logging.info("[THREADED] Running with %d mods", len(mods))
    results = []
    max_workers = config.get("threaded_mode", {}).get("max_workers", 10)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch, mod) for mod in mods]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    logging.info("[THREADED] Completed %d mods", len(results))
    return results
