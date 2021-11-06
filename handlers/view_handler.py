import discord

import handlers.helpers as H
import handlers.raid_handler as RH
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
        #RH.remove_raid_from_button(interaction, bot)

    @discord.ui.button(custom_id="button_add_role_raid", label="Get notifications", emoji="📬")#, style=discord.ButtonStyle.green)
    async def add_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await RH.add_request_role_to_user_from_button(interaction, self.__bot)
        #await interaction.channel.send("Not implemented yet")
        pass
        #RH.remove_raid_from_button(interaction, bot)

    @discord.ui.button(custom_id="button_remove_role_raid", label="Stop notifications", emoji="📪")#, style=discord.ButtonStyle.red)
    async def remove_role_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        #await interaction.channel.send("Not implemented yet")
        pass
        #RH.remove_raid_from_button(interaction, bot)


#def construct_raid_view(bot):
#    raid_view = discord.ui.View(timeout=None)
