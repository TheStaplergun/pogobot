import asyncio
from datetime import datetime, timedelta
import pytz
import traceback

import asyncpg
import discord

import handlers.friend_code_handler as FCH
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.raid_lobby_management as RLM
from handlers.raid_handler import increment_raid_counter

async def create_raid_host_role(guild):
    try:
        return await guild.create_role(name="Raid Host", reason="Setting up a lobby system role.")
    except discord.DiscordException:
        pass

async def create_lobby_roles_for_guild(guild):
    try:
        await guild.create_role(name="Lobby Member", reason="Setting up a lobby system role.")
    except discord.DiscordException:
        pass
    try:
        await guild.create_role(name="Raid Moderator", reason="Setting up a lobby system role.")
    except discord.DiscordException:
        pass
    await create_raid_host_role(guild)


GET_CATEGORY_BY_GUILD_ID = """
    SELECT * FROM raid_lobby_category WHERE (guild_id = $1) LIMIT 1;
"""
async def get_raid_lobby_category_by_guild_id(bot, guild_id):
    try:
        category_data = await bot.database.fetchrow(GET_CATEGORY_BY_GUILD_ID,
                                                    int(guild_id))
    except asyncpg.PostgresError as error:
        print("[!] Error retreiving raid lobby category data. [{}]".format(error))
        return

    if not category_data:
        print("[!] Error retreiving raid lobby category data. [{}]".format("No category found. Ignoring."))
        return

    return category_data


GET_LOBBY_BY_USER_ID = """
    SELECT * FROM raid_lobby_user_map WHERE (host_user_id = $1);
"""
async def get_lobby_data_by_user_id(bot, user_id):
    return await bot.database.fetchrow(GET_LOBBY_BY_USER_ID,
                                       int(user_id))

async def get_lobby_channel_for_user_by_id(bot, user_id):
    try:
        lobby_data = await bot.database.fetchrow(GET_LOBBY_BY_USER_ID,
                                                 int(user_id))
    except asyncpg.PostgresError as error:
        print("[!] Error retreiving raid lobby data. [{}]".format(error))
        return

    if not lobby_data:
        return

    lobby_channel_id = lobby_data.get("lobby_channel_id")
    lobby = bot.get_channel(int(lobby_channel_id))
    if not lobby:
        try:
            lobby = await bot.fetch_channel(int(lobby_channel_id))
        except discord.NotFound:
            await remove_lobby_by_lobby_id(bot, lobby_channel_id)
            return
        except discord.DiscordException as error:
            print(f"[!] Error fetching channel [{error}]")
            return

    return lobby

GET_LOBBY_BY_LOBBY_ID = """
    SELECT * FROM raid_lobby_user_map WHERE (lobby_channel_id = $1);
"""
async def get_lobby_channel_by_lobby_id(bot, channel_id):
    try:
        lobby_data = await bot.database.fetchrow(GET_LOBBY_BY_LOBBY_ID,
                                                 int(channel_id))
    except asyncpg.PostgresError as error:
        print("[!] Error retreiving raid lobby data. [{}]".format(error))
        return

    if not lobby_data:
        return False

    lobby_channel_id = lobby_data.get("lobby_channel_id")

    lobby = bot.get_channel(int(lobby_channel_id))
    if not lobby:
        return False
    lobby.lobby_data = lobby_data
    return lobby

GET_RELEVANT_LOBBY_BY_TIME_AND_USERS = """
    SELECT * FROM raid_lobby_user_map
    WHERE (user_count < user_limit)
    ORDER BY posted_at;
"""
async def get_latest_lobby_data_by_timestamp(bot):
    return await bot.database.fetch(GET_RELEVANT_LOBBY_BY_TIME_AND_USERS)

async def send_log_message(bot, message, lobby_channel, lobby_data, author=None, guild=None):
    is_system_log = True if author else False
    author = author if author else message.author
    guild = guild if guild else message.guild
    category_data = await get_raid_lobby_category_by_guild_id(bot, guild.id)
    log_channel_id = category_data.get("log_channel_id")
    log_channel = bot.get_channel(int(log_channel_id))
    if is_system_log:
        new_embed = discord.Embed(title="System Log", description=message)
        url = author.avatar.url if author.avatar and author.avatar.url else None
    else:
        new_embed = discord.Embed(title="Logged Message", url=message.jump_url, description=message.content)
        url = author.guild_avatar.url if author.guild_avatar and author.guild_avatar.url else author.avatar.url if author.avatar and author.avatar.url else None
    if url:
        new_embed.set_author(name=author.name, icon_url=url)
    else:
        new_embed.set_author(name=author.name)
    new_embed.set_footer(text=f"User ID: {author.id} | Time: {datetime.utcnow()} UTC")
    host_user_id = lobby_data.get("host_user_id")
    guild = lobby_channel.guild
    host_member = discord.utils.get(guild.members, id=host_user_id)
    await log_channel.send(f"Lobby: {lobby_channel.name}\nHost: {host_member.mention}", embed=new_embed)

NEW_LOBBY_INSERT = """
INSERT INTO raid_lobby_user_map (lobby_channel_id, host_user_id, raid_message_id, guild_id, posted_at, delete_at, user_count, user_limit, applied_users, notified_users)
VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
"""
async def add_lobby_to_table(bot, lobby_channel, host_user_id, raid_id, guild_id, delete_at, invite_slots, host):
    """Add a raid to the database with all the given data points."""
    cur_time = datetime.now()
    lobby = await bot.get_lobby(lobby_channel.id, user_limit=int(invite_slots), raid_id=int(raid_id), host=host, delete_time=delete_at)
    lobby.lobby_channel = lobby_channel
    bot.lobbies.update({lobby_channel.id:lobby})
    await bot.database.execute(NEW_LOBBY_INSERT,
                               int(lobby_channel.id),
                               int(host_user_id),
                               int(raid_id),
                               int(guild_id),
                               cur_time,
                               delete_at,
                               0,
                               int(invite_slots),
                               0,
                               0)

