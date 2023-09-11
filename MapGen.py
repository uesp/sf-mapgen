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


STAR_CSV = "d:/src/starfield/TestEsm/TestEsm/Stars.csv"
PLANET_CSV = "d:/src/starfield/TestEsm/TestEsm/Planets.csv"
OUTPUT_PATH = "c:/Downloads/Starfield/Maps"

SAVE_IMAGES = False
VERBOSE = False

IMAGE_WIDTH = 8192
IMAGE_HEIGHT = 8192

SYSTEM_SIZE = 1000

OFFSET_X = 25.5
OFFSET_Y = 25.9
MAX_X = 30
MAX_Y = 30

MAX_ZOOM = 5
MIN_ZOOM = 0

TILE_SIZE = 256

    # Pixels
BASE_STAR_SIZE = 20
PLANET_STAR_SIZE = 200
PLANET_SIZE = 50
MOON_SIZE = 5
MAX_MOON_ORBITSIZE = 50
MIN_MOON_ORBITSIZE = 10

DB_NEXT_WORLD_ID = 1

BACKGROUND_COLOR = (0, 0, 0)

g_Stars = []
g_Planets = []
g_StarIdMap = {}
g_SystemIdMap = {}



def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
        

def MakeMapTileFilename(OutputPath, MapName, X, Y, Zoom):
    return "{0}/zoom{4}/{1}-{2}-{3}.jpg".format(OutputPath, MapName, X, Y, Zoom)


def IsValidWorldName(mapName):
    mapName = mapName.lower()

    if (mapName == ''): return False
    if (mapName.find("test") >= 0): return False

    return True


def GetRandomLabelPos(labelName):
    random.seed(labelName);
    labelPos = int(random.random() * 9 + 1)
    if (labelPos == 5): return 8
    return labelPos
    

def MakeNiceMapName(mapName):
    niceName = mapName.lower()
    niceName = niceName.strip()
    niceName = niceName.replace(' ', '')
    niceName = niceName.replace('\'', '')
    niceName = niceName.replace('"', '')
    return niceName


def EscapeSql(sql):
    return sql.replace("'", "\\'")


def ReadStarCsv (CsvFilename):
    print "Reading star CSV file {0}...".format(CsvFilename)

    with open(CsvFilename, 'rb') as f:
        reader = csv.reader(f)
        
        for row in reader:
            g_Stars.append(row)

    print "\tFound {0} stars!".format(len(g_Stars))
    return


def ReadPlanetCsv (CsvFilename):
    print "Reading planet CSV file {0}...".format(CsvFilename)

    with open(CsvFilename, 'rb') as f:
        reader = csv.reader(f)
        
        for row in reader:
            g_Planets.append(row)

    print "\tFound {0} planets!".format(len(g_Planets))
    return



def ConvertCsvToObject(headerRow, row):
    newObj = {}
    col = 0

    for field in headerRow:
        newObj[field.strip()] = row[col]
        col += 1
        
    return newObj    


def CreateImage():
    image = Image.new(mode="RGB", size=(IMAGE_WIDTH, IMAGE_HEIGHT), color = BACKGROUND_COLOR)
    return image


def GetStarColor(Type):
    #http://www.vendian.org/mncharity/dir3/starcolor/
    colors = {
        "A0": (202,215,255),
        "A1": (186,204,255),
        "A3": (192,209,255),
        "A4": (202,215,255),
        "A5": (202,216,255),
        "A7": (202,215,255),
        "A9": (202,215,255),
        "B9": (170,191,255),
        "F0": (237,238,255),
        "F2": (248,247,255),
        "F3": (248,247,255),
        "F5": (251,248,255),
        "F6": (248,247,255),
        "F7": (248,247,255),
        "F8": (248,249,249),
        "F9": (248,247,255),
        "G0": (255,244,234),
        "G1": (255,244,234),
        "G2": (255,245,236),
        "G3": (255,244,234),
        "G4": (255,244,234),
        "G5": (255,244,232),
        "G6": (255,244,234),
        "G7": (255,244,234),
        "G8": (255,241,223),
        "G9": (255,244,234),
        "K0": (255,235,209),
        "K1": (255,210,161),
        "K2": (255,210,161),
        "K3": (255,210,161),
        "K4": (255,215,174),
        "K5": (255,210,161),
        "K7": (255,198,144),
        "M0": (255,204,111),
        "M1": (255,204,111),
        "M2": (255,190,127),
        "M3": (255,204,111),
        "M4": (255,204,111),
        "M5": (255,187,123),
        "M6": (255,187,123),
        "WD0": (255,255,255),
        "WD5": (255,255,255),
        "WD9": (255,255,255),
    }

    if (Type in colors): return colors[Type]
    return (255,255,255)
    


