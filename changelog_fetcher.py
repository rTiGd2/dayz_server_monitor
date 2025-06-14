# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import requests
from bs4 import BeautifulSoup

def get_workshop_changelog(workshop_id):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/changelog/{workshop_id}"
    response = requests.get(url)

    if not response.ok:
        return "No changelog available"

    soup = BeautifulSoup(response.text, 'html.parser')
    changelog_div = soup.find('div', class_='changeLogBlock')
    if changelog_div:
        return changelog_div.get_text(strip=True)

    return "No changelog available"