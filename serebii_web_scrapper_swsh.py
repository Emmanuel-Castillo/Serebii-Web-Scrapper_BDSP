import requests
from bs4 import BeautifulSoup
import json
import re
import copy

TIME_OF_DAY = ["Morning","Day","Evening","Night"]
ITEM_NEEDED = ["Old Rod","Good Rod","Super Rod"]
WEATHER = ["All Weather", "Normal Weather", "Overcast", "Raining", "Thunderstorm", "Snowing", "Snowstorm", "Sandstorm", "Intense Sun", "Fog"]
# RARITY = ["Rare","Very Rare"]



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
            p1["location"]["game_version"] = [32, 33]

            # if (p0["location"] == p1["location"]) and (p0["location"] == "Iron Island"):
            #     print(p0, p1)
            #     print("p0 is already in the list!!!!")
            return True
    return False

def grabEncounterMethod(row, curr_weather):
    encounter_method = {}
    # extra_row = table.find_all("tr")[0]
    a = row.find(re.compile("a"))
    encounter_method["method"] = a.text
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
        else: 
            encounter_method["requisite"] = second_word
        # elif second_word in RARITY:
        #     encounter_method["rarity"] = second_word
        # else:
            # print(second_word)

    # Add curr_weather to requisite
    if curr_weather:
        if encounter_method["requisite"] is not None:
            encounter_method["requisite"] += " - " + curr_weather
        else:
            encounter_method["requisite"] = curr_weather

    return encounter_method

    # print("Encounter method: ", encounter_method)
    # print("Time of day: " + time_of_day)

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
        img_src_split_words = re.split(r"[/.-]", img_src)
        # print(img_src_split_words)
        nat_dex_id = img_src_split_words[4]

        # See if the next char is 'g' for Galarian form
        # 'g' should be the only char of concern
        if (len(img_src_split_words) > 5 and img_src_split_words[5] == 'g'):
            pokemon_row_list[i]["pokemon"]["rvId"] = 3
        else:
            pokemon_row_list[i]["pokemon"]["rvId"] = 1


        # SPECIFICALLY FOR ZAMAZENTA AND ETERNATUS IMGS FOR SHIELD TABLE
        if not nat_dex_id.isdigit():
            nat_dex_id = img_src_split_words[3]

        pokemon_row_list[i]["pokemon"]["national_dex_id"] = int(nat_dex_id)

def grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor):
    # Grabbing name
    # Start assigning size of pokemon list per row
    # As well as initialzing pokemon data appropriately
    cells = row.find_all("td")
    
    for i, cell in enumerate(cells):
        if (cell.text == "Zamazenta"):
            print("Zamazenta found!")
        pokemon_row_list[i]["pokemon"]["name"] = cell.text
        pokemon_row_list[i]["encounter_method"] = copy.deepcopy(encounter_method)
        pokemon_row_list[i]["location"] = {
            "name" : key,
            "area_anchor" : anchor,
            "region": "Galar",
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
            if cell.text == "Pokémon Sword":
                game_version.append(32)
            elif cell.text == "Pokémon Shield":
                game_version.append(33)

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
    game_version = [32, 33]
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
                requisite = None
                if len(cell.text) > 0:
                    requisite = cell.text
                    print(requisite)
                    # print(cell.text)
                    # print(pokemon_row_list[i]["pokemon"]["name"])
                    # print(cell.text)
                    # pokemon_row_list[i]["encounter_method"]["requisite"] = cell.text
                    # print(pokemon_row_list[i]["pokemon"]["name"] + " has requisite: " + pokemon_row_list[i]["encounter_method"]["requisite"])
                    # for pokemon in pokemon_row_list:
                        # print(pokemon["pokemon"]["name"] + ": " + pokemon["encounter_method"]["requisite"])
                # else:
                pokemon_row_list[i]["encounter_method"]["requisite"] = requisite
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
# Fetching pokemon from each endpoint
starting_url = "https://www.serebii.net"
response = requests.get(starting_url + "/pokearth/galar/")
soup = BeautifulSoup(response.text, 'html.parser')

region_form = soup.find("form", attrs={"name": "kalos"})
options = region_form.find_all("option")
locations_endpoint_dict = {}
area_anctabs = {}

for option in options[1:]:
    if option.text == "===":
        break
    location_name = option.text
    locations_endpoint_dict[location_name] = option.get("value")
    pokemon_in_location_dict[location_name] = {}    
    
# Read area achors from swsh file
with open("swsh_area_anchors.json", "r") as f:
    area_anctabs = json.load(f)

# SKIP AREAS
skip_areas = [
    "/pokearth/galar/circhester.shtml",
    "/pokearth/galar/hammerlocke.shtml"
]

# key = Official location name
# value = Endpoint to append to url
for key, value in locations_endpoint_dict.items():

    print(value)
    if value in skip_areas:
        print("SKIPPING...")
        continue

    # Grab anchors if location key present in area_anctabs
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

    # Encounter data is inside tables classified by either:
    #   "extradextable"
    #   "dextable"

    # Grabbing all tables
    tables = soup.find_all("table", class_=re.compile(r"\b(?:extra)?dextable\b"))
    # print(tables)

    extra_dextable_endpoints = []
    # Certain endpoints have extra dextables
    # if key in extra_dextable_endpoints:
    #     tables = tables[1:]

    # Pokemon in each endpoint
    pokemon_in_table_list = []

    curr_weather = None

    table_count = len(tables)
    table_index = 0

    # print(table_count, " tables present")
    # if table_count == 1:
    #     print(tables)

    anchor_pairs = []
    curr_anchor = {}
    curr_anchor_index = 0
    curr_anchor_table_index = 0
    # For location w/ anchors, set current anchor
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

    

    # Processing endpoint tables
    while table_index < table_count:
        table = tables[table_index]


        # Determine anchor limit & anchor
        anchor = "Main Area" # Default value
        if len(curr_anchor) > 0:
            # print(curr_anchor)
            anchor_name, anchor_limit = curr_anchor
            # print("anchor name: ", anchor_name, "anchor limit: ", anchor_limit)
            # Setting anchor if index < limit
            if curr_anchor_table_index < anchor_limit:
                anchor = anchor_name
            else:
                # Set new curr_anchor, anchor_name, anchor_limit, and anchor if reached limit
                curr_anchor_index += 1
                curr_anchor_table_index = 0
                curr_anchor = anchor_pairs[curr_anchor_index]
                anchor_name, anchor_limit = curr_anchor
                anchor = anchor_name

        print("table #", table_index, ", curr_anchor = ", curr_anchor, ", curr_anchor_table_index = ", curr_anchor_table_index)
        # print("Current anchor: ", anchor)

        # Tracker curr_weather & see if table indicates a new, different weather
        has_h4_tag = table.find(re.compile('^h[3-4]$'))
        # New weather indicates we are consuming first extradextable from grouping of tables
        # Every 2 tables after this one will be considered a pair (1 from SW, 1 from SH)
        if has_h4_tag and has_h4_tag.text in WEATHER and has_h4_tag.text != curr_weather:
            curr_weather = has_h4_tag.text
            # print(curr_weather)

            # Current table_index should be pointing to next table (first table of pair)
            table_index += 1

            # Also move anchor index???
            curr_anchor_table_index += 1

            # Check if no pairs in curr_weather exist (new table should be different weather)
            possible_new_weather_table = tables[table_index]
            has_h4_tag = possible_new_weather_table.find(re.compile('^h[3-4]$'))
            if has_h4_tag and has_h4_tag.text in WEATHER and has_h4_tag.text != curr_weather:
                a_name, a_limit = curr_anchor
                # print(key + " has zero tables in " + curr_weather + " at anchor " + a_name)
                continue


        # print("Current weather: ", curr_weather)
        # Set table again
        table = tables[table_index]
        # print("Current table: ", table)

        # Processing table
        # Some endpoints contain groupings of extradextable tables (overworld & weather encounters)
        # We track each table to see if they mark a new different weather. If so, every other two
        # tables will be considered a pair until the next weather has been reached
        # Do do by skipping the first table, and consuming the pairs of extradextable/dextable tables

        # NOTE: FIRST GROUPING OF TABLES INCLUDE AN EXTRADEXTABLE TABLE INDICATING WEATHER REQ.

        # First table
        rows = table.find_all("tr")
        # Should work for all pairs of tables; first table in pair MUST HAVE class name extradextable
        # Check if table has class extradextable
        # If so, process itself (+ grab encounter_method) and the next table
        if 'extradextable' in table.get('class', []):
            starting_index_first_table = 1
            # For all weather, except "All Weather", skip the first table second row
            if curr_weather is not None and curr_weather != "All Weather":
                starting_index_first_table = 2

            # Processing pair of tables
            encounter_method = grabEncounterMethod(rows[0], curr_weather)
            # print("Encounter method: ", encounter_method)

            # FOR ENERGY PLANT ONLY
            # INTERACTABLE POKEMON TABLE SHOULD HAVE TWO TABLES FOR VERSION EXCLUSIVES
            # BUT INSTEAD, SEREBII COMBINES THE TWO INTO ONE SINGLE TABLE WTFFFF
            if encounter_method["method"] == "Interactable Pokémon" and key == "Energy Plant":
                processTable(rows[starting_index_first_table:8], pokemon_in_table_list, encounter_method, key, anchor)
                processTable(rows[8:], pokemon_in_table_list, encounter_method, key, anchor)
                table_index += 1
                curr_anchor_table_index += 1
                continue

            # print(rows)
            # print(starting_index_first_table)
            # print(rows[starting_index_first_table])
            processTable(rows[starting_index_first_table:], pokemon_in_table_list, encounter_method, key, anchor)

            if table_index + 1 < table_count:
                rows = tables[table_index + 1].find_all("tr")
                processTable(rows, pokemon_in_table_list, encounter_method, key, anchor)
            
            table_index += 2
            curr_anchor_table_index += 2
        else:
            # Otherwise, check if gift pokemon table
            encounter_method = grabEncounterMethod(rows[0], curr_weather)
            if encounter_method["method"] == "Gift Pokémon":
                processGiftTable(rows[1:], encounter_method, key, pokemon_in_table_list, anchor)

            # Handle trade pokemon table!
            # Done elsewhere

            table_index += 1
            curr_anchor_table_index += 1

    # Add pokemon_list to locations_dict
    pokemon_in_location_dict[key] = pokemon_in_table_list
                

# print(pokemon_list)
# Save pokemon_list as JSON file
with open("swsh_encounters.json", "w") as f:
    json.dump(pokemon_in_location_dict, f, indent=4)

        
        




