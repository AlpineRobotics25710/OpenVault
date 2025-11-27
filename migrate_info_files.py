"""
General migration script for info.json files in OpenVaultFiles repository.

This script allows you to:
1. Fetch all info.json files from the OpenVaultFiles repository
2. Apply custom transformations to the data
3. Generate updated files or push them directly to GitHub

Usage:
    python migrate_info_files.py --transform=<function_name> [--push] [--branch=<name>]

Examples:
    # Preview changes only
    python migrate_info_files.py --transform=my_transform

    # Generate files locally
    python migrate_info_files.py --transform=my_transform --generate

    # Push directly to GitHub (requires GITHUB_TOKEN)
    python migrate_info_files.py --transform=my_transform --push --branch=my-migration
"""

import requests
import json
import base64
import os
import sys
import argparse
from typing import List, Dict, Any, Callable, Optional


# GitHub configuration
GITHUB_OWNER = "AlpineRobotics25710"
GITHUB_REPO = "OpenVaultFiles"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# API endpoints
API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main"


# ==================== TRANSFORMATION FUNCTIONS ====================
# Add your custom transformation functions here


def example_transform(
    data: Dict[str, Any], file_info: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Example transformation function.

    Args:
        data: The current info.json data
        file_info: Additional info about the file (path, section, subsection, folder)

    Returns:
        Modified data dict, or None if no changes needed
    """
    # Example: Add a new field
    if "example-field" not in data:
        data["example-field"] = "example value"
        return data
    return None


def years_to_seasons_transform(
    data: Dict[str, Any], file_info: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Convert years-used to seasons-used format."""
    if "years-used" in data and "seasons-used" not in data:
        years_value = data["years-used"]

        # Convert to array if it's a string
        if isinstance(years_value, str):
            seasons = [years_value]
        elif isinstance(years_value, list):
            seasons = years_value
        else:
            seasons = []

        data["seasons-used"] = seasons
        del data["years-used"]
        return data
    return None


# Add your custom transformations to this registry
TRANSFORM_REGISTRY = {
    "example": example_transform,
    "years_to_seasons": years_to_seasons_transform,
}


# ==================== CORE FUNCTIONS ====================


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
            print(f"Fetching {section}/{subsection}...")

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


def apply_transform(
    files: List[Dict[str, Any]], transform_func: Callable
) -> Dict[str, Any]:
    """Apply transformation function to all files."""
    modified_files = []
    unchanged_files = []

    for file_info in files:
        data = file_info["data"].copy()
        result = transform_func(data, file_info)

        if result is not None:
            file_info["modified_data"] = result
            modified_files.append(file_info)
        else:
            unchanged_files.append(file_info)

    return {"modified": modified_files, "unchanged": unchanged_files}


def generate_local_files(
    files: List[Dict[str, Any]], output_dir: str = "migrated_files"
):
    """Generate modified files locally."""
    os.makedirs(output_dir, exist_ok=True)

    for file_info in files:
        file_path = os.path.join(output_dir, file_info["path"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(file_info["modified_data"], f, indent=4)

        print(f"  ✓ {file_info['path']}")

    print(f"\n✓ Updated files saved to ./{output_dir}/")


def get_file_sha(file_path: str, branch: str = "main") -> Optional[str]:
    """Get the SHA of an existing file in the repository."""
    url = f"{API_BASE}/contents/{file_path}?ref={branch}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    return None


def create_branch(branch_name: str, base_branch: str = "main") -> bool:
    """Create a new branch from base branch."""
    ref_url = f"{API_BASE}/git/ref/heads/{base_branch}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        print(f"Error getting base branch: {response.text}")
        return False

    base_sha = response.json()["object"]["sha"]

    create_ref_url = f"{API_BASE}/git/refs"
    data = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}

    response = requests.post(create_ref_url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"✓ Created branch: {branch_name}")
        return True
    elif "already exists" in response.text.lower():
        print(f"⚠ Branch already exists: {branch_name}")
        return True
    else:
        print(f"Error creating branch: {response.text}")
        return False


def push_to_github(files: List[Dict[str, Any]], branch_name: str, commit_message: str):
    """Push modified files to GitHub."""
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        return False

    # Create branch
    if not create_branch(branch_name):
        return False

    # Upload each file
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    for i, file_info in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Uploading {file_info['path']}...")

        url = f"{API_BASE}/contents/{file_info['path']}"
        content = json.dumps(file_info["modified_data"], indent=4)
        encoded_content = base64.b64encode(content.encode()).decode()

        sha = get_file_sha(file_info["path"], branch_name)

        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch_name,
        }

        if sha:
            data["sha"] = sha

        response = requests.put(url, headers=headers, json=data)

        if response.status_code in [200, 201]:
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Failed: {response.text}")

    return True


def create_pull_request(branch_name: str, title: str, body: str) -> Optional[str]:
    """Create a pull request."""
    url = f"{API_BASE}/pulls"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {"title": title, "body": body, "head": branch_name, "base": "main"}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        pr_url = response.json()["html_url"]
        print(f"✓ Pull request created: {pr_url}")
        return pr_url
    else:
        print(f"Error creating PR: {response.text}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Migrate info.json files in OpenVaultFiles repository"
    )
    parser.add_argument(
        "--transform",
        required=True,
        choices=list(TRANSFORM_REGISTRY.keys()),
        help="Transformation function to apply",
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate files locally"
    )
    parser.add_argument("--push", action="store_true", help="Push changes to GitHub")
    parser.add_argument(
        "--branch",
        default="migration",
        help="Branch name for GitHub push (default: migration)",
    )
    parser.add_argument("--pr-title", help="Pull request title")
    parser.add_argument("--pr-body", help="Pull request body")

    args = parser.parse_args()

    print("=" * 70)
    print("OpenVault Info Files Migration Tool")
    print("=" * 70)
    print()

    # Get transformation function
    transform_func = TRANSFORM_REGISTRY[args.transform]
    print(f"Using transformation: {args.transform}")
    print()

    # Fetch all files
    print("Fetching all info.json files...")
    all_files = fetch_all_info_files()
    print(f"Found {len(all_files)} files\n")

    # Apply transformation
    print("Applying transformation...")
    result = apply_transform(all_files, transform_func)

    modified = result["modified"]
    unchanged = result["unchanged"]

    print(f"  Modified: {len(modified)}")
    print(f"  Unchanged: {len(unchanged)}")
    print()

    if not modified:
        print("✓ No files need modification!")
        return

    # Show preview of changes
    print("Preview of changes (first 5):")
    for file_info in modified[:5]:
        print(f"  {file_info['path']}")
    if len(modified) > 5:
        print(f"  ... and {len(modified) - 5} more")
    print()

    # Generate or push
    if args.push:
        print("Pushing to GitHub...")
        commit_msg = f"Apply {args.transform} transformation to info.json files"

        if push_to_github(modified, args.branch, commit_msg):
            if args.pr_title:
                pr_title = args.pr_title
                pr_body = (
                    args.pr_body
                    or f"Applied {args.transform} transformation to {len(modified)} files"
                )
                create_pull_request(args.branch, pr_title, pr_body)

    elif args.generate:
        print("Generating files locally...")
        generate_local_files(modified)

    else:
        print("Preview mode - no files generated or pushed")
        print("\nUse --generate to create files locally")
        print("Use --push to push to GitHub")


if __name__ == "__main__":
    main()
