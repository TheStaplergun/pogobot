import json
import requests

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
import discord

import api_helper as AH

def retrieve_data_from_api(link, params):
    sess = CacheControl(requests.Session(),
                        cache=FileCache('.webcache'))
    if params:
        sess.params = params
    session = sess.get(link)
    return session.json()

def fetch_pokedex():
    data = retrieve_data_from_api("https://fight.pokebattler.com/pokemon", None)
    return data['pokemon']

def fetch_raids():
    data = retrieve_data_from_api("https://fight.pokebattler.com/raids", None)
    return data

def fetch_moves():
    data = retrieve_data_from_api("https://fight.pokebattler.com/moves", None)
    return data['move']

def fetch_rankings():
    data = retrieve_data_from_api("https://static.pokebattler.com/raidSummaries.json", None)

valid_tiers = [
    "RAID_LEVEL_1",
    "RAID_LEVEL_3",
    "RAID_LEVEL_4_5",
    "RAID_LEVEL_5",
    "RAID_LEVEL_6",
    "RAID_LEVEL_MEGA"
]
def current_tier_valid(tier):
    return tier in valid_tiers

form_converter = {
    "ALOLA":"Alolan",
    "GALARIAN":"Galarian",
    "ORIGIN":"Origin",
}

def format_pokemon_name(name):
    name = name.split("_")
    form = None
    if "FORM" in name:
        name.pop(-1)
        form = form_converter.get(name.pop(-1))
        name.insert(0, form)

    if "MEGA" in name:
        name.insert(0, name.pop(-1))

    name = " ".join(name).title()
    return name

def add_tier_to_raid_data(raid, tier):
    raid.update({"tier":tier})
    return raid

def filter_current_raids(raids):
    return {format_pokemon_name(raid.get("pokemon")):add_tier_to_raid_data(raid, tier.get("tier"))
                for tier in raids.get("tiers") 
                    if current_tier_valid(tier.get("tier"))
                        for raid in tier.get("raids")}

def fetch_raids_filtered():
    return filter_current_raids(fetch_raids())

"""CLEAR,
RAINY,
PARTLY_CLOUDY,
OVERCAST,
WINDY,
SNOW,
FOG"""
def get_move_data():
    pass
def link_builder(name, tier, weather):
    return f"https://fight.pokebattler.com/raids/defenders/{name}/levels/{tier}/attackers/levels/40/strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC"

def get_counter_for(dex, name, tier, weather):
    params = {
        b"sort":b"ESTIMATOR",
        b"weatherCondition":f"{weather}".encode(),
        b"dodgeStrategy":b"DODGE_REACTION_TIME",
        b"aggregation":b"AVERAGE",
        b"includeLegendary":b"true",
        b"includeShadow":b"true",
        b"includeMegas":b"true",
        b"attackerTypes":b"POKEMON_TYPE_ALL",
    }
    result = retrieve_data_from_api(link_builder(name, tier, weather), params)
    result = result.get("attackers").pop().get("randomMove").get("defenders")[-1:-7:-1]
    for defender in result:
        moves = defender.get("byMove").pop()
        moves.pop("result")
        for movenum, move in moves:
            moves[movenum] = dex.get_move_data(move)
        defender["byMove"] = moves
    return result
