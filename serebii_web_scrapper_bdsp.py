import requests
from bs4 import BeautifulSoup
import json
import re

TIME_OF_DAY = ["Morning","Day","Evening","Night"]
ITEM_NEEDED = ["Old Rod","Good Rod","Super Rod"]
# RARITY = ["Rare","Very Rare"]

# rvId = Default in Room table PokemonRegionalVariants
RV_ID = 1

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
def checkIfPokemonInBothVersions(p0, pokemon_list):
    for p1 in pokemon_list:
        if (p0["pokemon"] == p1["pokemon"]) and (p0["encounter_method"] == p1["encounter_method"]) and (p0["location"]["name"] == p1["location"]["name"]) and (p0["location"]["area_anchor"] == p1["location"]["area_anchor"]) and (p0["location"]["region"] == p1["location"]["region"]):
            p1["location"]["game_version"] = [34, 35]

            # if (p0["location"] == p1["location"]) and (p0["location"] == "Iron Island"):
            #     print(p0, p1)
            #     print("p0 is already in the list!!!!")
            return True
    return False

def grabEncounterMethod(row):
    encounter_method = {}
    # extra_row = table.find_all("tr")[0]
    h = row.find(re.compile("^h"))
    encounter_method["method"] = h.text
    encounter_method["time_of_day"] = "Anytime"
    encounter_method["requisite"] = None
    encounter_method["item_needed"] = None
    # encounter_method["rarity"] = "Common"

    # check if table includes time of day by splitting
    split_words = encounter_method["method"].split(' - ')
    if len(split_words) > 1:
        encounter_method["method"] = split_words[0]
        second_word = split_words[1]
        if second_word in TIME_OF_DAY:
            encounter_method["time_of_day"] = second_word
        elif second_word in ITEM_NEEDED:
            encounter_method["item_needed"] = second_word
        # elif second_word in RARITY:
        #     encounter_method["rarity"] = second_word
        # else:
            # print(second_word)

    return encounter_method

    # print("Encounter method: ", encounter_method)
    # print("Time of day: " + time_of_day)

def grabPokemonNatDexId(row, pokemon_row_list):
    cells = row.find_all("td")

    # Clear and extend the existing list instead of replacing it
    pokemon_row_list.clear()  
    pokemon_row_list.extend([{"pokemon":{}} for _ in range(len(cells))])
    
    for i, cell in enumerate(cells):
        img = cell.find("img")
        img_src = img.get("src")
        img_src_split_words = re.split(r"[/.-]", img_src)
        nat_dex_id = img_src_split_words[4]
        pokemon_row_list[i]["pokemon"]["national_dex_id"] = int(nat_dex_id)
        pokemon_row_list[i]["pokemon"]["rvId"] = RV_ID


def grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor):
    # Grabbing name
    # Start assigning size of pokemon list per row
    # As well as initialzing pokemon data appropriately
    cells = row.find_all("td")
    
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["pokemon"]["name"] = cell.text
        pokemon_row_list[i]["encounter_method"] = encounter_method
        pokemon_row_list[i]["location"] = {
            "name" : key,
            "area_anchor" : anchor,
            "region": "Sinnoh",
            "game_version" : game_version,
        }
        # print("Pokemon: ", cell.text)

def grabPokemonTypes(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        types = cell.find_all("a")
        pokemon_row_list[i]["pokemon"]["type1"] = None
        pokemon_row_list[i]["pokemon"]["type2"] = None
        for j, type in enumerate(types):
            img = type.find("img")
            img_src = img.get("src")
            type_name = re.split(r"[/.]", img_src)

            if j == 0:
                pokemon_row_list[i]["pokemon"]["type1"] = type_name[3].title()
            elif j == 1:
                pokemon_row_list[i]["pokemon"]["type2"] = type_name[3].title()


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

def processPokemonRows(rows, pokemon_row_list, pokemon_in_table_list, game_version, encounter_method, key, anchor):
    for index, row in enumerate(rows):

        # Grabbing nat_dex_id
        if index == 0:
            grabPokemonNatDexId(row, pokemon_row_list)

        # Grabbing name
        if index == 1:
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)
        # Grabbing type
        # elif index == 2:
            # grabPokemonTypes(row, pokemon_row_list)

        # Grabbing chance
        elif index == 3:
            grabPokemonChance(row, pokemon_row_list)

        # Grabbing level
        # elif index == 5:
        #     grabPokemonLevels(row, pokemon_row_list)

    # Add new pokemon_row_list to pokemon_list
    for pokemon in pokemon_row_list:
        # Check if pokemon already in locations_dict[location], and has the same data (except game version)
        # If so, do not append pokemon and modify pokemon in locations_dict[location].game_version = "Both"
        if not checkIfPokemonInBothVersions(pokemon, pokemon_in_table_list):
            pokemon_in_table_list.append(pokemon)
            # print(pokemon["name"] , pokemon["game_version"])
        # else:
            # print(pokemon["name"], " is already in the other game!")

