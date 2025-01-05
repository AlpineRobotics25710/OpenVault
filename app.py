from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("ftc/index.html")

@app.route('/cad/intake')
def cad_intake_page():
    return render_template("ftc/cad/intake.html")

@app.route('/cad/outtake')
def cad_outtake_page():
    return render_template("ftc/cad/outtake.html")

@app.route('/cad/claw')
def cad_claw_page():
    return render_template("ftc/cad/claw.html")

@app.route('/cad/slides')
def cad_slides_page():
    return render_template("ftc/cad/slides.html")

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

