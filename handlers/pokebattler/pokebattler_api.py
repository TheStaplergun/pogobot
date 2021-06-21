import json
import requests

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
import discord

def fetch_pokedex():
    sess = CacheControl(requests.Session(),
                        cache=FileCache('.webcache'))

    pokebattler_counter_link = "https://fight.pokebattler.com/pokemon"
    session = sess.get(pokebattler_counter_link)
    data = json.loads(session.text)
    return data['pokemon']

def fetch_raids():
    sess = CacheControl(requests.Session(),
                        cache=FileCache('.webcache'))

    pokebattler_counter_link = "https://fight.pokebattler.com/raids"
    session = sess.get(pokebattler_counter_link)
    data = json.loads(session.text)
    return data
    #return data['raids']


tab_count = 0

def print_all_keys(f, itera):
    global tab_count
    if isinstance(itera, list):
        f.write("--ENTER LIST--\n")
        print_list(f, itera)
        f.write("--EXIT LIST--\n")
    
    if isinstance(itera, dict):
        f.write("--ENTER DICT--\n")
        print_dict(f, itera)
        f.write("--EXIT DICT--\n")
    
    if isinstance(itera, (int, str)):
        to_print = tab_count * "\t"
        f.write(f"{to_print} value: {itera}\n")

def print_dict(f, dictionary):
    global tab_count
    tab_count = tab_count + 1
    for k,v in dictionary.items():
        to_print = tab_count * "\t"
        f.write(f"{to_print}key: {k}\n")
        print_all_keys(f, v)
    tab_count = tab_count - 1

def print_list(f, itera):
    for item in itera:
        print_all_keys(f, item)

raids = fetch_raids()
with open("./keys", "w+") as f:
    print_all_keys(f, raids)