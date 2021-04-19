import os
import pokemon_list

for name in pokemon_list.DEX_FOR_IMAGE_PARSE:
  os.makedirs("training_images/{}".format(name), exist_ok=True)
