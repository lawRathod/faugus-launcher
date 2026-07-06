"""Faugus Launcher — FastAPI backend server.

Usage::

    python -m faugus.server            # start on port 9876
    python -m faugus.server --port 9876
"""

import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from faugus.api.games import router as games_router
from faugus.api.config import router as config_router
from faugus.api.runners import router as runners_router
from faugus.api.steam import router as steam_router
from faugus.api.files import router as files_router
from faugus.api.logs import router as logs_router
from faugus.api.envar import router as envar_router
from faugus.api.backup import router as backup_router
from faugus.api.system import router as system_router
from faugus.api.ws import router as ws_router

app = FastAPI(
    title="Faugus Launcher API",
    version="1.22.7",
    docs_url="/docs",
)

# ── CORS (dev only — locked to localhost) ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────
app.include_router(games_router)
app.include_router(config_router)
app.include_router(runners_router)
app.include_router(steam_router)
app.include_router(files_router)
app.include_router(logs_router)
app.include_router(envar_router)
app.include_router(backup_router)
app.include_router(system_router)
app.include_router(ws_router)


def serve(port: int = 9876) -> None:
    """Start the Uvicorn server."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


def main() -> None:
    parser = argparse.ArgumentParser(description="Faugus Launcher API server")
    parser.add_argument("--port", type=int, default=9876)
    args = parser.parse_args()
    serve(port=args.port)


if __name__ == "__main__":
    main()
