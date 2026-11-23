import base64
import json
import re
import secrets
from datetime import datetime

import requests
from flask import render_template
from werkzeug.utils import secure_filename

from util import CATEGORIES, CONTENT_REPO, TIMEOUT, github_headers, safe_url

GITHUB_API_URL = f"https://api.github.com/repos/{CONTENT_REPO}"

# Form category value -> site section
FORM_SECTIONS = {"CAD": "cad", "Code": "code", "Portfolios": "portfolios"}
REQUIRED_FIELDS = ["email", "team_number", "title", "author", "description", "category"]


class SubmissionError(Exception):
    pass


def process_submit_pr(request):
    """Handles the contribute form: creates a branch, uploads files, opens a PR."""
    form = request.form
    data = {
        "email": form.get("email", "").strip(),
        "team_number": form.get("teamNumber", "").strip(),
        "title": form.get("title", "").strip(),
        "author": form.get("author", "").strip(),
        "description": form.get("description", "").strip(),
        "category": form.get("category", ""),
    }
    if not all(data[f] for f in REQUIRED_FIELDS):
        return render_error("Missing required fields.")
    if not data["team_number"].isdigit():
        return render_error("Team number must be a number.")

    section = FORM_SECTIONS.get(data["category"])
    if section == "cad":
        category = form.get("cadSubcategory")
    elif section == "code":
        category = form.get("codeSubcategory")
    else:
        category = "portfolios"
    if section is None or category not in CATEGORIES[section]:
        return render_error("Please choose a valid category and subcategory.")

    if section == "cad":
        if not safe_url(form.get("onshapeLink"), {"cad.onshape.com"}):
            return render_error("Onshape link must start with https://cad.onshape.com/")
    elif section == "code" and form.get("codeSource", "zip") == "github":
        if not safe_url(form.get("githubLink"), {"github.com"}):
            return render_error("GitHub link must start with https://github.com/")

    branch = generate_branch_name(data["team_number"], data["title"])
    folder = f"ftc/{section}/{category}/{branch}"

    try:
        create_branch(branch)
        preview_name = upload_file(request.files.get("previewImage"), folder, branch)
        main_name = ""
        if section == "portfolios":
            main_name = upload_file(request.files.get("portfolioUpload"), folder, branch)
        elif section == "code" and form.get("codeSource", "zip") == "zip":
            main_name = upload_file(request.files.get("codeUpload"), folder, branch)

        info = build_info_json(form, data, section, preview_name, main_name)
        create_file(f"{folder}/info.json", json.dumps(info, indent=4).encode(), branch)
        create_pull_request(data, branch)
    except SubmissionError as e:
        return render_error(str(e))
    except requests.RequestException as e:
        print(f"GitHub request failed for {branch}: {e!r}")
        return render_error("Could not reach GitHub. Please try again later.")

    # Contributor email stays out of the public repo and PR; it is only logged
    # so moderators can reach the submitter.
    print(f"Submission {branch} contact email: {data['email']}")
    return render_template("ftc/contribute.html", submitted=True)


def generate_branch_name(team_number, title):
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")[:50] or "submission"
    return f"{team_number}-{slug}-{secrets.token_hex(3)}"


def github_call(method, path, **kwargs):
    """Call the GitHub API; raise SubmissionError with details logged on a non-2xx response."""
    resp = requests.request(
        method, f"{GITHUB_API_URL}{path}", headers=github_headers(), timeout=TIMEOUT, **kwargs
    )
    if not resp.ok:
        print(f"GitHub {method} {path} failed: {resp.status_code} {resp.text[:500]}")
        raise SubmissionError(f"GitHub rejected the submission (status {resp.status_code}).")
    return resp.json()


def create_branch(branch, base_branch="main"):
    base_sha = github_call("GET", f"/git/ref/heads/{base_branch}")["object"]["sha"]
    github_call("POST", "/git/refs", json={"ref": f"refs/heads/{branch}", "sha": base_sha})


def create_file(path, content, branch):
    github_call(
        "PUT",
        f"/contents/{path}",
        json={
            "message": f"Add {path}",
            "content": base64.b64encode(content).decode(),
            "branch": branch,
        },
    )


def upload_file(file, folder, branch):
    """Upload an optional form file into the post folder. Returns the stored filename or ''."""
    if not file or not file.filename:
        return ""
    name = secure_filename(file.filename) or "upload"
    create_file(f"{folder}/{name}", file.read(), branch)
    return name


def build_info_json(form, data, section, preview_name, main_name):
    try:
        tags = json.loads(form.get("tags") or "[]")
    except ValueError:
        tags = []

    info = {
        "preview-image-name": preview_name,
        "title": data["title"],
        "author": data["author"],
        "description": data["description"],
        "team-number": data["team_number"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tags": [str(t) for t in tags] if isinstance(tags, list) else [],
        "seasons-used": form.getlist("seasons"),
    }
    if section == "code":
        is_github = form.get("codeSource", "zip") == "github"
        info.update(
            {
                "download-name": "" if is_github else main_name,
                "github-link": safe_url(form.get("githubLink"), {"github.com"}) if is_github else "",
                "used-in-comp": form.get("usedInCompCode") == "on",
                "language": form.get("languageUsed", ""),
            }
        )
    elif section == "portfolios":
        info.update({"file-name": main_name, "awards-won": form.get("awardsWon", "")})
    elif section == "cad":
        info.update(
            {
                "used-in-comp": form.get("usedInCompCAD") == "on",
                "onshape-link": safe_url(form.get("onshapeLink"), {"cad.onshape.com"}),
            }
        )
    return info


def create_pull_request(data, branch):
    body = (
        f"Team {data['team_number']} is submitting {data['title']} under {data['category']}. "
        "This Pull Request was automatically generated by the OpenVault website by "
        "submitting the form on the 'Contribute' page."
    )
    github_call(
        "POST",
        "/pulls",
        json={
            "title": f"{data['team_number']} - {data['title']}",
            "body": body,
            "head": branch,
            "base": "main",
        },
    )


def render_error(message):
    return render_template("ftc/contribute.html", error=True, error_message=message), 400
