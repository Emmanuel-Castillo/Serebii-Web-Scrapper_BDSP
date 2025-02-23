import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://www.serebii.net/pokearth/sinnoh/route201.shtml"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

pokemon_list = []

# Encounter data is inside tables classified by either:
#   "extradextable"
#   "dextable"

# Grabbing all tables
tables = soup.find_all("table", attrs={"class": "extradextable"})

encounters = []
for table in tables:
    rows = table.find_all("tr")

    encounter_method = ""
    game_version = ""
    pokemon_row_list = []
    for index, row in enumerate(rows):

        # Grabbing encounter method
        if index == 0:
            cells = row.find("td")
            a = cells.find("a")
            h3 = a.find("h3")
            # print("Encounter method: ", h3.text)
            encounter_method = h3.text

        # Grabbing game version
        elif index == 1:
            cells = row.find("td")
            # print("Game version: ", cells.text)
            game_version = cells.text

        # Grabbing name
        # Start assigning size of pokemon list per row
        # As well as initialzing pokemon data appropriately
        elif index == 3:
            cells = row.find_all("td")

            # Initializing a list of empty dictionaries
            pokemon_row_list = [{} for _ in range(len(cells))]
            
            for i, cell in enumerate(cells):
                pokemon_row_list[i]["name"] = cell.text
                pokemon_row_list[i]["encounter_method"] = encounter_method
                pokemon_row_list[i]["game_version"] = game_version
                # print("Pokemon: ", cell.text)

        # Grabbing type
        elif index == 4:
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
        elif index == 5:
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                pokemon_row_list[i]["chance"] = cell.text
                # print("Chance: ", cell.text)

        # Grabbing level
        elif index == 7:
            cells = row.find_all("td")
            for i, cell in enumerate(cells):
                pokemon_row_list[i]["level"] = cell.text
                # print("Levels: ", cell.text)

        # Print current pokemon_row_list
        # print(pokemon_row_list)

    # Add new pokemon_row_list to pokemon_list
    pokemon_list.extend(pokemon_row_list)

print(pokemon_list)

        
        




