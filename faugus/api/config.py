"""Config API — read/write config.ini.

Defaults are sourced from a static copy of ConfigManager.default_config.
I/O is handled directly (not through ConfigManager) to avoid stale-import
issues in tests.  File locking ensures concurrent safety.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from fastapi import APIRouter
from pydantic import BaseModel

from faugus import path_manager as pm

router = APIRouter()

# ── File locking (same pattern as games.py) ────────────────────────────

import fcntl


@contextmanager
def _locked_config() -> Iterator[dict[str, str]]:
    """Read config.ini under exclusive file lock.

    Tracks whether the dict was modified and only writes when dirty.
    """
    path = pm.config_file_dir
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            raw = f.read()
            config = _parse_ini(raw) if raw.strip() else {}
            original = dict(config)
            yield config
            if config != original:
                f.seek(0)
                f.truncate()
                _write_ini(f, config)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


# ── INI helpers (ConfigManager-compatible format) ──────────────────────

# Hardcoded defaults — keep in sync with ../config_manager.py:ConfigManager.default_config
_CONFIG_DEFAULTS: dict[str, str] = {
    "close-onlaunch": "False",
    "default-prefix": "",
    "mangohud": "False",
    "gamemode": "False",
    "disable-hidraw": "False",
    "prevent-sleep": "False",
    "default-runner": "Proton-CachyOS Latest",
    "lossless-location": "",
    "discrete-gpu": "False",
    "splash-disable": "False",
    "system-tray": "False",
    "start-boot": "False",
    "mono-icon": "False",
    "interface-mode": "List",
    "show-labels": "False",
    "enable-logging": "False",
    "wayland-driver": "False",
    "enable-wow64": "False",
    "language": "en_US",
    "logging-warning": "False",
    "show-hidden": "False",
    "disable-updates": "False",
    "show-donate": "True",
    "donate-last": "",
    "playtime": "0",
    "gamepad-navigation": "False",
    "start-minimized": "False",
    "show-categories": "False",
    "backup-auto-enabled": "False",
    "backup-frequency": "daily",
    "backup-target-day": "0",
    "backup-dest-dir": "",
    "backup-last-date": "",
    "window-behavior": "None",
    "width": "1280",
    "height": "720",
    "banner-size": "100",
    "sort": "alpha",
    "category": "all",
}
_VALID_KEYS = frozenset(_CONFIG_DEFAULTS)


class ConfigUpdate(BaseModel):
    """Arbitrary key-value config update.

    Only keys in ``_VALID_KEYS`` are accepted; unknown keys return 422.
    """
    key_values: dict[str, str]


def _parse_ini(raw: str) -> dict[str, str]:
    """Parse config.ini lines into a dict."""
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip().strip('"')
    return result


def _write_ini(f: Any, config: dict[str, str]) -> None:
    """Write config dict to an open file in ConfigManager format."""
    for key, value in config.items():
        if key in ("default-prefix", "default-runner"):
            f.write(f'{key}="{value}"\n')
        else:
            f.write(f"{key}={value}\n")


def _read_raw(path: str) -> str:
    """Read file contents, returning empty string if missing."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""


# ── endpoints ───────────────────────────────────────────────────────────


@router.get("/api/config")
def get_config() -> dict[str, str]:
    """Return all configuration key-value pairs."""
    raw = _read_raw(pm.config_file_dir)
    file_config = _parse_ini(raw) if raw.strip() else {}
    result = dict(_CONFIG_DEFAULTS)
    result["default-prefix"] = pm.prefixes_dir
    result.update(file_config)
    return result


@router.put("/api/config")
def update_config(body: ConfigUpdate) -> dict[str, str]:
    """Update configuration key-value pairs.

    Only known keys (matching ConfigManager.default_config) are accepted.
    Unknown keys are silently ignored.
    """
    with _locked_config() as config:
        for key, value in body.key_values.items():
            if key.strip() and key in _VALID_KEYS:
                config[key] = str(value)
        # Return with defaults merged in (file-only config lacks defaults)
        result = dict(_CONFIG_DEFAULTS)
        result["default-prefix"] = pm.prefixes_dir
        result.update(config)
        return result
