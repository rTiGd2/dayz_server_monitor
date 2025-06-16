# DayZ Server Monitor
# File: server_monitor_tracker.py
# Purpose: Track mod state and performance per server using JSON in data/tracking and data/performance.
# Author: Tig Campbell-Moore, Copilot
# License: CC BY-NC 4.0

import os
import json

TRACKING_DIR = "data/tracking"
PERFORMANCE_DIR = "data/performance"

def _tracking_file(server_name):
    os.makedirs(TRACKING_DIR, exist_ok=True)
    return os.path.join(TRACKING_DIR, f"{server_name}_mods.json")

def _performance_file(server_name):
    os.makedirs(PERFORMANCE_DIR, exist_ok=True)
    return os.path.join(PERFORMANCE_DIR, f"{server_name}_perf.json")

def save_mod_tracking(server_name, mods_dict):
    """Save the mod tracking info as a JSON dictionary keyed by workshop_id."""
    path = _tracking_file(server_name)
    with open(path, "w") as f:
        json.dump(mods_dict, f, indent=2)

def load_mod_tracking(server_name):
    """Load the mod tracking info, returning a dict keyed by workshop_id."""
    path = _tracking_file(server_name)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def detect_mod_changes(server_name, current_mod_names):
    """Detect added/removed mods by mod name (for summary purposes)."""
    prev = load_mod_tracking(server_name)
    prev_names = set((mod["name"] for mod in prev.values()))
    curr_names = set(current_mod_names)
    added = curr_names - prev_names
    removed = prev_names - curr_names
    return added, removed

def update_performance(server_name, stats):
    """Append a performance record for a server to its JSON log."""
    path = _performance_file(server_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                records = json.load(f)
            except Exception:
                records = []
    else:
        records = []
    records.append(stats)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)

def load_performance_stats(server_name, last_N=20):
    """Load the last N performance stats for a server."""
    path = _performance_file(server_name)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            records = json.load(f)
        except Exception:
            return []
    return records[-last_N:] if len(records) > last_N else records
