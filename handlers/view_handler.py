import discord

import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handler as REQH
import handlers.raid_lobby_handler as RLH

class RaidView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.__bot = bot

    @discord.ui.button(custom_id="button_delete_raid", label="Delete", emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RH.remove_raid_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_sign_up_raid", label="Sign up", emoji="📝", style=discord.ButtonStyle.green)
    async def sign_up_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RLH.handle_application_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_add_role_raid", label="Get notifications", emoji="📬")#, style=discord.ButtonStyle.green)
    async def add_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await REQH.add_request_role_to_user_from_button(interaction, self.__bot)

    @discord.ui.button(custom_id="button_remove_role_raid", label="Stop notifications", emoji="📪")#, style=discord.ButtonStyle.red)
    async def remove_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await REQH.remove_request_role_from_user_from_button(interaction, self.__bot)

class CheckInView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.__bot = bot

    @discord.ui.button(custom_id="button_check_in", label="Delete", emoji="⏱️", style=discord.ButtonStyle.green)
    async def check_in_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RLH.handle_check_in_from_button(interaction, self.__bot)
