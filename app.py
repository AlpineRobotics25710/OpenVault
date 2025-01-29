import requests
from flask import Flask, render_template, request, session
from bs4 import BeautifulSoup
import uuid

app = Flask(__name__)
app.secret_key = "779650ac697181207529db19091dc55b93aa47a70ffbbe52d9cb8330c7b9ed4f"


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    #print(session["curr_template"])
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
                 subfolder.get("title") not in unique_titles and not unique_titles.add(subfolder.get("title"))]

        for subfolder in links:
            post_info = requests.get(f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/info.json")
            if post_info.status_code == 200:
                post_info_json = post_info.json()

                record = {
                    "uuid": str(uuid.uuid4()),
                    "preview_image_url": f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['preview-image-name']}",
                    "title": post_info_json["title"],
                    "author": post_info_json["author"],
                    "description": post_info_json["description"],
                    "team_number": post_info_json["team-number"],
                    "years_used": post_info_json["years-used"],
                }

                if section == "code":
                    record[
                        "download_url"] = f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['download-name']}"
                    record["language"] = post_info_json["language"]
                elif section == "portfolios":
                    record[
                        "download_url"] = f"{base_url}/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['file-name']}"
                    record["awards_won"] = post_info_json["awards-won"]
                elif section == "cad":
                    record["used_in_comp"] = post_info_json["used-in-comp"]
                    record["onshape_link"] = post_info_json["onshape-link"]

                session["records"].append(record)

    return session["records"]


@app.route('/search', methods=["GET", "POST"])
def search():
    if "curr_template" not in session:
        return index()

    if "records" not in session or session["records"] == []:
        return render_template(session["curr_template"], records=session["records"])

    curr_template = session["curr_template"]
    records = session["records"]
    #print("curr template:" + curr_template)
    #print("records:" + str(records))
    if request.method == "POST":
        search_query = request.form.get("searchBox")
        if search_query == "":
            return render_template(curr_template, records=records)
        if search_query:
            search_query = search_query.lower()
            #print("search query:" + search_query)
            #print(records)
            filtered_records = [
                record for record in records if
                search_query in record["title"].lower() or
                search_query in record["author"].lower() or
                search_query in record["description"].lower() or
                search_query in record["team_number"].lower() or
                search_query in record["years_used"].lower()
            ]
            return render_template(curr_template, records=filtered_records)

    return render_template(curr_template, records=records)


@app.route('/')
def index():
    session["curr_template"] = "ftc/index.html"
    return render_template("ftc/index.html")


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
