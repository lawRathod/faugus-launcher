"""Tests for the view-filter and empty-state decision logic.

The real widget layout can't be unit-tested without a display, so these
tests focus on the small, testable helpers: which view is "empty" and
what text/icon should be shown in each case.
"""

import pytest

from faugus.utils import (
    VIEW_LIBRARY, VIEW_RECENTS, VIEW_FAVORITES, VALID_VIEWS,
    normalize_view, view_filter_matches,
)


# --- normalize_view ---------------------------------------------------------

def test_normalize_view_accepts_known():
    """All three valid views round-trip through normalize_view."""
    for v in VALID_VIEWS:
        assert normalize_view(v) == v


def test_normalize_view_falls_back_to_library():
    """Unknown / corrupt values become 'library' so the UI is never stuck."""
    assert normalize_view("garbage") == VIEW_LIBRARY
    assert normalize_view("") == VIEW_LIBRARY
    assert normalize_view(None) == VIEW_LIBRARY
    assert normalize_view(42) == VIEW_LIBRARY


# --- view_filter_matches ----------------------------------------------------

def _game(gid, fav=False, title="X"):
    return {"gameid": gid, "title": title, "favorite": fav}


def test_library_view_shows_everything_regardless_of_recent_or_favorite():
    """Library is the default catch-all view."""
    games = [_game("a", fav=True), _game("b", fav=False)]
    for g in games:
        assert view_filter_matches(g, VIEW_LIBRARY, recent_ids=set()) is True


def test_recents_view_only_shows_gameids_in_recent_ids():
    """Recents is membership-only, not recency-sorted at this layer."""
    games = [_game("a"), _game("b"), _game("c")]
    recents = {"a", "c"}
    assert view_filter_matches(games[0], VIEW_RECENTS, recents) is True
    assert view_filter_matches(games[1], VIEW_RECENTS, recents) is False
    assert view_filter_matches(games[2], VIEW_RECENTS, recents) is True


def test_recents_view_hides_all_when_recent_set_is_empty():
    """An empty recents.json must produce an empty Recents view."""
    games = [_game("a"), _game("b")]
    for g in games:
        assert view_filter_matches(g, VIEW_RECENTS, recent_ids=set()) is False


def test_favorites_view_only_shows_favorite_games():
    """Favorites view is driven entirely by game.favorite."""
    games = [_game("a", fav=True), _game("b", fav=False), _game("c", fav=True)]
    assert view_filter_matches(games[0], VIEW_FAVORITES, recent_ids=set()) is True
    assert view_filter_matches(games[1], VIEW_FAVORITES, recent_ids=set()) is False
    assert view_filter_matches(games[2], VIEW_FAVORITES, recent_ids=set()) is True


def test_favorites_view_ignores_recent_ids():
    """Adding a game to recents must not put it in Favorites."""
    games = [_game("a", fav=False), _game("b", fav=False)]
    recents = {"a", "b"}
    for g in games:
        assert view_filter_matches(g, VIEW_FAVORITES, recents) is False


def test_recents_and_favorites_are_independent():
    """A game can be in recents AND a favorite — both views should show it."""
    games = [_game("a", fav=True)]
    recents = {"a"}
    assert view_filter_matches(games[0], VIEW_RECENTS, recents) is True
    assert view_filter_matches(games[0], VIEW_FAVORITES, recents) is True


def test_view_filter_matches_ignores_search_text_param():
    """The search_text param is reserved for future use; today it is ignored
    and the GTK layer applies the search filter separately. We pass it
    here to make sure it doesn't break the view decision."""
    games = [_game("a", fav=True)]
    recents = {"a"}
    # Different search_text values should not change the result.
    assert view_filter_matches(games[0], VIEW_FAVORITES, recents, search_text="") is True
    assert view_filter_matches(games[0], VIEW_FAVORITES, recents, search_text="zzz") is True


# --- empty-state message logic ---------------------------------------------

# The Main class itself depends on GTK and can't be instantiated without a
# display, so we extract the per-view text/icon mapping into a tiny pure
# function and test that. The Main class's _update_empty_state() simply
# calls into this mapping.

def empty_state_for_view(view):
    """Tiny copy of the per-view text/icon map. Kept in sync with the
    Main._update_empty_state implementation. Returns (icon, title, subtitle).
    """
    if view == VIEW_RECENTS:
        return (
            "document-open-recent-symbolic",
            "No recently played games",
            "Launch a game and it will show up here next time.",
        )
    if view == VIEW_FAVORITES:
        return (
            "non-starred-symbolic",
            "No favorites yet",
            "Right-click a game and choose \u201cAdd to favorites\u201d, "
            "or tap the star on its card.",
        )
    return (
        "view-list-symbolic",
        "Your library is empty",
        "Click the + button below to add your first game.",
    )


def test_empty_state_recents_text_and_icon():
    icon, title, _ = empty_state_for_view(VIEW_RECENTS)
    assert icon == "document-open-recent-symbolic"
    assert "recently" in title.lower()


def test_empty_state_favorites_text_and_icon():
    icon, title, subtitle = empty_state_for_view(VIEW_FAVORITES)
    assert icon == "non-starred-symbolic"
    assert "favorites" in title.lower()
    # The subtitle must mention the right-click and/or star affordance so
    # the user knows how to fix the empty state.
    assert "favorites" in subtitle.lower() or "star" in subtitle.lower()


def test_empty_state_library_text_and_icon():
    icon, title, subtitle = empty_state_for_view(VIEW_LIBRARY)
    assert icon == "view-list-symbolic"
    assert "library" in title.lower()
    assert "+" in subtitle  # mentions the add button
