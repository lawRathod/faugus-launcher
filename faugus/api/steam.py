"""Steam API — detect Steam, list installed games, manage shortcuts.

Wraps ``steam_setup`` helpers at call time.  The GTK-free ``steam``
instance avoids pulling PyGObject into the server process.
"""

from __future__ import annotations

import os
from pathlib import Path

import vdf

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ── Lazy steam module (cached, no GTK dependency) ───────────────────────

_steam_module = None


def _get_steam():
    """Lazy-import steam_setup, cached after first load."""
    global _steam_module
    if _steam_module is None:
        import faugus.steam_setup as ss
        _steam_module = ss
    return _steam_module


# ── GTK-free icon lookup (replaces get_steam_icon_path which uses GdkPixbuf)


def _steam_icon_path(appid: str, librarycache: Path | None) -> str:
    """Return the largest .jpg icon for a Steam app, GTK-free.

    Uses file size as a proxy for resolution — avoids importing GdkPixbuf.
    """
    if librarycache is None:
        return ""
    cachedir = librarycache / str(appid)
    if not cachedir.is_dir():
        return ""

    candidates: list[tuple[int, Path]] = []
    for img in cachedir.rglob("*.jpg"):
        name = img.name
        if name in ("header.jpg", "library_600x900.jpg", "library_capsule.jpg"):
            continue
        try:
            size = os.path.getsize(img)
            candidates.append((size, img))
        except OSError:
            continue

    if not candidates:
        return ""
    candidates.sort(key=lambda x: x[0])
    return str(candidates[-1][1])


# ── Models ──────────────────────────────────────────────────────────────


class ShortcutAction(BaseModel):
    gameid: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9._-]+$")
    title: str = Field(..., min_length=1)
    path: str = Field("", description="Game directory (reserved for VDF impl)")
    action: str = Field("add", pattern="^(add|remove)$")


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("/api/steam/status")
def steam_status() -> dict:
    """Detect Steam installation and return status."""
    try:
        ss = _get_steam()
        version = ss.detect_steam_version()
        sid = ss.detect_steam_id()
        return {
            "version": version,
            "steam_id": sid,
            "shortcuts_path": str(ss.steam_shortcuts_path) if ss.steam_shortcuts_path else None,
        }
    except Exception as exc:
        raise HTTPException(503, f"Steam detection error: {exc}")


@router.get("/api/steam/games")
def steam_games() -> list[dict]:
    """List installed Steam games from appmanifest files."""
    try:
        ss = _get_steam()
        librarycache = ss.librarycache
        return [
            {
                "appid": appid,
                "name": name,
                "icon": _steam_icon_path(appid, librarycache),
            }
            for appid, name in ss.read_installed_games()
        ]
    except Exception as exc:
        raise HTTPException(503, f"Steam games error: {exc}")




def _add_shortcut(shortcuts: dict, title: str, exe: str, start_dir: str, launch_opts: str, icon: str) -> dict:
    """Add or update a Steam shortcut entry."""
    existing_id = None
    for app_id, game in shortcuts.get("shortcuts", {}).items():
        if isinstance(game, dict) and game.get("AppName") == title:
            existing_id = app_id
            break

    if existing_id:
        game = shortcuts["shortcuts"][existing_id]
        game.update({
            "Exe": exe,
            "StartDir": start_dir,
            "LaunchOptions": launch_opts,
            "icon": icon,
        })
        return shortcuts

    new_id = max([int(k) for k in shortcuts.get("shortcuts", {}).keys() if k.isdigit()] or [0]) + 1
    shortcuts.setdefault("shortcuts", {})[str(new_id)] = {
        "appid": new_id,
        "AppName": title,
        "Exe": exe,
        "StartDir": start_dir,
        "icon": icon,
        "ShortcutPath": "",
        "LaunchOptions": launch_opts,
        "IsHidden": 0,
        "AllowDesktopConfig": 1,
        "AllowOverlay": 1,
        "OpenVR": 0,
        "Devkit": 0,
        "DevkitGameID": "",
        "LastPlayTime": 0,
        "FlatpakAppID": "",
    }
    return shortcuts


def _remove_shortcut(shortcuts: dict, title: str) -> dict:
    """Remove a Steam shortcut by title."""
    to_remove = [
        app_id for app_id, game in shortcuts.get("shortcuts", {}).items()
        if isinstance(game, dict) and game.get("AppName") == title
    ]
    for app_id in to_remove:
        del shortcuts["shortcuts"][app_id]
    return shortcuts


def _build_exe_and_launch(gameid: str, launcher_path: str, is_steam_flatpak: bool, is_flatpak: bool) -> tuple[str, str]:
    """Build Exe and LaunchOptions for the Steam shortcut."""
    if is_flatpak:
        if is_steam_flatpak:
            exe = '"flatpak-spawn"'
            launch = f'--host flatpak run --command={launcher_path} io.github.Faugus.faugus-launcher --game {gameid}'
        else:
            exe = '"flatpak"'
            launch = f'run --command={launcher_path} io.github.Faugus.faugus-launcher --game {gameid}'
    else:
        if is_steam_flatpak:
            exe = '"flatpak-spawn"'
            launch = f'--host {launcher_path} --game {gameid}'
        else:
            exe = f'"{launcher_path}"'
            launch = f'--game {gameid}'
    return exe, launch


@router.post("/api/steam/shortcut")
def steam_shortcut(body: ShortcutAction) -> dict:
    """Add or remove a Steam shortcut for a game."""
    try:
        ss = _get_steam()
        version = ss.detect_steam_version()
    except Exception as exc:
        raise HTTPException(503, f"Steam detection error: {exc}")

    if version is None:
        raise HTTPException(503, "Steam not detected on this system.")

    shortcuts_path = ss.steam_shortcuts_path
    if not shortcuts_path:
        raise HTTPException(503, "Steam shortcuts path not found.")

    # Load existing shortcuts
    try:
        if os.path.isfile(shortcuts_path):
            with open(shortcuts_path, "rb") as f:
                shortcuts = vdf.binary_load(f)
        else:
            shortcuts = {"shortcuts": {}}
    except SyntaxError:
        shortcuts = {"shortcuts": {}}

    # Build paths
    from faugus.path_manager import IS_FLATPAK, launcher_path

    exe, launch_opts = _build_exe_and_launch(
        body.gameid,
        launcher_path or "faugus-launcher",
        getattr(ss, "IS_STEAM_FLATPAK", False),
        IS_FLATPAK,
    )

    if body.action == "add":
        game_dir = body.path or os.path.expanduser("~")
        icon = f"{launcher_path}.png" if launcher_path else ""
        shortcuts = _add_shortcut(shortcuts, body.title, exe, game_dir, launch_opts, icon)
    elif body.action == "remove":
        shortcuts = _remove_shortcut(shortcuts, body.title)

    # Save
    os.makedirs(os.path.dirname(shortcuts_path), exist_ok=True)
    with open(shortcuts_path, "wb") as f:
        vdf.binary_dump(shortcuts, f)

    return {"status": f"{body.action}ed shortcut for '{body.title}'"}
