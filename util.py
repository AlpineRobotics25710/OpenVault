import os
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from urllib.parse import urlparse

import requests

CONTENT_REPO = "AlpineRobotics25710/OpenVaultFiles"
TREE_URL = f"https://api.github.com/repos/{CONTENT_REPO}/git/trees/main?recursive=1"
RAW_BASE = f"https://raw.githubusercontent.com/{CONTENT_REPO}/main/ftc"
TIMEOUT = 10  # seconds per GitHub request
CACHE_TTL = 300  # seconds a category listing is reused before refetching

# Single source of truth for site sections and their categories.
# Each (section, category) maps to ftc/<section>/<category>/ in OpenVaultFiles.
SECTIONS = {"cad": "CAD", "code": "Code", "portfolios": "Portfolios"}
CATEGORIES = {
    "cad": {
        "active-intakes": "Active Intakes",
        "arms": "Arms",
        "claws": "Claws",
        "dead-axles": "Dead Axles",
        "drivetrains": "Drivetrains",
        "linkages": "Linkages",
        "outtakes": "Outtakes",
        "power-transmissions": "Power Transmissions",
        "robots": "Robots",
    },
    "code": {
        "autonomous": "Autonomous",
        "full-repo": "Full Repositories",
        "mechanism-control": "Mechanism Control",
        "teleop": "TeleOp",
        "vision": "Vision",
    },
    "portfolios": {"portfolios": "Portfolios"},
}

# FTC season names, most recent first. Add each new season at the top.
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

# ponytail: per-process caches; each serverless instance keeps its own copy.
# Move to a shared cache (e.g. Redis/KV) if GitHub rate limits still bite.
_cache = {}  # (section, category) -> (fetched_at, records)
_folders = None  # (fetched_at, {(section, category): [folders]})


def github_headers():
    token = os.getenv("GITHUB_TOKEN")
    return {"Authorization": f"token {token}"} if token else {}


def format_season_with_name(season_year):
    """'2024-2025' -> '2024-2025 (INTO THE DEEP)'"""
    season_year = str(season_year).strip()
    name = SEASON_NAMES.get(season_year)
    return f"{season_year} ({name})" if name else season_year


def normalize_season(value):
    """'2024-25' / '2024 - 2025' -> '2024-2025'; None for anything that isn't a known season."""
    m = re.fullmatch(r"(\d{4})\s*[-–]\s*(\d{2}|\d{4})", str(value).strip())
    if not m:
        return None
    start = int(m.group(1))
    if int(m.group(2)) % 100 != (start + 1) % 100:
        return None
    season = f"{start}-{start + 1}"
    return season if season in SEASON_NAMES else None


def season_filters(records):
    """[(season, name, post count)] newest first, for seasons that have posts.
    Empty when filtering would not narrow anything (no seasons, or every post shares one)."""
    if not isinstance(records, list):
        return []
    counts = Counter(s for r in records for s in r["seasons_used"])
    if not any(n < len(records) for n in counts.values()):
        return []
    return [(s, SEASON_NAMES[s], counts[s]) for s in SEASON_NAMES if s in counts]


def safe_url(url, hosts=None):
    """Return url if it is http(s) (and, if given, on one of hosts), else ''.
    Blocks javascript:/data: links from user-submitted info.json."""
    parsed = urlparse(str(url or "").strip())
    try:
        port = parsed.port
    except ValueError:
        return ""
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return ""
    if hosts is not None and (parsed.scheme != "https" or parsed.hostname not in hosts):
        return ""
    # Rebuild from the validated host, dropping userinfo, so browsers and urlparse can't
    # disagree about the destination (e.g. "https://evil.com\\@github.com/").
    netloc = parsed.hostname + (f":{port}" if port else "")
    return parsed._replace(netloc=netloc).geturl()


def _as_list(value):
    return [value] if isinstance(value, str) else list(value or [])


def _parse_date(value):
    try:
        return datetime.fromisoformat(value).date()
    except (TypeError, ValueError):
        return None


