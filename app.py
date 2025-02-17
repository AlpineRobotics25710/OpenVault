import base64
import uuid
import json

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, session, jsonify
from requests import JSONDecodeError
from contribute import create_pull_request, create_file, create_branch

app = Flask(__name__)
app.secret_key = "779650ac697181207529db19091dc55b93aa47a70ffbbe52d9cb8330c7b9ed4f"


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    # print(session["curr_template"])
    return {'active_route': session["curr_template"]}


# Generic function to fetch data from GitHub
def fetch_data_from_github(section, sub_section):
    base_url = "https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc"
    github_page = requests.get(
        f"https://github.com/AlpineRobotics25710/OpenVaultFiles/tree/main/ftc/{section}/{sub_section}")
    session["records"] = []

    if github_page.status_code == 200:
        soup = BeautifulSoup(github_page.content, "html.parser")
        unique_titles = set()
        links = [subfolder for subfolder in soup.find_all("a", class_="Link--primary") if
                 subfolder.get("title") not in unique_titles and not unique_titles.add(
                     subfolder.get("title")) and "filler" not in subfolder.get("title")]

        for subfolder in links:
            post_info = requests.get(f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/info.json")
            if post_info.status_code == 200:
                try:
                    post_info_json = post_info.json()
                except JSONDecodeError:
                    continue

                record = {"uuid": str(uuid.uuid4()),
                          "preview_image_url": f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['preview-image-name']}",
                          "title": post_info_json["title"], "author": post_info_json["author"],
                          "description": post_info_json["description"], "team_number": post_info_json["team-number"],
                          "years_used": post_info_json["years-used"], }

                if section == "code":
                    record[
                        "download_url"] = f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['download-name']}"
                    record["language"] = post_info_json["language"]
                    record["used_in_comp"] = post_info_json["used-in-comp"]
                elif section == "portfolios":
                    record[
                        "download_url"] = f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['file-name']}"
                    record["awards_won"] = post_info_json["awards-won"]
                elif section == "cad":
                    record["used_in_comp"] = post_info_json["used-in-comp"]
                    record["onshape_link"] = post_info_json["onshape-link"]

                session["records"].append(record)

    return session["records"]


@app.route('/search', methods=["POST"])
def search():
    if "curr_template" not in session:
        return index()

    if "records" not in session or session["records"] == []:
        return render_template(session["curr_template"], records=session["records"])

    curr_template = session["curr_template"]
    records = session["records"]
    # print("curr template:" + curr_template)
    # print("records:" + str(records))
    if request.method == "POST":
        search_query = request.form.get("searchBox")
        if search_query == "":
            return render_template(curr_template, records=records)
        if search_query:
            search_query = search_query.lower()
            # print("search query:" + search_query)
            # print(records)
            filtered_records = []
            for record in records:
                if (search_query in record["title"].lower() or search_query in record[
                    "author"].lower() or search_query in record["description"].lower() or search_query in record[
                    "team_number"].lower() or search_query in record["years_used"].lower() or (
                        "code" in curr_template and search_query in record["language"].lower()) or (
                        "portfolios" in curr_template and search_query in record["awards_won"].lower())):
                    filtered_records.append(record)
            return render_template(curr_template, records=filtered_records)

    return render_template(curr_template, records=records)


@app.route('/')
def index():
    session["curr_template"] = "ftc/index.html"
    return render_template("ftc/index.html")


@app.route('/contribute')
def contribute():
    session["curr_template"] = "ftc/contribute.html"
    return render_template("ftc/contribute.html", submitted=False)


