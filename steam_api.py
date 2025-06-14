# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import requests

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

def get_mod_info(workshop_id, api_key=None):
    data = {'itemcount': 1, 'publishedfileids[0]': workshop_id}
    response = requests.post(STEAM_API_URL, data=data)
    response.raise_for_status()
    details = response.json()['response']['publishedfiledetails'][0]

    return {
        'title': details.get('title', 'Unknown'),
        'time_updated': details.get('time_updated', 0),
        'description': details.get('description', '')
    }