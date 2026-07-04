"""Logs API — read and clear game logs.

Logs are stored in ``logs_dir/<gameid>/proton.log`` and ``.../umu.log``.
"""

from __future__ import annotations

import os
import shutil

from fastapi import APIRouter

router = APIRouter()


def _logs_dir():
    from faugus.path_manager import logs_dir
    return logs_dir


@router.get("/api/logs/{gameid}")
def get_logs(gameid: str) -> dict:
    """Return proton.log and umu.log for a game (empty strings if missing)."""
    game_log_dir = os.path.join(_logs_dir(), gameid)
    proton = ""
    umu = ""
    try:
        proton_path = os.path.join(game_log_dir, "proton.log")
        if os.path.isfile(proton_path):
            with open(proton_path, encoding="utf-8", errors="replace") as f:
                proton = f.read()
        umu_path = os.path.join(game_log_dir, "umu.log")
        if os.path.isfile(umu_path):
            with open(umu_path, encoding="utf-8", errors="replace") as f:
                umu = f.read()
    except OSError:
        pass
    return {"gameid": gameid, "proton_log": proton, "umu_log": umu}


@router.delete("/api/logs")
def clear_logs() -> dict:
    """Delete all game log directories."""
    logs_dir = _logs_dir()
    if os.path.isdir(logs_dir):
        try:
            shutil.rmtree(logs_dir)
        except OSError:
            pass
    return {"cleared": True}
