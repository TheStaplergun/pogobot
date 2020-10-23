import discord
import importlib
from discord.ext import commands
import pogo_raid_lib
from datetime import datetime, timedelta
from pogo_raid_lib import *
from bot_lib import *

class RaidPost(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    importlib.reload(pogo_raid_lib)

  async def acquire_pool_connection(self, ctx):
    connection = await self.bot.pool.acquire()
    ctx.connection = connection

  async def release_pool_connection(self, ctx):
    if ctx.connection:
      await self.bot.pool.release(ctx.connection)

  #@commands.command()
  #@commands.before_invoke(acquire_pool_connection)
  #@commands.after_invoke(release_pool_connection)
  #@commands.has_role("Mods")
  #async def recreate_main_raid_table(self, ctx):
  #  await recreate_raid_table(ctx)

  @commands.command()
  @commands.before_invoke(acquire_pool_connection)
  @commands.after_invoke(release_pool_connection)
  @commands.has_role("Mods")
  async def get_raids(self, ctx):
    await get_all_raids_in_db(ctx)

  #@commands.command()
  @commands.before_invoke(acquire_pool_connection)
  @commands.after_invoke(release_pool_connection)
  @commands.has_role("Mods")
  async def register(self,
                     ctx,
                     level = 0,
                     friend_code = "No code provided",
                     friend_code_middle = "",
                     friend_code_end = ""):

    is_registered, _ = await check_for_player(ctx, ctx.author.id)
    if not is_registered:
      await register_user(ctx,
                          level,
                          friend_code,
                          friend_code_middle,
                          friend_code_end)
      await ctx.author.send("Registration successful.")
    else:
      await ctx.author.send("You are already registered!")

  @commands.command()
  @commands.before_invoke(acquire_pool_connection)
  @commands.after_invoke(release_pool_connection)
  @commands.guild_only()
  @commands.has_role("Mods")
  async def post_raid(self,
                      ctx,
                      tier = "`No tier provided`",
                      pokemon_name = "`No Pokemon Name provided`",
                      gym_color = "`No gym color provided`",
                      weather = "`No weather condition provided`",
                      invite_slots = "`No invite slot count provided`",
                      time_to_start = "`No time to start provided`",
                      time_to_expire = "`No time to expire provided`"):

    if ctx.guild.id not in self.bot.guild_info_dictionary:
      return

    if ctx.channel.id not in self.bot.guild_info_dictionary[ctx.guild.id].get("allowed_raid_channels"):
      return

    print(ctx.guild)
    await ctx.message.delete()
    async with ctx.channel.typing():
      raid_is_valid, response, remove_after, suggestion = validate_and_format_message(ctx,
                                                                                      tier,
                                                                                      pokemon_name,
                                                                                      gym_color,
                                                                                      weather,
                                                                                      invite_slots,
                                                                                      time_to_start,
                                                                                      time_to_expire)
      if raid_is_valid:
        remove_after_seconds = int(remove_after) * 60
        message = await ctx.send(embed=response, delete_after = remove_after_seconds)
        no_emoji = self.bot.get_emoji(743179437054361720)
        await message.add_reaction(no_emoji)
        print("Raid successfully listed.\n")
        time_to_delete = datetime.now() + timedelta(seconds = remove_after_seconds)
        await add_raid_to_table(ctx, message.id, ctx.guild.id, message.channel.id, time_to_delete)
      else:
        response += "---------\n"
        response += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
        await ctx.author.send(response)
        correction_suggestion = ctx.prefix + "post_raid " + suggestion
        await ctx.author.send(correction_suggestion)
        print("Raid failed to list. Sent user errors and suggestions.\n")
