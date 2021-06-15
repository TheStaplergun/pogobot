"""Cog containing member commands"""
import discord
from discord.ext import commands

import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handlers as REQH

class MemberCommands(commands.Cog):
    """Members Commands Cog"""
    def __init__(self, bot):
        self.__bot = bot

    @commands.command()
    @commands.guild_only()
    async def request(self, ctx, tier=None, pokemon_name=None):
        """Processes a users pokemon request"""
        if not await REQH.check_if_valid_request_channel(self.__bot, ctx.channel.id):
            await ctx.author.send(H.guild_member_dm("That channel is not a valid request channel."))
            return
        await REQH.request_pokemon_handle(self.__bot, ctx, tier, pokemon_name)

    @commands.command()
    @commands.guild_only()
    async def raid_count(self, ctx):
        """Show total raids hosted in this server"""
        try:
            await ctx.message.delete()
        except discord.NotFound as error:
            print(f'[!] Message already gone. [{error}]')
        await RH.get_raid_count(self.__bot, ctx, True)


def setup(bot):
    """Default setup function for file"""
    bot.add_cog(MemberCommands(bot))