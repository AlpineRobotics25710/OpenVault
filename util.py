import pickle
import uuid
from json.decoder import JSONDecodeError

import faiss
import numpy as np
import requests
from requests import JSONDecodeError

vocab = {}
search_index = None
record_embeddings = None


def build_index(records, index_file="search_index.faiss", meta_file="index_meta.pkl"):
    global vocab, search_index, record_embeddings

    texts = []
    for record in records:
        fields = [
            record.get("title", ""),
            record.get("author", ""),
            record.get("description", ""),
            record.get("team_number", ""),
            record.get("years_used", ""),
            record.get("language", ""),
            record.get("awards_won", ""),
        ]
        texts.append(" ".join(fields).lower())

    # Build vocab
    vocab = {}
    for text in texts:
        for word in text.split():
            if word not in vocab:
                vocab[word] = len(vocab)
    dim = len(vocab)

    # Generate bag-of-words embeddings
    embeddings = np.zeros((len(texts), dim), dtype='float32')
    for i, text in enumerate(texts):
        for word in text.split():
            if word in vocab:
                embeddings[i, vocab[word]] += 1.0

    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    embeddings = embeddings / norms
    record_embeddings = embeddings

    # Build and save FAISS index
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, index_file)

    # Save vocab and embeddings metadata
    with open(meta_file, "wb") as f:
        pickle.dump({
            "vocab": vocab,
            "record_embeddings": record_embeddings,
            "records": records
        }, f)

    # Assign globals
    search_index = index
    return {"index": search_index, "records": records, "vocab": vocab}


def embed_text(text, vocab):
    vector = np.zeros(len(vocab), dtype='float32')
    for word in text.lower().split():
        if word in vocab:
            vector[vocab[word]] += 1.0
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector /= norm
    return vector


def load_index(index_file="search_index.faiss", meta_file="index_meta.pkl"):
    search_index = faiss.read_index(index_file)

    with open(meta_file, "rb") as f:
        data = pickle.load(f)

    return {
        "search_index": search_index,
        "record_embeddings": data["record_embeddings"],
        "vocab": data["vocab"]
    }


def fetch_data_from_github(section, sub_section):
    api_url = f"https://api.github.com/repos/AlpineRobotics25710/OpenVaultFiles/contents/ftc/{section}/{sub_section}"
    raw_base_url = "https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/main/ftc"

    records = []
    response = requests.get(api_url)

    if response.status_code == 200:
        try:
            entries = response.json()
        except JSONDecodeError:
            return {"error": "Failed to decode GitHub API response."}

        for entry in entries:
            if entry["type"] == "dir" and "filler" not in entry["name"]:
                info_url = f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/info.json"
                post_info_resp = requests.get(info_url)

                if post_info_resp.status_code == 200:
                    try:
                        post_info_json = post_info_resp.json()
                    except JSONDecodeError:
                        continue

                    record = {
                        "uuid": str(uuid.uuid4()),
                        "preview_image_url": f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['preview-image-name']}",
                        "title": post_info_json["title"],
                        "author": post_info_json["author"],
                        "description": post_info_json["description"],
                        "team_number": post_info_json["team-number"],
                        "years_used": post_info_json["years-used"],
                    }

                    if section == "code":
                        record[
                            "download_url"] = f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['download-name']}"
                        record["language"] = post_info_json["language"]
                        record["used_in_comp"] = post_info_json["used-in-comp"]

                    elif section == "portfolios":
                        record[
                            "download_url"] = f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['file-name']}"
                        record["awards_won"] = post_info_json["awards-won"]

                    elif section == "cad":
                        record["used_in_comp"] = post_info_json["used-in-comp"]
                        record["onshape_link"] = post_info_json["onshape-link"]

                    records.append(record)
    else:
        return {"error": f"GitHub API returned status {response.status_code}"}

    return records
