import base64
import json

import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session

from contribute import create_pull_request, create_file, create_branch
from util import fetch_data_from_github, embed_text, build_index, load_index

# TODO: Add filters
# TODO: Record the date posted and sort posts by date

app = Flask(__name__)
app.secret_key = "779650ac697181207529db19091dc55b93aa47a70ffbbe52d9cb8330c7b9ed4f"


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    # print(session["curr_template"])
    return {'active_route': session["curr_template"]}


@app.route('/')
def index():
    session["curr_template"] = "ftc/index.html"
    return render_template("ftc/index.html")


@app.route('/contribute')
def contribute():
    session["curr_template"] = "ftc/contribute.html"
    return render_template("ftc/contribute.html", submitted=False)


@app.route('/<base>/<category>')
def render_page(base, category):
    session["records"] = fetch_data_from_github(base, category)
    session["curr_template"] = f"ftc/{base}/{category}.html"
    build_index(session.get("records"))
    return render_template(session.get("curr_template"), records=session.get("records"))


# For legacy purposes/ease of use. You can access portfolios through /portfolios/portfolios
@app.route('/portfolios')
def portfolios():
    return redirect(url_for("render_page", base="portfolios", category="portfolios"))


@app.route('/search', methods=["GET", "POST"])
def search():
    #print("Search function was called")

    if request.method == "GET":
        return redirect(url_for("index"))

    if "curr_template" not in session or "records" not in session:
        return redirect(url_for("index"))

    curr_template = session.get("curr_template")
    records = session.get("records")
    search_query = request.form.get("searchBox", "").strip()

    # Load index and metadata from files
    index_data = load_index()  # loads vocab, search_index, record_embeddings
    search_index = index_data["search_index"]
    record_embeddings = index_data["record_embeddings"]
    vocab = index_data["vocab"]

    # print("Search query is: ", search_query)
    # print("search index is: ", search_index)
    # print("record embedding shape is: ", record_embeddings.shape)
    # print("vocab size is: ", len(vocab))

    filtered_records = []
    if not search_query:
        filtered_records = records
        #print("search query is empty")
    elif len(records) > 0 and record_embeddings is not None and search_index is not None:
        query_vector = embed_text(search_query, vocab)
        #print("Processed query vector.")

        if np.linalg.norm(query_vector) > 0:
            D, I = search_index.search(np.array([query_vector]).astype('float32'), k=len(records))
            indices = I[0]
            similarities = D[0]
            #print("similarities: " + str(similarities))

            threshold = 0.00
            filtered = [(i, sim) for i, sim in zip(indices, similarities) if sim > threshold]
            sorted_filtered = sorted(filtered, key=lambda x: x[1], reverse=True)
            filtered_records = [records[i] for i, _ in sorted_filtered]

    return render_template(curr_template, records=filtered_records)


@app.route("/submit-pr", methods=["POST"])
def submit_pr():
    """Handles form submission and creates a PR."""

    # Step 1: Validate input fields
    email = request.form.get("email")
    team_number = request.form.get("teamNumber")
    title = request.form.get("title")
    author = request.form.get("author")
    description = request.form.get("description")
    category = request.form.get("category")
    cad_subcategory = request.form.get("cadSubcategory")
    code_subcategory = request.form.get("codeSubcategory")

    if not team_number or not title or not category or not email:
        return render_template("ftc/contribute.html", error=True,
                               error_message={"error": "Missing required fields"}), 400

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
        "email": email,
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


if __name__ == '__main__':
    app.run(debug=True)
