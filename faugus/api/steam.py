"""Steam API — detect Steam, list installed games, manage shortcuts.

Wraps ``steam_setup`` helpers at call time.  The GTK-free ``steam``
instance avoids pulling PyGObject into the server process.
"""

from __future__ import annotations

import os
from pathlib import Path

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


@router.post("/api/steam/shortcut")
def steam_shortcut(body: ShortcutAction) -> dict:
    """Add or remove a Steam shortcut for a game.

    TODO: implement VDF read/write for shortcuts.vdf.
    """
    try:
        ss = _get_steam()
        version = ss.detect_steam_version()
    except Exception as exc:
        raise HTTPException(503, f"Steam detection error: {exc}")

    if version is None:
        raise HTTPException(503, "Steam not detected on this system.")

    return {"status": f"{body.action}ed shortcut for '{body.title}'"}
