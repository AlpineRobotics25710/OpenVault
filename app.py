import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import uuid

app = Flask(__name__)

records = []
curr_template = ""


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    # print(request.endpoint)
    return {'active_route': request.endpoint}


# Function to fetch data from the database
def fetch_cad_data_from_github(section, sub_section):
    global records
    github_page = requests.get(f"https://github.com/AlpineRobotics25710/OpenVaultFiles/tree/main/ftc/{section}/{sub_section}")
    records = []
    if github_page.status_code == 200:
        soup = BeautifulSoup(github_page.content, "html.parser")
        unique_titles = set()
        links = []

        for subfolder in soup.find_all("a", class_="Link--primary"):
            title = subfolder.get("title")
            if title not in unique_titles:
                unique_titles.add(title)
                links.append(subfolder)

        #print(links)

        for subfolder in links:
            post_info = requests.get(f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/info.json")
            if post_info.status_code == 200:
                post_info_json = post_info.json()
                records.append(
                    {
                        "uuid": uuid.uuid4().__str__(),
                        "preview_image_url": f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['preview-image-name']}",
                        "title": post_info_json["title"],
                        "author": post_info_json["author"],
                        "description": post_info_json["description"],
                        "used_in_comp": post_info_json["used-in-comp"],
                        "team_number": post_info_json["team-number"],
                        "years_used": post_info_json["years-used"],
                        "onshape_link": post_info_json["onshape-link"]
                    }
                )

    return records

# Function to fetch data from the database
def fetch_code_data_from_github(section, sub_section):
    global records
    github_page = requests.get(f"https://github.com/AlpineRobotics25710/OpenVaultFiles/tree/main/ftc/{section}/{sub_section}")
    records = []
    if github_page.status_code == 200:
        soup = BeautifulSoup(github_page.content, "html.parser")
        unique_titles = set()
        links = []

        for subfolder in soup.find_all("a", class_="Link--primary"):
            title = subfolder.get("title")
            if title not in unique_titles:
                unique_titles.add(title)
                links.append(subfolder)

        #print(links)

        for subfolder in links:
            post_info = requests.get(f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/info.json")
            if post_info.status_code == 200:
                post_info_json = post_info.json()
                records.append(
                    {
                        "uuid": uuid.uuid4().__str__(),
                        "preview_image_url": f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['preview-image-name']}",
                        "download_url": f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['download-name']}",
                        "title": post_info_json["title"],
                        "author": post_info_json["author"],
                        "description": post_info_json["description"],
                        "used_in_comp": post_info_json["used-in-comp"],
                        "team_number": post_info_json["team-number"],
                        "years_used": post_info_json["years-used"],
                        "language": post_info_json["language"]
                    }
                )

    return records


# Function to fetch data from the database
def fetch_portfolios_data_from_github(section, sub_section):
    global records
    github_page = requests.get(f"https://github.com/AlpineRobotics25710/OpenVaultFiles/tree/main/ftc/{section}/{sub_section}")
    records = []
    if github_page.status_code == 200:
        soup = BeautifulSoup(github_page.content, "html.parser")
        unique_titles = set()
        links = []

        for subfolder in soup.find_all("a", class_="Link--primary"):
            title = subfolder.get("title")
            if title not in unique_titles:
                unique_titles.add(title)
                links.append(subfolder)

        #print(links)

        for subfolder in links:
            post_info = requests.get(f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/info.json")
            if post_info.status_code == 200:
                post_info_json = post_info.json()
                records.append(
                    {
                        "uuid": uuid.uuid4().__str__(),
                        "preview_image_url": f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['preview-image-name']}",
                        "download_url": f"https://raw.githubusercontent.com/AlpineRobotics25710/OpenVaultFiles/refs/heads/main/ftc/{section}/{sub_section}/{subfolder.get('title')}/{post_info_json['file-name']}",
                        "title": post_info_json["title"],
                        "author": post_info_json["author"],
                        "description": post_info_json["description"],
                        "team_number": post_info_json["team-number"],
                        "years_used": post_info_json["years-used"],
                        "awards_won": post_info_json["awards-won"]
                    }
                )

    return records


@app.route('/search', methods=["GET", "POST"])
def search():
    global records, curr_template
    if request.method == "POST":
        search_query = request.form.get("searchBox")
        if search_query == "":
            return render_template(curr_template, records=records)
        if search_query:
            search_query = search_query.lower()
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
    return render_template("ftc/index.html")


