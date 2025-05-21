import requests
from bs4 import BeautifulSoup
import json
import re

TIME_OF_DAY = ["Morning","Day","Evening","Night"]
ITEM_NEEDED = ["Old Rod","Good Rod","Super Rod"]
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
            p1["location"]["game_version"] = [30, 31]

            # if (p0["location"] == p1["location"]) and (p0["location"] == "Iron Island"):
            #     print(p0, p1)
            #     print("p0 is already in the list!!!!")
            return True
    return False

def grabEncounterMethod(row):
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
        nat_dex_id = img_src_split_words[3]

        # See if next char is 'a' for Alolan form (only other regional variant besides default)
        if (len(img_src_split_words) > 4 and img_src_split_words[4] == 'a'):
            pokemon_row_list[i]["pokemon"]["rvId"] = 2
        else: 
            # Default regional variant id
            pokemon_row_list[i]["pokemon"]["rvId"] = 1

        pokemon_row_list[i]["pokemon"]["national_dex_id"] = int(nat_dex_id)
        

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
            "region": "Kanto",
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
            if cell.text == "Pokémon: Let's Go, Pikachu!":
                game_version.append(30)
            elif cell.text == "Pokémon: Let's Go, Eevee!":
                game_version.append(31)

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
    game_version = [30, 31]
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
                if len(cell.text) > 0:
                    pokemon_row_list[i]["encounter_method"]["requisite"] = cell.text
                else:
                    pokemon_row_list[i]["encounter_method"]["requisite"] = None
                pokemon_row_list[i]["encounter_method"]["chance"] = "100%"

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
response = requests.get(starting_url + "/pokearth/kanto/")
soup = BeautifulSoup(response.text, 'html.parser')

region_form = soup.find("form", attrs={"name": "kanto"})
options = region_form.find_all("option")
locations_endpoint_dict = {}
area_anctabs = {}

for option in options[1:]:
    location_name = option.text
    locations_endpoint_dict[location_name] = option.get("value")
    pokemon_in_location_dict[location_name] = {}    
    
# Read area achors from lgpe file
with open("lgpe_area_anchors.json", "r") as f:
    area_anctabs = json.load(f)

# SKIP AREAS
skip_areas = [
    "/pokearth/kanto/route26.shtml",
    "/pokearth/kanto/route27.shtml",
    "/pokearth/kanto/route28.shtml",
    "/pokearth/kanto/receptiongate.shtml",
    "/pokearth/kanto/safarizone.shtml",
    "/pokearth/kanto/tohjofalls.shtml"
]

# key = Official location name
# value = Endpoint to append to url
for key, value in locations_endpoint_dict.items():

    print(value)
    if value in skip_areas:
        print("SKIPPING...")
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

    # Encounter data is inside tables classified by either:
    #   "extradextable"
    #   "dextable"

    # Grabbing all tables
    tables = soup.find_all("table", class_=re.compile(r"\b(?:extra)?dextable\b"))
    # print(tables)

    extra_dextable_endpoints = [
        "Celadon City",
        "Cerulean City",
        "Fuchsia City",
    ]
    # Certain endpoints have extra dextables
    if key in extra_dextable_endpoints:
        tables = tables[1:]

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

    # Processing endpoint tables
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

            # Handle trade pokemon table!

            table_index += 1
            curr_anchor_table_index += 1

    # Add pokemon_list to locations_dict
    pokemon_in_location_dict[key] = pokemon_in_table_list
                
# Fixing Gift Pokemon from Vermillion City
pokemon_list = pokemon_in_location_dict["Vermilion City"] 
squirtle = next((pokemon for pokemon in pokemon_list if pokemon["pokemon"]["name"] == "Squirtle"), None)

if squirtle:
    squirtle["encounter_method"]["requisite"] = "60 Pokémon Caught"

persian = next((pokemon for pokemon in pokemon_list if pokemon["pokemon"]["name"] == "Persian"), None)

if persian:
    persian["encounter_method"]["requisite"] = "Catch 5 Growlithe"
    persian["location"]["game_version"] = [30]

arcanine = next((pokemon for pokemon in pokemon_list if pokemon["pokemon"]["name"] == "Arcanine"), None)

