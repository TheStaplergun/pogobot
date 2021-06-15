import re
from datetime import datetime

import discord

NEW_FC_INSERT = """
INSERT INTO friend_codes(user_id, friend_code, last_time_recalled)
VALUES($1, $2, $3)
"""
async def add_friend_code_to_table(bot, user_id, friend_code):
    """Add a raid to the database with all the given data points."""
    connection = await bot.acquire()
    await connection.execute(NEW_FC_INSERT,
                             int(user_id),
                             str(friend_code),
                             datetime.now())
    await bot.release(connection)

GET_FC_BY_USER_ID = """
SELECT * FROM friend_codes WHERE (user_id = $1);
"""
UPDATE_LAST_RECALLED_TIME = """
    UPDATE friend_codes
    SET last_time_recalled = $1
    WHERE (user_id = $2);
"""
async def get_friend_code(bot, user_id):
    connection = await bot.acquire()
    result = await connection.fetchrow(GET_FC_BY_USER_ID,
                                       int(user_id))
    if result:
        await connection.execute(UPDATE_LAST_RECALLED_TIME,
                                 datetime.now(),
                                 int(user_id))
    await bot.release(connection)
    return result.get("friend_code") if result else "Friend Code not found for member. To set your friend code, type '-fcreg <friend code>' in any lobby or appropriate channel."

async def send_friend_code(ctx, bot):
    friend_code = await get_friend_code(bot, ctx.author.id)
    message_to_send = f"{friend_code}\n{ctx.author.mention}"
    if len(friend_code) == 12:
        message_to_send = f"{message_to_send}*Note: This message can be directly copied and pasted into your add friend code box in game*"

    try:
        await ctx.send(message_to_send)
    except discord.DiscordException:
        pass

def validate_fc(args):
    joined_args = "".join(args)
    if not len(joined_args) == 12:
        return

    valid_format = re.compile(r'((\d){4} ?){3}')
    valid = re.match(valid_format, joined_args)

    if valid:
        return joined_args

async def set_friend_code(ctx, bot):
    author = ctx.author
    fc = validate_fc(ctx.args)
    if fc:
        new_embed = discord.Embed(title="System Notification", description="Your friend code has been registered. Recall it at any time with -fc.")
        await add_friend_code_to_table(bot, author.user_id, fc)
    else:
        new_embed = discord.Embed(title="Error", description="Invalid friend code. Valid friend code format is 1234 5678 9012 with or without spaces.")
    
    await ctx.send("", embed=new_embed, delete_after=15)
