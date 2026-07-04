"""Pure-python utility functions (no GTK dependency).

GTK-dependent helpers have been moved to :mod:`faugus.gtk_utils`.
The API server and runner_core import only from this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from faugus.path_manager import games_json


# ═══════════════════════════════════════════════════════════════════════
# File I/O helpers
# ═══════════════════════════════════════════════════════════════════════


def ensure_parent_dir(path: str) -> None:
    """Create parent directories for *path* if they don't exist."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_json_file(filepath: str, default: Any = None) -> Any:
    """Load a JSON file, returning *default* on error."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json_file(data: Any, filepath: str, indent: int = 4) -> None:
    """Save *data* as JSON to *filepath*, creating parent directories."""
    ensure_parent_dir(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════
# Game / title helpers
# ═══════════════════════════════════════════════════════════════════════


def format_title(title: str) -> str:
    """Convert a game title to a filesystem-safe identifier."""
    safe = re.sub(r"[^\w\s-]", "", title).strip().lower()
    safe = re.sub(r"[\s_]+", "-", safe)
    return safe or hashlib.md5(title.encode()).hexdigest()[:8]


def game_to_dict(game: object) -> dict[str, Any]:
    """Convert a Game object to a dict (canonical field order)."""
    return {field: getattr(game, field) for field in GAME_FIELDS}


def game_to_save_dict(game: object, hidden: bool | None = None) -> dict[str, Any]:
    """Convert a Game object to a saveable dict with proper type coercion."""
    d: dict[str, Any] = {**game_to_dict(game)}
    d["mangohud"] = True if getattr(game, "mangohud", False) else ""
    d["gamemode"] = True if getattr(game, "gamemode", False) else ""
    d["disable_hidraw"] = True if getattr(game, "disable_hidraw", False) else ""
    d["addapp_checkbox"] = "addapp_enabled" if getattr(game, "addapp_checkbox", False) else ""
    if hidden is not None:
        d["hidden"] = hidden
    return d


def prepare_game_kwargs(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare keyword arguments for Game() constructor from JSON data."""
    defaults: dict[str, Any] = {f: "" for f in GAME_FIELDS}
    defaults.update({
        "playtime": 0,
        "hidden": False,
        "prevent_sleep": False,
        "category": False,
        "icon": "",
    })
    return {f: data.get(f, defaults[f]) for f in GAME_FIELDS}


def init_addon_defaults(obj: object) -> None:
    """Set default addon/launch argument attributes on an object."""
    obj.addapp_enabled = False
    obj.addapp = ""
    obj.addapp_delay = ""
    obj.addapp_first = False
    obj.launch_arguments = ""
    obj.lossless_enabled = False
    obj.lossless_multiplier = ""
    obj.lossless_flow = ""
    obj.lossless_performance = ""
    obj.lossless_hdr = False
    obj.lossless_present = False
    obj.checkbox_mangohud = None
    obj.checkbox_gamemode = None
    obj.checkbox_disable_hidraw = None
    obj.checkbox_prevent_sleep = None


GAME_FIELDS = [
    "gameid", "title", "path", "prefix",
    "launch_arguments", "game_arguments",
    "mangohud", "gamemode", "disable_hidraw",
    "protonfix", "runner",
    "addapp_checkbox", "addapp", "addapp_bat", "addapp_delay", "addapp_first",
    "banner",
    "lossless_enabled", "lossless_multiplier", "lossless_flow",
    "lossless_performance", "lossless_hdr", "lossless_present",
    "playtime", "hidden", "prevent_sleep", "category", "icon",
]

# ═══════════════════════════════════════════════════════════════════════
# Lossless / addapp / env helpers
# ═══════════════════════════════════════════════════════════════════════


def build_lossless_env(lossless_enabled, lossless_multiplier, lossless_flow,
                       lossless_performance, lossless_hdr, lossless_present):
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

def write_addapp_bat(bat_path, exe_path, addapp, addapp_delay, addapp_first, game_arguments):
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

# ═══════════════════════════════════════════════════════════════════════
# Icon / extraction helpers (GTK-free)
# ═══════════════════════════════════════════════════════════════════════


def is_valid_image(file_path: str) -> bool:
    """Check if *file_path* is a valid image (by extension + magic bytes).

    GTK-free replacement for the original that used GdkPixbuf.
    """
    if not os.path.isfile(file_path):
        return False
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".ico", ".svg"):
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        if ext in (".jpg", ".jpeg"):
            return header.startswith(b"\xff\xd8")
        if ext == ".png":
            return header.startswith(b"\x89PNG")
        if ext == ".ico":
            return header.startswith(b"\x00\x00\x01\x00")
        if ext == ".svg":
            return b"<svg" in header.lower()
        return True
    except OSError:
        return False


def extract_ico_simple(exe_path, output_path):
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
                print("The file does not contain icons.")
                return "no_icons"
            print(f"Error extracting icon: {result.stderr}")
            return "error"

        magick = shutil.which("magick") or shutil.which("convert")
        if not magick:
            return "error"

        subprocess.run(
            [magick, temp_ico, "-resize", "256x256!", output_path], check=True
        )
        return "ok"

    except Exception as e:
        print(f"An error occurred: {e}")
        return "error"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

def extract_ico_frames(exe_path, output_path):
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
                print("The file does not contain icons.")
                return "no_icons"
            print(f"Error extracting icon: {result.stderr}")
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

    except Exception as e:
        print(f"An error occurred: {e}")
        return "error"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

# ═══════════════════════════════════════════════════════════════════════
# Version / sorting helpers
# ═══════════════════════════════════════════════════════════════════════


def version_key(v):
    cleaned = re.sub(r'^[^\d]+', '', v)
    parts = re.split(r'(\d+)', cleaned)
    return [int(p) if p.isdigit() else p for p in parts]

# ═══════════════════════════════════════════════════════════════════════
# games.json maintenance
# ═══════════════════════════════════════════════════════════════════════


def update_games_json():
    games = load_json_file(games_json, None)
    if games is None:
        return

    changed = False

    icons_dir = PathManager.user_config('faugus-launcher/icons')

    for game in games:
        if game.get("runner") == "Proton-CachyOS":
            game["runner"] = "Proton-CachyOS (System)"
            changed = True

        if "favorite" in game:
            if game["favorite"] == True:
                game["category"] = False

            game.pop("favorite")
            changed = True

        game_id = game.get("gameid")

        if game_id:
            new_icon_path = os.path.join(icons_dir, f"{game_id}.ico")

            if game.get("icon") != new_icon_path:
                game["icon"] = new_icon_path
                changed = True

    if changed:
        save_json_file(games, games_json)

__all__ = [
    "GAME_FIELDS",
    "build_lossless_env",
    "ensure_parent_dir",
    "extract_ico_frames",
    "extract_ico_simple",
    "format_title",
    "game_to_dict",
    "game_to_save_dict",
    "init_addon_defaults",
    "is_valid_image",
    "load_json_file",
    "prepare_game_kwargs",
    "save_json_file",
    "update_games_json",
    "version_key",
    "write_addapp_bat",
]