# Table should start at row that collect game_version
def processTable(rows, pokemon_in_table_list, encounter_method, key, anchor):
    game_version = []
    pokemon_row_list = []
    for index, row in enumerate(rows):

        # Grabbing game version
        if index == 0:
            cell = row.find("td")
            # print("Game version: ", cells.text)
            if cell.text == "Pokémon Brilliant Diamond":
                game_version.append(34)
            elif cell.text == "Pokémon Shining Pearl":
                game_version.append(35)

        elif index == 1:
            grabPokemonNatDexId(row, pokemon_row_list)

        elif index == 2:
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)
        # Grabbing type
        # elif index == 3:
            # grabPokemonTypes(row, pokemon_row_list)

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
        # Check if pokemon already in locations_dict[location], and has the same data (except game version)
        # If so, do not append pokemon and modify pokemon in locations_dict[location].game_version = "Both"
        if not checkIfPokemonInBothVersions(pokemon, pokemon_in_table_list):
            pokemon_in_table_list.append(pokemon)

def processGiftTable(rows, encounter_method, key, pokemon_in_table_list, anchor):
    game_version = [34, 35]
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
            # grabPokemonTypes(row, pokemon_row_list)

        # Grabbing level
        # elif index == 4:
        #     grabPokemonLevels(row, pokemon_row_list)

        # Grabbing requisite for each Gift Pokemon & setting chance
        elif index == 5:
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                pokemon_row_list[i]["encounter_method"]["requisite"] = cell.text
                pokemon_row_list[i]["encounter_method"]["chance"] = "100%"

    # Print current pokemon_row_list

    # Add new pokemon_row_list to pokemon_list
    # Gift pokemon are automatically initialized to be acquired in both games
    for pokemon in pokemon_row_list:
        pokemon_in_table_list.append(pokemon)

def processTrophyGardenTables(tables, anchor_pairs, pokemon_in_table_list):
    table_count = len(tables)
    table_index = 0

    # print(table_count, "tables")
    # print(len(anchor_pairs), "anchors")

    curr_anchor_index = 0
    curr_anchor_table_index = 0
    curr_anchor = anchor_pairs[curr_anchor_index]

    while table_index < table_count:
        table = tables[table_index]

        if table_index == 6:
            # print("Fake table")
            table_index += 1
            continue
        # Determine anchor limit & anchor
        anchor = "Main Area" # Default value
        if len(curr_anchor) > 0:
            # print(curr_anchor)
            anchor_name, anchor_limit = curr_anchor
            # print("anchor name: ", anchor_name, "anchor limit: ", anchor_limit)
            if curr_anchor_table_index < anchor_limit:
                anchor = anchor_name
            else:
                curr_anchor_index += 1
                curr_anchor_table_index = 0
                curr_anchor = anchor_pairs[curr_anchor_index]
                anchor_name, new_anchor_limit = curr_anchor
                anchor = anchor_name

        # print(anchor)

        # Grab rows
        rows = table.find_all("tr")

        # Check if table has class extradextable
        # If so, process itself (+ grab encounter_method) and the next table
        if 'extradextable' in table.get('class', []) and table_index < 6:
            encounter_method = grabEncounterMethod(rows[0])
            processTable(rows[1:], pokemon_in_table_list, encounter_method, key, anchor)

            if table_index + 1 < table_count:
                rows = tables[table_index + 1].find_all("tr")
                processTable(rows, pokemon_in_table_list, encounter_method, key, anchor)
            
            table_index += 2
            curr_anchor_table_index += 2

        else:
            # Remove extra row
            if table_index == 7:
                encounter_method = grabEncounterMethod(rows[0])
                rows = rows[2:]

                # Find number of pokemon rows
                NUM_INFO_ROWS_PER_POKEMON = 6
                NUM_POKEMON_ROWS = len(rows) // NUM_INFO_ROWS_PER_POKEMON
                # print(NUM_POKEMON_ROWS, "rows of pokemon in table")


                for i in range(NUM_POKEMON_ROWS):
                    # print(i, "ROW*******************")
                    game_version = "BD"
                    pokemon_row_list = []
                    start = i * NUM_INFO_ROWS_PER_POKEMON + 1
                    excludedEnd = i * NUM_INFO_ROWS_PER_POKEMON + NUM_INFO_ROWS_PER_POKEMON  + 1
                    # print("start:", start, "excludedEnd:", excludedEnd)
                    processPokemonRows(rows[start: excludedEnd], pokemon_row_list, pokemon_in_table_list, game_version, encounter_method, key, anchor)
                    
                    if table_index + 1 < table_count:
                        game_version = "SP"
                        # start = i * NUM_INFO_ROWS_PER_POKEMON + 1
                        # excludedEnd = i * NUM_INFO_ROWS_PER_POKEMON + NUM_INFO_ROWS_PER_POKEMON+ 1
                        # print("start:", start, "excludedEnd:", excludedEnd)
                        next_table_rows = tables[table_index + 1].find_all("tr")
                        processPokemonRows(next_table_rows[start: excludedEnd], pokemon_row_list, pokemon_in_table_list, game_version, encounter_method, key, anchor)
                
                table_index += 2
                curr_anchor_table_index += 2
            else:
                table_index += 1
                curr_anchor_table_index += 1
    pass

