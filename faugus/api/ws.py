"""WebSocket endpoints for real-time game events.

Log streaming and lifecycle notifications are powered by FastAPI's
built-in WebSocket support.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/api/ws/game/{gameid}/log")
async def game_log_ws(ws: WebSocket, gameid: str) -> None:
    """Stream game log output in real-time during launch.

    TODO: wire up to subprocess stdout so the client receives live
    Proton/UMU log lines as they are produced.
    """
    await ws.accept()
    try:
        await ws.send_json({"type": "connected", "gameid": gameid})
        # Placeholder — keep connection open
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
    """Stream game lifecycle events (launching → running → exited).

    TODO: wire up to subprocess watcher so status changes are pushed.
    """
    await ws.accept()
    try:
        await ws.send_json({"type": "connected", "gameid": gameid})
        # Placeholder — keep connection open
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json({"type": "pong"})
            else:
                break
    except WebSocketDisconnect:
        pass
