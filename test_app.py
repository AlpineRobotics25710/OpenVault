"""Run: python -m unittest -v   (GitHub is mocked; no network needed)"""
import io
import unittest
from unittest import mock

import util
from app import app
from search import search

TREE = {"tree": [
    {"path": "ftc/cad/drivetrains/good-post/info.json"},
    {"path": "ftc/cad/drivetrains/good-post/preview.png"},
    {"path": "ftc/cad/drivetrains/broken-post/info.json"},
    {"path": "ftc/cad/drivetrains/no-info-post/preview.png"},  # no info.json: never fetched
    {"path": "ftc/cad/drivetrains/filler/info.json"},
    {"path": "ftc/code/teleop/other-post/info.json"},
]}
GOOD_INFO = {
    "title": "Mecanum Drivetrain",
    "author": "Alpine",
    "description": "Fast and smooth",
    "team-number": "25710",
    "preview-image-name": "preview.png",
    "seasons-used": ["2024-2025"],
    "used-in-comp": True,
    "onshape-link": "https://cad.onshape.com/x",
    "timestamp": "2025-01-02 03:04:05",
}


def fake_response(json_data=None, status=200):
    resp = mock.Mock(status_code=status, ok=status < 400, text="")
    resp.json.return_value = json_data
    if status >= 400:
        resp.raise_for_status.side_effect = util.requests.HTTPError(response=resp)
    return resp


def fake_github_get(url, **kwargs):
    if url == util.TREE_URL:
        return fake_response(TREE)
    if url.endswith("good-post/info.json"):
        return fake_response(GOOD_INFO)
    if url.endswith("broken-post/info.json"):
        return fake_response({"author": "no title"})  # missing required "title"
    raise AssertionError(f"unexpected URL {url}")


class SiteTests(unittest.TestCase):
    def setUp(self):
        util._cache.clear()
        util._folders = None
        self.client = app.test_client()

    def test_unknown_category_is_404_without_calling_github(self):
        with mock.patch("util.requests.get") as get:
            self.assertEqual(self.client.get("/foo/bar").status_code, 404)
            self.assertEqual(self.client.get("/cad/not-a-category").status_code, 404)
            get.assert_not_called()

    def test_bad_info_json_is_skipped_not_fatal(self):
        with mock.patch("util.requests.get", side_effect=fake_github_get):
            resp = self.client.get("/cad/drivetrains")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Mecanum Drivetrain", html)
        self.assertIn("01/02/2025", html)
        self.assertNotIn("no title", html)

    def test_github_failure_shows_error_on_every_section(self):
        with mock.patch("util.requests.get", return_value=fake_response({}, status=403)):
            for path in ["/cad/drivetrains", "/code/teleop", "/portfolios/portfolios"]:
                html = self.client.get(path).get_data(as_text=True)
                self.assertIn("rate limit reached", html, path)

    def test_listing_failure_serves_last_good_listing(self):
        with mock.patch("util.requests.get", side_effect=fake_github_get):
            self.client.get("/cad/drivetrains")
        util._cache.clear()  # records expired
        util._folders = (util._folders[0] - util.CACHE_TTL - 1, util._folders[1])  # listing expired

        def rate_limited(url, **kwargs):
            if url == util.TREE_URL:
                return fake_response({}, status=403)
            return fake_github_get(url)

        with mock.patch("util.requests.get", side_effect=rate_limited):
            html = self.client.get("/cad/drivetrains").get_data(as_text=True)
        self.assertIn("Mecanum Drivetrain", html)
        self.assertNotIn("Error:", html)

    def test_rejected_token_falls_back_to_unauthenticated(self):
        def get(url, headers=None, **kwargs):
            if headers:
                return fake_response({}, status=401)
            return fake_github_get(url)

        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "expired"}), \
                mock.patch("util.requests.get", side_effect=get):
            html = self.client.get("/cad/drivetrains").get_data(as_text=True)
        self.assertIn("Mecanum Drivetrain", html)

    def test_nav_lists_every_category(self):
        html = self.client.get("/").get_data(as_text=True)
        for section, cats in util.CATEGORIES.items():
            for slug in cats:
                self.assertIn(f'href="/{section}/{slug}"', html)

    def test_search_api_filters_posts(self):
        with mock.patch("util.requests.get", side_effect=fake_github_get):
            hit = self.client.post(
                "/api/search", json={"query": "mecanum", "base": "cad", "category": "drivetrains"}
            ).get_json()["html"]
            miss = self.client.post(
                "/api/search", json={"query": "zzz", "base": "cad", "category": "drivetrains"}
            ).get_json()["html"]
        self.assertIn("Mecanum Drivetrain", hit)
        self.assertIn("No Results Found", miss)

    def test_search_api_rejects_unknown_category(self):
        resp = self.client.post("/api/search", json={"query": "x", "base": "../", "category": "x"})
        self.assertEqual(resp.status_code, 404)

    def test_season_normalization(self):
        n = util.normalize_season
        self.assertEqual(n("2024-25"), "2024-2025")
        self.assertEqual(n(" 2024 - 2025 "), "2024-2025")
        for junk in ["N/A", "1", "2025", "2023-2025", "2024 onwards (2 seasons)", "1999-2000"]:
            self.assertIsNone(n(junk), junk)

    def test_season_filters_only_when_useful(self):
        post = lambda *s: {"seasons_used": list(s)}  # noqa: E731
        # every post in one season: filtering narrows nothing
        self.assertEqual(util.season_filters([post("2024-2025"), post("2024-2025")]), [])
        self.assertEqual(util.season_filters([post(), post()]), [])
        self.assertEqual(util.season_filters({"error": "x"}), [])
        self.assertEqual(
            util.season_filters([post("2023-2024"), post("2024-2025", "2023-2024"), post()]),
            [("2024-2025", "INTO THE DEEP", 1), ("2023-2024", "CENTERSTAGE", 2)],
        )

    def test_search_matches_team_number_and_tags(self):
        records = [
            {"title": "Drive", "team_number": 25710},
            {"title": "Claw", "tags": ["dr4b"]},
        ]
        self.assertEqual([r["title"] for r in search("25710", records)], ["Drive"])
        self.assertEqual([r["title"] for r in search("dr4b", records)], ["Claw"])