def CreateGalaxy(image):
    headerRow = g_Stars[0]

    for row in g_Stars[1:]:
        star = ConvertCsvToObject(headerRow, row)
        CreateStar(star, image)

    if (not SAVE_IMAGES): return

    filename = OUTPUT_PATH + "/galaxy.jpg"
    print("\tSaving galaxy map to '{0}'".format(filename))
    image.save(filename, quality=95)
    
    return


def CreateStar(star, image):

    if (star['X'] == ''): return False
    if (star['Y'] == ''): return False
    
    X = float(star['X']) + OFFSET_X
    Y = float(star['Y']) + OFFSET_Y

    pixelX = int(X * IMAGE_WIDTH / MAX_X)
    pixelY = IMAGE_HEIGHT - int(Y * IMAGE_HEIGHT / MAX_Y)

    draw = ImageDraw.Draw(image)
    draw.ellipse((pixelX, pixelY, pixelX+BASE_STAR_SIZE, pixelY+BASE_STAR_SIZE), fill = GetStarColor(star['Spectral']))

    return True


def CreateZoomTiles(image, mapName, zoom, scale):

    print("\t{0}: Creating zoom level {1}...".format(mapName, zoom))
    
    mapPath = OUTPUT_PATH + "/" + mapName + "/leaflet/default"
    zoomPath = mapPath + "/zoom" + str(zoom)
    mkdir_p(zoomPath)
    
    scaledImage = image.resize((IMAGE_WIDTH/scale, IMAGE_HEIGHT/scale), Image.ANTIALIAS)
    width, height = scaledImage.size

    tilesX = width/TILE_SIZE
    tilesY = height/TILE_SIZE

    for y in xrange(tilesX):
        for x in xrange(tilesY):
            splitImage = scaledImage.crop((x*TILE_SIZE, y*TILE_SIZE, (x+1)*TILE_SIZE, (y+1)*TILE_SIZE))
            OutputFilename = MakeMapTileFilename(mapPath, mapName, x, y, zoom)
            splitImage.save(OutputFilename, quality=95)

    return


def CreateMapTiles(image, mapName):
    
    if (not SAVE_IMAGES): return
    
    mapPath = OUTPUT_PATH + "/" + mapName + "/leaflet/default/"
    mkdir_p(mapPath)

    for zoom in range(MAX_ZOOM, MIN_ZOOM-1, -1):
        scale = pow(2, MAX_ZOOM - zoom)
        CreateZoomTiles(image, mapName, zoom, scale)

    return


def CreateStarWorldDB(star, mapName):
    global DB_NEXT_WORLD_ID
    sql = ""

    if (mapName == ""): mapName = star['Name']
    mapDisplayName = mapName
    if (mapDisplayName == "galaxy"): mapDisplayName = "Galaxy"
    mapName = MakeNiceMapName(mapName)

    if (not IsValidWorldName(mapName)): return ""
    
    ID = DB_NEXT_WORLD_ID
    DB_NEXT_WORLD_ID += 1

    if (ID == 1 or mapName == "galaxy"):
        posLeft = -25.54
        posRight = posLeft + MAX_X
        posTop = 4.14
        posBottom = posTop - MAX_Y
    else:
        posLeft = 0
        posTop = SYSTEM_SIZE
        posRight = SYSTEM_SIZE
        posBottom = 0
        
    mapParentID = -1
    if (ID > 1): mapParentID = 1
    
    tilesX = pow(2, MAX_ZOOM)
    tilesY = pow(2, MAX_ZOOM)
    defaultZoom = MAX_ZOOM - 1
    maxTilesX = pow(2, MAX_ZOOM)
    maxTilesY = pow(2, MAX_ZOOM)
    displayData = '{"hasGrid":false,"hasCellResource":false,"layers":[{"name":"default"}]}';
    mapDisplayName = EscapeSql(mapDisplayName)

    sql = "INSERT INTO world(id, revisionId, parentId, name, displayName, minZoom, maxZoom, zoomOffset, posLeft, posTop, posRight, posBottom, enabled, tilesX, tilesY, defaultZoom, maxTilesX, maxTilesY, displayData) VALUES('{0}', '-1', '{9}', '{1}', '{8}', '{3}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '1', '{10}', '{11}', '{12}', '{13}', '{14}', '{15}');\n".format(
        ID, mapName, MAX_ZOOM, MIN_ZOOM, posLeft, posTop, posRight, posBottom, mapDisplayName, mapParentID, tilesX, tilesY, defaultZoom, maxTilesX, maxTilesY, displayData)

    g_SystemIdMap[mapName] = ID
    
    star['mapId'] = ID
    g_StarIdMap[ID] = star

    return sql


