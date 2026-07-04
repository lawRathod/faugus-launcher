"""Tests for the Files API — TDD Red-Green cycle."""

import os
import json


class TestBrowse:
    """GET /api/files/browse"""

    def test_returns_list(self, client) -> None:
        """Returns a list of directory entries."""
        resp = client.get("/api/files/browse", params={"path": "/tmp"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_entry_has_expected_fields(self, client) -> None:
        """Each entry has name, path, type, size."""
        resp = client.get("/api/files/browse", params={"path": "/tmp"})
        entries = resp.json()
        if entries:
            assert "name" in entries[0]
            assert "path" in entries[0]
            assert "type" in entries[0]
            assert "size" in entries[0]

    def test_rejects_path_traversal(self, client) -> None:
        """Path with '..' returns 422."""
        resp = client.get("/api/files/browse", params={"path": "/tmp/../../etc"})
        assert resp.status_code == 422

    def test_nonexistent_directory(self, client) -> None:
        """Non-existent path returns empty list."""
        resp = client.get("/api/files/browse", params={"path": "/nonexistent_dir_xyzzy"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_browses_nested_files(self, client, tmp_path) -> None:
        """A real directory with files is listed correctly."""
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "file.txt").write_text("hello")
        (sub / "script.sh").write_text("#!/bin/sh")
        resp = client.get("/api/files/browse", params={"path": str(sub)})
        entries = resp.json()
        names = [e["name"] for e in entries]
        assert "file.txt" in names
        assert "script.sh" in names

    def test_type_field_distinguishes_file_and_dir(self, client, tmp_path) -> None:
        """type is 'file' or 'dir'."""
        (tmp_path / "afile").write_text("x")
        (tmp_path / "adir").mkdir()
        resp = client.get("/api/files/browse", params={"path": str(tmp_path)})
        by_name = {e["name"]: e["type"] for e in resp.json()}
        assert by_name.get("afile") == "file"
        assert by_name.get("adir") == "dir"


# Test PNG data: starts with valid PNG magic bytes
# Full validation is not needed — endpoint only checks magic + size
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_TEST_PNG = _PNG_MAGIC + b"\x00\x00\x00\x0dIHDR... stub data"


class TestUploadIcon:
    """POST /api/files/icon"""

    def test_upload_valid(self, client, pm) -> None:
        """Upload a valid PNG icon returns the saved path."""
        resp = client.post(
            "/api/files/icon",
            files={"file": ("icon.png", _TEST_PNG, "image/png")},
            data={"gameid": "test-game"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "path" in data
        assert data["path"].endswith(".ico") or data["path"].endswith(".png")
        import os
        assert os.path.isfile(data["path"])

    def test_rejects_non_image(self, client) -> None:
        """Non-image file returns 422."""
        resp = client.post(
            "/api/files/icon",
            files={"file": ("bad.txt", b"not an image", "text/plain")},
            data={"gameid": "test-game"},
        )
        assert resp.status_code == 422

    def test_rejects_no_gameid(self, client) -> None:
        """Missing gameid returns 422."""
        resp = client.post(
            "/api/files/icon",
            files={"file": ("icon.png", _TEST_PNG, "image/png")},
        )
        assert resp.status_code == 422

    def test_rejects_huge_file(self, client) -> None:
        """File over size limit returns 422."""
        huge = b"x" * (11 * 1024 * 1024)  # 11 MB
        resp = client.post(
            "/api/files/icon",
            files={"file": ("big.png", huge, "image/png")},
            data={"gameid": "test-game"},
        )
        assert resp.status_code == 422


class TestUploadBanner:
    """POST /api/files/banner"""

    def test_upload_valid(self, client, pm) -> None:
        """Upload a valid PNG banner returns the saved path."""
        resp = client.post(
            "/api/files/banner",
            files={"file": ("banner.png", _TEST_PNG, "image/png")},
            data={"gameid": "test-game"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "path" in data
        assert os.path.isfile(data["path"])

    def test_rejects_non_image(self, client) -> None:
        """Non-image file returns 422."""
        resp = client.post(
            "/api/files/banner",
            files={"file": ("bad.txt", b"not an image", "text/plain")},
            data={"gameid": "test-game"},
        )
        assert resp.status_code == 422

    def test_rejects_huge_file(self, client) -> None:
        """File over size limit returns 422."""
        huge = b"x" * (21 * 1024 * 1024)  # 21 MB
        resp = client.post(
            "/api/files/banner",
            files={"file": ("big.png", huge, "image/png")},
            data={"gameid": "test-game"},
        )
        assert resp.status_code == 422


class TestPrefixSuggest:
    """GET /api/files/prefix-suggest"""

    def test_suggests_based_on_title(self, client) -> None:
        """Returns a suggested prefix path for a game title."""
        resp = client.get("/api/files/prefix-suggest", params={"title": "My Game"})
        assert resp.status_code == 200
        data = resp.json()
        assert "prefix" in data
        assert data["prefix"].endswith("my-game")
