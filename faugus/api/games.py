"""Games CRUD API.

Every endpoint reads/writes games.json — the canonical game library file.
All read-modify-write operations use a file lock to prevent corruption
from concurrent requests.

Field names match the canonical GAME_FIELDS in faugus/utils.py:
  path               — .exe path
  launch_arguments   — UMU / Proton launch arguments
  game_arguments     — arguments passed to the game binary
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from contextlib import contextmanager
from typing import Any, Iterator

from fastapi import APIRouter, HTTPException, Query

from faugus.api.models import (
    CategoryUpdate,
    CustomOrderRequest,
    DuplicateRequest,
    GameCreate,
    GameResponse,
    GameUpdate,
)
from faugus import path_manager as pm
from faugus.runner_core import build_launch_command
from faugus.utils import format_title, save_json_file

router = APIRouter()


# ── file locking ─────────────────────────────────────────────────────────

# We can't import fcntl on non-Unix, but this app is Linux-only.
import fcntl


@contextmanager
def _locked_games() -> Iterator[list[dict]]:
    """Read games.json under an exclusive file lock.

    On exit, writes the (possibly modified) list back to disk.
    If the file doesn't exist, yields an empty list and creates it.
    """
    path = pm.games_json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            raw = f.read()
            games: list[dict] = json.loads(raw) if raw.strip() else []
            yield games
            f.seek(0)
            f.truncate()
            json.dump(games, f, indent=4, ensure_ascii=False)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


@contextmanager
def _locked_running() -> Iterator[dict[str, int]]:
    """Read running_games.json under an exclusive file lock."""
    path = pm.running_games
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            raw = f.read()
            running: dict[str, int] = json.loads(raw) if raw.strip() else {}
            yield running
            f.seek(0)
            f.truncate()
            json.dump(running, f, indent=4)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


# ── helpers ──────────────────────────────────────────────────────────────


def _normalize_categories(raw: Any) -> list[str]:
    """Canonicalise the category field from any legacy format.

    Existing games.json entries may have:
      - ``False`` (boolean) — uncategorised
      - ``"RTS"`` (str) — single legacy category
      - ``["RTS", "FPS"]`` (list) — current format
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        return [raw] if raw else []
    # False, None, 0, or anything else
    return []


def _game_response(g: dict) -> dict:
    """Convert an internal game dict to the API response shape."""
    return {
        "gameid": g.get("gameid", ""),
        "title": g.get("title", ""),
        "path": g.get("path", ""),
        "prefix": g.get("prefix", ""),
        "launch_arguments": g.get("launch_arguments", ""),
        "game_arguments": g.get("game_arguments", ""),
        "runner": g.get("runner", ""),
        "protonfix": g.get("protonfix", ""),
        "icon": g.get("icon", ""),
        "banner": g.get("banner", ""),
        "category": _normalize_categories(g.get("category", [])),
        "hidden": g.get("hidden", False),
        "mangohud": g.get("mangohud", ""),
        "gamemode": g.get("gamemode", ""),
        "disable_hidraw": g.get("disable_hidraw", ""),
        "prevent_sleep": g.get("prevent_sleep", False),
        "playtime": g.get("playtime", 0),
        "lastplayed": g.get("lastplayed", 0),
        "addapp_checkbox": g.get("addapp_checkbox", ""),
        "addapp": g.get("addapp", ""),
        "addapp_bat": g.get("addapp_bat", ""),
        "addapp_delay": g.get("addapp_delay", ""),
        "addapp_first": g.get("addapp_first", ""),
        "lossless_enabled": g.get("lossless_enabled", ""),
        "lossless_multiplier": g.get("lossless_multiplier", ""),
        "lossless_flow": g.get("lossless_flow", ""),
        "lossless_performance": g.get("lossless_performance", ""),
        "lossless_hdr": g.get("lossless_hdr", ""),
        "lossless_present": g.get("lossless_present", ""),
        "settings": g.get("settings", {}),
    }


def _title_to_gameid(title: str) -> str:
    """Generate a filesystem-safe game ID from a title."""
    return format_title(title)