async def create_raid_lobby(ctx, bot, raid_message_id, raid_host_member, time_to_remove_lobby, invite_slots) -> discord.TextChannel:
    guild = ctx.guild
    raid_lobby_category_channel_data = await get_raid_lobby_category_by_guild_id(bot, guild.id)
    if not raid_lobby_category_channel_data:
        return False
    raid_lobby_category_channel_id = raid_lobby_category_channel_data.get("category_id")
    raid_lobby_category_channel = bot.get_channel(int(raid_lobby_category_channel_id))

    raid_moderator_role = discord.utils.get(guild.roles, name="Raid Moderator")
    lobby_member_role = discord.utils.get(guild.roles, name="Lobby Member")
    muted_role = discord.utils.get(guild.roles, name="Muted")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        raid_host_member: discord.PermissionOverwrite(read_messages=True,
                                                      #send_messages=True,
                                                      embed_links=True,
                                                      attach_files=True,
                                                      add_reactions=True),
        bot.user: discord.PermissionOverwrite(read_messages=True,
                                              send_messages=True,
                                              embed_links=True,
                                              manage_channels=True,
                                              manage_messages=True)
    }

    if raid_moderator_role:
        overwrites.update({raid_moderator_role: discord.PermissionOverwrite(read_messages=True)})

    if muted_role:
        overwrites.update({muted_role:discord.PermissionOverwrite(send_messages=False)})

    # count = await RH.get_raid_count(bot, ctx, False)
    # channel_name = "raid-lobby-{}".format(await RH.get_raid_count(bot, ctx, False))

    reason = "Spawning new raid lobby for [{}]".format(raid_host_member.name)
    try:
        new_raid_lobby = await raid_lobby_category_channel.create_text_channel("raid-lobby-{}".format(await RH.get_raid_count(bot, ctx, False)), reason=reason, overwrites=overwrites)
        #await increment_raid_counter(ctx, bot, ctx.guild.id)
    except discord.DiscordException as error:
        try:
            await ctx.send("Something went wrong when trying to create your raid lobby: [{}]".format(error), delete_after=15)
        except discord.DiscordException:
            pass
        print("[!] An error occurred creating a raid lobby. [{}]".format(error))
        return False
    except AttributeError as error:
        try:
            await ctx.send("Something went wrong when trying to create your raid lobby: [{}]".format(error), delete_after=15)
        except discord.DiscordException:
            pass
        print("[!] An error occurred creating a raid lobby. [{}]".format(error))
        return False

    new_embed = discord.Embed(title="Start of Lobby", description="Welcome to your raid lobby. As players apply they will check in and be added here.\n\nAs the host it is your job to ensure you either add everyone, or everyone adds you. Once you have everyone in your friends list, then it is up to you to invite the players who join this lobby into your raid in game.")

    friend_code, has_code = await FCH.get_friend_code(bot, raid_host_member.id, host=True)
    trainer_name, has_name = await FCH.get_trainer_name(bot, raid_host_member.id, host=True)
    header_message_body = f"{friend_code} <- **Host friend code. Add this.**\n{raid_host_member.mention}"
    header_message_body = f"{header_message_body}\n{trainer_name} **<- Trainer Name**\n"

    try:
        header_message_body = header_message_body + "Ping the role {} for managing all members of this lobby at once.".format(lobby_member_role.mention)
    except AttributeError as error:
        pass

    if has_code:
        new_embed.set_footer(text="You can copy this message directly into the game.")

    message = await new_raid_lobby.send(header_message_body, embed=new_embed)
    try:
        await message.pin()
    except discord.DiscordException:
        pass
    try:
        await add_lobby_to_table(bot, new_raid_lobby, raid_host_member.id, raid_message_id, ctx.guild.id, time_to_remove_lobby, invite_slots, raid_host_member)
    except asyncpg.PostgresError as error:
        print("[!] An error occurred adding a lobby to the database. [{}]".format(error))
        await new_raid_lobby.delete()
        return
    bot.five_minute_trigger.set()

    role = discord.utils.get(guild.roles, name="Raid Host")
    if not role:
        role = await create_raid_host_role(guild)

    await bot.add_role_ignore_error(raid_host_member, role, "Giving raid host the raid host role.")

    #await RLM.give_member_management_channel_view_permissions(bot, raid_lobby_category_channel_data, raid_host_member)

    bot.lobby_remove_trigger.set()

    return new_raid_lobby


UPDATE_TIME_TO_REMOVE_LOBBY = """
    UPDATE raid_lobby_user_map
    SET delete_at = $1
    WHERE (raid_message_id = $2);
"""
async def update_delete_time_with_given_time(bot, new_time, raid_id):
    return await bot.database.execute(UPDATE_TIME_TO_REMOVE_LOBBY,
                                       new_time,
                                       int(raid_id))

async def alter_deletion_time_for_raid_lobby(bot, lobby):
    lobby_data = await get_lobby_data_by_raid_id(bot, lobby.raid_id)
    if not lobby_data:
        return

    lobby_channel = bot.get_channel(int(lobby.lobby_id))
    if not lobby_channel:
        try:
            lobby = await bot.fetch_channel(int(lobby.lobby_id))
        except discord.DiscordException:
            pass
    if not lobby_channel:
        return

    users = lobby.user_count#lobby_data.get("user_count")
    # new_delete_time = current_time if users == 0 else current_time + timedelta(minutes=15)

    # await bot.database.execute(UPDATE_TIME_TO_REMOVE_LOBBY,
    #                            new_delete_time,
    #                            int(lobby_data.get("raid_message_id")))
    limit = lobby.user_limit#lobby_data.get("user_limit")
    try:
        if lobby and users > 0:
            if users < limit:
                new_embed = discord.Embed(title=f"{users}/{limit}", description="Use -extend to add time as needed.\n\nNo new members will be added to this lobby.\n\nIf there are not enough players to complete this raid, please don’t waste any time or passes attempting unless you are confident you can complete the raid with a smaller group.")
            else:
                new_embed = discord.Embed(title=f"{users}/{limit} FULL", description="Use -extend to add time as needed.\n\nThe lobby is now full.\n\nIf someone needs to be removed, you can use the command `-remove` and any of their name, their ID, their nickname, or just `-remove @user`.")
                #await RH.set_raid_status_full(lobby.raid_id)
            new_embed.set_footer(text="If you have any feedback or questions about this bot, reach out to TheStaplergun#6920")
            await lobby_channel.send(" ", embed=new_embed)
    except discord.DiscordException:
        pass

