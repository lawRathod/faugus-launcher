#!/usr/bin/env python3
"""Core game launch logic — no GTK dependency.

Extracted from :mod:`faugus.runner` during Phase 0.2 to allow the API
server and headless ``faugus-run`` to launch games without importing GTK.

Usage::

    python -m faugus.runner_core --game <gameid>
    python -m faugus.runner_core "ENV=VALUE umu-run ..."
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time

from faugus.ea_fix import update_ea_path
from faugus.path_manager import (
    IS_FLATPAK,
    PathManager,
    compatibility_dir,
    gamemoderun,
    games_json,
    logs_dir,
    mangohud_dir,
    proton_cachyos,
    umu_run,
)
from faugus.steam_setup import IS_STEAM_FLATPAK
from faugus.utils import (
    build_lossless_env,
    load_json_file,
    save_json_file,
)

# ── Environment tracking ────────────────────────────────────────────────

_env_set: set[str] = set()


def set_env(key: str, value: str) -> None:
    """Set an environment variable and track it for logging."""
    os.environ[key] = value
    _env_set.add(key)


# ── Game launch command builder ────────────────────────────────────────


def build_launch_command(game: dict) -> str:
    """Build a single UMU launch command string from a game record.

    The returned string is a shell command composed of environment
    variables and the UMU runner invocation.
    """
    gameid = game.get("gameid", "")
    path = game.get("path", "")
    prefix = game.get("prefix", "")
    launch_arguments = game.get("launch_arguments", "")
    game_arguments = game.get("game_arguments", "")
    protonfix = game.get("protonfix", "")
    runner = game.get("runner", "")
    addapp_bat = game.get("addapp_bat", "")
    mangohud = game.get("mangohud", "")
    gamemode = game.get("gamemode", "")
    disable_hidraw = game.get("disable_hidraw", "")
    prevent_sleep = game.get("prevent_sleep", "")
    addapp_checkbox = game.get("addapp_checkbox", "")
    lossless_enabled = game.get("lossless_enabled", "")
    lossless_multiplier = game.get("lossless_multiplier", "")
    lossless_flow = game.get("lossless_flow", "")
    lossless_performance = game.get("lossless_performance", "")
    lossless_hdr = game.get("lossless_hdr", "")
    lossless_present = game.get("lossless_present", "")
    icon = game.get("icon", "")

    if gameid == "ea-app":
        path = update_ea_path(prefix)

    command_parts: list[str] = []

    if icon:
        command_parts.append(f"SPLASHICON={icon}")
    if gameid:
        command_parts.append(f"LOG_DIR='{gameid}'")
        command_parts.append(f"FAUGUSID={gameid}")
    if disable_hidraw:
        command_parts.append("PROTON_DISABLE_HIDRAW=1")
    if prevent_sleep:
        command_parts.append("PREVENT_SLEEP=1")
    if protonfix:
        command_parts.append(f"GAMEID={protonfix}")
    if runner:
        if runner == "Linux-Native":
            command_parts.append("PROTONPATH=umu-sniper")
        elif runner == "Proton-CachyOS (System)":
            command_parts.append(f"WINEPREFIX={shlex.quote(prefix)}")
            command_parts.append(f"PROTONPATH={proton_cachyos}")
        else:
            command_parts.append(f"WINEPREFIX={shlex.quote(prefix)}")
            command_parts.append(f"PROTONPATH='{runner}'")
    else:
        command_parts.append(f"WINEPREFIX={shlex.quote(prefix)}")

    command_parts.extend(
        build_lossless_env(lossless_enabled, lossless_multiplier, lossless_flow,
                          lossless_performance, lossless_hdr, lossless_present)
    )

    if launch_arguments:
        command_parts.append(os.path.expanduser(launch_arguments))

    if gamemode and os.path.exists(gamemoderun):
        command_parts.append("gamemoderun")
    if mangohud and os.path.exists(mangohud_dir):
        command_parts.append("mangohud")

    if runner != "Steam":
        command_parts.append(f"'{umu_run}'")

    if addapp_checkbox == "addapp_enabled":
        command_parts.append(shlex.quote(addapp_bat))
    else:
        if runner != "Steam":
            command_parts.append(shlex.quote(path))
        else:
            steam_args = "-nobigpicture -nochatui -nofriendsui -silent -applaunch"
            if IS_FLATPAK:
                if IS_STEAM_FLATPAK:
                    command_parts.append(
                        f"flatpak-spawn --host flatpak run com.valvesoftware.Steam {steam_args} {path}")
                else:
                    command_parts.append(f"flatpak-spawn --host steam {steam_args} {path}")
            else:
                if IS_STEAM_FLATPAK:
                    command_parts.append(
                        f"flatpak run com.valvesoftware.Steam {steam_args} {path}")
                else:
                    command_parts.append(f"steam {steam_args} {path}")

    if game_arguments:
        command_parts.append(game_arguments)

    return " ".join(command_parts)


# ── JSON loader ─────────────────────────────────────────────────────────


def load_game_from_json(gameid: str) -> dict | None:
    """Load a single game record from ``games.json`` by ID."""
    games = load_json_file(games_json, None)
    if games is None:
        return None
    for game in games:
        if game.get("gameid") == gameid:
            return game
    return None


# ── Apple Silicon detection ─────────────────────────────────────────────


def is_apple_silicon() -> bool:
    """Detect Apple Silicon (for muvm wrapping on Linux)."""
    path = "/proc/device-tree/compatible"
    if not os.path.exists(path):
        return False
    try:
        with open(path, "rb") as f:
            dtcompat = f.read().decode("utf-8", errors="ignore")
        return "apple,arm-platform" in dtcompat
    except Exception:
        return False


# ── CLI entry point ─────────────────────────────────────────────────────


def run_headless(args: argparse.Namespace) -> None:
    """Launch a game without the GTK splash/log window."""
    if args.game:
        game = load_game_from_json(args.game)
        if not game:
            print(f"Game '{args.game}' not found in games.json", file=sys.stderr)
            sys.exit(1)
        command = build_launch_command(game)
    else:
        command = args.message or ""

    print(f"=== UMU-LAUNCHER COMMAND ===")
    print(f"{command}\n")
    sys.stdout.flush()

    proc = subprocess.Popen(command, shell=True)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


def main() -> None:
    """CLI entry point for headless game launch."""
    if is_apple_silicon() and "FAUGUS_MUVM" not in os.environ:
        import shutil
        muvm_path = shutil.which("muvm")
        if muvm_path:
            env = os.environ.copy()
            args = [muvm_path, "-i", "-e", "FAUGUS_MUVM=1",
                    sys.executable, os.path.abspath(__file__)]
            os.execvpe(muvm_path, args + sys.argv[1:], env)

    parser = argparse.ArgumentParser(description="Faugus Launcher — headless game runner")
    parser.add_argument("message", nargs="?", default="", help="Launch command string")
    parser.add_argument("command", nargs="?", default=None, help="Sub-command (legacy)")
    parser.add_argument("--game", help="Game ID to launch from games.json")
    args = parser.parse_args()
    run_headless(args)


if __name__ == "__main__":
    main()
