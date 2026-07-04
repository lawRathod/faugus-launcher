# Faugus Launcher — Agent Context

## Project Overview

Faugus Launcher is a lightweight GTK3 Python application for running Windows games on Linux using UMU-Launcher / Proton. It provides a graphical game library manager with Steam integration, Proton management, and gamepad navigation.

- **Version:** 1.22.7
- **License:** MIT
- **Language:** Python 3 (PyGObject/GTK3)
- **Build system:** Meson
- **Domain:** Linux gaming, Wine/Proton, game launcher

## Architecture

### Entry Points

| File | Purpose |
|------|---------|
| `faugus-launcher` | Shell launcher — routes args to `faugus.runner`, `faugus.launcher`, or `faugus.shortcut` |
| `faugus_run.py` | Installed as `faugus-run` — fixes desktop/Steam shortcuts then execs into `faugus.runner` |
| `faugus/launcher.py` | The main GTK3 GUI application (`FaugusApp` → `Main` window) |
| `faugus/runner.py` | Game execution process (splash screen, log window, Proton/UMU launch) |
| `faugus/shortcut.py` | .desktop shortcut creation from .exe files |

### Core Modules

| Module | Responsibility |
|--------|---------------|
| `config_manager.py` | `ConfigManager` — loads/saves `~/.config/faugus-launcher/config.ini` |
| `path_manager.py` | `PathManager` — XDG path resolution, flatpak-aware, binary/icon detection |
| `launcher.py` | Main window, game list (3 modes: List/Blocks/Banners), search, sort, categories, tray icon, gamepad, drag-and-drop reordering |
| `runner.py` | Game process lifecycle: environment setup, Wine/Proton prefix management, logs, EA anti-cheat fixes, splash window |
| `components.py` | UI component helpers (game list widgets, artwork loading) |
| `utils.py` | Dark theme detection, HiDPI mixin, pixbuf loading, JSON helpers |
| `steam_setup.py` | Steam flatpak detection, `shortcuts.vdf` management |
| `ea_fix.py` | EA anti-cheat compatibility workarounds |
| `proton_downloader.py` | Download/update Proton runners (GE, CachyOS) |
| `proton_manager.py` | Proton runner management UI |
| `gamepad.py` | Gamepad navigation support |
| `keyboard.py` | Keyboard navigation/hotkeys |
| `backup.py` | Game configuration backup/restore |
| `language_config.py` | i18n / gettext setup |

### Key Data Paths

| Path | Purpose |
|------|---------|
| `~/.config/faugus-launcher/config.ini` | Application settings |
| `~/.config/faugus-launcher/games.json` | Game library database |
| `~/.config/faugus-launcher/logs/` | Proton/UMU logs per game |
| `~/.config/faugus-launcher/icons/` | Per-game icons |
| `~/.config/faugus-launcher/banners/` | Per-game banner artwork |
| `~/.config/faugus-launcher/categories.txt` | User-defined categories |
| `~/.config/faugus-launcher/custom-order.json` | Custom sort order (drag-and-drop) |
| `~/.config/faugus-launcher/presets.json` | Game presets |
| `~/.config/faugus-launcher/envar.txt` | Custom environment variables |
| `~/.local/share/faugus-launcher/umu-run` | UMU runner binary |
| `~/Faugus/` | Default game prefixes location |
| `~/.local/share/Steam/compatibilitytools.d/` | Proton runners |
| `~/.local/share/applications/` | Desktop shortcuts |
| `~/.local/share/faugus-launcher/running_games.json` | Currently running game PIDs |

## Conventions & Patterns

### Code Style
- Python 3, `#!/usr/bin/python3` or `#!/usr/bin/env python3`
- Indentation: 4 spaces
- Imports: standard library → third-party → project modules
- Class naming: PascalCase (`ConfigManager`, `FaugusApp`, `Main`)
- Methods/functions: snake_case
- Constants: UPPER_SNAKE_CASE
- Type hints: minimal, used sparingly

### GTK Patterns
- Application class → `Gtk.Application` (`FaugusApp`)
- Main window extends `Gtk.ApplicationWindow` + `HiDpiMixin`
- CSS styling via `Gtk.CssProvider` (embedded in `launcher.py`)
- UI built programmatically (no Glade/Builder XML)
- Signals connected via `connect()` method
- `GLib.timeout_add` for periodic checks (running game poll)
- `GLib.idle_add` for thread → main thread callbacks

### Game Data Model
Each game in `games.json`:
```python
{
  "gameid": str,        # Unique identifier (hash-based)
  "title": str,         # Display name
  "exe": str,           # Path to .exe
  "path": str,          # Working directory
  "args": str,          # Command-line arguments
  "runner": str,        # Proton runner selection
  "prefix": str,        # Wine prefix path
  "icon": str,          # Icon path
  "banner": str,        # Banner image path
  "category": str|list, # Category assignment(s)
  "hidden": bool,       # Hidden from main list
  "playtime": int,      # Playtime in seconds
  "lastplayed": int,    # Unix timestamp
  "settings": dict,     # Per-game override settings
}
```

### i18n
- gettext with `.po`/`.mo` files in `languages/`
- Three translation domains: `faugus-launcher`, `faugus-proton-manager`, `faugus-run`
- `_()` function for string marking
- New strings: add to `.pot` files in `languages/`

### Testing
- pytest in `.venv`
- No dedicated test directory yet

## Common Development Tasks

### Add a new config option
1. Add default to `ConfigManager.default_config` in `config_manager.py`
2. Wire up the UI toggle in `launcher.py` (settings dialog)
3. Read the value where needed (e.g., `config_manager.config.get('option-name')`)

### Add a new UI mode
1. Create view setup in `Main.setup_interface()` (switch on `self.interface_mode`)
2. Add artwork loading in `Main.load_games()` and `components.py`
3. Handle mode toggle in settings

### Add a new Proton runner source
1. Add download logic in `proton_downloader.py`
2. Add UI entry in `proton_manager.py`
3. Register in runner detection in `runner.py` or `launcher.py`

## Flatpak Awareness

The codebase has extensive `IS_FLATPAK` branching:
- `PathManager` adjusts home dir via `HOST_HOME`
- Icon/theming paths differ
- GTK dark theme detection uses `org.freedesktop.portal.Settings`
- Tray icon uses Flatpak app ID vs. local path
- Game execution wraps flatpak-spawn or direct calls

## Environment Detection
- `IS_FLATPAK`: Set by `FLATPAK_ID` env var or `/.flatpak-info` file
- `IS_STEAM_FLATPAK`: Set in `steam_setup.py`

## Key Technical Decisions

- **No Glade/UI builder** — all widgets created programmatically
- **Embedded CSS** — styles loaded via `Gtk.CssProvider` in constructor
- **Threading** — game processes run in threads, UI updates via `GLib.idle_add`
- **Gamepad** — optional, can be enabled in settings for HTPC/big picture use
- **Drag-and-drop** — custom order DnD with `custom-order.json` persistence
- **System tray** — `AyatanaAppIndicator3` for background running
