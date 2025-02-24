import requests
from bs4 import BeautifulSoup
import json
import re

starting_url = "https://www.serebii.net"
response = requests.get(starting_url + "/pokearth/sinnoh/")
soup = BeautifulSoup(response.text, 'html.parser')

sinnoh_form = soup.find("form", attrs={"name": "sinnoh"})
options = sinnoh_form.find_all("option")
location_names = []
locations_endpoint = []
locations_dict = {}
for option in options[1:]:
    location_name = option.text
    location_names.append(location_name)
    locations_endpoint.append(option.get("value"))
    locations_dict[location_name] = {}
    
print(location_names)

def checkIfPokemonInBothVersions(p0, pokemon_list):
    
    for p1 in pokemon_list:
        
        if p0["name"] == p1["name"] and p0["encounter_method"] == p1["encounter_method"] and p0["time_of_day"] == p1["time_of_day"] and p0["chance"] == p0["chance"]:
            p1["game_version"] = "Both"
            return True
    return False
    


for endpoint_index, endpoint in enumerate(locations_endpoint):
    
    # Skipping Grand Underground cuz fuckkk me
    # Skipping Solaceon Runs cuz fuccckkk me again
    if endpoint == "/pokearth/sinnoh/grandunderground.shtml" or endpoint == "/pokearth/sinnoh/solaceonruins.shtml" or endpoint == "/pokearth/sinnoh/trophygarden.shtml":
        print("Skipping ", endpoint)
        continue
    
    print(endpoint)
    
    response = requests.get("https://www.serebii.net" + endpoint)
    soup = BeautifulSoup(response.text, 'html.parser')


    # Encounter data is inside tables classified by either:
    #   "extradextable"
    #   "dextable"

    # Grabbing all tables
    tables = soup.find_all("table", class_=re.compile(r"\b(?:extra)?dextable\b"))
    # print(tables)

    pokemon_location_list = []
    encounters = []
    encounter_method = ""
    time_of_day = ""
    
    # Offset needed b/c of Iron Island gift pokemon
    offset = 0
    
    for table_index, table in enumerate(tables):
        
        calc_table_index = table_index + offset
        starting_row_index = 0
        

        # extradextable has addtional row indicating encounter method
        # UPDATE: If 'Gift Pokemon', offset = 1 to properly send future tables to correct condition cases
        # encounter method may include time of day
        # every other table starting at index 0 is an extradextable
        if calc_table_index % 2 == 0:
            extra_row = table.find_all("tr")[0]
            h = extra_row.find(re.compile("^h"))
            print(h)
            encounter_method = h.text
            
            if encounter_method == "Gift Pokémon":
                offset += 1

            # check if includes time of day by splitting
            split_words = encounter_method.split(' - ')
            if len(split_words) > 1:
                encounter_method = split_words[0]
                time_of_day = split_words[1]
            else:
                time_of_day = "Anytime"

            # print("Encounter method: ", encounter_method)
            # print("Time of day: " + time_of_day)

            starting_row_index = 1
        
        rows = table.find_all("tr")

        game_version = ""
        pokemon_row_list = []
        for index, row in enumerate(rows[starting_row_index + offset:]):

            # Grabbing game version
            if index == 0:
                cells = row.find("td")
                # print("Game version: ", cells.text)
                game_version = cells.text

            # Grabbing name
            # Start assigning size of pokemon list per row
            # As well as initialzing pokemon data appropriately
            elif index == 2:
                cells = row.find_all("td")

                # Initializing a list of empty dictionaries
                pokemon_row_list = [{} for _ in range(len(cells))]
                
                for i, cell in enumerate(cells):
                    pokemon_row_list[i]["name"] = cell.text
                    pokemon_row_list[i]["encounter_method"] = encounter_method
                    pokemon_row_list[i]["game_version"] = game_version
                    pokemon_row_list[i]["time_of_day"] = time_of_day
                    pokemon_row_list[i]["location"] = location_names[endpoint_index]
                    # print("Pokemon: ", cell.text)

            # Grabbing type
            elif index == 3:
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

            # Grabbing chance
            elif index == 4:
                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    pokemon_row_list[i]["chance"] = cell.text
                    # print("Chance: ", cell.text)

            # Grabbing level
            elif index == 6:
                cells = row.find_all("td")
                for i, cell in enumerate(cells):
                    pokemon_row_list[i]["level"] = cell.text
                    # print("Levels: ", cell.text)

            # Print current pokemon_row_list
            # print(pokemon_row_list)

        # Add new pokemon_row_list to pokemon_list
        for pokemon in pokemon_row_list:
            # Check if pokemon already in locations_dict[location], and has the same data (except game version)
            # If so, do not append pokemon and modify pokemon in locations_dict[location].game_version = "Both"
            if not checkIfPokemonInBothVersions(pokemon, pokemon_location_list):
                pokemon_location_list.append(pokemon)
        
    # Add pokemon_list to locations_dict
    locations_dict[location_names[endpoint_index]] = pokemon_location_list

# print(pokemon_list)
# Save pokemon_list as JSON file
with open("encounters.json", "w") as f:
    json.dump(locations_dict, f, indent=4)

        
        




