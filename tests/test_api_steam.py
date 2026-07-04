"""Tests for the Steam API — TDD Red-Green cycle.

These tests work without Steam installed — the API returns null/empty
responses when Steam is not detected.
"""


class TestSteamStatus:
    """GET /api/steam/status"""

    def test_returns_status_object(self, client) -> None:
        """Returns a status dict with version field."""
        resp = client.get("/api/steam/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "steam_id" in data
        assert "shortcuts_path" in data

    def test_version_is_string_or_null(self, client) -> None:
        """Version is either null (not found) or 'native'/'flatpak'."""
        resp = client.get("/api/steam/status")
        data = resp.json()
        assert data["version"] in (None, "native", "flatpak")


class TestSteamGames:
    """GET /api/steam/games"""

    def test_returns_list(self, client) -> None:
        """Returns a list (may be empty in CI)."""
        resp = client.get("/api/steam/games")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestSteamShortcut:
    """POST /api/steam/shortcut"""

    def test_shortcut_without_gameid_fails(self, client) -> None:
        """Missing gameid returns 422."""
        resp = client.post("/api/steam/shortcut", json={
            "title": "Test Game",
            "action": "add",
        })
        assert resp.status_code == 422
