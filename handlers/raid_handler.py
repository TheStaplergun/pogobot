"""Raid SQL statements and database interaction functions"""
from datetime import datetime
import asyncpg
import discord

NEW_RAID_INSERT = """
INSERT INTO raids(message_id, time_registered, guild_id, channel_id, user_id, time_to_remove)
VALUES($1, $2, $3, $4, $5, $6)
"""
async def add_raid_to_table(ctx, message_id, guild_id, channel_id, user_id, time_to_remove):
    """Add a raid to the database with all the given data points."""
    cur_time = datetime.now()
    await ctx.connection.execute(NEW_RAID_INSERT,
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
async def increment_raid_counter(ctx, guild_id):
    """Increments raid counter for a server for statistics tracking."""
    await ctx.connection.execute(INCREMENT_RAID_UPDATE_STATEMENT, guild_id)

GET_RAID_COUNT_STATEMENT = """
    SELECT * FROM guild_raid_counters WHERE (guild_id = $1) LIMIT 1;
"""
async def get_raid_count(bot, ctx):
    """Get raid count for server the command was called in."""
    connection = await bot.pool.acquire()
    try:
        count = await connection.fetchrow(GET_RAID_COUNT_STATEMENT,
                                          int(ctx.guild.id))
    except asyncpg.Exception as error:
        print("[!] Error obtaining raid count for guild. [{}]".format(error))
        return
    finally:
        await bot.pool.release(connection)
    num = count.get("raid_counter")
    msg = "Total raids sent within this server [`{}`]".format(num)
    try:
        await ctx.channel.send(msg)
    except discord.DiscordException as error:
        print("[!] Error sending raid count to channel. [{}]".format(error))

GET_RAIDS_FOR_GUILD = """
    SELECT * FROM raids WHERE (guild_id = $1);
"""
async def get_all_raids_for_guild(bot, ctx):
    """Admin command. Gets all raids for a guild and all pertaining data."""
    connection = await bot.acquire()
    results = await ctx.connection.fetch(GET_RAIDS_FOR_GUILD, ctx.guild.id)
    await bot.release(connection)
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
 SELECT * FROM raids where (user_id = $1)
"""
async def check_if_in_raid(ctx, user_id):
    """Checks if a user is already in a raid. Prevents double listing."""
    results = await ctx.connection.fetchrow(GET_RAID_FOR_USER, int(user_id))
    return results

RAID_TABLE_REMOVE_RAID = """
DELETE FROM raids WHERE (message_id = $1)
RETURNING message_id
"""
async def remove_raid_from_table(connection, message_id):
    """Removes a raid from the table."""
    await connection.execute(RAID_TABLE_REMOVE_RAID, int(message_id))

CHECK_VALID_RAID_CHANNEL = """
 SELECT * FROM valid_raid_channels where (channel_id = $1)
"""
async def check_if_valid_raid_channel(bot, channel_id):
    """Checks if the channel is registered as a valid raid channel."""
    connection = await bot.pool.acquire()
    results = await connection.fetchrow(CHECK_VALID_RAID_CHANNEL, int(channel_id))
    await bot.pool.release(connection)
    if not results:
        return False
    return True
