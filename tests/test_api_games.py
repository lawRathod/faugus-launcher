"""Tests for the Games API — TDD Red-Green cycle.

Every test is written before the implementation code.
"""

import json
from pathlib import Path


class TestListGames:
    """GET /api/games"""

    def test_empty_list(self, client) -> None:
        """No games configured → empty JSON array."""
        resp = client.get("/api/games")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_saved_games(self, client, sample_game, games_path) -> None:
        """Games from games.json are returned."""
        games_path.write_text(json.dumps([sample_game]))
        resp = client.get("/api/games")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["gameid"] == "test-game-1"
        assert data[0]["title"] == "Test Game"

    def test_hidden_excluded_by_default(self, client, sample_game, games_path) -> None:
        """Hidden games are omitted unless ?hidden=1."""
        hidden = dict(sample_game, gameid="hidden-1", hidden=True)
        visible = dict(sample_game, gameid="visible-1", hidden=False)
        games_path.write_text(json.dumps([hidden, visible]))
        resp = client.get("/api/games")
        ids = [g["gameid"] for g in resp.json()]
        assert "visible-1" in ids
        assert "hidden-1" not in ids

    def test_include_hidden_with_param(self, client, sample_game, games_path) -> None:
        """?hidden=1 includes hidden games."""
        hidden = dict(sample_game, gameid="hidden-1", hidden=True)
        visible = dict(sample_game, gameid="visible-1", hidden=False)
        games_path.write_text(json.dumps([hidden, visible]))
        resp = client.get("/api/games?hidden=1")
        ids = [g["gameid"] for g in resp.json()]
        assert "visible-1" in ids
        assert "hidden-1" in ids

    def test_hidden_as_bool_param(self, client, sample_game, games_path) -> None:
        """?hidden=true (bool string) also works."""
        hidden = dict(sample_game, gameid="h1", hidden=True)
        visible = dict(sample_game, gameid="v1", hidden=False)
        games_path.write_text(json.dumps([hidden, visible]))
        resp = client.get("/api/games?hidden=true")
        ids = [g["gameid"] for g in resp.json()]
        assert "h1" in ids
        assert "v1" in ids

    def test_search_filter(self, client, sample_game, games_path) -> None:
        """?search=term filters by title substring (case-insensitive)."""
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="g1", title="Half-Life 2"),
            dict(sample_game, gameid="g2", title="Portal 2"),
            dict(sample_game, gameid="g3", title="Team Fortress 2"),
        ]))
        resp = client.get("/api/games?search=portal")
        ids = [g["gameid"] for g in resp.json()]
        assert ids == ["g2"]

    def test_sort_alpha(self, client, sample_game, games_path) -> None:
        """?sort=alpha returns games alphabetically."""
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="z", title="Zoo Tycoon"),
            dict(sample_game, gameid="a", title="Age of Empires"),
        ]))
        resp = client.get("/api/games?sort=alpha")
        ids = [g["gameid"] for g in resp.json()]
        assert ids == ["a", "z"]

    def test_category_filter(self, client, sample_game, games_path) -> None:
        """?category=RTS filters to games in that category."""
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="g1", category=["RTS"]),
            dict(sample_game, gameid="g2", category=["FPS"]),
            dict(sample_game, gameid="g3", category=["RTS", "FPS"]),
        ]))
        resp = client.get("/api/games?category=RTS")
        ids = [g["gameid"] for g in resp.json()]
        assert "g1" in ids
        assert "g2" not in ids
        assert "g3" in ids

    def test_category_legacy_string(self, client, sample_game, games_path) -> None:
        """Legacy games with category as a string still get filtered."""
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="g1", category="RTS"),
            dict(sample_game, gameid="g2", category="FPS"),
        ]))
        resp = client.get("/api/games?category=RTS")
        ids = [g["gameid"] for g in resp.json()]
        assert "g1" in ids
        assert "g2" not in ids

    def test_category_false_value(self, client, sample_game, games_path) -> None:
        """Category = False is treated as uncategorized."""
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="g1", category=False),
            dict(sample_game, gameid="g2", category=["RTS"]),
        ]))
        resp = client.get("/api/games?category=_uncategorized")
        ids = [g["gameid"] for g in resp.json()]
        assert "g1" in ids
        assert "g2" not in ids

    def test_category_uncategorized(self, client, sample_game, games_path) -> None:
        """?category=_uncategorized returns games with no category."""
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="g1", category=[]),
            dict(sample_game, gameid="g2", category=["RTS"]),
            dict(sample_game, gameid="g3"),
        ]))
        resp = client.get("/api/games?category=_uncategorized")
        ids = [g["gameid"] for g in resp.json()]
        assert "g1" in ids
        assert "g2" not in ids
        assert "g3" in ids


