"""Games CRUD API.

Every endpoint reads/writes games.json using the existing project utilities.
"""

import json
import os
import signal
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from faugus.api.models import (
    CategoryUpdate,
    CustomOrderRequest,
    DuplicateRequest,
    GameCreate,
    GameUpdate,
)
from faugus import path_manager as pm
from faugus.utils import format_title, load_json_file, save_json_file

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────

def _load_games() -> list[dict]:
    """Load games list from disk."""
    data = load_json_file(pm.games_json, [])
    if data is None:
        return []
    return data


def _save_games(games: list[dict]) -> None:
    """Save games list to disk."""
    os.makedirs(os.path.dirname(pm.games_json), exist_ok=True)
    save_json_file(games, pm.games_json)


def _find_game(gameid: str) -> dict | None:
    for g in _load_games():
        if g.get("gameid") == gameid:
            return g
    return None


def _game_response(g: dict) -> dict:
    """Convert internal game dict to API response shape."""
    return {
        "gameid": g.get("gameid", ""),
        "title": g.get("title", ""),
        "exe": g.get("exe", ""),
        "path": g.get("path", ""),
        "args": g.get("args", ""),
        "runner": g.get("runner", ""),
        "prefix": g.get("prefix", ""),
        "icon": g.get("icon", ""),
        "banner": g.get("banner", ""),
        "category": g.get("category", []),
        "hidden": g.get("hidden", False),
        "playtime": g.get("playtime", 0),
        "lastplayed": g.get("lastplayed", 0),
        "settings": g.get("settings", {}),
    }


def _title_to_gameid(title: str) -> str:
    """Generate a filesystem-safe game ID from a title."""
    return format_title(title)


def _load_running() -> dict[str, int | dict]:
    data = load_json_file(pm.running_games, {})
    return data if data else {}


def _save_running(data: dict) -> None:
    os.makedirs(os.path.dirname(pm.running_games), exist_ok=True)
    save_json_file(data, pm.running_games)


# ── endpoints (static routes before {gameid} to avoid greedy match) ──────


@router.get("/api/games")
def list_games(
    search: str = Query(""),
    sort: str = Query("alpha"),
    category: str = Query(""),
    hidden: int = Query(0),
) -> list[dict]:
    """List games with optional filtering and sorting."""
    games = _load_games()

    if not hidden:
        games = [g for g in games if not g.get("hidden", False)]

    if search:
        sl = search.lower()
        games = [g for g in games if sl in g.get("title", "").lower()]

    if category:
        if category == "_uncategorized":
            games = [g for g in games if not g.get("category") or g["category"] == []]
        else:
            games = [g for g in games if category in g.get("category", [])]

    if sort == "alpha":
        games.sort(key=lambda g: g.get("title", "").lower())

    return [_game_response(g) for g in games]


@router.post("/api/games", status_code=201)
def create_game(body: GameCreate) -> dict:
    """Create a new game entry."""
    games = _load_games()
    title = body.title.strip()
    gameid = _title_to_gameid(title)

    if any(g.get("title", "").lower() == title.lower() for g in games):
        raise HTTPException(409, f"Game '{title}' already exists.")
    if any(g.get("gameid") == gameid for g in games):
        raise HTTPException(409, f"Game ID '{gameid}' already exists.")

    record: dict[str, Any] = {
        "gameid": gameid,
        "title": title,
        "exe": body.exe,
        "path": body.path,
        "args": body.args or "",
        "runner": body.runner or "",
        "prefix": body.prefix,
        "icon": body.icon or "",
        "banner": body.banner or "",
        "category": body.category or [],
        "hidden": body.hidden,
        "playtime": 0,
        "lastplayed": 0,
        "settings": body.settings or {},
    }
    games.append(record)
    _save_games(games)
    return _game_response(record)


# ── static sub-routes (must come before {gameid}) ────────────────────────


@router.get("/api/games/status")
def running_status() -> dict:
    """Return currently running game processes."""
    return _load_running()


