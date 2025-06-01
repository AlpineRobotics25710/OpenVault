import uuid
from datetime import datetime
from json.decoder import JSONDecodeError

import requests
from requests import JSONDecodeError


def fetch_data_from_github(section, sub_section):
    api_url = f"https://api.github.com/repos/AlpineRobotics25710/OpenVaultFiles/contents/ftc/{section}/{sub_section}"
    raw_base_url = (
        "https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/main/ftc"
    )

    records = []
    response = requests.get(api_url)

    if response.status_code == 200:
        try:
            entries = response.json()
        except JSONDecodeError:
            return {"error": "Failed to decode GitHub API response."}

        for entry in entries:
            if entry["type"] == "dir" and "filler" not in entry["name"]:
                info_url = (
                    f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/info.json"
                )
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

                    if "timestamp" in post_info_json:
                        record["timestamp"] = datetime.fromisoformat(post_info_json["timestamp"]).date().strftime(
                            "%m/%d/%Y")

                    if section == "code":
                        record["download_url"] = (
                            f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['download-name']}"
                        )
                        record["language"] = post_info_json["language"]
                        record["used_in_comp"] = post_info_json["used-in-comp"]

                    elif section == "portfolios":
                        record["download_url"] = (
                            f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['file-name']}"
                        )
                        record["awards_won"] = post_info_json["awards-won"]

                    elif section == "cad":
                        record["used_in_comp"] = post_info_json["used-in-comp"]
                        record["onshape_link"] = post_info_json["onshape-link"]

                    records.append(record)
    else:
        return {"error": f"GitHub API returned status {response.status_code}"}

    # Sort records by timestamp if available
    if records and "timestamp" in records[0]:
        def parse_timestamp(record):
            ts = record.get("timestamp", "")
            try:
                return datetime.fromisoformat(ts)
            except Exception:
                return datetime.min

        records.sort(key=parse_timestamp, reverse=True)

    return records