class TestCreateGame:
    """POST /api/games"""

    def test_create_minimal(self, client) -> None:
        """Create a game with minimal fields."""
        resp = client.post("/api/games", json={
            "title": "My Game",
            "path": "/home/game.exe",
            "prefix": "/home/prefix",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Game"
        assert data["gameid"]  # auto-generated
        assert data["path"] == "/home/game.exe"

    def test_create_requires_title(self, client) -> None:
        """Missing title returns 422."""
        resp = client.post("/api/games", json={
            "path": "/home/game.exe",
            "prefix": "/home/prefix",
        })
        assert resp.status_code == 422

    def test_create_empty_title(self, client) -> None:
        """Empty string title returns 422."""
        resp = client.post("/api/games", json={
            "title": "",
            "path": "/home/game.exe",
            "prefix": "/home/prefix",
        })
        assert resp.status_code == 422

    def test_create_requires_path(self, client) -> None:
        """Missing path returns 422."""
        resp = client.post("/api/games", json={
            "title": "Game",
            "prefix": "/home/prefix",
        })
        assert resp.status_code == 422

    def test_create_duplicate_title(self, client, sample_game, games_path) -> None:
        """Duplicate title returns 409."""
        games_path.write_text(json.dumps([sample_game]))
        resp = client.post("/api/games", json={
            "title": sample_game["title"],
            "path": "/other.exe",
            "prefix": "/other/prefix",
        })
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Game 'Test Game' already exists."

    def test_create_persists_to_disk(self, client, games_path) -> None:
        """Created game is written to games.json."""
        client.post("/api/games", json={
            "title": "Persist Test",
            "path": "/home/persist.exe",
            "prefix": "/home/prefix",
        })
        saved = json.loads(games_path.read_text())
        assert len(saved) == 1
        assert saved[0]["title"] == "Persist Test"

    def test_create_rejects_path_traversal(self, client) -> None:
        """Path with .. returns 422."""
        resp = client.post("/api/games", json={
            "title": "Bad",
            "path": "/home/../../etc/game.exe",
            "prefix": "/home/prefix",
        })
        assert resp.status_code == 422

    def test_create_rejects_prefix_traversal(self, client) -> None:
        """Prefix with .. returns 422."""
        resp = client.post("/api/games", json={
            "title": "Bad",
            "path": "/home/game.exe",
            "prefix": "/home/../../etc/prefix",
        })
        assert resp.status_code == 422


class TestGetGame:
    """GET /api/games/{gameid}"""

    def test_get_existing(self, client, sample_game, games_path) -> None:
        games_path.write_text(json.dumps([sample_game]))
        resp = client.get("/api/games/test-game-1")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Game"

    def test_get_missing(self, client) -> None:
        resp = client.get("/api/games/nonexistent")
        assert resp.status_code == 404


class TestUpdateGame:
    """PUT /api/games/{gameid}"""

    def test_update_title(self, client, sample_game, games_path) -> None:
        games_path.write_text(json.dumps([sample_game]))
        resp = client.put("/api/games/test-game-1", json={
            "title": "Updated Title",
            "path": sample_game["path"],
            "prefix": sample_game["prefix"],
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        saved = json.loads(games_path.read_text())
        assert saved[0]["title"] == "Updated Title"

    def test_update_preserves_extra_fields(self, client, sample_game, games_path) -> None:
        """Fields not in the update model (e.g. mangohud) survive the update."""
        game = dict(sample_game, mangohud=True, protonfix="12345", lossless_multiplier="3")
        games_path.write_text(json.dumps([game]))
        resp = client.put("/api/games/test-game-1", json={
            "title": "Still Extra",
            "path": game["path"],
            "prefix": game["prefix"],
        })
        assert resp.status_code == 200
        saved = json.loads(games_path.read_text())
        assert saved[0]["mangohud"] is True
        assert saved[0]["protonfix"] == "12345"
        assert saved[0]["lossless_multiplier"] == "3"

    def test_update_nonexistent(self, client) -> None:
        resp = client.put("/api/games/nonexistent", json={
            "title": "Nope",
            "path": "/nope.exe",
            "prefix": "/nope",
        })
        assert resp.status_code == 404


class TestDeleteGame:
    """DELETE /api/games/{gameid}"""

    def test_delete_existing(self, client, sample_game, games_path) -> None:
        games_path.write_text(json.dumps([sample_game]))
        resp = client.delete("/api/games/test-game-1")
        assert resp.status_code == 200
        saved = json.loads(games_path.read_text())
        assert len(saved) == 0

    def test_delete_nonexistent(self, client) -> None:
        resp = client.delete("/api/games/nonexistent")
        assert resp.status_code == 404


class TestLaunchGame:
    """POST /api/games/{gameid}/launch — depends on runner_core.py (Phase 0)"""

    def test_launch_nonexistent(self, client) -> None:
        """Missing game → 404."""
        resp = client.post("/api/games/nonexistent/launch")
        assert resp.status_code == 404


class TestKillGame:
    """POST /api/games/{gameid}/kill — depends on runner_core.py (Phase 0)"""

    def test_kill_nonexistent(self, client) -> None:
        """Missing game → 404."""
        resp = client.post("/api/games/nonexistent/kill")
        assert resp.status_code == 404


class TestDuplicateGame:
    """POST /api/games/{gameid}/duplicate"""

    def test_duplicate(self, client, sample_game, games_path) -> None:
        games_path.write_text(json.dumps([sample_game]))
        resp = client.post("/api/games/test-game-1/duplicate", json={"title": "Test Game Copy"})
        assert resp.status_code == 201
        saved = json.loads(games_path.read_text())
        assert len(saved) == 2
        titles = [g["title"] for g in saved]
        assert "Test Game Copy" in titles

    def test_duplicate_nonexistent(self, client) -> None:
        resp = client.post("/api/games/nonexistent/duplicate", json={"title": "Copy"})
        assert resp.status_code == 404


class TestToggleHidden:
    """PATCH /api/games/{gameid}/hide"""

    def test_toggle_hidden(self, client, sample_game, games_path) -> None:
        assert sample_game["hidden"] is False
        games_path.write_text(json.dumps([sample_game]))
        resp = client.patch("/api/games/test-game-1/hide")
        assert resp.status_code == 200
        assert resp.json()["hidden"] is True
        saved = json.loads(games_path.read_text())
        assert saved[0]["hidden"] is True

    def test_toggle_nonexistent(self, client) -> None:
        resp = client.patch("/api/games/nonexistent/hide")
        assert resp.status_code == 404


class TestSetCategory:
    """PATCH /api/games/{gameid}/category"""

    def test_set_category(self, client, sample_game, games_path) -> None:
        games_path.write_text(json.dumps([sample_game]))
        resp = client.patch("/api/games/test-game-1/category", json={"categories": ["RTS", "Strategy"]})
        assert resp.status_code == 200
        assert sorted(resp.json()["category"]) == sorted(["RTS", "Strategy"])
        saved = json.loads(games_path.read_text())
        assert sorted(saved[0]["category"]) == sorted(["RTS", "Strategy"])

    def test_set_category_nonexistent(self, client) -> None:
        resp = client.patch("/api/games/nonexistent/category", json={"categories": ["RTS"]})
        assert resp.status_code == 404


class TestCustomOrder:
    """PUT /api/games/custom-order"""

    def test_save_order(self, client, sample_game, games_path, pm) -> None:
        order_path = Path(pm.custom_order)
        order_path.parent.mkdir(parents=True, exist_ok=True)
        games_path.write_text(json.dumps([
            dict(sample_game, gameid="g1"),
            dict(sample_game, gameid="g2"),
        ]))
        resp = client.put("/api/games/custom-order", json={"order": {"g1": 2, "g2": 1}})
        assert resp.status_code == 200
        saved = json.loads(order_path.read_text())
        assert saved == {"g1": 2, "g2": 1}


class TestRunningStatus:
    """GET /api/games/status"""

    def test_no_running_games(self, client) -> None:
        resp = client.get("/api/games/status")
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_returns_dict(self, client) -> None:
        resp = client.get("/api/games/status")
        assert isinstance(resp.json(), dict)
