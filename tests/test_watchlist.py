"""Watchlist service regression tests using the collection test fixtures."""

import pytest
from models import WatchlistEntry
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
