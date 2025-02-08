import requests
import base64
from flask import request

# Expires in a year. Keep secret.
GITHUB_TOKEN = "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"
OWNER = "AlpineRobotics25710"
REPO = "OpenVaultFiles"
BRANCH_NAME = "if-this-is-the-name-that-means-somethings-wrong"

GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"

def create_branch(base_branch="main"):
    global BRANCH_NAME
    """Creates a new branch from main (or another base branch)."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Get latest commit SHA of the base branch
    base_branch_info = requests.get(f"{GITHUB_API_URL}/git/ref/heads/{base_branch}", headers=headers)
    if base_branch_info.status_code != 200:
        return {"error": "Failed to get base branch info", "details": base_branch_info.json()}

    base_sha = base_branch_info.json()["object"]["sha"]

    # Create a new branch
    BRANCH_NAME = request.form.get("teamNumber") + "-" + request.form.get("title").replace(" ", "_")
    branch_ref = f"refs/heads/{BRANCH_NAME}"
    create_branch_response = requests.post(
        f"{GITHUB_API_URL}/git/refs",
        headers=headers,
        json={"ref": branch_ref, "sha": base_sha}
    )

    return create_branch_response.json()

def create_file(filename, content, branch=BRANCH_NAME):
    """Creates a file in the repository."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    file_url = f"{GITHUB_API_URL}/contents/{filename}"

    create_file_response = requests.put(
        file_url,
        headers=headers,
        json={
            "message": f"Add {filename}",
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),  # Ensure Base64 encoding
            "branch": branch
        }
    )

    return create_file_response.json()

def create_pull_request(title, body, head=BRANCH_NAME, base="main"):
    """Creates a pull request."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    pr_url = f"{GITHUB_API_URL}/pulls"

    pr_response = requests.post(
        pr_url,
        headers=headers,
        json={"title": title, "body": body, "head": head, "base": base}
    )

    return pr_response.json()
