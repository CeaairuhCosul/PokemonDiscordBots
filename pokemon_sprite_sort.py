import csv
import os
import shutil

name = []
classification = []

with open("..//Shiny_Pokemon_Sprites/Pokemon_Info.csv",'r') as f:
    pokemon_info = csv.reader(f)
    for row in pokemon_info:
        name_pokemon = row[2].replace("\"","")
        class_pokemon = row[6]

        if (class_pokemon == "NULL"):
            continue
        else:
            name.append(name_pokemon.lower())
            classification.append(class_pokemon)


# for i in range(len(name)):
#     print(f"Name: {name[i]}, Class: {classification[i]}")

name.append('mega')

source_path = "..\Shiny_Pokemon_Sprites\AllSprites"
destination = "..\Shiny_Pokemon_Sprites\OnlyLegendaries"
image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')

for file_name in os.listdir(source_path):
    file_name_compare = file_name.replace("-", " ")
    source_folder = os.path.join(source_path, file_name)
    if any(keyword in file_name_compare.lower() for keyword in name):
        shutil.copy(source_folder, destination)