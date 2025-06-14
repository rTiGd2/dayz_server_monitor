# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import dayzquery
import logging

def query_server(ip, port):
    server_address = (ip, port)
    try:
        ruleset = dayzquery.dayz_rules(server_address)
    except TimeoutError:
        logging.error(f"Timed out querying DayZ server at {ip}:{port}")
        raise
    except Exception as e:
        logging.exception(f"Failed to query DayZ server: {e}")
        raise

    info = {
        "island": ruleset.island,
        "platform": ruleset.platform,
        "dedicated": ruleset.dedicated,
        "time_left": ruleset.time_left,
        "mods_count": ruleset.mods_count
    }

    mods = []
    for mod in ruleset.mods:
        mods.append({
            'name': mod.name,
            'workshop_id': str(mod.workshop_id)
        })

    return info, mods