import discord
import asyncio
from discord.ext import commands
import asyncpg
from pogo_raid_lib import *
import time
from datetime import datetime
import shutil


def wrap_bot_dm(guild_name, message):
  return "**From:** {} raid hosting bot\n{}".format(guild_name, message)

new_raid_insert = """
INSERT INTO raids(message_id, time_registered, guild_id, channel_id, user_id, time_to_remove)
VALUES($1, $2, $3, $4, $5, $6)
"""

async def add_raid_to_table(ctx, message_id, guild_id, channel_id, user_id, time_to_remove):
  cur_time = datetime.now()
  await ctx.connection.execute(new_raid_insert,
                               int(message_id),
                               cur_time,
                               int(guild_id),
                               int(channel_id),
                               int(user_id),
                               time_to_remove)

increment_raid_update_statement = """
UPDATE guild_raid_counters
SET raid_counter = raid_counter + 1
WHERE (guild_id = $1);
"""
async def increment_raid_counter(ctx, guild_id):
  results = await ctx.connection.execute(increment_raid_update_statement, guild_id)

get_raid_count_statement = """
  SELECT * FROM guild_raid_counters WHERE (guild_id = $1) LIMIT 1;
"""
async def get_raid_count(bot, ctx):
  connection = await bot.pool.acquire()
  try:
    count = await connection.fetchrow(get_raid_count_statement,
                                      int(ctx.guild.id))
  except Exception as e:
    print("[!] Error obtaining raid count for guild. [{}]".format(e))
    return
  finally:
    await bot.pool.release(connection)
  num = count.get("raid_counter")
  msg = "Total raids sent within this server [`{}`]".format(num)
  try:
    await ctx.channel.send(msg)
  except Exception as e:
    print("[!] Error sending raid count to channel. [{}]".format(e))
  

get_raids_for_guild = """
  SELECT * FROM raids WHERE (guild_id = $1);
"""
async def get_all_raids_for_guild(ctx):
  results = await ctx.connection.fetch(get_raids_for_guild, ctx.guild.id)
  if not results:
    message = "No raids currently running."
    return
  else:
    message = "RAIDS\n"
    for _, item in enumerate(results):
      message += "-----------------\n"
      for column, value in item.items():
        message += str(column) + ": " + str(value) + "\n"
    message += "-----------------\nEND"
  await ctx.channel.send(message)

get_raid_for_user = """
 SELECT * FROM raids where (user_id = $1)
"""
async def check_if_in_raid(ctx, user_id):
  results = await ctx.connection.fetchrow(get_raid_for_user, int(user_id))
  return results

raid_table_remove_raid = """
DELETE FROM raids WHERE (message_id = $1)
RETURNING message_id
"""
async def remove_raid_from_table(connection, message_id):
  results = await connection.execute(raid_table_remove_raid, int(message_id))

async def delete_after_delay(bot, channel_id, message_id, delay):
  print("[*] Sleeping for [{}] for next message deletion.".format(delay))
  await asyncio.sleep(delay)
  try:
    await bot.http.delete_message(channel_id, message_id)
  except Exception as e:
    print("[!] Message did not exist on server. [{}]".format(e))
    return
  #connection = await bot.pool.acquire()
  #await remove_raid_from_table(connection, message_id)
  #await bot.pool.release(connection)

get_all_raids = """
  SELECT * FROM raids;
"""
async def spin_up_message_deletions(bot):
  connection = await bot.pool.acquire()
  results = await connection.fetch(get_all_raids)

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
      await bot.get_channel(channel_id).delete_messages(delete_snowflakes)
    except Exception as e:
      print("[!] Message(s) did not exist on server. [{}]".format(e))

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


check_valid_raid_channel = """
 SELECT * FROM valid_raid_channels where (channel_id = $1)
"""

async def check_if_valid_raid_channel(bot, channel_id):
  connection = await bot.pool.acquire()
  results = await connection.fetchrow(check_valid_raid_channel, int(channel_id))
  await bot.pool.release(connection)
  if not results:
    return False
  return True

add_raid_channel = """
INSERT INTO valid_raid_channels (channel_id, guild_id)
VALUES ($1, $2);
"""

init_raid_counter = """
INSERT INTO guild_raid_counters (guild_id)
VALUES ($1);
"""
async def database_register_raid_channel(bot, ctx, channel_id, guild_id):
  connection = await bot.pool.acquire()
  results = None
  try:
    results = await connection.execute(add_raid_channel,
                                       int(channel_id),
                                       int(guild_id))
  except Exception as e:
    print("[!] Error occured registering raid channel. [{}]".format(e))
  try:
    result2 = await connection.execute(init_raid_counter,
                                       int(guild_id))
  except Exception as e:
    print("[!] Error occured registering raid counter. [{}]".format(e))
  await bot.pool.release(connection)
  if results:
    print("[*] [{}] [{}] New raid channel registered.".format(ctx.guild.name, channel_id))

