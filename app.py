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
    session["base"] = base
    session["category"] = category

    return render_template(session["curr_template"], records=records)


# For legacy purposes/ease of use. You can access portfolios through /portfolios/portfolios
# Simply redirects to /portfolios/portfolios
@app.route("/portfolios")
def portfolios():
    session["curr_template"] = "ftc/portfolios/portfolios.html"
    return redirect(url_for("render_page", base="portfolios", category="portfolios"))


@app.route("/api/search", methods=["POST"])
def search_api():
    search_query = request.json.get("query", "").strip()
    curr_template = session.get("curr_template")
    base = session.get("base")
    category = session.get("category")

    # Always fetch fresh data for search to ensure we have the latest content
    if base and category:
        records = fetch_data_from_github(base, category)
        # Update session with fresh data
        session["records"] = records
    else:
        records = session.get("records")

    if not records:
        return jsonify({"error": "No records available"}), 400

    if not search_query:
        return (
            jsonify({"template": render_template(curr_template, records=records)}),
            200,
        )

    try:
        # Use new Whoosh-based search
        similarities, ranked_indices = search(search_query, records=records)

        # Filter results with meaningful similarity scores
        threshold = 0.01
        filtered = [
            (ranked_indices[i], similarities[i])
            for i in range(len(similarities))
            if similarities[i] >= threshold
        ]

        # Sort by similarity score (already sorted by Whoosh, but ensuring order)
        filtered = sorted(filtered, key=lambda x: x[1], reverse=True)
        filtered_records = [records[i] for i, _ in filtered]

        rendered_template = render_template(curr_template, records=filtered_records)
        return jsonify({"template": rendered_template})

    except Exception as e:
        print(f"Search error: {e}")
        # Fallback to original records on error
        rendered_template = render_template(curr_template, records=records)
        return jsonify({"template": rendered_template})


@app.route("/api/refresh-search-index", methods=["POST"])
def refresh_search_index():
    """Manually refresh the search index with latest data from GitHub"""
    base = session.get("base")
    category = session.get("category")

    if not base or not category:
        return jsonify({"error": "No active category to refresh"}), 400

    try:
        # Fetch fresh data from GitHub
        records = fetch_data_from_github(base, category)
        session["records"] = records

        # Force rebuild of search index by clearing the hash
        from search import force_index_rebuild

        force_index_rebuild()

        return jsonify(
            {
                "success": True,
                "message": f"Search index refreshed with {len(records)} records",
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to refresh search index: {str(e)}"}), 500


@app.route("/api/search-stats", methods=["GET"])
def search_stats():
    """Get statistics about the current search index"""
    records = session.get("records", [])

    try:
        from search import get_search_stats

        stats = get_search_stats(records)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/submit-pr", methods=["POST"])
def submit_pr():
    """Handles form submission and creates a PR."""
    session["curr_template"] = "ftc/contribute.html"
    return process_submit_pr(request)


if __name__ == "__main__":
    app.run(debug=True)
