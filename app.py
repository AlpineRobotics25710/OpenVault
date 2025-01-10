import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

records = []
curr_template = ""


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    # print(request.endpoint)
    return {'active_route': request.endpoint}


# Function to fetch data from the database
def fetch_data_from_db(section, table_name):
    # Connect to the database
    connection = sqlite3.connect(f"static/databases/{section}.db")
    cursor = connection.cursor()

    # Fetch all rows from the active_intakes table
    cursor.execute(f"SELECT * FROM {table_name}")
    records = cursor.fetchall()
    connection.close()
    return records


@app.route('/filter-code', methods=['POST', 'GET'])
def filter_code():
    year = request.form.get('selectedYear') if request.form.get('selectedYear') != "Any" else None
    language = request.form.get('selectedLanguage') if request.form.get('selectedLanguage') != "Any" else None
    used_in_comp = True if request.form.get('usedInComp') == "yes" else False if request.form.get('usedInComp') == "no" else None
    print(used_in_comp)
    filtered_records = get_filtered_code_records(year, language, used_in_comp)
    return render_template(curr_template, records=filtered_records)


def get_filtered_code_records(years_used=None, language=None, used_in_comp=None):
    new_records = []
    for record in records:
        append = True
        if years_used and years_used.lower() not in record[8].lower():
            append = False
        if language and language.lower() not in record[6].lower():
            append = False
        if used_in_comp is not None and used_in_comp != record[7]:
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
    records = fetch_data_from_db("cad", "active_intakes")
    return render_template("ftc/cad/active-intakes.html", records=records)


@app.route('/cad/arms')
def cad_arms_page():
    records = fetch_data_from_db("cad", "arms")
    return render_template("ftc/cad/arms.html", records=records)


@app.route('/cad/dead-wheels')
def cad_dead_wheels_page():
    records = fetch_data_from_db("cad", "dead_wheels")
    return render_template("ftc/cad/dead-wheels.html", records=records)


@app.route('/cad/drivetrains/')
def cad_drivetrains_page():
    records = fetch_data_from_db("cad", "drivetrains")
    return render_template("ftc/cad/drivetrains.html", records=records)


@app.route('/cad/linear-motion-guides')
def cad_linear_motions_guides_page():
    records = fetch_data_from_db("cad", "linear_motion_guides")
    return render_template("ftc/cad/linear-motions-guides.html", records=records)


@app.route('/cad/linkages')
def cad_linkages_page():
    records = fetch_data_from_db("cad", "linkages")
    return render_template("ftc/cad/linkages.html", records=records)


@app.route('/cad/outtakes')
def cad_outtakes_page():
    records = fetch_data_from_db("cad", "outtakes")
    return render_template("ftc/cad/outtakes.html", records=records)


@app.route('/cad/passive-intakes')
def cad_passive_intakes_page():
    records = fetch_data_from_db("cad", "passive_intakes")
    return render_template("ftc/cad/passive-intakes.html", records=records)


@app.route('/cad/power-transmissions')
def cad_power_transmissions_page():
    records = fetch_data_from_db("cad", "power_transmissions")
    return render_template("ftc/cad/power-transmissions.html", records=records)


@app.route('/cad/transfers')
def cad_transfers_page():
    records = fetch_data_from_db("cad", "transfers")
    return render_template("ftc/cad/transfers.html", records=records)


@app.route('/cad/turrets')
def cad_turrets_page():
    records = fetch_data_from_db("cad", "turrets")
    return render_template("ftc/cad/turrets.html", records=records)


#      **Code section**

@app.route('/code/driver-enhancements')
def code_driver_enhancements_page():
    global records, curr_template
    records = fetch_data_from_db("code", "driver_enhancements")
    curr_template = "ftc/code/driver-enhancements.html"
    return render_template("ftc/code/driver-enhancements.html", records=records)


@app.route('/code/ftclib')
def code_ftclib_page():
    global records, curr_template
    records = fetch_data_from_db("code", "ftc_lib")
    curr_template = "ftc/code/ftc-lib.html"
    return render_template("ftc/code/ftc-lib.html", records=records)


@app.route('/code/gamepad')
def code_auton_page():
    records = fetch_data_from_db("code", "gamepad")
    return render_template("ftc/code/gamepad.html", records=records)


@app.route('/code/pedro-pathing')
def code_pedro_pathing_page():
    records = fetch_data_from_db("code", "pedro_pathing")
    return render_template("ftc/code/pedro-pathing.html", records=records)


@app.route('/code/road-runner')
def code_road_runner_page():
    records = fetch_data_from_db("code", "road_runner")
    return render_template("ftc/code/road-runner.html", records=records)


@app.route('/portfolios')
def portfolios():
    records = fetch_data_from_db("portfolios", "portfolios")
    return render_template("ftc/portfolios/portfolios.html", records=records)


if __name__ == '__main__':
    app.run(debug=True)
