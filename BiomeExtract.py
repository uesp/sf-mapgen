# Extracts images from Starfield's planetdata/boimemaps/ files
import os
import sys
import shutil
import math
import errno
import csv
import os.path
import re
import random
from PIL import Image, ImageDraw
import struct


INPUT_PATH = "c:/Downloads/Starfield/planetdata/biomemaps"
OUTPUT_PATH = "c:/Downloads/Starfield/BiomeMaps"

SAVE_IMAGES = True

g_ColorMap = {}
g_IndexMap = {}
g_Csv = []


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def MergeDictionaries(d1, d2):

    for k, v in d2.iteritems():
        if (k in d1):
            d1[k] += v
        else:
            d1[k] = v
    


def AnalyzeIndexData(size, data):
    stats = {}

    m = {}

    for i in range(size):
        d = ord(data[i])
        if (not d in m): m[d] = 0
        m[d] += 1

    sys.stdout.write("\t\tCount={0}: ".format(len(m)))

    for k, v in m.iteritems():
        sys.stdout.write("{0}={1}, ".format(k, v))
        
    print("")
    stats['map'] = m
    return stats


def AnalyzeColorData(size, data):
    stats = {}

    m = {}

    for i in range(size):
        d1 = ord(data[i*4])
        d2 = ord(data[i*4+1])
        d3 = ord(data[i*4+2])
        d4 = ord(data[i*4+3])
        d = d1 + (d2*256) + (d3*256*256) + (d4*256*256*256)

        if (not d in m): m[d] = 0
        m[d] += 1

    sys.stdout.write("\t\tCount={0}: ".format(len(m)))

    for k, v in m.iteritems():
        sys.stdout.write("{0}={1}, ".format(hex(k), v))
        
    print("")
    stats['map'] = m
    return stats


def ConvertMapProjection(width, height, image1, image2):
    owidth = width*4
    oheight = height*2
    newImage = Image.new(mode="RGB", size=(owidth, oheight))

    for y in range(oheight):
        for x in range(owidth):
            theta = 2 * math.pi * x / owidth
            rFactor = max(math.fabs(math.cos(theta)), math.fabs(math.sin(theta)))
            rMax = width/2 / rFactor
            
            if (y <= oheight/2):
                r = rMax * y / (oheight/2)
                # ox = int(math.cos(theta) * r + width/2)
                # oy = int(math.sin(theta) * r + height/2)
                ox = int(math.cos(-theta) * r + width/2)
                oy = int(math.sin(-theta) * r + height/2)
                if (ox < 0): ox = 0
                if (oy < 0): oy = 0
                if (ox >= width): ox = width - 1
                if (oy >= height): oy = height - 1

                #if (y > 127):
                #    print("\t\t\t({0}, {1}) => getpix({2}, {3}) {4}:{5}".format(x, y, ox, oy, r, theta))
                
                try:
                    pix = image1.getpixel((ox, oy))
                except:
                    print("\t\t\tError on getpix({0}, {1}) {2} : {3}".format(ox, oy, r, theta))
                    
            else:
                r = rMax * (oheight - y) / (oheight/2)
                # ox = int(math.cos(-theta + math.pi) * r + width/2)
                # oy = int(math.sin(-theta + math.pi) * r + height/2)
                ox = int(math.cos(theta + math.pi) * r + width/2)
                oy = int(math.sin(theta + math.pi) * r + height/2)
                if (ox < 0): ox = 0
                if (oy < 0): oy = 0
                if (ox >= width): ox = width - 1
                if (oy >= height): oy = height - 1
                
                try:
                    pix = image2.getpixel((ox, oy))
                except:
                    print("\t\t\tError on getpix({0}, {1}) {2} : {3}".format(ox, oy, r, theta))
                
            newImage.putpixel((x, y), pix)
            
    return newImage


def CreateImageFromBytesRGBX(width, height, data):
    image = Image.new(mode="RGB", size=(width, height))

    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 4
            r = ord(data[i])
            g = ord(data[i+1])
            b = ord(data[i+2])
            image.putpixel((x,y), (b, g, r, 0))
            
    return image


def CreateImageFromBytesIndex(width, height, data):
    image = Image.new(mode="RGB", size=(width, height))

    for y in range(height):
        for x in range(width):
            i = (y * width + x)
            r = (ord(data[i]) % 80) * 32
            g = (int(ord(data[i]) - 80)) * 32
            b = 0
            if (r > 255): r = 255
            if (g > 255): g = 255
            image.putpixel((x,y), (b, g, r, 0))
            
    return image


def ReadBiomeIndexData(f):
    data = {}

    size = struct.unpack('i', f.read(4))[0]

    data['data'] = f.read(size)

    data['size'] = size
    return data        


def ReadBiomeColorData(f):
    data = {}

    width = struct.unpack('i', f.read(4))[0]
    height = struct.unpack('i', f.read(4))[0]
    size = struct.unpack('i', f.read(4))[0]

    data['data'] = f.read(size * 4)

    data['width'] = width
    data['height'] = height
    data['size'] = size
    return data


