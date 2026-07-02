"""Pure utility functions with no UI dependencies.

These functions were extracted from faugus/utils.py to create a clean
separation between business logic and UI code. They handle:
- JSON file I/O
- Recents management
- Game data serialization
- View filtering
- String formatting
- Environment building
- Icon extraction
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def ensure_parent_dir(path):
    """Create parent directories for a file path if they don't exist."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_json_file(filepath, default=None):
    """Load a JSON file and return its contents.

    Returns ``default`` (or empty list) if the file is missing or malformed.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []


def save_json_file(data, filepath, indent=4):
    """Write data to a JSON file, creating parent directories as needed."""
    ensure_parent_dir(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Recents
# ---------------------------------------------------------------------------

def load_recents(recents_file):
    """Load the recents.json file and return ``{gameid: timestamp}``.

    Returns an empty dict if the file is missing, empty, or malformed.
    """
    data = load_json_file(recents_file, {})
    if not isinstance(data, dict):
        return {}
    return {str(k): float(v) for k, v in data.items() if isinstance(v, (int, float))}


def save_recents(recents_file, recents):
    """Write the ``{gameid: timestamp}`` map to recents.json atomically."""
    save_json_file(recents, recents_file, indent=2)


def touch_recent(recents_file, gameid):
    """Record that ``gameid`` was just launched.

    Loads the existing map, sets ``gameid`` to the current epoch time,
    and writes the result back. Returns the updated dict.
    """
    recents = load_recents(recents_file)
    recents[gameid] = time.time()
    save_recents(recents_file, recents)
    return recents


def clear_recents(recents_file):
    """Remove the recents file (no-op if it doesn't exist)."""
    try:
        if os.path.exists(recents_file):
            os.remove(recents_file)
    except OSError:
        pass


def format_recent_age(timestamp, now=None):
    """Return a short human-readable age string for a recents timestamp.

    Examples: ``"just now"``, ``"5 min ago"``, ``"2 h ago"``,
    ``"yesterday"``, ``"3 d ago"``, ``"2 w ago"``.

    Anything older than ~6 months returns ``None`` so the caller can hide
    the label instead of showing a long, unhelpful string.
    """
    if timestamp is None:
        return None
    if now is None:
        now = time.time()
    delta = now - float(timestamp)
    if delta < 0:
        return "just now"
    if delta < 60:
        return "just now"
    if delta < 3600:
        return f"{int(delta // 60)} min ago"
    if delta < 86400:
        return f"{int(delta // 3600)} h ago"
    days = int(delta // 86400)
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days} d ago"
    weeks = days // 7
    if weeks < 26:
        return f"{weeks} w ago"
    return None


# ---------------------------------------------------------------------------
# Game data helpers
# ---------------------------------------------------------------------------

GAME_FIELDS = [
    "gameid", "title", "path", "prefix",
    "launch_arguments", "game_arguments",
    "mangohud", "gamemode", "disable_hidraw",
    "protonfix", "runner",
    "addapp_checkbox", "addapp", "addapp_bat", "addapp_delay", "addapp_first",
    "banner",
    "lossless_enabled", "lossless_multiplier", "lossless_flow",
    "lossless_performance", "lossless_hdr", "lossless_present",
    "playtime", "hidden", "prevent_sleep", "category", "icon", "favorite",
]

GAME_DEFAULTS = {
    "playtime": 0, "hidden": False, "prevent_sleep": False,
    "category": False, "icon": "", "favorite": False,
}


def game_to_dict(game):
    """Serialize a Game object to a dict using GAME_FIELDS."""
    return {field: getattr(game, field) for field in GAME_FIELDS}


def game_to_save_dict(game, hidden=None):
    """Serialize a Game for persistence, normalizing boolean fields."""
    d = {**game_to_dict(game),
         "mangohud": True if game.mangohud else "",
         "gamemode": True if game.gamemode else "",
         "disable_hidraw": True if game.disable_hidraw else "",
         "addapp_checkbox": "addapp_enabled" if game.addapp_checkbox else ""}
    if hidden is not None:
        d["hidden"] = hidden
    return d


def prepare_game_kwargs(data):
    """Build a kwargs dict for Game construction from a raw JSON dict.

    Fills in defaults for any missing fields so Game.__init__ never
    raises on legacy games.json entries.
    """
    defaults = {f: "" for f in GAME_FIELDS}
    defaults.update(GAME_DEFAULTS)
    return {f: data.get(f, defaults[f]) for f in GAME_FIELDS}


def set_favorite_in_json(games_file, gameid, favorite):
    """Set the favorite flag for one game in games.json.

    Returns True if a matching game was found and updated, False otherwise.
    Does not raise on missing/corrupt files.
    """
    data = load_json_file(games_file, [])
    updated = False
    for entry in data:
        if isinstance(entry, dict) and entry.get("gameid") == gameid:
            entry["favorite"] = bool(favorite)
            updated = True
            break
    if updated:
        save_json_file(data, games_file)
    return updated


def update_games_json(games_file, icons_dir):
    """Migrate legacy games.json entries (icon paths, runner names)."""
    games = load_json_file(games_file, None)
    if games is None:
        return

    changed = False

    for game in games:
        if game.get("runner") == "Proton-CachyOS":
            game["runner"] = "Proton-CachyOS (System)"
            changed = True

        game_id = game.get("gameid")
        if game_id:
            new_icon_path = os.path.join(icons_dir, f"{game_id}.ico")
            if game.get("icon") != new_icon_path:
                game["icon"] = new_icon_path
                changed = True

    if changed:
        save_json_file(games, games_file)


# ---------------------------------------------------------------------------
# View filtering
# ---------------------------------------------------------------------------

VIEW_LIBRARY = "library"
VIEW_RECENTS = "recents"
VIEW_FAVORITES = "favorites"
VALID_VIEWS = (VIEW_LIBRARY, VIEW_RECENTS, VIEW_FAVORITES)


def view_filter_matches(game, view, recent_ids, search_text=""):
    """Decide whether a game passes the sidebar view filter.

    Args:
        game: dict-like with keys ``gameid``, ``title``, ``favorite``.
        view: one of ``"library"``, ``"recents"``, ``"favorites"``.
        recent_ids: iterable of gameids currently listed in latest-games.txt.
        search_text: lowercased substring the title must contain.

    Returns:
        True if the game should be visible under the given view.
    """
    if view == VIEW_RECENTS:
        return game.get("gameid") in set(recent_ids)
    if view == VIEW_FAVORITES:
        return bool(game.get("favorite"))
    return True


def normalize_view(value):
    """Return a valid view name, defaulting to library for unknown inputs."""
    if value in VALID_VIEWS:
        return value
    return VIEW_LIBRARY


# ---------------------------------------------------------------------------
# String formatting
# ---------------------------------------------------------------------------

def format_title(title):
    """Convert a game title to a URL-friendly slug."""
    title = title.strip().lower()
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"\s+", "-", title)
    return title


