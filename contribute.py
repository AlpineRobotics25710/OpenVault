import base64
import json
import os

import requests
from dotenv import load_dotenv
from flask import render_template
from datetime import datetime

load_dotenv()

OWNER = os.getenv("OWNER")
REPO = os.getenv("REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH_NAME = "if-this-is-the-name-that-means-somethings-wrong"

GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"


def process_submit_pr(request):
    """Handles form submission and creates a PR."""

    form_data = extract_form_data(request)
    if not validate_required_fields(form_data):
        return render_error("Missing required fields")

    branch_name = generate_branch_name(form_data["team_number"], form_data["title"])
    create_branch_response = create_branch(branch_name)
    if "error" in create_branch_response:
        return render_error(create_branch_response)

    preview_file = request.files.get("previewImage")
    if preview_file:
        file_response = upload_preview_image(preview_file, form_data, branch_name)
        if "error" in file_response:
            return render_error(file_response)

    upload_file_response = upload_main_file(request, form_data, branch_name)
    if upload_file_response and "error" in upload_file_response:
        return render_error(upload_file_response)

    info_response = upload_info_json(request, form_data, branch_name)
    if "error" in info_response:
        return render_error(info_response)

    pr_title, pr_body = generate_pr_details(form_data)
    pr_response = create_pull_request(pr_title, pr_body, branch_name)

    if pr_response:
        return render_template("ftc/contribute.html", submitted=True)
    else:
        return render_error(pr_response)


def create_branch(branch_name, base_branch="main"):
    """Creates a new branch from main (or another base branch)."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    print(GITHUB_TOKEN)

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

    return True


def extract_form_data(req):
    return {
        "email": req.form.get("email"),
        "team_number": req.form.get("teamNumber"),
        "title": req.form.get("title"),
        "author": req.form.get("author"),
        "description": req.form.get("description"),
        "category": req.form.get("category"),
        "cad_subcategory": req.form.get("cadSubcategory"),
        "code_subcategory": req.form.get("codeSubcategory")
    }


def validate_required_fields(data):
    return all(data.get(field) for field in ["email", "team_number", "title", "category"])


def generate_branch_name(team_number, title):
    return f"{team_number}-{title.replace(' ', '_')}"


def render_error(error_message):
    return render_template("ftc/contribute.html", error=True, error_message={"error": str(error_message)}), 400


def upload_preview_image(preview_file, data, branch_name):
    category = data["category"]
    subcategory = data["code_subcategory"] if category == "Code" else data["cad_subcategory"]

    if category == "Code":
        path = f"ftc/code/{subcategory}/{branch_name}"
    elif category == "Portfolios":
        path = f"ftc/portfolios/portfolios/{branch_name}"
    elif category == "CAD":
        path = f"ftc/cad/{subcategory}/{branch_name}"

    preview_filename = f"{path}/{preview_file.filename}"
    content = preview_file.read()
    return create_file(preview_filename, base64.b64encode(content).decode("utf-8"), branch_name)


def upload_main_file(req, data, branch_name):
    category = data["category"]
    file = None
    filename = None

    if category == "Code":
        file = req.files.get("codeUpload")
        filename = f"ftc/code/{data['code_subcategory']}/{branch_name}/{file.filename}"
    elif category == "Portfolios":
        file = req.files.get("portfolioUpload")
        filename = f"ftc/portfolios/portfolios/{branch_name}/{file.filename}"

    if file:
        content = file.read()
        return create_file(filename, base64.b64encode(content).decode("utf-8"), branch_name)


def upload_info_json(req, data, branch_name):
    preview_file = req.files.get("previewImage")
    category = data["category"]

    info_data = {
        "preview-image-name": preview_file.filename if preview_file else "",
        "title": data["title"],
        "author": data["author"],
        "description": data["description"],
        "team-number": data["team_number"],
        "email": data["email"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if category == "Code":
        file = req.files.get("codeUpload")
        info_data.update({
            "download-name": file.filename if file else "",
            "used-in-comp": req.form.get("usedInCompCode") == "on",
            "years-used": req.form.get("yearsUsed"),
            "language": req.form.get("languageUsed"),
        })
        path = f"ftc/code/{data['code_subcategory']}/{branch_name}/info.json"
    elif category == "Portfolios":
        file = req.files.get("portfolioUpload")
        info_data.update({
            "file-name": file.filename if file else "",
            "years-used": req.form.get("yearsUsed"),
            "awards-won": req.form.get("awardsWon"),
        })
        path = f"ftc/portfolios/portfolios/{branch_name}/info.json"
    elif category == "CAD":
        info_data.update({
            "used-in-comp": req.form.get("usedInCompCAD") == "on",
            "years-used": req.form.get("yearsUsed"),
            "onshape-link": req.form.get("onshapeLink"),
        })
        path = f"ftc/cad/{data['cad_subcategory']}/{branch_name}/info.json"

    encoded = base64.b64encode(json.dumps(info_data, indent=4).encode("utf-8")).decode("utf-8")
    return create_file(path, encoded, branch_name)


def generate_pr_details(data):
    title = f"{data['team_number']} - {data['title']}"
    body = (
        f"Team {data['team_number']} is submitting {data['title']} under {data['category']}. "
        "This Pull Request was automatically generated by the OpenVault website by submitting the form on the 'Contribute' page."
    )
    return title, body
