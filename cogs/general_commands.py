"""Cog containing general commands"""
import time

#import discord
from discord.ext import commands

import handlers.friend_code_handler as FCH

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

def setup(bot):
    """Default setup function for file"""
    bot.add_cog(GeneralCommands(bot))