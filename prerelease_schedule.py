# prerelease discord bot 

import requests
from bs4 import BeautifulSoup
import datetime
import time
import os
import json

# Webhook

webhook_url = os.getenv('my_webhook')

# Grab previous image source

prev_event_src = 'butts'
filename_json="prev_events.json"
if filename_json:
    with open(filename_json, "r") as f:
        json_info = json.load(f)
        prev_event_src = str(json_info[0]['image'][0]['src'])

def scrape_mg():

    mg_url = "http://www.mythicgamescolorado.com/calendar/"
    data = []
    header = {
        "User-Agent": "PokemonPrereleaseDateBot(+https://github.com/CeaairuhCosul)"
    }

    try:
        response = requests.get(mg_url,headers=header,timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content,"html.parser")

        prerelease_data = {}

        raw_event_text = []
        event_image = []

        for article in soup.find_all("article"):
            entry = article.find("div", class_="entry-content")
            if not entry:
                continue

            for p in soup.find_all("p"):
                text = p.get_text(strip = True)

                if text: 
                    if any(keyword in text.lower() for keyword in ["pokemon","pokémon"]):
                        if "prerelease" in text.lower():
                            current_time = datetime.datetime.now()
                            raw_event_text.append({
                                "title": "Pokemon Prerelease Event",
                                "text": text,
                                "time_pulled": current_time.strftime("%B %d, %Y at %H:%M")
                            })
                
                            figure_container = p.find_previous_sibling("figure")
                            if figure_container:
                                image_container = figure_container.find("img")
                                image_source = image_container.get("src")
                                event_image.append({
                                    "src": image_source
                                })

                            else:
                                print(f"No figure found")

        prerelease_data["raw_text"] = raw_event_text
        prerelease_data['image'] = event_image
        data.append(prerelease_data)
        time.sleep(2)

    except Exception as e:
        print(f"Error 1: {e}")
        
    return [data,image_source]

# Save Data 

def save_scraped_data(data,filename_json="prev_events.json"):
    if not data:
        print(f"No event")
        return
    try:
        with open(filename_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True)
        print(f"Event Saved")
    except Exception as e:
        print(f"Error 2: {e}")


def discord_message(content):
    try:
        data = {"content":content}
        if prev_event_src != content:
            post_response = requests.post(webhook_url,json=data)
        else:
            print("No new event")
    except Exception as e:
        print(f"Discord message not sending. Error: {e}")



def main() -> None:
    [data,to_post] = scrape_mg()
    discord_message(to_post)

    if data:
        print(f"Processing")
        save_scraped_data(data)
    else:
        print(f"No Data :(")

main()
