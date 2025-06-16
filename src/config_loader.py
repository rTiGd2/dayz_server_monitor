# Project: DayZ Server Monitor
# File: config_loader.py
# Purpose: Load and merge monitor-wide, per-server, defaults, and required config yaml files for multi-server/overrides support.
#          Now supports required fields within nested blocks (e.g. server.ip) and validates against unwanted top-level ip/port.
#          Updated: Pydantic integration for model validation, returns both raw and parsed configs.
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import os
import yaml
from glob import glob
from copy import deepcopy
from typing import Any, Dict, List, Tuple
from src.config_models import DayZServerMonitorConfig
from pydantic import ValidationError

def load_yaml(path: str) -> Dict[str, Any]:
    """
    Load YAML file, return empty dict if not found or empty.
    """
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def get_nested(config: Dict[str, Any], dotted_key: str) -> Any:
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

def set_nested(config: Dict[str, Any], dotted_key: str, value: Any) -> None:
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

def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge dict b into dict a (a is base, b is override), recursively.
    """
    for k, v in b.items():
        if isinstance(v, dict) and k in a and isinstance(a[k], dict):
            merge_dicts(a[k], v)
        else:
            a[k] = deepcopy(v)
    return a

def load_required_with_metadata(required_yaml: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a dict mapping dotted keys to type/description.
    """
    if not required_yaml or "required" not in required_yaml:
        return {}
    return required_yaml["required"]

def merge_server_blocks(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge 'server' blocks from two configs (base <- override).
    """
    merged: Dict[str, Any] = deepcopy(base.get('server', {}))
    override_block = override.get('server', {})
    if override_block:
        merge_dicts(merged, override_block)
    return merged

def load_configs(config_dir: str = "config") -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[DayZServerMonitorConfig]]:
    """
    Load configs for all servers, merging defaults, monitor.yaml, and server-specific YAMLs.
    Special handling for 'server' block: merges global (monitor.yaml) 'server' block with per-server override.
    Returns: ([raw_server_configs], required_dict, [validated_pydantic_configs])
    Each validated_pydantic_config is an instance of DayZServerMonitorConfig.
    If a config fails validation, it is skipped and error is printed.
    """
    defaults: Dict[str, Any] = load_yaml(os.path.join(config_dir, "config.defaults.yaml"))
    required_yaml: Dict[str, Any] = load_yaml(os.path.join(config_dir, "config.required.yaml"))
    required: Dict[str, Any] = load_required_with_metadata(required_yaml)
    monitor: Dict[str, Any] = load_yaml(os.path.join(config_dir, "monitor.yaml"))
    yamls = sorted(glob(os.path.join(config_dir, "*.yaml")))
    server_configs: List[Dict[str, Any]] = []

    monitor_server = monitor.get("server", {})

    for ypath in yamls:
        fname = os.path.basename(ypath)
        if fname in ("monitor.yaml", "config.defaults.yaml", "config.required.yaml"):
            continue
        server: Dict[str, Any] = load_yaml(ypath)
        merged: Dict[str, Any] = {}  # Only type annotate here
        merge_dicts(merged, deepcopy(defaults))
        merge_dicts(merged, deepcopy(monitor))
        merge_dicts(merged, server)
        # Special handling: merge 'server' block (monitor -> per-server)
        merged['server'] = merge_server_blocks(monitor, server)
        merged["_config_file"] = fname
        server_configs.append(merged)

    # Fallback: single-server mode (monitor.yaml only)
    if not server_configs and monitor:
        merged = {}  # Do NOT type annotate here, since already done above
        merge_dicts(merged, deepcopy(defaults))
        merge_dicts(merged, deepcopy(monitor))
        merged['server'] = merge_server_blocks(monitor, monitor)
        merged["_config_file"] = "monitor.yaml"
        server_configs = [merged]

    # Validate and parse into Pydantic models
    validated_pydantic_configs: List[DayZServerMonitorConfig] = []
    for conf in server_configs:
        try:
            # Remove _config_file before Pydantic validation
            conf_for_model: Dict[str, Any] = dict(conf)
            conf_for_model.pop("_config_file", None)
            validated = DayZServerMonitorConfig(**conf_for_model)
            validated_pydantic_configs.append(validated)
        except ValidationError as e:
            print(f"Config validation error in {conf.get('_config_file', 'unknown')}: {e}")

    return server_configs, required, validated_pydantic_configs

def validate_required(config: Dict[str, Any], required: Dict[str, Any], logger: Any) -> bool:
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
