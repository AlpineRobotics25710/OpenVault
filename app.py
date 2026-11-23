from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

from contribute import process_submit_pr
from search import search
from util import CATEGORIES, SEASON_NAMES, SECTIONS, fetch_data_from_github, season_filters

load_dotenv()

app = Flask(__name__)

SUBTITLES = {
    "cad": "Find various 3D models that you can use yourself!",
    "code": "Find various open source code files that you can use yourself!",
    "portfolios": "Find various portfolios that you can take inspiration from!",
}


@app.context_processor
def inject_site_data():
    return {"SECTIONS": SECTIONS, "CATEGORIES": CATEGORIES, "SEASON_NAMES": SEASON_NAMES}


def check_category(base, category):
    if category not in CATEGORIES.get(base, {}):
        abort(404)


@app.route("/")
def index():
    return render_template("ftc/index.html")


@app.route("/contribute")
def contribute():
    return render_template("ftc/contribute.html", submitted=False)


@app.route("/<base>/<category>")
def render_page(base, category):
    check_category(base, category)
    records = fetch_data_from_github(base, category)
    return render_template(
        "ftc/category.html",
        base=base,
        category=category,
        title=CATEGORIES[base][category],
        subtitle=SUBTITLES[base],
        records=records,
        seasons=season_filters(records),
    )


# Legacy URL; portfolios live at /portfolios/portfolios
@app.route("/portfolios")
def portfolios():
    return redirect(url_for("render_page", base="portfolios", category="portfolios"))


@app.route("/api/search", methods=["POST"])
def search_api():
    body = request.get_json(silent=True) or {}
    base, category = body.get("base"), body.get("category")
    check_category(base, category)

    records = fetch_data_from_github(base, category)
    query = str(body.get("query", "")).strip()
    if query and isinstance(records, list):
        try:
            records = search(query, records)
        except Exception as e:
            print(f"Search error for {query!r}: {e!r}")  # fall back to showing all posts
    return jsonify({"html": render_template("ftc/posts.html", base=base, records=records)})


@app.route("/submit-pr", methods=["POST"])
def submit_pr():
    return process_submit_pr(request)


if __name__ == "__main__":
    app.run(debug=True)
