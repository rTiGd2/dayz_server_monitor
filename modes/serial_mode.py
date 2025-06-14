# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import logging
import steam_api

def run(config, info, mods):
    logging.info("Running SERIAL mode")

    results = []
    for mod in mods:
        try:
            mod_info = steam_api.get_mod_info(mod['workshop_id'])
            results.append({
                "workshop_id": mod['workshop_id'],
                "title": mod_info['title'],
                "time_updated": mod_info['time_updated']
            })
        except Exception as e:
            logging.exception(f"Failed to fetch mod {mod['workshop_id']}: {e}")

    return results