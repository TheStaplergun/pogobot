import asyncio

import discord

from data.formats import STATUS_TO_COLOR
import handlers.raid_handler as RH
class Lobby():
    """
    A class containing various pieces of cached data about a lobbym
    """
    def __init__(self, bot, user_limit, user_count, lobby_id, raid_id, host, delete_time):
        self.__bot = bot
        self.user_limit = user_limit
        self.user_count = user_count
        self.applicant_count = 0
        self.lobby_id = lobby_id
        self.lobby_channel = None
        self.raid_id = raid_id
        self.host = host
        self.has_filled = self.is_full()
        self.pending_unlock = False
        self.lock()
        self.five_minute_warning = False
        self.delete_time = delete_time
        self.raid_still_exists = True
        self.updating_raid_status = False
        self.applicants = ()
        self.members = ()

    async def add_a_user(self, user_id):
        self.user_count+=1
        self.members.update(user_id)
        #await self.update_raid_status()
        return self.user_count

    async def remove_a_user(self, user_id):
        self.user_count-=1
        if user_id in self.members:
            self.members.remove(user_id)
        #await self.update_raid_status()

    async def add_an_applicant(self, user_id):
        self.applicant_count+=1
        self.applicants.update(user_id)
        #await self.update_raid_status()

    async def remove_an_applicant(self, user_id):
        self.applicant_count-=1
        if user_id in self.applicants:
            self.applicants.remove(user_id)
        #await self.update_raid_status()

    def check_if_user_already_in_lobby(self, user_id):
        return user_id in self.lobby_members

    def check_if_user_is_already_applied(self, user_id):
        return user_id in self.applicants

    def is_full(self):
        return self.user_count == self.user_limit

    async def lock(self):
        self.has_filled = True if self.is_full() else False
        #await self.update_raid_status()

    async def unlock(self):
        self.has_filled = False
        self.pending_unlock = False
        self.__bot.applicant_trigger.set()
        #await self.update_raid_status()

    async def update_raid_status(self):
        if self.updating_raid_status == True or not self.raid_still_exists:
            return
        self.updating_raid_status = True
        await asyncio.sleep(self.__bot.status_update_interval)
        raid_data = RH.retrieve_raid_data_by_message_id(None, self.__bot, self.raid_id)
        raid_channel = self.__bot.retrieve_channel(raid_data.get("channel_id"))
        try:
            raid_message = await raid_channel.fetch_message(self.raid_id)
        except discord.DiscordException:
            self.raid_still_exists = False
            return
        embed = raid_message.embeds[0]
        status=None
        if self.is_full:
            status = "Locked (Full)"
        if not self.is_full and not self.pending_unlock:
            status = "Unlocked (Searching for users)"
        new_embed = discord.Embed(title=embed.title, description=embed.description, color=STATUS_TO_COLOR.get(status))
        new_embed.add_field(name=embed.fields[0].name, value=embed.fields[0].value)
        new_embed.add_field(name=embed.fields[1].name, value=embed.fields[1].value)
        new_embed.add_field(name=embed.fields[2].name, value=embed.fields[2].value)
        new_embed.add_field(name=embed.fields[3].name, value=embed.fields[3].value)
        new_embed.add_field(name="Status", value=status)
        raid_message.edit(embed=new_embed)
        self.updating_raid_status = False

    async def get_channel(self):
        self.lobby_channel = await self.__bot.retrieve_channel(self.lobby_id) if not self.lobby_channel else self.lobby_channel

    async def ask_to_unlock(self):
        if self.pending_unlock:
            return

        embed = discord.Embed(title="Unlock?", description="The lobby is no longer full. Would you like to gather more users?")
        await self.get_channel()
        try:
            await self.lobby_channel.send(f"<@{self.host.id}>", embed=embed, view=self.__bot.unlock_lobby_view(self.__bot))
        except discord.DiscordException:
            pass

        self.pending_unlock = True

    async def send_five_minute_warning(self):
        embed = discord.Embed(title="Warning", description="Only five minutes remain on the time of this lobby. Would you like to extend the lobby?")
        await self.get_channel()
        try:
            await self.lobby_channel.send(f"<@{self.host.id}>", embed=embed, view=self.__bot.extend_lobby_view(self.__bot))
        except discord.DiscordException:
            pass
        self.five_minute_warning = True
