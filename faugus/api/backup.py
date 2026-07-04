"""Backup API — create and restore full config backups.

Uses the existing ``backup.py`` logic for creating ZIP archives.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/backup/create")
def create_backup() -> dict:
    """Create a ZIP backup of configuration and games data."""
    from faugus.path_manager import faugus_launcher_dir

    # Inline the backup logic to avoid pulling GTK into the server.
    # (faugus.backup imports gi.repository at module level — Phase 0 fix.)
    import os
    import shutil
    import json
    from datetime import datetime

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
    shutil.rmtree(temp_dir)

    size = os.path.getsize(dest) if os.path.isfile(dest) else 0
    return {"path": dest, "size": size, "date": current_date}


@router.post("/api/backup/restore")
def restore_backup() -> dict:
    """Restore from a backup ZIP (stub — multipart upload TBD)."""
    raise HTTPException(501, "Not implemented; upload endpoint coming")
