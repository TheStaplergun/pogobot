import json
import requests

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
import discord

  
# Opening JSON file
def fetch_pokedex():
    sess = CacheControl(requests.Session(),
                    cache=FileCache('.webcache'))

    pokebattler_counter_link = "https://fight.pokebattler.com/pokemon"
    session = sess.get(pokebattler_counter_link)
    data = json.loads(session.text)
    return data['pokemon']



def handle_get_pokemon_by_number(dex_number=0):
    if dex_number < 0 or dex_number > 809:
        return

    pokedex = fetch_pokedex()

    for entry in pokedex:
        pokedex_data = entry.get("pokedex")
        if pokedex_data.get("pokemonNum") == dex_number:
            print(entry)
            

def handle_get_pokemon_by_name(tier="None", name="None"):
    pokedex = fetch_pokedex()

    for entry in pokedex:
        entry_name = entry.get("pokemonId")
        if entry_name == name:
            return entry

async def retrieve_pokedex_data(bot, ctx, arg1="None", arg2="None"):
    print(arg1, arg2)
    result = None
    if arg1 == "Mega" and not arg2 == "None":
        result = handle_get_pokemon_by_name(arg1, arg2)
    if not result:
        result = handle_get_pokemon_by_name(None, arg1)
    
    if arg1.isnumeric():
        result = handle_get_pokemon_by_number(int(arg1))
    
    if not result:
        return
    embed = discord.Embed(title=result.get("pokemonId"))
    for key, value in result.items():
        if key == "pokemonId":
            continue
        embed.add_field(name=key, value=value)
    
    await ctx.send(embed=embed)
