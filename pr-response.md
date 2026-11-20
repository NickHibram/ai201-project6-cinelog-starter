# PR Response Doc — CineLog Watchlist Feature

## AI Usage

**Instance 1 — deciding the watchlist visibility default**

- *What I gave the AI:* The reviewer's question about the existing public default, the context of CineLog as a community film app, and my position that privacy matters and users should explicitly choose to share.
- *What it produced:* A comparison of private and public defaults, suggested PR wording, and a check of the API that showed `public` is stored and returned while the list endpoint serves entries with either value.
- *What I changed or directed:* I chose `public: false` for new entries and asked the AI to implement and test that default. I kept my opt-in sharing rationale and used the AI critique to clarify that the flag records a visibility preference and that enforcing it would require requester identity and access checks.

**Instance 2 — deciding the watchlist sort order**

- *What I gave the AI:* My stack analogy and my goal of showing the films I added most recently at the top.
- *What it produced:* Feedback that the analogy describes last in, first out for display order, suggested PR wording, and a comparison with alphabetical browsing. It also suggested sorting by the watchlist entry's addition time with a stable tie-breaker.
- *What I changed or directed:* I confirmed newest-added first and asked the AI to implement it. I used the feedback to explain the choice in terms of finding a recent save and to acknowledge that alphabetical order helps when I already know the title.

## Comment 1 — Rename

Renamed the service definition in services/watchlist_service.py and both the import and add_film route call in routes/watchlist/watchlist.py. Before editing, project-wide `rg -n 'save_to_watchlist|add_to_watchlist' .` found these three executable references and no watchlist tests. After editing, the same search restricted to `--glob '*.py'` found only the three new-name references; no obsolete executable references remain. Old names here describe historical work.

Verification: `.venv/bin/python -m pytest tests/ -v`, exit 0, 4 passed.

## Comment 2 — Deduplication

add_to_collection() validates the film first, then looks up CollectionEntry by both user_id and film_id using first(). A match raises AlreadyInCollectionError; it does not return or modify the existing entry. Successful additions commit and return the new entry.

The deduplication implementation was AI-assisted.

The analogous WatchlistEntry lookup raises AlreadyOnWatchlistError for the same user/film. Visibility and date_added remain unchanged. Other users can add that film. The route maps duplicates to JSON 409 and missing films to JSON 404, matching collection conventions.

Verification: an isolated in-memory check passed duplicate exception, single-entry count, unchanged metadata, independent users, and HTTP 409/404 assertions. The full suite passed four tests at that stage. The final HTTP check also confirmed a duplicate returns 409 and leaves the original entry unchanged. The PR description below gives reproducible commands for that check.

## Comment 3 — Missing test

test_add_to_watchlist_nonexistent_film_raises in tests/test_watchlist.py follows test_add_to_collection_nonexistent_film_raises in tests/test_collection.py. It reuses the isolated in-memory app and sample_user fixtures and pytest.raises(FilmNotFoundError), passes the absent well-formed UUID 00000000-0000-0000-0000-000000000000, and asserts no watchlist entry was created. No existing tests were overwritten.

Before rebasing, the watchlist suite passed one test and the full suite passed five tests, both with exit 0. The same missing-film test passed again against the UUID schema in the final suite.

## Comment 4 — Default visibility

I chose `public: false` for new watchlist entries. CineLog is a community app where users log watched films, rate them, and build collections. Saving a film for later can also be a personal planning task, so a save should record a private preference unless the user chooses to share. A public default would make it easier to discover films through other people's lists. I prefer opt-in sharing because it gives people a choice about whether a new save is marked public.

AI critique helped distinguish the stored preference from access control. The model now defaults new entries to false, and `POST /watchlist/<user_id>/add` inherits that default. `GET /watchlist/<user_id>` returns the saved flag and includes entries with either value. Enforcing visibility would require requester identity and access checks.

`test_watchlist_add_defaults_visibility_to_false` checks that POST returns 201 with `public: false` when the field is omitted and that GET returns the saved flag. The test initially failed because POST returned `true`. After the change, `.venv/bin/python -m pytest tests/test_watchlist.py -v` passed both tests and `.venv/bin/python -m pytest tests/ -v` passed all six tests, both with exit 0.

## Comment 5 — Sort order

I chose newest-added first so that when someone saves a film recommendation and returns to CineLog, they can find that film at the top of the watchlist. This supports the maintainer's point about seeing recent additions. Alphabetical order helps when someone already remembers a title and wants to find it in a long list. I prioritized returning to a recent save as the default task.

`GET /watchlist/<user_id>` now orders by the watchlist entry's `date_added` descending, with entry ID ascending to break timestamp ties. AI critique helped turn my stack analogy into a precise display order and frame the argument around a concrete task without assuming how most users behave.

`test_watchlist_lists_newest_additions_first` checks the GET response using film titles, release years, and save dates that produce different orders. It also checks the timestamp tie-breaker. The test failed against the old alphabetical order. After the change, `.venv/bin/python -m pytest tests/test_watchlist.py -v` passed all three watchlist tests and `.venv/bin/python -m pytest tests/ -v` passed all seven tests, both with exit 0.

## Comment 6 — Rebase

I compared the upstream and fork `main` refs. Both pointed to `57ec3f9` (`refactor: migrate film IDs from integer to UUID`), so the fork needed no update. With a clean working tree, I fetched `origin`, saved `backup/watchlist-before-uuid-rebase` at `987c982`, and ran `git rebase origin/main`.

