import discord
import importlib
from discord.ext import commands
from datetime import datetime, timedelta
from pogo_raid_lib import *
import handlers.helpers as H
import handlers.raid_handler as RH
import handlers.request_handler as REQH
import handlers.sticky_handler as SH

class RaidPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role("Mods")
    async def get_raids(self, ctx):
        """Mod Only - Show all current running raid statistics for this guild"""
        await RH.get_all_raids_for_guild(self.bot, ctx)

    @commands.command()
    @commands.guild_only()
    async def raid(self,
                   ctx,
                   tier = "`No tier provided`",
                   pokemon_name = "`No Pokemon Name provided`",
                   #gym_color = "`No gym color provided`",
                   weather = "`No weather condition provided`",
                   #invite_slots = "`No invite slot count provided`",
                   #time_to_start = "`No time to start provided`",
                   time_to_expire = "`No time to expire provided`"):

        """Post a raid"""

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
                remove_after_seconds = int(remove_after) * 60
                channel_message_body = "Raid hosted by {}\n".format(ctx.author.mention)
                _, _, _, role_id = await REQH.check_if_request_message_exists(self.bot, response.title, ctx.guild.id)
                if role_id:
                    role = discord.utils.get(ctx.guild.roles, id=role_id)
                    channel_message_body = "{} hosted by {}\n".format(role.mention, ctx.author.mention)
                message_to_dm = "Your raid has been successfully listed.\nIt will automatically be deleted at the time given in `Time to Expire`.\nPress the red X emoji to remove it at any time."
                try:
                    await ctx.author.send(H.guild_member_dm(ctx.guild.name, message_to_dm))
                except discord.Forbidden:
                    await ctx.send(ctx.author.name + ", I was unable to DM you. You must have your DMs open to coordinate raids.\nRaid will not be listed.", delete_after=15)
                    return
                request_channel_id = await REQH.get_request_channel(self.bot, ctx.guild.id)
                if request_channel_id:
                    response.add_field(name="Want to be notified for this pokemon in the future?", value="Click the 📬 reaction to receive a role and be pinged for future raids.\nClick 📪 to remove yourself from notifications.", inline=False)
                message = await ctx.send(channel_message_body, embed=response, delete_after=remove_after_seconds)
                no_emoji = self.bot.get_emoji(743179437054361720)
                await message.add_reaction(no_emoji)
                time_to_delete = datetime.now() + timedelta(seconds = remove_after_seconds)
                await RH.add_raid_to_table(ctx, self.bot, message.id, ctx.guild.id, message.channel.id, ctx.author.id, time_to_delete)
                print("[*][{}][{}] Raid successfuly posted.".format(ctx.guild, ctx.author.name))
                if request_channel_id:
                    try:
                        await message.add_reaction("📬")
                        await message.add_reaction("📪")
                    except discord.DiscordException as error:
                      print("[!] Exception occurred during adding request enrollment reactions. [{}]".format(error))
                try:
                    await SH.toggle_raid_sticky(self.bot, ctx, int(ctx.channel.id), int(ctx.guild.id))
                except discord.DiscordException as error:
                    print("[!] Exception occurred during togle of raid sticky. [{}]".format(error))
                try:
                    await RH.increment_raid_counter(ctx, self.bot, int(ctx.guild.id))
                except discord.DiscordException as error:
                    print("[!] Exception occured during increment of raid counter. [{}]".format(error))
            else:
                response += "---------\n"
                response += "*Here's the command you entered below. Suggestions were added. Check that it is correct and try again.*\n"
                await ctx.author.send(response)
                correction_suggestion = ctx.prefix + "raid " + suggestion
                await ctx.author.send(correction_suggestion)
                print("[!][{}][{}] Raid failed to post due to invalid arguments.".format(ctx.guild, ctx.author.name))
