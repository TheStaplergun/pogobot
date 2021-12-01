"""Helper functions"""

from data.formats import WEATHER_TO_EMOJI

def guild_member_dm(guild_name, message):
    return "**From:** {} raid hosting bot\n{}".format(guild_name, message)

def get_pokemon_name_from_raid(message):
    embed = message.embeds[0]
    title = embed.title
    if title.startswith("Mega ", 0, 5):
        return True, title.split(" ")[1]
    return False, title

def get_tier_from_raid(message):
    embed = message.embeds[0]
    tier = "1"
    for field in embed:
        if field.name == "Tier":
            tier = field.value
            break

    return tier

EMOJI_TO_WEATHER = {v:k for k,v in WEATHER_TO_EMOJI.items()}

def get_weather_from_emoji(message):
    embed = message.embeds[0]
    emoji = "☀️"
    for field in embed:
        if field.name == "Weather":
            emoji = field.value
            break

    return EMOJI_TO_WEATHER.get(emoji)
