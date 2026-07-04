"""WebSocket endpoints for real-time game events.

Log streaming reads existing log files on connect.  Status notifications
will be wired to the process reaper in a follow-up.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


def _read_log(path: str) -> list[str]:
    """Read all non-empty lines from a log file."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n\r") for line in f if line.strip()]
    except OSError:
        return []


@router.websocket("/api/ws/game/{gameid}/log")
async def game_log_ws(ws: WebSocket, gameid: str) -> None:
    """Stream game log output.

    On connect, sends existing lines from proton.log and umu.log,
    then keeps the connection open for future real-time streaming
    (TBD: wire to subprocess output).
    """
    await ws.accept()
    try:
        await ws.send_json({"type": "connected", "gameid": gameid})

        from faugus.path_manager import logs_dir
        game_log_dir = os.path.join(logs_dir, gameid)

        for source in ("proton.log", "umu.log"):
            log_path = os.path.join(game_log_dir, source)
            for line in _read_log(log_path):
                await ws.send_json({
                    "type": "log_line",
                    "source": source,
                    "line": line,
                })

        await ws.send_json({"type": "log_end", "gameid": gameid})

        # Keep connection alive (future: watch for new log lines)
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json({"type": "pong"})
            else:
                break
    except WebSocketDisconnect:
        pass


@router.websocket("/api/ws/game/{gameid}/status")
async def game_status_ws(ws: WebSocket, gameid: str) -> None:
    """Stream game lifecycle events.

    TODO: wire up to running_games.json watcher and process reaper
    so status changes (launching → running → exited) are pushed.
    """
    await ws.accept()
    try:
        await ws.send_json({"type": "connected", "gameid": gameid})
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json({"type": "pong"})
            else:
                break
    except WebSocketDisconnect:
        pass
