"""Tests for the Logs API — TDD Red-Green cycle."""

import os


class TestGetLogs:
    """GET /api/logs/{gameid}"""

    def test_nonexistent_game_returns_empty(self, client) -> None:
        """Game with no logs returns empty strings."""
        resp = client.get("/api/logs/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert "proton_log" in data
        assert "umu_log" in data
        assert data["proton_log"] == ""
        assert data["umu_log"] == ""


class TestClearLogs:
    """DELETE /api/logs"""

    def test_returns_success(self, client) -> None:
        """Clearing logs returns a success response."""
        resp = client.delete("/api/logs")
        assert resp.status_code == 200
        assert resp.json()["cleared"]
