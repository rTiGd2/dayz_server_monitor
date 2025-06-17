# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: discord_notifier.py
# Purpose: Send output summaries to a configured Discord channel using a webhook
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import requests
import logging

def send_discord_webhook(webhook_url: str, message: str) -> None:
    data = {"content": message}
    try:
        resp = requests.post(webhook_url, json=data, timeout=10)
        if resp.status_code == 204:
            logging.info("✅ Discord summary message sent.")
        else:
            logging.error(f"❌ Discord webhook returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logging.error(f"❌ Exception during Discord webhook operation: {e}")

def dispatch_discord(config: dict, message: str) -> None:
    if not config.get("discord", {}).get("enabled", False):
        logging.info("📭 Discord integration disabled.")
        return

    webhook_url = config["discord"].get("webhook_url")
    if not webhook_url:
        logging.error("🔒 Discord webhook_url is missing in config.")
        return

    send_discord_webhook(webhook_url, message)
