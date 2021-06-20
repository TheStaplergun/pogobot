"""
Bot class that wraps discord client
"""
import asyncio

from classes import database
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
        self.raid_channel_cache = []

    async def retrieve_channel(self, *args, **kwargs):
        """
        Automatically fetches channel if channel is not in local cache.
        Virtually guarantees getting channel object if it does exist and bot can see it.
        """
        channel = self.get_channel(*args, **kwargs)
        if not channel:
            channel = await self.fetch_channel(*args, **kwargs)

        return channel