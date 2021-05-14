"""Main bot set up and command set up"""

import argparse
import asyncio
import asyncpg
from datetime import datetime
import dotenv
import discord
from discord.ext import commands
import os
import raid_cog
import time
import handlers.event_handlers as EH
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH
import handlers.registration_handler as REGH
import handlers.request_handler as REQH
import handlers.startup_handler as SH

if os.path.exists('.env'):
    dotenv.load_dotenv()
else:
    print('[!] .env not found!')

DESCRIPTION = '''TheStaplergun's Bot in Python'''

#Set command_prefix to any character here.
COMMAND_PREFIX = os.getenv('PREFIX') or '-'
#Change this string to change the 'playing' status of the bot.
CUSTOM_STATUS = os.getenv('STATUS') or ''

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
    pool = await asyncpg.create_pool(database=os.getenv('DB'),
                                     port=os.getenv('DBPORT'),
                                     host=os.getenv('DBHOST'),
                                     user=os.getenv('DBUSER'),
                                     password=os.getenv('DBPASSWORD'))

    return pool

@BOT.event
async def on_ready():
    """Built in event"""
    print(f'[OK] Logged in as {BOT.user.name} \n')
    #print(BOT.commands)

@BOT.event
async def on_raw_reaction_add(ctx):
    """Built in event"""
    await EH.raw_reaction_add_handle(ctx, BOT)

@BOT.event
async def on_raw_message_delete(ctx):
    """Built in event"""
    await EH.raw_message_delete_handle(ctx, BOT)

@BOT.event
async def on_guild_channel_delete(channel):
    await EH.on_guild_channel_delete(channel, BOT)

@BOT.event
async def on_message(message):
    """Built in event"""
    try:
        await EH.on_message_handle(message, BOT)
    except Exception as error:
        print("[!] An exception occurred during message handling. [{}]".format(error))
    await BOT.process_commands(message)

@BOT.command()
@commands.guild_only()
@commands.has_role(os.getenv('MOD_ROLE'))
async def clear_raid(ctx, user_id):
    await RH.handle_clear_user_from_raid(ctx, BOT, user_id)

@BOT.command()
@commands.guild_only()
@commands.has_role(os.getenv('MOD_ROLE'))
async def clear_requests(ctx):
    await REQH.handle_clear_all_requests_for_guild(ctx, BOT)

@BOT.command()
@commands.guild_only()
async def request(ctx, tier=None, pokemon_name=None):
    """Processes a users pokemon request"""
    if not await REQH.check_if_valid_request_channel(BOT, ctx.channel.id):
        await ctx.author.send(H.guild_member_dm("That channel is not a valid request channel."))
        return
    await REQH.request_pokemon_handle(BOT, ctx, tier, pokemon_name)

@BOT.command()
@commands.guild_only()
@commands.has_role(os.getenv('MOD_ROLE'))
async def get_requests(ctx):
    await REQH.handle_get_all_requests(ctx, BOT)

@BOT.command()
@commands.guild_only()
@commands.has_role(os.getenv('MOD_ROLE'))
async def register_request_channel(ctx):
    """Mod only - Sets up channel to allow Pokemon requests"""
    await REGH.register_request_channel_handle(ctx, BOT)

@BOT.command()
@commands.guild_only()
@commands.has_role(os.getenv('MOD_ROLE'))
async def register_raid_channel(ctx):
    """Mod only - Sets up channel to allow hosting raids"""
    await REGH.register_raid_channel_handle(ctx, BOT)

@BOT.command()
@commands.guild_only()
@commands.has_role(os.getenv('MOD_ROLE'))
async def register_raid_lobby_category(ctx):
    """Mod only - Sets up category to allow automation of raid lobbies"""
    await REGH.register_raid_lobby_category(ctx, BOT)

@BOT.command()
@commands.has_role(os.getenv('MOD_ROLE'))
async def toggle_category_system(ctx):
    BOT.categories_allowed = not BOT.categories_allowed
    await ctx.send("System is {}".format("on" if BOT.categories_allowed else "off"), delete_after=5)

@BOT.command()
@commands.has_role(os.getenv('MOD_ROLE'))
async def raid_count(ctx):
    """Mod only - Show total raids hosted in this server"""
    try:
        await ctx.message.delete()
    except discord.NotFound as error:
        print("[!] Message already gone. [{}]".format(error))
    await RH.get_raid_count(BOT, ctx, True)

# @BOT.command()
# @commands.has_role(os.getenv('MOD_ROLE'))
# async def get_lobbies(ctx):
#     """Mod Only - Show all current running raid statistics for this guild"""
#     await RLH.get_all_lobbies_for_guild(ctx, BOT)

# @BOT.command()
# @commands.has_role(os.getenv('MOD_ROLE'))
# async def get_all_applications(ctx):
#     """Mod Only - Show all current running raid statistics for this guild"""
#     await RLH.get_all_applications_for_guild(ctx, BOT)

@BOT.command()
@commands.has_role(os.getenv('MOD_ROLE'))
async def refresh_request_reactions(ctx, message_id):
    try:
        await ctx.message.delete()
    except discord.DiscordException:
        pass

    channel = ctx.channel
    try:
        message = await channel.fetch_message(int(message_id))
        print(message)
        await message.clear_reactions()
        await message.add_reaction("📬")
        await message.add_reaction("📪")
    except discord.DiscordException as error:
        print("[!] Error refreshing reactions [{}]".format(error))
    
@BOT.command()
async def ping(ctx):
    """Check if alive"""
    curr = time.time()
    latency: float = round(ctx.bot.latency * 1000.0, 2)
    msg = await ctx.send('Pinging... 🏓')
    await msg.edit(
        content=f'🏓 Pong! Latency is {round((time.time() - curr) * 1000.0, 2)}ms. API latency is {latency}ms.')

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-l", action="store_true")
    args = parser.parse_args()
    BOT.applicant_trigger = asyncio.Event()
    BOT.lobby_remove_trigger = asyncio.Event()

    BOT.loop.create_task(startup_process())
    BOT.loop.create_task(status_update_loop())
    BOT.loop.create_task(applicant_loop())
    BOT.loop.create_task(lobby_removal_loop())
    if args.l:
        print("[i] Running bot live.")
        live=True
        BOT.run(os.getenv('LIVE_TOKEN'))
    else:
        print("[i] Running bot in test mode")
        BOT.run(os.getenv('TEST_TOKEN'))
