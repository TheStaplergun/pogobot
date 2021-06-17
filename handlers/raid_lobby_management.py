from datetime import datetime, timedelta
import math

import discord

import handlers.raid_lobby_handler as RLH

async def notify_lobby_members_of_host_deleting_lobby(lobby):
    members = lobby.members
    guild = lobby.guild
    lobby_member_role = discord.utils.get(guild.roles, name="Lobby Member")
    if not lobby_member_role:
        RLH.recreate_lobby_member_role(guild.roles)
        return

    new_embed = discord.Embed(title="Notification", description="The host has manually closed the lobby.")
    for member in members:
        if lobby_member_role in member.roles:
            try:
                await member.send(embed=new_embed)
            except discord.DiscordException:
                pass

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
    
    time_until_expiration_as_minutes = math.trunc((new_delete_time - datetime.now()).total_seconds()/60)
    new_embed = discord.Embed(title="System Notification", description=f"The host has extended the lobby duration by five minutes. It will now expire in {time_until_expiration_as_minutes}")
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
    category_id = channel.category_id
    if not category_id:
        embed = discord.Embed(title="Error", description="This channel is not in a lobby category. A category is necessary to set up a raid lobby system. Create a category and place a channel in there, then run this command again.", color=0xff8c00)
        ctx.send(" ",embed=embed)
        return False

    new_embed = discord.Embed(title="")