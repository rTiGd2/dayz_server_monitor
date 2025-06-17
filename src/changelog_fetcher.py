# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: changelog_fetcher.py
# Purpose: Retrieve latest mod changelogs from Steam
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import requests
from bs4 import BeautifulSoup
import logging

def get_workshop_changelog(workshop_id):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/changelog/{workshop_id}"
    logging.debug(f"Fetching changelog for mod: {workshop_id}")

    try:
        response = requests.get(url, timeout=10)
        if not response.ok:
            logging.warning(f"Bad response for changelog ({response.status_code})")
            return "No changelog available"

        soup = BeautifulSoup(response.text, 'html.parser')
        changelog_div = soup.find('div', class_='changeLogBlock')
        if changelog_div:
            return changelog_div.get_text(strip=True)
        return "No changelog available"

    except Exception as e:
        logging.error(f"Failed to fetch changelog: {e}")
        return "No changelog available"
