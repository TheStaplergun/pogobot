"""State restoration for bot."""

import asyncio
from datetime import datetime
import time
import discord
from handlers.raid_handler import remove_raid_from_table

async def delete_after_delay(bot, channel_id, message_id, delay):
    """Delete after timed delay helper function. For use when bot goes down."""
    print("[*] Sleeping for [{}] for next message deletion.".format(delay))
    await asyncio.sleep(delay)
    try:
        await bot.http.delete_message(channel_id, message_id)
    except discord.NotFound as error:
        print("[!] Message did not exist on server. [{}]".format(error))
        return

GET_ALL_RAIDS = """
  SELECT * FROM raids;
"""
async def spin_up_message_deletions(bot):
    """Re-establishes raid message removal loop."""
    connection = await bot.pool.acquire()
    results = await connection.fetch(GET_ALL_RAIDS)

    if not results:
        print("[*] No pending raids found to delete.")
        return

    cur_time = datetime.now()
    to_delete = {}
    future_delete = {}
    for record in results:
        ttr = record.get("time_to_remove")
        channel_id = int(record.get("channel_id"))
        message_id = int(record.get("message_id"))
        if ttr < cur_time:
            if channel_id not in to_delete.keys():
                to_delete[channel_id] = []
            to_delete[channel_id].append(message_id)
            await remove_raid_from_table(connection, message_id)
        else:
            future_delete[ttr] = [channel_id, message_id]

    if len(to_delete) == 0 and len(future_delete) == 0:
        await bot.pool.release(connection)
        return

    for channel_id, message_ids in to_delete.items():
        try:
            delete_snowflakes = [discord.Object(msg_id) for msg_id in message_ids]
            channel = bot.get_channel(channel_id)
            if not channel:
                continue
            await channel.delete_messages(delete_snowflakes)
        except discord.NotFound as error:
            print("[!] Message(s) did not exist on server. [{}]".format(error))

    await bot.pool.release(connection)

    if len(future_delete) == 0:
        return

    sorted(future_delete)
    for ttr, data in future_delete.items():
        cur_time = datetime.now()
        delay = ttr - cur_time
        if ttr < cur_time:
            delay = 0
        await delete_after_delay(bot, data[0], data[1], delay.total_seconds())

    print("[*] All pending deletions complete.")

GET_TOTAL_COUNT = """
  SELECT SUM(raid_counter) AS total
  FROM guild_raid_counters
  WHERE raid_counter > 0
  RETURNING total;
"""
async def set_new_presence(bot, old_count):
    """Gets total and sets presence to this new total."""
    connection = await bot.acquire()
    new_count = await connection.fetch(GET_ALL_RAIDS)
    await bot.release(connection)
    if new_count == old_count:
        return old_count

    game = discord.Game("Total raids hosted: {}".format(new_count))
    try:
        await bot.change_presence(activity=game)
    except discord.DiscordException:
        return
    return new_count

async def start_status_update_loop(bot):
    """Permanently running loop while bot is up."""
    count = 0
    while not bot.pool:
        await asyncio.sleep(1)

    while True:
        count = await set_new_presence(bot, count)
        await asyncio.sleep(10*60)
