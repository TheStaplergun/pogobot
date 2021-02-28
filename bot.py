"""Main bot set up and command set up"""

from datetime import datetime
import discord
from discord.ext import commands
import asyncpg
import important
import raid_cog
import handlers.event_handlers as EH
import handlers.helpers as H
import handlers.raid_handler as RH
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

GAME = discord.Game(CUSTOM_STATUS)
BOT = commands.Bot(COMMAND_PREFIX, description=DESCRIPTION, activity=GAME, intents=intent)

BOT.pool = None
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

@BOT.event
async def on_ready():
    """Built in event"""
    print('Logged in as')
    print(BOT.user.name)
    print('------------------')

@BOT.event
async def on_raw_reaction_add(ctx):
    """Built in event"""
    await EH.raw_reaction_add_handle(ctx, BOT)

@BOT.event
async def on_raw_message_delete(ctx):
    """Built in event"""
    await EH.raw_message_delete_handle(ctx, BOT)

@BOT.event
async def on_message(message):
    """Built in event"""
    handled = await EH.on_message_handle(message, BOT)
    if handled:
        return
    await BOT.process_commands(message)

@BOT.command()
@commands.guild_only()
@commands.has_role("Mods")
async def clear_raid(ctx, user_id):
    await RH.handle_clear_user_from_raid(ctx, BOT, user_id)

@BOT.command()
@commands.guild_only()
@commands.has_role("Mods")
async def clear_requests(ctx):
    await REQH.handle_clear_all_requests_for_guild(ctx, BOT)
    
@BOT.command()
@commands.guild_only()
async def request(ctx, tier=None, pokemon_name=None):
    """Processes a users pokemon request"""
    if not await REQH.check_if_valid_request_channel(BOT, ctx.channel.id):
        ctx.author.send(H.guild_member_dm("That channel is not a valid request channel."))
        return
    await REQH.request_pokemon_handle(BOT, ctx, tier, pokemon_name)

@BOT.command()
@commands.guild_only()
@commands.has_role("Mods")
async def get_requests(ctx):
    await REQH.handle_get_all_requests(ctx, BOT)

@BOT.command()
@commands.guild_only()
@commands.has_role("Mods")
async def register_request_channel(ctx):
    """Mod only - Sets up channel to allow Pokemon requests"""
    await REGH.register_request_channel_handle(ctx, BOT)

@BOT.command()
@commands.has_role("Mods")
async def register_raid_channel(ctx):
    """Mod only - Sets up channel to allow hosting raids"""
    await REGH.register_raid_channel_handle(ctx, BOT)

@BOT.command()
@commands.has_role("Mods")
async def raid_count(ctx):
    """Mod only - Show total raids hosted in this server"""
    try:
        await ctx.message.delete()
    except discord.NotFound as error:
        print("[!] Message already gone. [{}]".format(error))
    await RH.get_raid_count(BOT, ctx)

@BOT.command()
async def ping(ctx):
    """Check if alive"""
    create_time = ctx.message.created_at
    cur_time = datetime.now()
    time_dif = cur_time - create_time
    await ctx.send("Pong `{}ms`".format(time_dif.total_seconds()*1000))

async def startup_process():
    """Startup process. Linear process."""
    await BOT.wait_until_ready()
    BOT.pool = await init_pool()
    BOT.add_cog(raid_cog.RaidPost(BOT))
    #await SH.spin_up_message_deletions(BOT)

async def status_update_loop():
    """Updates status continually every ten minutes."""
    await BOT.wait_until_ready()
    await SH.start_status_update_loop(BOT)

BOT.loop.create_task(startup_process())
BOT.loop.create_task(status_update_loop())
BOT.run(important.TOKEN)
