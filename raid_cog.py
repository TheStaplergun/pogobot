import discord
import importlib
from discord.ext import commands
import pogo_bot_lib
from pogo_bot_lib import *

class RaidPost(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    importlib.reload(pogo_bot_lib)

  @commands.command()
  @commands.has_role("Mods")
  async def post_raid(self,
                      ctx,
                      tier = "No tier provided",
                      pokemon_name = "No Pokemon Name provided",
                      gym_color = "No gym color provided",
                      weather = "No weather condition provided",
                      invite_slots = "No invite slot count provided",
                      time_to_start = "No time to start provided",
                      time_to_expire = "No time to expire provided"):

    async with ctx.channel.typing():
      raid_is_valid, response = validate_and_format_message(ctx,
                                                            tier,
                                                            pokemon_name,
                                                            gym_color,
                                                            weather,
                                                            invite_slots,
                                                            time_to_start,
                                                            time_to_expire)
      if raid_is_valid:
        await ctx.send(embed=response)
      else:
        response += "---------\n"
        response += "*Here's the command you entered below. Make corrections and try again.*\n"
        await ctx.author.send(response)
        await ctx.author.send(ctx.message.content)