@router.put("/api/games/custom-order")
def save_custom_order(body: CustomOrderRequest) -> dict:
    """Persist drag-and-drop custom sort order."""
    os.makedirs(os.path.dirname(pm.custom_order), exist_ok=True)
    with open(pm.custom_order, "w") as f:
        json.dump(body.order, f)
    return {"saved": True}


# ── per-game routes ──────────────────────────────────────────────────────


@router.get("/api/games/{gameid}")
def get_game(gameid: str) -> dict:
    """Get a single game by ID."""
    g = _find_game(gameid)
    if g is None:
        raise HTTPException(404, "Game not found.")
    return _game_response(g)


@router.put("/api/games/{gameid}")
def update_game(gameid: str, body: GameUpdate) -> dict:
    """Update an existing game."""
    games = _load_games()
    for i, g in enumerate(games):
        if g.get("gameid") == gameid:
            games[i] = {
                "gameid": gameid,
                "title": body.title.strip(),
                "exe": body.exe,
                "path": body.path,
                "args": body.args or "",
                "runner": body.runner or "",
                "prefix": body.prefix,
                "icon": body.icon or "",
                "banner": body.banner or "",
                "category": body.category or [],
                "hidden": body.hidden,
                "playtime": g.get("playtime", 0),
                "lastplayed": g.get("lastplayed", 0),
                "settings": body.settings or {},
            }
            _save_games(games)
            return _game_response(games[i])
    raise HTTPException(404, "Game not found.")


@router.delete("/api/games/{gameid}")
def delete_game(gameid: str) -> dict:
    """Delete a game entry."""
    games = _load_games()
    for i, g in enumerate(games):
        if g.get("gameid") == gameid:
            removed = games.pop(i)
            _save_games(games)
            return {"deleted": removed.get("title")}
    raise HTTPException(404, "Game not found.")


@router.post("/api/games/{gameid}/duplicate", status_code=201)
def duplicate_game(gameid: str, body: DuplicateRequest) -> dict:
    """Duplicate a game with a new title."""
    g = _find_game(gameid)
    if g is None:
        raise HTTPException(404, "Game not found.")

    games = _load_games()
    new_title = body.title.strip()
    new_id = _title_to_gameid(new_title)

    if any(x.get("title", "").lower() == new_title.lower() for x in games):
        raise HTTPException(409, f"Game '{new_title}' already exists.")

    record = dict(g)
    record["gameid"] = new_id
    record["title"] = new_title
    record["playtime"] = 0
    record["lastplayed"] = 0
    games.append(record)
    _save_games(games)
    return _game_response(record)


@router.patch("/api/games/{gameid}/hide")
def toggle_hidden(gameid: str) -> dict:
    """Toggle the hidden flag on a game."""
    games = _load_games()
    for g in games:
        if g.get("gameid") == gameid:
            g["hidden"] = not g.get("hidden", False)
            _save_games(games)
            return _game_response(g)
    raise HTTPException(404, "Game not found.")


@router.patch("/api/games/{gameid}/category")
def set_category(gameid: str, body: CategoryUpdate) -> dict:
    """Set categories for a game."""
    games = _load_games()
    for g in games:
        if g.get("gameid") == gameid:
            g["category"] = body.categories
            _save_games(games)
            return _game_response(g)
    raise HTTPException(404, "Game not found.")


@router.post("/api/games/{gameid}/launch")
def launch_game(gameid: str) -> dict:
    """Launch a game via the UMU runner (stub — Phase 0)."""
    g = _find_game(gameid)
    if g is None:
        raise HTTPException(404, "Game not found.")
    return {"process_id": 0, "status": "error", "detail": "runner_core not implemented"}


@router.post("/api/games/{gameid}/kill")
def kill_game(gameid: str) -> dict:
    """Kill a running game process."""
    running = _load_running()
    pid = running.pop(gameid, None)
    if pid is None:
        raise HTTPException(404, "Game not found or not running.")
    try:
        os.kill(pid, signal.SIGUSR1)
    except ProcessLookupError:
        pass
    _save_running(running)
    return {"killed": gameid}
