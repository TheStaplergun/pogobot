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

get_all_raids = """
  SELECT * FROM raids
"""
async def get_all_raids_in_db(ctx):
  results = await ctx.connection.fetch(get_all_raids)
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
  print("[*] Table operation results [ {} ]".format(results))

async def delete_after_delay(bot, channel_id, message_id, delay):
  print("[*] Sleeping for [ {} ] for next message deletion.".format(delay))
  await asyncio.sleep(delay)
  try:
    await bot.http.delete_message(channel_id, message_id)
  except Exception as e:
    print("[!] Message did not exist on server. [ {} ]".format(e))
    return
  #connection = await bot.pool.acquire()
  #await remove_raid_from_table(connection, message_id)
  #await bot.pool.release(connection)

  
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
    release_pool_connection(connection)

    return

  for channel_id, message_ids in to_delete.items():
    try:
      delete_snowflakes = [discord.Object(msg_id) for msg_id in message_ids]
      await bot.get_channel(channel_id).delete_messages(delete_snowflakes)
    except Exception as e:
      print("[!] Message(s) did not exist on server. [ {} ]".format(e))
  
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
