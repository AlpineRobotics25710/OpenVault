import uuid
import json

import requests
from bs4 import BeautifulSoup
from flask import jsonify, session
from requests import JSONDecodeError


def build_index(records):
    index = {}

    for record in records:
        fields = [
            record.get("title", "").lower(),
            record.get("author", "").lower(),
            record.get("description", "").lower(),
            record.get("team_number", "").lower(),
            record.get("years_used", "").lower(),
            record.get("language", "").lower() if "language" in record else "",
            record.get("awards_won", "").lower() if "awards_won" in record else "",
        ]

        # Add each word in the fields to the index
        for field in fields:
            for word in field.split():
                if word not in index:
                    index[word] = []
                index[word].append(record)

    return index


def fetch_data_from_github(section, sub_section):
    base_url = "https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc"
    github_page = requests.get(f"https://github.com/AlpineRobotics25710/OpenVaultFiles/tree/main/ftc/{section}/{sub_section}")
    
    records = []
    if github_page.status_code == 200:
        soup = BeautifulSoup(github_page.text, "html.parser")
        script_tag = soup.find("script", {"type": "application/json", "data-target": "react-app.embeddedData"})
        
        if script_tag:
            try:
                # Parse the JSON content from the script tag
                embedded_data = json.loads(script_tag.string)
                entries = embedded_data.get("payload", {}).get("tree", {}).get("items", [])
                
                for entry in entries:
                    # Skip entries with "filler" in their name
                    if "filler" not in entry.get("name", ""):
                        post_info = requests.get(f"{base_url}/{section}/{sub_section}/{entry['name']}/info.json")
                        
                        if post_info.status_code == 200:
                            try:
                                post_info_json = post_info.json()
                            except JSONDecodeError:
                                continue

                            # Build the record based on the section type
                            record = {
                                "uuid": str(uuid.uuid4()),
                                "preview_image_url": f"{base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['preview-image-name']}",
                                "title": post_info_json["title"],
                                "author": post_info_json["author"],
                                "description": post_info_json["description"],
                                "team_number": post_info_json["team-number"],
                                "years_used": post_info_json["years-used"],
                            }

                            if section == "code":
                                record["download_url"] = f"{base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['download-name']}"
                                record["language"] = post_info_json["language"]
                                record["used_in_comp"] = post_info_json["used-in-comp"]

                            elif section == "portfolios":
                                record["download_url"] = f"{base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['file-name']}"
                                record["awards_won"] = post_info_json["awards-won"]

                            elif section == "cad":
                                record["used_in_comp"] = post_info_json["used-in-comp"]
                                record["onshape_link"] = post_info_json["onshape-link"]
                            
                            records.append(record)

                # Build the index for efficient search
                session["index"] = build_index(records)

            except (JSONDecodeError, KeyError):
                return { "error": "Failed to parse embedded JSON data." }
    
    return records
