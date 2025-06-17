# DayZ Server Monitor
# File: mod_checker.py
#
# Mod check and reporting logic for DayZ Server Monitor.
# Supports serial, threaded, and async processing models.
# Reports changelogs for added/updated mods if configured, with truncation.
# NEVER outputs links to Discord, file, or console.
# Cleans changelog: removes unsupported BBCode, stray tags, blank/formatting lines, links, and images.
#
# (C) Tig Campbell-Moore, rTiGd2/dayz_server_monitor contributors
# License: CC BY-NC 4.0

import logging
import time
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from src import server_query
from src import output_handler
from src.templates import TemplateLoader
from src import discord_notifier
from src import steam_api

from src.modes import serial_mode as serial_mode
from src.modes import threaded_mode as threaded_mode
from src.modes import async_mode as async_mode

from src.server_monitor_tracker import (
    update_performance,
    load_performance_stats,
    save_mod_tracking,
    load_mod_tracking,
)

PERF_LOG_FILE = Path("data/performance/performance_log.json")

def get_mod_attr(mod, key, default=None):
    if isinstance(mod, dict):
        return mod.get(key, default)
    return getattr(mod, key, default)

def get_mod_name(mod):
    for key in ("name", "mod_name", "title"):
        if isinstance(mod, dict) and key in mod:
            return mod[key]
        elif hasattr(mod, key):
            return getattr(mod, key)
    logging.warning(f"Could not find a name for mod: {mod}")
    return "<unknown>"

def get_mod_workshop_id(mod):
    wid = get_mod_attr(mod, "workshop_id", None)
    return str(wid) if wid is not None else None

def get_mod_changelog(mod):
    # Try common changelog keys
    for key in ("changelog", "description", "change_log", "log", "notes"):
        if isinstance(mod, dict) and key in mod:
            return mod[key]
        elif hasattr(mod, key):
            return getattr(mod, key)
    return ""

