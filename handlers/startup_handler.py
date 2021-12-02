"""State restoration for bot."""
from operator import itemgetter
import asyncio
from datetime import datetime, timedelta
import time
import traceback
import discord
import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH
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
    results = await bot.database.fetch(GET_ALL_RAIDS)

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
            await remove_raid_from_table(bot, message_id)
        else:
            future_delete[ttr] = [channel_id, message_id]

    if len(to_delete) == 0 and len(future_delete) == 0:
        return

    for channel_id, message_ids in to_delete.items():
        try:
            delete_snowflakes = [discord.Object(msg_id) for msg_id in message_ids]
            channel = bot.get_channel(channel_id)
            if not channel:
                continue
            await channel.delete_messages(delete_snowflakes)
        except discord.DiscordException as error:
            print("[!] Message(s) did not exist on server. [{}]".format(error))

    if len(future_delete) == 0:
        return

    sorted(future_delete)
    for ttr, data in future_delete.items():
        cur_time = datetime.now()
        delay = ttr - cur_time
        if ttr < cur_time:
            delay = 0
        await delete_after_delay(bot, data[0], data[1], delay.total_seconds())

    # lobbies = RLH.get_all_lobbies(bot)
    # for lobby in lobbies:
    #     if lobby.get("delete_at") < cur_time:
    #         lobby_channel_id = lobby.get("lobby_channel_id")
    #         lobby_channel = bot.get_channel(int(lobby_channel_id))
    #         try:
    #             await lobby_channel.delete()
    #         except discord.DiscordException:
    #             pass
    #         await RLH.remove_lobby_by_lobby_id(bot, lobby_channel_id)

    print("[*] All pending deletions complete.")

GET_GUILD_COUNTS = """
  SELECT * FROM guild_raid_counters;
"""
async def set_up_guild_raid_counters(bot):
    guild_counts = await bot.database.fetch(GET_GUILD_COUNTS)
    bot.guild_raid_counters = {record.get("guild_id"):record.get("raid_counter") for record in guild_counts}

GET_ALL_LOBBIES = """
  SELECT * FROM raid_lobby_user_map;
"""
async def set_up_lobbes(bot):
    lobbies = await bot.database.fetch(GET_ALL_LOBBIES)
    bot.lobbies = {lobby.get("lobby_channel_id"):await bot.get_lobby(lobby.get("lobby_channel_id"),
                                                                     user_limit=lobby.get("user_limit"),
                                                                     user_count=lobby.get("user_count"),
                                                                     raid_id=lobby.get("raid_message_id"),
                                                                     host=await bot.retrieve_user(lobby.get("host_user_id")),
                                                                     delete_time=lobby.get("delete_at")) for lobby in lobbies}


GET_TOTAL_COUNT = """
  SELECT SUM(raid_counter) AS total
  FROM guild_raid_counters
  WHERE (raid_counter > 0);
"""
async def set_new_presence(bot, old_count):
    """Gets total and sets presence to this new total."""
    new_count = await bot.database.fetch(GET_TOTAL_COUNT)
    total = (new_count.pop()).get("total")
    if total == old_count:
        return old_count

    game = discord.Game("{} raids hosted".format(total))
    try:
        await bot.change_presence(activity=game)
    except discord.DiscordException:
        return old_count
    return new_count

async def start_status_update_loop(bot):
    """Permanently running loop while bot is up."""
    while not bot.database:
        await asyncio.sleep(1)
    count = 0
    while True:
        count = await set_new_presence(bot, count)
        await asyncio.sleep(600)

async def start_five_minute_warning_loop(bot):
    while not bot.database:
        await asyncio.sleep(1)

    while True:
        # Outer loop waits on triggers
        while True:
            relevant_time = datetime.now() + timedelta(minutes=5)

            checked = 0
            for id, lobby in bot.lobbies.items():
                if not lobby.five_minute_warning:
                    if lobby.delete_time < relevant_time:
                        await lobby.send_five_minute_warning()
                    else:
                        continue
                checked += 1

            if checked == len(bot.lobbies):
                break

            await asyncio.sleep(1)

        await bot.five_minute_trigger.wait()
        bot.five_minute_trigger.clear()

