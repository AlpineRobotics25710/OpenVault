"""
Migration script to convert years-used to seasons-used in OpenVaultFiles repository.

This script will:
1. Fetch all info.json files from the OpenVaultFiles repository
2. Convert any "years-used" fields to "seasons-used" format
3. Generate the commands or API calls needed to update the files

Usage:
    python migrate_years_to_seasons.py
"""

import requests
import json
import base64
from typing import List, Dict, Any


# GitHub configuration
GITHUB_OWNER = "AlpineRobotics25710"
GITHUB_REPO = "OpenVaultFiles"
GITHUB_TOKEN = None  # Set this to your GitHub personal access token if needed

# API endpoints
API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main"


def parse_years_to_seasons(years_value: Any) -> List[str]:
    """
    Convert old years-used format to seasons-used array.

    Examples:
        "2024-2025" -> ["2024-2025"]
        "2023-2024, 2024-2025" -> ["2023-2024", "2024-2025"]
        "24-25" -> ["2024-2025"]
    """
    if isinstance(years_value, list):
        # Already in array format, just return it
        return years_value

    if not years_value or not isinstance(years_value, str):
        return []

    # Split by comma and clean up
    parts = [p.strip() for p in str(years_value).split(",")]
    seasons = []

    for part in parts:
        if not part:
            continue

        # Handle short format like "24-25"
        if len(part) == 5 and "-" in part:
            year1, year2 = part.split("-")
            if len(year1) == 2 and len(year2) == 2:
                # Convert 24-25 to 2024-2025
                full_year1 = f"20{year1}"
                full_year2 = f"20{year2}"
                part = f"{full_year1}-{full_year2}"

        seasons.append(part)

    return seasons


def fetch_all_info_files() -> List[Dict[str, Any]]:
    """Fetch all info.json files from the repository."""
    sections = {
        "code": ["autonomous", "full-repo", "teleop", "vision"],
        "cad": [
            "active-intakes",
            "claws",
            "dead-axles",
            "drivetrains",
            "outtakes",
            "power-transmissions",
            "robots",
        ],
        "portfolios": ["portfolios"],
    }

    all_files = []

    for section, subsections in sections.items():
        for subsection in subsections:
            api_url = f"{API_BASE}/contents/ftc/{section}/{subsection}"
            print(f"Checking {section}/{subsection}...")

            response = requests.get(api_url)
            if response.status_code != 200:
                print(f"  Warning: Could not access {section}/{subsection}")
                continue

            entries = response.json()
            for entry in entries:
                if entry["type"] == "dir" and "filler" not in entry["name"]:
                    info_path = f"ftc/{section}/{subsection}/{entry['name']}/info.json"
                    info_url = f"{RAW_BASE}/{info_path}"

                    info_response = requests.get(info_url)
                    if info_response.status_code == 200:
                        try:
                            info_data = info_response.json()
                            all_files.append(
                                {
                                    "path": info_path,
                                    "data": info_data,
                                    "section": section,
                                    "subsection": subsection,
                                    "folder": entry["name"],
                                }
                            )
                        except Exception as e:
                            print(f"  Error parsing {info_path}: {e}")

    return all_files


def analyze_migrations(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which files need migration."""
    needs_migration = []
    already_migrated = []

    for file_info in files:
        data = file_info["data"]
        has_old = "years-used" in data
        has_new = "seasons-used" in data

        if has_old and not has_new:
            needs_migration.append(file_info)
        elif has_new:
            already_migrated.append(file_info)

    return {"needs_migration": needs_migration, "already_migrated": already_migrated}


def migrate_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate a single file from years-used to seasons-used."""
    data = file_info["data"].copy()

    if "years-used" in data:
        old_value = data["years-used"]
        new_value = parse_years_to_seasons(old_value)

        # Add new field
        data["seasons-used"] = new_value

        # Remove old field
        del data["years-used"]

    return data


def main():
    print("=" * 70)
    print("OpenVault Migration Script: years-used → seasons-used")
    print("=" * 70)
    print()

    # Fetch all files
    print("Step 1: Fetching all info.json files from repository...")
    all_files = fetch_all_info_files()
    print(f"Found {len(all_files)} info.json files\n")

    # Analyze what needs migration
    print("Step 2: Analyzing which files need migration...")
    analysis = analyze_migrations(all_files)

    needs_migration = analysis["needs_migration"]
    already_migrated = analysis["already_migrated"]

    print(f"  Already migrated: {len(already_migrated)}")
    print(f"  Needs migration: {len(needs_migration)}")
    print()

    if not needs_migration:
        print("✓ All files are already using the new seasons-used format!")
        return

    # Show files that need migration
    print("Step 3: Files needing migration:")
    for file_info in needs_migration:
        old_value = file_info["data"].get("years-used")
        new_value = parse_years_to_seasons(old_value)
        print(f"  {file_info['path']}")
        print(f"    Old: years-used = {repr(old_value)}")
        print(f"    New: seasons-used = {new_value}")
        print()

    # Generate migration plan
    print("=" * 70)
    print("Migration Options:")
    print("=" * 70)
    print()
    print("Option 1: Manual Migration")
    print("  - Clone the OpenVaultFiles repository")
    print("  - Run this script with --update flag (requires GitHub token)")
    print()
    print("Option 2: Generate Updated Files")
    print("  - This script can generate the updated JSON files")
    print("  - You can then manually commit them to the repository")
    print()

    choice = input("Generate updated JSON files? (y/n): ").strip().lower()

    if choice == "y":
        print("\nGenerating updated files...")
        import os

        output_dir = "migrated_files"
        os.makedirs(output_dir, exist_ok=True)

        for file_info in needs_migration:
            migrated_data = migrate_file(file_info)

            # Create directory structure
            file_path = os.path.join(output_dir, file_info["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write migrated file
            with open(file_path, "w") as f:
                json.dump(migrated_data, f, indent=4)

            print(f"  ✓ {file_info['path']}")

        print(f"\n✓ Updated files saved to ./{output_dir}/")
        print(f"  You can now copy these files to the OpenVaultFiles repository")
    else:
        print("\nMigration cancelled.")


if __name__ == "__main__":
    main()
