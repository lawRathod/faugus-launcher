# AGENTS.md — Faugus Launcher

## Project Overview
GTK3-based Python GUI for running Windows games/applications on Linux via UMU-Launcher (Wine/Proton).  
Language: Python 3. GUI: GTK 3 via PyGObject. Build: Meson + Ninja.

## Key Commands
- **Run tests:** `pytest` (or `pytest -m "not gui"` for headless)
- **Build:** `meson setup builddir --prefix=/usr && cd builddir && ninja`
- **Install:** `sudo ninja install` (from builddir)

## Virtual Environment
- Using a venv is recommended; default location is `.venv/` (gitignored)
- If `.venv/` doesn't exist, the agent should create it: `python3 -m venv .venv`
- After creating/activating, install deps: `.venv/bin/pip install -r requirements.txt`
- Activate: `source .venv/bin/activate`

## Code Conventions
- Indentation: 4 spaces (no tabs)
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_CASE` for constants
- No type hints used in the codebase
- Shebang: `#!/usr/bin/python3` on executable scripts
- Import order: stdlib → third-party → local (`faugus.*`)
- Docstrings: triple double-quotes `"""..."""`
- Flake8 error codes suppressed inline: `# noqa: E402,F401`

## Testing
- Framework: pytest 9.x (config in `pytest.ini`)
- Test dir: `tests/` — pure logic only (no GTK display needed)
- Mark display-dependent tests: `@pytest.mark.gui`
- Fixtures in `tests/conftest.py`: `tmp_config_dir` (monkeypatches PathManager to temp dir)

## Architecture
- `faugus/launcher.py` (~6444 lines) — main GTK window, game library UI
- `faugus/runner.py` — game execution logic
- `faugus/proton_manager.py` — Proton management UI
- `faugus/proton_downloader.py` — downloading Proton versions
- `faugus/config_manager.py` — INI-style config
- `faugus/components.py` — UMU component download/update
- `faugus/path_manager.py` — XDG path resolution, Flatpak detection
- `faugus/gamepad.py` — gamepad navigation (pygame)
- `faugus/utils.py` — shared utilities (~1130 lines)
- `faugus/backup.py` — game config backups
- `faugus/language_config.py` — gettext i18n setup
- `faugus/shortcut.py` — Steam shortcut creation
- `faugus/steam_setup.py` — Steam compat directory setup
- `faugus/keyboard.py` — keyboard shortcuts
- `faugus/ea_fix.py` — EA App anti-cheat fix
- `faugus_run.py` — desktop file fixer + runner launcher
- `faugus-launcher` — shell script dispatcher entry point

## No Linting/Formatting/CI Configured
- No ruff, black, pylint, flake8 configs in repo
- No CI pipelines (`.github/` is empty)
