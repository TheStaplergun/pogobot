"""
Pokedex class that wraps pokebattler API
"""
import asyncio

from classes import database
from discord.ext import commands

from handlers.pokebattler import pokebattler_api as API

class Pokedex():
    def __init__(self):
        self.pokemon = API.fetch_pokedex()
        self.moves = API.fetch_moves()
        self.raids = API.fetch_raids()

    