"""Cog containing administrative commands"""
#import discord
from discord.ext import commands

from ..handlers import raid_handler as RH
from ..handlers import request_handler as REQH

class AdminCommands(commands.Cog):
    """Admin Commands Cog"""
    def __init__(self, bot):
        self.__bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def clear_raid(self, ctx, user_id):
        """Mod Only - Removes a given user from their raid. Deletes database entry."""
        await RH.handle_clear_user_from_raid(ctx, self.__bot, user_id)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    async def clear_requests(self, ctx):
        """Mod Only - Clears all requests for this guild."""
        await REQH.handle_clear_all_requests_for_guild(ctx, self.__bot)

def setup(bot):
    """Default setup function for file"""
    bot.add_cog(AdminCommands(bot))
