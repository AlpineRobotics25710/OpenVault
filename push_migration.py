"""
Script to push the migrated files to the OpenVaultFiles repository.

This script will create a Pull Request with all the migrated info.json files.
"""

import os
import sys
import json
import base64
from dotenv import load_dotenv
import requests
from pathlib import Path

load_dotenv()

# GitHub configuration
GITHUB_OWNER = "AlpineRobotics25710"
GITHUB_REPO = "OpenVaultFiles"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Set via environment variable

API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"


def get_file_sha(file_path, branch="main"):
    """Get the SHA of an existing file in the repository."""
    url = f"{API_BASE}/contents/{file_path}?ref={branch}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    return None


def create_or_update_file(file_path, content, message, branch):
    """Create or update a file in the repository."""
    url = f"{API_BASE}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get existing file SHA if it exists
    sha = get_file_sha(file_path, branch)

    # Encode content
    encoded_content = base64.b64encode(content.encode()).decode()

    data = {"message": message, "content": encoded_content, "branch": branch}

    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)
    return response


def create_branch(branch_name, base_branch="main"):
    """Create a new branch from base branch."""
    # Get the SHA of the base branch
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

    # Create new branch
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


def create_pull_request(branch_name, title, body):
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
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("\nTo set it, run:")
        print("  export GITHUB_TOKEN=your_github_token_here")
        print("\nYou can create a token at: https://github.com/settings/tokens")
        print("Required scopes: repo")
        sys.exit(1)

    print("=" * 70)
    print("Push Migration to OpenVaultFiles Repository")
    print("=" * 70)
    print()

    # Check if migrated_files directory exists
    if not os.path.exists("migrated_files"):
        print("ERROR: migrated_files directory not found")
        print("Please run migrate_years_to_seasons.py first")
        sys.exit(1)

    # Create a new branch
    branch_name = "migrate-years-to-seasons"
    if not create_branch(branch_name):
        print("Failed to create branch")
        sys.exit(1)

    # Find all migrated JSON files
    migrated_files = []
    for root, dirs, files in os.walk("migrated_files/ftc"):
        for file in files:
            if file == "info.json":
                full_path = os.path.join(root, file)
                # Get relative path from migrated_files/
                rel_path = os.path.relpath(full_path, "migrated_files")
                migrated_files.append((full_path, rel_path))

    print(f"\nFound {len(migrated_files)} files to upload")
    print()

    # Upload each file
    for i, (local_path, repo_path) in enumerate(migrated_files, 1):
        print(f"[{i}/{len(migrated_files)}] Uploading {repo_path}...")

        with open(local_path, "r") as f:
            content = f.read()

        response = create_or_update_file(
            repo_path,
            content,
            f"Migrate {repo_path} from years-used to seasons-used",
            branch_name,
        )

        if response.status_code in [200, 201]:
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Failed: {response.text}")

    print()
    print("=" * 70)
    print("Creating Pull Request...")
    print("=" * 70)

    pr_title = "Migrate info.json files from years-used to seasons-used"
    pr_body = f"""## Migration: years-used → seasons-used

This PR migrates all `info.json` files from the old `years-used` (string) format to the new `seasons-used` (array) format.

### Changes
- Updated {len(migrated_files)} info.json files
- Changed field name from `years-used` to `seasons-used`
- Converted values from string to array format

### Examples
- `"years-used": "2024-2025"` → `"seasons-used": ["2024-2025"]`
- `"years-used": "N/A"` → `"seasons-used": ["N/A"]`

### Backwards Compatibility
The OpenVault web application already supports both formats through backwards compatibility code in `util.py`:
```python
"seasons_used": post_info_json.get("seasons-used", post_info_json.get("years-used", []))
```

This ensures old posts will continue to work during and after the migration.
"""

    pr_url = create_pull_request(branch_name, pr_title, pr_body)

    if pr_url:
        print()
        print("=" * 70)
        print("✓ Migration Complete!")
        print("=" * 70)
        print(f"\nPull Request: {pr_url}")
        print("\nNext steps:")
        print("1. Review the PR on GitHub")
        print("2. Merge the PR to apply the changes")
    else:
        print("\n⚠ Files uploaded but PR creation failed")
        print("You can manually create a PR from the branch:", branch_name)


if __name__ == "__main__":
    main()