def bbcode_to_discord(text):
    """Convert common BBCode to Discord markdown. Strip all other BBCode tags, links, images, and blank lines."""
    if not text:
        return ""
    # Remove [img], [image], [url] tags and their content
    text = re.sub(r'\[img\](.*?)\[/img\]', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[image\](.*?)\[/image\]', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[url(=[^\]]*)?\](.*?)\[/url\]', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML links and images
    text = re.sub(r'<a\b[^>]*>(.*?)</a>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<img\b[^>]*>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Convert supported tags to Discord markdown
    text = re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[u\](.*?)\[/u\]', r'__\1__', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[s\](.*?)\[/s\]', r'~~\1~~', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove unsupported url/color/list/quote/etc tags
    text = re.sub(r'\[/?(url|color|list|quote|h[1-6]|img|image|spoiler|code|center|size|font|video|audio|flash|table|tr|td|th|hr|li|ol|ul|br|yt|youtube|media|left|right|justify|indent|outdent|sup|sub)(=[^\]]*)?\]', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove any other [tag] or [/tag]
    text = re.sub(r'\[/?[a-zA-Z0-9]+(=[^\]]*)?\]', '', text)
    # Remove lines containing only whitespace or only formatting (e.g. after stripping tags)
    lines = [l for l in text.splitlines() if l.strip() and not re.match(r'^[\*\_\~]+$', l.strip())]
    return "\n".join(lines)

def format_changelog_with_modname(changelog, mod_name):
    if not changelog or not mod_name:
        return bbcode_to_discord(changelog or "")
    plain_mod_name = re.sub(r'\[/?[a-z]+(=[^\]]*)?\]', '', mod_name, flags=re.IGNORECASE)
    decorated_name = f"__**{plain_mod_name}**__"
    changelog_strip = changelog.lstrip()
    modname_regex = r"^(\[b\]|\[u\])*" + re.escape(plain_mod_name) + r"(\[/u\]|\[/b\])*"
    match = re.match(modname_regex, changelog_strip, flags=re.IGNORECASE)
    if match:
        end = match.end()
        rest = changelog_strip[end:].lstrip(": \n")
        rest_formatted = bbcode_to_discord(rest)
        return f"{decorated_name} {rest_formatted}"
    else:
        return bbcode_to_discord(changelog)

def run_mod_check(config, templates=None):
    mods_cfg = config.get("mods", {})
    show_mod_changelog = mods_cfg.get("show_mod_changelog", True)
    max_changelog_lines = mods_cfg.get("max_changelog_lines", 10)
    mod_checking_enabled = mods_cfg.get("mod_checking_enabled", True)
    mod_check_mode = mods_cfg.get("mod_check_mode", "serial").lower()
    report_limit = mods_cfg.get("report_limit", 10)

    output_cfg = config.get('output', {})
    to_console = output_cfg.get('to_console', False)
    to_file = output_cfg.get('to_file', False)
    to_discord = output_cfg.get('to_discord', False)
    show_removed_mods = output_cfg.get('show_removed_mods', True)
    silent_on_no_changes = output_cfg.get('silent_on_no_changes', False)
    show_island = output_cfg.get('show_island', True)
    show_platform = output_cfg.get('show_platform', False)
    show_dedicated = output_cfg.get('show_dedicated', False)
    show_mod_count = output_cfg.get('show_mod_count', False)
    show_next_reboot = output_cfg.get('show_next_reboot', True)

    if not mod_checking_enabled:
        logging.info("Mod checking disabled via config.")
        return [], {}

    if templates is None:
        locale = config.get("locale", "en_GB")
        templates = TemplateLoader(locale)

    start_time = time.perf_counter()
    ip = config["server"]["ip"]
    port = config["server"]["port"]

    server_name = config.get("server_name", config.get("_config_file", "unnamed_server").replace(".yaml", ""))

    try:
        info, mods = server_query.query_server(ip, port)
    except TimeoutError:
        logging.error(f"Server query timed out at {ip}:{port}")
        output_handler.output_messages.append(f"❌ Failed to query server: Timed out at {ip}:{port}")
        return [], {}
    except Exception as e:
        logging.exception(f"Server query failed: {e}")
        output_handler.output_messages.append(f"❌ Failed to query server: {e}")
        return [], {}

    # Compute next reboot time (used in summary)
    next_reboot = None
    if show_next_reboot and "reboot" in config:
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

    # === Parallel processing model selection ===
    logging.info(f"[mod_checker] Using mod_check_mode: {mod_check_mode}")
    if mod_check_mode == "serial":
        mod_results = serial_mode.run(config, info, mods)
    elif mod_check_mode == "threaded":
        mod_results = threaded_mode.run(config, info, mods)
    elif mod_check_mode == "async":
        mod_results = async_mode.run(config, info, mods)
    else:
        logging.warning(f"[mod_checker] Unknown mod_check_mode '{mod_check_mode}', defaulting to serial")
        mod_results = serial_mode.run(config, info, mods)

    # Build current_mods_dict from mod_results (no changelogs stored)
    current_mods_dict = {}
    for base_mod, mod_res in zip(mods, mod_results):
        if not mod_res or not mod_res.get("workshop_id"):
            continue
        wid = str(mod_res["workshop_id"])
        current_mods_dict[wid] = {
            "name": mod_res.get("title", get_mod_name(mod_res)),
            "workshop_id": wid,
            "time_updated": mod_res.get("time_updated", 0),
        }

    previous_mods_dict = load_mod_tracking(server_name)
    prev_wids = set(previous_mods_dict.keys())
    curr_wids = set(current_mods_dict.keys())

    added_mods = curr_wids - prev_wids
    removed_mods = prev_wids - curr_wids

    updated_mods = []
    for wid in curr_wids & prev_wids:
        prev = previous_mods_dict[wid]
        curr = current_mods_dict[wid]
        if curr.get("time_updated", 0) > prev.get("time_updated", 0):
            updated_mods.append(wid)

    changes_detected = False
    mod_messages = []

    n_added = len(added_mods)
    n_updated = len(updated_mods)
    total_changes = n_added + n_updated

    if total_changes > report_limit:
        msg = {
            "type": "too_many",
            "title": "",
            "local_time": "",
            "discord_time": "",
            "changelog_text": "",
            "summary": f"{total_changes} mods updated/added, not reporting details in this post."
        }
        mod_messages = [msg]
        changes_detected = True
    else:
        # Report all ADDED mods (with changelog lookup/output if enabled)
        for wid in added_mods:
            mod = current_mods_dict[wid]
            name = mod["name"]
            time_updated = mod.get("time_updated", 0)
            local_time = datetime.fromtimestamp(time_updated).strftime("%Y-%m-%d %H:%M:%S") if time_updated else ""
            discord_time = f"<t:{int(time_updated)}:F>" if time_updated else ""
            changelog_text = ""
            if show_mod_changelog:
                # Lookup changelog live from Steam API
                try:
                    steam_info = steam_api.get_mod_info(wid)
                    changelog = steam_info.get("description", "")
                except Exception:
                    changelog = ""
                if changelog:
                    changelog_lines = changelog.splitlines()
                    # Remove blank lines after BBCode/HTML strip
                    changelog_lines = [line for line in changelog_lines if line.strip()]
                    if len(changelog_lines) > max_changelog_lines:
                        changelog_text = "\n".join(changelog_lines[:max_changelog_lines])
                        changelog_text += "\n[...] (truncated)"
                    else:
                        changelog_text = "\n".join(changelog_lines)
                    changelog_text = format_changelog_with_modname(changelog_text, name)
            msg = {
                "type": "new",
                "title": name,
                "local_time": local_time,
                "discord_time": discord_time,
                "changelog_text": changelog_text
            }
            mod_messages.append(msg)
            changes_detected = True

        # Report all UPDATED mods (with changelog lookup/output if enabled)
        for wid in updated_mods:
            mod = current_mods_dict[wid]
            name = mod["name"]
            time_updated = mod.get("time_updated", 0)
            local_time = datetime.fromtimestamp(time_updated).strftime("%Y-%m-%d %H:%M:%S") if time_updated else ""
            discord_time = f"<t:{int(time_updated)}:F>" if time_updated else ""
            changelog_text = ""
            if show_mod_changelog:
                # Lookup changelog live from Steam API
                try:
                    steam_info = steam_api.get_mod_info(wid)
                    changelog = steam_info.get("description", "")
                except Exception:
                    changelog = ""
                if changelog:
                    changelog_lines = changelog.splitlines()
                    changelog_lines = [line for line in changelog_lines if line.strip()]
                    if len(changelog_lines) > max_changelog_lines:
                        changelog_text = "\n".join(changelog_lines[:max_changelog_lines])
                        changelog_text += "\n[...] (truncated)"
                    else:
                        changelog_text = "\n".join(changelog_lines)
                    changelog_text = format_changelog_with_modname(changelog_text, name)
            msg = {
                "type": "updated",
                "title": name,
                "local_time": local_time,
                "discord_time": discord_time,
                "changelog_text": changelog_text
            }
            mod_messages.append(msg)
            changes_detected = True

    # Report REMOVED mods
    if show_removed_mods:
        for wid in removed_mods:
            mod = previous_mods_dict[wid]
            mod_messages.append({
                "type": "removed",
                "title": mod.get("name", wid),
                "local_time": "",
                "discord_time": "",
                "changelog_text": ""
            })
            changes_detected = True

    # If no changes, emit "no changes" message
    if not changes_detected and not silent_on_no_changes:
        mod_messages.append({
            "type": "no_changes",
            "title": "",
            "local_time": "",
            "discord_time": "",
            "changelog_text": ""
        })

    end_time = time.perf_counter()
    duration = end_time - start_time
    logging.info(f"Mod check completed in {duration:.2f} seconds using mode '{mod_check_mode}'.")

    performance_stats = {
        "duration_seconds": duration,
        "check_mode": mod_check_mode,
        "mod_count": len(current_mods_dict),
        "timestamp": datetime.now().isoformat()
    }
    update_performance(server_name, performance_stats)

    log_performance(duration)
    summarize_performance()

    server_info = {
        "map": get_mod_attr(info, "island") or get_mod_attr(info, "map"),
        "platform": get_mod_attr(info, "platform"),
        "dedicated": get_mod_attr(info, "dedicated"),
        "mods_count": get_mod_attr(info, "mods_count", len(mods)),
    }

    summary_message = build_summary_with_mods(
        config, templates, mod_messages, server_info=server_info, mods=mods, next_reboot=next_reboot, output_to_discord=False, server_name=server_name
    )
    output_handler.send_output(config, summary_message)

    if to_discord:
        discord_summary_message = build_summary_with_mods(
            config, templates, mod_messages, server_info=server_info, mods=mods, next_reboot=next_reboot, output_to_discord=True, server_name=server_name
        )
        if len(discord_summary_message) > 2000:
            discord_summary_message = f"Too many mod changes to display. ({total_changes} mods updated/added.)"
        if changes_detected or not silent_on_no_changes:
            discord_notifier.dispatch_discord(config, discord_summary_message)

    save_mod_tracking(server_name, current_mods_dict)

    return list(curr_wids), performance_stats

def build_summary_with_mods(config, templates, mod_messages, server_info, mods, next_reboot, output_to_discord=False, server_name=None):
    summary_lines = []
    if server_name:
        summary_lines.append(f"**📢 DayZ Server Monitor Summary for {server_name}**")
    else:
        summary_lines.append("**📢 DayZ Server Monitor Summary**")
    summary_lines.append("------------------------------------")

    output_cfg = config.get('output', {})

    if output_cfg.get('show_platform', False) and server_info.get('platform'):
        summary_lines.append(f"Platform: {server_info['platform']}")
    if output_cfg.get('show_dedicated', False) and server_info.get('dedicated') is not None:
        summary_lines.append(f"Dedicated: {'Yes' if server_info['dedicated'] else 'No'}")
    if output_cfg.get('show_island', True) and server_info.get('map'):
        summary_lines.append(f"Island: {server_info['map']}")
    if output_cfg.get('show_mod_count', False):
        summary_lines.append(f"Mod Count: {server_info.get('mods_count', len(mods))}")

    for msg in mod_messages:
        if msg.get("type") == "too_many":
            summary_lines.append(msg.get("summary"))
            continue

        if msg["type"] == "new":
            line = templates.format("output", "mod_new.txt", title=msg["title"])
            summary_lines.append(f"{line}")
            if msg.get("changelog_text"):
                changelog = msg["changelog_text"]
                summary_lines.append(f"Changelog:\n{changelog}")
        elif msg["type"] == "updated":
            timestamp = msg["discord_time"] if output_to_discord else msg["local_time"]
            line = templates.format("output", "mod_updated.txt", title=msg["title"], timestamp=timestamp)
            summary_lines.append(f"{line}")
            if msg.get("changelog_text"):
                changelog = msg["changelog_text"]
                summary_lines.append(f"Changelog:\n{changelog}")
        elif msg["type"] == "removed":
            line = templates.format("output", "mod_removed.txt", title=msg["title"])
            summary_lines.append(line)
        elif msg["type"] == "no_changes":
            line = templates.format("output", "no_changes.txt")
            summary_lines.append(line)

    if output_cfg.get('show_next_reboot', True) and next_reboot:
        if output_to_discord:
            unix_ts = int(next_reboot.timestamp())
            discord_time = f"<t:{unix_ts}:F>"
            summary_lines.append(f"Next reboot scheduled at: {discord_time}")
        else:
            summary_lines.append(f"Next reboot scheduled at: {next_reboot.strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(summary_lines)

def log_performance(duration):
    """Append performance log entry for this run."""
    PERF_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    perf_entry = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2)
    }
    if PERF_LOG_FILE.exists():
        try:
            with PERF_LOG_FILE.open("r") as f:
                records = json.load(f)
        except Exception:
            records = []
    else:
        records = []
    records.append(perf_entry)
    with PERF_LOG_FILE.open("w") as f:
        json.dump(records, f, indent=2)

def summarize_performance(last_N=20):
    """Summarize recent performance logs and log average run time."""
    if not PERF_LOG_FILE.exists():
        return
    try:
        with PERF_LOG_FILE.open("r") as f:
            records = json.load(f)
    except Exception:
        logging.warning("Could not read performance log.")
        return
    recent = records[-last_N:] if len(records) > last_N else records
    if not recent:
        return
    avg = sum(rec["duration_seconds"] for rec in recent) / len(recent)
    logging.info(f"Recent Performance Summary (last {len(recent)} runs): Avg: {avg:.2f} sec")
