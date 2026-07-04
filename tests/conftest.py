"""Shared fixtures for Faugus Launcher API tests.

Uses Starlette's synchronous TestClient so no pytest-asyncio needed.
"""

import os
import json
import importlib
import shutil
from pathlib import Path

import pytest
from starlette.testclient import TestClient


def _clean_path_module():
    """Force path_manager to re-resolve paths from current env vars."""
    import faugus.path_manager as pm
    importlib.reload(pm)
    return pm


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect all XDG paths to a temp directory.

    Every test gets a fresh home, so games.json / config.ini start empty.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    yield home


@pytest.fixture
def pm(isolated_home: Path) -> type:
    """Reloaded path_manager module with test-isolated paths."""
    return _clean_path_module()


@pytest.fixture
def games_path(pm) -> Path:
    """Path to games.json in the isolated temp home. Dir pre-created."""
    p = Path(pm.games_json)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@pytest.fixture
def running_games_path(pm) -> Path:
    """Path to running_games.json in the isolated temp home. Dir pre-created."""
    p = Path(pm.running_games)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@pytest.fixture
def sample_game() -> dict:
    return {
        "gameid": "test-game-1",
        "title": "Test Game",
        "path": "/home/test/game.exe",
        "prefix": "/home/test/prefix",
        "launch_arguments": "",
        "game_arguments": "",
        "runner": "",
        "protonfix": "",
        "icon": "",
        "banner": "",
        "category": [],
        "hidden": False,
        "playtime": 0,
        "lastplayed": 0,
        "mangohud": "",
        "gamemode": "",
        "disable_hidraw": "",
        "prevent_sleep": False,
        "addapp_checkbox": "",
        "addapp": "",
        "addapp_bat": "",
        "addapp_delay": "",
        "addapp_first": "",
        "lossless_enabled": "",
        "lossless_multiplier": "",
        "lossless_flow": "",
        "lossless_performance": "",
        "lossless_hdr": "",
        "lossless_present": "",
        "settings": {},
    }


@pytest.fixture
def client(pm) -> TestClient:
    """Starlette TestClient, isolated from real config.

    Reloads ``config_manager`` in addition to ``path_manager`` so that
    the config_file_dir path is correctly set to the test temp directory.
    """
    import faugus.config_manager as cm
    import importlib
    importlib.reload(cm)
    from faugus.server import app
    return TestClient(app)
