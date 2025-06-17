# DayZ Server Monitor
# File: server_monitor_tracker.py
# Purpose: Track mod state and performance per server using JSON in data/tracking and data/performance.
# Author: Tig Campbell-Moore, Copilot
# License: CC BY-NC 4.0

from pathlib import Path
import json

TRACKING_DIR = Path("data/tracking")
PERFORMANCE_DIR = Path("data/performance")

def _tracking_file(server_name):
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    return TRACKING_DIR / f"{server_name}_mods.json"

def _performance_file(server_name):
    PERFORMANCE_DIR.mkdir(parents=True, exist_ok=True)
    return PERFORMANCE_DIR / f"{server_name}_perf.json"

def save_mod_tracking(server_name, mods_dict):
    """Save the mod tracking info as a JSON dictionary keyed by workshop_id."""
    path = _tracking_file(server_name)
    with path.open("w") as f:
        json.dump(mods_dict, f, indent=2)

def load_mod_tracking(server_name):
    """Load the mod tracking info, returning a dict keyed by workshop_id."""
    path = _tracking_file(server_name)
    if not path.exists():
        return {}
    with path.open("r") as f:
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
    if path.exists():
        with path.open("r") as f:
            try:
                records = json.load(f)
            except Exception:
                records = []
    else:
        records = []
    records.append(stats)
    with path.open("w") as f:
        json.dump(records, f, indent=2)

def load_performance_stats(server_name, last_N=20):
    """Load the last N performance stats for a server."""
    path = _performance_file(server_name)
    if not path.exists():
        return []
    with path.open("r") as f:
        try:
            records = json.load(f)
        except Exception:
            return []
    return records[-last_N:] if len(records) > last_N else records
