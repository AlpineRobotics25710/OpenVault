import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, session, jsonify, redirect

from contribute import process_submit_pr
from search import build_index, search
from util import fetch_data_from_github

# TODO: Add filters
# TODO: OpenVault API for developers?

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    # print(session["curr_template"])
    return {"active_route": session["curr_template"]}


@app.route("/")
def index():
    session["curr_template"] = "ftc/index.html"
    return render_template("ftc/index.html")


@app.route("/contribute")
def contribute():
    session["curr_template"] = "ftc/contribute.html"
    return render_template("ftc/contribute.html", submitted=False)


@app.route("/<base>/<category>")
def render_page(base, category):
    records = fetch_data_from_github(base, category)
    session["records"] = records
    session["curr_template"] = f"ftc/{base}/{category}.html"

    return render_template(session["curr_template"], records=records)


# For legacy purposes/ease of use. You can access portfolios through /portfolios/portfolios
# Simply redirects to /portfolios/portfolios
@app.route("/portfolios")
def portfolios():
    session["curr_template"] = "ftc/portfolios/portfolios.html"
    return redirect(url_for("render_page", base="portfolios", category="portfolios"))


@app.route("/api/search", methods=["POST"])
def search_api():
    records = session.get("records")
    search_query = request.json.get("query", "").strip()
    curr_template = session.get("curr_template")

    if "records" not in session:
        return jsonify({"error": "No records in session"}), 400

    if not search_query:
        return jsonify({"template": render_template(curr_template, records=records)}), 200,

    # print(f"Search query: {search_query}")
    # print("tfidf_matrix:", tfidf_matrix)

    tfidf_matrix, idf, vocab, texts = build_index(records)

    if tfidf_matrix is None:
        return jsonify({"error": "tfidf matrix not present"}), 400

    similarities, _ = search(search_query, idf, vocab, tfidf_matrix)
    # print("Similarities:", similarities)

    threshold = 0.01
    filtered = [(i, sim) for i, sim in enumerate(similarities) if sim >= threshold]
    filtered = sorted(filtered, key=lambda x: x[1], reverse=True)
    filtered_records = [records[i] for i, _ in filtered]

    # print("Top Similarities:", sorted(similarities, reverse=True)[:5])
    # print("Filtered Indices:", [i for i, sim in filtered])

    rendered_template = render_template(curr_template, records=filtered_records)

    return jsonify({"template": rendered_template})


@app.route("/submit-pr", methods=["POST"])
def submit_pr():
    """Handles form submission and creates a PR."""
    session["curr_template"] = "ftc/contribute.html"
    return process_submit_pr(request)


if __name__ == "__main__":
    app.run(debug=True)
