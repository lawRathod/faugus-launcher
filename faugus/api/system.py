"""System API — version info and running game status."""

from __future__ import annotations

from fastapi import APIRouter

VERSION = "1.22.7"

router = APIRouter()


def _running():
    from faugus.path_manager import running_games
    from faugus.utils import load_json_file
    data = load_json_file(running_games, {})
    return data if data else {}


@router.get("/api/system/status")
def system_status() -> dict:
    """Return server version and running game processes."""
    return {
        "version": VERSION,
        "running_games": _running(),
    }
