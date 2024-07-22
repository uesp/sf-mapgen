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


WORLD_CSV = "c:/Downloads/Starfield/Maps/worlds.csv"
PLANET_CSV = "c:/Downloads/Starfield/Maps/planets.csv"
TEXTURE_PATH = "c:/Downloads/Starfield/PlanetMaps"
BIOME_PATH = "c:/Downloads/Starfield/BiomeMaps"
OUTPUT_PATH = "c:/Downloads/Starfield/MapTiles"

g_Worlds = []
g_Planets = []
g_WorldIdMap = {}
g_PlanetIdMap = {}
g_PlanetNameMap = {}
g_CreatedPlanets = {}

SAVE_IMAGES = False

MAX_ZOOM = 4
MIN_ZOOM = 0
BACKGROUND_COLOR = (0,0,0)
TILE_SIZE = 256
IMAGE_WIDTH = 4096
IMAGE_HEIGHT = 4096

DB_NEXT_WORLD_ID = 1000
SYSTEM_SIZE = 1000


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def MakeMapTileFilename(OutputPath, MapName, LayerName, X, Y, Zoom):
    return "{0}/{1}/leaflet/{5}/zoom{4}/{1}-{2}-{3}.jpg".format(OutputPath, MapName, X, Y, Zoom, LayerName)


def MakeNiceMapName(mapName):
    niceName = mapName.lower()
    niceName = niceName.strip()
    niceName = niceName.replace(' ', '')
    niceName = niceName.replace('\'', '')
    niceName = niceName.replace('"', '')
    return niceName


def LoadCsv(filename):
    data = []
    
    with open(filename, 'rb') as f:
        reader = csv.reader(f)
        
        for row in reader:
            data.append(row)

    print "\tLoaded {0} rows from {1}!".format(len(data), filename)  
    return data


def MakeWorldIdMap():
    global g_Worlds
    global g_WorldIdMap
    
    g_Worlds = LoadCsv(WORLD_CSV)

    for row in g_Worlds:
        id = int(row[1])
        name = row[0]
        g_WorldIdMap[name] = id

    return


def MakePlanetIdMap():
    global g_Planets
    global g_PlanetIdMap
    global g_PlanetNameMap
    
    g_Planets = LoadCsv(PLANET_CSV)

    for row in g_Planets:
        id = int(row[1])
        name = MakeNiceMapName(row[0])
        g_PlanetIdMap[name] = id
        g_PlanetNameMap[name] = row[0]

    return


def CheckPlanetNames():
    global g_Planets
    global g_Worlds
    global g_WorldIdMap

    tmpMap = {}

    for row in g_Planets:
        name = row[0]
        niceName = MakeNiceMapName(name)
        tmpMap[niceName] = 1

        if (name in g_WorldIdMap):
            print("Warning: Planet {0} conflicts with world name!".format(name))

        if (niceName in g_WorldIdMap):
            print("Warning: Planet {0} conflicts with world name!".format(niceName))

    if (len(tmpMap) != len(g_Planets)):
        print("Warning: Planet name overlap!")
        
    return


def EscapeSql(sql):
    return sql.replace("'", "\\'")


