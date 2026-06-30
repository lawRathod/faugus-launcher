"""Pytest configuration and shared fixtures for Faugus Launcher tests.

We use the *real* PyGObject / GTK3 stack, which can be imported and class-
introspected on a headless system (no DISPLAY required). Tests that actually
instantiate GTK windows should be marked @pytest.mark.gui and skipped via
`pytest -m "not gui"` in headless CI.
"""
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Use a non-X11 GDK backend where possible so widget construction doesn't
# require a display. This still allows importing GTK classes and constructing
# pure-Python objects that don't touch a display server.
os.environ.setdefault("GDK_BACKEND", "broadway")


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