def CreateStarDB(star, mapName, worldId):
    sql = ""

    mapName = MakeNiceMapName(mapName)

    if (not IsValidWorldName(mapName)): return ""
    
    if (star['Name'].find("Test") >= 0): return "";
    if (star['X'] == ''): return "";
    if (star['Y'] == ''): return "";

    cols = ['worldId', 'revisionId', 'destinationId', 'locType', 'x', 'y', 'width', 'height', 'name', 'description', 'iconType', 'displayData', 'wikiPage', 'displayLevel', 'visible']
    revisionId = -1
    destinationId = -star['mapId']
    locType = 1
    x = float(star['X'])
    y = float(star['Y'])
    width = 32
    height = 32
    name = EscapeSql(star['Name'])

    #   SystemId EditorID FormId Gliese	 Spectral AbsMag  Temperature XYZ
    description = ''
    if (star['Gliese']): description += star['Gliese'] + ", "
    if (star['Spectral']): description += star['Spectral'] + ", "
    description += "Mag " + str(star['AbsMag']) + ", "
    description += "" + str(star['Temperature']) + " K, "
    description += "SystemId " + str(star['SystemId']) + ", "
    description += "EditorId " + str(star['EditorID']) + ", "
    description += "FormId " + str(star['FormID'])

    iconType = 2
    labelPos = GetRandomLabelPos(star['Name'])
    displayData = '{' + "\"labelPos\":{2},\"points\":[{0},{1}]".format(x, y, labelPos) + '}'
    wikiPage = "Starfield:" + EscapeSql(star['Name'])
    displayLevel = 0
    visible = 1
    values = [ worldId, revisionId, destinationId, locType, x, y, width, height, name, description, iconType, displayData, wikiPage, displayLevel, visible]

    colStr = ",".join(cols)
    valueStr = ""

    for value in values:
        if (valueStr): valueStr += ","
        valueStr += "'" + str(value) + "'"

    sql = "INSERT INTO location({0}) VALUES({1});\n".format(colStr, valueStr)

    destinationId = 0
    worldId = star['mapId']
    iconType = 1
    x = SYSTEM_SIZE / 2
    y = SYSTEM_SIZE / 2

    displayData = '{' + "\"labelPos\":{2},\"points\":[{0},{1}]".format(x, y, labelPos) + '}'

    values = [ worldId, revisionId, destinationId, locType, x, y, width, height, name, description, iconType, displayData, wikiPage, displayLevel, visible]
    valueStr = ""

    for value in values:
        if (valueStr): valueStr += ","
        valueStr += "'" + str(value) + "'"

    sql += "INSERT INTO location({0}) VALUES({1});\n".format(colStr, valueStr)
    
    return sql


def CreateGalaxyMapDB(rootMapName, filename):
    headerRow = g_Stars[0]

    f = open(filename, "wb")

    sql = "TRUNCATE world;";
    sql += "TRUNCATE location;";
    # sql  = "DELETE FROM world WHERE id='{0}';\n".format(DB_NEXT_WORLD_ID);
    # sql += "DELETE FROM location WHERE worldId='{0}';\n".format(DB_NEXT_WORLD_ID);
    sql += CreateStarWorldDB({}, rootMapName)
    f.write(sql)

    for row in g_Stars[1:]:
        star = ConvertCsvToObject(headerRow, row)
        
        sql = CreateStarWorldDB(star, "")
        f.write(sql)
        
        sql = CreateStarDB(star, rootMapName, 1)
        f.write(sql)

    f.close()

    return


