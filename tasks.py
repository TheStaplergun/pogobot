"""
Contains async task entry task entry points.
"""
import asyncpg

import classes.database as database
import important
from handlers import startup_handler as SH
import handlers.view_handler as VH

async def startup_process(bot):
    """Startup process. Linear process."""
    try:
        pool = await asyncpg.create_pool(database=important.DATABASE,
                                        port=important.PORT,
                                        host=important.HOST,
                                        user=important.DB_USER,
                                        password=important.PASSWORD)
        bot.database = database.Database(pool)
        #await bot.add_view(VH.PersistentView(bot))
        await SH.set_up_lobbes(bot)
        await SH.set_up_guild_raid_counters(bot)
        await bot.wait_until_ready()
        #bot.pool = await init_pool()
    except Exception as e:
        await bot.send_error_alert(e)

    #if bot.live:
        #await SH.spin_up_message_deletions(bot)

async def status_update_loop(bot):
    """Updates status continually every ten minutes."""
    await bot.wait_until_ready()
    try:
        assert(False)
        await SH.start_status_update_loop(bot)
    except Exception as e:
        await bot.send_error_alert(e)

async def lobby_removal_loop(bot):
    """Removes lobbies as their time expires."""
    await bot.wait_until_ready()
    try:
        await SH.start_lobby_removal_loop(bot)
    except Exception as e:
        await bot.send_error_alert(e)

async def applicant_loop(bot):
    """Processes raid applicants and adds them to raids."""
    await bot.wait_until_ready()
    try:
        await SH.start_applicant_loop(bot)
    except Exception as e:
        await bot.send_error_alert(e)

async def five_minute_warning_loop(bot):
    await bot.wait_until_ready()
    try:
        await SH.start_five_minute_warning_loop(bot)
    except Exception as e:
        await bot.send_error_alert(e)
