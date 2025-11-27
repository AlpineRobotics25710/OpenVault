import uuid
from datetime import datetime
from json.decoder import JSONDecodeError

import requests
from requests import JSONDecodeError


# FTC Season name mapping
SEASON_NAMES = {
    "2025-2026": "DECODE",
    "2024-2025": "INTO THE DEEP",
    "2023-2024": "CENTERSTAGE",
    "2022-2023": "POWERPLAY",
    "2021-2022": "FREIGHT FRENZY",
    "2020-2021": "ULTIMATE GOAL",
    "2019-2020": "SKYSTONE",
    "2018-2019": "ROVER RUCKUS",
    "2017-2018": "RELIC RECOVERY",
    "2016-2017": "VELOCITY VORTEX",
    "2015-2016": "RES-Q",
}


def format_season_with_name(season_year):
    """Format a season year with its name, e.g., '2024-2025 (INTO THE DEEP)'"""
    if not season_year or not isinstance(season_year, str):
        return season_year

    season_year = season_year.strip()
    season_name = SEASON_NAMES.get(season_year)

    if season_name:
        return f"{season_year} ({season_name})"
    return season_year


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

                    # Support both new seasons-used and old years-used for backwards compatibility
                    seasons_raw = post_info_json.get(
                        "seasons-used", post_info_json.get("years-used", [])
                    )
                    # Ensure it's a list
                    if isinstance(seasons_raw, str):
                        seasons_raw = [seasons_raw]

                    # Get tags (default to empty array if not present)
                    tags = post_info_json.get("tags", [])
                    if isinstance(tags, str):
                        tags = [tags]

                    record = {
                        "uuid": str(uuid.uuid4()),
                        "preview_image_url": f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json['preview-image-name']}",
                        "title": post_info_json["title"],
                        "author": post_info_json["author"],
                        "description": post_info_json["description"],
                        "team_number": post_info_json["team-number"],
                        "seasons_used": seasons_raw,
                        "seasons_display": [
                            format_season_with_name(s) for s in seasons_raw
                        ],
                        "tags": tags,
                    }

                    if "timestamp" in post_info_json:
                        record["timestamp"] = (
                            datetime.fromisoformat(post_info_json["timestamp"])
                            .date()
                            .strftime("%m/%d/%Y")
                        )

                    if section == "code":
                        # Check if it's a GitHub link or download
                        if post_info_json.get("github-link"):
                            record["github_link"] = post_info_json["github-link"]
                            record["download_url"] = ""  # No download for GitHub links
                        else:
                            record["download_url"] = (
                                f"{raw_base_url}/{section}/{sub_section}/{entry['name']}/{post_info_json.get('download-name', '')}"
                            )
                            record["github_link"] = ""
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

    # Sort records by timestamp - earliest first, records without timestamp at the end
    def sort_key(record):
        ts = record.get("timestamp", "")
        if not ts:
            # Records without timestamp go to the end (use max date)
            return datetime.max
        try:
            # Parse the formatted date string back to datetime for sorting
            return datetime.strptime(ts, "%m/%d/%Y")
        except Exception:
            # Invalid timestamps also go to the end
            return datetime.max

    records.sort(key=sort_key)

    return records
