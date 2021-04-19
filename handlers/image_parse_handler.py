import numpy as np
import cv2 as cv
import pytesseract
#path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
image_path = r"ponyta.jpg"
kernel = np.ones((2,2),np.uint8)
# load image
img = cv.imread(image_path, 0)

img = cv.medianBlur(img,5)
#th2 = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_MEAN_C,cv.THRESH_BINARY,11,2)
th3 = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY,11,2)
# Providing the tesseract executable
# location to pytesseract library
#pytesseract.tesseract_cmd = path_to_tesseract

# Passing the image object to image_to_string() function
# This function will extract the text from the image
#text = pytesseract.image_to_string(th3)

# Displaying the extracted text
#for line in text:#.split('\n'):
    #if re.match(r'.*\w+', line):
#print(text)

# Convert BGR to HSV
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

# define range of black color in HSV
lower_val = np.array([0,0,0])
upper_val = np.array([179,100,130])

# Threshold the HSV image to get only black colors
mask = cv.inRange(hsv, lower_val, upper_val)

# Bitwise-AND mask and original image
res = cv.bitwise_and(img,img, mask= mask)
# invert the mask to get black letters on white background
res2 = cv.bitwise_not(mask)
region_to_show = img[411:515, 0:-1]
# display image
cv.imshow("img", region_to_show)
cv.imshow("img2", res2)
cv.waitKey(0)
cv.destroyAllWindows()

26.5
33.5
