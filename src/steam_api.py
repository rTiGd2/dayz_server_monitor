# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: steam_api.py
# Purpose: Fetch mod metadata from Steam Workshop
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import requests
import logging

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

def get_mod_info(workshop_id, api_key=None):
    data = {'itemcount': 1, 'publishedfileids[0]': workshop_id}
    try:
        response = requests.post(STEAM_API_URL, data=data, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.exception(f"Failed to fetch Steam info for mod {workshop_id}: {e}")
        raise

    details = response.json().get('response', {}).get('publishedfiledetails', [{}])[0]

    return {
        'title': details.get('title', 'Unknown'),
        'time_updated': details.get('time_updated', 0),
        'description': details.get('description', '')
    }
