import os
import sys
import shutil
import math
import errno
import csv
import os.path
import re
import random
from PIL import Image, ImageDraw, ImageFont


INPUT_TEXTURE = "c:/Downloads/Starfield/PlanetMapsOrig/jupiter.jpg"
OUTPUT_PATH = "c:/Downloads/Starfield/TestProj"


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def ConvertStarfieldToAzimuth(inputTexture):
    outputFilename1 = OUTPUT_PATH + "/azimuth1-" + os.path.basename(inputTexture)
    outputFilename2 = OUTPUT_PATH + "/azimuth2-" + os.path.basename(inputTexture)

    image = Image.open(inputTexture)
    (width, height) = image.size

    owidth = width
    oheight = width

    aImage1 = Image.new(image.mode, (owidth, oheight))
    aImage2 = Image.new(image.mode, (owidth, oheight))

    for y in range(0, width):
        for x in range(0, width):
            y1 = y + width

            pix1 = image.getpixel((x, y))
            pix2 = image.getpixel((x, y1))

            xx = (float(x) - width/2)/(width/2)
            yy = (float(y) - width/2)/(width/2)

            uu = xx * math.sqrt(1 - yy*yy/2)
            vv = yy * math.sqrt(1 - xx*xx/2)

            u = int((uu + 1) * width/2)
            v = int((vv + 1) * width/2)

            if (y % 100 == 0 and x % 100 == 0):
                print("\t({0},{1}) => ({2},{3}) => ({4}, {5})) => ({6}, {7})".format(x, y, xx, yy, uu, vv, u, v))

            aImage1.putpixel((u, v), pix1)
            aImage2.putpixel((u, v), pix2)

    aImage1.save(outputFilename1)
    aImage2.save(outputFilename2)
    
    return


def ConvertStarfieldToSquircircle(inputTexture):
    outputFilename1 = OUTPUT_PATH + "/squircle1-" + os.path.basename(inputTexture)
    outputFilename2 = OUTPUT_PATH + "/squircle2-" + os.path.basename(inputTexture)

    image = Image.open(inputTexture)
    (width, height) = image.size

    owidth = width
    oheight = width

    aImage1 = Image.new(image.mode, (owidth, oheight))
    aImage2 = Image.new(image.mode, (owidth, oheight))

    for y in range(0, width):
        for x in range(0, width):
            y1 = y + width

            pix1 = image.getpixel((x, y))
            pix2 = image.getpixel((x, y1))

            xx = (float(x) - width/2)/(width/2)
            yy = (float(y) - width/2)/(width/2)

            r2 = math.sqrt(xx*xx + yy*yy)
            if (r2 < 0.00001): continue
            
            c = math.sqrt(xx*xx + yy*yy - xx*xx*yy*yy) / r2
            uu = xx * c
            vv = yy * c

            u = int((uu + 1) * width/2)
            v = int((vv + 1) * width/2)

            if (y % 100 == 0 and x % 100 == 0):
                print("\t({0},{1}) => ({2},{3}) => ({4}, {5})) => ({6}, {7})".format(x, y, xx, yy, uu, vv, u, v))

            aImage1.putpixel((u, v), pix1)
            aImage2.putpixel((u, v), pix2)

    aImage1.save(outputFilename1)
    aImage2.save(outputFilename2)
    
    return
        
mkdir_p(OUTPUT_PATH)
# ConvertStarfieldToAzimuth(INPUT_TEXTURE)
ConvertStarfieldToSquircircle(INPUT_TEXTURE)