GET_NEXT_LOBBY_TO_REMOVE_QUERY = """
    SELECT * FROM raid_lobby_user_map
    ORDER BY delete_at
    LIMIT 1;
"""
#
async def get_next_lobby_to_remove(bot):
    return await bot.database.fetchrow(GET_NEXT_LOBBY_TO_REMOVE_QUERY)

UPDATE_APPLICATION_DATA_FOR_USER = """
    UPDATE raid_application_user_map
    SET raid_message_id = $1
    WHERE (user_id = $2);
"""
async def update_application_for_user(bot, member, raid_message_id):
    async with bot.database.connect() as c:
        await bot.database.execute(UPDATE_APPLICATION_DATA_FOR_USER,
                                int(raid_message_id),
                                int(member.id))
    try:
        new_embed = discord.Embed(title="System Notification", description="You have updated your application to the selected raid.")
        await member.send(" ", embed=new_embed)
    except discord.DiscordException:
        pass

REMOVE_APPLICATION_FOR_USER_BY_ID = """
    DELETE FROM raid_application_user_map WHERE (user_id = $1)
    RETURNING raid_message_id;
"""
REDUCE_APPLICANT_COUNT_BY_RAID_ID = """
    UPDATE raid_lobby_user_map
    SET applied_users = applied_users - 1
    WHERE (raid_message_id = $1);
"""
async def remove_application_for_user(bot, member, raid_id, lobby, should_notify=True):
    async with bot.database.connect() as c:
        await c.execute(REMOVE_APPLICATION_FOR_USER_BY_ID, member.id)
        await c.execute(REDUCE_APPLICANT_COUNT_BY_RAID_ID, raid_id)

    await lobby.remove_an_applicant(member.id)
    await lobby.update_raid_status()

    try:
        if should_notify:
            new_embed = discord.Embed(title="System Notification", description="You have withdrawn your application to the selected raid.")
            await member.send(" ", embed=new_embed)
    except discord.DiscordException:
        pass
    #await lobby.update_raid_status()
    bot.applicant_trigger.set()

REDUCE_USER_COUNT_BY_RAID_ID = """
    UPDATE raid_lobby_user_map
    SET user_count = user_count - 1
    WHERE (raid_message_id = $1);
"""
async def decrement_user_count_for_lobby(bot, raid_id, user_id, lobby_data=None):
    if lobby_data:
        lobby = bot.lobbies.get(lobby_data.get("lobby_channel_id"))
        await lobby.remove_a_user(user_id)
    await bot.database.execute(REDUCE_USER_COUNT_BY_RAID_ID, raid_id)
    bot.applicant_trigger.set()

async def user_remove_self_from_lobby(bot, ctx, member, lobby_data):
    lobby_member_role = discord.utils.get(ctx.guild.roles, name="Lobby Member")
    await bot.remove_role_ignore_error(member, lobby_member_role, "Removed from lobby.")
    await ctx.channel.set_permissions(member, read_messages=False)
    lobby = bot.lobbies.get(lobby_data.get("lobby_channel_id"))
    await remove_application_for_user(bot, member, lobby_data.get("raid_message_id"), lobby, should_notify=False)
    await decrement_user_count_for_lobby(bot, lobby_data.get("raid_message_id"), member.id, lobby_data=lobby_data)
    tasks = []
    embed = discord.Embed(title="System Notification", description=f"{member.name} has left the lobby.")
    tasks.append(bot.send_ignore_error(ctx.channel, " ", embed=embed))
    embed = discord.Embed(title="System Notification", description="You have left the lobby.")
    tasks.append(bot.send_ignore_error(member, " ", embed=embed))
    tasks.append(lobby.update_raid_status())
    await asyncio.gather(*tasks)

async def remove_lobby_member_by_command(bot, ctx, user, is_self=False):
    user_id = None
    member = user if is_self else None
    host_id = None
    channel = ctx.channel

    lobby_data = await get_lobby_data_by_lobby_id(bot, channel.id)
    lobby = bot.lobbies.get(channel.id)
    if not lobby_data:
        embed = discord.Embed(title="Error", description="This channel is not a valid lobby.")
        await bot.send_ignore_error(ctx, " ", embed=embed, delete_after=15)
        return

    if not is_self:
        if "@" in user:
            user = user.strip("<@!")
            user = user.strip(">")
        try:
            user_id = int(user)
            member = discord.utils.get(ctx.guild.members, id=user_id)
        except ValueError:
            pass
        except TypeError:
            pass
        if not member:
            member = discord.utils.get(ctx.guild.members, name=user)

        if not member:
            member = discord.utils.get(ctx.guild.members, nick=user)

        if not member:
            embed = discord.Embed(title="Error", description="I could not find a user with that ID or Name/Nickname in this server.")
            await bot.send_ignore_error(ctx, " ", embed=embed, delete_after=15)
            return

    host_id = lobby_data.get("host_user_id")

    if member == ctx.author and member.id == host_id:
        embed = discord.Embed(title="Error", description="You can't remove yourself from your own lobby. Close the lobby if you want to leave.")
        await bot.send_ignore_error(ctx, " ", embed=embed, delete_after=15)
        return

    if member not in channel.members:
        embed = discord.Embed(title="Error", description="That user is not a member of this lobby.")
        await bot.send_ignore_error(ctx, " ", embed=embed, delete_after=15)
        return

    if not discord.utils.get(member.roles, name="Lobby Member"):
        embed = discord.Embed(title="Error", description="That user is not a member of this lobby.")
        await bot.send_ignore_error(ctx, " ", embed=embed, delete_after=15)
        return

    if is_self:
        await user_remove_self_from_lobby(bot, ctx, member, lobby_data)
        return

    if host_id != ctx.author.id:
        if channel and not channel.permissions_for(ctx.author).manage_channels:
            embed = discord.Embed(title="", description="You do not have permission to manage this lobby.")
            await bot.send_ignore_error(ctx, "", embed=embed, delete_after=15)
            return
        # else:
        #     embed = discord.Embed(title="Error", description="You are not the host of this lobby.")
        #     await bot.send_ignore_error(ctx, " ", embed=embed, delete_after=15)



    lobby_member_role = discord.utils.get(ctx.guild.roles, name="Lobby Member")

    await bot.remove_role_ignore_error(member, lobby_member_role, "Removed from lobby.")
    await ctx.channel.set_permissions(member, read_messages=False)
    await remove_application_for_user(bot, member, lobby_data.get("raid_message_id"), lobby, should_notify=False)
    await decrement_user_count_for_lobby(bot, lobby_data.get("raid_message_id"), member.id, lobby_data=lobby_data)
    tasks = []
    embed = discord.Embed(title="System Notification", description=f"{member.name} was removed from the lobby.")
    tasks.append(bot.send_ignore_error(ctx.channel, " ", embed=embed))
    embed = discord.Embed(title="System Notification", description="You were removed from the lobby.")
    tasks.append(bot.send_ignore_error(member, " ", embed=embed))
    tasks.append(lobby.update_raid_status())
    await asyncio.gather(*tasks)
    #bot.applicant_trigger.set()

