# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: modes/async_mode.py
# Purpose: Mod metadata lookup using asyncio + aiohttp
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)

import logging
import asyncio
import aiohttp
from aiohttp import ClientTimeout

STEAM_API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

async def fetch_mod(session, mod):
    workshop_id = mod.get('workshop_id')
    if not workshop_id:
        return None

    try:
        data = {'itemcount': 1, 'publishedfileids[0]': workshop_id}
        async with session.post(STEAM_API_URL, data=data) as resp:
            result = await resp.json()
            response = result.get('response', {})
            details_list = response.get('publishedfiledetails', [])
            if not details_list or not isinstance(details_list, list):
                logging.warning(f"[ASYNC] No details found for {workshop_id}")
                return None
            details = details_list[0]
            return {
                "workshop_id": workshop_id,
                "title": details.get('title', 'Unknown'),
                "time_updated": details.get('time_updated', 0)
            }
    except Exception as e:
        logging.exception(f"[ASYNC] Failed for {workshop_id}: {e}")
        return None

async def process(mods):
    timeout = ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [fetch_mod(session, mod) for mod in mods]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        filtered_results = []
        for r in results:
            if isinstance(r, Exception):
                logging.exception(f"[ASYNC] Task raised exception: {r}")
            elif r:
                filtered_results.append(r)
        return filtered_results

def run(config, info, mods):
    logging.info("[ASYNC] Running with %d mods", len(mods))
    return asyncio.run(process(mods))
