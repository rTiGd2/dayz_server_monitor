# DayZ Server Monitor
# File: mod_checker.py
# Prevents Discord embeds/previews by never emitting bare URLs and uses correct changelog URLs.
# Uses zero-width space in URLs for extra Discord safety.

import logging
import time
import os
import json
from datetime import datetime, timedelta
import server_query
import output_handler
from templates import TemplateLoader
import discord_notifier
import steam_api

from server_monitor_tracker import (
    update_performance,
    load_performance_stats,
    save_mod_tracking,
    load_mod_tracking,
)

PERF_LOG_FILE = "data/performance/performance_log.json"

def break_embed(url: str) -> str:
    """Insert a zero-width space after protocol to prevent Discord preview."""
    return url.replace("://", "://\u200B")

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
    return get_mod_attr(mod, "changelog", "")

def get_mod_workshop_url(mod):
    wid = get_mod_workshop_id(mod)
    if wid:
        return f"https://steamcommunity.com/sharedfiles/filedetails/?id={wid}"
    return None

def get_mod_changelog_url(wid):
    if wid:
        return f"https://steamcommunity.com/sharedfiles/filedetails/changelog/{wid}"
    return None

def run_mod_check(config, templates=None):
    mods_cfg = config.get("mods", {})
    show_mod_changelog = mods_cfg.get("show_mod_changelog", True)
    max_changelog_lines = mods_cfg.get("max_changelog_lines", 10)
    show_mod_links = mods_cfg.get("show_mod_links", True)
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

    # Compute next reboot time once, for use in both outputs
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

    current_mods_dict = {}
    for mod in mods:
        wid = get_mod_workshop_id(mod)
        try:
            steam_info = steam_api.get_mod_info(wid)
        except Exception:
            steam_info = {'title': get_mod_name(mod), 'time_updated': 0, 'description': ''}
        mod_entry = {
            "name": steam_info.get('title', get_mod_name(mod)),
            "workshop_id": wid,
            "time_updated": steam_info.get('time_updated', 0),
            "changelog": steam_info.get('description', '') or get_mod_changelog(mod),
            "workshop_url": get_mod_workshop_url(mod)
        }
        current_mods_dict[wid] = mod_entry

    previous_mods_dict = load_mod_tracking(server_name)
    prev_wids = set(previous_mods_dict.keys())
    curr_wids = set(current_mods_dict.keys())

    # Added/removed by workshop_id:
    added_mods = curr_wids - prev_wids
    removed_mods = prev_wids - curr_wids

    # Updated: only those present in both, where update time increased
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
            "workshop_url": None,
            "discord_link_str": "",
            "changelog_text": "",
            "changelog_url": None,
            "summary": f"{total_changes} mods updated/added, not reporting details in this post."
        }
        mod_messages = [msg]
        changes_detected = True
    else:
        # Report all added mods
        for wid in added_mods:
            mod = current_mods_dict[wid]
            name = mod["name"]
            time_updated = mod.get("time_updated", 0)
            local_time = datetime.fromtimestamp(time_updated).strftime("%Y-%m-%d %H:%M:%S") if time_updated else ""
            discord_time = f"<t:{int(time_updated)}:F>" if time_updated else ""
            workshop_url = mod.get("workshop_url")
            changelog = mod.get("changelog", "")
            changelog_url = get_mod_changelog_url(wid)

            discord_link_str = ""
            if show_mod_links and workshop_url:
                safe_url = break_embed(workshop_url)
                discord_link_str = f" [Workshop]({safe_url})"
            elif workshop_url:
                safe_url = break_embed(workshop_url)
                discord_link_str = f" ([Workshop]({safe_url}))"

            changelog_text = ""
            if show_mod_changelog and changelog:
                changelog_lines = changelog.splitlines()
                if len(changelog_lines) > max_changelog_lines:
                    changelog_text = "\n".join(changelog_lines[:max_changelog_lines])
                    changelog_text += "\n[...] (truncated)"
                else:
                    changelog_text = changelog

            msg = {
                "type": "new",
                "title": name,
                "local_time": local_time,
                "discord_time": discord_time,
                "workshop_url": workshop_url,
                "discord_link_str": discord_link_str,
                "changelog_text": changelog_text,
                "changelog_url": changelog_url
            }
            mod_messages.append(msg)
            changes_detected = True

        # Report all updated mods
        for wid in updated_mods:
            mod = current_mods_dict[wid]
            name = mod["name"]
            time_updated = mod.get("time_updated", 0)
            local_time = datetime.fromtimestamp(time_updated).strftime("%Y-%m-%d %H:%M:%S") if time_updated else ""
            discord_time = f"<t:{int(time_updated)}:F>" if time_updated else ""
            workshop_url = mod.get("workshop_url")
            changelog = mod.get("changelog", "")
            changelog_url = get_mod_changelog_url(wid)

            discord_link_str = ""
            if show_mod_links and workshop_url:
                safe_url = break_embed(workshop_url)
                discord_link_str = f" [Workshop]({safe_url})"
            elif workshop_url:
                safe_url = break_embed(workshop_url)
                discord_link_str = f" ([Workshop]({safe_url}))"

            changelog_text = ""
            if show_mod_changelog and changelog:
                changelog_lines = changelog.splitlines()
                if len(changelog_lines) > max_changelog_lines:
                    changelog_text = "\n".join(changelog_lines[:max_changelog_lines])
                    changelog_text += "\n[...] (truncated)"
                else:
                    changelog_text = changelog

            msg = {
                "type": "updated",
                "title": name,
                "local_time": local_time,
                "discord_time": discord_time,
                "workshop_url": workshop_url,
                "discord_link_str": discord_link_str,
                "changelog_text": changelog_text,
                "changelog_url": changelog_url
            }
            mod_messages.append(msg)
            changes_detected = True

    if show_removed_mods:
        for wid in removed_mods:
            mod = previous_mods_dict[wid]
            mod_messages.append({
                "type": "removed",
                "title": mod.get("name", wid),
                "local_time": "",
                "discord_time": "",
                "workshop_url": None,
                "discord_link_str": "",
                "changelog_text": "",
                "changelog_url": None
            })
            changes_detected = True

    if not changes_detected and not silent_on_no_changes:
        mod_messages.append({
            "type": "no_changes",
            "title": "",
            "local_time": "",
            "discord_time": "",
            "workshop_url": None,
            "discord_link_str": "",
            "changelog_text": "",
            "changelog_url": None
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
        link_part = ""
        if msg.get("discord_link_str") and output_to_discord:
            link_part = msg["discord_link_str"]
        elif msg.get("workshop_url"):
            safe_url = break_embed(msg["workshop_url"])
            link_part = f" ([Workshop]({safe_url}))"

        if msg["type"] == "new":
            line = templates.format("output", "mod_new.txt", title=msg["title"])
            summary_lines.append(f"{line}{link_part}")
            if msg.get("changelog_text"):
                changelog = msg["changelog_text"]
                # Always use markdown link to avoid Discord embed/preview
                if output_to_discord and msg.get("changelog_url") and changelog.endswith("(truncated)"):
                    safe_changelog_url = break_embed(msg['changelog_url'])
                    changelog += f"\n[Full changelog]({safe_changelog_url})"
                summary_lines.append(f"Changelog:\n{changelog}")
        elif msg["type"] == "updated":
            timestamp = msg["discord_time"] if output_to_discord else msg["local_time"]
            line = templates.format(
                "output", "mod_updated.txt", title=msg["title"], timestamp=timestamp
            )
            summary_lines.append(f"{line}{link_part}")
            if msg.get("changelog_text"):
                changelog = msg["changelog_text"]
                # Always use markdown link to avoid Discord embed/preview
                if output_to_discord and msg.get("changelog_url") and changelog.endswith("(truncated)"):
                    safe_changelog_url = break_embed(msg['changelog_url'])
                    changelog += f"\n[Full changelog]({safe_changelog_url})"
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
    os.makedirs(os.path.dirname(PERF_LOG_FILE), exist_ok=True)
    perf_entry = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2)
    }
    if os.path.exists(PERF_LOG_FILE):
        with open(PERF_LOG_FILE, "r") as f:
            try:
                records = json.load(f)
            except Exception:
                records = []
    else:
        records = []
    records.append(perf_entry)
    with open(PERF_LOG_FILE, "w") as f:
        json.dump(records, f, indent=2)

def summarize_performance(last_N=20):
    if not os.path.exists(PERF_LOG_FILE):
        return
    with open(PERF_LOG_FILE, "r") as f:
        try:
            records = json.load(f)
        except Exception:
            logging.warning("Could not read performance log.")
            return
    recent = records[-last_N:] if len(records) > last_N else records
    if not recent:
        return
    avg = sum(rec["duration_seconds"] for rec in recent) / len(recent)
    logging.info(f"Recent Performance Summary (last {len(recent)} runs): Avg: {avg:.2f} sec")
