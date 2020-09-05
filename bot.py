import discord
from discord.ext import commands
from data import *
import xml.etree.ElementTree as ET
import string
import wget
import os
import dict_digger

description = '''TheStaplergun's Bot in Python'''
bot = commands.Bot(command_prefix='$', description=description)

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print('------')
	await bot.change_presence(game=discord.Game(name='Work in Progress'))

@bot.command(pass_context=True)
async def whostheboss(ctx):
  if ctx.message.author.id == OWNERID:
    await bot.say("You're the boss")
  else:
    await bot.say("You ain't the boss")

@bot.command()
async def ping():
    """Check if alive"""
    await bot.say("pong")

bot.run(TOKEN)
