"""Event handler functions."""
import discord
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handler as REQH
import handlers.sticky_handler as SH

async def handle_reaction_remove_raid(bot, ctx, message, emoji):
    user_id = message.mentions[0].id

    if int(user_id) != ctx.user_id:
        message_to_send = "You are not the host. You cannot delete this raid!"
        try:
            await message.remove_reaction(emoji, (bot.get_guild(ctx.guild_id)).get_member(ctx.user_id))
        except discord.DiscordException as error:
            print("[*] Error removing reaction [{}]".format(error))
    else:
        message_to_send = "Your raid has been successfuly deleted."
        conn = await bot.acquire()
        await RH.remove_raid_from_table(conn, message.id)
        await bot.release(conn)
        await message.delete()
        try:
            await SH.toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
        except discord.DiscordException as error:
            print("[!] An error occurred [{}]".format(error))
    await ctx.member.send(H.guild_member_dm(bot.get_guild(ctx.guild_id).name, message_to_send))


async def raw_reaction_add_handle(ctx, bot):
    #Bot ignores itself adding emojis
    if ctx.user_id == bot.user.id:
        return

    raid_channel = await RH.check_if_valid_raid_channel(bot, ctx.channel_id)
    request_channel = await REQH.check_if_valid_request_channel(bot, ctx.channel_id)
    if not raid_channel and not request_channel:
        return

    channel = bot.get_channel(ctx.channel_id)
    try:
        message = await channel.fetch_message(ctx.message_id)
    except discord.DiscordException:
        return

    if not message.author.id == bot.user.id:
        return

    if not len(message.embeds) == 1:
        return

    if raid_channel or request_channel :
        await message.remove_reaction(ctx.emoji, discord.Object(ctx.user_id))#ctx.guild.get_member(ctx.user_id))

        if ctx.emoji.name == "📬":
            await REQH.add_request_role_to_user(bot, ctx, message)
            return
        elif ctx.emoji.name == "📪":
            await REQH.remove_request_role_from_user(bot, ctx, message)
            return
        elif len(message.mentions) == 1:
            no_emoji = bot.get_emoji(743179437054361720)
            if ctx.emoji == no_emoji:
                await handle_reaction_remove_raid(bot, ctx, message, no_emoji)
                return

async def raid_delete_handle(ctx, bot):
    if not await RH.message_is_raid(ctx, bot, ctx.message_id):
        return
    conn = await bot.acquire()

    await RH.remove_raid_from_table(conn, ctx.message_id)
    await bot.release(conn)
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

async def on_message_handle(message, bot):
    raid_channel = await RH.check_if_valid_raid_channel(bot, message.channel.id)
    request_channel = await REQH.check_if_valid_request_channel(bot, message.channel.id)
    if not raid_channel and not request_channel:
        return False

    if message.author.id == bot.user.id:
        return False
    if message.author.bot:
        return True
    if discord.utils.get(message.author.roles, name="Mods"):
        return False

    if not message.content.startswith(bot.command_prefix, 0, 1):
        content = message.content
        try:
            await message.author.send(H.guild_member_dm(message.guild.name, "This is a curated channel. Read the guide and use the correct command for this channel."))
        except discord.DiscordException:
            pass
        try:
            print("[*][{}][{}] Invalid message deleted [{}]".format(message.guild.name, message.author.name, content))
            await message.delete()
        except discord.NotFound:
            pass
