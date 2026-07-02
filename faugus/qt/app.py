"""Qt application entry point for Faugus Launcher."""

import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

from faugus.core.config import AppConfig
from faugus.path_manager import PathManager


def _apply_dark_palette(app):
    """Force a dark color palette so the app always looks correct."""
    palette = QPalette()

    # Base dark purple-tinted colors
    bg_darker = QColor(18, 12, 28)       # very dark purple
    bg_dark = QColor(25, 18, 38)         # dark purple
    bg_mid = QColor(35, 25, 52)          # mid purple
    bg_light = QColor(45, 35, 65)        # lighter purple
    fg = QColor(224, 224, 224)           # light gray text
    fg_dim = QColor(160, 150, 180)       # dim purple-gray text
    accent = QColor(138, 92, 246)        # purple accent
    accent_light = QColor(167, 139, 250) # lighter purple accent

    palette.setColor(QPalette.Window, bg_darker)
    palette.setColor(QPalette.WindowText, fg)
    palette.setColor(QPalette.Base, bg_dark)
    palette.setColor(QPalette.AlternateBase, bg_mid)
    palette.setColor(QPalette.ToolTipBase, bg_mid)
    palette.setColor(QPalette.ToolTipText, fg)
    palette.setColor(QPalette.Text, fg)
    palette.setColor(QPalette.Button, bg_mid)
    palette.setColor(QPalette.ButtonText, fg)
    palette.setColor(QPalette.BrightText, fg)
    palette.setColor(QPalette.Link, accent_light)
    palette.setColor(QPalette.Highlight, accent)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    # Disabled
    palette.setColor(QPalette.Disabled, QPalette.WindowText, fg_dim)
    palette.setColor(QPalette.Disabled, QPalette.Text, fg_dim)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, fg_dim)

    app.setPalette(palette)


def main():
    start_hidden = "--hide" in sys.argv

    # If launched with a game file, delegate to runner
    if len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
        from faugus.runner import run_file
        run_file(sys.argv[1])
        sys.exit(0)

    # Ensure config directory exists
    config_dir = PathManager.user_config("faugus-launcher")
    os.makedirs(config_dir, exist_ok=True)

    config_file = os.path.join(config_dir, "config.ini")
    cfg = AppConfig(config_file)

    # High DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

    app = QApplication(sys.argv)
    app.setApplicationName("faugus-launcher")
    app.setApplicationDisplayName("Faugus Launcher")

    _apply_dark_palette(app)

    from faugus.qt.main_window import MainWindow
    window = MainWindow(cfg, start_hidden=start_hidden)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
