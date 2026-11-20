"""Watchlist regression tests using the collection test fixtures."""

from datetime import datetime

import pytest
from app import db
from models import Film, WatchlistEntry
from services.watchlist_service import add_to_watchlist
from services.collection_service import FilmNotFoundError
from tests.test_collection import app, sample_film, sample_user


def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """An absent, well-formed film UUID raises without creating an entry."""
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"
        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)
        assert WatchlistEntry.query.count() == 0


def test_watchlist_add_defaults_visibility_to_false(app, sample_user, sample_film):
    client = app.test_client()
    watchlist_url = f"/watchlist/{sample_user}"

    added = client.post(f"{watchlist_url}/add", json={"film_id": sample_film})

    assert added.status_code == 201
    assert added.get_json()["public"] is False
    listed = client.get(watchlist_url)
    assert listed.status_code == 200
    assert [film["public"] for film in listed.get_json()] == [False]


def test_watchlist_add_accepts_uppercase_film_uuid(app, sample_user):
    film_id = "ac0322c5-19ae-4f40-8666-6a5202db8b8d"
    with app.app_context():
        db.session.add(Film(id=film_id, title="Alien"))
        db.session.commit()

    added = app.test_client().post(
        f"/watchlist/{sample_user}/add", json={"film_id": film_id.upper()}
    )

    assert added.status_code == 201
    assert added.get_json()["film_id"] == film_id


@pytest.mark.parametrize(("film_id", "expected_status"), [
    (1, 400),
    ("not-a-uuid", 400),
    ("00000000-0000-0000-0000-000000000000", 404),
])
def test_watchlist_add_distinguishes_invalid_and_absent_film_ids(
    app, sample_user, film_id, expected_status
):
    response = app.test_client().post(
        f"/watchlist/{sample_user}/add", json={"film_id": film_id}
    )

    assert response.status_code == expected_status
    assert "error" in response.get_json()


def test_watchlist_lists_newest_additions_first(app, sample_user):
    with app.app_context():
        alien = Film(title="Alien", year=1979)
        blade_runner = Film(title="Blade Runner", year=1982)
        solaris = Film(title="Solaris", year=1972)
        db.session.add_all([alien, blade_runner, solaris])
        db.session.flush()

        # Insert the tied entries out of ID order.
        earlier = datetime(2026, 1, 1)
        later = datetime(2026, 1, 2)
        db.session.add_all([
            WatchlistEntry(
                id="00000000-0000-4000-8000-000000000002",
                user_id=sample_user, film_id=blade_runner.id, date_added=later,
            ),
            WatchlistEntry(
                id="00000000-0000-4000-8000-000000000000",
                user_id=sample_user, film_id=alien.id, date_added=earlier,
            ),
            WatchlistEntry(
                id="00000000-0000-4000-8000-000000000001",
                user_id=sample_user, film_id=solaris.id, date_added=later,
            ),
        ])
        db.session.commit()

    listed = app.test_client().get(f"/watchlist/{sample_user}")

    assert listed.status_code == 200
    assert [film["title"] for film in listed.get_json()] == [
        "Solaris", "Blade Runner", "Alien",
    ]
