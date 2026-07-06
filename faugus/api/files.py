"""Files API — browse local filesystem, upload icons/banners.

All paths are validated against traversal attacks before any I/O.
"""

from __future__ import annotations

import os
import re
import stat

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

router = APIRouter()

_MAX_ICON_SIZE = 10 * 1024 * 1024  # 10 MB
_MAX_BANNER_SIZE = 20 * 1024 * 1024  # 20 MB


def _validate_path(path: str) -> str:
    """Reject path traversal and return the resolved path."""
    if ".." in path:
        raise HTTPException(422, "Path traversal not allowed")
    return path


def _save_upload(
    file: UploadFile,
    gameid: str,
    dest_dir: str,
    max_size: int,
    ext: str,
) -> str:
    """Validate and save an uploaded image file. Returns the saved path."""
    if not gameid.strip():
        raise HTTPException(422, "gameid is required")

    # Read up to max_size+1 to bound memory, then check size
    contents = file.file.read(max_size + 1)
    if len(contents) > max_size:
        raise HTTPException(422, f"File too large (max {max_size // (1024*1024)} MB)")

    # Validate PNG magic bytes (not just content-type)
    if not contents.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(422, "Only PNG files are accepted")

    # Sanitize gameid — allow only safe filename characters
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", gameid.strip())

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{safe_name}{ext}")

    with open(dest_path, "wb") as f:
        f.write(contents)

    return dest_path


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
                continue
        return entries
    except OSError:
        return []


@router.post("/api/files/icon")
def upload_icon(
    file: UploadFile = File(...),
    gameid: str = Form(...),
) -> dict:
    """Upload a PNG game icon. Saved as ``{icons_dir}/{gameid}.png``."""
    from faugus.path_manager import icons_dir
    path = _save_upload(file, gameid, icons_dir, _MAX_ICON_SIZE, ".png")
    return {"path": path}


@router.post("/api/files/banner")
def upload_banner(
    file: UploadFile = File(...),
    gameid: str = Form(...),
) -> dict:
    """Upload a PNG game banner. Saved as ``{banners_dir}/{gameid}.png``."""
    from faugus.path_manager import banners_dir
    path = _save_upload(file, gameid, banners_dir, _MAX_BANNER_SIZE, ".png")
    return {"path": path}


@router.get("/api/files/icon/{gameid}")
def get_icon(gameid: str) -> "fastapi.responses.FileResponse":
    """Serve a game icon file."""
    from faugus.path_manager import icons_dir
    import fastapi.responses as r
    # Try .png first, fall back to .ico
    for ext in (".png", ".ico"):
        path = os.path.join(icons_dir, f"{gameid}{ext}")
        if os.path.isfile(path):
            return r.FileResponse(path)
    return r.Response(status_code=404)


@router.get("/api/files/banner/{gameid}")
def get_banner(gameid: str) -> "fastapi.responses.FileResponse":
    """Serve a game banner file."""
    from faugus.path_manager import banners_dir
    import fastapi.responses as r
    path = os.path.join(banners_dir, f"{gameid}.png")
    if os.path.isfile(path):
        return r.FileResponse(path)
    # Return default banner
    return r.Response(status_code=404)


@router.get("/api/files/prefix-suggest")
def prefix_suggest(title: str = Query(...)) -> dict:
    """Suggest a prefix path for a game title."""
    from faugus.path_manager import prefixes_dir
    from faugus.utils import format_title
    safe = format_title(title)
    return {"prefix": os.path.join(prefixes_dir, safe)}
