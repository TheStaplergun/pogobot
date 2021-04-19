import cv2 as cv
from pytesseract import pytesseract
import re
import data.pokemon as dex
from fuzzywuzzy import fuzz
# Defining paths to tesseract.exe
# and the image we would be using
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
image_path = r"handlers\timburr.png"

pytesseract.tesseract_cmd = path_to_tesseract

def image_dimensions(image):
    return len(image), len(image[0])

def get_name_height(y_length):
    height_of_words = (550-410) / y_length
    return height_of_words * y_length

def start_of_name(y_length):
    baseline = 390/1560
    return int(baseline * y_length)

def get_region_to_search(y_length):
    start_at = start_of_name(y_dim)
    end_at = start_at + get_name_height(y_dim)
    return int(start_at), int(end_at)

def get_start_offset(x_width):
    baseline = 50/(720/2)
    print(baseline)
    converted_width = x_width/2 * baseline
    print(converted_width)
    return int(x_width/2 - converted_width)

def set_up_image(image, adaptive, blur):
    if adaptive:
        image = cv.adaptiveThreshold(image,255,cv.ADAPTIVE_THRESH_MEAN_C,cv.THRESH_BINARY,11,2)

    if blur:
        image = cv.medianBlur(image, blur)

    return image

process_list = [
    (False, 0),
    (False, 3),
    (False, 5),
    (True, 0),
    (True, 3),
    (True, 5)
]
def find_name(image):
    # Opening the image & storing it in an image object
    base_image = cv.imread(image)
    gray_image = cv.cvtColor(base_image, cv.COLOR_RGB2GRAY)
    y_dim, x_dim = image_dimensions(base_image)
    x_offset_start = get_start_offset(x_dim)
    x_offset = x_offset_start

    results = {}
    best_ratio = 0
    for pair in process_list:
        image_to_use = set_up_image(gray_image, pair[0], pair[1])
        latest_result, ratio = image_parse(image_to_use, y_dim, x_offset)
        #if ratio > best_ratio:
        #    best_ratio = ratio
        if not results.get(latest_result):
            results.update({latest_result:1})
        else:
            results[latest_result] += 1
        if ratio > 95:
            break
    cv.waitKey(0)
    highest = 0
    resulting_pokemon = None
    print(results)
    for name, count in results.items():
        if count > highest:
            highest = count
            resulting_pokemon = name
    print(resulting_pokemon, best_ratio)


def image_parse(image, y_dim, x_offset):
    answer = None
    region_to_show = None
    #suggestion = None
    while x_offset > 1 and not answer:
        region_to_show = image[int(y_dim * 0.20):int(y_dim * 0.4), x_offset:-x_offset]
        text = pytesseract.image_to_string(region_to_show, config='--psm 4 -l eng -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        best_ratio = 0
        #text = text.split('\n')[0]
        if re.search(r'\b', text):
            #print(text)
            text = re.sub(r'[^a-zA-Z]', ' ', text)
            #print(text)

            #cv.imshow("test {}".format(x_offset), region_to_show)
            #print(text.split())
            for thing in text.split():
                if len(thing) < 3 or len(thing) > 12:
                    continue
                if thing in dex.DEX_FOR_IMAGE_PARSE:
                    return thing, 100
                for dex_entry in dex.DEX_FOR_IMAGE_PARSE:
                    fuzz_ratio = fuzz.ratio(dex_entry, thing)
                    if fuzz_ratio > best_ratio and fuzz_ratio > 75:
                        best_ratio = fuzz_ratio
                        suggestion = dex_entry
                        cv.imshow("{} {}".format(dex_entry, fuzz_ratio), region_to_show)

                        print("New best: ", suggestion)
                    #if best_ratio > 90:
                        #return dex_entry
        x_offset-=10

                #print(thing)
    #return suggestion
        #if re.search(r'\w', text):
        #    outputs.append(text)
    return None, 0
if __name__ == "__main__":
    find_name(image_path)
