import requests
import re
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

# locations dict contains array of encounter txt files stored for each memorable loation in the Paldean region
locations = {
    "Socarrat Trail": [23, 20, 21, 25, 19, 22, 22],
    "Casseroya Lake": [165, 166, 171, 164, 175, 177, 156, 176, 174, 170, 169, 163, 168, 178, 173, 172, 167, 101, 105],
    "Area Three": [289, 179, 288, 217, 94, 180],
    "Glaseado Mountain (North)": [216, 92, 214, 213, 91, 159, 161, 153, 212, 154, 93, 152, 155, 158, 160, 34, 157, 162 ]
}

locations_pokemon_dict = {}
    
# for key, value in locations.items():
#     for locTxtFile in value:
# url = BASE_URL.format(locTxtFile)

locations = {
    "South Province": ["Naranja_Academy", "Uva_Academy", "Poco_Path", "Inlet_Grotto", "South_Paldean_Sea", "South_Province_(Area_One)", "South_Province_(Area_Two)", "South_Province_(Area_Three)", "South_Province_(Area_Four)", "South_Province_(Area_Five)", "South_Province_(Area_Six)", "Alfornada_Cavern"]
}
url = "https://bulbapedia.bulbagarden.net/wiki/{}"

for key, value in locations.items():
    loc_name = key
    locations_pokemon_dict[loc_name] = []
    
    for anchor in value:
        print(anchor)
        curr_anchor = anchor
        response = requests.get(url.format(anchor))

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

                        table = h2.find_next('table')
                        # print(table)

                        rows = table.find_all('tr')
                        print(len(rows), ' rows')

                        biome = ""
                        for i, row in enumerate(rows[2:]):
                            if not row.has_attr('style'):
                                biome = row.text
                                # print(row.text)

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
                                        "requisite": "",
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
                                cells = row.find_all(re.compile('t[d|h]'))
                                for j, cell in enumerate(cells):

                                    # Grab id and name
                                    if j == 0:
                                        a_tag = cell.find('a')
                                        nat_dex_id = re.split(r'[_|.|-]',  a_tag.get('href'))[2].lstrip('0')
                                        print(nat_dex_id)
                                        pokemon["pokemon"]["national_dex_id"] = int(nat_dex_id)

                                        span_tag = a_tag.find_next('span')
                                        name = span_tag.text
                                        print(name)
                                        pokemon["pokemon"]["name"] = name
                                        pokemon["pokemon"]["rvId"] = 1

                                    # If in Scarlet
                                    elif j == 1:
                                        if 'background:#F34134' in cell.get('style'):
                                            print("In Scarlet")
                                            pokemon["location"]["game_version"].append(37)

                                    # If in Violet
                                    elif j == 2:
                                        if 'background:#8334B7' in cell.get('style'):
                                            print("In Violet")
                                            pokemon["location"]["game_version"].append(38)

                                    elif j == 3:
                                        if '✔' in cell.text:
                                            print('In land')
                                            pokemon["encounter_method"]["requisite"] += "Land"
                                    elif j == 4:
                                        if '✔' in cell.text:
                                            print('In water surface')
                                            pokemon["encounter_method"]["requisite"] += ", Water Surface"
                                    elif j == 5:
                                        if '✔' in cell.text:
                                            print('In underwater')
                                            pokemon["encounter_method"]["requisite"] += ", Underwater"
                                    elif j == 6:
                                        if '✔' in cell.text:
                                            print('In overland')
                                            pokemon["encounter_method"]["requisite"] += ", Overland"
                                    elif j == 7:
                                        if '✔' in cell.text:
                                            print('In sky')
                                            pokemon["encounter_method"]["requisite"] += ", Sky"

                                    # Check time of day and chance (prob weight)
                                    elif j == 9:
                                        if 'background:#FFF' in cell.get('style'):
                                            print(cell.text +  " anytime!")
                                            pokemon["encounter_method"]["time_of_day"] = "Anytime"
                                        else:
                                            print(cells[j].text + " in the morning")
                                            print(cells[j + 1].text + " in the day")
                                            print(cells[j + 2].text + " in the evening")
                                            print(cells[j + 3].text + " in the night")

                                print(pokemon)



                                
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


