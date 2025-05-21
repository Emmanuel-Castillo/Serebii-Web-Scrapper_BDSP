import sys
import requests
from bs4 import BeautifulSoup
import json
import re
import copy

TIME_OF_DAY = ["Morning","Day","Evening","Night"]
WEATHER = ["All Weather", "Rainstorm", "Drought", "Rain", "Cloudy", "Sunny", "Fog"]
METHODS = ["Standard Spawn", "Standard Spawn - In Air", "Alpha Spawn", "Shaking Tree", "Shaking Ore Deposits", "Space-time Distortion", "Event Spawn", "Mass Outbreak", "Unown Spawn", "Swimming", "Flying", "Interactable Pokémon"]

# JSON file to store all available Pokemon
pokemon_in_location_dict = {}

# Structure for each encounter entry
# pokemon = {
#         "pokemon" : {
#             "name": "Unown",
#             "type1": "Psychic",
#             "type2": None
#         },
#         "encounter_method": {
#             "method": "Random Encounter",
#             "time_of_day": "Anytime",
#             "requisite": None,
#             "chance" : "100%"
#         },
#         "location": {
#             "name": key,
#             "area_anchor": anchor_name,
#             "region": "Sinnoh",
#             "game_version": "BDSP"
#         },
#     }

# Determine form of Pokemon
def determineForm(nat_dex_id, char):
    # If Unown, call different function, as branches in the bottom match case will conflict with braches determining Unown form
    if (nat_dex_id == 201):
        return 1
        # return determineUnownForm(char)
    match char:
        case 'a':
            return 2
            # return 'Alolan'
        case 'h':
            return 4
            # return "Hisuian"
        case _ :
            return 1
        # case 'c':
        #     return "Sandy Cloak"
        # case 's':
        #     return "Trash Cloak"
        # case 'o':
        #     return "Origin Form"
        # case 'w':
        #     return "White-Striped Form"
        # case 'e':
        #     return "East Form"
        
# Determine form of Unown
def determineUnownForm(char):
    match char:
        case '!':
            return "Exclamation Mark"
        case "qm":
            return "Question Mark"
        case _:
            return "Letter " + char.upper()
         

# Grabbing method field from encounter_method
def grabEncounterMethod(row):
    cell = row.find("td")
    cellText = cell.text

    if cellText in METHODS:
        return cellText
    return None

# First row to grab time of day AND weather conditions
def grabTimeOfDayAndWeather(row, encounter_method):
    # extra_row = table.find_all("tr")[0]
    cell = row.find(re.compile("td"))
    # print(cell)
    # print(cell.text)
    cellText = cell.text
    textList = cellText.split("-")

    # Default values for Interactable Pokemon tables
    time_of_day = "Anytime"
    weather = "All Weather"

    if key == user_location:
        print(textList)
    if (len(textList) > 1):
        time_of_day = textList[0].strip()
        weather = textList[1].strip()
        
    encounter_method["time_of_day"] = time_of_day
    encounter_method["requisite"] = weather
    encounter_method["item_needed"] = None

    # print("Encounter method: ", encounter_method)

def grabPokemonNatDexId(row, pokemon_row_list):
    cells = row.find_all("td")

    # Clear and extend the existing list instead of replacing it
    pokemon_row_list.clear()  
    pokemon_row_list.extend([{"pokemon":{}} for _ in range(len(cells))])
    
    for i, cell in enumerate(cells):
        # print(cell)
        img = cell.find("img")
        # print(img)
        img_src = img.get("src")
        img_src_split_words = re.split(r"[/.]", img_src)
        # print(img_src_split_words)
        img_file_name = img_src_split_words[4]

        # Default values
        nat_dex_id = img_file_name

        # form = None

        # Default regional variant id
        rvId = 1
        
        # See if contains form
        if '-' in img_file_name:
            img_file_name_split_words = re.split(r"[-]", img_file_name)
            nat_dex_id = int(img_file_name_split_words[0])

            # form = determineForm(nat_dex_id, img_file_name_split_words[1])
            rvId = determineForm(nat_dex_id, img_file_name_split_words[1] )
        else:
            nat_dex_id = int(nat_dex_id)

        # if form is None:
        #     match nat_dex_id:
        #         case 413:
        #             form = "Grassy Cloak"
        #         case 492:
        #             form = "Land Forme"
        #         case 423:
        #             form = "West Form"
        #         case 483 | 484:
        #             form = "Altered Form"
        #         case 201:
        #             form = "Letter A"

        pokemon_row_list[i]["pokemon"]["national_dex_id"] = int(nat_dex_id)
        pokemon_row_list[i]["pokemon"]["rvId"] = rvId

        # pokemon_row_list[i]["pokemon"]["form"] = form

def grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor):
    # Grabbing name
    # Start assigning size of pokemon list per row
    # As well as initialzing pokemon data appropriately
    cells = row.find_all("td")
    
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["pokemon"]["name"] = cell.text
        # pokemon_row_list[i]["pokemon"]["isAlpha"] = False
        pokemon_row_list[i]["encounter_method"] = copy.deepcopy(encounter_method)
        pokemon_row_list[i]["location"] = {
            "name" : key,
            "area_anchor" : anchor,
            "region": "Hisui",
            "game_version" : game_version,
        }
        # print("Pokemon: ", cell.text)

        # Check if Pokemon is alpha!!!
        img = cell.find("img")
        if img and img.get("src") == "alpha.png":
            pokemon_row_list[i]["encounter_method"]["method"] += " - Alpha"
            # pokemon_row_list[i]["pokemon"]["isAlpha"] = True


def grabPokemonTypes(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["pokemon"]["type1"] = None
        pokemon_row_list[i]["pokemon"]["type2"] = None
        types = cell.find_all("a")
        for j, type in enumerate(types):
            img = type.find("img")
            img_src = img.get("src")
            type_name = re.split(r"[/.]", img_src)

            if j == 0:
                pokemon_row_list[i]["pokemon"]["type1"] = type_name[3].title()
            elif j == 1:
                pokemon_row_list[i]["pokemon"]["type2"] = type_name[3].title()

        # Check if Pokemon have their types: Burmy, Wormadam



def grabPokemonChance(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["encounter_method"]["chance"] = cell.text
        # print("Chance: ", cell.text)

def grabPokemonLevels(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["level"] = cell.text
        # print("Levels: ", cell.text)

def processPokemonRows(rows, pokemon_row_list, pokemon_in_table_list, game_version, encounter_method, key):
    if key == user_location:
        print("in processPokemonRows")
    # print(encounter_method)
    for index, row in enumerate(rows):
        # Grabbing nat_dex_id
        if index == 0:
            if key == user_location:
                print("In first row: ", row)
            grabPokemonNatDexId(row, pokemon_row_list)

        # Grabbing name
        if index == 1:
            if key == user_location:
                print("In second row: ", row)
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)
        # Grabbing type
        # elif index == 2:
        #     if key == user_location:
        #         print("In third row: ", row)
        #     grabPokemonTypes(row, pokemon_row_list)

        # Grabbing chance
        elif index == 3:
            if key == user_location:
                print("In fourth row: ", row)
            grabPokemonChance(row, pokemon_row_list)

        # Grabbing level
        # elif index == 5:
        #     grabPokemonLevels(row, pokemon_row_list)

    # Add new pokemon_row_list to pokemon_list
    for pokemon in pokemon_row_list:
        pokemon_in_table_list.append(pokemon)

# Table should start at row that collect game_version
def processTable(rows, pokemon_in_table_list, method, key, anchor):
    game_version = [36]
    encounter_method = {
        "method": method
    }
    pokemon_row_list = []
    for index, row in enumerate(rows):

        # Grabbing game version
        if index == 0:
            grabTimeOfDayAndWeather(row, encounter_method)

        elif index == 1:
            grabPokemonNatDexId(row, pokemon_row_list)

        elif index == 2:
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)
        # Grabbing type
        # elif index == 3:
        #     grabPokemonTypes(row, pokemon_row_list)

        # Grabbing chance
        elif index == 4:
            grabPokemonChance(row, pokemon_row_list)

        # Grabbing level
        # elif index == 6:
        #     grabPokemonLevels(row, pokemon_row_list)

        # Print current pokemon_row_list
        # print(pokemon_row_list)

    # Add new pokemon_row_list to pokemon_list
    for pokemon in pokemon_row_list:
        pokemon_in_table_list.append(pokemon)

def processGiftTable(rows, encounter_method, key, pokemon_in_table_list, anchor):
    encounter_method["method"] = "Gift Pokémon"
    encounter_method["time_of_day"] = "Anytime"

    game_version = [36]
    pokemon_row_list = []
    for index, row in enumerate(rows):

        if index == 0:
            grabPokemonNatDexId(row, pokemon_row_list)

        # Grabbing name
        # Start assigning size of pokemon list per row
        # As well as initialzing pokemon data appropriately
        if index == 1:
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)

        # Grabbing type
        # elif index == 2:
        #     grabPokemonTypes(row, pokemon_row_list)

        # Grabbing level
        # elif index == 4:
        #     grabPokemonLevels(row, pokemon_row_list)

        # Grabbing requisite for each Gift Pokemon & setting chance
        elif index == 5:
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                requisite = None
                if len(cell.text) > 0:
                    requisite = cell.text
                    # print(requisite)
                    # print(cell.text)
                    # print(pokemon_row_list[i]["pokemon"]["name"])
                    # print(cell.text)
                    # pokemon_row_list[i]["encounter_method"]["requisite"] = cell.text
                    # print(pokemon_row_list[i]["pokemon"]["name"] + " has requisite: " + pokemon_row_list[i]["encounter_method"]["requisite"])
                    # for pokemon in pokemon_row_list:
                        # print(pokemon["pokemon"]["name"] + ": " + pokemon["encounter_method"]["requisite"])
                # else:
                pokemon_row_list[i]["encounter_method"]["requisite"] = requisite
                pokemon_row_list[i]["encounter_method"]["item_needed"] = None
                pokemon_row_list[i]["encounter_method"]["chance"] = "100%"
                # print(pokemon_row_list[i])

                # print("NEXT CELL \n\n\n\n\n")

    # Print current pokemon_row_list
    # print(pokemon_row_list)

    # Add new pokemon_row_list to pokemon_list
    # Gift pokemon are automatically initialized to be acquired in both games
    for pokemon in pokemon_row_list:
        pokemon_in_table_list.append(pokemon)

