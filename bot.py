"""Main bot set up and command set up"""

import argparse
import asyncio
from datetime import datetime
import sys

import asyncpg
import discord
from discord.ext import commands

import important
import raid_cog
import handlers.event_handlers as EH
import handlers.friend_code_handler as FCH
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH
import handlers.registration_handler as REGH
import handlers.request_handler as REQH
import handlers.startup_handler as SH

DESCRIPTION = '''TheStaplergun's Bot in Python'''

#Set command_prefix to any character here.
COMMAND_PREFIX = '-'
#Change this string to change the 'playing' status of the bot.
CUSTOM_STATUS = ""

intent = discord.Intents().default()
intent.members = True
intent.guilds = True

GAME = discord.Game(CUSTOM_STATUS)
BOT = commands.Bot(COMMAND_PREFIX, description=DESCRIPTION, activity=GAME, intents=intent)

BOT.pool = None
BOT.categories_allowed = True
#BOT.raids_enabled = True
#BOT.bot_ready_to_process = False

async def acquire_pool_connection():
    """Asyncpg pool connection acquisition wrapper"""
    connection = await BOT.pool.acquire()
    return connection

async def release_pool_connection(connection):
    """Asyncpg pool connection release wrapper"""
    if connection:
        await BOT.pool.release(connection)

BOT.acquire = acquire_pool_connection
BOT.release = release_pool_connection

async def init_pool():
    """Set up asyncpg connection pool"""
    pool = await asyncpg.create_pool(database=important.DATABASE,
                                     port=important.PORT,
                                     host=important.HOST,
                                     user=important.DB_USER,
                                     password=important.PASSWORD)

    return pool

live=False
async def startup_process():
    """Startup process. Linear process."""
    await BOT.wait_until_ready()
    BOT.pool = await init_pool()
    BOT.add_cog(raid_cog.RaidPost(BOT))
    if live:
        await SH.spin_up_message_deletions(BOT)

async def status_update_loop():
    """Updates status continually every ten minutes."""
    await BOT.wait_until_ready()
    await SH.start_status_update_loop(BOT)

async def lobby_removal_loop():
    """Removes lobbies as their time expires."""
    await BOT.wait_until_ready()
    #await RLH.establish_lobby_removal_list(BOT)
    await SH.start_lobby_removal_loop(BOT)

async def applicant_loop():
    await BOT.wait_until_ready()
    await SH.start_applicant_loop(BOT)

def initialize_cogs(bot):
    cog_list = []
    for root, _, files in os.walk("cogs"):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filepath.endswith(".py"):
                cog_list.append(filepath.split(".py")[0].replace(os.sep, "."))
    for cog in cog_list:
        try:
            bot.load_extension(cog)
        except Exception as error:
            print(f"[!] An error occurred while loading COG [{cog}]: [{error}]")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-l", action="store_true")
    args = parser.parse_args()

    if not initialize_cogs(BOT):
        print("[!] An error occurred during cog initialization. Exiting.")
        sys.exit()

    BOT.applicant_trigger = asyncio.Event()
    BOT.lobby_remove_trigger = asyncio.Event()

    BOT.loop.create_task(startup_process())
    BOT.loop.create_task(status_update_loop())
    BOT.loop.create_task(applicant_loop())
    BOT.loop.create_task(lobby_removal_loop())
    if args.l:
        print("[!] Running bot live.")
        live=True
        BOT.run(important.LIVE_TOKEN)
    else:
        print("[i] Running bot in test mode")
        BOT.run(important.TESTING_TOKEN)
