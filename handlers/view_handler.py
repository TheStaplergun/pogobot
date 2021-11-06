import discord

import handlers.helpers as H
import handlers.raid_handler as RH

def construct_raid_view(bot):
    raid_view = discord.ui.View()
    delete_button = discord.ui.Button(custom_id="button_delete_raid", label="Delete", emoji="🗑️")
    sign_up_button = discord.ui.Button(custom_id="button_sign_up_raid", label="Sign up", emoji="📝")
    add_role_button = discord.ui.Button(custom_id="button_add_role_raid", label="Get notifications", emoji="📬")
    remove_role_button = discord.ui.Button(custom_id="button_remove_role_raid", label="Stop notifications", emoji="📪")

    async def delete_button_callback(interaction):
        message_id = interaction.message.id
        results = await RH.check_if_in_raid(interaction, bot, interaction.user.id)
        if results and results.get("message_id") == message_id:
            message_to_send = "Your raid has been successfuly deleted."
            try:
                await interaction.message.delete()
            except discord.DiscordException:
                pass
        else:
            message_to_send = "You are not the host. You cannot delete this raid!"
        await interaction.user.send(H.guild_member_dm(bot.get_guild(interaction.guild_id).name, message_to_send))

    #delete_button.callback = test_function
    delete_button.callback = delete_button_callback
    raid_view.add_item(delete_button)
    raid_view.add_item(sign_up_button)
    raid_view.add_item(add_role_button)
    raid_view.add_item(remove_role_button)
    return raid_view
