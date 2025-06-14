# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import logging
import time
import csv
import os
from collections import defaultdict
import server_query
import state_manager
import output_handler
from templates import TemplateLoader
from datetime import datetime, timedelta
from modes import serial_mode, threaded_mode, async_mode

PERF_LOG_FILE = "data/performance_log.csv"

def run_mod_check(config):
    if not config.get("mod_checking_enabled", True):
        logging.info("Mod checking disabled via config.")
        return

    start_time = time.perf_counter()

    mode = config.get("mod_check_mode", "serial").lower()

    ip = config["server"]["ip"]
    port = config["server"]["port"]

    try:
        info, mods = server_query.query_server(ip, port)
    except TimeoutError:
        logging.error(f"Server query timed out at {ip}:{port}")
        output_handler.send_output(config, f"❌ Failed to query server: Timed out at {ip}:{port}")
        return
    except Exception as e:
        logging.exception(f"Server query failed: {e}")
        output_handler.send_output(config, f"❌ Failed to query server: {e}")
        return

    locale = config.get("locale", "en_US")
    templates = TemplateLoader(locale)

    # SERVER INFO OUTPUT (fully restored)
    if config['output'].get('show_island', True):
        output_handler.send_output(config, f"Island: {info['island']}")

    if config['output'].get('show_platform', True):
        output_handler.send_output(config, f"Platform: {info['platform']}")

    if config['output'].get('show_dedicated', True):
        output_handler.send_output(config, f"Dedicated: {info['dedicated']}")

    if config['output'].get('show_mod_count', True):
        output_handler.send_output(config, f"Mods installed: {info['mods_count']}")

    if config['output'].get('show_next_reboot', True):
        base_hour, base_minute = map(int, config['reboot']['base_time'].split(":"))
        interval = config['reboot']['interval_minutes']
        now = datetime.now()
        base = now.replace(hour=base_hour, minute=base_minute, second=0, microsecond=0)
        for i in range(0, 24 * 60, interval):
            reboot = base + timedelta(minutes=i)
            if reboot > now:
                next_reboot = reboot
                break
        else:
            next_reboot = base + timedelta(days=1)
        output_handler.send_output(config, f"Next reboot scheduled at: {next_reboot.strftime('%Y-%m-%d %H:%M:%S')}")

    # STATE LOADING
    previous_state = state_manager.load_state()
    current_state = {}

    logging.info(f"Selected mode: {mode}")

    # CORRECT MODE DISPATCH
    if mode == "serial":
        mod_results = serial_mode.run(config, info, mods)
    elif mode == "threaded":
        mod_results = threaded_mode.run(config, info, mods)
    elif mode == "async":
        mod_results = async_mode.run(config, info, mods)
    else:
        logging.warning(f"Unknown mode {mode}, defaulting to serial.")
        mod_results = serial_mode.run(config, info, mods)

    # STATE COMPARISON
    changes_detected = False
    for mod in mod_results:
        workshop_id = mod['workshop_id']
        title = mod['title']
        time_updated = mod['time_updated']
        timestamp = datetime.fromtimestamp(time_updated).strftime("%Y-%m-%d %H:%M:%S")

        current_state[workshop_id] = {
            "title": title,
            "time_updated": time_updated
        }

        previous_mod = previous_state.get(workshop_id)
        if not previous_mod:
            message = templates.format_template("mod_new.txt", title=title)
            output_handler.send_output(config, message)
            changes_detected = True
        elif time_updated > previous_mod['time_updated']:
            message = templates.format_template("mod_updated.txt", title=title, timestamp=timestamp)
            output_handler.send_output(config, message)
            changes_detected = True

    # REMOVED MODS
    if config["output"].get("show_removed_mods", True):
        for workshop_id in previous_state:
            if workshop_id not in current_state:
                removed_title = previous_state[workshop_id]['title']
                message = templates.format_template("mod_removed.txt", title=removed_title)
                output_handler.send_output(config, message)
                changes_detected = True

    state_manager.save_state(current_state)

    if not changes_detected:
        if not config["output"].get("silent_on_no_changes", False):
            message = templates.format_template("no_changes.txt")
            output_handler.send_output(config, message)

    # Performance logging
    end_time = time.perf_counter()
    duration = end_time - start_time
    logging.info(f"Mod check completed in {duration:.2f} seconds using mode '{mode}'.")

    log_performance(mode, duration)
    summarize_performance()


# Performance logging functions:

def log_performance(mode, duration):
    os.makedirs(os.path.dirname(PERF_LOG_FILE), exist_ok=True)
    is_new = not os.path.exists(PERF_LOG_FILE)
    with open(PERF_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["timestamp", "mode", "duration_seconds"])
        writer.writerow([datetime.now().isoformat(), mode, f"{duration:.2f}"])

def summarize_performance(last_N=20):
    if not os.path.exists(PERF_LOG_FILE):
        return

    mode_sums = defaultdict(lambda: [0, 0])
    with open(PERF_LOG_FILE, "r") as f:
        reader = list(csv.DictReader(f))
        recent = reader[-last_N:] if len(reader) > last_N else reader
        for row in recent:
            mode = row["mode"]
            duration = float(row["duration_seconds"])
            mode_sums[mode][0] += duration
            mode_sums[mode][1] += 1

    logging.info("Recent Performance Summary (last {} runs):".format(last_N))
    for mode, (total, count) in mode_sums.items():
        avg = total / count
        logging.info(f"  Mode: {mode:8s} | Avg: {avg:.2f} sec over {count} runs")