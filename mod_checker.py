# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: mod_checker.py
# Purpose: Run mod check, compare states, and output results
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
import discord_notifier  # NEW: for summary dispatch

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

    locale = config.get("locale", "en_GB")
    templates = TemplateLoader(locale)

    # Compute next reboot time once, for use in both outputs
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

        # Always print the local time version to the console/log/other outputs
        output_handler.send_output(
            config, f"Next reboot scheduled at: {next_reboot.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    previous_state = state_manager.load_state()
    current_state = {}

    logging.info(f"Selected mode: {mode}")
    if mode == "serial":
        mod_results = serial_mode.run(config, info, mods)
    elif mode == "threaded":
        mod_results = threaded_mode.run(config, info, mods)
    elif mode == "async":
        mod_results = async_mode.run(config, info, mods)
    else:
        logging.warning(f"Unknown mode {mode}, defaulting to serial.")
        mod_results = serial_mode.run(config, info, mods)

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
            message = templates.format("output", "mod_new.txt", title=title)
            output_handler.send_output(config, message)
            changes_detected = True
        elif time_updated > previous_mod['time_updated']:
            message = templates.format("output", "mod_updated.txt", title=title, timestamp=timestamp)
            output_handler.send_output(config, message)
            changes_detected = True

    if config["output"].get("show_removed_mods", True):
        for workshop_id in previous_state:
            if workshop_id not in current_state:
                removed_title = previous_state[workshop_id]['title']
                message = templates.format("output", "mod_removed.txt", title=removed_title)
                output_handler.send_output(config, message)
                changes_detected = True

    state_manager.save_state(current_state)

    if not changes_detected and not config["output"].get("silent_on_no_changes", False):
        message = templates.format("output", "no_changes.txt")
        output_handler.send_output(config, message)

    end_time = time.perf_counter()
    duration = end_time - start_time
    logging.info(f"Mod check completed in {duration:.2f} seconds using mode '{mode}'.")

    log_performance(mode, duration)
    summarize_performance()

    # ✅ Discord summary output (respect silent_on_no_changes)
    if config["output"].get("to_discord", False):
        if changes_detected or not config["output"].get("silent_on_no_changes", False):
            # Patch: Insert Discord timestamp for next reboot if show_next_reboot is enabled
            summary_message = output_handler.get_discord_summary(config, templates)
            if config['output'].get('show_next_reboot', True):
                unix_ts = int(next_reboot.timestamp())
                discord_time = f"<t:{unix_ts}:F>"
                # Try to replace any pre-existing 'Next reboot scheduled at:' line
                import re
                if re.search(r"Next reboot scheduled at:.*", summary_message):
                    summary_message = re.sub(
                        r"Next reboot scheduled at:.*",
                        f"Next reboot scheduled at: {discord_time}",
                        summary_message
                    )
                else:
                    summary_message += f"\nNext reboot scheduled at: {discord_time}"
            discord_notifier.dispatch_discord(config, summary_message)
        else:
            logging.info("No mod changes detected and silent_on_no_changes is True; not sending Discord output.")

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
