"""Regression tests for the games.json migration in update_games_json().

The migration used to strip a ``favorite`` field that the old code stored
on games. A later redesign repurposed ``favorite`` as a real user-facing
flag, but the migration kept stripping it — every cold launch would
silently destroy the user's favorites. These tests pin the new
behaviour: the migration must leave ``favorite`` alone.
"""

import json

from faugus.utils import update_games_json


def test_migration_preserves_favorite_true(tmp_path, monkeypatch):
    """A game with favorite=True on disk must still have it after migration."""
    import faugus.utils as utils
    monkeypatch.setattr(utils, "games_json", str(tmp_path / "games.json"))
    games = [
        {"gameid": "g1", "title": "G1", "favorite": True, "category": "Action"},
    ]
    (tmp_path / "games.json").write_text(json.dumps(games))

    update_games_json()

    with open(tmp_path / "games.json") as f:
        result = json.load(f)
    assert result[0]["favorite"] is True
    # The category field is now user data, not a migration side effect.
    assert result[0]["category"] == "Action"


def test_migration_preserves_favorite_false(tmp_path, monkeypatch):
    """A game with favorite=False must still have it after migration."""
    import faugus.utils as utils
    monkeypatch.setattr(utils, "games_json", str(tmp_path / "games.json"))
    games = [
        {"gameid": "g1", "title": "G1", "favorite": False},
    ]
    (tmp_path / "games.json").write_text(json.dumps(games))

    update_games_json()

    with open(tmp_path / "games.json") as f:
        result = json.load(f)
    assert "favorite" in result[0]
    assert result[0]["favorite"] is False


def test_migration_does_not_add_favorite_field(tmp_path, monkeypatch):
    """Games without a favorite field must not gain one from the migration."""
    import faugus.utils as utils
    monkeypatch.setattr(utils, "games_json", str(tmp_path / "games.json"))
    games = [
        {"gameid": "g1", "title": "G1"},
    ]
    (tmp_path / "games.json").write_text(json.dumps(games))

    update_games_json()

    with open(tmp_path / "games.json") as f:
        result = json.load(f)
    assert "favorite" not in result[0]


def test_migration_still_runs_proton_cachyos_rename(tmp_path, monkeypatch):
    """The Proton-CachyOS rename migration must still happen."""
    import faugus.utils as utils
    monkeypatch.setattr(utils, "games_json", str(tmp_path / "games.json"))
    games = [
        {"gameid": "g1", "title": "G1", "runner": "Proton-CachyOS", "favorite": True},
    ]
    (tmp_path / "games.json").write_text(json.dumps(games))

    update_games_json()

    with open(tmp_path / "games.json") as f:
        result = json.load(f)
    assert result[0]["runner"] == "Proton-CachyOS (System)"
    # And the favorite field is still intact.
    assert result[0]["favorite"] is True