async def handle_manual_clear_application(ctx, user_id, bot):
    result = await bot.database.execute(REMOVE_APPLICATION_FOR_USER_BY_ID, int(user_id))
    try:
        await ctx.send(result)
    except discord.DiscordException:
        pass

INSERT_NEW_APPLICATION_DATA = """
    INSERT INTO raid_application_user_map (user_id, raid_message_id, guild_id, is_requesting, app_weight, has_been_notified, checked_in)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
"""
UPDATE_LOBBY_APPLICANT_DATA = """
    UPDATE raid_lobby_user_map
    SET applied_users = applied_users + 1
    WHERE (raid_message_id = $1);
"""
async def insert_new_application(bot, user_id, raid_message_id, guild_id, is_requesting, app_weight):
    try:
        await bot.database.execute(INSERT_NEW_APPLICATION_DATA,
                                   int(user_id),
                                   int(raid_message_id),
                                   int(guild_id),
                                   is_requesting,
                                   app_weight,
                                   False,
                                   False)
    except asyncpg.PostgresError as error:
        pass

async def calculate_speed_bonus(message, listing_duration):
    creation_time = message.created_at
    time_difference = (discord.utils.utcnow() - creation_time)
    return 100 - (time_difference.total_seconds() / listing_duration * 100) # Calculated by quickness of application over total life of raid listing.

async def handle_new_application(ctx, bot, member, message, lobby):
    raid_data = await RH.retrieve_raid_data_by_message_id(ctx, bot, message.id)
    if not raid_data:
        return False
    _, pokemon_name = H.get_pokemon_name_from_raid(message)
    host_id = raid_data.get("user_id")

    try:
        if host_id == member.id:
            new_embed = discord.Embed(title="Error", description="You cannot apply to your own raid!")
            await ctx.response.send_message(" ", embed=new_embed, ephemeral=True)
            #await member.send(" ", embed=new_embed)
            return False
        else:
            new_embed = discord.Embed(title="System Notification", description="You have applied for the selected raid.\nApplicants will be selected based on a weighted system.\n\n\nYou will know within 60 seconds if you are selected.\n\nIt is possible to be pulled into the lobby if someone is removed later on.")
            await ctx.response.send_message(" ", embed=new_embed, ephemeral=True)
            #await member.send(" ", embed=new_embed)
    except discord.Forbidden:
        # Prevents users from applying without ability to send a DM.
        new_embed = discord.Embed(title="Communication Error", description="{}, I cannot DM you. You will not be able to apply for raids until I can.".format(member.mention))
        await ctx.response.send_message(" ", embed=new_embed, ephemeral=True)
        #await channel.send(" ", embed=new_embed, delete_after=15)
        return False
    role = discord.utils.get(member.roles, name=pokemon_name)
    time_to_end = raid_data.get("time_to_remove")
    time_to_end = pytz.utc.localize(time_to_end)
    listing_duration = time_to_end - message.created_at
    speed_bonus = await calculate_speed_bonus(message, listing_duration.total_seconds())
    app_weight = await calculate_weight(bot, True if role else False, speed_bonus, member.id)
    await lobby.add_an_applicant(member.id)
    await lobby.update_raid_status()
    #await lobby.update_raid_status()
    await insert_new_application(bot, member.id, message.id, message.guild.id, (True if role else False), app_weight)
    bot.applicant_trigger.set()

QUERY_APPLICATION_DATA_FOR_USER = """
    SELECT * FROM raid_application_user_map WHERE (user_id = $1);
"""
async def get_applicant_data_for_user(bot, user_id):
    return await bot.database.fetchrow(QUERY_APPLICATION_DATA_FOR_USER, user_id)

async def handle_application_from_button(interaction, bot):
    await handle_application_to_raid(bot, interaction, interaction.message, interaction.channel)

async def handle_application_to_raid(bot, itx, message, channel):
    guild = message.guild
    member = guild.get_member(itx.user.id)
    # try:
    #     interacted_message = await itx.original_message()
    # except discord.DiscordException:
    #     pass
    result = await get_applicant_data_for_user(bot, itx.user.id)
    if discord.utils.get(member.roles, name="Muted"):
        embed = discord.Embed(title="Error", description="You are currently muted and your application has been dropped. Try again when you are no longer muted.")
        await itx.response.send_message(" ", embed=embed, ephemeral=True)
        #await bot.send_ignore_error(member, " ", embed=embed)
        return

    friend_code_set = await FCH.has_friend_code_set(bot, itx.user.id)
    if not friend_code_set:
        embed = discord.Embed(title="Error", description="You cannot join a raid without your friend code set. Use `-setfc 1234 5678 9012` to set your friend code.")
        await bot.send_ignore_error(itx.user, " ", embed=embed)
        return
    trainer_name_set = await FCH.has_trainer_name_set(bot, itx.user.id)
    if not trainer_name_set:
        embed = discord.Embed(title="Error", description="You cannot join a raid without your in game trainer name set. Use `-setname USERNAME` to set your trainer name.")
        await bot.send_ignore_error(itx.user, " ", embed=embed)
        return
    raid_message_id = message.id

    lobby_data = await get_lobby_data_by_raid_id(bot, raid_message_id)
    if not lobby_data:
        return
    lobby_id = lobby_data.get("lobby_channel_id")
    lobby = bot.lobbies.get(lobby_id)
    if itx.user.id in lobby.applicants:
        try:
            bot.interactions.pop(itx.user.id)
        except KeyError:
            pass
        await remove_application_for_user(bot, member, lobby.raid_id, lobby)
        return
    if result:
        applied_to_raid_id = result.get("raid_message_id")
        has_been_notified = result.get("has_been_notified")
        if has_been_notified:
            new_embed = discord.Embed(title="Error", description="You are already locked into a raid. Wait until that raid is complete, or leave that lobby with `-leave`.")
            await itx.response.send_message(" ", embed=new_embed, ephemeral=True)
            return
        #raid_message_id = message.id
        if applied_to_raid_id == raid_message_id:
            try:
                bot.interactions.pop(itx.user.id)
            except KeyError:
                pass
            await remove_application_for_user(bot, member, applied_to_raid_id, lobby)
            return
        # else:
        #     bot.interactions.update({itx.user.id:{
        #         "interaction":itx,
        #         "raid_id":raid_message_id}
        #     })
        #     await update_application_for_user(bot, member, raid_message_id)
    if not bot.interactions.get(itx.user.id):
        bot.interactions.update({itx.user.id:[{
            "interaction":itx,
            "raid_id":raid_message_id}]
        })
    else:
        bot.interactions[itx.user.id].append({
            "interaction":itx,
            "raid_id":raid_message_id}
        )
    await handle_new_application(itx, bot, member, message, lobby)

