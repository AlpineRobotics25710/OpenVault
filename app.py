import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from github import Auth
from github import Github
from sklearn.feature_extraction.text import TfidfVectorizer

from contribute import submit_pr
from util import fetch_data_from_github, build_index, search

# TODO: Add filters
# TODO: Record the date posted and sort posts by date

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
github = Github(auth=auth)

reduced_vectors = None
tfidf_vectorizer = TfidfVectorizer()
svd_model = None


@app.context_processor
def inject_active_route():
    # Provide the current route name to all templates
    # print(session["curr_template"])
    return {'active_route': session["curr_template"]}


@app.route('/')
def index():
    session["curr_template"] = "ftc/index.html"
    return render_template("ftc/index.html")


@app.route('/contribute')
def contribute():
    session["curr_template"] = "ftc/contribute.html"
    return render_template("ftc/contribute.html", submitted=False)


@app.route('/<base>/<category>')
def render_page(base, category):
    records = fetch_data_from_github(base, category)
    session["records"] = records
    session["curr_template"] = f"ftc/{base}/{category}.html"
    print("records: ", len(records))

    if records:
        global tfidf_vectorizer, svd_model, reduced_vectors
        tfidf_vectorizer, svd_model, reduced_vectors = build_index(records, min(len(records), 100))

    return render_template(session["curr_template"], records=records)



# For legacy purposes/ease of use. You can access portfolios through /portfolios/portfolios
@app.route('/portfolios')
def portfolios():
    return redirect(url_for("render_page", base="portfolios", category="portfolios"))


@app.route('/api/search', methods=["GET", "POST", "FETCH"])
def search_api():
    global tfidf_vectorizer, svd_model, reduced_vectors

    if request.method == "GET":
        return jsonify({"error": "Cannot access this endpoint through \"GET\""}), 403

    if "records" not in session:
        return jsonify({"error": "No records in session"}), 400

    records = session.get("records")
    search_query = request.json.get("query", "").strip()

    #print("reduced vectors:", reduced_vectors)
    #print("svd_model:", svd_model)
    #print("tfidf_vectorizer:", tfidf_vectorizer)
    #print("search query:", search_query)

    if not search_query or reduced_vectors is None:
        return jsonify({"records": records})

    similarities, _ = search(search_query, tfidf_vectorizer, svd_model, reduced_vectors)
    #print("similarities:", similarities)

    # Filter based on similarity threshold
    threshold = 0.3
    filtered = [(i, sim) for i, sim in enumerate(similarities) if sim >= threshold]
    filtered = sorted(filtered, key=lambda x: x[1], reverse=True)
    filtered_records = [records[i] for i, _ in filtered]

    rendered_template = render_template(session.get("curr_template"), records=filtered_records)

    return jsonify({"template": rendered_template})


@app.route("/submit-pr", methods=["POST"])
def submit_pr():
    """Handles form submission and creates a PR."""
    session["curr_template"] = "ftc/contribute.html"
    return submit_pr(request)


if __name__ == '__main__':
    app.run(debug=True)
