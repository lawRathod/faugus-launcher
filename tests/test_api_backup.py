"""Tests for the Backup API — TDD Red-Green cycle."""


class TestCreateBackup:
    """POST /api/backup/create"""

    def test_returns_backup_path(self, client) -> None:
        """Creating a backup returns a path."""
        resp = client.post("/api/backup/create")
        assert resp.status_code == 200
        data = resp.json()
        assert "path" in data
        assert "size" in data
        assert "date" in data


class TestRestoreBackup:
    """POST /api/backup/restore — stub until multipart handling"""

    def test_not_implemented(self, client) -> None:
        """Returns 501 for now."""
        resp = client.post("/api/backup/restore")
        assert resp.status_code == 501
