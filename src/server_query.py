# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: server_query.py
# Purpose: Query DayZ server and extract mod and system metadata
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import dayzquery # type: ignore
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
        "island": getattr(ruleset, "island", "Unknown"),
        "platform": getattr(ruleset, "platform", "Unknown"),
        "dedicated": getattr(ruleset, "dedicated", False),
        "time_left": getattr(ruleset, "time_left", 0),
        "mods_count": getattr(ruleset, "mods_count", 0)
    }

    mods = [{'name': mod.name, 'workshop_id': str(mod.workshop_id)} for mod in ruleset.mods]

    logging.debug(f"Queried server: {info['platform']} on {info['island']} with {len(mods)} mods.")
    return info, mods
