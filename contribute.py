import requests

# Expires in a year. Keep secret.
GITHUB_TOKEN = "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"
OWNER = "AlpineRobotics25710"
REPO = "OpenVaultFiles"
BRANCH_NAME = "if-this-is-the-name-that-means-somethings-wrong"

GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"


def create_branch(branch_name, base_branch="main"):
    """Creates a new branch from main (or another base branch)."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # Get latest commit SHA of the base branch
    base_branch_info = requests.get(f"{GITHUB_API_URL}/git/ref/heads/{base_branch}", headers=headers)
    if base_branch_info.status_code != 200:
        return {"error": "Failed to get base branch info", "details": base_branch_info.json()}

    base_sha = base_branch_info.json()["object"]["sha"]

    # Create a new branch
    branch_ref = f"refs/heads/{branch_name}"
    create_branch_response = requests.post(f"{GITHUB_API_URL}/git/refs", headers=headers,
                                           json={"ref": branch_ref, "sha": base_sha})

    if create_branch_response.status_code != 201:
        return {"error": "Failed to create branch", "details": create_branch_response.json()}

    return {"message": "Branch created successfully", "branch_name": branch_name}


def get_file_sha(filename, branch_name):
    """Gets the SHA of an existing file (if it exists) to update it."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    file_url = f"{GITHUB_API_URL}/contents/{filename}?ref={branch_name}"

    response = requests.get(file_url, headers=headers)

    if response.status_code == 200:
        return response.json().get("sha")  # Return SHA if file exists
    return None  # Return None if file does not exist


def create_file(filename, encoded_content, branch_name):
    """Creates or updates a file in the repository."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    file_url = f"{GITHUB_API_URL}/contents/{filename}"

    # Get SHA if file exists
    sha = get_file_sha(filename, branch_name)

    data = {
        "message": f"Add or update {filename}",
        "content": encoded_content,
        "branch": branch_name,
    }

    if sha:
        data["sha"] = sha  # Required for updating an existing file

    create_file_response = requests.put(file_url, headers=headers, json=data)

    if create_file_response.status_code not in [200, 201]:
        return {"error": "Failed to create file", "details": create_file_response.json(), "filename": filename}

    return {"message": "File created successfully", "filename": filename}


def create_pull_request(title, body, branch_name, base="main"):
    """Creates a pull request."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    pr_url = f"{GITHUB_API_URL}/pulls"

    pr_response = requests.post(pr_url, headers=headers,
                                json={"title": title, "body": body, "head": branch_name, "base": base})

    if pr_response.status_code != 201:
        return {"error": "Failed to create PR", "details": pr_response.json()}

    return {"message": "Pull request created successfully", "pr_url": pr_response.json().get("html_url")}
