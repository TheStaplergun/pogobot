"""Event handler functions."""
from datetime import datetime
import discord
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handler as REQH
import handlers.raid_lobby_handler as RLH
import handlers.sticky_handler as SH

async def handle_reaction_remove_raid_with_lobby(bot, ctx, message):
    message_id = message.id
    results = await RH.check_if_in_raid(ctx, bot, ctx.user_id)
    if results and results.get("message_id") == message_id:
        message_to_send = "Your raid has been successfuly deleted."
        conn = await bot.acquire()
        await RH.remove_raid_from_table(conn, message.id)
        await bot.release(conn)
        try:
            await message.delete()
        except discord.DiscordException:
            pass
        await RLH.alter_deletion_time_for_raid_lobby(bot, ctx)
        try:
            await SH.toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
        except discord.DiscordException as error:
            print("[!] An error occurred [{}]".format(error))
    else:
        message_to_send = "You are not the host. You cannot delete this raid!"

    await ctx.member.send(H.guild_member_dm(bot.get_guild(ctx.guild_id).name, message_to_send))

async def handle_reaction_remove_raid_no_lobby(bot, ctx, message):
    user_id = message.mentions[0].id

    if int(user_id) != ctx.user_id:
        message_to_send = "You are not the host. You cannot delete this raid!"
    else:
        message_to_send = "Your raid has been successfuly deleted."
        conn = await bot.acquire()
        await RH.remove_raid_from_table(conn, message.id)
        await bot.release(conn)
        try:
            await message.delete()
        except discord.DiscordException:
            pass
        try:
            await SH.toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
        except discord.DiscordException as error:
            print("[!] An error occurred [{}]".format(error))
    await ctx.member.send(H.guild_member_dm(bot.get_guild(ctx.guild_id).name, message_to_send))

WATCHED_EMOJIS = (
    "📝",
    "📬",
    "📪",
    "🗑️",
    "⏱️"
)

async def raw_reaction_add_handle(ctx, bot):
    #Bot ignores itself adding emojis
    if ctx.user_id == bot.user.id:
        return

    if ctx.emoji.name not in WATCHED_EMOJIS:
        return

    raid_channel = await RH.check_if_valid_raid_channel(bot, ctx.channel_id)
    request_channel = await REQH.check_if_valid_request_channel(bot, ctx.channel_id)

    channel = bot.get_channel(int(ctx.channel_id))
    if not channel:
        try:
            bot.fetch_channel(int(ctx.channel_id))
        except discord.DiscordException:
            return
    try:
        message = await channel.fetch_message(int(ctx.message_id))
    except discord.DiscordException:
        return

    if not message.author.id == bot.user.id:
        return

    if bot.categories_allowed and ctx.emoji.name == "⏱️" and channel.type == discord.ChannelType.private:
        await RLH.handle_activity_check_reaction(ctx, bot, message)
        return
    # if not len(message.embeds) == 1:
    #     return
    # if not raid_channel and not request_channel:
    #     return
    if raid_channel or request_channel:
        #await message.remove_reaction(ctx.emoji, discord.Object(ctx.user_id))#ctx.guild.get_member(ctx.user_id))
        category_exists = await RLH.get_raid_lobby_category_by_guild_id(bot, message.guild.id)
        if bot.categories_allowed and ctx.emoji.name == "📝":

            if not category_exists:
                return
            await RLH.handle_application_to_raid(bot, ctx, message, channel)
        elif ctx.emoji.name == "📬":
            await REQH.add_request_role_to_user(bot, ctx, message)
        elif ctx.emoji.name == "📪":
            await REQH.remove_request_role_from_user(bot, ctx, message)
        elif ctx.emoji.name == "🗑️":
            if not category_exists or not bot.categories_allowed:
                await handle_reaction_remove_raid_no_lobby(bot, ctx, message)
            else:
                await handle_reaction_remove_raid_with_lobby(bot, ctx, message)
        # elif len(message.mentions) == 1:
        #     no_emoji = bot.get_emoji(743179437054361720)
        #     if ctx.emoji == no_emoji:
        #         await handle_reaction_remove_raid(bot, ctx, message, no_emoji)
        #         return