def ParseBiomeFile(filename, outputPath):
    global g_ColorMap
    global g_IndexMap
    
    print("\tParsing biome file {0}...".format(filename))
    
    f = open(filename, 'rb')

    size = os.path.getsize(filename)

    u1 = struct.unpack('h', f.read(2))[0]
    colorCount = struct.unpack('i', f.read(4))[0]
    colors = []

    for i in range(colorCount):
        colors.append(struct.unpack('i', f.read(4))[0])
        
    flags = struct.unpack('i', f.read(4))[0]

    print("\t\t{0}, {1}, {2}, {3}, {4}".format(os.path.basename(filename), size, u1, colorCount, flags))

    colorData1 = ReadBiomeColorData(f)
    indexData1 = ReadBiomeIndexData(f)
    colorData2 = ReadBiomeColorData(f)
    indexData2 = ReadBiomeIndexData(f)

    if (f.tell() != size):
        print("\t\tWarning: {0} bytes left over at end of file!".format(size - f.tell()))

    f.close()

    if (SAVE_IMAGES):
        colorImage1 = CreateImageFromBytesRGBX(colorData1['width'], colorData1['height'], colorData1['data'])
        colorImage2 = CreateImageFromBytesRGBX(colorData2['width'], colorData2['height'], colorData2['data'])
        combColorImage = ConvertMapProjection(colorData1['width'], colorData1['height'], colorImage1, colorImage2)

        indexImage1 = CreateImageFromBytesIndex(colorData1['width'], colorData1['height'], indexData1['data'])
        indexImage2 = CreateImageFromBytesIndex(colorData1['width'], colorData1['height'], indexData2['data'])
        combIndexImage = ConvertMapProjection(colorData1['width'], colorData1['height'], indexImage1, indexImage2)

        path = outputPath + "/" + os.path.basename(filename)
        mkdir_p(path)

        colorFile1 = path + "/colorImage1.png"
        colorFile2 = path + "/colorImage2.png"
        combColorFile = path + "/combImage.png"
        indexFile1 = path + "/indexImage1.png"
        indexFile2 = path + "/indexImage2.png"
        combIndexFile = path + "/indexImage.png"

        colorImage1.save(colorFile1)
        colorImage2.save(colorFile2)
        combColorImage.save(combColorFile)
        indexImage1.save(indexFile1)
        indexImage2.save(indexFile2)
        combIndexImage.save(combIndexFile)

    colorStats1 = AnalyzeColorData(colorData1['size'], colorData1['data'])
    colorStats2 = AnalyzeColorData(colorData2['size'], colorData2['data'])
    indexStats1 = AnalyzeIndexData(indexData1['size'], indexData1['data'])
    indexStats2 = AnalyzeIndexData(indexData2['size'], indexData2['data'])

    colorStats = {}
    indexStats = {}
    MergeDictionaries(colorStats, colorStats1['map'])
    MergeDictionaries(colorStats, colorStats2['map'])
    MergeDictionaries(indexStats, indexStats1['map'])
    MergeDictionaries(indexStats, indexStats2['map'])

    MergeDictionaries(g_ColorMap, colorStats)
    MergeDictionaries(g_IndexMap, indexStats)

    # g_Csv.append("Planet, Filesize, Header, ColorCount1, Flags, ColorCount1, IndexCount, Colors, Indexes")
    row = "\"" + os.path.basename(filename) + "\""
    row += "," + str(size)
    row += "," + str(u1)
    row += "," + str(colorCount)
    row += "," + str(flags)
    row += "," + str(len(colorStats))
    row += "," + str(len(indexStats))

    s = ""
    
    for key in colorStats:
        s += hex(key) + ": " + str(colorStats[key]) + ", "
    
    row += ",\"{" + str(s) + "}\""
    row += ",\"" + str(indexStats) + "\""
    
    g_Csv.append(row)
    print(row)
    
    return True


def ParseBiomeFiles(inputPath, outputPath):

    mkdir_p(outputPath)
    fileCount = 0

    g_Csv.append("Planet, Filesize, Header, ColorCount1, U4, ColorCount1, IndexCount, Colors, Indexes")
    
    for filename in os.listdir(inputPath):
        f = os.path.join(inputPath, filename)
        
        if os.path.isfile(f):
            fileCount += 1
            ParseBiomeFile(f, outputPath)

    print("Found {0} biome files!".format(fileCount))


    print("Color Stats:")
    
    for k in g_ColorMap:
        print("\t{0} : {1}".format(hex(k), g_ColorMap[k]))

    print("Index Stats:")
    
    for k in g_IndexMap:
        print("\t{0} : {1}".format(k, g_IndexMap[k]))

    with open(outputPath + "/biomeinfo.csv", "w") as f:
        f.write("\n".join(g_Csv))
    

ParseBiomeFiles(INPUT_PATH, OUTPUT_PATH)     
