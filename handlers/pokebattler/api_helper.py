from data import formats as F
from pogo_raid_lib import *
tab_count = -1
recurse_limit = 2
def unwind(f, itera):
    global tab_count
    global recurse_limit
    if isinstance(itera, list):
        if tab_count < recurse_limit:
            f.write("--ENTER LIST--\n")
        print_list(f, itera)
        if tab_count < recurse_limit:
            f.write("--EXIT LIST--\n")
    
    if isinstance(itera, dict):
        if tab_count < recurse_limit:
            f.write("--ENTER DICT--\n")
        print_dict(f, itera)
        if tab_count < recurse_limit:
            f.write("--EXIT DICT--\n")
    
    if isinstance(itera, (int, str)):
        to_print = tab_count * "\t"
        if tab_count < recurse_limit + 1:
            f.write(f"{to_print} value: {itera}\n")

def print_dict(f, dictionary):
    global tab_count
    global recurse_limit
    tab_count = tab_count + 1
    for k,v in dictionary.items():
        to_print = tab_count * "\t"
        if tab_count < recurse_limit + 1:
            f.write(f"{to_print}key: {k}\n")
        unwind(f, v)
    tab_count = tab_count - 1

def print_list(f, itera):
    for item in itera:
        unwind(f, item)

root_key_convert = {
    'type':'Type',
    'pokemonId':'Name',
    'stats':'Base Stats',
    'quickMoves':'Fast Moves',
    'cinematicMoves':'Charge Moves',
    'rarity':'Rarity',
    'pokedexHeightM':'Height',
    'pokedexWeightKg':'Weight',
    'parentPokemonId':'Evolves From',
    'heightStdDev':'Height Deviation',
    'weightStdDev':'Weight Deviation',
    'familyId':'Family',
    'candyToEvolve':'Candy To Evolve',
    'thirdMove':'Third Move',
    'movesets':'Movesets',
    'pokedex':'Pokedex',
    'tmMovesets':'TM Movesets',
    'currentMovesets':'Current Movesets',
}

value_from_arg ={
    "name":lambda entry: " ".join(entry.get("pokemonId").split("_")).title(),
    "dex_num":lambda entry: entry.get("pokedex").get("pokemonNum"),
    "form":lambda entry: entry.get("pokedex").get("form"),
    "type":lambda entry: entry.get("type").split("_").pop(2).title(),
    "type2":lambda entry: entry.get("type2").split("_").pop(2).title() if entry.get("type2") else None,
    "stats":lambda entry: entry.get("stats"),
    "rarity":lambda entry: entry.get("rarity").split("_").pop(2).title()
}

def move_to_readable(bot, movenum, move):
    move_category = {
        "move1":"<Fast",
        "move2":"<Charge"
    }.get(movenum)

    move_name = move.get("moveId").replace("_FAST","")
    move_name = move_name.replace("_", " ").title()

    move_type = move.get("type").split("_").pop()
    move_type = bot.get_emoji(F.TYPE_TO_EMOJI.get(move_type))
    return f"{move_type} {move_name} {move_category}"

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


async def get_counter(bot, ctx, tier, name, weather):
    author = ctx.author
    if not tier or (tier.lower() == "mega" and not name):
        await author.send("No pokemon given to get counters for.")
        return

    message_to_send = ""
    is_valid, response = validate_tier(tier)
    if not is_valid:
        message_to_send = f"{message_to_send}{response}\n"

    is_valid, response, suggestion, dex_num = validate_pokemon(name, tier)
    if tier.lower() == "mega" and not name.startswith("Mega ", 0, 5):
        name = "Mega " + name
    
    if not is_valid:
        message_to_send = f"{message_to_send}{response}\nDid you mean **{suggestion}**\n"
        return

    is_valid, response, suggestion = validate_weather_argument(weather)
    if not is_valid:
        message_to_send = f"{message_to_send}{response}\nDid you mean **{suggestion}**"
    
    if not is_valid:
        await author.send(message_to_send)
        return
    
    embed = bot.dex.get_counter_for(name, tier, weather)
    await ctx.send(embed=embed)