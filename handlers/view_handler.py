import discord

import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH

def construct_raid_view(bot):
    raid_view = discord.ui.View(timeout=None)

    @discord.ui.Button(custom_id="button_delete_raid", label="Delete", emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete_button_callback(interaction):
        await RH.remove_raid_from_button(interaction, bot)

    @discord.ui.Button(custom_id="button_sign_up_raid", label="Sign up", emoji="📝", style=discord.ButtonStyle.green)
    async def sign_up_button_callback(interaction):
        await RLH.handle_application_from_button(interaction, bot)
        #RH.remove_raid_from_button(interaction, bot)

    @discord.ui.Button(custom_id="button_add_role_raid", label="Get notifications", emoji="📬")#, style=discord.ButtonStyle.green)
    async def add_role_button_callback(interaction):
        await interaction.channel.send("Not implemented yet")
        pass
        #RH.remove_raid_from_button(interaction, bot)

    @discord.ui.Button(custom_id="button_remove_role_raid", label="Stop notifications", emoji="📪")#, style=discord.ButtonStyle.red)
    async def remove_role_button_callback(interaction):
        await interaction.channel.send("Not implemented yet")
        pass
        #RH.remove_raid_from_button(interaction, bot)

    #delete_button.callback = test_function
    #delete_button.callback = delete_button_callback
    #sign_up_button.callback = sign_up_button_callback
    #add_role_button.callback = add_role_button_callback
    #remove_role_button.callback = remove_role_button_callback
    raid_view.add_item(delete_button)
    raid_view.add_item(sign_up_button)
    raid_view.add_item(add_role_button)
    raid_view.add_item(remove_role_button)
    return raid_view
