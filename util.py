import uuid
import json

import requests
from bs4 import BeautifulSoup
from flask import session
from requests import JSONDecodeError
import numpy as np
import faiss

vocab = {}
search_index = None
record_embeddings = None 

def build_index(records):
    global vocab, search_index, record_embeddings

    texts = []
    for record in records:
        fields = [
            record.get("title", ""),
            record.get("author", ""),
            record.get("description", ""),
            record.get("team_number", ""),
            record.get("years_used", ""),
            record.get("language", "") if "language" in record else "",
            record.get("awards_won", "") if "awards_won" in record else "",
        ]
        texts.append(" ".join(fields).lower())

    vocab = {}
    for text in texts:
        for word in text.split():
            if word not in vocab:
                vocab[word] = len(vocab)
    dim = len(vocab)

    embeddings = np.zeros((len(texts), dim), dtype='float32')
    for i, text in enumerate(texts):
        for word in text.split():
            if word in vocab:
                embeddings[i, vocab[word]] += 1.0
    record_embeddings = embeddings  # Save for later use

    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    assert index.is_trained, "Index is not trained. Check the embeddings."
    search_index = index
    return {"index": search_index, "records": records, "vocab": vocab}

def embed_text(text):
    """Embed a query string into the same vector space as the index."""
    global vocab
    dim = len(vocab)
    vec = np.zeros((dim,), dtype='float32')
    for word in text.lower().split():
        if word in vocab:
            vec[vocab[word]] += 1.0
    return vec


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
                build_index(records)

            except (JSONDecodeError, KeyError):
                return { "error": "Failed to parse embedded JSON data." }
    
    return records
