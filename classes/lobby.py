import discord

class Lobby():
    """
    A class containing various pieces of cached data about a lobbym
    """
    def __init__(self, bot, user_limit, user_count, lobby_id, raid_id, host, delete_time):
        self.__bot = bot
        self.user_limit = user_limit
        self.user_count = user_count
        self.lobby_id = lobby_id
        self.lobby_channel = None
        self.raid_id = raid_id
        self.host = host
        self.has_filled = False
        self.lock()
        self.five_minute_warning = False
        print(f"Lobby delete time is {delete_time}")
        self.delete_time = delete_time
        #self.lobby_members = []

    def add_a_user(self):
        self.user_count+=1
        return self.user_count

    def remove_a_user(self):
        self.user_count-=1

    def is_full(self):
        return self.user_count == self.user_limit

    def lock(self):
        self.has_filled = True if self.is_full() else False

    def unlock(self):
        self.has_filled = False
        self.__bot.applicant_trigger.set()

    async def get_channel(self):
        self.lobby_channel = await self.__bot.retrieve_channel(self.lobby_id) if not self.lobby_channel else self.lobby_channel

    async def ask_to_unlock(self):
        embed = discord.Embed(title="Unlock?", description="The lobby is no longer full. Would you like to gather more users?")
        await self.get_channel()
        try:
            await self.lobby_channel.send(f"<@{self.host.id}>", embed=embed, view=self.__bot.unlock_lobby_view(self.__bot))
        except discord.DiscordException:
            pass

    async def send_five_minute_warning(self):
        embed = discord.Embed(title="Warning", description="Only five minutes remain on the time of this lobby. Would you like to extend the lobby?")
        await self.get_channel()
        try:
            await self.lobby_channel.send(f"<@{self.host.id}>", embed=embed, view=self.__bot.extend_lobby_view(self.__bot))
        except discord.DiscordException:
            pass
        self.five_minute_warning = True
