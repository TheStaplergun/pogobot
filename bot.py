import discord
from discord.ext import commands
import data
from important import *
import raid_cog
from raid_cog import *
from bot_lib import *
import xml.etree.ElementTree as ET
import string
import os
import re

description = '''TheStaplergun's Bot in Python'''

"""Set command_prefix to any character here."""
COMMAND_PREFIX = '-'
"""Change this string to change the 'playing' status of the bot."""
CUSTOM_STATUS = "WIP"

guild_info_dictionary = {
  652487145193209856:{
    "allowed_raid_channels":[737736358801571901, 750078168496472176]
  }
}
game = discord.Game(CUSTOM_STATUS)
bot = commands.Bot(COMMAND_PREFIX, description=description, activity=game)

bot.pool = None
bot.raids_enabled = True
bot.guild_info_dictionary = guild_info_dictionary
bot.bot_ready_to_process = False

async def temp_acquire_pool_connection():
  connection = await bot.pool.acquire()
  return connection

async def temp_release_pool_connection(connection):
  if connection:
    await bot.pool.release(connection)

async def init_pool():
  pool = await asyncpg.create_pool(database=database,
                                   port=port,
                                   host=host,
                                   user=user,
                                   password=password)

  return pool



@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print('------')

@bot.event
async def on_raw_reaction_add(ctx):
  if not bot.raids_enabled:
    return

  if ctx.guild_id not in bot.guild_info_dictionary:
    return

  if ctx.channel_id not in bot.guild_info_dictionary[ctx.guild_id].get("allowed_raid_channels"):
    return

  """Bot ignores itself adding emojis"""
  if ctx.user_id == bot.user.id:
    return

  channel = bot.get_channel(ctx.channel_id)
  message = await channel.fetch_message(ctx.message_id)

  if not message.author.id == bot.user.id:
    return

  if not len(message.embeds) == 1:
    return

  if not len(message.mentions) == 1:
    return

  user_id = message.mentions[0].id

  if int(user_id) != ctx.user_id:
    dm = "You are not the host. You cannot delete this raid!"
    for reaction in message.reactions:
      async for user in reaction.users():
        if user.id == ctx.user_id:
          try:
            await reaction.remove(user)
          except Exception as e:
            print("[*] Error removing reaction [{}]".format(e))
  else:
    dm = "Your raid has been successfuly deleted."
    conn = await temp_acquire_pool_connection()
    await remove_raid_from_table(conn, message.id)
    await temp_release_pool_connection(conn)
    await message.delete()
    try:
      await toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
    except Exception as e:
      print("[!] An error occurred [{}]".format(e))
  await ctx.member.send(wrap_bot_dm(channel.guild.name, dm))

@bot.event
async def on_raw_message_delete(ctx):
  if not bot.raids_enabled:
    return

  if ctx.guild_id not in bot.guild_info_dictionary:
    return

  if ctx.channel_id not in bot.guild_info_dictionary[ctx.guild_id].get("allowed_raid_channels"):
    return

  conn = await temp_acquire_pool_connection()
  await remove_raid_from_table(conn, ctx.message_id)
  await temp_release_pool_connection(conn)
  try:
    await toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
  except Exception as e:
    print("[!] An error occurred [{}]".format(e))

@bot.command()
@commands.has_role("Mods")
async def toggle_raid_module(ctx):
  bot.raids_enabled = not (bot.raids_enabled)
  print("[!] Raid module enabled status [ {} ]".format(bot.raids_enabled))
  await ctx.channel.send("Raid module has been {}.".format(bot.raids_enabled and "enabled" or "disabled"))

@bot.command()
@commands.has_role("Mods")
async def register_raid_channel(ctx):

  channel_id = ctx.channel.id
  guild_id = ctx.guild.id
  try:
    await ctx.message.delete()
  except:
    pass
  await database_register_raid_channel(bot, ctx, channel_id, guild_id)
  try:
    await toggle_raid_sticky(bot, ctx, channel_id, guild_id)
  except Exception as e:
    print("[!] An error occurred [{}]".format(e))
  

#@bot.command()
#@commands.before_invoke(acquire_pool_connection)
#@commands.after_invoke(release_pool_connection)
#@commands.has_role("Mods")
#@commands.guild_only()
async def check_registration(ctx, user_id = ""):
  if not user_id:
    await ctx.send("No ID provided.")
    return
  try:
    int(user_id)
  except ValueError:
    await ctx.send("Invalid parameter provided [`" + str(user_id) + "`]. Must be discord user ID.")
    return
  entry_found, results = await check_for_player(ctx, user_id)
  if entry_found:
    await ctx.send(results)
  else:
    await ctx.send("No entry found for that User ID")

#@check_registration.error
async def check_registration_error(ctx, error):
  if isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
    await ctx.author.send("This command cannot be executed via DM")
  elif isinstance(error, discord.ext.commands.errors.MissingRole):
    await ctx.author.send("You do not have permission to execute this command")
  else:
    await ctx.author.send(error)

#@bot.command()
#@commands.before_invoke(acquire_pool_connection)
#@commands.after_invoke(release_pool_connection)
#@commands.has_role("Mods")
#@commands.guild_only()
async def remove_registration(ctx, user_id= ""):
  if not user_id:
    await ctx.send("No ID provided.")
    return
  try:
    int(user_id)
  except ValueError:
    await ctx.send("Invalid parameter provided [`" + str(user_id) + "`]. Must be discord user ID.")
    return
  entry_found, _ = await check_for_player(ctx, user_id)
  if entry_found:
    await remove_player(ctx, user_id)
    await ctx.send("Removed entry for given ID")
  else:
    await ctx.send("No entry found for that user ID")

#@remove_registration.error
async def remove_registration_error(ctx, error):
  if isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
    await ctx.author.send("This command cannot be executed via DM")
  elif isinstance(error, discord.ext.commands.errors.MissingRole):
    await ctx.author.send("You do not have permission to execute this command")
  else:
    await ctx.author.send(error)

@bot.command()
async def ping(ctx):
    """Check if alive"""
    await ctx.send("pong")

#@bot.command()
#@commands.has_role("Mods")
#async def reset_bot_raid_cog(ctx):
#  await ctx.send("Removing cog [RaidPost]")
#  bot.remove_cog('RaidPost')
#  importlib.reload(raid_cog)
#  await ctx.send("Cog [RaidPost] Removed.\nRe-adding cog.")
#  bot.add_cog(RaidPost(bot))
#  await ctx.send("Cog [RaidPost] added and reset.")

#@bot.event
#async def on_command_error(ctx,error):
#  if isinstance(error, commands.errors.NoPrivateMessage):
#    print("User tried to use guild only command")


async def startup_process():
  await bot.wait_until_ready()
  bot.pool = await init_pool()
  bot.add_cog(RaidPost(bot))
  bot.guild_info_dictionary = guild_info_dictionary
  await spin_up_message_deletions(bot)

bot.loop.create_task(startup_process())
bot.run(TOKEN)
