# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: config_loader.py
# Purpose: Load configuration from YAML, Docker secrets, or environment
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import yaml
import os

SECRETS_PATH = "/run/secrets"

def read_secret(secret_name):
    path = os.path.join(SECRETS_PATH, secret_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return None

def load_config(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with open(filepath, 'r') as f:
        config = yaml.safe_load(f) or {}

    # Ensure keys exist
    config.setdefault("discord", {})
    config.setdefault("steam", {})

    # Override Discord token
    discord_token = (
        read_secret("webhook_url")
        or config["discord"].get("webhook_url")
        or os.environ.get("DISCORD_WEBHOOK_URL")
    )
    if discord_token:
        config["discord"]["webhook_url"] = discord_token

    # Override Steam API key
    steam_key = (
        read_secret("steam_api_key")
        or config["steam"].get("api_key")
        or os.environ.get("STEAM_API_KEY")
    )
    if steam_key:
        config["steam"]["api_key"] = steam_key

    return config