def _load_record(section, category, folder):
    """Fetch and parse one post's info.json. Returns None if it is missing or malformed."""
    base_url = f"{RAW_BASE}/{section}/{category}/{folder}"
    try:
        resp = requests.get(f"{base_url}/info.json", timeout=TIMEOUT)
        resp.raise_for_status()
        info = resp.json()
        # Accept legacy "years-used" for posts not yet migrated to "seasons-used".
        seasons = _as_list(info.get("seasons-used", info.get("years-used")))
        normalized = [normalize_season(s) for s in seasons]
        record = {
            "id": folder,
            "title": info["title"],
            "author": info.get("author", ""),
            "description": info.get("description", ""),
            "team_number": info.get("team-number", ""),
            "preview_image_url": f"{base_url}/{info.get('preview-image-name', '')}",
            # Normalized known seasons drive the filter; display keeps what the author wrote.
            "seasons_used": list(dict.fromkeys(s for s in normalized if s)),
            "seasons_display": [
                format_season_with_name(n or s) for s, n in zip(seasons, normalized)
            ],
            "tags": _as_list(info.get("tags")),
            "added": _parse_date(info.get("timestamp")),
        }
        if section == "code":
            github_link = safe_url(info.get("github-link"))
            record["github_link"] = github_link
            record["download_url"] = (
                "" if github_link else f"{base_url}/{info.get('download-name', '')}"
            )
            record["language"] = info.get("language", "")
            record["used_in_comp"] = info.get("used-in-comp", False)
        elif section == "portfolios":
            record["download_url"] = f"{base_url}/{info.get('file-name', '')}"
            record["awards_won"] = info.get("awards-won", "")
        elif section == "cad":
            record["used_in_comp"] = info.get("used-in-comp", False)
            record["onshape_link"] = safe_url(info.get("onshape-link"))
        return record
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError) as e:
        print(f"Skipping {section}/{category}/{folder}: {e!r}")
        return None


def _fetch_post_folders():
    """{(section, category): [post folder names]} for every folder that has an info.json.
    One git-trees API call covers the whole repo, so the rate limit is spent once per TTL."""
    resp = requests.get(TREE_URL, headers=github_headers(), timeout=TIMEOUT)
    if resp.status_code == 401 and github_headers():
        # A bad/expired token must not take the site down; the repo is public.
        print("GITHUB_TOKEN rejected (401); retrying without auth. Replace the token.")
        resp = requests.get(TREE_URL, timeout=TIMEOUT)
    resp.raise_for_status()
    folders = {}
    for item in resp.json()["tree"]:
        parts = item["path"].split("/")  # ftc/<section>/<category>/<folder>/info.json
        if len(parts) == 5 and parts[0] == "ftc" and parts[4] == "info.json" and "filler" not in parts[3]:
            folders.setdefault((parts[1], parts[2]), []).append(parts[3])
    return folders


def _post_folders():
    global _folders
    if _folders and time.monotonic() - _folders[0] < CACHE_TTL:
        return _folders[1]
    try:
        _folders = (time.monotonic(), _fetch_post_folders())
    except (requests.RequestException, ValueError, KeyError) as e:
        if not _folders:
            raise
        # Stale listing beats an error page (e.g. while rate limited); retry after next TTL.
        print(f"GitHub listing failed, serving last good listing: {e!r}")
        _folders = (time.monotonic(), _folders[1])
    return _folders[1]


def fetch_data_from_github(section, category):
    """Return the list of post records for a category, or {"error": msg} on failure."""
    key = (section, category)
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL:
        return cached[1]

    try:
        folders = _post_folders().get(key, [])
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"GitHub listing failed: {e!r}")
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status in (403, 429):
            return {"error": "GitHub rate limit reached. Please try again in a few minutes."}
        return {"error": f"Could not load posts from GitHub (status {status or 'unavailable'})."}

    with ThreadPoolExecutor(max_workers=16) as pool:
        records = [
            r for r in pool.map(lambda f: _load_record(section, category, f), folders) if r
        ]

    # Oldest first; posts without a date go last.
    records.sort(key=lambda r: r["added"] or date.max)
    _cache[key] = (time.monotonic(), records)
    return records
