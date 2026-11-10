"""Watchlist service regression tests using the collection test fixtures."""

import pytest
from models import WatchlistEntry
from services.watchlist_service import add_to_watchlist
from services.collection_service import FilmNotFoundError
from tests.test_collection import app, sample_user


def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """An absent, well-formed film UUID raises without creating an entry."""
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"
        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)
        assert WatchlistEntry.query.count() == 0
