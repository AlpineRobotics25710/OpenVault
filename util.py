import uuid
from json.decoder import JSONDecodeError

import numpy as np
import requests
from requests import JSONDecodeError
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_index(records, n_components=100):
    #Collect all unique keys from all records
    all_keys = set()
    for record in records:
        all_keys.update(record.keys())

    def stringify(r):
        # For each key, get its string value or empty string if missing
        return ", ".join(str(r.get(k, "")) for k in sorted(all_keys))

    texts = [stringify(r) for r in records]
    #print("n_components: ", n_components)

    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(texts)
    #print("tfidf_matrix: ", tfidf_matrix)
    #print(n_components, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1)

    max_components = max(1, min(n_components, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1))
    #print("max_components: ", max_components)
    svd_model = TruncatedSVD(n_components=max_components)
    reduced_vectors = svd_model.fit_transform(tfidf_matrix)

    norms = np.linalg.norm(reduced_vectors, axis=1, keepdims=True)
    reduced_vectors = reduced_vectors / norms

    return tfidf_vectorizer, svd_model, reduced_vectors


def search(query: str, tfidf_vectorizer, svd_model, reduced_vectors):
    if not tfidf_vectorizer or not svd_model or reduced_vectors is None:
        return [], []

    # Convert query to same vector space
    query_tfidf = tfidf_vectorizer.transform([query])
    if not query_tfidf.nnz:  # No non-zero entries
        return [], []
    query_vector = svd_model.transform(query_tfidf)
    query_vector = query_vector / np.linalg.norm(query_vector)

    # Compute cosine similarity
    similarities = cosine_similarity(query_vector, reduced_vectors)[0]

    # Sort results by similarity
    ranked_indices = np.argsort(similarities)[::-1]
    return similarities, ranked_indices


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