_NEW_GAME_DEFAULTS: dict[str, Any] = {
    "launch_arguments": "",
    "game_arguments": "",
    "runner": "",
    "protonfix": "",
    "icon": "",
    "banner": "",
    "category": [],
    "hidden": False,
    "mangohud": "",
    "gamemode": "",
    "disable_hidraw": "",
    "prevent_sleep": False,
    "playtime": 0,
    "lastplayed": 0,
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


# ── endpoints (static routes before {gameid} to avoid greedy match) ──────


@router.get("/api/games", response_model=list[GameResponse])
def list_games(
    search: str = Query(""),
    sort: str = Query("alpha"),
    category: str = Query(""),
    hidden: bool = Query(False),
) -> list[dict]:
    """List games with optional filtering and sorting."""
    with _locked_games() as games:
        # Filter hidden
        if not hidden:
            games = [g for g in games if not g.get("hidden", False)]

        # Search filter (case-insensitive title substring)
        if search:
            sl = search.lower()
            games = [g for g in games if sl in g.get("title", "").lower()]

        # Category filter
        if category:
            if category == "_uncategorized":
                games = [
                    g for g in games
                    if not _normalize_categories(g.get("category", []))
                ]
            else:
                games = [
                    g for g in games
                    if category in _normalize_categories(g.get("category", []))
                ]

        # Sort
        if sort == "alpha":
            games.sort(key=lambda g: g.get("title", "").lower())

        return [_game_response(g) for g in games]


@router.post("/api/games", status_code=201, response_model=GameResponse)
def create_game(body: GameCreate) -> dict:
    """Create a new game entry."""
    title = body.title.strip()
    gameid = _title_to_gameid(title)

    with _locked_games() as games:
        # Duplicate check
        if any(g.get("title", "").lower() == title.lower() for g in games):
            raise HTTPException(409, f"Game '{title}' already exists.")
        if any(g.get("gameid") == gameid for g in games):
            raise HTTPException(409, f"Game ID '{gameid}' already exists.")

        record = dict(_NEW_GAME_DEFAULTS)
        record["gameid"] = gameid
        record["lastplayed"] = int(time.time())
        record.update(body.model_dump())
        # Booleans → string convention for mangohud/gamemode/disable_hidraw
        for bf in ("mangohud", "gamemode", "disable_hidraw"):
            if bf in body.model_dump(exclude_unset=True):
                record[bf] = True if getattr(body, bf) else ""
        games.append(record)
        return _game_response(record)


# ── static sub-routes (must come before {gameid}) ────────────────────────


@router.get("/api/games/status", response_model=dict)
def running_status() -> dict:
    """Return currently running game processes."""
    with _locked_running() as running:
        return dict(running)


@router.put("/api/games/custom-order")
def save_custom_order(body: CustomOrderRequest) -> dict:
    """Persist drag-and-drop custom sort order."""
    save_json_file(dict(body.order), pm.custom_order)
    return {"saved": True}


# ── per-game routes ──────────────────────────────────────────────────────


@router.get("/api/games/{gameid}", response_model=GameResponse)
def get_game(gameid: str) -> dict:
    """Get a single game by ID."""
    with _locked_games() as games:
        for g in games:
            if g.get("gameid") == gameid:
                return _game_response(g)
    raise HTTPException(404, "Game not found.")


@router.put("/api/games/{gameid}", response_model=GameResponse)
def update_game(gameid: str, body: GameUpdate) -> dict:
    """Update an existing game.

    Fields provided in the request body overwrite matching fields.
    Fields NOT in the body (e.g. mangohud, lossless_*, addapp_*) are
    preserved from the existing record — no data loss.
    """
    with _locked_games() as games:
        for i, g in enumerate(games):
            if g.get("gameid") == gameid:
                # Start from existing record then apply client fields.
                # Fields NOT sent by the client (their value matches the
                # model default and the existing record has a real value)
                # are preserved from the original.
                updated = dict(g)
                body_fields = body.model_dump(exclude_unset=True)
                updated.update(body_fields)
                # gameid is always from the URL
                updated["gameid"] = gameid
                games[i] = updated
                return _game_response(updated)
    raise HTTPException(404, "Game not found.")


@router.delete("/api/games/{gameid}")
def delete_game(gameid: str) -> dict:
    """Delete a game entry."""
    with _locked_games() as games:
        for i, g in enumerate(games):
            if g.get("gameid") == gameid:
                removed = games.pop(i)
                return {"deleted": removed.get("title")}
    raise HTTPException(404, "Game not found.")


@router.post("/api/games/{gameid}/duplicate", status_code=201, response_model=GameResponse)
def duplicate_game(gameid: str, body: DuplicateRequest) -> dict:
    """Duplicate a game with a new title."""
    new_title = body.title.strip()
    new_id = _title_to_gameid(new_title)

    with _locked_games() as games:
        # Find source
        source = None
        for g in games:
            if g.get("gameid") == gameid:
                source = g
                break
        if source is None:
            raise HTTPException(404, "Game not found.")

        # Duplicate check
        if any(x.get("title", "").lower() == new_title.lower() for x in games):
            raise HTTPException(409, f"Game '{new_title}' already exists.")

        record = dict(source)
        record["gameid"] = new_id
        record["title"] = new_title
        record["playtime"] = 0
        record["lastplayed"] = 0
        games.append(record)
        return _game_response(record)


@router.patch("/api/games/{gameid}/hide", response_model=GameResponse)
def toggle_hidden(gameid: str) -> dict:
    """Toggle the hidden flag on a game."""
    with _locked_games() as games:
        for g in games:
            if g.get("gameid") == gameid:
                g["hidden"] = not g.get("hidden", False)
                return _game_response(g)
    raise HTTPException(404, "Game not found.")


@router.patch("/api/games/{gameid}/category", response_model=GameResponse)
def set_category(gameid: str, body: CategoryUpdate) -> dict:
    """Set categories for a game."""
    with _locked_games() as games:
        for g in games:
            if g.get("gameid") == gameid:
                g["category"] = body.categories
                return _game_response(g)
    raise HTTPException(404, "Game not found.")


@router.post("/api/games/{gameid}/launch")
def launch_game(gameid: str) -> dict:
    """Launch a game via the UMU runner.

    Builds the launch command using ``runner_core.build_launch_command``
    and spawns the process.  The PID is recorded in
    ``running_games.json`` for lifecycle tracking.  A daemon reaper
    thread cleans up the entry when the process exits.
    """
    # Prevent double-launch
    with _locked_running() as running:
        if gameid in running:
            raise HTTPException(409, f"Game '{gameid}' is already running.")

    with _locked_games() as games:
        game = None
        for g in games:
            if g.get("gameid") == gameid:
                game = g
                break
    if game is None:
        raise HTTPException(404, "Game not found.")

    command = build_launch_command(game)
    cwd = None
    game_dir = os.path.dirname(game.get("path", ""))
    if game_dir and os.path.isdir(game_dir):
        cwd = game_dir

    proc = subprocess.Popen(command, shell=True, cwd=cwd)

    with _locked_running() as running:
        running[gameid] = proc.pid

    # Daemon reaper — cleans up running_games.json when process exits
    def _reaper(pid: int, gid: str) -> None:
        try:
            os.waitpid(pid, 0)
        except (ChildProcessError, OSError):
            try:
                os.kill(pid, 0)
            except OSError:
                pass  # already dead
        with _locked_running() as running:
            running.pop(gid, None)

    import threading
    threading.Thread(target=_reaper, args=(proc.pid, gameid), daemon=True).start()

    return {"process_id": proc.pid, "status": "launching"}


@router.post("/api/games/{gameid}/kill")
def kill_game(gameid: str) -> dict:
    """Kill a running game process."""
    with _locked_running() as running:
        pid = running.get(gameid)
        if pid is None:
            raise HTTPException(404, "Game not found or not running.")
        if not isinstance(pid, int):
            raise HTTPException(500, "Corrupted running_games.json: expected int PID")

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # already dead
    except Exception as exc:
        raise HTTPException(500, f"Failed to kill process {pid}: {exc}")

    with _locked_running() as running:
        running.pop(gameid, None)

    return {"killed": gameid}
