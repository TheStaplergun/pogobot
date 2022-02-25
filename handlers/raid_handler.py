"""Raid SQL statements and database interaction functions"""
from datetime import datetime, timedelta

import asyncpg
import discord

import handlers.helpers as H
#import handlers.raid_lobby_handler as RLH
import handlers.request_handler as REQH
import handlers.sticky_handler as SH
from pogo_raid_lib import validate_and_format_message

NEW_RAID_INSERT = """
INSERT INTO raids(message_id, time_registered, guild_id, channel_id, user_id, time_to_remove)
VALUES($1, $2, $3, $4, $5, $6)
"""
async def add_raid_to_table(ctx, bot, message_id, guild_id, channel_id, user_id, time_to_remove):
    """Add a raid to the database with all the given data points."""
    cur_time = datetime.now()

    await bot.database.execute(NEW_RAID_INSERT,
                                 int(message_id),
                                 cur_time,
                                 int(guild_id),
                                 int(channel_id),
                                 int(user_id),
                                 time_to_remove)


INCREMENT_RAID_UPDATE_STATEMENT = """
UPDATE guild_raid_counters
SET raid_counter = $2
WHERE (guild_id = $1);
"""
async def increment_raid_counter(ctx, bot, guild_id):
    """Increments raid counter for a server for statistics tracking."""
    bot.guild_raid_counters[guild_id] += 1
    await bot.database.execute(INCREMENT_RAID_UPDATE_STATEMENT, guild_id, bot.guild_raid_counters[guild_id])

GET_RAID_COUNT_STATEMENT = """
    SELECT * FROM guild_raid_counters WHERE (guild_id = $1) LIMIT 1;
"""
async def get_raid_count(bot, ctx, should_print):
    """Get raid count for server the command was called in."""
    num = bot.guild_raid_counters.get(ctx.guild.id)
    # try:
    #     count = await bot.database.fetchrow(GET_RAID_COUNT_STATEMENT,
    #                                         int(ctx.guild.id))
    # except asyncpg.Exception as error:
    #     print("[!] Error obtaining raid count for guild. [{}]".format(error))
    #     return

    #num = count.get("raid_counter")
    if should_print:
        msg = "Total raids sent within this server [`{}`]".format(num)
        try:
            await ctx.channel.send(msg)
        except discord.DiscordException as error:
            print("[!] Error sending raid count to channel. [{}]".format(error))
    else:
        await increment_raid_counter(ctx, bot, ctx.guild.id)
        return num

GET_RAIDS_FOR_GUILD = """
    SELECT * FROM raids WHERE (guild_id = $1);
"""
async def get_all_raids_for_guild(bot, ctx):
    """Admin command. Gets all raids for a guild and all pertaining data."""

    results = await bot.database.fetch(GET_RAIDS_FOR_GUILD, ctx.guild.id)

    if not results:
        message = "No raids currently running."
        return
    message = "RAIDS\n"
    for _, item in enumerate(results):
        message += "-----------------\n"
        for column, value in item.items():
            message += str(column) + ": " + str(value) + "\n"
    message += "-----------------\nEND"
    await ctx.channel.send(message)

GET_RAID_FOR_USER = """
 SELECT * FROM raids where (user_id = $1);
"""
async def check_if_in_raid(ctx, bot, user_id):
    """Checks if a user is already in a raid. Prevents double listing."""
    return await bot.database.fetchrow(GET_RAID_FOR_USER, int(user_id))

CHECK_IF_MESSAGE_IS_RAID = """
  SELECT * FROM raids WHERE (message_id = $1)
"""
async def message_is_raid(ctx, bot, message_id):
    result = await bot.database.fetchrow(CHECK_IF_MESSAGE_IS_RAID, int(message_id))
    if result:
        return True
    return False

# Redundant but different return type. Can probably be added to above but do not feel like reworking at the moment.
async def retrieve_raid_data_by_message_id(ctx, bot, message_id):

    result = await bot.database.fetchrow(CHECK_IF_MESSAGE_IS_RAID, int(message_id))

    return result

