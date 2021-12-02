"""
Bot class that wraps discord client
"""
import asyncio

import discord
from discord.ext import commands

#import classes.database as database
from classes.lobby import Lobby
#import classes.lobby as lobby
import classes.pokedex as pokedex
import handlers.view_handler as VH
#from classes import database
#from classes import pokedex


class Bot(commands.Bot):
    """
    Subclasses commands.Bot from discord.
    Contains database and asyncio events directly.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.applicant_trigger = asyncio.Event()
        self.lobby_remove_trigger = asyncio.Event()
        self.raid_remove_trigger = asyncio.Event()
        self.five_minute_trigger = asyncio.Event()

        self.database = None
        self.dex = pokedex.Pokedex()
        self.raid_channel_cache = set()
        self.request_channel_cache = set()
        self.guild_raid_counters = {}
        self.raid_view = VH.RaidView
        self.request_view = VH.RequestView
        self.unlock_lobby_view = VH.UnlockLobbyView
        self.extend_lobby_view = VH.ExtendLobbyView
        #self.check_in_view = VH.CheckInView

        self.interactions = {}
        self.lobbies = {}

        self.error_channel = None
        self.status_update_interval = 1

    async def on_ready(self):
        self.add_view(VH.RaidView(self))
        self.add_view(VH.RequestView(self))
        self.add_view(VH.UnlockLobbyView(self))
        self.add_view(VH.ExtendLobbyView(self))

    async def get_lobby(self, lobby_id, user_limit=None, user_count=0, raid_id=None, host=None, delete_time=None, applicants=0):
        lobby = self.lobbies.get(lobby_id)
        if not lobby:
            lobby = Lobby(self, user_limit, user_count, lobby_id, raid_id, host, delete_time, applicants)

        return lobby

    async def retrieve_channel(self, *args, **kwargs):
        """
        Automatically fetches channel if channel is not in local cache.
        Virtually guarantees getting channel object if it does exist and bot can see it.
        """
        channel = self.get_channel(*args, **kwargs)
        if not channel:
            try:
                channel = await self.fetch_channel(*args, **kwargs)
            except discord.DiscordException:
                pass

        return channel

    async def retrieve_user(self, *args, **kwargs):
        """
        Automatically fetches a user if the user is not in the local cache.
        Virtually guarantees getting user object if it does exist and the bot can see it.
        """
        user = self.get_user(*args, **kwargs)
        if not user:
            try:
                user = await self.fetch_user(*args, **kwargs)
            except discord.DiscordException:
                pass

        return user

    async def delete_ignore_error(self, item):
        try:
            await item.delete()
        except discord.DiscordException:
            return
        except AttributeError:
            # Ignore if item doesn't have delete method
            return

    async def remove_role_ignore_error(self, member, role, reason):
        try:
            await member.remove_roles(role, reason=reason)
        except discord.DiscordException:
            pass
        except AttributeError:
            #Ignore if object doesn't have "remove_roles" method
            pass

    async def add_role_ignore_error(self, member, role, reason):
        try:
            await member.add_roles(role, reason=reason)
        except discord.DiscordException:
            pass
        except AttributeError:
            pass

    async def send_ignore_error(self, messageable, text, embed=None, delete_after=None):
        try:
            await messageable.send(text, embed=embed, delete_after=delete_after)
        except discord.DiscordException:
            pass
        except AttributeError:
            pass

    async def get_error_channel(self):
        if not self.error_channel:
            self.error_channel = await self.retrieve_channel(914713447772598282)

        return self.error_channel
