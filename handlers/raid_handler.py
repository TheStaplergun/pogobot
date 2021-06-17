"""Raid SQL statements and database interaction functions"""
from datetime import datetime
import asyncpg
import discord

NEW_RAID_INSERT = """
INSERT INTO raids(message_id, time_registered, guild_id, channel_id, user_id, time_to_remove)
VALUES($1, $2, $3, $4, $5, $6)
"""
async def add_raid_to_table(ctx, bot, message_id, guild_id, channel_id, user_id, time_to_remove):
    """Add a raid to the database with all the given data points."""
    cur_time = datetime.now()

    await bot.database.execute(NEW_RAID_INSERT,
                                 int(message_id),
                                 cur_time,
                                 int(guild_id),
                                 int(channel_id),
                                 int(user_id),
                                 time_to_remove)


INCREMENT_RAID_UPDATE_STATEMENT = """
UPDATE guild_raid_counters
SET raid_counter = raid_counter + 1
WHERE (guild_id = $1);
"""
async def increment_raid_counter(ctx, bot, guild_id):
    """Increments raid counter for a server for statistics tracking."""
    await bot.database.execute(INCREMENT_RAID_UPDATE_STATEMENT, guild_id)

GET_RAID_COUNT_STATEMENT = """
    SELECT * FROM guild_raid_counters WHERE (guild_id = $1) LIMIT 1;
"""
async def get_raid_count(bot, ctx, should_print):
    """Get raid count for server the command was called in."""
    try:
        count = await bot.database.fetchrow(GET_RAID_COUNT_STATEMENT,
                                            int(ctx.guild.id))
    except asyncpg.Exception as error:
        print("[!] Error obtaining raid count for guild. [{}]".format(error))
        return

    num = count.get("raid_counter")
    if should_print:
        msg = "Total raids sent within this server [`{}`]".format(num)
        try:
            await ctx.channel.send(msg)
        except discord.DiscordException as error:
            print("[!] Error sending raid count to channel. [{}]".format(error))
    else:
        return num

GET_RAIDS_FOR_GUILD = """
    SELECT * FROM raids WHERE (guild_id = $1);
"""
async def get_all_raids_for_guild(bot, ctx):
    """Admin command. Gets all raids for a guild and all pertaining data."""

    results = await bot.database.fetch(GET_RAIDS_FOR_GUILD, ctx.guild.id)

    if not results:
        message = "No raids currently running."
        return
    message = "RAIDS\n"
    for _, item in enumerate(results):
        message += "-----------------\n"
        for column, value in item.items():
            message += str(column) + ": " + str(value) + "\n"
    message += "-----------------\nEND"
    await ctx.channel.send(message)

GET_RAID_FOR_USER = """
 SELECT * FROM raids where (user_id = $1);
"""
async def check_if_in_raid(ctx, bot, user_id):
    """Checks if a user is already in a raid. Prevents double listing."""
    return await bot.database.fetchrow(GET_RAID_FOR_USER, int(user_id))

CHECK_IF_MESSAGE_IS_RAID = """
  SELECT * FROM raids WHERE (message_id = $1)
"""
async def message_is_raid(ctx, bot, message_id):
    result = await bot.database.fetchrow(CHECK_IF_MESSAGE_IS_RAID, int(message_id))
    if result:
        return True
    return False

# Redundant but different return type. Can probably be added to above but do not feel like reworking at the moment.
async def retrieve_raid_data_by_message_id(ctx, bot, message_id):

    result = await bot.database.fetchrow(CHECK_IF_MESSAGE_IS_RAID, int(message_id))

    return result

RAID_TABLE_REMOVE_RAID = """
DELETE FROM raids WHERE (message_id = $1)
RETURNING message_id
"""
CLEAR_APPLICANTS_FOR_RAID = """
DELETE FROM raid_application_user_map WHERE (raid_message_id = $1)
"""
async def remove_raid_from_table(bot, message_id):
    """Removes a raid from the table."""
    async with bot.database.connect() as c:
        await c.execute(RAID_TABLE_REMOVE_RAID, int(message_id))
        await c.execute(CLEAR_APPLICANTS_FOR_RAID, int(message_id))

async def delete_raid(bot, raid_id):
    raid_data = await retrieve_raid_data_by_message_id(None, bot, raid_id)
    if not raid_data:
        return
    try:
        await bot.http.delete_message(raid_data.get("channel_id"), raid_data.get("message_id"))
    except discord.DiscordException:
        return
    

async def handle_clear_user_from_raid(ctx, bot, user_id):
    guild = ctx.guild
    member = guild.get_member(user_id)
    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except discord.DiscordException as error:
            pass
    if not member:
        await ctx.send("That user doesn't exist on this server.", delete_after=5)
        return
    results = await check_if_in_raid(ctx, bot, user_id)
    if not results:
        await ctx.send("That user is not in a raid.", delete_after=5)
        return
    message_id = results.get("message_id")
    channel_id = results.get("channel_id")
    guild_id = results.get("guild_id")
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    try:
        message = await channel.fetch_message(message_id)
        await message.delete()
    except discord.NotFound:

        await remove_raid_from_table(bot, message_id)

    except discord.DiscordException as error:
        print("[!] An error occurred trying to remove a user from their raid manually. [{}]".format(error))
        return
    await ctx.send("User was successfully removed from raid.", delete_after=5)

CHECK_VALID_RAID_CHANNEL = """
 SELECT * FROM valid_raid_channels where (channel_id = $1)
"""
async def check_if_valid_raid_channel(bot, channel_id):
    """Checks if the channel is registered as a valid raid channel."""

    results = await bot.database.fetchrow(CHECK_VALID_RAID_CHANNEL, int(channel_id))

    if not results:
        return False
    return True
