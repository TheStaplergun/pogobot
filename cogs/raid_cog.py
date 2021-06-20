from datetime import datetime, timedelta
import os

import discord
from discord.ext import commands
from pogo_raid_lib import validate_and_format_message
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH
import handlers.request_handler as REQH
import handlers.sticky_handler as SH

class RaidPost(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

    @commands.command(aliases=["r", "Raid"])
    @commands.guild_only()
    async def raid(self,
                   ctx,
                   tier = "`No tier provided`",
                   pokemon_name = "`No Pokemon Name provided`",
                   weather = "`No weather condition provided`",
                   invite_slots = "5"):

        """Post a raid"""
        print("[*] Processing raid.")
        if not await RH.check_if_valid_raid_channel(self.__bot, ctx.channel.id):
            return
        try:
            await ctx.message.delete()
        except:
            pass
        if await RH.check_if_in_raid(ctx, self.__bot, ctx.author.id):
            await ctx.author.send(H.guild_member_dm(ctx.guild.name, "You are already in a raid."))
            return
        if await RLH.get_lobby_data_by_user_id(self.__bot, ctx.author.id):
            await ctx.author.send(H.guild_member_dm(ctx.guild.name, "You currently have a lobby open. Please close your old lobby and retry."))
            return

        async with ctx.channel.typing():
            raid_is_valid, response, suggestion = validate_and_format_message(ctx,
                                                                              tier,
                                                                              pokemon_name,
                                                                              weather,
                                                                              invite_slots)
            if raid_is_valid:
                remove_after_seconds = 600
                channel_message_body = f'Raid hosted by {ctx.author.mention}\n'
                _, _, _, role_id = await REQH.check_if_request_message_exists(self.__bot, response.title, ctx.guild.id)
                message_to_dm = "Your raid has been successfully listed.\nIt will automatically be deleted at the time given in `Time to Expire` or just 10 minutes.\nPress the trash can to remove it at any time."
                try:
                    await ctx.author.send(H.guild_member_dm(ctx.guild.name, message_to_dm))
                except discord.Forbidden:
                    await ctx.send(ctx.author.name + ", I was unable to DM you. You must have your DMs open to coordinate raids.\nRaid will not be listed.", delete_after=15)
                    return
                request_channel_id = await REQH.get_request_channel(self.__bot, ctx.guild.id)
                if request_channel_id:
                    response.add_field(name="Want to be pinged for future raids?", value="📬 Add Role\n📪 Remove Role", inline=False)
                raid_lobby_category = await RLH.get_raid_lobby_category_by_guild_id(self.__bot, ctx.guild.id)
                start_string = ""
                if role_id:
                    role = discord.utils.get(ctx.guild.roles, id=role_id)
                    start_string = f'{role.mention}'
                end_string = ""
                if raid_lobby_category:
                    response.set_footer(text="📝 sign up")
                else:
                    end_string = f' hosted by {ctx.author.mention}\n'
                channel_message_body = start_string + end_string
                try:
                    message = await ctx.send(channel_message_body, embed=response, delete_after=remove_after_seconds)
                except discord.DiscordException as error:
                    print(f'[*][{ctx.guild.name}][{ctx.author}] An error occurred listing a raid. [{error}]')
                    return

                await message.add_reaction("🗑️")

                time_to_delete = datetime.now() + timedelta(seconds=remove_after_seconds)
                if await RLH.get_raid_lobby_category_by_guild_id(self.__bot, ctx.guild.id):
                    time_to_remove_lobby = time_to_delete + timedelta(seconds=300)
                    lobby = await RLH.create_raid_lobby(ctx, self.__bot, message.id, ctx.author, time_to_remove_lobby, int(invite_slots))
                    await message.add_reaction("📝")
                if request_channel_id:
                    try:
                        await message.add_reaction("📬")
                        await message.add_reaction("📪")
                    except discord.DiscordException as error:
                        print(f'[!] Exception occurred during adding request enrollment reactions. [{error}]')
                edited_message_content = f"{message.content}\n{lobby.mention} **<- lobby**"
                await message.edit(content=edited_message_content)
                await RH.add_raid_to_table(ctx, self.__bot, message.id, ctx.guild.id, message.channel.id, ctx.author.id, time_to_delete)
                print(f'[*][{ctx.guild}][{ctx.author.name}] Raid successfuly posted.')

                try:
                    await SH.toggle_raid_sticky(self.__bot, ctx, int(ctx.channel.id), int(ctx.guild.id))
                except discord.DiscordException as error:
                    print(f'[!] Exception occurred during toggle of raid sticky. [{error}]')
                try:
                    await RH.increment_raid_counter(ctx, self.__bot, int(ctx.guild.id))
                except discord.DiscordException as error:
                    print(f'[!] Exception occured during increment of raid counter. [{error}]')
            else:
                response += "---------\n"
                response += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
                await ctx.author.send(response)
                correction_suggestion = ctx.prefix + "raid " + suggestion
                await ctx.author.send(correction_suggestion)
                print(f'[!][{ctx.guild}][{ctx.author.name}] Raid failed to post due to invalid arguments.')

def setup(bot):
    """Default setup function for file"""
    bot.add_cog(RaidPost(bot))
