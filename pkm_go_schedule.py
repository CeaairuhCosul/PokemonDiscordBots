# Pokemon go raid bot

import requests
from bs4 import BeautifulSoup
from datetime import datetime,timezone
from dateutil import parser
import json
import os
import uuid
import urllib.parse


# Get previous data

the_file_path = "pokemon_go_events.json"
with open(the_file_path,"r") as f:
    info = json.load(f)
    prev_raids = info["current_raids"]["current_raids"]
    cur_event = info["general_events"]["current_events"]
    fut_event = info["general_events"]["future_events"]
    prev_current_events = []
    prev_future_events = []
    for item in cur_event:
        prev_current_events.append(item["name"])
    for item in fut_event:
        prev_future_events.append(item["name"])
    
# Webhook

webhook_url = os.getenv('my_webhook')

# Shiny sprites

sprites_dict = {}

source_path = "OnlyLegendaries"
image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')

def grab_sprite(pokemon):
    for file_name in os.listdir(source_path):
        file_name_compare = file_name.replace("-", " ")
        pokemon = pokemon.lower()
        pokemon = pokemon.replace("mega ","")
        if (pokemon in file_name_compare.lower()):
            path = os.path.join(source_path,file_name)
            return path
            

def scrape_website():
    urls = ['https://leekduck.com/boss/','https://leekduck.com/events/']
    main_header = {
        "User-Agent": "PokemonRaidsShinyHuntingBotDebugging (+https://github.com/CeaairuhCosul)"
    }
    current_date = datetime.now(timezone.utc)
    data = {}

    try:
        raid_data = {}

        # Grabbing current pokemon go raids
        response = requests.get(urls[0],headers=main_header,timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content,"html.parser")

        current_raids = {}
        general_events = {}

        for article in soup.find_all("article"):
            h_1 = article.find("h1", class_="page-title")
            header = h_1.get_text(strip=True)
            p = article.find("p")
            page_info = p.get_text(strip=True)
            if not header or not page_info:
                continue

            current_raids["title"] = header
            current_raids["general_info"] = page_info
            pokemon = []
            for h_2 in article.find_all("h2"):
                tier = h_2.get_text(strip=True)
                if tier == "Tier 5" or tier == "Mega":
                    active_raids = h_2.find_next_sibling()
                    for p in active_raids.find_all("p"):
                        card = p.get_text(strip=True)
                        pokemon.append(card)
            current_raids["current_raids"] = pokemon

        response = requests.get(urls[1],headers=main_header,timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        for article in soup.find_all("article"):
            events = article.find("div", class_="page-content")
            current_events = events.find("div", class_="events-list current-events")
            # future_events = events.find("div", class_="events-list upcoming-events")
            c_events = []
            f_events = []
            for span in current_events.find_all("span", class_="event-header-item-wrapper"):
                event_item = span.find("a", class_="event-item-link")

                event_time = span.find("h5")
                start_date_sort = event_time.get("data-event-start-date-check")
                start_dt = parser.isoparse(start_date_sort)

                p = event_item.find("p")
                event_type = p.get_text(strip=True)

                if any(keyword in event_type.lower() for keyword in ["raid","community"]):
                    event_text = event_item.find("div", class_="event-text")

                    h_2 = event_text.find("h2")
                    event_name = h_2.get_text(strip=True)

                    p = event_text.find("p")
                    event_date = p.get_text(strip=True)

                    if start_dt <= current_date:
                        c_events.append({
                            "type": event_type,
                            "name": event_name,
                            "end_date": event_date
                        })
                    else:
                        f_events.append({
                            "type": event_type,
                            "name": event_name,
                            "start_date": event_date                            
                        })

            general_events["current_events"] = c_events
            general_events["future_events"] = f_events
        
        raid_data["current_raids"] = current_raids
        raid_data["general_events"] = general_events

    except Exception as e:
        print(f"Uh Oh! Error: {e}")

    return raid_data

# Save Data 

def save_scraped_data(data,filename_json="pokemon_go_events.json"):
    if not data:
        print(f"No event")
        return
    try:
        with open(filename_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True)
        print(f"Events Saved")
    except Exception as e:
        print(f"Error 2: {e}")

def send_message(filename):
    #Parse out specific information I want to sent in a format I like
    json_send = {}
    json_send = {
        "content": "Pokemon Go Raid Updates"
    }

    embeds = []
    image_file_name = []

    # Quick Current Raids
    current_pokemon_raids = filename["current_raids"]["current_raids"] 
    if any(poke not in prev_raids for poke in current_pokemon_raids):
        for pokemon in current_pokemon_raids:
            current_image_file_name = str(uuid.uuid4()) + ".png"
            image_file_name.append(current_image_file_name)
            print(current_image_file_name)
            embeds.append({
                "title": pokemon,
                "author": {"name": "Current Active Raids"},
                "thumbnail": {"url": f"attachment://{current_image_file_name}"}
        })


    #Current Events
    current_events = {
        "title": "Current Events",
        "description": "List of active events (raids and community days)"
    }
    c_events = filename["general_events"]["current_events"]
    c_fields = []
    for item in c_events:
        if item["name"] not in prev_current_events:
            c_fields.append({
                "name": item["name"],
                "value": f"End Date: {item["end_date"]}"
            })
    if c_fields:
        current_events["fields"] = c_fields
        embeds.append(current_events)

    #Future Events
    future_events = {
        "title": "Future Events",
        "description": "List of future events (raids and community days)"
    }
    f_events = filename["general_events"]["future_events"]
    f_fields = []
    for item in f_events:
        if item["name"] not in prev_future_events:
            f_fields.append({
                "name": item["name"],
                "value": f"Start Date: {item["start_date"]}"
            })
    if f_fields:
        future_events["fields"] = f_fields
        embeds.append(future_events)
    if embeds:
        json_send["embeds"] = embeds
        try:
            photo_files = {}
            count = 0
            if image_file_name:
                for pokemon in current_pokemon_raids:
                    print(pokemon)
                    file_path = grab_sprite(pokemon)
                    print(file_path)
                    print(image_file_name)
                    photo_files[f"files[{count}]"] = (image_file_name[count],open(file_path, "rb"))
                    count += 1

            post_response = requests.post(
                webhook_url,
                files=photo_files,
                data={'payload_json': json.dumps(json_send)})

            # print(post_response.status_code, post_response.text) 

        except Exception as e:
            print(f"Uh Oh! Spaghettio. Error: {e}")



def main() -> None:
    data = scrape_website()
    if data:
        send_message(data)
        print("Message Sent")

    if data:
        print(f"Processing")
        save_scraped_data(data)
    else:
        print(f"No Data :(")

main()

