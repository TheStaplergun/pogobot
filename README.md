# Pokemon Go Raid hosting bot
This is yet another implementation of a raid hosting framework for use within the r/pokemongo discord. It can be hosted on a raspberry pi or any VPS.

## Requirements

### Python 3
This bot runs on python3

### discord.py module

Installation instructions and documentation for the entire discord.py library can be found at https://pypi.org/project/discord.py/

### Fuzzywuzzy module

```pip install fuzzywuzzy```

This is used to attempt to provide corrections for typos and suggest it back to the hosting user in a DM.

## Use
### Bot Hosting
Host the bot and restrict the channels it can see on discord. This will be changed at a later date to allow for setting it dynamically. It will respond to any user and post the raid message in the channel it sees the command in.

### Posting a raid
The hosting user would type the following in the preferred raid channel:

`<command prefix>post_raid <tier> <pokemon name> <gym team control/color> <weather type> <invite slots avaialable> <time to start (minutes)> <time to end (minutes)>`

An example of this would be:

`$post_raid T5 Giratina-Altered Red(Or you can type valor) Sunny 5 0 10`

## Notes
Any part that the user gets wrong will be pointed out specifically and sent to the raid host in a DM, along with valid options pulled directly from what it uses to check again.

For the pokemon name, team name, and weather, it will attempt to perform a fuzzy search and suggest a correction. This correction along with the rest of the command that was given will be sent back to the user so they can copy and paste it back into the channel after verifying.