def version_key(v):
    """Sort key for version strings (e.g. 'GE-Proton9-5' -> [9, '-', 5])."""
    cleaned = re.sub(r'^[^\d]+', '', v)
    parts = re.split(r'(\d+)', cleaned)
    return [int(p) if p.isdigit() else p for p in parts]


# ---------------------------------------------------------------------------
# Environment building
# ---------------------------------------------------------------------------

def build_lossless_env(lossless_enabled, lossless_multiplier, lossless_flow,
                       lossless_performance, lossless_hdr, lossless_present):
    """Build LSFG/LSFGVK environment variable list for Lossless Scaling."""
    parts = []
    if not lossless_enabled:
        return parts
    parts.append("LSFG_LEGACY=1")
    parts.append("LSFGVK_ENV=1")
    if lossless_multiplier:
        parts.append(f"LSFG_MULTIPLIER={lossless_multiplier}")
        parts.append(f"LSFGVK_MULTIPLIER={lossless_multiplier}")
    if lossless_flow:
        parts.append(f"LSFG_FLOW_SCALE={lossless_flow/100}")
        parts.append(f"LSFGVK_FLOW_SCALE={lossless_flow/100}")
    if lossless_performance:
        parts.append("LSFG_PERFORMANCE_MODE=1")
        parts.append("LSFGVK_PERFORMANCE_MODE=1")
    else:
        parts.append("LSFG_PERFORMANCE_MODE=0")
        parts.append("LSFGVK_PERFORMANCE_MODE=0")
    if lossless_hdr:
        parts.append("LSFG_HDR_MODE=1")
    else:
        parts.append("LSFG_HDR_MODE=0")
    if lossless_present:
        parts.append(f"LSFG_EXPERIMENTAL_PRESENT_MODE={lossless_present}")
    return parts


# ---------------------------------------------------------------------------
# BAT file generation
# ---------------------------------------------------------------------------

def write_addapp_bat(bat_path, exe_path, addapp, addapp_delay, addapp_first, game_arguments):
    """Write a Windows .bat file for launching an addapp + game."""
    with open(bat_path, "w") as f:
        f.write('@echo off\n')
        if not addapp_first:
            if game_arguments:
                f.write(f'start "" "z:{exe_path}" {game_arguments}\n')
            else:
                f.write(f'start "" "z:{exe_path}"\n')
            if addapp_delay:
                f.write(f'ping -n {addapp_delay} 127.0.0.1 >nul\n')
            f.write(f'start "" "z:{addapp}"\n')
        else:
            f.write(f'start "" "z:{addapp}"\n')
            if addapp_delay:
                f.write(f'ping -n {addapp_delay} 127.0.0.1 >nul\n')
            if game_arguments:
                f.write(f'start "" "z:{exe_path}" {game_arguments}\n')
            else:
                f.write(f'start "" "z:{exe_path}"\n')


