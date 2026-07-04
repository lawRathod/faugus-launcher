"""Environment Variables API — read/write global env var list.

Stored in ``envar.txt`` (one VAR=value per line).
"""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter()


def _envar_path():
    from faugus.path_manager import envar_dir
    return envar_dir


@router.get("/api/envar")
def get_envar() -> list[str]:
    """Return the list of global environment variable strings."""
    path = _envar_path()
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


@router.put("/api/envar")
def update_envar(body: list[str]) -> list[str]:
    """Replace the global environment variable list."""
    path = _envar_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cleaned = [line.strip() for line in body if line.strip()]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned) + "\n")
    return cleaned
