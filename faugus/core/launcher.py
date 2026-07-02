"""Game launch command building.

Builds the UMU-Launcher command string for a game, handling all
environment variables, proton paths, and special cases.
"""

import os
import shlex

from faugus.core.utils import build_lossless_env


def build_launch_command(game, *, proton_cachyos_path, compatibility_dir,
                         umu_run_path, mangohud_path, gamemoderun_path,
                         is_flatpak, is_steam_flatpak, ea_fix_fn=None):
    """Build the complete launch command for a game.

    Args:
        game: dict-like with game configuration keys.
        proton_cachyos_path: Path to the system Proton-CachyOS.
        compatibility_dir: Path to Steam compatibilitytools.d.
        umu_run_path: Path to the umu-run script.
        mangohud_path: Path to mangohud binary (or empty).
        gamemoderun_path: Path to gamemoderun binary (or empty).
        is_flatpak: Whether running in Flatpak.
        is_steam_flatpak: Whether Steam is installed as Flatpak.
        ea_fix_fn: Optional callable to fix EA App paths.

    Returns:
        A shell command string ready for subprocess execution.
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

    if gameid == "ea-app" and ea_fix_fn:
        path = ea_fix_fn(prefix)

    command_parts = []

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
            command_parts.append('PROTONPATH=umu-sniper')
        elif runner == "Proton-CachyOS (System)":
            command_parts.append(f"WINEPREFIX={shlex.quote(prefix)}")
            command_parts.append(f"PROTONPATH={proton_cachyos_path}")
        else:
            command_parts.append(f"WINEPREFIX={shlex.quote(prefix)}")
            command_parts.append(f"PROTONPATH='{runner}'")
    else:
        command_parts.append(f"WINEPREFIX={shlex.quote(prefix)}")

    command_parts.extend(build_lossless_env(
        lossless_enabled, lossless_multiplier, lossless_flow,
        lossless_performance, lossless_hdr, lossless_present
    ))

    if launch_arguments:
        command_parts.append(os.path.expanduser(launch_arguments))
    if gamemode and gamemoderun_path and os.path.exists(gamemoderun_path):
        command_parts.append("gamemoderun")
    if mangohud and mangohud_path and os.path.exists(mangohud_path):
        command_parts.append("mangohud")

    if runner != "Steam":
        command_parts.append(f"'{umu_run_path}'")

    if addapp_checkbox == "addapp_enabled":
        command_parts.append(shlex.quote(addapp_bat))
    else:
        if runner != "Steam":
            command_parts.append(shlex.quote(path))
        else:
            steam_arguments = "-nobigpicture -nochatui -nofriendsui -silent -applaunch"
            if is_flatpak:
                if is_steam_flatpak:
                    command_parts.append(f"flatpak-spawn --host flatpak run com.valvesoftware.Steam {steam_arguments} {path}")
                else:
                    command_parts.append(f"flatpak-spawn --host steam {steam_arguments} {path}")
            else:
                if is_steam_flatpak:
                    command_parts.append(f"flatpak run com.valvesoftware.Steam {steam_arguments} {path}")
                else:
                    command_parts.append(f"steam {steam_arguments} {path}")

    if game_arguments:
        command_parts.append(game_arguments)

    return " ".join(command_parts)
