from datetime import timedelta

import discord

import handlers.raid_lobby_handler as RLH

async def notify_lobby_members_of_host_deleting_lobby(lobby):
    members = lobby.members
    guild = lobby.guild
    lobby_member_role = discord.utils.get(guild.roles, name="Lobby Member")
    for member in members:
        if lobby_member_role in member.roles:
            try:
                new_embed = discord.Embed(title="Notification", description="The host has manually closed the lobby.")
                await member.send(embed=new_embed)

async def extend_duration_of_lobby(bot, ctx):
    lobby_data = await RLH.get_lobby_data_by_user_id(bot, ctx.user_id)
    lobby_delete_time = lobby_data.get("delete_at")
    new_delete_time = lobby_delete_time + timedelta(minutes=5)
    total_duration = lobby_delete_time - lobby_data.get("posted_at")

    lobby = bot.get_channel(lobby_data.get("lobby_channel_id"))
    if not lobby:
        try:
            lobby = bot.fetch_channel(lobby_data.get("lobby_channel_id"))
        except discord.DiscordException:
            return
    if total_duration.total_seconds() > 2700:
        lobby.send("The lobby duration cannot be extended beyond 45 minutes.")
        return
    
    RLH.update_delete_time_with_given_time(bot, new_delete_time, lobby_data.get("raid_message_id"))


async def host_manual_remove_lobby(bot, ctx):
    lobby = await RLH.get_lobby_channel_for_user_by_id(bot, ctx.user_id)
    if not lobby:
        return

    await notify_lobby_members_of_host_deleting_lobby(lobby)
    try:
        await lobby.delete()
    except discord.DiscordException:
        pass


async def set_up_management_channel(ctx, bot):
    channel = ctx.channel
    if not channel.category_id:
        embed = discord.Embed(title="Error", description="This channel is not in a lobby category. A category is necessary to set up a raid lobby system. Create a category and place a channel in there, then run this command again.", color=0xff8c00)
        ctx.send(" ",embed=embed, delete_after=15)
        return False

    category_id = channel.category_id


async def user_lobby_management_reaction_handle(ctx, bot):
    pass

