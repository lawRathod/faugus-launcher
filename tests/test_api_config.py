"""Tests for the Config API — TDD Red-Green cycle."""

import os


class TestGetConfig:
    """GET /api/config"""

    def test_returns_defaults(self, client) -> None:
        """No config file yet → returns defaults."""
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["close-onlaunch"] == "False"
        assert data["default-runner"] == "Proton-CachyOS Latest"
        assert data["interface-mode"] == "List"

    def test_returns_custom_value(self, client, pm) -> None:
        """Config file on disk is reflected in response."""
        config_dir = os.path.dirname(pm.config_file_dir)
        os.makedirs(config_dir, exist_ok=True)
        with open(pm.config_file_dir, "w") as f:
            f.write('close-onlaunch="True"\n')
            f.write('default-runner="GE-Proton"\n')
        resp = client.get("/api/config")
        assert resp.status_code == 200
        assert resp.json()["close-onlaunch"] == "True"
        assert resp.json()["default-runner"] == "GE-Proton"


class TestPutConfig:
    """PUT /api/config"""

    def test_update_single_value(self, client) -> None:
        """Update a single config key."""
        resp = client.put("/api/config", json={"key_values": {"close-onlaunch": "True"}})
        assert resp.status_code == 200
        assert resp.json()["close-onlaunch"] == "True"

    def test_update_persists_to_disk(self, client) -> None:
        """Updated values survive a server re-read."""
        client.put("/api/config", json={"key_values": {"close-onlaunch": "True", "interface-mode": "Banners"}})
        resp = client.get("/api/config")
        assert resp.json()["close-onlaunch"] == "True"
        assert resp.json()["interface-mode"] == "Banners"

    def test_unknown_key_ignored(self, client) -> None:
        """Unknown config keys are silently ignored."""
        initial = client.get("/api/config").json()
        resp = client.put("/api/config", json={"key_values": {"nonexistent": "value"}})
        assert resp.status_code == 200
        assert resp.json() == initial

    def test_partial_update_preserves_others(self, client) -> None:
        """Updating one key doesn't clobber others."""
        client.put("/api/config", json={"key_values": {"close-onlaunch": "True", "mangohud": "True"}})
        resp = client.put("/api/config", json={"key_values": {"mangohud": "False"}})
        assert resp.json()["close-onlaunch"] == "True"
        assert resp.json()["mangohud"] == "False"

    def test_empty_key_ignored(self, client) -> None:
        """Empty key is silently ignored."""
        initial = client.get("/api/config").json()
        resp = client.put("/api/config", json={"key_values": {"": "value"}})
        assert resp.status_code == 200
        assert resp.json() == initial

    def test_empty_body(self, client) -> None:
        """Empty key_values dict is a no-op."""
        initial = client.get("/api/config").json()
        resp = client.put("/api/config", json={"key_values": {}})
        assert resp.status_code == 200
        assert resp.json() == initial

    def test_no_write_when_nothing_changed(self, client, pm) -> None:
        """PUT with unchanged values doesn't write to disk (mtime preserved)."""
        # First, write an initial config
        client.put("/api/config", json={"key_values": {"close-onlaunch": "True"}})
        initial_mtime = os.path.getmtime(pm.config_file_dir)
        # PUT the same value
        client.put("/api/config", json={"key_values": {"close-onlaunch": "True"}})
        after_mtime = os.path.getmtime(pm.config_file_dir)
        assert after_mtime == initial_mtime
