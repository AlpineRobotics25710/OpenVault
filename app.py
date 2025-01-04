from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/cad')
def cad():
    return render_template("cad.html")

@app.route('/code')
def code():
    return render_template("code.html")

@app.route('/portfolios')
def portfolios():
    return render_template("portfolios.html")


if __name__ == '__main__':
    app.run(debug=True)