def processGrandUndergroundTables(tables, anchor_pairs, pokemon_in_table_list):
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
    #             "game_version": "BDSP"
    #         },
    #     }
    tables.pop(0)
    table_count = len(tables)
    table_index = 0

    curr_anchor_index = 0
    curr_anchor_table_index = 0
    curr_anchor = anchor_pairs[curr_anchor_index]

    # tables = soup.find_all("table", class_=re.compile(r"\b(?:extra)?dextable\b"))
    encounter_method = {}
    encounter_requisite = ""
    while table_index < table_count:
        table = tables[table_index]
        if table_index % 3 == 0:
            h = table.find("h4")
            # print("Fake", h.text)
            encounter_requisite = h.text
            table_index += 1
            continue

        # Determine anchor limit & anchor
        anchor = "Main Area" # Default value
        if len(curr_anchor) > 0:
            # print(curr_anchor)
            anchor_name, anchor_limit = curr_anchor
            # print("anchor name: ", anchor_name, "anchor limit: ", anchor_limit)
            if curr_anchor_table_index < anchor_limit:
                anchor = anchor_name
            else:
                curr_anchor_index += 1
                curr_anchor_table_index = 0
                curr_anchor = anchor_pairs[curr_anchor_index]
                anchor_name, new_anchor_limit = curr_anchor
                anchor = anchor_name

        # If table after getting encounter_requisite
        if (table_index - 1) % 3 == 0:

            rows = table.find_all("tr")
            # print(rows[0])
            encounter_method = grabEncounterMethod(rows[0])
            encounter_method["requisite"] = encounter_requisite

            rows = rows[3:]

            # Find number of pokemon rows
            NUM_INFO_ROWS_PER_POKEMON = 6
            NUM_POKEMON_ROWS = len(rows) // NUM_INFO_ROWS_PER_POKEMON

            for i in range(NUM_POKEMON_ROWS):
                game_version = [34]
                pokemon_row_list = []
                start = i * NUM_INFO_ROWS_PER_POKEMON
                excludedEnd = i * NUM_INFO_ROWS_PER_POKEMON + NUM_INFO_ROWS_PER_POKEMON
                # print("start:", start, "excludedEnd:", excludedEnd)
                processPokemonRows(rows[start: excludedEnd], pokemon_row_list, pokemon_in_table_list, game_version, encounter_method, key, anchor)
                # if table_index == 1:
                    # print(pokemon_row_list)
                if table_index + 1 < table_count:
                    game_version = [35]
                    next_table_rows = tables[table_index + 1].find_all("tr")
                    start = i * NUM_INFO_ROWS_PER_POKEMON + 1
                    excludedEnd = i * NUM_INFO_ROWS_PER_POKEMON + NUM_INFO_ROWS_PER_POKEMON  + 1
                    # print("start:", start, "excludedEnd:", excludedEnd)
                    processPokemonRows(next_table_rows[start: excludedEnd], pokemon_row_list, pokemon_in_table_list, game_version, encounter_method, key, anchor)

            table_index += 2
            curr_anchor_table_index += 2
        else:
            table_index += 1
            curr_anchor_table_index += 1

    # print(anchor_pairs)
    
