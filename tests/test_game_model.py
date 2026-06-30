"""Tests for the Game data model and persistence layer.

Covers:
- Game construction accepts a favorite field
- GAME_FIELDS includes "favorite" so it round-trips through games.json
- prepare_game_kwargs defaults favorite to False for legacy games.json files
"""
import pytest

import faugus.launcher as launcher
from faugus.utils import GAME_FIELDS, prepare_game_kwargs


def _minimal_game_kwargs():
    """Return the bare-minimum dict of fields needed to construct a Game."""
    return {
        "gameid": "test-game-1",
        "title": "Test Game",
        "path": "/tmp/test.exe",
        "prefix": "",
        "launch_arguments": "",
        "game_arguments": "",
        "mangohud": False,
        "gamemode": False,
        "disable_hidraw": False,
        "protonfix": "",
        "runner": "Proton-CachyOS",
        "addapp_checkbox": False,
        "addapp": "",
        "addapp_bat": "",
        "addapp_delay": "",
        "addapp_first": False,
        "banner": "",
        "lossless_enabled": False,
        "lossless_multiplier": 1,
        "lossless_flow": 100,
        "lossless_performance": False,
        "lossless_hdr": False,
        "lossless_present": False,
        "playtime": 0,
        "hidden": False,
        "prevent_sleep": False,
        "category": [],
        "icon": "",
    }


class TestGameFavoriteField:
    def test_game_class_has_favorite_attribute(self):
        """A newly constructed Game exposes game.favorite."""
        game = launcher.Game(favorite=False, **_minimal_game_kwargs())
        assert game.favorite is False

    def test_game_can_be_marked_favorite(self):
        game = launcher.Game(favorite=True, **_minimal_game_kwargs())
        assert game.favorite is True


class TestGameFieldsRoundTrip:
    def test_favorite_in_game_fields(self):
        """favorite must be in GAME_FIELDS so it serializes to/from games.json."""
        assert "favorite" in GAME_FIELDS

    def test_prepare_game_kwargs_defaults_favorite_to_false(self):
        """Legacy games.json entries without a 'favorite' key default to False."""
        data = {"gameid": "legacy", "title": "Old Game"}
        kwargs = prepare_game_kwargs(data)
        assert kwargs.get("favorite") is False

    def test_prepare_game_kwargs_preserves_favorite_true(self):
        data = {"gameid": "new", "title": "New Game", "favorite": True}
        kwargs = prepare_game_kwargs(data)
        assert kwargs.get("favorite") is True