RAID_TABLE_REMOVE_RAID = """
DELETE FROM raids WHERE (message_id = $1)
RETURNING message_id
"""
UPDATE_PERSISTENCE_BONUS_BY_RAID_ID = """
    UPDATE trainer_data td
    SET persistence = persistence + 1
    FROM raid_application_user_map raum
    WHERE
    (raum.raid_message_id = $1 and raum.has_been_notified = FALSE and td.user_id = raum.user_id);
"""
CLEAR_APPLICANTS_FOR_RAID = """
DELETE FROM raid_application_user_map WHERE (raid_message_id = $1)
"""
async def remove_raid_from_table(bot, message_id):
    """Removes a raid from the table."""
    async with bot.database.connect() as c:
        await c.execute(RAID_TABLE_REMOVE_RAID, int(message_id))
        await c.execute(UPDATE_PERSISTENCE_BONUS_BY_RAID_ID, int(message_id))
        await c.execute(CLEAR_APPLICANTS_FOR_RAID, int(message_id))

async def delete_raid(bot, raid_id):
    raid_data = await retrieve_raid_data_by_message_id(None, bot, raid_id)
    if not raid_data:
        return
    try:
        await bot.http.delete_message(raid_data.get("channel_id"), raid_data.get("message_id"))
    except discord.DiscordException:
        return

REMOVE_RAID_BY_ID = """
    DELETE FROM raids WHERE (message_id = $1);
"""
async def remove_raid_by_raid_id(bot, raid_data):
    await bot.database.execute(REMOVE_RAID_BY_ID, int(raid_data.get("message_id")))

async def remove_raid_from_button(interaction, bot):
    message_id = interaction.message.id
    results = await check_if_in_raid(interaction, bot, interaction.user.id)
    if results and results.get("message_id") == message_id:
        message_to_send = "Your raid has been successfuly deleted."
        try:
            await interaction.message.delete()
        except discord.DiscordException:
            pass
    else:
        message_to_send = "You are not the host. You cannot delete this raid!"
        await interaction.response.send_message("You are not the host. You cannot delete this raid!", ephemeral=True)
    #await interaction.user.send(H.guild_member_dm(bot.get_guild(interaction.guild_id).name, message_to_send))


GET_NEXT_RAID_TO_REMOVE_QUERY = """
    SELECT * FROM raids
    ORDER BY time_to_remove
    LIMIT 1;
"""
async def get_next_raid_to_remove(bot):
    return await bot.database.fetchrow(GET_NEXT_RAID_TO_REMOVE_QUERY)

UPDATE_TIME_TO_REMOVE_RAID = """
    UPDATE raids
    SET time_to_remove = $1
    WHERE (message_id = $2);
"""
async def update_delete_time(bot, new_time, raid_id):
    return await bot.database.execute(UPDATE_TIME_TO_REMOVE_RAID,
                                       new_time,
                                       int(raid_id))

async def handle_clear_user_from_raid(ctx, bot, user_id):
    guild = ctx.guild
    member = guild.get_member(user_id)
    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except discord.DiscordException as error:
            pass
    if not member:
        await ctx.send("That user doesn't exist on this server.", delete_after=5)
        return
    results = await check_if_in_raid(ctx, bot, user_id)
    if not results:
        await ctx.send("That user is not in a raid.", delete_after=5)
        return
    message_id = results.get("message_id")
    channel_id = results.get("channel_id")
    guild_id = results.get("guild_id")
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    try:
        message = await channel.fetch_message(message_id)
        await message.delete()
    except discord.NotFound:

        await remove_raid_from_table(bot, message_id)

    except discord.DiscordException as error:
        print("[!] An error occurred trying to remove a user from their raid manually. [{}]".format(error))
        return
    await ctx.send("User was successfully removed from raid.", delete_after=5)

CHECK_VALID_RAID_CHANNEL = """
 SELECT * FROM valid_raid_channels where (channel_id = $1)
"""
async def check_if_valid_raid_channel(bot, channel_id):
    """Checks if the channel is registered as a valid raid channel."""
    channel_id = int(channel_id)
    if channel_id in bot.raid_channel_cache:
        return True

    results = await bot.database.fetchrow(CHECK_VALID_RAID_CHANNEL, channel_id)

    if results:
        bot.raid_channel_cache.add(channel_id)

    if not results:
        return False
    return True

