"""Cog containing administrative commands"""
import asyncio

import discord
from discord.ext import commands

import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH
import handlers.request_handler as REQH

class AdminCommands(commands.Cog):
    """Admin Commands Cog"""
    def __init__(self, bot):
        self.__bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    async def clear_raid(self, ctx, user_id):
        """Mod Only - Removes a given user from their raid. Deletes database entry."""
        await asyncio.gather(RH.handle_clear_user_from_raid(ctx, self.__bot, user_id),
                             self.__bot.delete_ignore_error(ctx.message))


    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    async def clear_requests(self, ctx):
        """Mod Only - Clears all requests for this guild."""
        await asyncio.gather(REQH.handle_clear_all_requests_for_guild(ctx, self.__bot),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    async def clear_application(self, ctx, user_id):
        """Mod Only - Clears an application for a specific user by ID"""
        await asyncio.gather(RLH.handle_manual_clear_application(ctx, user_id, self.__bot),
                             self.__bot.delete_ignore_error(ctx.message))
        
    # @commands.command()
    # @commands.guild_only()
    # @commands.has_guild_permissions(manage_messages=True, manage_roles=True, manage_channels=True)
    # async def clear_lobby(self, ctx, user_id):
    #     """Mod Only - Clears an application for a specific user by ID"""
    #     await asyncio.gather(RLH.handle_admin_clear_lobby(ctx, user_id, self.__bot),
    #                          self.__bot.delete_ignore_error(ctx.message))
    
    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True, manage_channels=True)
    async def a_close(self, ctx, channel_id=""):
        """Mod Only - Flags a raid lobby for closure."""
        await asyncio.gather(RLH.handle_admin_close_lobby(ctx, self.__bot, channel_id),
                             self.__bot.delete_ignore_error(ctx.message))

    @commands.command(name="add_action", aliases=["aa"])
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    async def add_evasion(self, ctx, message):
        user_id = message.split(" ")[0]
        note = message.split(" ").remove(message[0])
        await asyncio.gather(REQH.insert_mod_action(ctx, self.__bot, user_id, note))

    @commands.command(name="delete_action", aliases=["da"])
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    async def delete_evasion(self, action_id):
        await asyncio.gather(REQH.delete_mod_action(self.__bot, action_id))

    @commands.command(name="get_actions", aliases=["ga"])
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    def get_all_evasion_mod_actions(self, ctx, user_id):
        results = asyncio.gather(REQH.get_mod_actions_by_user_id(user_id))
        all_results = ""
        if not results:
            all_results = "No records found for this user."
        for r in results:
            mod_id = r.get("mod_id")
            note = r.get("note")
            date = r.get("date")
            all_results += "Action ID: " + r.get("action_id") + f"\nMod: <@{mod_id}>" + f"\nDate: {date}" + f"\nNote: {note}\n\n"
        new_embed = discord.Embed(title=f"All action information for user: <@{user_id}>", color=0x00ff00)
        new_embed.add_field(value=all_results)
        ctx.send(new_embed)

    @commands.command(name="get_action")
    @commands.has_guild_permissions(manage_messages=True, manage_roles=True)
    async def get_one_evasion_mod_action(self, ctx, action_id):
        result = asyncio.gather(REQH.get_mod_action_by_id(action_id))
        response = ""
        if not result:
            response = "Oh fuck action doesn't exist."
        else:
            mod_id = result.get("mod_id")
            note = result.get("note")
            date = result.get("date")
            user_id = result.get("user_id")
            response = "Action ID: " + result.get("action_id") + f"\nMod: <@{mod_id}>" + f"\nDate: {date}" + f"\nNote: {note}\n\n"
        new_embed = discord.Embed(title=f"All action information for user: <@{user_id}>", color=0x00ff00)
        new_embed.add_field(value=response)
        ctx.send(new_embed)


def setup(bot):
    """Default setup function for file"""
    bot.add_cog(AdminCommands(bot))