QUERY_APPLICANT_BY_MESSAGE_ID = """
    SELECT * FROM raid_application_user_map WHERE (activity_check_message_id = $1);
"""
async def get_applicant_data_by_message_id(bot, message_id):
    return await bot.database.fetchrow(QUERY_APPLICANT_BY_MESSAGE_ID, message_id)

GET_USERS_BY_RAID_MESSAGE_ID = """
    SELECT * FROM raid_application_user_map
    WHERE (raid_message_id = $1 and has_been_notified = FALSE)
    ORDER BY app_weight DESC;
"""
"""
    LIMIT $2;
"""
async def get_applicants_by_raid_id(bot, raid_message_id):#, user_limit):
    return await bot.database.fetch(GET_USERS_BY_RAID_MESSAGE_ID, int(raid_message_id))#, int(user_limit))

QUERY_RECENT_PARTICIPATION = """
    SELECT * FROM raid_participation_table WHERE (user_id = $1);
"""
GET_PERSISTENCE_BONUS = """
    SELECT * FROM trainer_data WHERE (user_id = $1);
"""
async def calculate_weight(bot, is_requesting, speed_bonus_weight, member_id):
    async with bot.database.connect() as c:
        result = await c.fetchrow(QUERY_RECENT_PARTICIPATION, int(member_id))
        persistence = await c.fetchrow(GET_PERSISTENCE_BONUS, int(member_id))

    recent_participation_weight = 100
    #is_requesting = user_data.get("is_requesting")
    #speed_bonus_weight = user_data.get("speed_bonus_weight")
    persistence_weight = persistence.get("persistence") if persistence else 0
    persistence_weight = persistence_weight+(5*persistence_weight**2)
    if result:
        last_participation_time = result.get("last_participation_time")
        current_time = datetime.now()
        time_difference = current_time - last_participation_time
        if time_difference.total_seconds() < 3600:
            recent_participation_weight = (time_difference.total_seconds()/3600) * 100
    return recent_participation_weight + (100 if is_requesting else 0) + speed_bonus_weight + persistence_weight

UPDATE_LOBBY_APPLICANT_DATA = """
    UPDATE raid_application_user_map
    SET has_been_notified = true
    WHERE (user_id = $1);
"""

async def set_notified_flag(bot, user_id):
    await bot.database.execute(UPDATE_LOBBY_APPLICANT_DATA, int(user_id))

INCREMENT_APPLICANT_COUNT = """
    UPDATE raid_lobby_user_map
    SET notified_users = notified_users + 1
    WHERE (lobby_channel_id = $1)
"""
async def increment_notified_users_for_raid_lobby(bot, lobby_id):
    await bot.database.execute(INCREMENT_APPLICANT_COUNT, int(lobby_id))

async def process_user_list(bot, raid_lobby_data, users, guild):
    if not guild and raid_lobby_data:
        guild = bot.get_guild(raid_lobby_data.get("guild_id"))
    if not guild:
        return

    counter = 1
    lobby = bot.lobbies.get(raid_lobby_data.get("lobby_channel_id"))
    current_count = lobby.user_count
    user_limit = lobby.user_limit
    #notified_count = raid_lobby_data.get("notified_users")

    current_needed = user_limit - current_count# - total_pending
    lobby_channel = await bot.retrieve_channel(raid_lobby_data.get("lobby_channel_id"))
    if not lobby_channel:
        return
    tasks = []
    async def notify_user_task(member, user):
        """This function is being used to create tasks to allow concurrent asynchronous processing."""
        user_interaction_data = bot.interactions.get(user.get("user_id"))

        if not user_interaction_data:
            return
        try:
            interaction = [itx for itx in user_interaction_data if itx["raid_id"] == lobby.raid_id].pop()
        except IndexError:
            interaction = None
        try:
            if interaction:
                new_embed = discord.Embed(title="Notification", description="You have been accepted into a lobby. Click the replied to message above to see which lobby.")
                message = await interaction["interaction"].followup.send(f"{member.mention}", embed=new_embed, ephemeral=True)
            else:
                # If no interaction available, or of it fails to send on the interaction, just Dm the user.
                new_embed = discord.Embed(title="Notification", description=f"An error occurred from discord, so I DMed you instead to let you know you were selected for a raid. You can find it here: [{lobby_channel.mention}]")
                message = await bot.send_ignore_error(member, " ", embed=new_embed)
        except discord.DiscordException as e:
            new_embed = discord.Embed(title="Notification", description=f"An error occurred from discord, so I DMed you instead to let you know you were selected for a raid. You can find it here: [{lobby_channel.mention}]")
            message = await bot.send_ignore_error(member, " ", embed=new_embed)
            print(f"[!] An exception occurred while attempting to send a followup message: [{e}]")
        finally:
            await set_notified_flag(bot, member.id)
            await process_and_add_user_to_lobby(bot, member, lobby_channel, guild, message, raid_lobby_data, lobby.raid_id)

    for user in users:
        if counter > current_needed:
            break
        if int(user.get("user_id")) in lobby.members:
            continue
        member = guild.get_member(int(user.get("user_id")))#user["member_object"]
        if not member:
            continue
        tasks.append(notify_user_task(member, user))
        counter+=1

    await asyncio.gather(*tasks)
    await check_if_lobby_full(bot, lobby_channel.id)