VERIFIED_ONLY_RAIDS = [
    "Mega Steelix",
    "Deoxys-Defense",
    "Lugia"
]
async def process_raid(ctx, bot, tier, pokemon_name, weather, invite_slots):
    from handlers.raid_lobby_handler import create_raid_lobby, get_lobby_data_by_user_id, get_raid_lobby_category_by_guild_id
    from handlers.friend_code_handler import has_friend_code_set

    try:
        await ctx.message.delete()
    except:
        pass
    if not await check_if_valid_raid_channel(bot, ctx.channel.id):
        return

    if await check_if_in_raid(ctx, bot, ctx.author.id):
        await ctx.author.send(H.guild_member_dm(ctx.guild.name, "You are already in a raid."))
        return
    if await get_lobby_data_by_user_id(bot, ctx.author.id):
        await ctx.author.send(H.guild_member_dm(ctx.guild.name, "You currently have a lobby open. Please close your old lobby and retry."))
        return
    is_verified = discord.utils.get(ctx.author.roles, name="Verified Raid Host")
    try:
        invite_slots = int(invite_slots)
        if not is_verified and invite_slots > 5:
            embed = discord.Embed(title="Error", description="To host a raid with more than 5 users, you must be verified by the moderators of this server and given the `Verified Raid Host` role to show you understand how to host a large party raid.")
            await bot.send_ignore_error(ctx.author, "", embed=embed)
            return
    except ValueError:
        pass

    async with ctx.channel.typing():
        raid_is_valid, response, suggestion = validate_and_format_message(ctx,
                                                                          tier,
                                                                          pokemon_name,
                                                                          weather,
                                                                          invite_slots)
        if raid_is_valid:
            if not is_verified or not invite_slots > 5:
                if response.title in VERIFIED_ONLY_RAIDS and not invite_slots > 5:
                    embed = discord.Embed(title="Error", description="This raid has proven to be excessively difficult, and has been deemed as only being allowed to be hosted by `Verified Raid Hosts` with 6 or more slots. To get this role, you must be verified by the moderators of this server and given the 'Verified Raid Host' role, and host the raid with more than 5 slots.")
                    await bot.send_ignore_error(ctx.author, "", embed=embed)
                    return
            temp = response.title
            temp = temp.replace("-Altered", "")
            temp = temp.replace("-Origin","")
            temp = temp.replace("-", " ")
            if temp not in bot.dex.current_raid_bosses():
                embed = discord.Embed(title="Error", description=f"That pokemon ({temp}) is not currently in rotation. If you believe this is an error, please contact TheStaplergun#6920.")
                await bot.send_ignore_error(ctx.author, " ", embed=embed)
                return
            if not await has_friend_code_set(bot, ctx.author.id):
                embed = discord.Embed(title="Error", description="You cannot host a raid without your friend code set. Use `-setfc 1234 5678 9012` to set your code.")
                await bot.send_ignore_error(ctx.author, " ", embed=embed)
                return
            remove_after_seconds = 900
            #channel_message_body = f'Raid hosted by {ctx.author.mention}\n'
            _, _, _, role_id = await REQH.check_if_request_message_exists(bot, response.title, ctx.guild.id)

            raid_lobby_category = await get_raid_lobby_category_by_guild_id(bot, ctx.guild.id)
            start_string = ""
            if role_id:
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                start_string = f'{role.mention}'
            end_string = ""

            channel_message_body = start_string + end_string
            try:
                response.add_field(name="Status", value="Gathering Applications", inline=False)
                message = await ctx.send(channel_message_body, embed=response, view=bot.raid_view(bot))
            except discord.DiscordException as error:
                print(f'[*][{ctx.guild.name}][{ctx.author}] An error occurred listing a raid. [{error}]')
                return
            time_to_delete = datetime.now() + timedelta(seconds=remove_after_seconds)
            await add_raid_to_table(ctx, bot, message.id, ctx.guild.id, message.channel.id, ctx.author.id, time_to_delete)

            lobby = None
            if raid_lobby_category:
                time_to_remove_lobby = time_to_delete + timedelta(seconds=300)
                lobby = await create_raid_lobby(ctx, bot, message.id, ctx.author, time_to_remove_lobby, int(invite_slots))

            if lobby:
                edited_message_content = f"{message.content}\n{lobby.mention} **<-lobby**"
                await message.edit(content=edited_message_content)
            print(f'[*][{ctx.guild}][{ctx.author.name}] Raid successfuly posted.')

            # try:
            #     await SH.toggle_raid_sticky(bot, ctx, int(ctx.channel.id), int(ctx.guild.id))
            # except discord.DiscordException as error:
            #     print(f'[!] Exception occurred during toggle of raid sticky. [{error}]')

            bot.raid_remove_trigger.set()
        else:
            response += "---------\n"
            response += "**Here's the command you entered below. Suggestions were added. Check that it is correct and try again.**\n"
            await ctx.author.send(response)
            correction_suggestion = ctx.prefix + "raid " + suggestion
            await ctx.author.send(correction_suggestion)
            print(f'[!][{ctx.guild}][{ctx.author.name}] Raid failed to post due to invalid arguments.')
