import discord
import handlers.raid_handler as RH

async def get_raid_lobby_category_channel(bot, guild_id):
    connection = await bot.acquire()

    await bot.release(connection)

async def get_lobby_for_user_by_id(bot, user_id):
    connection = await bot.acquire()

    await bot.release(connection)

async def set_up_management_channel(bot, guild_id, lobby_cagetogory):


async def create_raid_lobby(ctx, bot, raid_message_id, raid_host_member):
    guild = ctx.guild
    raid_lobby_category_channel_id = await get_raid_lobby_category_channel_id(bot, guild.id)
    if not raid_lobby_category_channel_id:
        return False

    raid_lobby_category_channel = guild.get_channel(raid_lobby_category_channel_id)

    mod_role = discord.utils.get(guild.roles, name="Mods")
    raid_moderator_role = discord.utils.get(guild.roles, name="Raid Moderator")
    count = RH.get_raid_count(bot, ctx, False)
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
            ctx.send("Something went wrong when trying to create your raid lobby: [{}]".format(error))
        except discord.DiscordException:
            pass
        print("[!][{}] An error occurred creating a raid lobby. [{}]".format(error))
        return False
    return True