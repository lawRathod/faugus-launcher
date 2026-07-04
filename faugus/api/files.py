"""Files API — browse local filesystem, upload icons/banners.

All paths are validated against traversal attacks before any I/O.
"""

from __future__ import annotations

import os
import stat

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def _validate_path(path: str) -> str:
    """Reject path traversal and return the resolved path."""
    if ".." in path:
        raise HTTPException(422, "Path traversal not allowed")
    return path


@router.get("/api/files/browse")
def browse_directory(path: str = Query("/")) -> list[dict]:
    """List files and directories at *path*."""
    safe = _validate_path(path)
    if not os.path.isdir(safe):
        return []

    try:
        entries: list[dict] = []
        for name in sorted(os.listdir(safe)):
            full = os.path.join(safe, name)
            try:
                st = os.stat(full)
                is_dir = stat.S_ISDIR(st.st_mode)
                entries.append({
                    "name": name,
                    "path": full,
                    "type": "dir" if is_dir else "file",
                    "size": st.st_size,
                })
            except OSError:
                continue  # skip unreadable entries
        return entries
    except OSError:
        return []


@router.post("/api/files/icon")
def upload_icon() -> dict:
    """Upload a game icon. (stub — multipart handling TBD)"""
    raise HTTPException(501, "Not implemented")


@router.post("/api/files/banner")
def upload_banner() -> dict:
    """Upload a game banner. (stub — multipart handling TBD)"""
    raise HTTPException(501, "Not implemented")


@router.get("/api/files/prefix-suggest")
def prefix_suggest(title: str = Query(...)) -> dict:
    """Suggest a prefix path for a game title."""
    from faugus.path_manager import prefixes_dir
    # Lazy import to avoid pulling GTK into the server
    from faugus.utils import format_title
    safe = format_title(title)
    return {"prefix": os.path.join(prefixes_dir, safe)}