#
# 
#
#
# Fetching command line argument to debugh location
user_location = None
if len(sys.argv) > 1:
    user_location = sys.argv[1]
    print(user_location)
#
# Fetching pokemon from each endpoint
starting_url = "https://www.serebii.net"
response = requests.get(starting_url + "/pokearth/hisui/")
soup = BeautifulSoup(response.text, 'html.parser')

region_form = soup.find("form", attrs={"name": "kalos"})
options = region_form.find_all("option")
locations_endpoint_dict = {}

for option in options[1:]:
    if option.text == "===":
        continue
    location_name = option.text
    locations_endpoint_dict[location_name] = option.get("value")
    pokemon_in_location_dict[location_name] = {}    
    
# SKIP AREAS
skip_areas = [
    "/pokearth/paldea/index.shtml",
    "/pokearth/hisui/obsidianfieldlands.shtml",
    "/pokearth/hisui/crimsonmirelands.shtml",
    "/pokearth/hisui/cobaltcoastlands.shtml",
    "/pokearth/hisui/coronethighlands.shtml",
    "/pokearth/hisui/alabastericelands.shtml",
    "/pokearth/hisui/ancientretreat.shtml",
]

# key = Official location name
# value = Endpoint to append to url
for key, value in locations_endpoint_dict.items():

    print(value)
    if value in skip_areas:
        # print("SKIPPING...")
        continue

    response = requests.get("https://www.serebii.net" + value)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encounter data is inside tables classified by either:
    #   "extradextable"
    #   "dextable"

    # Grabbing all tables
    tables = soup.find_all("table", class_=re.compile(r"\b(?:extra)?dextable\b"))
    # print(tables)

    if key == user_location:
        print(len(tables) , " in", user_location)

    extra_dextable_endpoints = []
    # Certain endpoints have extra dextables
    # if key in extra_dextable_endpoints:
    #     tables = tables[1:]

    # Pokemon in each endpoint
    pokemon_in_table_list = []

    table_count = len(tables)
    table_index = 0

    # print(table_count, " tables present")

    curr_method = None

    # Processing endpoint tables
    while table_index < table_count:
        # print("New table!!!")
        table = tables[table_index]

        if key == user_location:
            print("Table #", table_index)


        # Determine anchor limit & anchor
        anchor = "Main Area" # Default value
        # print("Current anchor: ", anchor)

        # Processing table
        # Majority of the HTML consists of groupings of extradextable tables
        # The first table indicates the method for encounters listed on sequential tables
        # So, we consume the method from the first, then dissect the rest tables, then modify the method when coming across 
        # a table with a different method
        # Some cases, we'll come across single tables (Gift Pokemon)

        # First table
        rows = table.find_all("tr")
        # Should work for all pairs of tables; first table in pair MUST HAVE class name extradextable
        # Check if table has class extradextable
        # If so, check if contains different method, if any
        if 'extradextable' in table.get('class', []):
            starting_index_first_table = 1

            # Processing pair of tables
            method = grabEncounterMethod(rows[0])
            # print("Encounter method: ", encounter_method)

            # If reached table with different weather, modify curr_method and continue to next table
            if method is not None:
                curr_method = method
                if key == user_location:
                    print(curr_method)
                if curr_method != "Interactable Pokémon":
                    table_index += 1
                    continue
                else:
                    starting_index_first_table += 1

            # For proceeding tables after grabbing method of encounter from prev
            # Grab time of day and weather 
            encounter_method = {
                "method": curr_method
            }
            grabTimeOfDayAndWeather(rows[0], encounter_method)

            # Process proceeding tables
            # Tables could have multiple rows of Pokemon
            NUM_ROWS_TABLE = len(rows[starting_index_first_table:])
            # if NUM_ROWS_TABLE > 6:

            NUM_ROWS_DETAILS_PER_POKEMON = 6
            NUM_ROWS_POKEMON_IN_TABLE = NUM_ROWS_TABLE // NUM_ROWS_DETAILS_PER_POKEMON
            # print(NUM_ROWS_POKEMON_IN_TABLE , " row(s)")
            for i in range(NUM_ROWS_POKEMON_IN_TABLE):
                # print(i)
                # print("New Row for Pokemon!!")
                pokemon_row_list = []
                start_index = i * NUM_ROWS_DETAILS_PER_POKEMON + starting_index_first_table
                end_index = i * NUM_ROWS_DETAILS_PER_POKEMON + starting_index_first_table + NUM_ROWS_DETAILS_PER_POKEMON
                processPokemonRows(rows[start_index:end_index], pokemon_row_list, pokemon_in_table_list,[36], encounter_method, key)
            # else:
                # processTable(rows[starting_index_first_table:], pokemon_in_table_list, method, key, anchor)

        else:

            # Skip weather chance table (very first table in list)
            if table_index == 0:
                table_index =+ 1
                continue
            # print(key, "Table:", table_index)
            # print(table)
            # Otherwise, check if gift pokemon table
            method = grabEncounterMethod(rows[0])
            encounter_method = {
                "method": method
            }
            starting_index = 1
            processGiftTable(rows[starting_index:], encounter_method, key, pokemon_in_table_list, anchor)
 
        table_index += 1

    if key == user_location:
        print(pokemon_in_table_list)

    # Add pokemon_list to locations_dict
    # If no pokemon in 
    pokemon_in_location_dict[key] = pokemon_in_table_list

# For those endpoints we skipped, set their values to an empty list        
for key, value in pokemon_in_location_dict.items():
    if value == {}:
        pokemon_in_location_dict[key] = []

# print(pokemon_list)
# Save pokemon_list as JSON file
with open("lga_encounters.json", "w") as f:
    json.dump(pokemon_in_location_dict, f, indent=4)

        
        




