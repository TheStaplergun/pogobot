"""
Pokedex class that wraps pokebattler API
"""
import asyncio

from classes import database
from discord.ext import commands

from handlers.pokebattler import pokebattler_api as API
from handlers.pokebattler import pokebattler_calc as PBC

class Pokedex():
    def __init__(self):
        self.update_pokemon_cache()
        self.update_moves_cache()
        self.update_raids_cache()
        self.update_rankings_cache()

    def update_pokemon_cache(self):
        self.pokemon = API.fetch_pokedex()

    def update_moves_cache(self):
        self.moves = API.fetch_moves()

    def update_raids_cache(self):
        self.raids = API.fetch_raids_filtered()

    def update_rankings_cache(self):
        self.rankings = API.fetch_rankings()

    def calculate_players_power_percent(self, player_level, boss_name):
        raid_data = self.raids.get(boss_name)

        name = raid_data.get("pokemon")
        tier = raid_data.get("tier")
        penalty = 1.5 if player_level < 40 else 1
        ranking = self.get_ranking(name, tier)
        if len(ranking) == 0:
            return 1/penalty

        shift_value = 4 - len(ranking)
        index = 0
        if player_level >= 45:
            index = 0
        elif player_level >= 40:
            index = 1
        elif player_level >= 30:
            index = 2
        else:
            index = 3
        index = index - shift_value

        if index < 0:
            return 1/penalty

        weight = 1/(penalty * ranking[index]) * 100

    def get_ranking(self, name, tier):
        pokemon_rankings = self.rankings.get(name)
        return pokemon_rankings.get(tier)
    
    def get_counter_data(self, name, weather):
        API.get_counter_for(name, weather)
    
    def get_move_data(self, name):
        move = next(move for move in self.moves if move.get("moveId") == name)
        return move