async def start_lobby_removal_loop(bot):
    """Permanently running loop while bot is up."""

    while not bot.database:
        await asyncio.sleep(1)

    # Outer loop to wait on the event if no lobbies are present.
    while True:
        # Process lobbies until no lobbies remain before going to outer loop.
        while True:
            lobby_data = await RLH.get_next_lobby_to_remove(bot)
            if not lobby_data:
                break

            cur_time = datetime.now()
            deletion_time = lobby_data.get("delete_at")
            deletion_time_dif = deletion_time - cur_time
            if cur_time < deletion_time:
                if deletion_time_dif.total_seconds() > 1:
                    await asyncio.sleep(1)
                    continue

                if deletion_time_dif.total_seconds() > 0:
                    await asyncio.sleep(deletion_time_dif.total_seconds())

            lobby_id = lobby_data.get("lobby_channel_id")
            lobby_channel = await bot.retrieve_channel(int(lobby_id))
            lobby = bot.lobbies.get(lobby_id)
            #lobby = bot.get_channel(int(lobby_id))
            if not lobby_channel:
                await RLH.remove_lobby_by_lobby_id(bot, lobby_data)
                continue
            await RLH.delete_lobby(bot, lobby, lobby_channel, lobby_data)
        await bot.lobby_remove_trigger.wait()
        bot.lobby_remove_trigger.clear()

async def start_raid_removal_loop(bot):
    """Permanently running loop while bot is up."""

    while not bot.database:
        await asyncio.sleep(1)

    # Outer loop to wait on the event if no lobbies are present.
    while True:
        # Process lobbies until no lobbies remain before going to outer loop.
        while True:
            raid_data = await RH.get_next_raid_to_remove(bot)
            if not raid_data:
                break

            cur_time = datetime.now()
            deletion_time = raid_data.get("time_to_remove")
            deletion_time_dif = deletion_time - cur_time
            if cur_time < deletion_time:
                if deletion_time_dif.total_seconds() > 1:
                    await asyncio.sleep(1)
                    continue

                if deletion_time_dif.total_seconds() > 0:
                    await asyncio.sleep(deletion_time_dif.total_seconds())

            raid_id = raid_data.get("message_id")
            raid = await bot.retrieve_message(int(raid_id))
            #raid = bot.get_channel(int(raid_id))
            if not raid:
                await RH.remove_raid_by_raid_id(bot, raid_data)
                continue
            await bot.delete_ignore_error(raid)
        await bot.raid_remove_trigger.wait()
        bot.raid_remove_trigger.clear()

async def start_applicant_loop(bot):
    while not bot.database:
        await asyncio.sleep(1)

    while True:
        # Outer loop waits on triggers.
        while True:
            try:
                raid_lobby_data_list = await RLH.get_latest_lobby_data_by_timestamp(bot)
                if not raid_lobby_data_list:
                    break

                total_lobbies_to_handle = len(raid_lobby_data_list)
                checked_count = 0
                cur_time = datetime.now()
                threshold_time = cur_time - timedelta(seconds=45)
                for raid_lobby_data in raid_lobby_data_list:
                    lobby = bot.lobbies.get(raid_lobby_data.get("lobby_channel_id"))
                    if not lobby.raid_still_exists or lobby.pending_unlock:
                        continue
                    if lobby.has_filled:
                        await lobby.ask_to_unlock()
                        checked_count += 1
                        continue
                    posted_time = raid_lobby_data.get("posted_at")
                    if not lobby.auto_locked and not lobby.is_full() and (cur_time - posted_time).total_seconds() > 300:
                        await lobby.auto_lock()
                        lobby.update_raid_status()
                        continue

                    if posted_time < threshold_time:
                        #raid_host_id = raid_lobby_data.get("host_user_id")
                        raid_message_id = raid_lobby_data.get("raid_message_id")
                        users = await RLH.get_applicants_by_raid_id(bot, raid_message_id)
                        if not users:
                            checked_count += 1
                        guild_id = raid_lobby_data.get("guild_id")
                        guild = bot.get_guild(int(guild_id))
                        lobby.remove_starting_phase()
                        await RLH.process_user_list(bot, raid_lobby_data, users, guild)
                if checked_count == total_lobbies_to_handle:
                    break
                await asyncio.sleep(1)
            except Exception as e:
                error_channel = await bot.get_error_channel()
                await bot.send_ignore_error(error_channel, f"<@422429826809331712>\nAn exception occurred during the applicant loop. [{e}] Check the logs for the traceback.")
                traceback.print_last(file="/home/ubuntu/traceback.log")


        await bot.applicant_trigger.wait()

        bot.applicant_trigger.clear()
