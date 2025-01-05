from flask import Flask, render_template, request

app = Flask(__name__)


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    #print(request.endpoint)
    return {'active_route': request.endpoint}

@app.route('/')
def index():
    return render_template("ftc/index.html")

#      **CAD section**

@app.route('/cad/active-intakes')
def cad_active_intakes_page():
    return render_template("ftc/cad/active-intakes.html")

@app.route('/cad/arms')
def cad_arms_page():
    return render_template("ftc/cad/arms.html")

@app.route('/cad/dead-wheels')
def cad_dead_wheels_page():
    return render_template("ftc/cad/dead-wheels.html")

@app.route('/cad/drivetrains')
def cad_drivetrains_page():
    return render_template("ftc/cad/drivetrains.html")

@app.route('/cad/linear-motion-guides')
def cad_linear_motions_guides_page():
    return render_template("ftc/cad/linear-motions-guides.html")

@app.route('/cad/linkages')
def cad_linkages_page():
    return render_template("ftc/cad/linkages.html")

@app.route('/cad/outtakes')
def cad_outtakes_page():
    return render_template("ftc/cad/outtakes.html")

@app.route('/cad/passive-intakes')
def cad_passive_intakes_page():
    return render_template("ftc/cad/passive-intakes.html")

@app.route('/cad/power-transmissions')
def cad_power_transmissions_page():
    return render_template("ftc/cad/power-transmissions.html")

@app.route('/cad/transfers')
def cad_transfers_page():
    return render_template("ftc/cad/transfers.html")

@app.route('/cad/turrets')
def cad_turrets_page():
    return render_template("ftc/cad/turrets.html")

#      **Code section**

@app.route('/code/teleop')
def code_teleop_page():
    return render_template("ftc/code/teleop.html")

@app.route('/code/auton')
def code_auton_page():
    return render_template("ftc/code/auton.html")

@app.route('/code/ftclib')
def code_ftclib_page():
    return render_template("ftc/code/ftclib.html")

@app.route('/portfolios')
def portfolios():
    return render_template("ftc/portfolios/portfolios.html")


if __name__ == '__main__':
    app.run(debug=True)

