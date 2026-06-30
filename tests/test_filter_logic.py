"""Tests for the sidebar view filter logic.

The filter is a pure function: given a game, a view name, the set of recent
gameids, and a search text, decide whether the game should be shown.
"""
import pytest

from faugus.utils import view_filter_matches


class TestViewFilterLibrary:
    """In 'library' view every game passes (subject to other filters)."""

    def test_library_shows_any_game(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Anything", "favorite": False},
            view="library",
            recent_ids={"g1", "g2"},
            search_text="",
        ) is True

    def test_library_shows_favorite(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Fav", "favorite": True},
            view="library",
            recent_ids=set(),
            search_text="",
        ) is True

    def test_library_shows_non_recent(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Old", "favorite": False},
            view="library",
            recent_ids=set(),  # game is not in recents
            search_text="",
        ) is True


class TestViewFilterRecents:
    """In 'recents' view only games in recent_ids are shown."""

    def test_recents_shows_recent_game(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Played", "favorite": False},
            view="recents",
            recent_ids={"g1"},
            search_text="",
        ) is True

    def test_recents_hides_non_recent_game(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Never played", "favorite": False},
            view="recents",
            recent_ids={"g2", "g3"},
            search_text="",
        ) is False

    def test_recents_shows_favorite_even_if_not_recent(self):
        """A favorite is a favorite regardless of recents list."""
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Fav", "favorite": True},
            view="recents",
            recent_ids=set(),
            search_text="",
        ) is False  # recents is strict: only games in recent_ids

    def test_recents_with_empty_recent_list(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "x", "favorite": False},
            view="recents",
            recent_ids=set(),
            search_text="",
        ) is False


class TestViewFilterFavorites:
    """In 'favorites' view only games with favorite=True are shown."""

    def test_favorites_shows_favorite_game(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Fav", "favorite": True},
            view="favorites",
            recent_ids=set(),
            search_text="",
        ) is True

    def test_favorites_hides_non_favorite_game(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "Regular", "favorite": False},
            view="favorites",
            recent_ids={"g1"},
            search_text="",
        ) is False

    def test_favorites_with_no_favorites(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "x", "favorite": False},
            view="favorites",
            recent_ids=set(),
            search_text="",
        ) is False


class TestViewFilterUnknownView:
    """Unknown view strings fall through to 'show all' for forward-compat."""

    def test_unknown_view_shows_all(self):
        assert view_filter_matches(
            game={"gameid": "g1", "title": "x", "favorite": False},
            view="something_new",
            recent_ids=set(),
            search_text="",
        ) is True