Only `models.py` conflicted, while replaying the inherited watchlist commit `9eafe68`. Its indexed watchlist film foreign key used an integer, while `main` used a UUID stored as `String(36)`. I kept the UUID type and the index on `WatchlistEntry.film_id`. `Film.id` and `CollectionEntry.film_id` use the same UUID representation from `main`. User IDs were already UUID strings. The service still looks up films with `db.session.get`, and the fixtures use the actual IDs generated by the model. The required missing-film service test still passes a well-formed UUID that is absent from the isolated test database.

The separate `fix: update watchlist film IDs to UUID format after main refactor` commit updates the add endpoint to parse UUID strings and pass their canonical form to the service. An uppercase UUID for an existing film succeeds and returns the stored UUID. An integer or malformed string returns JSON 400. A well-formed but absent UUID still returns JSON 404. The endpoint example and service docstring now describe UUIDs.

After rebasing, the existing full suite passed all seven tests. After the endpoint update, `.venv/bin/python -m pytest tests/test_watchlist.py -v` passed seven tests and `.venv/bin/python -m pytest tests/ -v` passed eleven, both with exit 0. `git merge-base --is-ancestor origin/main HEAD` returned 0, and `git ls-files -u` listed no unresolved conflicts.

## Stretch Features

Deferred by choice. Removal, an additional committed duplicate test, and accepting an explicit `public` value on the add endpoint are outside this submission. The required deduplication behavior was verified over HTTP.

## Commit History

I reviewed the diffs for the entire feature range and ran `git rebase -i origin/main`. The inherited watchlist introduction now has a `feat:` subject and includes the working blueprint import. The following lookup fix contains only the session-based film lookup changes. The ignore rules and baseline notes have distinct commits. The rename, deduplication, missing-film test, visibility default, sorting, and UUID compatibility changes retain their separate commits.

The feature history follows [CONTRIBUTING.md](CONTRIBUTING.md) and the [Conventional Commits format](https://www.conventionalcommits.org/en/v1.0.0/). `git merge-base --is-ancestor origin/main HEAD` returned 0. `git rev-list --merges origin/main..HEAD` and `git ls-files -u` printed nothing. `git diff --check origin/main..HEAD` passed. The code and tests match the pre-cleanup backup. The inherited `refactor:` commit is on `main`, outside the feature-only range.

<!-- screenshot:pending -->

## PR Description

### Add and review saved films in CineLog

CineLog users can save films they intend to watch and list their saved films by most recent addition. The add endpoint uses film UUIDs, reports missing films, and rejects a repeated save for the same user and film without changing the original entry.

- **Default visibility.** New entries store `public: false` because saving a film can be a personal planning task. The flag records a visibility preference. The prototype list endpoint returns entries with either value and does not enforce access control.
- **Default order.** The newest additions appear first so returning users can quickly find a recommendation they recently saved. Entries saved at the same timestamp are ordered by entry ID.

### Manual API checks

1. In the repository root, create or activate a virtual environment, install the requirements, and start Flask with a disposable SQLite database. `seed.py` inserts the demo `User` and catalog `Film` rows using the current schema. Copy the demo user UUID it prints. Keep this terminal running during the checks.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   cinelog_review_dir=$(mktemp -d /tmp/cinelog-review.XXXXXX)
   export DATABASE_URL="sqlite:///$cinelog_review_dir/cinelog.db"
   python seed.py
   python -m flask --app app:create_app run --host 127.0.0.1 --port 5056
   ```

2. In a second terminal, list the films. Use the `id` values from the `Alien` and `The Godfather` rows, and the user UUID printed by the seed command.

   ```bash
   base=http://127.0.0.1:5056
   curl -sS "$base/films/" | python3 -m json.tool

   user_id='<demo user UUID>'
   alien_id='<Alien film UUID>'
   godfather_id='<The Godfather film UUID>'
   watchlist="$base/watchlist/$user_id"

   add_film() {
       curl -si -H 'Content-Type: application/json' \
           --data "{\"film_id\":\"$1\"}" "$watchlist/add"
   }
   ```

3. Run `add_film "$alien_id"`, then `curl -si "$watchlist"`. The first request returns **201** with `film_id`, `date_added`, and `public: false` among the entry fields. The list returns **200** with one film, `Alien`, and its saved visibility and addition time. In the list response, `id` is the film UUID.
4. Repeat `add_film "$alien_id"`, then list again. The add returns **409** with a JSON `error`. The list still contains one `Alien` entry with its original `date_added` and `public` values.
5. Run `add_film 00000000-0000-0000-0000-000000000000`. This well-formed UUID is absent from the seeded catalog and returns **404** with a JSON `error`. Run `curl -si -H 'Content-Type: application/json' --data '{"film_id":1}' "$watchlist/add"` to verify that an integer returns **400** with `film_id must be a UUID string`.
6. Run `add_film "$godfather_id"`, then `curl -si "$watchlist"`. The add returns **201**. The list returns **200** with `The Godfather` followed by `Alien`. That order differs from both title order and release year descending because `The Godfather` was saved later.

The requests and response assertions were exercised over HTTP against a temporary Flask server with a freshly seeded SQLite database. The shell commands above reproduce those checks.

### Automated verification

- `.venv/bin/python -m pytest tests/test_watchlist.py -v` — 7 passed, exit 0.
- `.venv/bin/python -m pytest tests/ -v` — 11 passed, exit 0.

## Baseline and source review

Original review: https://github.com/codepath/ai201-project6-cinelog-starter/pull/1 . All six comments retrieved, including inline and conversation comments. Read README.md, CONTRIBUTING.md, models, services, routes, and collection tests. Existing .gitignore preserved; added pytest cache exclusion. Existing .venv requirements are satisfied. `.venv/bin/python -m pytest tests/ -v`: exit 0, 4 passed. System python3 lacks pytest; use the project environment. No pre-existing test failures.
