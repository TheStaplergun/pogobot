import discord

async def construct_raid_view(bot):
    raid_view = discord.ui.View()
    delete_button = discord.ui.Button(custom_id="button_delete_raid", label="Delete", emoji="🗑️")
    sign_up_button = discord.ui.Button(custom_id="button_sign_up_raid", label="Sign up", emoji="📝")
    add_role_button = discord.ui.Button(custom_id="button_add_role_raid", label="Get notifications", emoji="📬")
    remove_role_button = discord.ui.Button(custom_id="button_remove_role_raid", label="Stop notifications", emoji="📪")
    async def test_function():
        print("This is a test")
    delete_button.callback = test_function
    raid_view.add_item(delete_button)
