import os
import os.path
import sys
import shutil
import math
import errno
import csv
import glob
import re
import random
from PIL import Image, ImageDraw
import struct

INPUT_PATH1 = "C:/Downloads/Starfield/textures/planets/namedplanets"
INPUT_PATH2 = "C:/Downloads/Starfield/textures/planets/houdiniplanets/biomemasks"
OUTPUT_PATH = "c:/Downloads/Starfield/PlanetMaps"


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

        
def ConvertMapProjection(image):
    (width, height) = image.size
    owidth = width * 4
    oheight = width * 2
    newImage = Image.new(mode="RGB", size=(owidth, oheight))

    for y in range(oheight):
        for x in range(owidth):
            theta = 2 * math.pi / owidth * x
            rFactor = max(math.fabs(math.cos(theta)), math.fabs(math.sin(theta)))
            rMax = width/2 / rFactor
            
            if (y <= oheight/2):
                r = rMax * y / width
                ox = int(math.cos(-theta) * r + width/2)
                oy = int(math.sin(-theta) * r + width/2)
                if (ox < 0): ox = 0
                if (oy < 0): oy = 0
                if (ox >= width): ox = width - 1
                if (oy >= width): oy = width - 1

                #if (y > 127):
                #    print("\t\t\t({0}, {1}) => getpix({2}, {3}) {4}:{5}".format(x, y, ox, oy, r, theta))
                
                try:
                    pix = image.getpixel((ox, oy))
                except:
                    print("\t\t\tError on getpix({0}, {1}) {2} : {3}".format(ox, oy, r, theta))
                    
            else:
                r = rMax * (width*2 - y) / width
                ox = int(math.cos(theta) * r + width/2)
                oy = int(math.sin(theta) * r + width/2)
                if (ox < 0): ox = 0
                if (oy < 0): oy = 0
                if (ox >= width): ox = width - 1
                if (oy >= width): oy = width - 1
                
                try:
                    pix = image.getpixel((ox, oy + width))
                except:
                    print("\t\t\tError on getpix({0}, {1}) {2} : {3}".format(ox, oy, r, theta))
                
            newImage.putpixel((x, y), pix)
            
    return newImage


def ParsePlanetTexture(filename, outputPath):
    print("\tConverting {0}...".format(filename))

    image = Image.open(filename)

    convImage = ConvertMapProjection(image)

    newName = os.path.basename(filename).replace("_color", "")
    newFilename = outputPath + "/" + newName
    convImage.save(newFilename)
    
    return


def ParsePlanetTextures(inputPath, outputPath):

    os.chdir(inputPath)
    print("Finding planet textures in {0}...".format(inputPath))

    for f in glob.glob("*_color.png"):
        ParsePlanetTexture(f, outputPath)

    for root, dirs, files in os.walk("."):
        for path in dirs:
            newPath = os.path.join(inputPath, path)
            ParsePlanetTextures(newPath, outputPath)
    
    return


mkdir_p(OUTPUT_PATH)

# ParsePlanetTextures(INPUT_PATH1, OUTPUT_PATH)
ParsePlanetTextures(INPUT_PATH2, OUTPUT_PATH)