# ---------------------------------------------------------------------------
# Icon extraction (no GTK dependency)
# ---------------------------------------------------------------------------

def extract_ico_simple(exe_path, output_path):
    """Extract the best icon from a Windows executable.

    Returns "ok", "no_icons", or "error".
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        ensure_parent_dir(output_path)
        temp_ico = os.path.join(tmp_dir, "icon.ico")

        result = subprocess.run(
            ['icoextract', exe_path, temp_ico],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            if "NoIconsAvailableError" in result.stderr or "PEFormatError" in result.stderr:
                return "no_icons"
            return "error"

        magick = shutil.which("magick") or shutil.which("convert")
        if not magick:
            return "error"

        subprocess.run(
            [magick, temp_ico, "-resize", "256x256!", output_path], check=True
        )
        return "ok"

    except Exception:
        return "error"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def extract_ico_frames(exe_path, output_path):
    """Extract all icon frames from a Windows executable and pick the largest.

    Returns "ok", "no_icons", or "error".
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        ensure_parent_dir(output_path)
        temp_ico = os.path.join(tmp_dir, "icon.ico")

        result = subprocess.run(
            ['icoextract', exe_path, temp_ico],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            if "NoIconsAvailableError" in result.stderr or "PEFormatError" in result.stderr:
                return "no_icons"
            return "error"

        magick = shutil.which("magick") or shutil.which("convert")
        if not magick:
            return "error"

        subprocess.run(
            [magick, temp_ico, os.path.join(tmp_dir, "frame_%d.png")],
            capture_output=True
        )

        if os.path.isfile(temp_ico):
            os.remove(temp_ico)

        def get_index(filepath):
            match = re.search(r'frame_(\d+)\.png', filepath.name)
            return int(match.group(1)) if match else 999

        png_files = sorted(Path(tmp_dir).glob("frame_*.png"), key=get_index)
        if not png_files:
            return "error"

        best, size = None, 0
        for f in png_files:
            r = subprocess.run(
                [magick, "identify", "-format", "%wx%h", str(f)],
                capture_output=True, text=True
            )
            if r.returncode == 0 and r.stdout:
                w, h = map(int, r.stdout.strip().split("x"))
                current_size = w * h
                if current_size > size:
                    best, size = str(f), current_size

        if best:
            subprocess.run(
                [magick, best, "-resize", "256x256!", output_path], check=True
            )
            return "ok"

        return "error"

    except Exception:
        return "error"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

def is_apple_silicon():
    """Detect if running on Apple Silicon (Asahi Linux)."""
    path = "/proc/device-tree/compatible"
    if not os.path.exists(path):
        return False
    try:
        with open(path, "rb") as f:
            dtcompat = f.read().decode('utf-8', errors='ignore')
            return "apple,arm-platform" in dtcompat
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Addon defaults
# ---------------------------------------------------------------------------

def init_addon_defaults(obj):
    """Initialize addon-related attributes on an object with safe defaults."""
    obj.addapp_enabled = False
    obj.addapp = ""
    obj.addapp_delay = ""
    obj.addapp_first = False
    obj.launch_arguments = ""
    obj.lossless_enabled = False
    obj.lossless_multiplier = 1
    obj.lossless_flow = 100
    obj.lossless_performance = False
    obj.lossless_hdr = False
    obj.lossless_present = False


# ---------------------------------------------------------------------------
# Runner list building
# ---------------------------------------------------------------------------

def build_runner_list(proton_cachyos_path, compatibility_dir_path):
    """Build the list of available Proton runners.

    Returns a list of runner name strings, with the default first.
    """
    runners = [
        "Proton-CachyOS Latest (default)",
        "GE-Proton Latest",
        "Proton-EM Latest",
        "DW-Proton Latest",
        "UMU-Proton Latest",
    ]

    if os.path.exists(proton_cachyos_path):
        runners.append("Proton-CachyOS (System)")

    try:
        if os.path.exists(compatibility_dir_path):
            versions = []
            for entry in os.listdir(compatibility_dir_path):
                entry_path = os.path.join(compatibility_dir_path, entry)
                if (
                    os.path.isdir(entry_path)
                    and entry not in ("UMU-Latest", "LegacyRuntime")
                    and not entry.startswith("Proton-GE Latest")
                    and not entry.startswith("Proton-EM Latest")
                    and not entry.startswith("DW-Proton Latest")
                    and not entry.startswith("Proton-CachyOS Latest")
                ):
                    versions.append(entry)

            versions.sort(key=version_key, reverse=True)
            runners.extend(versions)
    except Exception:
        pass

    return runners
