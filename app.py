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


@app.route('/filter-code', methods=['POST', 'GET'])
def filter_code():
    if not records:
        return render_template(curr_template, record=records)
    year = request.form.get('selectedYear') if request.form.get('selectedYear') != "Any" else None
    used_in_comp = True if request.form.get('usedInComp') == "yes" else False if request.form.get(
        'usedInComp') == "no" else None
    team_number = request.form.get('selectedTeamNumber') if request.form.get('selectedTeamNumber') != "Any" else None
    language = request.form.get('selectedLanguage') if request.form.get('selectedLanguage') != "Any" else None
    filtered_records = get_filtered_code_records(year, used_in_comp, team_number, language)
    return render_template(curr_template, records=filtered_records)


def get_filtered_code_records(years_used=None, used_in_comp=None, team_number=None, language=None, ):
    new_records = []
    for record in records:
        append = True
        if years_used and years_used.lower() not in record["years_used"].lower():
            append = False
        if language and language.lower() not in record["language"].lower():
            append = False
        if used_in_comp is not None and used_in_comp != bool(record["used_in_comp"]):
            append = False
        if team_number:
            record_team_number = int(record["team_number"])
            match team_number:
                case "<500":
                    if record_team_number >= 500:
                        append = False
                case "500":
                    if record_team_number < 500 or record_team_number >= 1000:
                        append = False
                case "1000":
                    if record_team_number < 1000 or record_team_number >= 1500:
                        append = False
                case "1500":
                    if record_team_number < 1500 or record_team_number >= 2000:
                        append = False
                case "2000":
                    if record_team_number < 2000:
                        append = False
        if append:
            new_records.append(record)

    return new_records


@app.route('/filter-cad', methods=['POST', 'GET'])
def filter_cad():
    print(records)
    if not records:
        return render_template(curr_template, records=records)
    year = request.form.get('selectedYear') if request.form.get('selectedYear') != "Any" else None
    used_in_comp = True if request.form.get('usedInComp') == "yes" else False if request.form.get(
        'usedInComp') == "no" else None
    team_number = request.form.get('selectedTeamNumber') if request.form.get('selectedTeamNumber') != "Any" else None
    filtered_records = get_filtered_cad_records(year, used_in_comp, team_number)
    return render_template(curr_template, records=filtered_records)


def get_filtered_cad_records(years_used=None, used_in_comp=None, team_number=None):
    global records
    new_records = []
    for record in records:
        append = True
        if years_used and years_used.lower() not in record["years_used"].lower():
            append = False
        if used_in_comp is not None and used_in_comp != bool(record["used_in_comp"]):
            append = False
        if team_number:
            record_team_number = int(record["team_number"])
            match team_number:
                case "<500":
                    if record_team_number >= 500:
                        append = False
                case "500":
                    if record_team_number < 500 or record_team_number >= 1000:
                        append = False
                case "1000":
                    if record_team_number< 1000 or record_team_number >= 1500:
                        append = False
                case "1500":
                    if record_team_number < 1500 or record_team_number >= 2000:
                        append = False
                case "2000":
                    if record_team_number < 2000:
                        append = False
        if append:
            new_records.append(record)

    return new_records


@app.route('/filter-portfolios', methods=['POST', 'GET'])
def filter_portfolios():
    if not records:
        return render_template(curr_template, records=records)
    year = request.form.get('selectedYear') if request.form.get('selectedYear') != "Any" else None
    team_number = request.form.get('selectedTeamNumber') if request.form.get('selectedTeamNumber') != "Any" else None
    awards_won = request.form.get('selectedAwardWon') if request.form.get('selectedAwardWon') != "Any" else None
    filtered_records = get_filtered_portfolios_records(year, awards_won, team_number)
    return render_template(curr_template, records=filtered_records)


def get_filtered_portfolios_records(years_used=None, awards_won=None, team_number=None):
    new_records = []
    for record in records:
        append = True
        if years_used and years_used.lower() not in record["years_used"].lower():
            append = False
        if awards_won and awards_won.lower() not in record["awards_won"].lower():
            append = False
        if team_number:
            record_team_number = int(record["team_number"])
            match team_number:
                case "<500":
                    if record_team_number >= 500:
                        append = False
                case "500":
                    if record_team_number < 500 or record_team_number >= 1000:
                        append = False
                case "1000":
                    if record_team_number < 1000 or record_team_number >= 1500:
                        append = False
                case "1500":
                    if record_team_number < 1500 or record_team_number >= 2000:
                        append = False
                case "2000":
                    if record_team_number < 2000:
                        append = False
        if append:
            new_records.append(record)

    return new_records


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


@app.route('/cad/drivetrains/')
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
