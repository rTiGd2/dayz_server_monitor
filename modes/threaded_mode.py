# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import logging
import concurrent.futures
import steam_api

def fetch(mod):
    try:
        mod_info = steam_api.get_mod_info(mod['workshop_id'])
        return {
            "workshop_id": mod['workshop_id'],
            "title": mod_info['title'],
            "time_updated": mod_info['time_updated']
        }
    except Exception as e:
        logging.exception(f"Threaded failed for mod {mod['workshop_id']}: {e}")
        return None

def run(config, info, mods):
    logging.info("Running THREADED mode")

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch, mod) for mod in mods]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    return results