def processSolaceonRuinsTables(anchor_pairs, pokemon_in_table_list, key):
    # print(anchor_pairs)
    for anchor_pair in anchor_pairs:
        anchor_name, anchor_value = anchor_pair

        pokemon = {
            "pokemon" : {
                "national_dex_id": 201,
                "rvId": 1
            },
            "encounter_method": {
                "method": "Random Encounter",
                "time_of_day": "Anytime",
                "item_needed": None,
                "requisite": None,
                "chance": "100%"
            },
            "location": {
                "name": key,
                "area_anchor": anchor_name,
                "region": "Sinnoh",
                "game_version": [34, 35],
            },
        }

        pokemon_in_table_list.append(pokemon)
#
#
#
# Fetching pokemon from each endpoint
starting_url = "https://www.serebii.net"
response = requests.get(starting_url + "/pokearth/sinnoh/")
soup = BeautifulSoup(response.text, 'html.parser')

sinnoh_form = soup.find("form", attrs={"name": "sinnoh"})
options = sinnoh_form.find_all("option")
locations_endpoint_dict = {}

for option in options[1:]:
    location_name = option.text
    locations_endpoint_dict[location_name] = option.get("value")
    pokemon_in_location_dict[location_name] = {}    

# These endpoints have set area_anchors that hold different pokemon encounters
# area_anchors_endpoints = [
#     "/pokearth/sinnoh/route204.shtml",
#     "/pokearth/sinnoh/route205.shtml",
#     "/pokearth/sinnoh/route210.shtml",
#     "/pokearth/sinnoh/route211.shtml",
#     "/pokearth/sinnoh/route212.shtml",
#     "/pokearth/sinnoh/fuegoironworks.shtml",
#     "/pokearth/sinnoh/grandunderground.shtml",
#     "/pokearth/sinnoh/greatmarsh.shtml",
#     "/pokearth/sinnoh/ironisland.shtml",
#     "/pokearth/sinnoh/lakeacuity.shtml",
#     "/pokearth/sinnoh/lakevalor.shtml",
#     "/pokearth/sinnoh/lakeverity.shtml",
#     "/pokearth/sinnoh/losttower.shtml",
#     "/pokearth/sinnoh/mt.coronet.shtml",
#     "/pokearth/sinnoh/oldchateau.shtml",
#     "/pokearth/sinnoh/oreburghgate.shtml",
#     "/pokearth/sinnoh/oreburghmine.shtml",
#     "/pokearth/sinnoh/ruinsmaniac'scave.shtml",
#     "/pokearth/sinnoh/snowpointtemple.shtml",
#     "/pokearth/sinnoh/solaceonruins.shtml",
#     "/pokearth/sinnoh/starkmountain.shtml",
#     "/pokearth/sinnoh/trophygarden.shtml",
#     "/pokearth/sinnoh/turnbackcave.shtml",
#     "/pokearth/sinnoh/victoryroad.shtml",
#     "/pokearth/sinnoh/waywardcave.shtml"
#     ]
    
area_anctabs = {}
# print(pokemon_list)
# Save pokemon_list as JSON file
with open("area_anchors.json", "r") as f:
    area_anctabs = json.load(f)

# locations_endpoint_dict = {
#     "Grand Underground" : "/pokearth/sinnoh/grandunderground.shtml"
# }       

