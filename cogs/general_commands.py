"""Cog containing general commands"""
import time

#import discord
from discord.ext import commands

import handlers.friend_code_handler as FCH
import handlers.pokebattler.api_helper as APIH

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

    @commands.command()
    async def fcreg(self, ctx):
        """Allows a user to register their Pokemon Go friend code."""
        await FCH.set_friend_code(ctx, self.__bot)

    @commands.command()
    async def fc(self, ctx):
        """Sends registered friend code to the channel the command was typed in."""
        await FCH.send_friend_code(ctx, self.__bot)

    @commands.command()
    async def dex(self, ctx, arg1="None", arg2="None"):
        """Retrieves Pokedex information for a given Pokedex number or Pokemon Name"""
        await APIH.retrieve_pokedex_data(self.__bot, ctx, arg1, arg2)
    
    @commands.command()
    async def c(self, ctx, tier="None", name="None", weather="Clear"):
        await APIH.get_counter(self.__bot, ctx, tier, name, weather)

    #@commands.command()

def setup(bot):
    """Default setup function for file"""
    bot.add_cog(GeneralCommands(bot))