def DrawPlanet(planet, image, stats):
    radius = 0
    distance = 0
    if (planet['Radius'] != ''): radius = float(planet['Radius'])
    if (planet['MeanOrbit'] != ''): distance = float(planet['MeanOrbit'])

    print("\tDrawing Planet {0}...".format(planet['Name']))
    
    if (VERBOSE):
        print("\t\tDistance: {0} ({1}-{2})".format(distance, stats['minDistance'], stats['maxDistance']))
        print("\t\t  Radius: {0} ({1}-{2})".format(radius, stats['minRadius'], stats['maxRadius']))

    orbitRadiusPix = distance / (stats['maxDistance']) * (IMAGE_WIDTH/2 - PLANET_SIZE - PLANET_STAR_SIZE/1.9 - 50) + PLANET_STAR_SIZE/2
    orbitRadiusPix = int(orbitRadiusPix)

    if (VERBOSE):
        print("\t\tOrbit Radius {0} pixels".format(orbitRadiusPix))

    pixelX = IMAGE_WIDTH / 2
    pixelY = IMAGE_HEIGHT / 2

    draw = ImageDraw.Draw(image)
    draw.ellipse((pixelX - orbitRadiusPix, pixelY - orbitRadiusPix, pixelX + orbitRadiusPix, pixelY + orbitRadiusPix), fill = None, outline = (128,128,128))

    planetRadiusPix = radius / stats['maxRadius'] * PLANET_SIZE
    if (planetRadiusPix < 5): planetRadiusPix = 5
    planetRadiusPix = int(planetRadiusPix)

    if (VERBOSE):
        print("\t\tPlanet Radius {0} pixels".format(planetRadiusPix))

    random.seed(planet['Name'])
    angle = random.random() * 2 * 3.14159
    pixelX = math.cos(angle) * orbitRadiusPix + IMAGE_WIDTH / 2
    pixelY = math.sin(angle) * orbitRadiusPix + IMAGE_HEIGHT / 2

    draw.ellipse((pixelX - planetRadiusPix, pixelY - planetRadiusPix, pixelX + planetRadiusPix, pixelY + planetRadiusPix), fill = (255,128,128))

    planet['outputX'] = pixelX
    planet['outputY'] = pixelY
    planet['outputRadius'] = planetRadiusPix
    planet['isMoon'] = 0
    
    return True


def DrawMoon(moon, planet, stats, image):
    radius = 0
    distance = 0
    if (moon['Radius'] != ''): radius = float(moon['Radius'])
    if (moon['MeanOrbit'] != ''): distance = float(moon['MeanOrbit'])

    moon['orbitName'] = planet['Name']
    moon['isMoon'] = 1

    print("\tDrawing Moon {0}...".format(moon['Name']))

    if (VERBOSE):
        print("\t\tDistance: {0} ({1}-{2})".format(distance, stats['minDistance'], stats['maxDistance']))
        print("\t\t  Radius: {0} ({1}-{2})".format(radius, stats['minRadius'], stats['maxRadius']))

    if (not 'outputRadius' in planet):
        print("\t\tERROR: Missing outputRadius and position in planet!")
        return False
    
    planetRadius = planet['outputRadius']

    if (stats['maxDistance'] == stats['minDistance']):
        orbitRadiusPix = planetRadius*1.2 + MIN_MOON_ORBITSIZE
    else:
        orbitRadiusPix = (distance - stats['minDistance'])/ (stats['maxDistance'] - stats['minDistance']) * (MAX_MOON_ORBITSIZE + planetRadius) + planetRadius*1.2 + MIN_MOON_ORBITSIZE
        
    orbitRadiusPix = int(orbitRadiusPix)

    if (VERBOSE):
        print("\t\tOrbit Radius {0} pixels".format(orbitRadiusPix))

    pixelX = planet['outputX']
    pixelY = planet['outputY']

    draw = ImageDraw.Draw(image)
    draw.ellipse((pixelX - orbitRadiusPix, pixelY - orbitRadiusPix, pixelX + orbitRadiusPix, pixelY + orbitRadiusPix), fill = None, outline = (128,128,128))

    moonRadiusPix = radius / stats['maxRadius'] * MOON_SIZE
    if (moonRadiusPix < 3): moonRadiusPix = 3
    moonRadiusPix = int(moonRadiusPix)

    if (VERBOSE):
        print("\t\tMoon Radius {0} pixels".format(moonRadiusPix))

    random.seed(moon['Name'])
    angle = random.random() * 2 * 3.14159
    moonPixelX = math.cos(angle) * orbitRadiusPix + pixelX
    moonPixelY = math.sin(angle) * orbitRadiusPix + pixelY

    draw.ellipse((moonPixelX - moonRadiusPix, moonPixelY - moonRadiusPix, moonPixelX + moonRadiusPix, moonPixelY + moonRadiusPix), fill = (150,128,128))

    moon['outputX'] = moonPixelX
    moon['outputY'] = moonPixelY
    moon['outputRadius'] = moonRadiusPix


    return True


