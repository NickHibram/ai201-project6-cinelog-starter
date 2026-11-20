# PR Response Doc — CineLog Watchlist Feature

## AI Usage

**Instance 1 — deciding the watchlist visibility default**

- *What I gave the AI:* The reviewer's question about the existing public default, the context of CineLog as a community film app, and my position that privacy matters and users should explicitly choose to share.
- *What it produced:* A comparison of private and public defaults, suggested PR wording, and a check of the API that showed `public` is stored and returned while the list endpoint serves entries with either value.
- *What I changed or directed:* I chose `public: false` for new entries and asked the AI to implement and test that default. I kept my opt-in sharing rationale and used the AI critique to clarify that the flag records a visibility preference and that enforcing it would require requester identity and access checks.

## Comment 1 — Rename

Renamed the service definition in services/watchlist_service.py and both the import and add_film route call in routes/watchlist/watchlist.py. Before editing, project-wide `rg -n 'save_to_watchlist|add_to_watchlist' .` found these three executable references and no watchlist tests. After editing, the same search restricted to `--glob '*.py'` found only the three new-name references; no obsolete executable references remain. Old names here describe historical work.

Verification: `.venv/bin/python -m pytest tests/ -v`, exit 0, 4 passed.

## Comment 2 — Deduplication

add_to_collection() validates the film first, then looks up CollectionEntry by both user_id and film_id using first(). A match raises AlreadyInCollectionError; it does not return or modify the existing entry. Successful additions commit and return the new entry.

The deduplication implementation was AI-assisted.

The analogous WatchlistEntry lookup raises AlreadyOnWatchlistError for the same user/film. Visibility and date_added remain unchanged. Other users can add that film. The route maps duplicates to JSON 409 and missing films to JSON 404, matching collection conventions.

Verification: an isolated in-memory check (`PYTHONPATH=. .venv/bin/python /tmp/cinelog_dedup_check.py`) passed duplicate exception, single-entry count, unchanged metadata, independent users, and HTTP 409/404 assertions (exit 0). `.venv/bin/python -m pytest tests/ -v`: exit 0, 4 passed. Dedicated committed edge tests follow separately.

## Comment 3 — Missing test

test_add_to_watchlist_nonexistent_film_raises in tests/test_watchlist.py follows test_add_to_collection_nonexistent_film_raises in tests/test_collection.py. It reuses the isolated in-memory app and sample_user fixtures and pytest.raises(FilmNotFoundError), passes the absent well-formed UUID 00000000-0000-0000-0000-000000000000, and asserts no watchlist entry was created. No existing tests were overwritten.

`.venv/bin/python -m pytest tests/test_watchlist.py -v`: exit 0, 1 passed. `.venv/bin/python -m pytest tests/ -v`: exit 0, 5 passed. These are pre-rebase results; UUID compatibility will be verified again after the real rebase.

## Comment 4 — Default visibility

I chose `public: false` for new watchlist entries. CineLog is a community app where users log watched films, rate them, and build collections. Saving a film for later can also be a personal planning task, so a save should record a private preference unless the user chooses to share. A public default would make it easier to discover films through other people's lists. I prefer opt-in sharing because it gives people a choice about whether a new save is marked public.

AI critique helped distinguish the stored preference from access control. The model now defaults new entries to false, and `POST /watchlist/<user_id>/add` inherits that default. `GET /watchlist/<user_id>` returns the saved flag and includes entries with either value. Enforcing visibility would require requester identity and access checks.

`test_watchlist_add_defaults_visibility_to_false` checks that POST returns 201 with `public: false` when the field is omitted and that GET returns the saved flag. The test initially failed because POST returned `true`. After the change, `.venv/bin/python -m pytest tests/test_watchlist.py -v` passed both tests and `.venv/bin/python -m pytest tests/ -v` passed all six tests, both with exit 0.

## Comment 5 — Sort order

Pending.

## Comment 6 — Rebase

Pending.

## Stretch Features

Pending.

## Commit History

Pending.

## PR Description

Pending.

## Baseline and source review

Original review: https://github.com/codepath/ai201-project6-cinelog-starter/pull/1 . All six comments retrieved, including inline and conversation comments. Read README.md, CONTRIBUTING.md, models, services, routes, and collection tests. Existing .gitignore preserved; added pytest cache exclusion. Existing .venv requirements are satisfied. `.venv/bin/python -m pytest tests/ -v`: exit 0, 4 passed. System python3 lacks pytest; use the project environment. No pre-existing test failures.