async def unlock_lobby_from_button(interaction, bot):
    lobby = bot.lobbies.get(interaction.channel.id)

    if interaction.user.id != lobby.host.id:
        return
    lobby.unlock()
    await lobby.update_raid_status()
    bot.applicant_trigger.set()
    await bot.delete_ignore_error(interaction.message)

async def lock_lobby_from_button(interaction, bot):
    lobby = bot.lobbies.get(interaction.channel.id)

    if interaction.user.id != lobby.host.id:
        return
    await RH.delete_raid(bot, lobby.raid_id)
    if not lobby:
        return
    lobby.raid_still_exists = False
    await bot.delete_ignore_error(interaction.message)

QUERY_LOBBY_BY_RAID_ID = """
    SELECT * FROM raid_lobby_user_map WHERE (raid_message_id = $1)
"""
async def get_lobby_data_by_raid_id(bot, raid_id):
    return await bot.database.fetchrow(QUERY_LOBBY_BY_RAID_ID, int(raid_id))

UPDATE_USER_COUNT_FOR_RAID_LOBBY = """
    UPDATE raid_lobby_user_map
    SET user_count = user_count + 1,
        notified_users = notified_users - 1
    WHERE (lobby_channel_id = $1);
"""
async def increment_user_count_for_raid_lobby(bot, lobby_id, user_id):
    await bot.database.execute(UPDATE_USER_COUNT_FOR_RAID_LOBBY, int(lobby_id))

    lobby = await bot.get_lobby(lobby_id)
    return await lobby.add_a_user(user_id)

UPDATE_CHECKED_IN_FLAG = """
    UPDATE raid_application_user_map
    SET checked_in = true
    WHERE (user_id = $1);
"""
RESET_PERSISTENCE_INCREMENT_PARTICPATED = """
    UPDATE trainer_data
    SET persistence = 0,
        raids_participated_in = raids_participated_in + 1
    WHERE (user_id = $1);
"""
async def set_checked_in_flag(bot, user_id):
    async with bot.database.connect() as c:
        await c.execute(UPDATE_CHECKED_IN_FLAG, int(user_id))
        await c.execute(RESET_PERSISTENCE_INCREMENT_PARTICPATED, int(user_id))

DELETE_RECENT_PARTICIPATION_RECORD = """
    DELETE FROM raid_participation_table WHERE (user_id = $1);
"""
UDPATE_RECENT_PARTICIPATION = """
    INSERT INTO raid_participation_table(user_id, last_participation_time)
    VALUES ($1, $2);
"""
async def set_recent_participation(bot, user_id):
    async with bot.database.connect() as c:
        await c.execute(DELETE_RECENT_PARTICIPATION_RECORD, int(user_id))
        await c.execute(UDPATE_RECENT_PARTICIPATION, int(user_id), datetime.now())

async def update_raid_removal_and_lobby_removal_times(bot, raid_id, time_to_remove=datetime.now(), lobby_id=0):
    lobby = bot.lobbies.get(lobby_id)
    if lobby:
        lobby.delete_time = time_to_remove
        lobby.five_minute_warning = False
    bot.five_minute_trigger.set()
    await update_delete_time_with_given_time(bot, time_to_remove, raid_id)
    await RH.update_delete_time(bot, time_to_remove, raid_id)
    bot.lobby_remove_trigger.set()

async def check_if_lobby_full(bot, lobby_id):
    #lobby_data = await bot.database.fetchrow(GET_LOBBY_BY_LOBBY_ID, int(lobby_id))
    lobby = bot.lobbies.get(lobby_id)
    #if lobby_data.get("user_count") == lobby_data.get("user_limit"):

    if lobby.is_full():
        lobby.lock()
        await alter_deletion_time_for_raid_lobby(bot, lobby)

DELETE_APPLICATIONS_THAT_ARE_NOT_RELEVANT_FOR_USER = """
    DELETE FROM raid_application_user_map
    WHERE (user_id = $1 and raid_message_id != $2);
"""
async def process_and_add_user_to_lobby(bot, member, lobby_channel, guild, message, lobby_data, raid_id):
    await bot.database.execute(DELETE_APPLICATIONS_THAT_ARE_NOT_RELEVANT_FOR_USER,
                               int(member.id),
                               int(raid_id))
    bot.interactions.update({member.id:[item for item in bot.interactions.get(member.id) if item["raid_id"] != raid_id]})
    role = discord.utils.get(guild.roles, name="Lobby Member")
    friend_code, has_code = await FCH.get_friend_code(bot, member.id)
    trainer_name, has_name = await FCH.get_trainer_name(bot, member.id)
    #users = lobby_data.get("user_count")
    limit = lobby_data.get("user_limit")
    count = await increment_user_count_for_raid_lobby(bot, lobby_data.get("lobby_channel_id"), member.id)
    lobby = bot.lobbies.get(lobby_channel.id)

    #if has_code:
    message_to_send = f"{friend_code} **<-Friend Code**\n{member.mention} **{count}/{limit}** joined."
    #if has_name:
    message_to_send = f"{message_to_send}\n{trainer_name} **<- Trainer name**"
    message_to_send = f"{message_to_send}\n**Copy this message directly into the game.**"

    message_to_send += "\nCheck the 📌pinned📌 message for host information.\n-----"
    if not lobby_channel:
        return
    try:
        await asyncio.gather(set_checked_in_flag(bot, member.id),
                             lobby_channel.set_permissions(member, read_messages=True,
                                                         #send_messages=True,
                                                         embed_links=True,
                                                         attach_files=True,
                                                         add_reactions=True),
                             set_recent_participation(bot, member.id),
                             bot.add_role_ignore_error(member, role, "Member of lobby"),
                             bot.send_ignore_error(lobby_channel, message_to_send),
                             bot.delete_ignore_error(message))
        await lobby.update_raid_status()
    except discord.DiscordException as e:
        print(f"[!]An exception occurred during the process of adding a user to a lobby. [{e}]")