def FindMoonPlanet(planetGroup, planetId):
    
    for planet in planetGroup:
        if (int(planet['PlanetId']) == planetId): return planet
        
    return None


def ComputePlanetStats(planetGroup, planetId):
    stats = {}

    minRadius = 10000000
    maxRadius = 0
    minDistance = 10299000000
    maxDistance = 0

    for planet in planetGroup:
        if (planetId == 0 and int(planet['Primary']) > 0): continue
        if (planetId > 0 and planetId != int(planet['Primary'])): continue
        
        radius = 0
        distance = 0
        if (planet['Radius'] != ''): radius = float(planet['Radius'])
        if (planet['MeanOrbit'] != ''): distance = float(planet['MeanOrbit'])

        if (minRadius > radius): minRadius = radius
        if (maxRadius < radius): maxRadius = radius
        if (minDistance > distance): minDistance = distance
        if (maxDistance < distance): maxDistance = distance

    stats['minRadius'] = minRadius
    stats['maxRadius'] = maxRadius
    stats['minDistance'] = minDistance
    stats['maxDistance'] = maxDistance

    if (stats['maxDistance'] == 0): stats['maxDistance'] = 1000
    if (stats['maxRadius'] == 0): stats['maxRadius'] = 5
    
    return stats


def CreateSystemMap(starMapId, planetGroup):
    print("Creating system map for mapId {0}...".format(starMapId))

    image = CreateImage()
    
    if (not starMapId in g_StarIdMap):
        print("Failed to find star ID {0} in star ID map!\t".format(starMapId));
        return False
    
    star = g_StarIdMap[starMapId]
    starColor = GetStarColor(star['Spectral'])

    pixelX = IMAGE_WIDTH/2 - PLANET_STAR_SIZE/2
    pixelY = IMAGE_HEIGHT/2 - PLANET_STAR_SIZE/2
    
    draw = ImageDraw.Draw(image)
    draw.ellipse((pixelX, pixelY, pixelX+PLANET_STAR_SIZE, pixelY+PLANET_STAR_SIZE), fill = starColor)

    stats = ComputePlanetStats(planetGroup, 0)
   
        # Draw primary orbits
    for planet in planetGroup:
        if (int(planet['Primary']) > 0): continue
        DrawPlanet(planet, image, stats)

        # Draw moon orbits
    for moon in planetGroup:
        planetId = int(moon['Primary'])
        if (planetId <= 0): continue

        planet = FindMoonPlanet(planetGroup, planetId)
        
        if (planet == None):
            print("\t\tNo planet found for moon!".format(moon['Name']))
            continue

        stats = ComputePlanetStats(planetGroup, planetId)
        
        DrawMoon(moon, planet, stats, image)

    if (not SAVE_IMAGES): return True

    filename = OUTPUT_PATH + "/" + planet['parentMap'] + ".jpg"
    print("\tSaving system map to '{0}'".format(filename))
    image.save(filename, quality=95)

    CreateMapTiles(image, planet['parentMap'])
    
    return True


def GroupPlanetsWithSystem():
    global g_PlanetGroups

    print("Grouping planets with parent stars...")
    headerRow = g_Planets[0]

    g_PlanetGroups = {}

    for row in g_Planets[1:]:
        planet = ConvertCsvToObject(headerRow, row)

        parentName = MakeNiceMapName(planet['StarName'])
        parentId = -1

        if (not IsValidWorldName(parentName)):
            continue

        if (not parentName in g_SystemIdMap):
            print("\tPlanet {0}: Could not find parent map name '{1}!".format(planet['EditorID'], parentName))
            continue

        parentId = g_SystemIdMap[parentName]

        if (not parentId in g_PlanetGroups):
            g_PlanetGroups[parentId] = []

        planet['parentMap'] = parentName
        planet['parentId'] = parentId
        g_PlanetGroups[parentId].append(planet)
        
    return


