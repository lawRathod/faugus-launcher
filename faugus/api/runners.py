"""Runners API — detect installed Proton versions and check for updates."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

# Runner variants known to the downloader (mirrors proton_manager.VARIANTS
# without importing GTK).  Used to mark "Latest" symlink directories.
_VARIANTS: dict[str, dict[str, str]] = {
    "cachyos": {"name": "Proton-CachyOS", "latest": "Proton-CachyOS Latest"},
    "ge": {"name": "GE-Proton", "latest": "Proton-GE Latest"},
    "em": {"name": "Proton-EM", "latest": "Proton-EM Latest"},
    "dw": {"name": "DW-Proton", "latest": "DW-Proton Latest"},
}
_LATEST_NAMES = {info["latest"] for info in _VARIANTS.values()}


def _compatibility_dir() -> Path:
    """Return the compatibility tools directory (reads at call time)."""
    from faugus.path_manager import compatibility_dir
    return Path(compatibility_dir)


@router.get("/api/runners")
def list_runners() -> list[dict]:
    """Scan compatibilitytools.d and return installed Proton runners."""
    compat_path = _compatibility_dir()
    if not compat_path.is_dir():
        return []

    runners: list[dict] = []
    try:
        entries = sorted(compat_path.iterdir())
    except OSError:
        # Directory exists but isn't readable
        return []

    for entry in entries:
        if not entry.is_dir():
            continue
        name = entry.name

        # Determine runner type from name prefix
        # Keep in sync with proton_manager.VARIANTS
        typ = "proton"
        if name.startswith("Proton-CachyOS"):
            typ = "cachyos"
        elif name.startswith(("GE-Proton", "Proton-GE")):
            typ = "ge"
        elif name.startswith(("Proton-EM", "EM-", "proton-EM")):
            typ = "em"
        elif name.startswith(("DW-Proton", "dwproton")):
            typ = "dw"

        runners.append({
            "name": name,
            "path": str(entry),
            "type": typ,
            "is_latest": name in _LATEST_NAMES,
        })

    return runners


@router.get("/api/runners/latest")
def latest_runner_versions() -> list[dict]:
    """Fetch latest version tags from GitHub for each runner variant."""
    from faugus.proton_downloader import get_latest_tag_and_url

    results: list[dict] = []
    for key, info in _VARIANTS.items():
        tag = None
        try:
            if key == "cachyos":
                tag, _, _ = get_latest_tag_and_url(
                    "https://api.github.com/repos/CachyOS/proton-cachyos/releases",
                    ["x86_64.tar.xz"],
                )
            elif key == "ge":
                tag, _, _ = get_latest_tag_and_url(
                    "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases",
                    [".tar.gz", ".tar.xz"],
                )
            elif key == "em":
                tag, _, _ = get_latest_tag_and_url(
                    "https://api.github.com/repos/Etaash-mathamsetty/Proton/releases",
                    [".tar.xz"],
                )
            elif key == "dw":
                tag, _, _ = get_latest_tag_and_url(
                    "https://api.github.com/repos/CachyOS/proton-cachyos/releases",
                    ["x86_64.tar.xz"],
                )
            if tag:
                tag = tag.lstrip("v")
        except Exception:
            pass  # API unreachable, return None
        results.append({"key": key, "display_name": info["name"], "latest_version": tag})
    return results
