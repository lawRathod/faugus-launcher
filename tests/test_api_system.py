"""Tests for the System API — TDD Red-Green cycle."""


class TestSystemStatus:
    """GET /api/system/status"""

    def test_returns_status(self, client) -> None:
        """Returns system status with version and running games."""
        resp = client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "running_games" in data
        assert data["version"] == "1.22.7"
