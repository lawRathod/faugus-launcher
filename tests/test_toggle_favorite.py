"""Tests for the toggle_favorite persistence layer.

The actual toggle_favorite method on the Main window does two things:
  1. Find the game object, flip its .favorite attribute
  2. Persist the change to games.json

Step 2 is a pure data operation and lives in faugus.utils as
``set_favorite_in_json``. Step 1 is a thin wrapper in launcher.py.
"""
import json
from pathlib import Path

import pytest

from faugus.utils import set_favorite_in_json


def _write_games(path: Path, games: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(games))


def _read_games(path: Path) -> list:
    return json.loads(path.read_text())


class TestSetFavoriteInJson:
    """set_favorite_in_json reads games.json, flips one game, writes it back."""

    def test_set_true(self, tmp_path):
        games_file = tmp_path / "games.json"
        _write_games(games_file, [
            {"gameid": "g1", "title": "Game 1", "favorite": False},
        ])
        result = set_favorite_in_json(games_file, "g1", True)
        assert result is True
        assert _read_games(games_file)[0]["favorite"] is True

    def test_set_false(self, tmp_path):
        games_file = tmp_path / "games.json"
        _write_games(games_file, [
            {"gameid": "g1", "title": "Game 1", "favorite": True},
        ])
        result = set_favorite_in_json(games_file, "g1", False)
        assert result is True
        assert _read_games(games_file)[0]["favorite"] is False

    def test_unknown_gameid_returns_false(self, tmp_path):
        games_file = tmp_path / "games.json"
        _write_games(games_file, [
            {"gameid": "g1", "title": "Game 1", "favorite": False},
        ])
        result = set_favorite_in_json(games_file, "does-not-exist", True)
        assert result is False
        # Original game untouched
        assert _read_games(games_file)[0]["favorite"] is False

    def test_preserves_other_fields(self, tmp_path):
        games_file = tmp_path / "games.json"
        _write_games(games_file, [
            {"gameid": "g1", "title": "Game 1", "runner": "Proton",
             "playtime": 42, "favorite": False},
        ])
        set_favorite_in_json(games_file, "g1", True)
        game = _read_games(games_file)[0]
        assert game["title"] == "Game 1"
        assert game["runner"] == "Proton"
        assert game["playtime"] == 42
        assert game["favorite"] is True

    def test_only_target_game_is_modified(self, tmp_path):
        games_file = tmp_path / "games.json"
        _write_games(games_file, [
            {"gameid": "g1", "title": "Game 1", "favorite": False},
            {"gameid": "g2", "title": "Game 2", "favorite": False},
            {"gameid": "g3", "title": "Game 3", "favorite": True},
        ])
        set_favorite_in_json(games_file, "g2", True)
        games = _read_games(games_file)
        assert games[0]["favorite"] is False  # g1 untouched
        assert games[1]["favorite"] is True   # g2 toggled
        assert games[2]["favorite"] is True   # g3 untouched

    def test_missing_file_returns_false(self, tmp_path):
        games_file = tmp_path / "does-not-exist.json"
        result = set_favorite_in_json(games_file, "g1", True)
        assert result is False
