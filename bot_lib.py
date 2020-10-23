import discord
from discord.ext import commands
import asyncpg
from important import *
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

  guild = ctx.guild
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
    message_to_dm += response
    message_to_dm += "\n"

  is_valid, friend_code = validate_friend_code_format(friend_code, friend_code_middle, friend_code_end)
  if not is_valid:
    registration_valid = False
    message_to_dm += response

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
INSERT INTO raids(message_id, time_registered, guild_id, channel_id, time_to_remove)
VALUES($1, $2, $3, $4, $5)
"""

async def add_raid_to_table(ctx, message_id, guild_id, channel_id, time_to_remove):
  cur_time = datetime.now()
  await ctx.connection.execute(new_raid_insert,
                               int(message_id),
                               cur_time,
                               int(guild_id),
                               int(channel_id),
                               time_to_remove)

raid_columns = ["Time registered", "Message ID", "Channel ID", "Time to Remove"]
get_all_raids = """
  SELECT * FROM raids
"""
async def get_raids_to_delete(ctx):
  cur_time = datetime.now()
  results = await ctx.connection.fetch(get_all_raids)
  
  if not results:
    print("No raids found.")
    return
  else:
    message = "RAIDS\n"
    for index, item in enumerate(results):
      message += "-----------------\n"
      for column, value in item.items():
        message += str(column) + ": " + str(value) + "\n"
    message += "-----------------\nEND"
    await ctx.channel.send(message)

raid_table_remove_raid = """
DELETE FROM raids WHERE (message_id = $1)
RETURNING message_id
"""
async def remove_raid_from_table(connection, message_id):
  results = await connection.execute(raid_table_remove_raid, int(message_id))
  print(results)

recreate_raid_table_string = """
  DROP TABLE IF EXISTS raids CASCADE;
  CREATE TABLE raids (
  message_id BIGINT PRIMARY KEY,
  time_registered TIMESTAMP NOT NULL,
  guild_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  time_to_remove TIMESTAMP NOT NULL
  );
"""

async def recreate_raid_table(ctx):
  print(await ctx.connection.execute(recreate_raid_table_string))
