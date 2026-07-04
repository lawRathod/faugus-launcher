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
    """POST /api/backup/restore"""

    def test_rejects_non_zip(self, client) -> None:
        """Non-zip file returns 422."""
        resp = client.post(
            "/api/backup/restore",
            files={"file": ("backup.txt", b"not a zip", "text/plain")},
        )
        assert resp.status_code == 422

    def test_rejects_no_marker(self, client, pm) -> None:
        """Valid zip without .faugus_marker returns 422."""
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("somefile.txt", "data")
        resp = client.post(
            "/api/backup/restore",
            files={"file": ("backup.zip", buf.getvalue(), "application/zip")},
        )
        assert resp.status_code == 422

    def test_restore_valid_backup(self, client, pm) -> None:
        """Valid backup zip is restored."""
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(".faugus_marker", "faugus-launcher-backup")
            z.writestr("config.ini", 'close-onlaunch="True"\n')
        resp = client.post(
            "/api/backup/restore",
            files={"file": ("backup.zip", buf.getvalue(), "application/zip")},
        )
        assert resp.status_code == 200
        assert resp.json()["restored"] is True