class SubmitTests(unittest.TestCase):
    FORM = {
        "email": "a@b.c",
        "teamNumber": "25710",
        "title": "My Claw: v2?",
        "author": "Alpine",
        "description": "desc",
        "category": "CAD",
        "cadSubcategory": "claws",
        "onshapeLink": "https://cad.onshape.com/x",
        "tags": '["dr4b"]',
    }

    def setUp(self):
        self.client = app.test_client()

    def submit(self, form, request_side_effect):
        with mock.patch("contribute.requests.request", side_effect=request_side_effect) as req:
            data = dict(form, previewImage=(io.BytesIO(b"img"), "../../evil name.png"))
            resp = self.client.post("/submit-pr", data=data, content_type="multipart/form-data")
        return resp, req

    def test_successful_submission(self):
        calls = []

        def ok(method, url, **kwargs):
            calls.append((method, url, kwargs.get("json")))
            return fake_response({"object": {"sha": "abc"}}, status=201)

        resp, _ = self.submit(self.FORM, ok)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Your Submission Has Been Recorded", resp.get_data(as_text=True))
        branch_ref = calls[1][2]["ref"]
        self.assertRegex(branch_ref, r"^refs/heads/25710-My_Claw_v2-[0-9a-f]{6}$")
        put_urls = [url for method, url, _ in calls if method == "PUT"]
        self.assertTrue(all("/ftc/cad/claws/" in u for u in put_urls))
        self.assertTrue(any(u.endswith("/evil_name.png") for u in put_urls))  # sanitized
        info_put = next(j for m, u, j in calls if m == "PUT" and u.endswith("info.json"))
        self.assertNotIn("a@b.c", str(info_put))  # email never goes to the public repo

    def test_failed_pr_shows_error_not_success(self):
        def pr_fails(method, url, **kwargs):
            if url.endswith("/pulls"):
                return fake_response({"message": "nope"}, status=422)
            return fake_response({"object": {"sha": "abc"}}, status=201)

        resp, _ = self.submit(self.FORM, pr_fails)
        self.assertEqual(resp.status_code, 400)
        self.assertNotIn("Your Submission Has Been Recorded", resp.get_data(as_text=True))

    def test_non_https_links_rejected_before_github(self):
        for link in ["javascript:alert(1)", "http://cad.onshape.com/x", "https://evil.com/x"]:
            resp, req = self.submit(dict(self.FORM, onshapeLink=link), None)
            self.assertEqual(resp.status_code, 400, link)
            req.assert_not_called()
        code_form = dict(self.FORM, category="Code", codeSubcategory="teleop",
                         codeSource="github", githubLink="javascript:alert(1)")
        resp, req = self.submit(code_form, None)
        self.assertEqual(resp.status_code, 400)
        req.assert_not_called()

    def test_existing_bad_links_not_rendered(self):
        self.assertEqual(util.safe_url("javascript:alert(1)"), "")
        self.assertEqual(util.safe_url(" JavaScript:alert(1)"), "")
        self.assertEqual(util.safe_url("data:text/html,x"), "")
        self.assertEqual(util.safe_url("https://cad.onshape.com/d/1"), "https://cad.onshape.com/d/1")
        gh = {"github.com"}
        # browsers treat "\" as "/", so the raw string would navigate to evil.com
        self.assertEqual(util.safe_url("https://evil.com\\@github.com/x", gh), "https://github.com/x")
        self.assertEqual(util.safe_url("https://user:pw@github.com/x", gh), "https://github.com/x")
        self.assertEqual(util.safe_url("https://github.com:99999/x", gh), "")
        self.assertEqual(util.safe_url("https://github.com.evil.com/x", gh), "")

    def test_invalid_subcategory_rejected_before_github(self):
        resp, req = self.submit(dict(self.FORM, cadSubcategory="nope"), None)
        self.assertEqual(resp.status_code, 400)
        req.assert_not_called()


if __name__ == "__main__":
    unittest.main()
