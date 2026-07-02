"""Tests for core.repository — GameRepository and RecentsRepository."""

import os
import pytest
from faugus.core.repository import GameRepository, RecentsRepository
from faugus.core.models import Game


def _make_game(gameid="g1", title="Test Game", **overrides):
    """Helper to build a Game with sane defaults."""
    defaults = {
        "gameid": gameid,
        "title": title,
        "path": f"/tmp/{gameid}.exe",
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
        "favorite": False,
    }
    defaults.update(overrides)
    return Game(**defaults)


class TestGameRepository:
    def test_load_empty(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        assert repo.load_all() == []

    def test_save_and_load(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        games = [_make_game("g1", "Game 1"), _make_game("g2", "Game 2")]
        repo.save_all(games)
        loaded = repo.load_all()
        assert len(loaded) == 2
        assert loaded[0].gameid == "g1"
        assert loaded[1].title == "Game 2"

    def test_find_by_id(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1"), _make_game("g2")])
        found = repo.find_by_id("g2")
        assert found is not None
        assert found.title == "Test Game"

    def test_find_by_id_missing(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1")])
        assert repo.find_by_id("nonexistent") is None

    def test_add_game(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1")])
        repo.add_game(_make_game("g2"))
        assert repo.count() == 2

    def test_update_game(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1", "Old Title")])
        updated = _make_game("g1", "New Title")
        repo.update_game(updated)
        loaded = repo.find_by_id("g1")
        assert loaded.title == "New Title"

    def test_delete_game(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1"), _make_game("g2")])
        repo.delete_game("g1")
        assert repo.count() == 1
        assert repo.find_by_id("g1") is None

    def test_set_favorite(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1")])
        assert repo.set_favorite("g1", True) is True
        loaded = repo.find_by_id("g1")
        assert loaded.favorite is True

    def test_set_favorite_unknown(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        assert repo.set_favorite("nonexistent", True) is False

    def test_update_playtime(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        repo.save_all([_make_game("g1")])
        repo.update_playtime("g1", 100)
        loaded = repo.find_by_id("g1")
        assert loaded.playtime == 100

    def test_count(self, tmp_path):
        repo = GameRepository(str(tmp_path / "games.json"))
        assert repo.count() == 0
        repo.save_all([_make_game("g1"), _make_game("g2"), _make_game("g3")])
        assert repo.count() == 3


class TestRecentsRepository:
    def test_load_empty(self, tmp_path):
        repo = RecentsRepository(str(tmp_path / "recents.json"))
        assert repo.load() == {}

    def test_save_and_load(self, tmp_path):
        repo = RecentsRepository(str(tmp_path / "recents.json"))
        repo.save({"g1": 1000.0, "g2": 2000.0})
        loaded = repo.load()
        assert loaded["g1"] == 1000.0
        assert loaded["g2"] == 2000.0

    def test_touch(self, tmp_path):
        repo = RecentsRepository(str(tmp_path / "recents.json"))
        repo.touch("g1")
        loaded = repo.load()
        assert "g1" in loaded

    def test_clear(self, tmp_path):
        repo = RecentsRepository(str(tmp_path / "recents.json"))
        repo.save({"g1": 1.0})
        repo.clear()
        assert repo.load() == {}

    def test_get_recent_ids(self, tmp_path):
        repo = RecentsRepository(str(tmp_path / "recents.json"))
        repo.save({"g1": 1000.0, "g2": 2000.0, "g3": 1500.0})
        ids = repo.get_recent_ids()
        assert ids == ["g2", "g3", "g1"]
