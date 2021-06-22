import json
import requests

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
import discord

import handlers.pokebattler.api_helper as AH

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

def add_tier_to_raid_data(raid, tier):
    raid.update({"tier":tier})
    return raid

def filter_current_raids(raids):
    return {AH.format_pokemon_name(raid.get("pokemon")):add_tier_to_raid_data(raid, tier.get("tier"))
                for tier in raids.get("tiers") 
                    if current_tier_valid(tier.get("tier"))
                        for raid in tier.get("raids")}

def fetch_raids_filtered():
    return filter_current_raids(fetch_raids())

def link_builder(name, tier, weather):
    return f"https://fight.pokebattler.com/raids/defenders/{name}/levels/{tier}/attackers/levels/40/strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC"
def get_move_data(name):
    move = next((move for move in fetch_moves() if move.get("moveId") == name), None)
    return move
def get_counter_for(name, tier, weather):
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
        print(moves)
        for movenum, move in moves.items():
            moves[movenum] = get_move_data(move)
        defender["byMove"] = moves
    return result

with open("./output", "w+") as f:
    AH.unwind(f, get_counter_for("REGIGIGAS","RAID_LEVEL_5","CLEAR"))