def CreatePlanetWorldDB(planetName, mapName):
    global DB_NEXT_WORLD_ID
    global g_PlanetIdMap
    
    sql = ""

    if (mapName == ""): mapName = planetName
    mapDisplayName = planetName

    mapName = MakeNiceMapName(mapName)

    ID = DB_NEXT_WORLD_ID
    DB_NEXT_WORLD_ID += 1

    posLeft = 0
    posTop = SYSTEM_SIZE
    posRight = SYSTEM_SIZE
    posBottom = 0
        
    mapParentID = -1
    
    if (mapName in g_PlanetIdMap):
        mapParentID = g_PlanetIdMap[mapName]
    else:
        print("\t\tWarning: Missing parent world for planet {0}!".format(mapName))
        
    tilesX = pow(2, MAX_ZOOM)
    tilesY = pow(2, MAX_ZOOM)
    defaultZoom = MAX_ZOOM - 1
    maxTilesX = pow(2, MAX_ZOOM)
    maxTilesY = pow(2, MAX_ZOOM)
    displayData = '{"hasGrid":false,"hasCellResource":false,"layers":[{"name":"default"},{"name":"biome1"},{"name":"biome2"}]}';
    mapDisplayName = EscapeSql(mapDisplayName)

    sql = "INSERT INTO world(id, revisionId, parentId, name, displayName, minZoom, maxZoom, zoomOffset, posLeft, posTop, posRight, posBottom, enabled, tilesX, tilesY, defaultZoom, maxTilesX, maxTilesY, displayData) VALUES('{0}', '-1', '{9}', '{1}', '{8}', '{3}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '1', '{10}', '{11}', '{12}', '{13}', '{14}', '{15}');\n".format(
        ID, mapName, MAX_ZOOM, MIN_ZOOM, posLeft, posTop, posRight, posBottom, mapDisplayName, mapParentID, tilesX, tilesY, defaultZoom, maxTilesX, maxTilesY, displayData)

    safeName = EscapeSql(planetName)
    sql += "UPDATE location set destinationId = '{2}' WHERE worldId='{0}' AND name='{1}';\n".format(mapParentID, safeName, -ID)

    return sql


def CreateZoomTiles(image, mapName, layer, zoom, scale):

    print("\t\t{0}: Creating zoom level {1}...".format(mapName, zoom))
    
    mapPath = os.path.dirname(MakeMapTileFilename(OUTPUT_PATH, mapName, layer, 0, 0, zoom))
    mkdir_p(mapPath)
    
    scaledImage = image.resize((IMAGE_WIDTH/scale, IMAGE_HEIGHT/scale), Image.ANTIALIAS)
    width, height = scaledImage.size

    tilesX = width/TILE_SIZE
    tilesY = height/TILE_SIZE

    for y in xrange(tilesX):
        for x in xrange(tilesY):
            splitImage = scaledImage.crop((x*TILE_SIZE, y*TILE_SIZE, (x+1)*TILE_SIZE, (y+1)*TILE_SIZE))
            OutputFilename = MakeMapTileFilename(OUTPUT_PATH, mapName, layer, x, y, zoom)
            splitImage.save(OutputFilename, quality=95)

    return


def CreateMapTiles(image, mapName, layer):
    
    if (not SAVE_IMAGES): return

    for zoom in range(MAX_ZOOM, MIN_ZOOM-1, -1):
        scale = pow(2, MAX_ZOOM - zoom)
        CreateZoomTiles(image, mapName, layer, zoom, scale)

    return


