import requests
from bs4 import BeautifulSoup
import json
import re

TIME_OF_DAY = ["Morning","Day","Evening","Night"]
ITEM_NEEDED = ["Old Rod","Good Rod","Super Rod"]
RARITY = ["Rare","Very Rare"]

# JSON file to store all available Pokemon
pokemon_in_location_dict = {}

def checkIfPokemonInBothVersions(p0, pokemon_list):
    for p1 in pokemon_list:
        if (p0["name"] == p1["name"]) and (p0["encounter_method"] == p1["encounter_method"]) and (p0["chance"] == p1["chance"]) and (p0["location"] == p1["location"]):
            p1["game_version"] = "Both"

            # if (p0["location"] == p1["location"]) and (p0["location"] == "Iron Island"):
            #     print(p0, p1)
            #     print("p0 is already in the list!!!!")
            return True
    return False

def grabEncounterMethod(table):
    encounter_method = {}
    extra_row = table.find_all("tr")[0]
    h = extra_row.find(re.compile("^h"))
    encounter_method["method"] = h.text
    encounter_method["time_of_day"] = "Anytime"
    encounter_method["requisite"] = "None"
    encounter_method["rarity"] = "Common"

    # check if table includes time of day by splitting
    split_words = encounter_method["method"].split(' - ')
    if len(split_words) > 1:
        encounter_method["method"] = split_words[0]
        second_word = split_words[1]
        if second_word in TIME_OF_DAY:
            encounter_method["time_of_day"] = second_word
        elif second_word in ITEM_NEEDED:
            encounter_method["requisite"] = second_word
        elif second_word in RARITY:
            encounter_method["rarity"] = second_word
        else:
            print(second_word)

    return encounter_method

    # print("Encounter method: ", encounter_method)
    # print("Time of day: " + time_of_day)

def grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor):
    # Grabbing name
    # Start assigning size of pokemon list per row
    # As well as initialzing pokemon data appropriately
    cells = row.find_all("td")

    # Clear and extend the existing list instead of replacing it
    pokemon_row_list.clear()  
    pokemon_row_list.extend([{} for _ in range(len(cells))])
    
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["name"] = cell.text
        pokemon_row_list[i]["encounter_method"] = encounter_method
        pokemon_row_list[i]["game_version"] = game_version
        pokemon_row_list[i]["location"] = {
            "name" : key,
            "area_anchor" : anchor
        }
        # print("Pokemon: ", cell.text)

def grabPokemonTypes(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        types = cell.find_all("a")
        type_list = []
        for type in types:
            img = type.find("img")
            img_src = img.get("src")
            type_name = re.split(r"[/.]", img_src)
            type_list.append(type_name[3].title())
            # print("Type: ", type_name[3].title())

        pokemon_row_list[i]["type"] = type_list

def grabPokemonChance(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["chance"] = cell.text
        # print("Chance: ", cell.text)

def grabPokemonLevels(row, pokemon_row_list):
    cells = row.find_all("td")
    for i, cell in enumerate(cells):
        pokemon_row_list[i]["level"] = cell.text
        # print("Levels: ", cell.text)

def processRow(row, pokemon_in_table_list, encounter_method, key, anchor):
    pass

# Table should start at row that collect game_version
def processTable(rows, pokemon_in_table_list, encounter_method, key, anchor):

    NUMBER_ROWS_POKEMON_DETAILS = 6
    # Grab # rows of pokemon
    num_rows_pokemon = len(rows[1:]) / NUMBER_ROWS_POKEMON_DETAILS

    game_version = ""
    pokemon_row_list = []
    for index, row in enumerate(rows):

        # Grabbing game version
        if index == 0:
            cell = row.find("td")
            # print("Game version: ", cells.text)
            game_version = cell.text

        elif index == 2:
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)
        # Grabbing type
        elif index == 3:
            grabPokemonTypes(row, pokemon_row_list)

        # Grabbing chance
        elif index == 4:
            grabPokemonChance(row, pokemon_row_list)

        # Grabbing level
        elif index == 6:
            grabPokemonLevels(row, pokemon_row_list)

        # Print current pokemon_row_list
        # print(pokemon_row_list)

    # Add new pokemon_row_list to pokemon_list
    for pokemon in pokemon_row_list:
        # Check if pokemon already in locations_dict[location], and has the same data (except game version)
        # If so, do not append pokemon and modify pokemon in locations_dict[location].game_version = "Both"
        if not checkIfPokemonInBothVersions(pokemon, pokemon_in_table_list):
            pokemon_in_table_list.append(pokemon)

def processGiftTable(table, encounter_method, key, pokemon_in_table_list, anchor):
    rows = table.find_all("tr")
    game_version = "Both"
    pokemon_row_list = []
    for index, row in enumerate(rows[1:]):

        # Grabbing name
        # Start assigning size of pokemon list per row
        # As well as initialzing pokemon data appropriately
        if index == 1:
            grabPokemonNames(row, game_version, encounter_method, key, pokemon_row_list, anchor)

        # Grabbing type
        elif index == 2:
            grabPokemonTypes(row, pokemon_row_list)

        # Grabbing level
        elif index == 4:
            grabPokemonLevels(row, pokemon_row_list)

        # Grabbing requisite for each Gift Pokemon & setting chance
        elif index == 5:
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                pokemon_row_list[i]["encounter_method"]["requisite"] = cell.text
                pokemon_row_list[i]["chance"] = "100%"

    # Print current pokemon_row_list

    # Add new pokemon_row_list to pokemon_list
    # Gift pokemon are automatically initialized to be acquired in both games
    for pokemon in pokemon_row_list:
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

# key = Official location name
# value = Endpoint to append to url
for key, value in locations_endpoint_dict.items():

    print(value)
    
    # Skipping Grand Underground cuz fuckkk me
    # Skipping Solaceon Runs cuz fuccckkk me again
    if value == "/pokearth/sinnoh/grandunderground.shtml" or value == "/pokearth/sinnoh/solaceonruins.shtml" or value == "/pokearth/sinnoh/trophygarden.shtml":
        print("Skipping ", value)
        continue

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

        # Check if table has class extradextable
        # If so, process itself (+ grab encounter_method) and the next table
        if 'extradextable' in table.get('class', []):
            encounter_method = grabEncounterMethod(table)
            rows = table.find_all("tr")
            processTable(rows[1:], pokemon_in_table_list, encounter_method, key, anchor)

            if table_index + 1 < table_count:
                rows = tables[table_index + 1].find_all("tr")
                processTable(rows, pokemon_in_table_list, encounter_method, key, anchor)
            
            table_index += 2
            curr_anchor_table_index += 2
        else:
            # Otherwise, check if gift pokemon table
            encounter_method = grabEncounterMethod(table)
            if encounter_method["method"] == "Gift Pokémon":
                processGiftTable(table, encounter_method, key, pokemon_in_table_list, anchor)

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

        
        




