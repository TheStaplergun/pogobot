import discord
import importlib
from discord.ext import commands
from datetime import datetime, timedelta
from pogo_raid_lib import *
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.raid_lobby_handler as RLH
import handlers.request_handler as REQH
import handlers.sticky_handler as SH
import os
import dotenv

if os.path.exists('.env'):
    dotenv.load_dotenv()

class RaidPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(os.getenv('MOD_ROLE'))
    async def get_raids(self, ctx):
        """Mod Only - Show all current running raid statistics for this guild"""
        await RH.get_all_raids_for_guild(self.bot, ctx)

    @commands.command(aliases=["r"])
    @commands.guild_only()
    async def raid(self,
                   ctx,
                   tier = "`No tier provided`",
                   pokemon_name = "`No Pokemon Name provided`",
                   #gym_color = "`No gym color provided`",
                   weather = "`No weather condition provided`",
                   #invite_slots = "`No invite slot count provided`",
                   #time_to_start = "`No time to start provided`",
                   time_to_expire = "0"):

        """Post a raid"""
        print("[*] Processing raid.")
        if not await RH.check_if_valid_raid_channel(self.bot, ctx.channel.id):
            return

        try:
            await ctx.message.delete()
        except:
            pass
        if await RH.check_if_in_raid(ctx, self.bot, ctx.author.id):
            try:
                await ctx.author.send(H.guild_member_dm(ctx.guild.name, "You are already in a raid."))
            except discord.DiscordException:
                pass
            return

        async with ctx.channel.typing():
            raid_is_valid, response, remove_after, suggestion = validate_and_format_message(ctx,
                                                                                            tier,
                                                                                            pokemon_name,
                                                                                            #gym_color,
                                                                                            weather,
                                                                                            #invite_slots,
                                                                                            #time_to_start,
                                                                                            time_to_expire)
            if raid_is_valid:
                if remove_after < 10:
                    remove_after = 10
                remove_after_seconds = int(remove_after) * 60 
                channel_message_body = f'Raid hosted by {ctx.author.mention}\n'
                _, _, _, role_id = await REQH.check_if_request_message_exists(self.bot, response.title, ctx.guild.id)
                message_to_dm = "Your raid has been successfully listed.\nIt will automatically be deleted at the time given in `Time to Expire` or just 10 minutes.\nPress the trash can to remove it at any time."
                try:
                    await ctx.author.send(H.guild_member_dm(ctx.guild.name, message_to_dm))
                except discord.Forbidden:
                    await ctx.send(ctx.author.name + ", I was unable to DM you. You must have your DMs open to coordinate raids.\nRaid will not be listed.", delete_after=15)
                    return
                request_channel_id = await REQH.get_request_channel(self.bot, ctx.guild.id)
                if request_channel_id:
                    response.add_field(name="Want to be notified for this pokemon in the future?", value="Click the 📬 reaction to be notified of future raids.\nClick 📪 to remove yourself from notifications.", inline=False)
                raid_lobby_category = await RLH.get_raid_lobby_category_by_guild_id(self.bot, ctx.guild.id)
                start_string = ""
                if role_id:
                    role = discord.utils.get(ctx.guild.roles, id=role_id)
                    start_string = f'{role.mention}'
                end_string = ""
                if self.bot.categories_allowed and raid_lobby_category:
                    response.set_footer(text="To sign up for this raid, tap the 📝 below.")
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
                if self.bot.categories_allowed and await RLH.get_raid_lobby_category_by_guild_id(self.bot, ctx.guild.id):
                    time_to_remove_lobby = time_to_delete + timedelta(seconds=300)
                    await RLH.create_raid_lobby(ctx, self.bot, message.id, ctx.author, time_to_remove_lobby)
                    await message.add_reaction("📝")

                await RH.add_raid_to_table(ctx, self.bot, message.id, ctx.guild.id, message.channel.id, ctx.author.id, time_to_delete)
                print(f'[*][{ctx.guild}][{ctx.author.name}] Raid successfuly posted.')
                if request_channel_id:
                    try:
                        await message.add_reaction("📬")
                        await message.add_reaction("📪")
                    except discord.DiscordException as error:
                      print(f'[!] Exception occurred during adding request enrollment reactions. [{error}]')
                try:
                    await SH.toggle_raid_sticky(self.bot, ctx, int(ctx.channel.id), int(ctx.guild.id))
                except discord.DiscordException as error:
                    print(f'[!] Exception occurred during toggle of raid sticky. [{error}]')
                try:
                    await RH.increment_raid_counter(ctx, self.bot, int(ctx.guild.id))
                except discord.DiscordException as error:
                    print(f'[!] Exception occured during increment of raid counter. [{error}]')
            else:
                response += "---------\n"
                response += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
                await ctx.author.send(response)
                correction_suggestion = ctx.prefix + "raid " + suggestion
                await ctx.author.send(correction_suggestion)
                print(f'[!][{ctx.guild}][{ctx.author.name}] Raid failed to post due to invalid arguments.')
