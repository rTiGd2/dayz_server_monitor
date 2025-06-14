# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import logging
import asyncio
import aiohttp

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

async def fetch_mod(session, mod):
    try:
        data = {'itemcount': 1, 'publishedfileids[0]': mod['workshop_id']}
        async with session.post(STEAM_API_URL, data=data) as resp:
            result = await resp.json()
            details = result['response']['publishedfiledetails'][0]
            return {
                "workshop_id": mod['workshop_id'],
                "title": details.get('title', 'Unknown'),
                "time_updated": details.get('time_updated', 0)
            }
    except Exception as e:
        logging.exception(f"Async failed for mod {mod['workshop_id']}: {e}")
        return None

async def process(mods):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_mod(session, mod) for mod in mods]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

def run(config, info, mods):
    logging.info("Running ASYNC mode")
    return asyncio.run(process(mods))