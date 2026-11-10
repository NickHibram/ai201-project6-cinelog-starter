# PR Response Doc — CineLog Watchlist Feature

## AI Usage

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

Pending.

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
