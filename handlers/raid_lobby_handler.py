import asyncpg
import discord
import handlers.raid_handler as RH

GET_CATEGORY_BY_GUILD_ID = """
    SELECT * FROM raid_lobby_category WHERE (guild_id = $1) LIMIT 1;
"""
async def get_raid_lobby_category_channel_id(bot, guild_id):
    connection = await bot.acquire()
    try:
        category_data = await connection.fetchrow(GET_CATEGORY_BY_GUILD_ID,
                                                  int(guild_id))
    except asyncpg.Exception as error:
        print("[!] Error retreiving raid lobby category data. [{}]".format(error))
        return
    finally:
        await bot.pool.release(connection)

    category_id = category_data.get("category_id")
    if not category_id:
        print("[!] Error retreiving raid lobby category data. [{}]".format(error))
        return False

    return category_id


GET_LOBBY_BY_USER_ID = """
    SELECT * FROM raid_lobby_user_map WHERE (host_user_id = $1) LIMIT 1;
"""
async def get_lobby_channel_for_user_by_id(bot, user_id):
    connection = await bot.acquire()
    try:
        lobby_data = await connection.fetchrow(GET_LOBBY_BY_USER_ID,
                                                  int(user_id))
    except asyncpg.Exception as error:
        print("[!] Error retreiving raid lobby data. [{}]".format(error))
        return
    finally:
        await bot.pool.release(connection)

    lobby_channel_id = lobby_data.get("lobby_channel_id")
    guild_id = lobby_data.get("guild_id")

    guild = bot.get_guild(int(guild_id))
    if not guild:
        print("[!] Error retreiving guild. [{}]".format(error))
        return False

    lobby = guild.get_channel(int(lobby_channel_id))
    if not lobby:
        print("[!] Error retreiving lobby. [{}]".format(error))
        return False

    return lobby

GET_LOBBY_BY_LOBBY_ID = """
    SELECT * FROM raid_lobby_user_map WHERE (lobby_channel_id = $1) LIMIT 1;
"""
async def get_lobby_channel_by_lobby_id(bot, channel_id):
    connection = await bot.acquire()
    try:
        lobby_data = await connection.fetchrow(GET_LOBBY_BY_USER_ID,
                                               int(channel_id))
    except asyncpg.Exception as error:
        print("[!] Error retreiving raid lobby data. [{}]".format(error))
        return
    finally:
        await bot.pool.release(connection)
    if not lobby_data:
        return False

    lobby_channel_id = lobby_data.get("lobby_channel_id")
    guild_id = lobby_data.get("guild_id")

    guild = bot.get_guild(int(guild_id))
    if not guild:
        print("[!] Error retreiving guild. [{}]".format(error))
        return False

    lobby = guild.get_channel(int(lobby_channel_id))
    if not lobby:
        print("[!] Error retreiving lobby. [{}]".format(error))
        return False

    return lobby

async def log_message_in_raid_lobby_channel(bot, message, raid_lobby_channel):
    author = message.author
    new_embed = discord.Embed(title="Logged Message", url=message.jump_url, description=message.content)
    new_embed.set_author(name=author.display_name, icon_url=author.avatar_url)
    new_embed.set_footer(text="User ID: {}".format(author.id))
    await raid_lobby_channel.send(" ", embed=new_embed)
# async def set_up_management_channel(ctx, bot):
#     channel = ctx.channel
#     if not channel.category_id:
#         embed = discord.Embed(title="Error", description="This channel is not in a category. A category is necessary to set up a raid lobby system. Create a category and place a channel in there, then run this command again.", color=0xff8c00)
#         ctx.send(" ",embed=embed, delete_after=15)
#         return False

#     category_id = channel.category_id



#async def user_lobby_management_reaction_handle(ctx, bot):

# async def set_up_lobby_log_channel(ctx, bot):
#     channel = ctx.channel
#     if not channel.category_id:
#         embed = discord.Embed(title="Error", description="This channel is not in a category. A category is necessary to set up a raid lobby system. Create a category and place a channel in there, then run this command again.", color=0xff8c00)
#         ctx.send(" ",embed=embed, delete_after=15)
#         return False

#     try:
#         await channel.edit(name="raid-lobby-logs", reason="Establishing log channel for raid lobbies.")
#     except discord.DiscordException as error:
#         print("[*][{}] An error occurred setting up the log channel for a raid category. [{}]".format(ctx.guild.name, error))
#         return False

#     return True

NEW_LOBBY_INSERT = """
INSERT INTO raid_lobby_user_map (lobby_channel_id, host_user_id, guild_id, delete_at)
VALUES($1, $2, $3, $4, $5, $6)
"""
async def add_lobby_to_table(bot, lobby_channel_id, host_user_id, guild_id, delete_at):
    """Add a raid to the database with all the given data points."""
    cur_time = datetime.now()
    connection = await bot.acquire()
    await connection.execute(NEW_LOBBY_INSERT,
                             int(lobby_channel_id),
                             int(host_user_id),
                             int(guild_id),
                             delete_at)
    await bot.release(connection)

async def create_raid_lobby(ctx, bot, raid_message_id, raid_host_member, time_to_remove_lobby):
    guild = ctx.guild
    raid_lobby_category_channel_id = await get_raid_lobby_category_channel_id(bot, guild.id)
    if not raid_lobby_category_channel_id:
        return False

    raid_lobby_category_channel = guild.get_channel(int(raid_lobby_category_channel_id))

    mod_role = discord.utils.get(guild.roles, name="Mods")
    raid_moderator_role = discord.utils.get(guild.roles, name="Raid Moderator")
    count = await RH.get_raid_count(bot, ctx, False)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        mod_role: discord.PermissionOverwrite(read_messages=True),
        raid_moderator_role: discord.PermissionOverwrite(read_messages=True),
        raid_host_member: discord.PermissionOverwrite(read_messages=True)
    }
    channel_name = "Raid Lobby {}".format(count)
    reason = "Spawning new raid lobby for [{}]".format(raid_host_member.name)
    try:
        new_raid_lobby = await raid_lobby_category_channel.create_channel(channel_name, reason=reason, overwrites=overwrites)
    except discord.DiscordException as error:
        try:
            await ctx.send("Something went wrong when trying to create your raid lobby: [{}]".format(error))
        except discord.DiscordException:
            pass
        print("[!][{}] An error occurred creating a raid lobby. [{}]".format(error))
        return False

    try:
        await add_lobby_to_table(bot, new_raid_lobby.id, raid_host_member.id, ctx.guild.id, time_to_remove_lobby)
    except asyncpg.PostgresError as error:
        print("[!][{}] An error occurred adding a lobby to the database. [{}]".format(error))
        await new_raid_lobby.delete()
        return False

    return True