def CreatePlanetTiles(filename, layer, niceName, planetName):
    global g_CreatedPlanets
    
    niceName = MakeNiceMapName(niceName)
    print("\t{0}({1}): Creating tiles for layer {1} from {3}...".format(planetName, niceName, layer, filename))
    
    g_CreatedPlanets[niceName] = planetName

    if (not SAVE_IMAGES): return

    if (type(filename) is str):
        image = Image.open(filename)
    else:
        image = filename
        
    (width, height) = image.size

    if (width != IMAGE_WIDTH):
        factor = IMAGE_WIDTH/width
        image = image.resize((IMAGE_WIDTH, int(height * factor)), Image.ANTIALIAS)
        width = IMAGE_WIDTH
        height = int(height * factor)

    paddedImage = Image.new(image.mode, (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
    paddedImage.paste(image, (0, (width-height)/2))

    CreateMapTiles(paddedImage, niceName, layer)
    
    return


def CreateAllTiles(texturePath, layer):
    global g_PlanetNameMap

    for subdir, dirs, files in os.walk(texturePath):
        for file in files:
            filename = os.path.join(texturePath, file)
            niceName, ext = os.path.splitext(os.path.basename(filename))
            planetName = niceName
            niceName = MakeNiceMapName(niceName)
            if (niceName in g_PlanetNameMap): planetName = g_PlanetNameMap[niceName]
            
            CreatePlanetTiles(filename, layer, niceName, planetName)
            
    return


def CreateAllBiomeTiles(biomePath):
    global g_PlanetNameMap

    for subdir, dirs, files in os.walk(biomePath):
        for dir in dirs:
            path = os.path.join(biomePath, dir)

            combImage = os.path.join(path, "combImage.png")
            indexImage = os.path.join(path, "indexImage.png")

            niceName = dir.replace(".biom", "")
            planetName = niceName
            niceName = MakeNiceMapName(niceName)
            if (niceName in g_PlanetNameMap): planetName = g_PlanetNameMap[niceName]
            
            CreatePlanetTiles(combImage, "biome1", niceName, planetName) 
            CreatePlanetTiles(indexImage, "biome2", niceName, planetName)
            
    return


def ConvertImageToGrayscale(image):
    (width, height) = image.size

    for y in xrange(height):
        for x in xrange(width):
            r, g, b = image.getpixel((x, y))
            gray = int(r * 299.0/1000 + g * 587.0/1000 + b * 114.0/1000)
            image.putpixel((x, y), (gray, gray, gray))
        
    return image


def CreateMissingPlanetTiles(niceName, planetName, biomePath, subdir, layer):
    
    print("\tCreating missing planet tiles for {0}...".format(planetName))
    combFilename = os.path.join(biomePath, subdir, "combImage.png")
    indexFilename = os.path.join(biomePath, subdir, "indexImage.png")

    if (not SAVE_IMAGES):
        g_CreatedPlanets[niceName] = planetName
        return

    combImage = Image.open(combFilename)
    indexImage = Image.open(indexFilename)

    image = ConvertImageToGrayscale(Image.blend(combImage, indexImage, 0.5))
    (width, height) = image.size

    msg = "This is a Placeholder Texture"
    font = ImageFont.load_default()
    font = ImageFont.truetype("arial.ttf", 32)
    (textWidth, textHeight) = font.getsize(msg)
    draw = ImageDraw.Draw(image)
    
    draw.text((width/2 - textWidth/2,height/2-textHeight/2), msg, (255,255,255), font=font)
    
    CreatePlanetTiles(image, layer, niceName, planetName)
    
    return


def CreateMissingTiles(texturePath, biomePath, layer):
    global g_Planets
    global g_PlanetNameMap
    
    texturePlanets = {}
    biomePlanets = {}
    biomeSubdir = {}
    allPlanets = {}

    for subdir, dirs, files in os.walk(texturePath):
        for file in files:
            filename = os.path.join(texturePath, file)
            planetName, ext = os.path.splitext(os.path.basename(filename))
            niceName = MakeNiceMapName(planetName)

            allPlanets[niceName] = 1
            texturePlanets[niceName] = planetName

    for subdir, dirs, files in os.walk(biomePath):
        for dir in dirs:
            path = os.path.join(biomePath, dir)
            planetName = dir.replace(".biom", "")
            niceName = MakeNiceMapName(planetName)
            biomePlanets[niceName] = planetName
            biomeSubdir[niceName] = dir

            if (niceName in g_PlanetNameMap): biomePlanets[niceName] = g_PlanetNameMap[niceName]

            if (niceName in allPlanets):
                allPlanets[niceName] = 3
            else:
                allPlanets[niceName] = 2

    for name in biomePlanets:
        if (name in texturePlanets): continue
        CreateMissingPlanetTiles(name, biomePlanets[name], biomePath, biomeSubdir[niceName], layer)

    missingCount = 0

    for row in g_Planets:
        planetName = row[0]
        niceName = MakeNiceMapName(planetName)
        
        if (not niceName in allPlanets):
            missingCount += 1
            print("\t{0}) {1}: Missing planet texture!".format(missingCount, niceName))
            
    return


def CreatePlanetSql(sqlFilename):
    global g_CreatedPlanets
    
    f = open(sqlFilename, 'w')

    for niceName in g_CreatedPlanets:
        planetName = g_CreatedPlanets[niceName]
        sql = CreatePlanetWorldDB(planetName, niceName)
        f.write(sql + "\n")

    f.close()
    return
        


MakeWorldIdMap()
MakePlanetIdMap()

#print(str(g_PlanetNameMap))
#exit

CheckPlanetNames()

CreateAllTiles(TEXTURE_PATH, "default")
CreateAllBiomeTiles(BIOME_PATH)

CreateMissingTiles(TEXTURE_PATH, BIOME_PATH, "default")
CreatePlanetSql(OUTPUT_PATH + "/planet.sql")
