import requests
import re
import json
import copy
from bs4 import BeautifulSoup

TIME_OF_DAY = ["Morning", "Day", "Evening", "Night"]

# {
#             "pokemon": {
#                 "rvId": 1,
#                 "national_dex_id": 572,
#                 "name": "Minccino"
#             },
#             "encounter_method": {
#                 "method": "Random in Grass",          // Location field for each encounter entry
#                 "time_of_day": "Anytime",
#                 "requisite": "Normal Weather",        // Biome field  the encounter can occur
#                 "item_needed": null,
#                 "chance": "5%"
#             },
#             "location": {
#                 "name": "Rolling Fields",             // keys in the location dict
#                 "area_anchor": "Main Area",           // markers serebii displays on the map (encounter txt files are different between markers in the same location)
#                 "region": "Galar",
#                 "game_version": [
#                     33
#                 ]
#             }
#         }

BASE_URL = "https://www.serebii.net/pokearth/paldea/spawntable/{}.txt"
SEREBII_URL = "https://www.serebii.net/pokearth/paldea/{}.shtml"

# locations dict contains array of encounter txt files stored for each memorable loation in the Paldean region
locations = {
    "Socarrat Trail": [23, 20, 21, 25, 19, 22, 22],
    "Casseroya Lake": [165, 166, 171, 164, 175, 177, 156, 176, 174, 170, 169, 163, 168, 178, 173, 172, 167, 101, 105],
    "Area Three": [289, 179, 288, 217, 94, 180],
    "Glaseado Mountain (North)": [216, 92, 214, 213, 91, 159, 161, 153, 212, 154, 93, 152, 155, 158, 160, 34, 157, 162 ]
}

# mass_outbreak_loc = [
#     "South_Province_(Area_Three)"
# ]
locations_pokemon_dict = {}
    
# for key, value in locations.items():
#     for locTxtFile in value:
# url = BASE_URL.format(locTxtFile)

locations = {
    "South Province": ["Poco_Path", "Inlet_Grotto", "South_Paldean_Sea", "South_Province_(Area_One)", "South_Province_(Area_Two)", "South_Province_(Area_Three)", "South_Province_(Area_Four)", "South_Province_(Area_Five)", "South_Province_(Area_Six)", "Alfornada_Cavern"],
    "East Province": ["Tagtree_Thicket", "East_Paldean_Sea", "East_Province_(Area_One)", "East_Province_(Area_Two)", "East_Province_(Area_Three)"],
    "West Province": ["Asado_Desert", "West_Paldean_Sea", "West_Province_(Area_One)", "West_Province_(Area_Two)", "Colonnade_Hollow", "West_Province_(Area_Three)"],
    "North Province": ["Glaseado_Mountain", "Casseroya_Lake", "Dalizapa_Passage", "Socarrat_Trail", "North_Paldean_Sea", "North_Province_(Area_One)", "North_Province_(Area_Two)", "North_Province_(Area_Three)"],
    "Great Crater of Paldea": ["Area_Zero", "Zero_Lab"]
}

loc_mult_areas = {
    "Glaseado Mountain": ["Southern Mountain", "Northern Mountain"],
    "Dalizapa Passage": ["Northern Passage", "Western Passage"],
    "Area Zero": ["Upper Field", "Lower Field", "Small Cave", "Station No. 3 Cave", "Waterfall Cave", "Grassy Cave", "Depths"]
}
url = "https://bulbapedia.bulbagarden.net/wiki/{}"