#      **CAD section**

@app.route('/cad/active-intakes')
def cad_active_intakes_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "active_intakes")
    curr_template = "ftc/cad/active-intakes.html"
    return render_template("ftc/cad/active-intakes.html", records=records)


@app.route('/cad/arms')
def cad_arms_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "arms")
    curr_template = "ftc/cad/arms.html"
    return render_template("ftc/cad/arms.html", records=records)


@app.route('/cad/dead-wheels')
def cad_dead_wheels_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "dead-wheels")
    curr_template = "ftc/cad/dead-wheels.html"
    return render_template("ftc/cad/dead-wheels.html", records=records)


@app.route('/cad/drivetrains/', methods=['POST', 'GET'])
def cad_drivetrains_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "drivetrains")
    curr_template = "ftc/cad/drivetrains.html"
    return render_template("ftc/cad/drivetrains.html", records=records)


@app.route('/cad/linear-motion-guides')
def cad_linear_motions_guides_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "linear-motion-guides")
    curr_template = "ftc/cad/linear-motions-guides.html"
    return render_template("ftc/cad/linear-motions-guides.html", records=records)


@app.route('/cad/linkages')
def cad_linkages_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "linkages")
    curr_template = "ftc/cad/linkages.html"
    return render_template("ftc/cad/linkages.html", records=records)


@app.route('/cad/outtakes')
def cad_outtakes_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "outtakes")
    curr_template = "ftc/cad/outtakes.html"
    return render_template("ftc/cad/outtakes.html", records=records)


@app.route('/cad/passive-intakes')
def cad_passive_intakes_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "passive-intakes")
    curr_template = "ftc/cad/passive-intakes.html"
    return render_template("ftc/cad/passive-intakes.html", records=records)


@app.route('/cad/power-transmissions')
def cad_power_transmissions_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "power-transmissions")
    curr_template = "ftc/cad/power-transmissions.html"
    return render_template("ftc/cad/power-transmissions.html", records=records)


@app.route('/cad/transfers')
def cad_transfers_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "transfers")
    curr_template = "ftc/cad/transfers.html"
    return render_template("ftc/cad/transfers.html", records=records)


@app.route('/cad/turrets')
def cad_turrets_page():
    global records, curr_template
    records = fetch_cad_data_from_github("cad", "turrets")
    curr_template = "ftc/cad/turrets.html"
    return render_template("ftc/cad/turrets.html", records=records)


#      **Code section**

@app.route('/code/driver-enhancements')
def code_driver_enhancements_page():
    global records, curr_template
    records = fetch_code_data_from_github("code", "driver-enhancements")
    curr_template = "ftc/code/driver-enhancements.html"
    return render_template("ftc/code/driver-enhancements.html", records=records)


@app.route('/code/ftclib')
def code_ftclib_page():
    global records, curr_template
    records = fetch_code_data_from_github("code", "ftc-lib")
    curr_template = "ftc/code/ftc-lib.html"
    return render_template("ftc/code/ftc-lib.html", records=records)


@app.route('/code/gamepad')
def code_auton_page():
    global records, curr_template
    records = fetch_code_data_from_github("code", "gamepad")
    curr_template = "ftc/code/gamepad.html"
    return render_template("ftc/code/gamepad.html", records=records)


@app.route('/code/pedro-pathing')
def code_pedro_pathing_page():
    global records, curr_template
    records = fetch_code_data_from_github("code", "pedro-pathing")
    curr_template = "ftc/code/pedro-pathing.html"
    return render_template("ftc/code/pedro-pathing.html", records=records)


@app.route('/code/road-runner')
def code_road_runner_page():
    global records, curr_template
    records = fetch_code_data_from_github("code", "road-runner")
    curr_template = "ftc/code/road-runner.html"
    return render_template("ftc/code/road-runner.html", records=records)


@app.route('/portfolios')
def portfolios():
    global records, curr_template
    records = fetch_portfolios_data_from_github("portfolios", "portfolios")
    curr_template = "ftc/portfolios/portfolios.html"
    return render_template("ftc/portfolios/portfolios.html", records=records)


if __name__ == '__main__':
    app.run(debug=True)
