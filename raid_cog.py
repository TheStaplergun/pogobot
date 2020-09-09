import discord
import importlib
from discord.ext import commands
import pogo_raid_lib
from pogo_raid_lib import *
from bot_lib import update_raid_tracker

class RaidPost(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    importlib.reload(pogo_raid_lib)

  @commands.command()
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
        print("Raid successfully listed.\n")
        update_raid_tracker(message, remove_after_seconds)
      else:
        response += "---------\n"
        response += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
        await ctx.author.send(response)
        correction_suggestion = ctx.prefix + "post_raid " + suggestion
        await ctx.author.send(correction_suggestion)
        print("Raid failed to list. Sent user errors and suggestions.\n")