def CreateSystemMaps(sqlFilename):
    global g_PlanetGroups
    
    GroupPlanetsWithSystem()

    f = open(sqlFilename, "wb")

    for groupId in g_PlanetGroups:
        CreateSystemMap(groupId, g_PlanetGroups[groupId])
        sql = CreatePlanetGroupSql(groupId, g_PlanetGroups[groupId])
        f.write(sql)

    f.close()        
    return


def CreatePlanetSql(worldId, planet):
    sql = ""

    if (not 'outputX' in planet):
        print("\t\tError: Planet {0} has no output coordinates!".format(planet['Name']))
        return ""
    
    x = planet['outputX'] / IMAGE_WIDTH * SYSTEM_SIZE
    y = SYSTEM_SIZE - planet['outputY'] / IMAGE_HEIGHT * SYSTEM_SIZE

    cols = ['worldId', 'revisionId', 'destinationId', 'locType', 'x', 'y', 'width', 'height', 'name', 'description', 'iconType', 'displayData', 'wikiPage', 'displayLevel', 'visible']
    revisionId = -1
    destinationId = 0
    locType = 1
    width = 32
    height = 32
    name = EscapeSql(planet['Name'])

    # StarName Class Gliese Life MagField Type Special
    # MeanOrbit Aphelion Perihelion Eccentricity Gravity Density Mass Temperature Radius PlanetId Heat HydroPct Seed Asteroids Year StartAngle PeriAngle
    description = ''
    if (planet['Type'] == "Gas G."): planet['Type'] == "Gas Giant"
    if (planet['Type'] == "Hot Gas G."): planet['Type'] == "Hot Gas Giant"
    if (planet['Type'] == "Ice G."): planet['Type'] == "Ice Giant"
    
    if (planet['Type']): description += planet['Type'] + ", "
    if (planet['Special']): description += planet['Special'] + ", "
    if (planet['Class']): description += planet['Class'] + ", "
    if (planet['Gliese']): description += planet['Gliese'] + ", "
    if ('orbitName' in planet and planet['orbitName']): description += "Orbits " + planet['orbitName'] + ", "
    if (planet['Life']): description += "Life:" + planet['Life'] + ", "
    if (planet['MagField']): description += "MagField:" + planet['MagField'] + ", "
    description += "PlanetId " + str(planet['PlanetId']) + ", "
    description += "EditorId " + str(planet['EditorID']) + ", "
    description += "FormId " + str(planet['FormID'])
    description = EscapeSql(description)

    iconType = 100
    if (planet['isMoon']): iconType = 150

    labelPos = GetRandomLabelPos(planet['Name'])
    displayData = '{' + "\"labelPos\":{2},\"points\":[{0},{1}]".format(x, y, labelPos) + '}'
    wikiPage = "Starfield:" + EscapeSql(planet['Name'])
    displayLevel = 0
    visible = 1
    values = [ worldId, revisionId, destinationId, locType, x, y, width, height, name, description, iconType, displayData, wikiPage, displayLevel, visible]

    colStr = ",".join(cols)
    valueStr = ""

    for value in values:
        if (valueStr): valueStr += ","
        valueStr += "'" + str(value) + "'"

    sql = "INSERT INTO location({0}) VALUES({1});\n".format(colStr, valueStr)
    
    return sql


def CreatePlanetGroupSql(mapId, planetGroup):
    sql = ""
    
    for planet in planetGroup:
        sql += CreatePlanetSql(mapId, planet)
        
    return sql


def CreateSystemDB(filename):
    global g_PlanetGroups

    f = open(filename, "wb")

    for groupId in g_PlanetGroups:
        sql = CreatePlanetGroupSql(groupId, g_PlanetGroups[groupId])
        f.write(sql)

    f.close()
    return


# Start Main Program
ReadStarCsv(STAR_CSV)
ReadPlanetCsv(PLANET_CSV)

image = CreateImage()
CreateGalaxy(image)
CreateMapTiles(image, "galaxy")

CreateGalaxyMapDB("galaxy", OUTPUT_PATH + "/galaxy.sql")

CreateSystemMaps(OUTPUT_PATH + "/system.sql")

