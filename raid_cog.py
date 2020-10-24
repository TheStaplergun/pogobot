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
  #async def recreate_raid_table(self, ctx):
  #  await drop_and_make(ctx)

  @commands.command()
  @commands.before_invoke(acquire_pool_connection)
  @commands.after_invoke(release_pool_connection)
  @commands.has_role("Mods")
  async def get_raids(self, ctx):
    await get_all_raids_in_db(ctx)

  #@commands.command()
  #@commands.before_invoke(acquire_pool_connection)
  #@commands.after_invoke(release_pool_connection)
  #@commands.has_role("Mods")
  #async def register(self,
  #                   ctx,
  #                   level = 0,
  #                   friend_code = "No code provided",
  #                   friend_code_middle = "",
  #                   friend_code_end = ""):

  #  is_registered, _ = await check_for_player(ctx, ctx.author.id)
  #  if not is_registered:
  #    await register_user(ctx,
  #                        level,
  #                        friend_code,
  #                        friend_code_middle,
  #                        friend_code_end)
  #    await ctx.author.send("Registration successful.")
  #  else:
  #    await ctx.author.send("You are already registered!")

  @commands.command()
  @commands.before_invoke(acquire_pool_connection)
  @commands.after_invoke(release_pool_connection)
  @commands.guild_only()
  async def post_raid(self,
                      ctx,
                      tier = "`No tier provided`",
                      pokemon_name = "`No Pokemon Name provided`",
                      gym_color = "`No gym color provided`",
                      weather = "`No weather condition provided`",
                      invite_slots = "`No invite slot count provided`",
                      time_to_start = "`No time to start provided`",
                      time_to_expire = "`No time to expire provided`"):

    if not self.bot.raids_enabled:
      return 
      
    if ctx.guild.id not in self.bot.guild_info_dictionary:
      return

    if ctx.channel.id not in self.bot.guild_info_dictionary[ctx.guild.id].get("allowed_raid_channels"):
      return
    try:
      await ctx.message.delete()
    except:
      pass
    if await check_if_in_raid(ctx, ctx.author.id):
      await ctx.author.send(wrap_bot_dm(ctx.guild.name, "You are already in a raid."))
      return
    
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
        channel_message_body = "Raid hosted by {}\n".format(ctx.author.mention)
        message = await ctx.send(channel_message_body, embed=response, delete_after = remove_after_seconds)
        no_emoji = self.bot.get_emoji(743179437054361720)
        await message.add_reaction(no_emoji)
        time_to_delete = datetime.now() + timedelta(seconds = remove_after_seconds)
        await add_raid_to_table(ctx, message.id, ctx.guild.id, message.channel.id, ctx.author.id, time_to_delete)
        message_to_dm = "Your raid has been successfully listed.\nIt will automatically be deleted at the time given in `Time to Expire`.\nPress the red X emoji to remove it at any time."
        await ctx.author.send(wrap_bot_dm(ctx.guild.name, message_to_dm))
        print("[*] [ {} ] [ {} ] Raid successfuly posted.".format(ctx.guild, ctx.author.id))

      else:
        response += "---------\n"
        response += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
        await ctx.author.send(response)
        correction_suggestion = ctx.prefix + "post_raid " + suggestion
        await ctx.author.send(correction_suggestion)
        print("[!] [ {} ] [ {} ] Raid failed to post due to invalid arguments.".format(ctx.guild, ctx.author.id))
