import discord
from discord.ext import commands
import fuzzysearch
from fuzzysearch import find_near_matches
from data.formats import *
from data.pokemon import *

# A macro to set a default fuzzy search limit
def fuzzy_search(search_for, search_in, limit):
  match = find_near_matches(search_for,
                            search_in,
                            max_deletions=limit,
                            max_insertions=limit,
                            max_substitutions=limit,
                            max_l_dist=limit)

  try:
    data_to_return = (True, match.pop().matched)
  except IndexError:
    data_to_return = (False, "")

  return data_to_return

def validate_and_format_message(ctx,
                                tier,
                                pokemon_name,
                                gym_color,
                                weather,
                                invite_slots,
                                time_to_start,
                                time_to_expire):
  # Format raid post
  raid_post_valid = True
  author_dm = "**From:** r/pokemongo raid hosting bot\n"

  """----------------------------------------------------------------"""
  is_valid, response = validate_tier(tier)
  if is_valid:
    embed_tier = response
  else:
    raid_post_valid = False
    author_dm += response
  """----------------------------------------------------------------"""
  pokemon_name = pokemon_name.title()
  """----------------------------------------------------------------"""
  is_valid, response = validate_gym_argument(gym_color)
  if is_valid:
    embed_gym = response
  else:
    raid_post_valid = False
    author_dm += response
  """----------------------------------------------------------------"""
  is_valid, response = validate_weather_argument(weather)
  if is_valid:
    embed_weather = response
  else:
    raid_post_valid = False
    author_dm += response
  """----------------------------------------------------------------"""
  """is_valid, response = validate_invites_argument(invite_slots)
  if is_valid:
    embed_invites = response
  else:
    raid_post_valid = False
    author_dm += response"""


  if raid_post_valid:
    embed = discord.Embed(title='Test', description='Test embed', color=get_embed_color(gym_color))
    embed.add_field(name="Tier", value=embed_tier, inline=False)
    embed.add_field(name="Pokemon", value=pokemon_name, inline=False)
    embed.add_field(name="Gym Control", value=embed_gym, inline=False)
    embed.add_field(name="Weather", value=embed_weather, inline=False)
    """embed.add_field(name="Invites Available", value=embed_invites, inline=False)"""
    embed.set_footer(text="TheStaplergun")
    """Send Message"""
    return (raid_post_valid, embed)
  else:
    return (raid_post_valid, author_dm)

"""----------------------------------------------------------------"""
"""TIER"""
# Creates the error message string for the author providing an invalid tier in the post_raid command
def validate_tier(tier):
  tier = tier.lower()
  response = ""
  is_valid = True

  if tier.lower() in TIERS:
    response = tier.title()
  else:
    is_valid = False
    response = format_invalid_tier_message(tier)

  return(is_valid, response)

def format_invalid_tier_message(tier):
  author_dm = "You gave an invalid **Tier** of [`" + tier + "`]. Valid tiers are: "

  for index, item in enumerate(TIERS):
    author_dm += item.title()
    if index < len(TIERS) - 1:
      author_dm += ", "

  author_dm += "\n"
  return author_dm
"""----------------------------------------------------------------"""
"""GYM COLOR"""
def validate_gym_argument(gym_color):
  gym_color = gym_color.lower()
  is_valid = False
  response = ""

  for key, value in GYM_COLOR_TO_CONTROL_TEAM.items():
    if gym_color == key:
      gym_control = GYM_COLOR_TO_CONTROL_TEAM.get(gym_color)
      is_valid = True
    elif gym_color == value:
      gym_control = value
      is_valid = True

  if is_valid:
    response = gym_control + " <:gym" + gym_control.lower() + ":" + GYM_CONTROL_EMOJI_ID.get(gym_control) + ">"
  else:
    response = format_invalid_gym_message(gym_color)

  return (is_valid, response)

# Iterates over the GYM_COLOR_TO_CONTROL_TEAM dictionary and appends all keys with values to the string.
def format_invalid_gym_message(gym_color):
  response = "You gave an invalid **Gym Color** of [`" + gym_color + "`]. Valid gym colors are: "
  fuzzy_match_found = False
  suggestion = ""
  for index, (color, team) in enumerate(GYM_COLOR_TO_CONTROL_TEAM.items()):
    response += color.title() + " or " + team.title()
    if index < len(GYM_COLOR_TO_CONTROL_TEAM) - 1:
      response += ", "

    if not fuzzy_match_found:
      fuzzy_match_found, match = fuzzy_search(gym_color, color.lower(), 1)
      if fuzzy_match_found:
        suggestion = color.lower()

    if not fuzzy_match_found:
      fuzzy_match_found, match = fuzzy_search(gym_color, team.lower(), 2)
      if fuzzy_match_found:
        suggestion = team.lower()

  response += "\n"

  if fuzzy_match_found:
    response += "Did you mean [`" + suggestion.title() + "`]?"
  else:
    response += "Could not find a close match based on given parameter [`" + gym_color + "`]"

  response += "\n"
  return response


def get_embed_color(gym_color):
  gym_color = gym_color.lower()
  response = GYM_CONTROL_COLOR_HEX.get("Unclaimed")

  for key, value in GYM_COLOR_TO_CONTROL_TEAM.items():
    if gym_color == key:
      gym_control = GYM_COLOR_TO_CONTROL_TEAM.get(gym_color)
    elif gym_color == value:
      gym_control = value

  response = GYM_CONTROL_COLOR_HEX.get(gym_control)
  return response
"""----------------------------------------------------------------"""
"""WEATHER"""

def validate_weather_argument(weather):
  weather = weather.lower()
  is_valid = False
  # Search for valid weather type (dictionary keys)
  if weather in WEATHER_TO_OUTPUT.keys():
    response = WEATHER_TO_OUTPUT.get(weather) + " " + WEATHER_TO_EMOJI.get(weather)
    is_valid = True
  else:
    response = format_invalid_weather_message(weather)
  return (is_valid, response)


def format_invalid_weather_message(weather):
  response = "You gave an invalid **Weather Condition** of [`" + weather + "`]. Valid weather conditions are: "
  fuzzy_match_found = False
  suggestion = ""
  for index, (key, _) in enumerate(WEATHER_TO_OUTPUT.items()):
    response += key.title()
    if index < len(WEATHER_TO_OUTPUT) - 1:
      response += ", "

    if not fuzzy_match_found:
      fuzzy_match_found, match = fuzzy_search(weather, key.lower(), 1)
      if fuzzy_match_found:
        suggestion = key.lower()

  response += "\n"

  if fuzzy_match_found:
    response += "Did you mean [`" + suggestion.title() + "`]?"
  else:
    response += "Could not find a close match based on given parameter [`" + weather + "`]"

  response += "\n"
  return response
