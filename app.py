from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("ftc/index.html")

#      **CAD section**

@app.route('/cad/drivetrains')
def cad_slides_page():
    return render_template("ftc/cad/drivetrains.html")

@app.route('/cad/passiveIntakes')
def cad_intake_page():
    return render_template("ftc/cad/passiveIntakes.html")

@app.route('/cad/activeIntakes')
def cad_claw_page():
    return render_template("ftc/cad/activeIntakes.html")

@app.route('/cad/transfers')
def cad_slides_page():
    return render_template("ftc/cad/drivetrains.html")

@app.route('/cad/outtakes')
def cad_outtake_page():
    return render_template("ftc/cad/outtakes.html")

@app.route('/cad/arms')
def cad_slides_page():
    return render_template("ftc/cad/arms.html")

@app.route('/cad/linearMotionGuides')
def cad_slides_page():
    return render_template("ftc/cad/linearMotionGuides.html")

@app.route('/cad/deadWheels')
def cad_slides_page():
    return render_template("ftc/cad/deadWheels.html")

@app.route('/cad/linkages')
def cad_slides_page():
    return render_template("ftc/cad/linkages.html")

@app.route('/cad/powerTransmissions')
def cad_slides_page():
    return render_template("ftc/cad/powerTransmissions.html")

@app.route('/cad/turrets')
def cad_slides_page():
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

