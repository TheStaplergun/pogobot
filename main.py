"""Main bot set up and command set up"""

import argparse
import asyncio
from datetime import datetime
import os
import sys

import asyncpg
import discord
#from discord.ext import commands

import classes.bot as bot
import important
#import raid_cog

#from . import handlers
from tasks import *

DESCRIPTION = '''Pokemon Go Raid Bot'''

#Set command_prefix to any character here.
COMMAND_PREFIX = '-'
#Change this string to change the 'playing' status of the bot.
CUSTOM_STATUS = ""

intent = discord.Intents().default()
intent.members = True
intent.guilds = True

GAME = discord.Game(CUSTOM_STATUS)
BOT = bot.Bot(COMMAND_PREFIX, description=DESCRIPTION, activity=GAME, intents=intent)

BOT.pool = None
BOT.categories_allowed = True

live=False

def initialize_cogs():
    cog_list = []
    for root, _, files in os.walk("cogs"):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filepath.endswith(".py"):
                cog_list.append(filepath.split(".py")[0].replace(os.sep, "."))
    for cog in cog_list:
        try:
            BOT.load_extension(cog)
        except Exception as error:
            print(f"[!] An error occurred while loading COG [{cog}]: [{error}]")
            return False
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-l", action="store_true")
    args = parser.parse_args()

    if not initialize_cogs():
        print("[!] An error occurred during cog initialization. Exiting.")
        sys.exit()

    BOT.loop.create_task(startup_process(BOT, live))
    BOT.loop.create_task(status_update_loop(BOT))
    BOT.loop.create_task(applicant_loop(BOT))
    BOT.loop.create_task(lobby_removal_loop(BOT))
    if args.l:
        print("[!] Running bot live.")
        live=True
        BOT.run(important.LIVE_TOKEN)
    else:
        print("[i] Running bot in test mode")
        BOT.run(important.TESTING_TOKEN)
