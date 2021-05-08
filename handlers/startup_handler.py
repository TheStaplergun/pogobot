"""State restoration for bot."""
from operator import itemgetter
import asyncio
from datetime import datetime, timedelta
import time
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
        except discord.DiscordException as error:
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

GET_TOTAL_COUNT = """
  SELECT SUM(raid_counter) AS total
  FROM guild_raid_counters
  WHERE (raid_counter > 0);
"""
async def set_new_presence(bot, old_count):
    """Gets total and sets presence to this new total."""
    connection = await bot.acquire()
    new_count = await connection.fetch(GET_TOTAL_COUNT)
    await bot.release(connection)
    total = (new_count.pop()).get("total")
    if total == old_count:
        return old_count

    game = discord.Game("Total raids hosted: {}".format(total))
    try:
        await bot.change_presence(activity=game)
    except discord.DiscordException:
        return old_count
    return new_count

async def start_status_update_loop(bot):
    """Permanently running loop while bot is up."""
    while not bot.pool:
        await asyncio.sleep(1)
    count = 0
    while True:
        count = await set_new_presence(bot, count)
        await asyncio.sleep(10*60)

async def start_lobby_removal_loop(bot):
    """Permanently running loop while bot is up."""

    while not bot.pool:
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
            print("Deletion time [{}]".format(deletion_time))
            print("Current time [{}]".format(datetime.now()))
            deletion_time_dif = deletion_time - cur_time
            print("Deletion dif [{}]".format(deletion_time_dif.total_seconds()))
            # Refresh in 30 seconds if greater than one minute wait time.
            # Time to delete can be altered dramatically if a user removes their post early, reordering the database.
            if cur_time < deletion_time:
                print("Current time is behind deletion time.")
                if deletion_time_dif.total_seconds() > 30:
                    await asyncio.sleep(30)
                    continue

                if deletion_time_dif.total_seconds() > 0:
                    await asyncio.sleep(deletion_time_dif.total_seconds())

            lobby_id = lobby_data.get("lobby_channel_id")
            lobby = bot.get_channel(int(lobby_id))
            if not lobby:
                print("Lobby channel doesn't exist. Removing data.")
                await RLH.remove_lobby_by_lobby_id(bot, lobby_id)
                continue
            try:
                await lobby.delete()
            except discord.DiscordException as error:
                print("[!][{}] An error occurred removing a lobby automatically. [{}]".format(guild.name, error))
        await bot.lobby_remove_trigger.wait()
        bot.lobby_remove_trigger.clear()

async def start_applicant_loop(bot):
    while not bot.pool:
        await asyncio.sleep(1)

    while True:
        # Outer loop waits on triggers.
        while True:
            raid_lobby_data_list = await RLH.get_latest_lobby_data_by_timestamp(bot)
            if not raid_lobby_data_list:
                break

            for raid_lobby_data in raid_lobby_data_list:
                cur_time = datetime.now()
                threshold_time = cur_time - timedelta(seconds=30)
                posted_time = raid_lobby_data.get("posted_at")
                if posted_time < threshold_time:
                    #raid_host_id = raid_lobby_data.get("host_user_id")
                    raid_message_id = raid_lobby_data.get("raid_message_id")
                    users = await RLH.get_applicants_by_raid_id(bot, raid_message_id)
                    if not users:
                        continue
                    guild_id = raid_lobby_data.get("guild_id")
                    guild = bot.get_guild(int(guild_id))
                    user_list = []
                    for user in users:
                        has_been_notified = user.get("has_been_notified")
                        if has_been_notified:
                            continue
                        member_id = user.get("user_id")
                        member = guild.get_member(int(member_id))
                        user_data = {
                            "user_data":user,
                            "weight":await RLH.calculate_weight(bot, user, member),
                            "member_object":member,
                            }
                        user_list.append(user_data)
                    print("-------")
                    print(user_list)
                    print("-------")
                    sorted_users = sorted(user_list, key=itemgetter('weight'), reverse=True)
                    print(sorted_users)
                    print("-------")
                    await RLH.process_user_list(bot, raid_lobby_data, sorted_users)
            await asyncio.sleep(1)

        await bot.applicant_trigger.wait()

        bot.applicant_trigger.clear()