def processTable(table, loc_name, curr_anchor):
    print(f"Processing table for {curr_anchor}")
    rows = table.find_all('tr')

    # Default variables before consuming all encounters for table
    biome = "Land"
    biome_pokemon = []
    time_of_day_total_weights = {
        "Morning": 0,
        "Day": 0,
        "Evening": 0,
        "Night": 0
    }
    encounter_contains_mult_weights = False

    for i, row in enumerate(rows[2:]):
        # If new biome section of table encountered, reset default variables
        if not row.has_attr('style'):

            # Assess if encounter_contains_mult_weights is either False or True
            if not encounter_contains_mult_weights:
                total_weight = time_of_day_total_weights["Day"]     # Total weight is the same for the other times of the day
                for pokemon in biome_pokemon:
                    pokemon_weight = pokemon["encounter_method"]["chance"]
                    pokemon_encounter_rate = pokemon_weight / total_weight
                    pokemon["encounter_method"]["chance"] = str(f"{(pokemon_encounter_rate) * 100:.2f}%")

            else:
                # print("POKEMON WITH MULT WEIGHTS INCLUDED")
                pokemon_copies = []
                for pokemon in biome_pokemon:

                    # Check if pokemon encounter chance is a digit (only one weight for anytime), or a list (mult weights for certain times)
                    if isinstance(pokemon["encounter_method"]["chance"], list):
                        # print(pokemon["pokemon"]["name"], " has multiple weights...")
                        for weight_index, weight_key in enumerate(time_of_day_total_weights.keys()):
                            pokemon_copy = copy.deepcopy(pokemon)
                            pokemon_copy["encounter_method"]["time_of_day"] = weight_key
                            pokemon_weight = pokemon_copy["encounter_method"]["chance"][weight_index]

                            if pokemon_weight > 0:
                                pokemon_encounter_rate = pokemon_weight / time_of_day_total_weights[weight_key]
                                pokemon_copy["encounter_method"]["chance"] = str(f"{(pokemon_encounter_rate) * 100:.2f}%")
                                pokemon_copies.append(pokemon_copy)
                    else:
                        for weight_key in time_of_day_total_weights.keys():
                            pokemon_copy = copy.deepcopy(pokemon)
                            pokemon_copy["encounter_method"]["time_of_day"] = weight_key
                            pokemon_weight = pokemon_copy["encounter_method"]["chance"]
                            # print("Pokemon weight:", pokemon_weight)
                            # print(f"Total Weight for {weight_key}", time_of_day_total_weights[weight_key])
                            pokemon_encounter_rate = pokemon_weight / time_of_day_total_weights[weight_key]
                            pokemon_copy["encounter_method"]["chance"] = str(f"{(pokemon_encounter_rate) * 100:.2f}%")
                            pokemon_copies.append(pokemon_copy )

                biome_pokemon = pokemon_copies
            
            locations_pokemon_dict[loc_name] += biome_pokemon
            biome_pokemon = []
            biome = row.text
            # print(row.text)

            time_of_day_total_weights = {
                "Morning": 0,
                "Day": 0,
                "Evening": 0,
                "Night": 0
            }

            encounter_contains_mult_weights = False
        
        else:
            # Process Pokemon row
            pokemon = {
                "pokemon": {
                    "rvId": 1,
                    "national_dex_id": 0,
                    "name": ""
                },
                "encounter_method": {
                    "method": "Wild Encounter",
                    "time_of_day": "",
                    "requisite": f"Biome: {biome.strip()}\nTerrain: ",
                    "item_needed": None,
                    "chance": "-%"
                },
                "location": {
                    "name": loc_name,
                    "area_anchor": curr_anchor,
                    "region": "Paldea",
                    "game_version": []
                }
            }

            terrain_list = []
            cells = row.find_all(re.compile('t[d|h]'))
            for j, cell in enumerate(cells):

                # Grab id and name
                if j == 0:
                    a_tag = cell.find('a')
                    a_tag_split_words = re.split(r'[_|.|-]',  a_tag.get('href'))
                    nat_dex_id = a_tag_split_words[2].lstrip('0')
                    # print(nat_dex_id)
                    pokemon["pokemon"]["national_dex_id"] = int(nat_dex_id)

                    span_tag = a_tag.find_next('span')
                    name = span_tag.text
                    # print(name)
                    pokemon["pokemon"]["name"] = name
                    pokemon["pokemon"]["rvId"] = 5 if "Paldea" in a_tag_split_words else 1 

                # If in Scarlet
                elif j == 1:
                    if 'background:#F34134' in cell.get('style'):
                        # print("In Scarlet")
                        pokemon["location"]["game_version"].append(37)

                # If in Violet
                elif j == 2:
                    if 'background:#8334B7' in cell.get('style'):
                        # print("In Violet")
                        pokemon["location"]["game_version"].append(38)

                elif j == 3:
                    if '✔' in cell.text:
                        # print('In land')
                        terrain_list.append("Land")
                elif j == 4:
                    if '✔' in cell.text:
                        # print('In water surface')
                        terrain_list.append("Water Surface")
                elif j == 5:
                    if '✔' in cell.text:
                        # print('In underwater')
                        terrain_list.append("Underwater")
                elif j == 6:
                    if '✔' in cell.text:
                        # print('In overland')
                        terrain_list.append("Overland")
                elif j == 7:
                    if '✔' in cell.text:
                        # print('In sky')
                        terrain_list.append("Sky")
                        

                # Check time of day and chance (prob weight)
                elif j == 9:

                    # If only one weight for any time, simply add the integer to the field
                    if cell.get('style') == 'background:#FFF':
                        # print(cell.text +  " anytime!")
                        pokemon["encounter_method"]["time_of_day"] = "Anytime"

                        weight = cell.text
                        if not (cell.text.isdigit()):
                            weight = 1
                        else:
                            weight = int(weight)

                        pokemon["encounter_method"]["chance"] = weight
                        
                        # Add encounter weight to all total weights in dict
                        for key in time_of_day_total_weights.keys():
                            time_of_day_total_weights[key] += weight

                        # print(time_of_day_total_weights)

                    # If more than one weight, capture all weights for that encounter to use for later
                    else:

                        encounter_contains_mult_weights = True
                        # print("SETTING ECMW TO TRUE")

                        for dict_index, key in enumerate(time_of_day_total_weights.keys()):
                            time_of_day_total_weights[key] += int(cells[j + dict_index].text)

                        # When inside the mult_weights branch in the row conditional, check if this field is only a digit or a list
                        pokemon["encounter_method"]["chance"] = [
                            int(cells[j].text),
                            int(cells[j + 1].text),
                            int(cells[j + 2].text),
                            int(cells[j + 3].text),
                        ]
                        # print(cells[j].text + " in the morning")
                        # print(cells[j + 1].text + " in the day")
                        # print(cells[j + 2].text + " in the evening")
                        # print(cells[j + 3].text + " in the night")

            terrain_list = ', '.join(terrain_list)
            pokemon["encounter_method"]["requisite"] += terrain_list
            # print(pokemon)
            biome_pokemon.append(pokemon)
            # locations_pokemon_dict[loc_name].append(pokemon)


