"""Tests for the core Game model."""

import pytest
from faugus.core.models import Game
from faugus.core.utils import GAME_FIELDS, GAME_DEFAULTS


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


class TestGameConstruction:
    def test_basic_construction(self):
        game = Game(**_minimal_game_kwargs())
        assert game.gameid == "test-game-1"
        assert game.title == "Test Game"

    def test_favorite_default(self):
        game = Game(**_minimal_game_kwargs())
        assert game.favorite is False

    def test_favorite_explicit(self):
        game = Game(favorite=True, **_minimal_game_kwargs())
        assert game.favorite is True

    def test_repr(self):
        game = Game(**_minimal_game_kwargs())
        assert "test-game-1" in repr(game)
        assert "Test Game" in repr(game)


class TestGameFromDict:
    def test_from_dict_minimal(self):
        data = {"gameid": "g1", "title": "Game 1"}
        game = Game.from_dict(data)
        assert game.gameid == "g1"
        assert game.title == "Game 1"
        assert game.favorite is False

    def test_from_dict_full(self):
        data = _minimal_game_kwargs()
        data["favorite"] = True
        game = Game.from_dict(data)
        assert game.favorite is True
        assert game.runner == "Proton-CachyOS"

    def test_from_dict_fills_defaults(self):
        data = {"gameid": "g2", "title": "Game 2"}
        game = Game.from_dict(data)
        assert game.playtime == 0
        assert game.hidden is False
        assert game.icon == ""


class TestGameSerialization:
    def test_to_dict_roundtrip(self):
        data = _minimal_game_kwargs()
        data["favorite"] = True
        game = Game.from_dict(data)
        d = game.to_dict()
        assert d["gameid"] == "g1" or d["gameid"] == "test-game-1"
        assert d["favorite"] is True

    def test_to_save_dict_normalizes_booleans(self):
        data = _minimal_game_kwargs()
        data["mangohud"] = True
        data["gamemode"] = True
        data["addapp_checkbox"] = True
        game = Game.from_dict(data)
        d = game.to_save_dict()
        assert d["mangohud"] is True
        assert d["gamemode"] is True
        assert d["addapp_checkbox"] == "addapp_enabled"

    def test_to_save_dict_with_hidden(self):
        data = _minimal_game_kwargs()
        game = Game.from_dict(data)
        d = game.to_save_dict(hidden=True)
        assert d["hidden"] is True


class TestGameQueryHelpers:
    def _make(self, **overrides):
        data = _minimal_game_kwargs()
        data.update(overrides)
        return Game(**data)

    def test_display_name(self):
        game = self._make(title="  My Game  ")
        assert game.display_name == "My Game"

    def test_formatted_playtime_zero(self):
        game = self._make(playtime=0)
        assert game.formatted_playtime == "0m"

    def test_formatted_playtime_hours(self):
        game = self._make(playtime=3661)
        assert game.formatted_playtime == "1h 1m"

    def test_formatted_playtime_minutes_only(self):
        game = self._make(playtime=300)
        assert game.formatted_playtime == "5m"

    def test_has_addapp_false(self):
        game = self._make(addapp_checkbox="", addapp="")
        assert game.has_addapp is False

    def test_has_addapp_true(self):
        game = self._make(addapp_checkbox="addapp_enabled", addapp="/path/to/app")
        assert game.has_addapp is True

    def test_has_lossless_false(self):
        game = self._make(lossless_enabled=False)
        assert game.has_lossless is False

    def test_has_lossless_true(self):
        game = self._make(lossless_enabled=True)
        assert game.has_lossless is True


class TestGameEquality:
    def _make_game(self, gameid, title):
        kwargs = {k: "" for k in GAME_FIELDS if k not in ("gameid", "title", "playtime", "hidden", "prevent_sleep", "category", "favorite")}
        kwargs["playtime"] = 0
        kwargs["hidden"] = False
        kwargs["prevent_sleep"] = False
        kwargs["category"] = False
        kwargs["favorite"] = False
        return Game(gameid=gameid, title=title, **kwargs)

    def test_equal_by_gameid(self):
        g1 = self._make_game("x", "A")
        g2 = self._make_game("x", "B")
        assert g1 == g2

    def test_not_equal_different_gameid(self):
        g1 = self._make_game("x", "A")
        g2 = self._make_game("y", "A")
        assert g1 != g2

    def test_hash_by_gameid(self):
        g1 = self._make_game("x", "A")
        g2 = self._make_game("x", "B")
        assert hash(g1) == hash(g2)
