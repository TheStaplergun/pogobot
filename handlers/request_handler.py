"""Request handler system."""
import discord
import handlers.helpers as H
from pogo_raid_lib import validate_pokemon

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
    except Exception as e:
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
        does_exist, guild_id, message_id, role_id = check_if_request_message_exists(pokemon_name, guild_id)
        if not does_exist:
            set_up_request_role_and_message(pokemon_name)
        else:
            give_request_role(author, role_id)
            increment_request_count(message_id, guild_id)
    return