async def handle_check_in_from_button(itx, bot):
    result = await bot.database.fetchrow(QUERY_APPLICATION_DATA_FOR_USER, itx.user.id)
    if not result:
        return

    activity_check_message_id = result.get("activity_check_message_id")
    if not itx.message.id == activity_check_message_id:
        return

    raid_message_id = result.get("raid_message_id")

    lobby_data = await get_lobby_data_by_raid_id(bot, raid_message_id)
    if not lobby_data:
        return
    lobby_id = lobby_data.get("lobby_channel_id")
    lobby_channel = bot.get_channel(int(lobby_id))
    lobby = bot.lobbies.get(lobby_id)
    guild = lobby_channel.guild
    #user_id = itx.user.id
    #member = guild.get_member(int(user_id))
    if discord.utils.get(itx.member.roles, name="Muted"):
        embed = discord.Embed(title="Error", description="You are currently muted and your application has been dropped. Try again when you are no longer muted.")
        await itx.response.send_message(" ", embed=embed, ephemeral=True)
        await remove_application_for_user(bot, itx.user, raid_message_id, lobby, should_notify=False)
        return
    await process_and_add_user_to_lobby(bot, itx.user, lobby_channel, guild, itx.message, lobby_data, lobby_data.get("raid_message_id"))

async def handle_activity_check_reaction(ctx, bot, message):
    result = await bot.database.fetchrow(QUERY_APPLICATION_DATA_FOR_USER, ctx.user_id)
    if not result:
        return

    activity_check_message_id = result.get("activity_check_message_id")
    if not message.id == activity_check_message_id:
        return

    raid_message_id = result.get("raid_message_id")

    lobby_data = await get_lobby_data_by_raid_id(bot, raid_message_id)
    if not lobby_data:
        return
    lobby_id = lobby_data.get("lobby_channel_id")
    lobby_channel = bot.get_channel(int(lobby_id))
    lobby = bot.lobbies.get(lobby_id)
    guild = lobby_channel.guild
    user_id = ctx.user_id
    member = guild.get_member(int(user_id))
    if discord.utils.get(member.roles, name="Muted"):
        embed = discord.Embed(title="Error", description="You are currently muted and your application has been dropped. Try again when you are no longer muted.")
        await bot.send_ignore_error(member, " ", embed=embed)
        await remove_application_for_user(bot, member, raid_message_id, lobby, should_notify=False)
        return
    await process_and_add_user_to_lobby(bot, member, lobby_channel, guild, message, lobby_data)

GET_LOBBY_BY_LOBBY_ID = """
    SELECT * FROM raid_lobby_user_map WHERE (lobby_channel_id = $1);
"""
async def get_lobby_data_by_lobby_id(bot, lobby_id):
    return await bot.database.fetchrow(GET_LOBBY_BY_LOBBY_ID, int(lobby_id))

PURGE_APPLICANTS_FOR_RAID = """
    DELETE FROM raid_application_user_map WHERE (raid_message_id = $1);
"""
async def remove_applicants_for_raid_by_raid_id(bot, raid_id):
    await bot.database.execute(PURGE_APPLICANTS_FOR_RAID, raid_id)

REMOVE_LOBBY_BY_ID = """
    DELETE FROM raid_lobby_user_map WHERE (lobby_channel_id = $1);
"""
async def remove_lobby_by_lobby_id(bot, lobby_data):
    if lobby_data:
        raid_id = lobby_data.get("raid_message_id")
        to_pop = []
        for id, data in bot.interactions.items():
            bot.interactions.update({id:[item for item in data if item["raid_id"] != raid_id]})
            if len(bot.interactions.get(id)) < 1:
                to_pop.append(id)

        for item in to_pop:
            bot.interactions.pop(item)
        #         counter+=1
        # bot.interactions = {k:v for k, v in bot.interactions.items() for itx in v if itx["raid_id"] != raid_id}
        await remove_applicants_for_raid_by_raid_id(bot, raid_id)

    await bot.database.execute(REMOVE_LOBBY_BY_ID, int(lobby_data.get("lobby_channel_id")))

SELECT_ALL_LOBBIES = """
    SELECT * FROM raid_lobby_user_map;
"""
async def get_all_lobbies(bot):
    return await bot.database.fetch(SELECT_ALL_LOBBIES)

SELECT_ALL_APPLICATIONS = """
    SELECT * FROM raid_application_user_map;
"""
async def get_all_applications(bot):
    return await bot.database.fetch(SELECT_ALL_APPLICATIONS)

REMOVE_LOG_CHANNEL_BY_ID = """
    DELETE FROM raid_lobby_category WHERE (log_channel_id = $1);
"""
async def check_if_log_channel_and_purge_data(bot, channel_id):
    await bot.database.execute(REMOVE_LOG_CHANNEL_BY_ID, int(channel_id))

SELECT_TRAINERS_IN_CURRENT_LOBBY = """
    SELECT * FROM raid_application_user_map
    WHERE (raid_message_id = $1 and checked_in = true)
"""
async def show_trainer_names(bot, ctx):
    lobby_data = await get_lobby_data_by_lobby_id(bot, ctx.channel.id)
    if not lobby_data:
        new_embed = discord.Embed(title="Error", description="This channel is not a lobby.")
        await bot.send_ignore_error(ctx.author, " ", embed=new_embed)

    raid_message_id = lobby_data.get('raid_message_id')
    results = await bot.database.fetch(SELECT_TRAINERS_IN_CURRENT_LOBBY,
                                       raid_message_id)
    print(results)
    names = []
    for result in results:
        name, has_name = await FCH.get_trainer_name(bot, result.get("user_id"))
        names.append(name)
    first_half = ",".join(list(names[:min(len(names), 5)]))
    second_half = None
    if len(names) > 5:
        second_half = ",".join(list(names[5:]))
    await bot.send_ignore_error(ctx.channel, first_half)
    if len(names) > 5:
        await bot.send_ignore_error(ctx.channel, second_half)
    embed = discord.Embed(title="Notification", description="The above {} can be used to search on your friends list for easier inviting.".format("two messages" if second_half else "message"))
    await bot.send_ignore_error(ctx.channel, " ", embed=embed)


