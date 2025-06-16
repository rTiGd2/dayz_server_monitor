# Project: DayZ Server Monitor
# File: config_loader.py
# Purpose: Load and merge monitor-wide, per-server, defaults, and required config yaml files for multi-server/overrides support.
#          Now supports required fields within nested blocks (e.g. server.ip) and validates against unwanted top-level ip/port.
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import os
import yaml
from glob import glob
from copy import deepcopy

def load_yaml(path):
    """
    Load YAML file, return empty dict if not found or empty.
    """
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def get_nested(config, dotted_key):
    """
    Fetch a nested value from dict using dot notation (e.g., 'server.ip').
    """
    keys = dotted_key.split('.')
    d = config
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d

def set_nested(config, dotted_key, value):
    """
    Set a nested value in dict using dot notation (e.g., 'server.ip').
    """
    keys = dotted_key.split('.')
    d = config
    for k in keys[:-1]:
        if k not in d or not isinstance(d[k], dict):
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value

def merge_dicts(a, b):
    """
    Merge dict b into dict a (a is base, b is override), recursively.
    """
    for k, v in b.items():
        if isinstance(v, dict) and k in a and isinstance(a[k], dict):
            merge_dicts(a[k], v)
        else:
            a[k] = deepcopy(v)
    return a

def load_required_with_metadata(required_yaml):
    """
    Return a dict mapping dotted keys to type/description.
    """
    if not required_yaml or "required" not in required_yaml:
        return {}
    return required_yaml["required"]

def merge_server_blocks(base, override):
    """
    Merge 'server' blocks from two configs (base <- override).
    """
    merged = deepcopy(base.get('server', {}))
    override_block = override.get('server', {})
    if override_block:
        merge_dicts(merged, override_block)
    return merged

def load_configs(config_dir="config"):
    """
    Load configs for all servers, merging defaults, monitor.yaml, and server-specific YAMLs.
    Special handling for 'server' block: merges global (monitor.yaml) 'server' block with per-server override.
    Returns: ([server_configs], required_dict)
    """
    defaults = load_yaml(os.path.join(config_dir, "config.defaults.yaml"))
    required_yaml = load_yaml(os.path.join(config_dir, "config.required.yaml"))
    required = load_required_with_metadata(required_yaml)
    monitor = load_yaml(os.path.join(config_dir, "monitor.yaml"))
    yamls = sorted(glob(os.path.join(config_dir, "*.yaml")))
    server_configs = []

    monitor_server = monitor.get("server", {})

    for ypath in yamls:
        fname = os.path.basename(ypath)
        if fname in ("monitor.yaml", "config.defaults.yaml", "config.required.yaml"):
            continue
        server = load_yaml(ypath)
        merged = {}
        # Start with defaults and monitor.yaml
        merge_dicts(merged, deepcopy(defaults))
        merge_dicts(merged, deepcopy(monitor))
        merge_dicts(merged, server)
        # Special handling: merge 'server' block (monitor -> per-server)
        merged['server'] = merge_server_blocks(monitor, server)
        merged["_config_file"] = fname
        server_configs.append(merged)

    # Fallback: single-server mode (monitor.yaml only)
    if not server_configs and monitor:
        merged = {}
        merge_dicts(merged, deepcopy(defaults))
        merge_dicts(merged, deepcopy(monitor))
        merged['server'] = merge_server_blocks(monitor, monitor)
        merged["_config_file"] = "monitor.yaml"
        server_configs = [merged]

    return server_configs, required

def validate_required(config, required, logger):
    """
    Validates that all required config options (with dot notation) are present.
    Logs error and returns False if any are missing.
    Also checks that ip/port are not present at the top-level (should be in server block).
    """
    is_valid = True
    # Warn/error if ip/port are present at top level
    for forbidden in ("ip", "port"):
        if forbidden in config:
            logger.error(f"Config error: '{forbidden}' must be inside the 'server:' block, not top-level.")
            is_valid = False
    for req_key, meta in required.items():
        if get_nested(config, req_key) is None:
            desc = meta.get("description", "") if isinstance(meta, dict) else ""
            logger.error(f"Missing required config option: {req_key}"
                         + (f" ({desc})" if desc else ""))
            is_valid = False
    return is_valid
