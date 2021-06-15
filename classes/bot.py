"""
Bot class that wraps discord client
"""
import asyncio 

from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.client = commands.Bot(command_prefix, description=description, activity=game, intents=intent)

        self.applicant_trigger = asyncio.Event()
        self.lobby_remove_trigger = asyncio.Event()
