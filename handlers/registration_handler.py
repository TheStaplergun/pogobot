"""Channel registration handling"""
import asyncpg
import discord
import handlers.request_handler as REQH
import handlers.sticky_handler as SH

ADD_RAID_CHANNEL = """
INSERT INTO valid_raid_channels (channel_id, guild_id)
VALUES ($1, $2);
"""
INIT_RAID_COUNTER = """
INSERT INTO guild_raid_counters (guild_id)
VALUES ($1);
"""
async def database_register_raid_channel(bot, ctx, channel_id, guild_id):
    """Registers raid channel within database and initalizes guilds raid counter."""
    connection = await bot.acquire()
    results = None
    try:
        results = await connection.execute(ADD_RAID_CHANNEL,
                                           int(channel_id),
                                           int(guild_id))
    except asyncpg.PostgresError as error:
        print("[!] Error occured registering raid channel. [{}]".format(error))
    try:
        await connection.execute(INIT_RAID_COUNTER,
                                 int(guild_id))
    except asyncpg.PostgresError as error:
        print("[!] Error occured registering raid counter. [{}]".format(error))
    await bot.release(connection)
    if results:
        print("[*][{}][{}] New raid channel registered.".format(ctx.guild.name, channel_id))

async def register_request_channel_handle(ctx, bot):
    channel_id = ctx.channel.id
    guild_id = ctx.guild.id
    try:
        await ctx.message.delete()
    except:
        pass
    await REQH.database_register_request_channel(bot, ctx, channel_id, guild_id)

async def register_raid_channel_handle(ctx, bot):
    channel_id = ctx.channel.id
    guild_id = ctx.guild.id
    try:
        await ctx.message.delete()
    except discord.DiscordException:
        pass
    await database_register_raid_channel(bot, ctx, channel_id, guild_id)
    try:
        await SH.toggle_raid_sticky(bot, ctx, channel_id, guild_id)
    except discord.DiscordException as e:
        print("[!] An error occurred [{}]".format(e))