DECREMENT_NOTIFIED_USERS = """
    UPDATE raid_lobby_user_map
    SET notified_users = notified_users - 1
    WHERE (raid_message_id = $1)
"""
# async def decrement_notified_users_by_raid_id(bot, raid_id):
#     await bot.database.execute(DECREMENT_NOTIFIED_USERS, int(raid_id))

# async def handle_user_failed_checkin(bot, applicant_data):
#     guild_id = applicant_data.get("guild_id")
#     guild = bot.get_guild(int(guild_id))
#     member = guild.get_member(applicant_data.get("user_id"))
#     if not member:
#         return False
#     raid_id = applicant_data.get("raid_message_id")
#     lobby_data = await get_lobby_data_by_raid_id(bot, raid_id)
#     lobby = await bot.retrieve_channel(lobby_data.get("lobby_channel_id"))
#     try:
#         bot.interactions.pop(applicant_data.get("user_id"))
#     except KeyError:
#         pass
#     embed = discord.Embed(title="System Notification", description="A user has failed to check in. Attempting to find a replacement...")
#     new_embed = discord.Embed(title="System Notification", description="You failed to check in and have been removed.")
#     await asyncio.gather(bot.send_ignore_error(lobby, " ", embed=embed),
#                          remove_application_for_user(bot, member, raid_id),
#                          decrement_notified_users_by_raid_id(bot, raid_id),
#                          bot.send_ignore_error(member, " ", embed=new_embed))

async def delete_lobby(bot, lobby, lobby_channel, lobby_data):
    members = lobby_channel.members
    guild = lobby_channel.guild
    lobby_member_role = discord.utils.get(guild.roles, name="Lobby Member")
    raid_host_role = discord.utils.get(guild.roles, name="Raid Host")
    new_embed = discord.Embed(title="System Notification", description="This lobby has been flagged for removal or has expired and is in the process of being shut down.")
    try:
        await lobby_channel.send(embed=new_embed)
    except discord.DiscordException:
        pass

    tasks = []
    if not lobby:
        return
    for member in members:
        if discord.utils.get(member.roles, name="Lobby Member") and member.id in lobby.members:
            tasks.append(bot.remove_role_ignore_error(member, lobby_member_role, "End of Raid"))
        if discord.utils.get(guild.roles, name="Raid Host") and member.id == lobby.host.id:
            tasks.append(bot.remove_role_ignore_error(member, raid_host_role, "End of Raid"))
    #await update_raid_removal_and_lobby_removal_times(bot, lobby_data.get("raid_message_id"))
    tasks.append(bot.delete_ignore_error(lobby_channel))
    tasks.append(RH.delete_raid(bot, lobby_data.get("raid_message_id")))
    await asyncio.gather(*tasks)
    bot.lobbies.pop(lobby_channel.id)

async def handle_admin_close_lobby(ctx, bot, lobby_id):
    if lobby_id == "":
        lobby_id = ctx.channel.id
    lobby_data = await get_lobby_data_by_lobby_id(bot, lobby_id)
    #lobby_channel = await bot.retrieve_channel(lobby_id)
    if lobby_data and lobby_id == ctx.channel.id:
        lobby_channel = ctx.channel
    else:
        lobby_channel = await bot.retrieve_channel(lobby_id)

    if lobby_channel and not lobby_channel.permissions_for(ctx.author).manage_channels:
        embed = discord.Embed(title="", description="You do not have permission to manage that lobby.")
        await bot.send_ignore_error(ctx, "", embed=embed, delete_after=15)
        return False

    if lobby_data and lobby_data.get("lobby_channel_id") != lobby_id:
        await bot.send_ignore_error(ctx, "The given channel id is not a valid lobby.", delete_after=15)
        return False

    if not lobby_channel:
        try:
            await ctx.send("The given channel id is not a valid lobby.")
        except discord.DiscordException:
            return

    try:
        embed = discord.Embed(title="", description="The lobby is being shut down.")
        message = await ctx.send(embed=embed)
    except discord.DiscordException:
        pass
    lobby = bot.lobbies.get(lobby_channel.id)
    await delete_lobby(bot, lobby, lobby_channel, lobby_data)
    if lobby_data and lobby_id != ctx.channel.id:
        try:
            embed = discord.Embed(title="", description="The requested lobby has been removed.")
            await message.edit(embed=embed)
        except discord.DiscordException:
            pass

SET_FROZEN_FLAG_QUERY = """
    UPDATE raid_lobby_user_map
    SET frozen = true
    WHERE (lobby_channel_id = $1)
"""
async def set_frozen_flag(bot, lobby_id):
    await bot.database.execute(SET_FROZEN_FLAG_QUERY, lobby_id)

async def handle_admin_freeze_lobby(ctx, bot, lobby_id):
    if lobby_id == "":
        lobby_id = ctx.channel.id
    lobby_data = await get_lobby_data_by_lobby_id(bot, lobby_id)
    #lobby_channel = await bot.retrieve_channel(lobby_id)
    if lobby_data and lobby_id == ctx.channel.id:
        lobby_channel = ctx.channel
    else:
        lobby_channel = await bot.retrieve_channel(lobby_id)
    lobby = bot.lobbies.get(lobby_channel.id)
    lobby.frozen = True

    if lobby_channel and not lobby_channel.permissions_for(ctx.author).manage_channels:
        embed = discord.Embed(title="", description="You do not have permission to manage that lobby.")
        await bot.send_ignore_error(ctx, "", embed=embed, delete_after=15)
        return False

    if lobby_data and lobby_data.get("lobby_channel_id") != lobby_id:
        await bot.send_ignore_error(ctx, "The given channel id is not a valid lobby.", delete_after=15)
        return False

    if not lobby_channel:
        try:
            await ctx.send("The given channel id is not a valid lobby.")
        except discord.DiscordException:
            return

    await set_frozen_flag(bot, lobby_id)
    try:
        embed = discord.Embed(title="Notification", description="This lobby has been frozen by an administrator.\n\nMembers may leave if they would like. The close and extend commands will no longer function. An administrator must close this lobby.")
        message = await ctx.send(embed=embed)
    except discord.DiscordException:
        pass
    #send_log_message(bot, message, lobby_channel, lobby_data)