check_for_raids_in_guild_channel = """
 SELECT * FROM raids where (channel_id = $1)
"""
async def check_if_raids_remaining_in_channel(bot, channel_id):
  connection = await bot.pool.acquire()
  results = await connection.fetchrow(check_for_raids_in_guild_channel, int(channel_id))
  await bot.pool.release(connection)
  if not results:
    return False
  return True

raid_placeholder_sticky_select = """
 SELECT * FROM raid_placeholder_stickies where (channel_id = $1)
"""
async def get_sticky_message(bot, channel_id):
  connection = await bot.pool.acquire()
  record = await connection.fetchrow(raid_placeholder_sticky_select, int(channel_id))
  await bot.pool.release(connection)
  if not record:
    return (False, None)

  message_id = int(record.get("message_id"))
  channel = bot.get_channel(channel_id)
  try:
    message = await channel.fetch_message(message_id)
  except Exception as e:
    print(e)
    return (True, None)
  
  if not message:
    return (True, None)

  return (True, message)

add_placeholder_sticky_message = """
INSERT INTO raid_placeholder_stickies(channel_id, message_id, guild_id)
VALUES($1, $2, $3)
"""
async def update_placeholder_database(bot, channel_id, message_id, guild_id):
  connection = await bot.pool.acquire()
  await connection.execute(add_placeholder_sticky_message,
                           int(channel_id),
                           int(message_id),
                           int(guild_id))
  await bot.pool.release(connection)

delete_placeholder_sticky_message = """
DELETE FROM raid_placeholder_stickies WHERE (channel_id = $1)
RETURNING channel_id
"""
async def remove_old_sticky_message_from_table(bot, channel_id):
  connection = await bot.pool.acquire()
  results = await connection.execute(delete_placeholder_sticky_message, int(channel_id))
  await bot.pool.release(connection)
  print("[*] Table operation results [{}]".format(results))

async def make_new_no_raids_placeholder_message(bot, ctx, channel_id):
  channel = bot.get_channel(channel_id)
  title = "No raids available."
  description = "Check back any time to see if one has been listed."
  embed = format_sticky_embed(title, description)
  message = await channel.send(embed=embed)

  await update_placeholder_database(bot, int(channel.id), int(message.id), int(channel.guild.id))

async def make_new_raids_remaining_placeholder_message(bot, ctx, channel_id):
  channel = bot.get_channel(channel_id)
  title = "Raids available!"
  description = "All available raids are listed below."
  embed = format_sticky_embed(title, description)
  message = await channel.send(embed=embed)

  await update_placeholder_database(bot, int(channel.id), int(message.id), int(channel.guild.id))

def format_sticky_embed(title, description):
  embed = discord.Embed(title=title, description=description, color=0xff8c00)
  embed_host_raid_msg = "If you want to host a raid, check out the post above!"
  embed.add_field(name="Want to host a raid?", value=embed_host_raid_msg, inline=False)
  return embed

async def edit_to_no_raids_remaining_placeholder(bot, channel_id, message):
  title = "No raids available."
  description = "Check back any time to see if one has been listed."
  embed = format_sticky_embed(title, description)
  await message.edit(embed=embed)

async def edit_to_raids_remaining_placeholder(bot, channel_id, message):
  title = "Raids available!"
  description = "All available raids are listed below."
  embed = format_sticky_embed(title, description)
  await message.edit(embed=embed)

async def toggle_raid_sticky(bot, ctx, channel_id, guild_id):
  if not await check_if_valid_raid_channel(bot, channel_id):
    return
  try:

    raids_remaining = await check_if_raids_remaining_in_channel(bot, channel_id)

    message_exists_in_table, message = await get_sticky_message(bot, channel_id)
    if message:
      if not raids_remaining:
        await edit_to_no_raids_remaining_placeholder(bot, channel_id, message)
        return

      await edit_to_raids_remaining_placeholder(bot, channel_id, message)
      return

    if message_exists_in_table:
      await remove_old_sticky_message_from_table(bot, channel_id)

    if not raids_remaining:
      await make_new_no_raids_placeholder_message(bot, ctx, channel_id)
      return

    await make_new_raids_remaining_placeholder_message(bot, ctx, channel_id)
    return

  except Exception as e:
    print("[!] An exception occured while creating a placeholder. [{}]".format(e))


#recreate_raid_table_string = """
#  DROP TABLE IF EXISTS raids CASCADE;
#  CREATE TABLE raids (
#  message_id BIGINT PRIMARY KEY,
#  time_registered TIMESTAMP NOT NULL,
#  guild_id BIGINT NOT NULL,
#  channel_id BIGINT NOT NULL,
#  user_id BIGINT NOT NULL,
#  time_to_remove TIMESTAMP NOT NULL
#  );
#"""

#async def drop_and_make(ctx):
#  print(await ctx.connection.execute(recreate_raid_table_string))
