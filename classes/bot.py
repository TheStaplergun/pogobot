"""
Bot class that wraps discord client
"""
import asyncio

import classes.database as database
from discord.ext import commands

class Bot(commands.Bot):
    """
    Subclasses commands.Bot from discord.
    Contains database and asyncio events directly.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.applicant_trigger = asyncio.Event()
        self.lobby_remove_trigger = asyncio.Event()

        self.database = None
