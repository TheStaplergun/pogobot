"""Cog containing member commands"""
import asyncio

import discord
from discord.ext import commands

import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handler as REQH
import handlers.raid_lobby_handler as RLH

class MemberCommands(commands.Cog):
    """Members Commands Cog"""
    def __init__(self, bot):
        self.__bot = bot

    @commands.command()
    @commands.guild_only()
    async def request(self, ctx, tier=None, pokemon_name=None):
        """Processes a users pokemon request"""
        if not await REQH.check_if_valid_request_channel(self.__bot, ctx.channel.id):
            await ctx.author.send(H.guild_member_dm(ctx.guild.name, "That channel is not a valid request channel."))
            return
        await asyncio.gather(REQH.request_pokemon_handle(self.__bot, ctx, tier, pokemon_name),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command()
    @commands.guild_only()
    async def raid_count(self, ctx):
        """Show total raids hosted in this server"""
        await asyncio.gather(RH.get_raid_count(self.__bot, ctx, True),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command()
    @commands.guild_only()
    async def remove(self, ctx, user):
        """Allows a host to remove a user from their lobby."""
        await asyncio.gather(RLH.remove_lobby_member_by_command(self.__bot, ctx, user),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx):
        """Allows a member to leave a lobby."""
        await asyncio.gather(RLH.remove_lobby_member_by_command(self.__bot, ctx, ctx.author, is_self=True),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command()
    @commands.guild_only()
    async def names(self, ctx):
        """Shows all trainer names for lobby members in a nice format."""
        await asyncio.gather(RLH.get_lobby_member_names(self.__bot, ctx),
                             self.__bot.delete_ignore_error(ctx.message))

def setup(bot):
    """Default setup function for file"""
    bot.add_cog(MemberCommands(bot))
