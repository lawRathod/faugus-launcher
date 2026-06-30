"""Pytest configuration and shared fixtures for Faugus Launcher tests."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Force headless mode for tests so the gi mock is always installed
os.environ.setdefault("FAUGUS_TEST_HEADLESS", "1")


# --- gi (PyGObject) mock ----------------------------------------------------
# We mock the GTK/GLib stack so that test collection can import the launcher
# module on a headless system (no display server). Tests that exercise real
# GTK widgets should be marked @pytest.mark.gui and skipped in headless runs.

try:
    import gi  # noqa: F401
    HAS_GI = True
except ImportError:
    HAS_GI = False


def _install_gi_mock():
    """Install a MagicMock-based stub for gi.* and faugus.config_manager.

    Lets us import faugus.launcher in a headless environment. Methods called
    on the mocks are auto-generated, so tests can configure return values per
    test case.
    """
    sys.modules["gi"] = MagicMock()
    sys.modules["gi.repository"] = MagicMock()
    # Sub-modules commonly accessed via gi.repository.* need to be mockable too
    gi_repo = sys.modules["gi.repository"]
    for name in (
        "Gtk", "Gdk", "GLib", "GdkPixbuf", "Pango",
        "AyatanaAppIndicator3", "GObject",
    ):
        setattr(gi_repo, name, MagicMock())


if not HAS_GI or os.environ.get("FAUGUS_TEST_HEADLESS") == "1":
    _install_gi_mock()


# --- Path isolation ---------------------------------------------------------

@pytest.fixture
def tmp_config_dir(tmp_path, monkeypatch):
    """Redirect all PathManager user paths to a temporary directory.

    Tests that read/write config.ini, games.json, latest-games.txt, etc.
    should use this fixture so they never touch the real user config.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / ".local" / "share"))
    monkeypatch.setenv("XDG_DATA_DIRS", str(tmp_path / ".local" / "share"))
    return tmp_path


@pytest.fixture
def sample_games_json(tmp_config_dir):
    """Write a small games.json to the temp config dir and return its path."""
    config_dir = tmp_config_dir / ".config" / "faugus-launcher"
    config_dir.mkdir(parents=True, exist_ok=True)
    games_file = config_dir / "games.json"
    games_file.write_text("[]")
    return games_file


@pytest.fixture
def sample_latest_games(tmp_config_dir):
    """Write a latest-games.txt with some entries and return its path."""
    config_dir = tmp_config_dir / ".config" / "faugus-launcher"
    config_dir.mkdir(parents=True, exist_ok=True)
    latest_file = config_dir / "latest-games.txt"
    latest_file.write_text("game-a\ngame-b\ngame-c\n")
    return latest_file
