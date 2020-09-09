import discord
from discord.ext import commands
import data
from important import OWNERID,TOKEN
import raid_cog
from raid_cog import *
from bot_lib import *
import xml.etree.ElementTree as ET
import string
import os

description = '''TheStaplergun's Bot in Python'''

"""Set command_prefix to any character here."""
COMMAND_PREFIX = '$'
"""Change this string to change the 'playing' status of the bot."""
CUSTOM_STATUS = "WIP"

bot = commands.Bot(COMMAND_PREFIX, description=description)
game = discord.Game(CUSTOM_STATUS)

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print('------')
  await bot.change_presence(activity=game)
  await perform_message_cleanup(bot)

@bot.command()
async def test(ctx):
  if ctx.author.id == int(OWNERID):
    await ctx.send("Success")
  else:
    await ctx.send(ctx.author.id)

@bot.command()
async def ping(ctx):
    """Check if alive"""
    await ctx.send("pong")

@bot.command()
@commands.has_role("Mods")
async def reset_bot_raid_cog(ctx):
  await ctx.send("Removing cog [RaidPost]")
  bot.remove_cog('RaidPost')
  importlib.reload(raid_cog)
  await ctx.send("Cog [RaidPost] Removed.\nRe-adding cog.")
  bot.add_cog(RaidPost(bot))
  await ctx.send("Cog [RaidPost] added and reset.")

@bot.command()
@commands.has_role("Mods")
async def restore_backup_data(ctx):
  restore_backup()

bot.add_cog(RaidPost(bot))
bot.run(TOKEN)
