# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: state_manager.py
# Purpose: Handle saving and loading of mod state data
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import json
import os
import logging
import shutil

STATE_FILE = "data/previous_run.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        logging.info("No previous state file found.")
        return {}
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        logging.debug(f"Loaded previous state with {len(state)} mods.")
        return state

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if os.path.exists(STATE_FILE):
        shutil.copy(STATE_FILE, STATE_FILE + ".bak")
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)
    logging.debug(f"Saved state with {len(state)} mods.")