for key, values in locations.items():
    for value in values:
        loc_name = ' '.join(value.split('_'))
        locations_pokemon_dict[loc_name] = []
        # print(f"loc_name: {loc_name}")
        if loc_name == "Zero Lab":
            locations_pokemon_dict[loc_name] = [{
                    "pokemon": {
                        "rvId": 1,
                        "national_dex_id": 1007,
                        "name": "Koraidon"
                    },
                    "encounter_method": {
                        "method": "Special Pokémon",
                        "time_of_day": "Anytime",
                        "requisite": None,
                        "item_needed": None,
                        "chance": "100%"
                    },
                    "location": {
                        "name": loc_name,
                        "area_anchor": "Main Area",
                        "region": "Paldea",
                        "game_version": [37]
                    }
                },{
                    "pokemon": {
                        "rvId": 1,
                        "national_dex_id": 1008,
                        "name": "Miraidon"
                    },
                    "encounter_method": {
                        "method": "Special Pokémon",
                        "time_of_day": "Anytime",
                        "requisite": None,
                        "item_needed": None,
                        "chance": "100%"
                    },
                    "location": {
                        "name": "Zero Lab",
                        "area_anchor": "Main Area",
                        "region": "Paldea",
                        "game_version": [38]
                    }
                }]
            continue

        response = requests.get(url.format(value))
        print(url.format(value))

        if response.status_code == 200 and response.text.strip():
            html_snippet = response.text
            # print(f"\n=== Table for Marker ID {locTxtFile}")

            # Parsing HTML string to soup HTML tree
            soup = BeautifulSoup(html_snippet, 'html.parser')

            # Grab table of Pokemon
            all_h2 = soup.find_all('h2')

            if len(all_h2) > 0:
                for h2 in all_h2:
                    if (h2.text == "Pokémon"):
                        # h3 = h2.find_next('h3')
                        # print(h3.text)

                        # Check if location has mult areas
                        if loc_mult_areas.get(loc_name):

                            areas = loc_mult_areas[loc_name]
                            print(f"{loc_name} has mult areas: {areas}")
                            for area in areas:
                                h3_area_string = h2.find_next('h3', string=area)
                                table = h3_area_string.find_next('table')

                                if loc_name == "Glaseado Mountain":
                                    new_loc_name = f"{loc_name} ({area})"
                                    locations_pokemon_dict[new_loc_name] = []
                                    processTable(table, new_loc_name, "Main Area")
                                
                                else:
                                    processTable(table, loc_name, area)

                        else:
                            table = h2.find_next('table')
                            # print(table)
                            processTable(table, loc_name, "Main Area")
                                
                # Find num of Pokemon rows
                # ROWS = table.find_all('tr')
                # NUMS_ROWS = len(ROWS)
                # NUM_ROWS_INFO_PER_POKEMON_ROW = 9
                # NUM_ROWS_POKEMON = NUMS_ROWS // NUM_ROWS_INFO_PER_POKEMON_ROW

                # for i in range (NUM_ROWS_POKEMON):
                #     print(f"in row {i}")
                #     processRows(ROWS[(i * NUM_ROWS_INFO_PER_POKEMON_ROW) : (i * NUM_ROWS_INFO_PER_POKEMON_ROW + NUM_ROWS_INFO_PER_POKEMON_ROW)])
            else:
                print("No h2 tag found")
        else:
            print(f"{anchor}: url request failed.")

        # Go to Serebii to find both fixed spawns and tera encounters
        anchor = ''.join(re.split(re.compile('[_|(|)]'), value)).lower()
        print(anchor)
        print(SEREBII_URL.format(anchor))
        response = requests.get(SEREBII_URL.format(anchor))
        if response.status_code == 200 and response.text.strip():
            html_snippet = response.text

            # Parsing HTML string to soup HTML tree
            soup = BeautifulSoup(html_snippet, 'html.parser')

            tables = soup.find_all('table', attrs={'class': 'trainer'})
            for table in tables:
                # pokemon = {
                #     "pokemon": {
                #         "rvId": 1,
                #         "national_dex_id": 0,
                #         "name": ""
                #     },
                #     "encounter_method": {
                #         "method": f"{biome.strip()} - Wild Encounter",
                #         "time_of_day": "",
                #         "requisite": "",
                #         "item_needed": None,
                #         "chance": "-%"
                #     },
                #     "location": {
                #         "name": loc_name,
                #         "area_anchor": curr_anchor,
                #         "region": "Paldea",
                #         "game_version": []
                #     }
                # }
                
                first_row = table.find_next('tr')
                
                # Default values (set to if tera encounter)
                METHOD = ""
                NUM_ROWS_INFO_PER_POKEMON = 0
                
                if "Wild Tera Type Battles" in first_row.text:
                    METHOD = "Wild Tera Encounter"
                    NUM_ROWS_INFO_PER_POKEMON = 5
                elif "Fixed Spawns" in first_row.text:
                    METHOD = "Fixed Spawn"
                    NUM_ROWS_INFO_PER_POKEMON = 4

                else:
                    continue

                print(METHOD)

                rows = table.find_all('tr')[2:]

                NUM_ROWS = len(rows)
                NUM_ROWS_POKEMON = NUM_ROWS // 5

                table_pokemon = []

                for i in range(NUM_ROWS_POKEMON):
                    row_pokemon = []
                    current_row_pokemon = rows[i * NUM_ROWS_INFO_PER_POKEMON: (i * NUM_ROWS_INFO_PER_POKEMON) + NUM_ROWS_INFO_PER_POKEMON ]
                    img_row = current_row_pokemon[0]
                    cells = img_row.find_all('td')
                    for cell in cells:
                        img = cell.find('img')
                        src = img.get('src')
                        src_split_words = re.split(r'[/|.|-]', src)
                        id_index = 5 if 'small' in src_split_words else 4
                        nat_dex_dex_id = int(src_split_words[id_index])
                        rvId = 5 if "p" in src_split_words else 1
                        row_pokemon.append(
                                            {
                                "pokemon": {
                                    "rvId": 1,
                                    "national_dex_id": nat_dex_dex_id,
                                    "name": ""
                                },
                                "encounter_method": {
                                    "method": METHOD,
                                    "time_of_day": "Anytime",
                                    "requisite": None,
                                    "item_needed": None,
                                    "chance": "-%"
                                },
                                "location": {
                                    "name": loc_name,
                                    "area_anchor": "Main Area",
                                    "region": "Paldea",
                                    "game_version": [37, 38]
                                }
                            }
                        )


                    name_row = current_row_pokemon[1]
                    cells = name_row.find_all('td')
                    for i, cell in enumerate(cells):
                        name = cell.text
                        row_pokemon[i]["pokemon"]["name"] = name

                    for pokemon in row_pokemon:
                        if not pokemon in table_pokemon:
                            table_pokemon.append(pokemon)
                
                locations_pokemon_dict[loc_name] += table_pokemon

        else:
            print(f"{anchor}: url request failed")


with open("sv_encounters.json", "w") as f:
    json.dump(locations_pokemon_dict, f, indent=4)


