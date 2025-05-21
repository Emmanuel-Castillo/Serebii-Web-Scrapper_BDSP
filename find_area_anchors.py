import re
import requests
from bs4 import BeautifulSoup
import json

game = {}

selected_choice = input("1. LGPE\n2. BDSP\n3. SWSH\n4. LGA\nEnter either number to proceed, or any other key to exit program: ")
anchor_table_index = 1
match int(selected_choice):
    case 1:
        game["endpoint"] = "/pokearth/kanto/"
        game["formName"] = "kanto"
        game["anchorFile"] = "lgpe_area_anchors1.json"
    case 2:
        game["endpoint"] = "/pokearth/sinnoh/"
        game["formName"] = "sinnoh"
        game["anchorFile"] = "bdsp_area_anchors.json"
    case 3:
        game["endpoint"] = "/pokearth/galar/"
        game["formName"] = "kalos"
        game["anchorFile"] = "swsh_area_anchors.json"
        anchor_table_index = 0
    case 4:
        game["endpoint"] = "/pokearth/hisui/"
        game["formName"] = "kalos"
        game["anchorFile"] = "lga_area_anchors.json"
    case _:
        exit()

# Fetching pokemon from each endpoint
starting_url = "https://www.serebii.net"
response = requests.get(starting_url + game["endpoint"])
soup = BeautifulSoup(response.text, 'html.parser')

region_form = soup.find("form", attrs={"name": game["formName"]})
options = region_form.find_all("option")
locations_endpoint_dict = {}
area_anctabs = {}

for option in options[1:]:
    location_name = option.text
    locations_endpoint_dict[location_name] = option.get("value")

for key, value in locations_endpoint_dict.items():

    print(value)

    area_anchors = {}
    # if key in area_anctabs.keys():
    #     area_anchors = area_anctabs[key]
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
    # All endpoints contain at least 1 anctab (to select game generation). Area anc_tab will be the next anctab after
    anctab_tables = soup.find_all("table", class_="anctab")
    if len(anctab_tables) > 1:

        # Special case
        if key == "Grand Underground":
            anchor_table_index = 0
        area_anctabs_table = anctab_tables[anchor_table_index]
        found_imgs = area_anctabs_table.find_all("img")
        if len(found_imgs) > 0:
            # print(value, "has area anchors")
            area_anctabs[key] = {}
            area_anchors = {}
            area_anctabs_a_tags = area_anctabs_table.find_all("a")
            for a in area_anctabs_a_tags:
                if len(a.text) > 0:
                    area_anchors[a.text] = 0
            area_anctabs[key]["anchors"] = area_anchors

            # print(area_anctabs)

            # Find first h2 elements
            head_tag = soup.find("head")
            # print(h2_tag)

            count_tables = 0
            curr_anchor = None
            # Traverse through all HTML tags in the page
            # Tracking number of extradextable/dextable tables while also tracking h2 that matches with area anchor names
            curr = head_tag.find_next()
            while curr:
                # Check if reached a h2 or h3 that carries name of an area anchor
                if (curr.name == "h2" or curr.name == "h3") and curr.text in area_anctabs[key]["anchors"].keys():
                    if curr_anchor:
                        # If currently on an anchor tracking tables, set the count as the value of anchor key
                        area_anctabs[key]["anchors"][curr_anchor] = count_tables
                        # Then reset the count
                        count_tables = 0
                    # Set the curr_anchor with next anchor
                    curr_anchor = curr.text

                # Check if it's a table with class "dextable" or "extradextable"
                if curr.name == "table" and curr.get("class"):
                    if any(re.match(r"\b(?:extra)?dextable\b", cls) for cls in curr["class"]):
                        count_tables += 1


                curr = curr.find_next()

            # Set count of tables in final anchor
            area_anctabs[key]["anchors"][curr_anchor] = count_tables
            # print("Number of target tables:", count_tables)

with open(game["anchorFile"], "w") as f:
    json.dump(area_anctabs, f, indent=4)