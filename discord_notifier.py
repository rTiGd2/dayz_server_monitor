# DayZ Server Monitor
# Project: DayZ Server Monitor
# File: 
# Purpose: 
# Author: Tig Campbell-Moore (firstname[at]lastname[dot]com)
# License: CC BY-NC 4.0 (see LICENSE file)
import discord
import asyncio
import logging

async def send_discord_message(token, channel_id, message):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(channel_id)
        if channel:
            await channel.send(message)
            logging.info("Discord message sent successfully.")
        else:
            logging.error("Discord channel not found.")
        await client.close()

    try:
        await client.start(token)
    except Exception as e:
        logging.exception(f"Failed to send Discord message: {e}")

def dispatch_discord(config, message):
    if not config.get("discord", {}).get("enabled", False):
        logging.info("Discord integration disabled.")
        return

    token = config["discord"]["token"]
    channel_id = int(config["discord"]["channel_id"])

    asyncio.run(send_discord_message(token, channel_id, message))