"""Request handler system."""
import discord
import handlers.helpers as H
from pogo_raid_lib import build_image_link_github, validate_pokemon

check_valid_request_channel = """
 SELECT * FROM valid_request_channels where (channel_id = $1)
"""

async def check_if_valid_request_channel(bot, channel_id):
    connection = await bot.acquire()
    results = await connection.fetchrow(check_valid_request_channel, int(channel_id))
    await bot.release(connection)
    if not results:
        return False
    return True

# FETCH_REQUEST_CHANNEL_INFO = """
#  SELECT * FROM valid_request_channels where (guild_id = $1)
# """
# async def get_request_channel(bot, guild_id):
#     connection = await bot.acquire()
#     results = await connection.fetchrow(FETCH_REQUEST_CHANNEL_INFO, guild_id)
#     if not results:
#         return False
#     return results.get("channel_id")

add_request_channel = """
INSERT INTO valid_request_channels (channel_id, guild_id)
VALUES ($1, $2);
"""
async def database_register_request_channel(bot, ctx, channel_id, guild_id):
    connection = await bot.pool.acquire()
    results = None
    try:
        results = await connection.execute(add_request_channel,
                                           int(channel_id),
                                           int(guild_id))
    except asyncpg.PostgresError as e:
        print("[!] Error occured registering request channel. [{}]".format(e))
    await bot.pool.release(connection)
    if results:
        print("[*] [{}] [{}] New request channel registered.".format(ctx.guild.name, channel_id))

how_to_request = """
To make a request, type the following:
`-request POKEMON_NAME`
If the pokemon is a mega pokemon, type:
`-request Mega POKEMON_NAME`
"""
def format_request_failed_dm(guild_name, wrapped_message):
    return H.guild_member_dm(guild_name, how_to_request + wrapped_message)

GET_REQUEST_POKEMON_MESSAGE = """
 SELECT * FROM request_role_id_map WHERE (role_name = $1 AND guild_id = $2);
"""
async def check_if_request_message_exists(bot, pokemon_name, guild_id):
    connection = await bot.acquire()
    result = await connection.execute(GET_REQUEST_POKEMON_MESSAGE, pokemon_name, int(guild_id))
    await bot.release(connection)
    if not result:
        return False, None, None
    return True, result.get("channel_id"), result.get("message_id"), result.get("role_id")

INSERT_NEW_ROLE = """
INSERT INTO request_role_id_map (role_id, message_id, guild_id, role_name)
VALUES ($1, $2, $3, $4);
"""
async def set_up_request_role_and_message(bot, ctx, pokemon_name, number):
    guild = ctx.guild
    try:
        new_role = await guild.create_role(name=pokemon_name, reason="Setting up a request role.")
    except discord.DiscordException as error:
        print("[!] An error occurred creating a new role: [{}]".format(error))
    author = ctx.author
    try:
        await author.add_roles([new_role])
    except discord.DiscordException as error:
        print("[!] An error occurred giving a user a role: [{}]".format(error))
        return
    new_embed = discord.embed(title=pokemon_name, description="")
    new_embed.set_url(url=build_image_link_github(number))
    new_embed.add_field(name="Number of players requesting", value=str(1))
    try:
        message = await ctx.channel.send(embed=new_embed)
    except discord.DiscordException as error:
        print("[!] An error occurred setting up the request sticky message. [{}]".format(error))
        await author.remove_roles([new_role])
        return

    connection = await bot.acquire()
    try:
        await connection.execute(INSERT_NEW_ROLE, new_role.id, message.id, guild.id, pokemon_name)
    except asyncpg.PostgresError as error:
        await message.delete()
        await author.remove_roles([new_role])
        print("[!] An error occurred inserting the new role data. [{}]".format(error))


async def give_request_role(author, role_id):
    role = [discord.Object(role_id)]
    try:
        await author.add_roles(role, reason="Giving user a request role.")
    except discord.DiscordException as error:
        print("[!] An error occurred giving a user a role: [{}]".format(error))
        return

async def increment_request_count(ctx, message_id):
    guild = ctx.guild
    channel = ctx.channel
    message = await channel.fetch_message(message_id)
    if len(message.embeds) == 1:
        embed = message.embeds[0]
        old_field = embed.fields[0]
        count = int(old_field.value)
    else:
        return
    
    count += 1
    new_embed = discord.embed(title=embed.title, description="")
    new_embed.set_url(url=old_field.thumbnail.url)
    new_embed.add_field(name=old_field.name, value=str(count))

    try:
        await message.edit(embed=new_embed)
    except discord.DiscordException as error:
        print("[!] An error occurred trying to update a request tracker. [{}]".format(error))

def get_pokemon_name_from_raid(message):
    embed = message.embeds[0]
    title = embed.title
    if title.startswith("Mega", 0, 4):
        return True, title.split(" ")[1]
    return False, embed.title

async def add_request_role_to_user_from_raid(bot, ctx, message):
    is_mega, pokemon_name = get_pokemon_name_from_raid(message)
    does_exist, channel_id, message_id, role_id = await check_if_request_message_exists(bot, pokemon_name, ctx.guild_id)
    tier = "Mega" if is_mega else ""
    _, _, _, dex_num = validate_pokemon(pokemon_name, tier)
    guild = bot.get_guild(ctx.guild_id)
    member = guild.get_member(ctx.user_id)
    if not does_exist:
        ctx.guild = guild
        ctx.author = member
        await set_up_request_role_and_message(bot, ctx, pokemon_name, dex_num)
    else:
        await give_request_role(member, role_id)
        ctx.channel = guild.get_channel(channel_id)
        await increment_request_count(ctx, message_id)

async def request_pokemon_handle(bot, ctx, tier, pokemon_name):
    """Sets up a request and gives you a role for that Pokemon"""
    author = ctx.author
    if not tier or (tier.lower() == "mega" and not pokemon_name):
        author.send(format_request_failed_dm(ctx.guild.Name, "No pokemon given to request."))
        return

    channel_id = ctx.channel.id
    try:
        await ctx.message.delete()
    except:
        pass
    if not check_if_valid_request_channel(bot, channel_id):
        author.send(H.guild_member_dm("That channel is not a valid request channel."))
        return
    if not pokemon_name:
        pokemon_name = tier
        tier = ""
    guild_id = ctx.guild.id
    is_valid, response, suggestion, dex_num = validate_pokemon(pokemon_name, tier)
    if not is_valid:
        author_dm = H.guild_member_dm(ctx.guild.name, "")
        author_dm += "---------\n"
        author_dm += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
        try:
            await author.send(author_dm)
        except discord.Forbidden:
            return
        correction_suggestion = ctx.prefix + "request " + suggestion
        await ctx.author.send(correction_suggestion)
    else:
        does_exist, _, message_id, role_id = await check_if_request_message_exists(bot, pokemon_name, guild_id)
        if not does_exist:
            await set_up_request_role_and_message(bot, ctx, pokemon_name, dex_num)
        else:
            await give_request_role(author, role_id)
            await increment_request_count(ctx, message_id)
    return
