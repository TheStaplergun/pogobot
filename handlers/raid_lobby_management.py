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
    if not lobby_data:
        return

    lobby_delete_time = lobby_data.get("delete_at")
    new_delete_time = lobby_delete_time + timedelta(minutes=5)
    total_duration = lobby_delete_time - lobby_data.get("posted_at")

    lobby = bot.get_channel(lobby_data.get("lobby_channel_id"))
    if not lobby:
        try:
            lobby = await bot.fetch_channel(lobby_data.get("lobby_channel_id"))
        except discord.DiscordException:
            return
    if total_duration.total_seconds() > 2700:
        await lobby.send("The lobby duration cannot be extended beyond 45 minutes.")
        return
    
    time_until_expiration_as_minutes = math.trunc((new_delete_time - datetime.now()).total_seconds()/60)
    new_embed = discord.Embed(title="System Notification", description=f"The host has extended the lobby duration by five minutes. It will now expire in {time_until_expiration_as_minutes}")
    RLH.update_delete_time_with_given_time(bot, new_delete_time, lobby_data.get("raid_message_id"))
    await lobby.send(embed=new_embed)

async def host_manual_remove_lobby(bot, ctx):
    lobby = await RLH.get_lobby_channel_for_user_by_id(bot, ctx.user_id)
    if not lobby:
        return

    await notify_lobby_members_of_host_deleting_lobby(lobby)
    await RLH.delete_lobby(lobby)

INSERT_MANAGEMENT_DATA = """
    UPDATE raid_lobby_category
    SET management_channel_id = $1,
        management_message_id = $2
    WHERE (guild_id = $3);
"""
async def insert_management_channel_data(bot, management_channel_id, management_message_id, guild_id):
    await bot.database.execute(INSERT_MANAGEMENT_DATA,
                               int(management_channel_id),
                               int(management_message_id),
                               int(guild_id))

async def create_dashboard_message(channel):
    new_embed = discord.Embed(title="Lobby Control Dashboard", description="Click one of the reactions below to control your lobby.")
    control_message = "\n".join([f"{x}:{y}" for x, y in controls.items()])
    new_embed.add_field(name="Options", value=control_message, inline=False)
    try:
        return await channel.send(embed=new_embed)
    except discord.DiscordException:
        return

controls = {
    "Add 5 Minutes":"⏱️",
    "Close Lobby":"❌"
}
async def set_up_management_channel(ctx, bot, should_create_channel):
    channel = ctx.channel
    category_id = channel.category_id
    lobby_category_data = await RLH.get_raid_lobby_category_by_guild_id(bot, ctx.guild.id)
    if should_create_channel and category_id == lobby_category_data.get("category_id"):
        channel = ctx.channel.category.create_text_channel(name="lobby-management")
    
    if not category_id:
        embed = discord.Embed(title="Error", description="This channel is not in a lobby category. A category is necessary to set up a raid lobby system. Create a category and place a channel in there, then run this command again.", color=0xff8c00)
        ctx.send(" ",embed=embed)
        return False

    dashboard_message = await create_dashboard_message(channel)
    if not dashboard_message:
        return

    await dashboard_message.add_reaction("⏱️")
    await dashboard_message.add_reaction("❌")

    await insert_management_channel_data(bot, channel.id, dashboard_message.id, ctx.guild.id)

