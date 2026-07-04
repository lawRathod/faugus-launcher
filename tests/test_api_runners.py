"""Tests for the Runners API — TDD Red-Green cycle."""

import os


class TestListRunners:
    """GET /api/runners"""

    def test_returns_list(self, client) -> None:
        """Returns a list of runners (may be empty in CI)."""
        resp = client.get("/api/runners")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_detects_installed_runners(self, client, pm) -> None:
        """Creates fake runner dirs and verifies detection."""
        compat_dir = pm.compatibility_dir
        os.makedirs(f"{compat_dir}/GE-Proton-8.0", exist_ok=True)
        os.makedirs(f"{compat_dir}/Proton-Experimental", exist_ok=True)
        resp = client.get("/api/runners")
        names = [r["name"] for r in resp.json()]
        assert "GE-Proton-8.0" in names
        assert "Proton-Experimental" in names

    def test_runner_entry_has_expected_fields(self, client, pm) -> None:
        """Each runner has name, path, and is_latest."""
        compat_dir = pm.compatibility_dir
        os.makedirs(f"{compat_dir}/Test-Proton-1.0", exist_ok=True)
        resp = client.get("/api/runners")
        runner = next(r for r in resp.json() if r["name"] == "Test-Proton-1.0")
        assert runner["name"] == "Test-Proton-1.0"
        assert runner["path"].endswith("Test-Proton-1.0")
        assert "is_latest" in runner
        assert "type" in runner


    def test_type_detection_by_name_prefix(self, client, pm) -> None:
        """Runner type is correctly inferred from directory name prefix."""
        compat_dir = pm.compatibility_dir
        os.makedirs(f"{compat_dir}/GE-Proton-8.31")
        os.makedirs(f"{compat_dir}/Proton-CachyOS-42.0")
        os.makedirs(f"{compat_dir}/Proton-EM-1.0")
        os.makedirs(f"{compat_dir}/proton-EM-2.0")
        os.makedirs(f"{compat_dir}/EM-3.0")
        os.makedirs(f"{compat_dir}/DW-Proton-1.0")
        os.makedirs(f"{compat_dir}/Vanilla-Proton-1.0")
        resp = client.get("/api/runners")
        by_name = {r["name"]: r["type"] for r in resp.json()}
        assert by_name["GE-Proton-8.31"] == "ge"
        assert by_name["Proton-CachyOS-42.0"] == "cachyos"
        assert by_name["Proton-EM-1.0"] == "em"
        assert by_name["proton-EM-2.0"] == "em"
        assert by_name["EM-3.0"] == "em"
        assert by_name["DW-Proton-1.0"] == "dw"
        assert by_name["Vanilla-Proton-1.0"] == "proton"


class TestListRunnerVariants:
    """GET /api/runners/latest — returns latest available versions from GitHub"""

    def test_returns_variant_list(self, client) -> None:
        """Returns list of known runner variants."""
        resp = client.get("/api/runners/latest")
        assert resp.status_code == 200
        variants = resp.json()
        assert isinstance(variants, list)
        # At minimum cachyos and ge should be present
        keys = [v["key"] for v in variants]
        assert "cachyos" in keys
        assert "ge" in keys

    def test_each_variant_has_expected_fields(self, client) -> None:
        """Each variant has key, display_name, and latest_version."""
        resp = client.get("/api/runners/latest")
        for variant in resp.json():
            assert "key" in variant
            assert "display_name" in variant
            # latest_version may be None if API unreachable, but field exists
            assert "latest_version" in variant