@app.route("/submit-pr", methods=["POST"])
def submit_pr():
    """Handles form submission and creates a PR."""

    # Step 1: Validate input fields
    team_number = request.form.get("teamNumber")
    title = request.form.get("title")
    author = request.form.get("author")
    description = request.form.get("description")
    category = request.form.get("category")
    cad_subcategory = request.form.get("cadSubcategory")
    code_subcategory = request.form.get("codeSubcategory")

    if not team_number or not title or not category:
        return render_template("ftc/contribute.html", error=True, error_message={"error": "Missing required fields"}), 400

    # Generate branch name
    branch_name = f"{team_number}-{title.replace(' ', '_')}"

    # Step 2: Create a new branch
    create_branch_response = create_branch(branch_name)
    if "error" in create_branch_response:
        return render_template("ftc/contribute.html", error=True, error_message=create_branch_response), 400

    # Step 3: Upload the preview image
    preview_file = request.files.get("previewImage")
    if preview_file:
        preview_file_path = ""
        if category == "Code":
            preview_file_path = f"ftc/code/{code_subcategory}/{branch_name}"
        elif category == "Portfolios":
            preview_file_path = f"ftc/portfolios/portfolios/{branch_name}"
        elif category == "CAD":
            preview_file_path = f"ftc/cad/{cad_subcategory}/{branch_name}"
        preview_filename = f"{preview_file_path}/{preview_file.filename}"
        preview_content = preview_file.read()
        file_response = create_file(preview_filename, base64.b64encode(preview_content).decode("utf-8"), branch_name)
        if "error" in file_response:
            return render_template("ftc/contribute.html", error=True, error_message=file_response), 400

    # Step 4: Upload the code zip file or portfolio PDF
    file = None
    filename = None
    if category == "Code":
        file = request.files.get("codeUpload")
        filename = f"ftc/code/{code_subcategory}/{branch_name}/{file.filename}"
    elif category == "Portfolios":
        file = request.files.get("portfolioUpload")
        filename = f"ftc/portfolios/portfolios/{branch_name}/{file.filename}"

    if file:
        file_content = file.read()
        file_response = create_file(filename, base64.b64encode(file_content).decode("utf-8"), branch_name)
        if "error" in file_response:
            return render_template("ftc/contribute.html", error=True, error_message=file_response), 400

    # Step 5: Create the info.json file
    # Do not change this formatting, it needs to be formatted like this
    info_data = {
        "preview-image-name": preview_file.filename,
        "title": title,
        "author": author,
        "description": description,
        "team-number": team_number,
    }

    info_file_path = None
    if category == "Code":
        info_file_path = f"ftc/code/{code_subcategory}/{branch_name}/info.json"
        info_data.update({
            "download-name": file.filename,
            "used-in-comp": True if request.form.get("usedInCompCode") == "on" else False,
            "years-used": request.form.get("yearsUsed"),
            "language": request.form.get("languageUsed"),
        })
    elif category == "Portfolios":
        info_file_path = f"ftc/portfolios/portfolios/{branch_name}/info.json"
        info_data.update({
            "file-name": file.filename,
            "years-used": request.form.get("yearsUsed"),
            "awards-won": request.form.get("awardsWon"),
        })
    elif category == "CAD":
        info_file_path = f"ftc/cad/{cad_subcategory}/{branch_name}/info.json"
        info_data.update({
            "used-in-comp": True if request.form.get("usedInCompCAD") == "on" else False,
            "years-used": request.form.get("yearsUsed"),
            "onshape-link": request.form.get("onshapeLink"),
        })

    # Convert to JSON and encode it
    info_content = json.dumps(info_data, indent=4)
    encoded_content = base64.b64encode(info_content.encode("utf-8")).decode("utf-8")

    # Create the info.json file in the correct directory
    file_response = create_file(info_file_path, encoded_content, branch_name)

    if "error" in file_response:
        return render_template("ftc/contribute.html", error=True, error_message=file_response), 400

    # Step 6: Create a pull request
    pr_title = f"{team_number} - {title}"
    pr_body = f"Team {team_number} is submitting {title} under {category}. This Pull Request was automatically generated by the OpenVault website by submitting the form on the 'Contribute' page."

    pr_response = create_pull_request(pr_title, pr_body, branch_name)

    if pr_response:
        session["curr_template"] = "ftc/contribute.html"
        return render_template("ftc/contribute.html", submitted=True)
    else:
        return render_template("ftc/contribute.html", error=True, error_message=pr_response), 400


@app.route('/cad/<category>')
def render_cad_page(category):
    session["records"] = fetch_data_from_github("cad", category)
    session["curr_template"] = f"ftc/cad/{category}.html"
    return render_template(session["curr_template"], records=session["records"])


@app.route('/code/<category>')
def render_code_page(category):
    session["records"] = fetch_data_from_github("code", category)
    session["curr_template"] = f"ftc/code/{category}.html"
    return render_template(session["curr_template"], records=session["records"])


@app.route('/portfolios')
def portfolios():
    session["records"] = fetch_data_from_github("portfolios", "portfolios")
    session["curr_template"] = "ftc/portfolios/portfolios.html"
    return render_template(session["curr_template"], records=session["records"])


if __name__ == '__main__':
    app.run(debug=True)
