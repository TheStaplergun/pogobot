"""Cog containing general commands"""
import asyncio
import time

#import discord
from discord.ext import commands

import handlers.friend_code_handler as FCH
import handlers.pokebattler.api_helper as APIH
import handlers.raid_lobby_handler as RLM

class GeneralCommands(commands.Cog):
    """General Commands Cog"""
    def __init__(self, bot):
        self.__bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Check if alive"""
        curr = time.time()
        latency: float = round(ctx.bot.latency * 1000.0, 2)
        msg = await ctx.send('Pinging... 🏓')
        await msg.edit(
            content=f'🏓 Pong! Latency is {round((time.time() - curr) * 1000.0, 2)}ms. API latency is {latency}ms.')

    @commands.command(aliases=["fcreg", "set_fc"])
    async def setfc(self, ctx):
        """Allows a user to register their Pokemon Go friend code."""
        await asyncio.gather(FCH.set_friend_code(ctx, self.__bot),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command(aliases=["set_name"])
    async def setname(self, ctx, name=""):
        """Allows a user to register their Pokemon Go trainer name."""
        await asyncio.gather(FCH.set_trainer_name(ctx, self.__bot),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command()
    async def fc(self, ctx):
        """Sends registered friend code to the channel the command was typed in."""
        await asyncio.gather(FCH.send_friend_code(ctx, self.__bot),
                             self.__bot.delete_ignore_error(ctx.message))


    @commands.command(aliases=["t", "T"])
    async def trainer(self, ctx):
        """Sends trainer information to current channel."""
        await asyncio.gather(FCH.send_trainer_information(ctx, self.__bot),
                             self.__bot.delete_ignore_error(ctx.message))


    @commands.command()
    async def dex(self, ctx, arg1="None", arg2="None"):
        """Retrieves Pokedex information for a given Pokedex number or Pokemon Name"""
        await asyncio.gather(APIH.retrieve_pokedex_data(self.__bot, ctx, arg1, arg2),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command(aliases=["c", "C"])
    async def counter(self, ctx, tier="None", name="None", weather="Clear"):
        await asyncio.gather(APIH.get_counter(self.__bot, ctx, tier, name, weather),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command(aliases=["Close"])
    async def close(self, ctx):
        """Allows a user to manually delete their lobby via command."""
        ctx.user_id = ctx.author.id
        await asyncio.gather(RLM.host_manual_remove_lobby(self.__bot, ctx),
                             self.__bot.delete_ignore_error(ctx.message))
    
    @commands.command(aliases=["Extend"])
    async def extend(self, ctx):
        """Allows a user to manually extend the time of their lobby via command."""
        ctx.user_id = ctx.author.id
        await asyncio.gather(RLM.extend_duration_of_lobby(self.__bot, ctx),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command(aliases=["ln", "Ln", "LN", "List_names"])
    async def list_names(self, ctx):
        """Shows all trainer names in a copy/paste format for searching in game."""
        ctx.user_id = ctx.author.id
        await asyncio.gather(RLM.show_raider_names(self.__bot, ctx),
                             self.__bot.delete_ignore_error(ctx.message))

def setup(bot):
    """Default setup function for file"""
    bot.add_cog(GeneralCommands(bot))
