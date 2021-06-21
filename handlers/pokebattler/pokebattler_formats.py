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
