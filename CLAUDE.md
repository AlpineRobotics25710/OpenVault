# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

OpenVault: Flask site (FTC Team 25710 Alpine Robotics) for browsing open-source FTC CAD, code, and portfolios. This repo holds **no content** — all posts live in the separate public GitHub repo `AlpineRobotics25710/OpenVaultFiles` and are fetched live. Deployed on Vercel (`vercel.json` routes everything to `app.py` via `@vercel/python`).

## Commands

```bash
pip install -r requirements.txt
python app.py                                  # dev server, debug=True, http://127.0.0.1:5000
python -m unittest -v                          # all tests (GitHub mocked, no network)
python -m unittest test_app.SubmitTests        # one class; append .test_name for one test
```

No linter or build step. Frontend is plain Jinja + static CSS/JS (Bootstrap via CDN), no bundler.

Env (`.env`, python-dotenv): `GITHUB_TOKEN` — used for the authenticated listing call (5000 req/h vs 60/h per IP without it) and required for the contribute/PR flow and `migrate_info_files.py --push`. A rejected token (401) falls back to unauthenticated reads so browsing keeps working.

Content migration tool (see `MIGRATION_GUIDE.md`): `python migrate_info_files.py --transform=<name> [--generate | --push --branch=<b>]`. New transforms: `fn(data, file_info) -> dict | None`, register in `TRANSFORM_REGISTRY`.

## Architecture

**Registry** — `util.py` holds `SECTIONS`, `CATEGORIES` and `SEASON_NAMES`, the single source of truth. They are injected into every template (context processor in `app.py`) and drive: route validation (unknown section/category → 404 before any GitHub call), the navbar, the contribute form's subcategory dropdowns and season checkboxes, the season filter tabs, and server-side submission validation. Adding a category or season = edit `util.py` (plus the matching folder in OpenVaultFiles). Nothing else.

**Read path** — `/<base>/<category>` renders `templates/ftc/category.html`, which includes `templates/ftc/posts.html` (cards + detail modals, branching on `base` for section-specific fields). `util.fetch_data_from_github` gets post folders from ONE git-trees API call for the whole repo (only folders containing an `info.json` count). That call is cached for `CACHE_TTL` (5 min), and the last good listing keeps being served if GitHub fails or rate-limits. It then fetches each folder's `info.json` from raw.githubusercontent (not API rate-limited) in parallel. Records are also cached per category for `CACHE_TTL`. A malformed `info.json` (missing `title`, bad JSON) is logged and skipped. On listing failure it returns `{"error": msg}` instead of a list; `posts.html` checks `records is mapping`.

`info.json` uses kebab-case keys (`team-number`, `seasons-used`, `preview-image-name`, ...) mapped to snake_case records. Legacy `years-used` is still accepted. Seasons are free-text from contributors: `util.normalize_season` maps `2024-25`-style values to `2024-2025` and drops unknowns for filtering (`seasons_used`), while `seasons_display` keeps the original text. The season filter (`util.season_filters`) shows only seasons present in the category, with counts, and is hidden when it wouldn't narrow anything. Record `id` is the folder name; modal DOM ids are `post-<index>`.

**Search** — stateless. `static/javascript/search.js` POSTs `{query, base, category}` (from `#searchForm` data attributes) to `/api/search`. That endpoint reuses the cached records, filters them with `search.search()` (Whoosh, in-memory index rebuilt per query) and returns `{"html": <rendered posts.html>}` for `#posts-div`. It then dispatches a `posts-updated` event that `season-filter.js` listens to. `modal-navigation.js` relies on each modal directly following its card column in the DOM, so it can skip season-filtered posts.

**Write path** — `/contribute` form → `/submit-pr` → `contribute.process_submit_pr`. It validates fields and the category against the registry, creates branch `<team>-<slug>-<random hex>` on OpenVaultFiles, uploads the preview and main file (names passed through `secure_filename`), writes `info.json`, and opens a PR. Every GitHub call goes through `github_call`, which raises `SubmissionError` on a non-2xx response, so any failure shows the error page. The contributor email is **never** written to the public repo or PR; it is only logged. Form field names (camelCase, e.g. `teamNumber`, `cadSubcategory`) are coupled to `contribute.html` and `contribute-script.js`. A new `info.json` field must be added in `contribute.build_info_json` (write), `util._load_record` (read), `posts.html` (display), and usually `search.py`.

Vercel caps request bodies at ~4.5 MB; `contribute-script.js` blocks submissions with more than 4 MB of files.