async def raid_delete_handle(ctx, bot):
    if not await RH.message_is_raid(ctx, bot, ctx.message_id):
        return
    conn = await bot.acquire()
    await RH.remove_raid_from_table(conn, ctx.message_id)
    await bot.release(conn)
    lobby_data = await RLH.get_lobby_data_by_raid_id(bot, ctx.message_id)
    if not lobby_data:
        return
    user_id = lobby_data.get("host_user_id")
    ctx.user_id = user_id
    await RLH.alter_deletion_time_for_raid_lobby(bot, lobby_data)

    try:
        await SH.toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
    except discord.DiscordException as error:
        print("[!] An error occurred [{}]".format(error))

async def request_delete_handle(ctx, bot):
    does_exist, channel_id, message_id, role_id = await REQH.get_request_by_message_id(bot, ctx.message_id)
    guild = bot.get_guild(ctx.guild_id)
    if not does_exist:
        return
    role = discord.utils.get(guild.roles, id=role_id)
    channel = guild.get_channel(channel_id)
    message = None
    try:
        if channel:
            message = await channel.fetch_message(message_id)
    except discord.DiscordException:
        pass
    await REQH.delete_request_role_and_post(ctx, bot, guild, message, role)

async def raw_message_delete_handle(ctx, bot):
    if await RH.check_if_valid_raid_channel(bot, ctx.channel_id):
        await raid_delete_handle(ctx, bot)

    if await REQH.check_if_valid_request_channel(bot, ctx.channel_id):
        await request_delete_handle(ctx, bot)

    channel_id = ctx.channel_id
    channel = bot.get_channel(int(channel_id))
    if bot.categories_allowed and channel.type == discord.ChannelType.private:
        applicant_data = await RLH.get_applicant_data_by_message_id(bot, ctx.message_id)
        if not applicant_data:
            return
        if not applicant_data.get("checked_in") and ctx.message_id == applicant_data.get("activity_check_message_id"):
            await RLH.handle_user_failed_checkin(bot, applicant_data)

async def on_message_handle(message, bot):
    if message.author.bot:
        return True
    # Handle this first because it's a logging function.
    raid_lobby_channel = await RLH.get_lobby_channel_by_lobby_id(bot, message.channel.id)
    if bot.categories_allowed and raid_lobby_channel:
        await RLH.log_message_in_raid_lobby_channel(bot, message)
        return True

    raid_channel = await RH.check_if_valid_raid_channel(bot, message.channel.id)
    request_channel = await REQH.check_if_valid_request_channel(bot, message.channel.id)

    if not raid_channel and not request_channel and not raid_lobby_channel:
        return False

    #if message.author.id == bot.user.id:
        #return False

    if discord.utils.get(message.author.roles, name="Mods"):
        return False
    
    if message.content.startswith(bot.command_prefix, 0, 1):
        for command in bot.commands:
            if message.content.startswith("-{}".format(command.name), 0, len(command.name) + 1):
                return False
            for alias in command.aliases:
                if message.content.startswith("-{}".format(alias), 0, len(alias) + 1):
                    return False

    content = message.content

    await message.author.send(H.guild_member_dm(message.guild.name, "This is a curated channel. Read the guide and use the correct command for this channel."))
        
    try:
        print("[*][{}][{}] Invalid message deleted [{}]".format(message.guild.name, message.author.name, content))
        await message.delete()
    except discord.NotFound:
        pass

async def on_guild_channel_delete(channel, bot):
    lobby_channel = await RLH.get_lobby_channel_by_lobby_id(bot, channel.id)
    if lobby_channel:
        RLH.remove_lobby_by_lobby_id(bot, lobby_channel.id)

    await RLH.check_if_log_channel_and_purge_data(bot, channel.id)
