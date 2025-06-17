# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: state_manager.py
# Purpose: Handle saving and loading of mod state data
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import json
import logging
import shutil
from pathlib import Path

STATE_FILE = Path("data/previous_run.json")

def load_state():
    if not STATE_FILE.exists():
        logging.info("No previous state file found.")
        return {}
    try:
        with STATE_FILE.open('r') as f:
            state = json.load(f)
            logging.debug(f"Loaded previous state with {len(state)} mods.")
            return state
    except Exception as e:
        logging.error(f"Failed to load previous state: {e}")
        return {}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        if STATE_FILE.exists():
            shutil.copy(STATE_FILE, str(STATE_FILE) + ".bak")
        with STATE_FILE.open('w') as f:
            json.dump(state, f, indent=4)
        logging.debug(f"Saved state with {len(state)} mods.")
    except Exception as e:
        logging.error(f"Failed to save state: {e}")