# key = Official location name
# value = Endpoint to append to url
for key, value in locations_endpoint_dict.items():

    print(value)

    area_anchors = {}
    if key in area_anctabs.keys():
        area_anchors = area_anctabs[key]
        # {
        #     "anchors": {
        #         "South": 16,
        #         "North": 8
        #     }
        # }
        # print(key , " has area_anchors")
        # print(area_anctabs[key])
    
    response = requests.get("https://www.serebii.net" + value)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Check if value has valid area anchors (Those that do include img tag inside anctab)
    # All endpoints contain at least 1 anctab (to select game generation). Area anc_tab will be the next anctab afterf
    # anctab_tables = soup.find_all("table", class_="anctab")
    # if len(anctab_tables) > 1:
    #     area_anctabs_table = anctab_tables[1]
    #     found_imgs = area_anctabs_table.find_all("img")
    #     if len(found_imgs) > 0:
    #         # print(value, "has area anchors")
    #         area_anctabs[key] = {}
    #         area_anchors = {}
    #         area_anctabs_a_tags = area_anctabs_table.find_all("a")
    #         for a in area_anctabs_a_tags:
    #             if len(a.text) > 0:
    #                 area_anchors[a.text] = 0
    #         area_anctabs[key]["anchors"] = area_anchors

    #         print(area_anctabs)


    # Encounter data is inside tables classified by either:
    #   "extradextable"
    #   "dextable"

    # Grabbing all tables
    tables = soup.find_all("table", class_=re.compile(r"\b(?:extra)?dextable\b"))
    # print(tables)

    pokemon_in_table_list = []

    table_count = len(tables)
    table_index = 0

    anchor_pairs = []
    curr_anchor = {}
    curr_anchor_index = 0
    curr_anchor_table_index = 0
    if len(area_anchors) > 0:
        curr_anchors = area_anchors["anchors"]
        # print(curr_anchors)
        #       {
        #         "South": 16,
        #         "North": 8
        #       }
        anchor_pairs = list(curr_anchors.items())
        # print(anchor_pairs)
        #       [('South', 16), ('North', 8)]
        curr_anchor = anchor_pairs[curr_anchor_index]
        # print(curr_anchor)
        #       ('South', 16)

    # Skipping Grand Underground cuz fuckkk me
    # Skipping Solaceon Runs cuz fuccckkk me again
    if value == "/pokearth/sinnoh/trophygarden.shtml":
        processTrophyGardenTables(tables, anchor_pairs, pokemon_in_table_list)
    elif value == "/pokearth/sinnoh/grandunderground.shtml":
        processGrandUndergroundTables(tables, anchor_pairs, pokemon_in_table_list)
    elif value == "/pokearth/sinnoh/solaceonruins.shtml":
        processSolaceonRuinsTables(anchor_pairs, pokemon_in_table_list, key)
    else:
        while table_index < table_count:
            table = tables[table_index]

            # Determine anchor limit & anchor
            anchor = "Main Area" # Default value

            if len(curr_anchor) > 0:
                # print(curr_anchor)
                anchor_name, anchor_limit = curr_anchor
                # print("anchor name: ", anchor_name, "anchor limit: ", anchor_limit)
                if curr_anchor_table_index < anchor_limit:
                    anchor = anchor_name
                else:
                    curr_anchor_index += 1
                    curr_anchor_table_index = 0
                    curr_anchor = anchor_pairs[curr_anchor_index]
                    anchor_name, new_anchor_limit = curr_anchor
                    anchor = anchor_name

            # print(anchor)

            rows = table.find_all("tr")
            # Check if table has class extradextable
            # If so, process itself (+ grab encounter_method) and the next table
            if 'extradextable' in table.get('class', []):
                encounter_method = grabEncounterMethod(rows[0])
                processTable(rows[1:], pokemon_in_table_list, encounter_method, key, anchor)

                if table_index + 1 < table_count:
                    rows = tables[table_index + 1].find_all("tr")
                    processTable(rows, pokemon_in_table_list, encounter_method, key, anchor)
                
                table_index += 2
                curr_anchor_table_index += 2
            else:
                # Otherwise, check if gift pokemon table
                encounter_method = grabEncounterMethod(rows[0])
                if encounter_method["method"] == "Gift Pokémon":
                    processGiftTable(rows[1:], encounter_method, key, pokemon_in_table_list, anchor)

                table_index += 1
                curr_anchor_table_index += 1

    # Add pokemon_list to locations_dict
    pokemon_in_location_dict[key] = pokemon_in_table_list
                
# with open("area_anchors.json", "w") as f:
#     json.dump(area_anctabs, f, indent=4)

# print(pokemon_list)
# Save pokemon_list as JSON file
with open("encounters.json", "w") as f:
    json.dump(pokemon_in_location_dict, f, indent=4)

        
        




