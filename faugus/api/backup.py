"""Backup API — create and restore full config backups.

Uses the existing ``backup.py`` logic for creating ZIP archives.
"""

from __future__ import annotations

import io
import os
import shutil
import zipfile

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()


@router.post("/api/backup/create")
def create_backup() -> dict:
    """Create a ZIP backup of configuration and games data."""
    from faugus.path_manager import faugus_launcher_dir
    from datetime import datetime
    import json as _json

    items = ["banners", "games-backup", "icons", "config.ini", "envar.txt",
             "games.json", "latest-games.txt"]
    temp_dir = os.path.join(faugus_launcher_dir, "temp-backup-api")
    os.makedirs(temp_dir, exist_ok=True)

    for item in items:
        src = os.path.join(faugus_launcher_dir, item)
        dst = os.path.join(temp_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    marker = os.path.join(temp_dir, ".faugus_marker")
    with open(marker, "w") as f:
        f.write("faugus-launcher-backup")

    current_date = datetime.now().strftime("%Y-%m-%d")
    dest = os.path.join(faugus_launcher_dir, f"faugus-launcher-{current_date}.zip")
    shutil.make_archive(dest.replace(".zip", ""), "zip", temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

    size = os.path.getsize(dest) if os.path.isfile(dest) else 0
    return {"path": dest, "size": size, "date": current_date}


@router.post("/api/backup/restore")
def restore_backup(file: UploadFile = File(...)) -> dict:
    """Restore configuration from an uploaded backup ZIP."""
    from faugus.path_manager import faugus_launcher_dir
    import tempfile

    contents = file.file.read()

    # Validate ZIP magic bytes
    if not contents.startswith(b"PK\x03\x04"):
        raise HTTPException(422, "Only ZIP files are accepted")

    tmpdir = tempfile.mkdtemp(prefix="faugus-restore-")
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as zf:
            zf.extractall(tmpdir)

        marker = os.path.join(tmpdir, ".faugus_marker")
        if not os.path.isfile(marker):
            raise HTTPException(422, "Not a valid Faugus Launcher backup")

        for item in os.listdir(tmpdir):
            if item == ".faugus_marker":
                continue
            src = os.path.join(tmpdir, item)
            dst = os.path.join(faugus_launcher_dir, item)
            if os.path.isdir(dst):
                shutil.rmtree(dst, ignore_errors=True)
            elif os.path.isfile(dst):
                os.remove(dst)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return {"restored": True}
