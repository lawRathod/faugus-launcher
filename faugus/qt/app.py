"""Qt application entry point for Faugus Launcher."""

import os
import signal
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import QSocketNotifier, QTimer

from faugus.core.config import AppConfig
from faugus.path_manager import PathManager


def _apply_dark_palette(app):
    """Force a dark color palette so the app always looks correct."""
    palette = QPalette()

    bg_darker = QColor(18, 12, 28)
    bg_dark = QColor(25, 18, 38)
    bg_mid = QColor(35, 25, 52)
    fg = QColor(224, 224, 224)
    fg_dim = QColor(160, 150, 180)
    accent = QColor(138, 92, 246)
    accent_light = QColor(167, 139, 250)

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

    palette.setColor(QPalette.Disabled, QPalette.WindowText, fg_dim)
    palette.setColor(QPalette.Disabled, QPalette.Text, fg_dim)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, fg_dim)

    app.setPalette(palette)


def main():
    start_hidden = "--hide" in sys.argv

    if len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
        from faugus.runner import run_file
        run_file(sys.argv[1])
        sys.exit(0)

    config_dir = PathManager.user_config("faugus-launcher")
    os.makedirs(config_dir, exist_ok=True)

    config_file = os.path.join(config_dir, "config.ini")
    cfg = AppConfig(config_file)

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

    app = QApplication(sys.argv)
    app.setApplicationName("faugus-launcher")
    app.setApplicationDisplayName("Faugus Launcher")

    _apply_dark_palette(app)

    # Allow Ctrl+C to quit: watch stdin for SIGINT
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    stdin_fd = sys.stdin.fileno()
    if os.isatty(stdin_fd):
        notif = QSocketNotifier(stdin_fd, QSocketNotifier.Read, app)
        notif.activated.connect(lambda: app.quit())

    from faugus.qt.main_window import MainWindow
    window = MainWindow(cfg, start_hidden=start_hidden)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
