import traceback

import discord

import handlers.pokebattler.api_helper as APIH
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handler as REQH
import handlers.raid_lobby_handler as RLH
import handlers.raid_lobby_management as RLM

class RaidView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.__bot = bot

    @discord.ui.button(custom_id="button_sign_up_raid", label="Sign up", emoji="📝", style=discord.ButtonStyle.green)
    async def sign_up_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RLH.handle_application_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_counter_raid", label="Recommended Counters", emoji="⚔️", style=discord.ButtonStyle.blurple)
    async def send_counters_button_callback(self, button:discord.ui.Button, interaction: discord.Interaction):
        await APIH.get_counter_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_add_role_raid", label="Get notifications", emoji="📬")#, style=discord.ButtonStyle.green)
    async def add_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await REQH.add_request_role_to_user_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_remove_role_raid", label="Stop notifications", emoji="📪")#, style=discord.ButtonStyle.red)
    async def remove_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await REQH.remove_request_role_from_user_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_delete_raid", label="Delete (Host only)", emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RH.remove_raid_from_button(interaction, self.__bot)

# class CheckInView(discord.ui.View):
#     def __init__(self, bot):
#         super().__init__(timeout=None)
#         self.__bot = bot

#     @discord.ui.button(custom_id="button_check_in", label="Delete", emoji="⏱️", style=discord.ButtonStyle.green)
#     async def check_in_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
#         await RLH.handle_check_in_from_button(interaction, self.__bot)

class RequestView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.__bot = bot

    @discord.ui.button(custom_id="button_add_role_request", label="Get notifications", emoji="📬", style=discord.ButtonStyle.green)
    async def add_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await REQH.add_request_role_to_user_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_remove_role_request", label="Stop notifications", emoji="📪", style=discord.ButtonStyle.red)
    async def remove_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await REQH.remove_request_role_from_user_from_button(interaction, self.__bot)

# TODO: Future shit.
# class AreYouSureCancelApplication(discord.ui.View):
#     def __init__(self, bot):
#         super().__init__(timeout=None)
#         self.__bot = bot

#     @discord.ui.button(custom_id="button_add_role_request", label="Get notifications", emoji="📬", style=discord.ButtonStyle.green)
#     async def add_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
#         await REQH.add_request_role_to_user_from_button(interaction, self.__bot)

#     @discord.ui.button(custom_id="button_remove_role_request", label="Stop notifications", emoji="📪", style=discord.ButtonStyle.red)
#     async def remove_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
#         await REQH.remove_request_role_from_user_from_button(interaction, self.__bot)

class UnlockLobbyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.__bot = bot

    @discord.ui.button(custom_id="button_unlock_lobby", label="Unlock Lobby (Attempt to Fill)", emoji="🔓", style=discord.ButtonStyle.green)
    async def unlock_lobby_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RLH.unlock_lobby_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_lock_lobby", label="Keep Lobby Locked (Deletes Raid)", emoji="🔒", style=discord.ButtonStyle.red)
    async def lock_lobby_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RLH.lock_lobby_from_button(interaction, self.__bot)

class ExtendLobbyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.__bot = bot

    @discord.ui.button(custom_id="button_extend_lobby", label="Extend Lobby Time", emoji="⏱️", style=discord.ButtonStyle.green)
    async def extend_lobby_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await RLM.extend_lobby_from_button(interaction, self.__bot)
        except Exception as e:
            #channel = await self.__bot.get_error_channel()
            await self.__bot.send_error_alert("applicant handler loop", e)
