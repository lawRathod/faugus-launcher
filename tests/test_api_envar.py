"""Tests for the Environment Variables API — TDD Red-Green cycle."""


class TestGetEnvar:
    """GET /api/envar"""

    def test_returns_list(self, client) -> None:
        """Returns a list of env var strings (may be empty)."""
        resp = client.get("/api/envar")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPutEnvar:
    """PUT /api/envar"""

    def test_saves_list(self, client) -> None:
        """Saves env var list and returns it."""
        resp = client.put("/api/envar", json=["FOO=bar", "BAZ=qux"])
        assert resp.status_code == 200
        assert "FOO=bar" in resp.json()
        assert "BAZ=qux" in resp.json()
