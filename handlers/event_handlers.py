"""Event handler functions."""
import discord
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.sticky_handler as SH


async def raw_reaction_add_handle(ctx, bot):
    #Bot ignores itself adding emojis
    if ctx.user_id == bot.user.id:
        return

    if not await RH.check_if_valid_raid_channel(bot, ctx.channel_id):
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

    if not len(message.mentions) == 1:
        return

    user_id = message.mentions[0].id

    if int(user_id) != ctx.user_id:
        message_to_send = "You are not the host. You cannot delete this raid!"
        for reaction in message.reactions:
            async for user in reaction.users():
                if user.id == ctx.user_id:
                    try:
                        await reaction.remove(user)
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
    await ctx.member.send(H.guild_member_dm(channel.guild.name, message_to_send))

async def raid_delete_handle(ctx, bot):
    conn = await bot.acquire()
    await RH.remove_raid_from_table(conn, ctx.message_id)
    await bot.release(conn)
    try:
        await SH.toggle_raid_sticky(bot, ctx, int(ctx.channel_id), int(ctx.guild_id))
    except discord.DiscordException as error:
        print("[!] An error occurred [{}]".format(error))

async def request_delete_handle(ctx, bot):
    pass

def has_role(roles, role_name):
    for role in roles:
        if role_name == role.name:
            return True

    return False

async def raw_message_delete_handle(ctx, bot):
    if await RH.check_if_valid_raid_channel(bot, ctx.channel_id):
        await raid_delete_handle(ctx, bot)
        return

    #if await check_if_valid_request_channel(bot, ctx.channel_id):
    #    await request_delete_handle(ctx, bot)

async def on_message_handle(message, bot):
    if not await RH.check_if_valid_raid_channel(bot, message.channel.id):
        return False

    #if not await check_if_valid_request_channel(bot, message.channel.id):
    #    return False

    if message.author.id == bot.user.id:
        return False

    if has_role(message.author.roles, "Mods"):
        return False

    if not message.content.startswith(bot.command_prefix, 0, 1):
        content = message.content
        try:
            await message.author.send(H.guild_member_dm(message.guild.name, "Type -raid in that channel to get more info."))
        except discord.DiscordException:
            pass
        try:
            print("[*][{}][{}] Invalid message deleted [{}]".format(message.guild.name, message.author.name, content))
            await message.delete()
        except discord.NotFound:
            pass

        return True

    return False
