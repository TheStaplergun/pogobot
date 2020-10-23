import discord
import asyncio
from discord.ext import commands
import asyncpg
from pogo_raid_lib import *
import time
from datetime import datetime
import shutil



new_player_table_insert = """
INSERT INTO players(user_id, friend_code, Level, time_registered, raids_posted, restricted)
VALUES($1, $2, $3, $4, $5, $6)
"""

column_names = ["Discord User ID", "Friend Code", "Level", "Time Registered", "Raids posted", "Restricted"]

player_table_query = """
SELECT * FROM players WHERE (user_id = $1)
"""

player_table_remove_player = """
DELETE FROM players WHERE (user_id = $1)
RETURNING user_id
"""
async def insert_new_player(ctx,
                            user_id,
                            friend_code,
                            level):
  cur_time = datetime.now()
  await ctx.connection.execute(new_player_table_insert,
                               int(user_id),
                               friend_code,
                               int(level),
                               cur_time,
                               0,
                               False)

async def remove_player(ctx, user_id):
  results = await ctx.connection.execute(player_table_remove_player, int(user_id))
  return results



async def check_for_player(ctx, user_id):
  results = await ctx.connection.fetchrow(player_table_query, int(user_id))
  message = ""
  match_found = False
  if results:
    match_found = True
    for index, item in enumerate(results):
      message += str(column_names[index]) + ": " + str(item) + "\n"

  return (match_found, message)

def wrap_bot_dm(guild_name, message):
  return "**From:** {} raid hosting bot\n{}".format(guild_name, message)


"""
  user_id BIGINT PRIMARY KEY,
  friend_code CHAR(12) NOT NULL,
  Level SMALLINT NOT NULL,
  time_registered TIMESTAMP NOT NULL,
  raids_posted INT NOT NULL,
  restricted BOOL NOT NULL
"""

async def register_user(ctx,
                        level,
                        friend_code,
                        friend_code_middle,
                        friend_code_end):

  author = ctx.author
  registration_valid = True
  message_to_send = ""
  message_to_dm = ""
  is_valid, level = validate_level(level)
  if is_valid:
    message_to_send += "Valid level given: " + level
    message_to_send += "\n"
  else:
    registration_valid = False
    message_to_dm += "\n"

  is_valid, friend_code = validate_friend_code_format(friend_code, friend_code_middle, friend_code_end)
  if not is_valid:
    registration_valid = False

  if registration_valid:
    await insert_new_player(ctx,
                            author.id,
                            friend_code,
                            level)
  else:
    await author.send(message_to_dm)

"""
  time_registered TIMESTAMP PRIMARY KEY,
  message_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  time_to_remove TIMESTAMP NOT NULL
"""

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
  print("[*] Sleeping for {} for next message deletion.".format(delay))
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
    print("no raids found.")
    return
  
  cur_time = datetime.now()
  to_delete = {}
  future_delete = {}
  for record in results:
    ttr = record.get("time_to_remove")
    print("Current time is {}".format(cur_time))
    print("Raid delete time is {}".format(ttr))
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
    delete_snowflakes = [discord.Object(msg_id) for msg_id in message_ids]
    await bot.get_channel(channel_id).delete_messages(delete_snowflakes)
  
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
