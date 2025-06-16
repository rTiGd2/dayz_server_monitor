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
import discord_notifier

PERF_LOG_FILE = "data/performance_log.csv"

def run_mod_check(config, templates=None):
    if not config.get("mod_checking_enabled", True):
        logging.info("Mod checking disabled via config.")
        return

    # Ensure templates is constructed if not passed
    if templates is None:
        locale = config.get("locale", "en_GB")
        templates = TemplateLoader(locale)

    start_time = time.perf_counter()
    mode = config.get("mod_check_mode", "serial").lower()
    ip = config["server"]["ip"]
    port = config["server"]["port"]

    try:
        info, mods = server_query.query_server(ip, port)
    except TimeoutError:
        logging.error(f"Server query timed out at {ip}:{port}")
        output_handler.output_messages.append(f"❌ Failed to query server: Timed out at {ip}:{port}")
        return
    except Exception as e:
        logging.exception(f"Server query failed: {e}")
        output_handler.output_messages.append(f"❌ Failed to query server: {e}")
        return

    # Compute next reboot time once, for use in both outputs
    next_reboot = None
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
    mod_messages = []  # Collect mod messages for summary and Discord output

    for mod in mod_results:
        workshop_id = mod['workshop_id']
        title = mod['title']
        time_updated = mod['time_updated']

        current_state[workshop_id] = {
            "title": title,
            "time_updated": time_updated
        }

        previous_mod = previous_state.get(workshop_id)
        # Prepare both time formats
        local_time = datetime.fromtimestamp(time_updated).strftime("%Y-%m-%d %H:%M:%S")
        discord_time = f"<t:{int(time_updated)}:F>"

        if not previous_mod:
            mod_messages.append({
                "type": "new",
                "title": title,
                "local_time": local_time,
                "discord_time": discord_time
            })
            changes_detected = True
        elif time_updated > previous_mod['time_updated']:
            mod_messages.append({
                "type": "updated",
                "title": title,
                "local_time": local_time,
                "discord_time": discord_time
            })
            changes_detected = True

    if config["output"].get("show_removed_mods", True):
        for workshop_id in previous_state:
            if workshop_id not in current_state:
                removed_title = previous_state[workshop_id]['title']
                mod_messages.append({
                    "type": "removed",
                    "title": removed_title,
                    "local_time": "",
                    "discord_time": ""
                })
                changes_detected = True

    state_manager.save_state(current_state)

    if not changes_detected and not config["output"].get("silent_on_no_changes", False):
        mod_messages.append({
            "type": "no_changes",
            "title": "",
            "local_time": "",
            "discord_time": ""
        })

    end_time = time.perf_counter()
    duration = end_time - start_time
    logging.info(f"Mod check completed in {duration:.2f} seconds using mode '{mode}'.")

    log_performance(mode, duration)
    summarize_performance()

    # Output only the summary (console, file, discord)
    summary_message = build_summary_with_mods(
        config, templates, mod_messages, server_info=info, next_reboot=next_reboot, output_to_discord=False
    )
    output_handler.send_output(config, summary_message)

    # Discord summary output (respect silent_on_no_changes)
    if config["output"].get("to_discord", False):
        if changes_detected or not config["output"].get("silent_on_no_changes", False):
            discord_summary_message = build_summary_with_mods(
                config, templates, mod_messages, server_info=info, next_reboot=next_reboot, output_to_discord=True
            )
            discord_notifier.dispatch_discord(config, discord_summary_message)
        else:
            logging.info("No mod changes detected and silent_on_no_changes is True; not sending Discord output.")

def build_summary_with_mods(config, templates, mod_messages, server_info, next_reboot, output_to_discord=False):
    summary_lines = []
    summary_lines.append("**📢 DayZ Server Monitor Summary**")
    summary_lines.append("------------------------------------")

    # Per-mod output
    for msg in mod_messages:
        if msg["type"] == "new":
            line = templates.format("output", "mod_new.txt", title=msg["title"])
            summary_lines.append(line)
        elif msg["type"] == "updated":
            timestamp = msg["discord_time"] if output_to_discord else msg["local_time"]
            line = templates.format(
                "output", "mod_updated.txt", title=msg["title"], timestamp=timestamp
            )
            summary_lines.append(line)
        elif msg["type"] == "removed":
            line = templates.format("output", "mod_removed.txt", title=msg["title"])
            summary_lines.append(line)
        elif msg["type"] == "no_changes":
            line = templates.format("output", "no_changes.txt")
            summary_lines.append(line)

    # Map/server info
    if server_info.get("map"):
        summary_lines.append(f"Map: {server_info['map']}")

    # Next reboot
    if config['output'].get('show_next_reboot', True) and next_reboot:
        if output_to_discord:
            unix_ts = int(next_reboot.timestamp())
            discord_time = f"<t:{unix_ts}:F>"
            summary_lines.append(f"Next reboot scheduled at: {discord_time}")
        else:
            summary_lines.append(f"Next reboot scheduled at: {next_reboot.strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(summary_lines)

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
