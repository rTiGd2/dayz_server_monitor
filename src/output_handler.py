# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: output_handler.py
# Purpose: Handle and store all output messages for file, console, and Discord
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging

output_messages = []

def send_output(config, message):
    # Store all messages in output_messages for use by summary/discord/etc.
    output_messages.append(message)

    # Only output to console/file if enabled in config
    if config['output'].get("to_console", False):
        logging.info(message)

    # If output to file, use the main logging system—do not write files directly here
    # This preserves the new logging policy: all output is routed through logging
    # If a dedicated file output is needed, this must be handled by a FileHandler in logger.py

def get_all_output():
    return "\n".join(output_messages)

def build_summary(config, templates, server_info=None, next_reboot=None):
    """
    Build the summary for all outputs, using localized templates for extra info.
    server_info: the latest DayZ query info dict (or similar object)
    next_reboot: a datetime, or None
    """
    if templates is None:
        raise ValueError("templates argument to build_summary cannot be None. Pass a valid TemplateLoader instance.")

    body = "\n".join(output_messages)
    summary = templates.format("discord", "summary.txt", body=body)

    extra_lines = []
    info = server_info or {}

    # Use correct template filenames based on your structure!
    if config['output'].get('show_island', True):
        # Use server_info if available, otherwise fallback to config, then empty string
        island = info.get('island') or config.get('server', {}).get('island') or ""
        extra_lines.append(templates.format("output", "server_island.txt", island=island))

    if config['output'].get('show_platform', True):
        platform = info.get('platform') or config.get('server', {}).get('platform') or ""
        extra_lines.append(templates.format("output", "server_platform.txt", platform=platform))

    if config['output'].get('show_dedicated', True):
        # Try bool or string representations from query
        dedicated = info.get('dedicated')
        if dedicated is None:
            dedicated = config.get('server', {}).get('dedicated')
        if dedicated is None:
            dedicated = ""
        extra_lines.append(templates.format("output", "server_dedicated.txt", dedicated=dedicated))

    if config['output'].get('show_mod_count', True):
        # Attempt to count mods from server query if available
        mod_count = None
        if "mods" in info and isinstance(info["mods"], list):
            mod_count = len(info["mods"])
        elif "mod_count" in info:
            mod_count = info["mod_count"]
        elif "mod_count" in config.get("server", {}):
            mod_count = config["server"]["mod_count"]
        else:
            mod_count = ""
        extra_lines.append(templates.format("output", "mod_count.txt", mod_count=mod_count))

    if config['output'].get('show_next_reboot', True) and next_reboot:
        # Use localized template for next reboot
        extra_lines.append(
            templates.format("output", "next_reboot.txt", next_reboot=next_reboot.strftime('%Y-%m-%d %H:%M:%S'))
        )

    if extra_lines:
        summary += "\n" + "\n".join(extra_lines)

    return summary
