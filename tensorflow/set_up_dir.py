import os
import pokemon_list
import cv2 as cv
from os import walk

from pokemon import NATIONAL_DEX, MEGA_DEX, ALOLAN_DEX, GALARIAN_DEX, ALTERNATE_FORME_DEX

relevant_dex = {
    "national":NATIONAL_DEX,
    "mega":MEGA_DEX,
    "alola":ALOLAN_DEX,
    "galar":GALARIAN_DEX,
    "alternate":ALTERNATE_FORME_DEX
}

colors = {
    "white":[255,255,255,255],
    "black":[0,0,0,255],
    "green":[126,208,136,255],
    "blue":[243,200,83,255],
    "pink":[179,130,236,255],
    "orange":[66,115,255,255]
}

masks = {
    "left-half":lambda x,y: (0, int(x/2), 0, y),
    "right-half":lambda x,y: (int(x/2), x, 0, y),
    "top-half":lambda x,y: (0, x, 0, int(y*0.75)),
    "bottom-half":lambda x,y: (0, x, int(y*0.75), y)
}



def recolor_image(image, color):
    new_image = image.copy()
    # Get transparency mask
    transparency_mask = new_image[:,:,3] == 0
    # Set transparency color
    new_image[transparency_mask] = colors.get(color)
    # Remove alpha layer
    new_image = cv.cvtColor(new_image, cv.COLOR_BGRA2BGR)
    return new_image

def mask_half(image, section):
    half_image = image.copy()
    # x is the second dimension measurement here
    x = len(image[0])
    y = len(image)
    x1, x2, y1, y2 = masks.get(section)(x,y)
    # Slice out the half we want
    half_image = half_image[y1:y2, x1:x2]
    return half_image

# offsets = {
#     "blank-pokemon-stats-screen.jpg":-110,
#     "empty-catch-screen.png":0,
#     "empty-raid-gym.png":150
# }

#def overlay_image(image, background, offset):


def make_and_convert():
    end_path = "./training"
    mypath = "./images_to_move"
    counter = 0

    # helper_images = {}
    # helper_images.update({"blank-pokemon-stats-screen.jpg":cv.imread("{}/HELPERS/blank-pokemon-stats-screen.jpg".format(mypath))})
    # helper_images.update({"empty-catch-screen.png":cv.imread("{}/HELPERS/empty-catch-screen.png".format(mypath))})
    # helper_images.update({"empty-raid-gym.png":cv.imread("{}/HELPERS/empty-catch-screen.png".format(mypath))})

    for (dirpath, dirnames, filenames) in walk(mypath):
        for filename in filenames:
            if "shiny" in filenames or \
                "pokemon" not in filename:
                continue


            split_file_name = filename.split('_')
            dex_number = split_file_name[2]
            special_category = split_file_name[3]
            if ".png" in special_category:
                special_category = special_category.split(".")[0]

            special_dex_value = "{}_{}".format(dex_number, special_category)
            current_file_name = "{}/{}".format(dirpath, filename)

            current_image = cv.imread(current_file_name, cv.IMREAD_UNCHANGED)

            image_list = {}
            for color in colors.keys():
                image_list[color] = recolor_image(current_image, color)

            image_to_crop = image_list["white"]

            for section in masks.keys():
                image_list[section] = mask_half(image_to_crop, section)

            for region, dex in relevant_dex.items():
                if special_dex_value not in dex.keys():
                    continue

                pokemon_name = dex.get(special_dex_value)
                dir_name = pokemon_name
                if region == "mega":
                    dir_name = "Mega {}".format(dir_name)

                new_dir_path = "{}/{}".format(end_path, dir_name)
                try:
                    os.mkdir(new_dir_path)
                except OSError as error:
                    print("Directory [{}] already exists. Ignoring.".format(dir_name))

                #os.rename(current_file_name, "{}/{}/{}".format(dirpath, dir_name, filename))


                for modification, image in image_list.items():
                    new_filename = "{}_{}.jpg".format(filename, modification)
                    new_file_path = "{}/{}".format(new_dir_path, new_filename)

                    cv.imwrite(new_file_path, image)



            # if special_dex_value in dex.MEGA_DEX.keys():
            #     dir_name = "Mega {}".format(dex.ALTERNATE_FORME_DEX.get(special_dex_value))
            #     os.mkdir(dir_name)
            #     os.rename(current_file_name, "{}/{}/{}".format(dirpath, dir_name, filename))
            #     continue

            # if special_dex_value in dex.ALOLAN_DEX.keys():
            #     dir_name = dex.ALOLAN_DEX.get(special_dex_value)
            #     os.mkdir(dir_name)
            #     os.rename(current_file_name, "{}/{}/{}".format(dirpath, dir_name, filename))
            #     continue

            # if special_dex_value in dex.GALARIAN_DEX.keys():
            #     dir_name = dex.GALARIAN_DEX.get(special_dex_value)
            #     os.mkdir(dir_name)
            #     os.rename(current_file_name, "{}/{}/{}".format(dirpath, dir_name, filename))
            #     continue

            # if special_dex_value in dex.ALTERNATE_FORME_DEX.keys():
            #     dir_name = dex.ALTERNATE_FORME_DEX.get(special_dex_value)
            #     os.mkdir(dir_name)
            #     os.rename(current_file_name, "{}/{}/{}".format(dirpath, dir_name, filename))
            #     continue

            #counter += 1

            #if counter == 2:
                #return

if __name__ == "__main__":
    make_and_convert()