if arcanine:
    arcanine["encounter_method"]["requisite"] = "Catch 5 Meowth"
    arcanine["location"]["game_version"] = [31]

pokemon_list.append({
            "pokemon": {
                "national_dex_id": 74,
                "name": "Geodude",
                "type1": "Rock",
                "type2": "Electric"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Geodude",
                "chance": "100%"
            },
            "location": {
                "name": "Verimilion City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })

# Add Fossils (revived in Pewter City)
pokemon_list = pokemon_in_location_dict["Pewter City"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 138,
                "name": "Omanyte",
                "type1": "Rock",
                "type2": "Water"
            },
            "encounter_method": {
                "method": "Gift Pok\u00e9mon",
                "time_of_day": "Anytime",
                "requisite": "Helix Fossil in Mt. Moon",
                "chance": "100%"
            },
            "location": {
                "name": "Pewter City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 142,
                "name": "Kabuto",
                "type1": "Rock",
                "type2": "Water"
            },
            "encounter_method": {
                "method": "Gift Pok\u00e9mon",
                "time_of_day": "Anytime",
                "requisite": "Dome Fossil in Mt. Moon",
                "chance": "100%"
            },
            "location": {
                "name": "Pewter City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })
        
# Adding Trades
pokemon_list = pokemon_in_location_dict["Cerulean City"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 19,
                "name": "Ratata",
                "type1": "Dark",
                "type2": "Normal"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Ratata",
                "chance": "100%"
            },
            "location": {
                "name": "Cerulean City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })

pokemon_list = pokemon_in_location_dict["Lavender Town"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 50,
                "name": "Ratata",
                "type1": "Ground",
                "type2": "Steel"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Diglett",
                "chance": "100%"
            },
            "location": {
                "name": "Lavender Town",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })

pokemon_list = pokemon_in_location_dict["Celadon City"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 27,
                "name": "Ratata",
                "type1": "Ice",
                "type2": "Steel"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Sandshrew",
                "chance": "100%"
            },
            "location": {
                "name": "Celadon City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30]
            }
        })
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 50,
                "name": "Vulpix",
                "type1": "Fire",
                "type2": None
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Vulpix",
                "chance": "100%"
            },
            "location": {
                "name": "Celadon City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [31]
            }
        })

pokemon_list = pokemon_in_location_dict["Saffron City"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 26,
                "name": "Ratata",
                "type1": "Electric",
                "type2": "Psychic"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Raichu",
                "chance": "100%"
            },
            "location": {
                "name": "Saffron City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })

pokemon_list = pokemon_in_location_dict["Fuchsia City"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 105,
                "name": "Marowak",
                "type1": "Fire",
                "type2": "Ghost"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Marowak",
                "chance": "100%"
            },
            "location": {
                "name": "Fuchsia City",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })

pokemon_list = pokemon_in_location_dict["Cinnabar Island"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 88,
                "name": "Grimer",
                "type1": "Poison",
                "type2": "Dark"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Grimer",
                "chance": "100%"
            },
            "location": {
                "name": "Cinnabar Island",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30]
            }
        })
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 52,
                "name": "Marowak",
                "type1": "Dark",
                "type2": None
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Meowth",
                "chance": "100%"
            },
            "location": {
                "name": "Cinnabar Island",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [31]
            }
        })

pokemon_list = pokemon_in_location_dict["Indigo Plateau"] 
pokemon_list.append({
            "pokemon": {
                "national_dex_id": 103,
                "name": "Exeggutor",
                "type1": "Grass",
                "type2": "Dragon"
            },
            "encounter_method": {
                "method": "Trade",
                "time_of_day": "Anytime",
                "requisite": "Trade Kantonian Exeggutor",
                "chance": "100%"
            },
            "location": {
                "name": "Indigo Plateau",
                "area_anchor": "Main Area",
                "region": "Kanto",
                "game_version": [30, 31]
            }
        })

# print(pokemon_list)
# Save pokemon_list as JSON file
with open("lgpe_encounters.json", "w") as f:
    json.dump(pokemon_in_location_dict, f, indent=4)

        
        




