"""Game card widget for the Qt-based game library grid/list.

Replaces the GTK FlowBoxChild + hbox + overlay system from launcher.py.
Each card displays a game image, title, playing overlay, favorite star,
and optional age label for recents view.
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
    QMenu,
    QSizePolicy,
)

from faugus.core.utils import load_json_file, save_json_file
from faugus.core.models import Game
from faugus.path_manager import PathManager

_BANNER_PLACEHOLDER = PathManager.system_data(
    "faugus-launcher/faugus-banner.png"
)
_DEFAULT_ICON = PathManager.get_icon("faugus-launcher.svg")

_GAMES_JSON = PathManager.user_config("faugus-launcher/games.json")
_LOGS_DIR = PathManager.user_config("faugus-launcher/logs")
_CATEGORIES_FILE = PathManager.user_config("faugus-launcher/categories.txt")


def _scaled_pixmap(path, width, height):
    """Load a pixmap from *path*, falling back to the default icon."""
    if path and os.path.isfile(path):
        pixmap = QPixmap(path)
    else:
        pixmap = QPixmap(_DEFAULT_ICON)
    if pixmap.isNull():
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(80, 80, 80))
    dpr = pixmap.devicePixelRatio() or 1.0
    scaled = pixmap.scaled(
        int(width * dpr),
        int(height * dpr),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )
    scaled.setDevicePixelRatio(dpr)
    return scaled


def _banner_pixmap(path, zoom_pct=100):
    """Load a banner pixmap scaled according to *zoom_pct*."""
    w = int(230 * (zoom_pct / 100.0))
    h = int(w * 1.5)
    return _scaled_pixmap(path, w, h)


class GameCard(QWidget):
    """A single game card widget for the library grid/list view."""

    context_action = Signal(str, object)
    doubleClicked = Signal(object)

    def __init__(self, game, mode="Banners", zoom_pct=100, parent=None):
        super().__init__(parent)
        self.game = game
        self._mode = mode
        self._zoom_pct = zoom_pct
        self._playing = False

        self.setObjectName("GameCard")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- Content (image + title) ---
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)

        self._title_label = QLabel(game.title)
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setWordWrap(True)
        self._title_label.setMaximumHeight(40)

        # --- Overlay (playing indicator) ---
        self._overlay = QWidget()
        self._overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay_layout = QVBoxLayout(self._overlay)
        overlay_layout.setAlignment(Qt.AlignCenter)
        playing_lbl = QLabel("\u25b6")
        playing_lbl.setAlignment(Qt.AlignCenter)
        playing_lbl.setStyleSheet("color: white; font-size: 32px; background: transparent;")
        overlay_layout.addWidget(playing_lbl)
        self._overlay.hide()

        # --- Corner overlays (favorite + age) ---
        self._corner = QWidget()
        self._corner.setAttribute(Qt.WA_TransparentForMouseEvents)
        corner_layout = QVBoxLayout(self._corner)
        corner_layout.setContentsMargins(4, 4, 4, 4)
        corner_layout.setSpacing(0)

        # Favorite button (top-right)
        self._fav_btn = QPushButton()
        self._fav_btn.setFixedSize(28, 28)
        self._fav_btn.setCursor(Qt.PointingHandCursor)
        self._fav_btn.clicked.connect(self._on_fav_clicked)
        self._fav_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 6px; font-size: 18px; }"
            "QPushButton:hover { background: rgba(138, 92, 246, 0.2); }"
        )
        self._update_fav_icon()
        corner_layout.addStretch()
        fav_row = QHBoxLayout()
        fav_row.addStretch()
        fav_row.addWidget(self._fav_btn)
        corner_layout.addLayout(fav_row)

        # Age label (bottom-right)
        self._age_label = QLabel()
        self._age_label.setStyleSheet(
            "QLabel { font-size: 11px; color: #e0d8f0; background: rgba(18, 12, 28, 0.75);"
            " padding: 2px 8px; border-radius: 6px; }"
        )
        self._age_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._age_label.hide()
        age_row = QHBoxLayout()
        age_row.addStretch()
        age_row.addWidget(self._age_label)
        corner_layout.addLayout(age_row)

        # --- Build mode ---
        if self._mode == "List":
            self._build_list_mode()
        elif self._mode == "Blocks":
            self._build_blocks_mode()
        else:
            self._build_banners_mode()

        # --- Stacked layout: content + overlay + corners ---
        stack = QStackedLayout()
        stack.setStackingMode(QStackedLayout.StackAll)
        stack.addWidget(self._content)
        stack.addWidget(self._overlay)
        stack.addWidget(self._corner)
        outer.addLayout(stack)

        self.setStyleSheet(self._card_stylesheet())

    # ------------------------------------------------------------------ #
    # Mode builders                                                        #
    # ------------------------------------------------------------------ #

    def _build_list_mode(self):
        row = QHBoxLayout()
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(8)

        icon_px = _scaled_pixmap(self.game.icon, 40, 40)
        self._image_label.setPixmap(icon_px)
        self._image_label.setFixedSize(40, 40)

        self._title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._title_label.setStyleSheet("font-size: 14px; color: #e0d8f0;")

        row.addWidget(self._image_label)
        row.addWidget(self._title_label, 1)
        self._content_layout.addLayout(row)
        self.setFixedHeight(60)

    def _build_blocks_mode(self):
        block = 100
        icon_px = _scaled_pixmap(self.game.icon, block, block)
        self._image_label.setPixmap(icon_px)
        self._image_label.setFixedSize(block, block)

        self._title_label.setMaximumWidth(block + 40)
        self._title_label.setStyleSheet("margin: 10px; font-size: 13px; color: #e0d8f0;")

        self._content_layout.addWidget(self._image_label, 0, Qt.AlignHCenter)
        self._content_layout.addWidget(self._title_label, 0, Qt.AlignHCenter)
        self.setFixedWidth(block + 40)

    def _build_banners_mode(self):
        banner_path = self.game.banner
        if not os.path.isfile(banner_path):
            banner_path = _BANNER_PLACEHOLDER

        px = _banner_pixmap(banner_path, self._zoom_pct)
        self._image_label.setPixmap(px)
        self._image_label.setFixedSize(px.size())

        self._title_label.setFixedHeight(50)
        self._title_label.setStyleSheet("margin: 0 10px; font-size: 13px; color: #e0d8f0;")
        self._content_layout.addWidget(self._image_label, 0, Qt.AlignHCenter)
        self._content_layout.addWidget(self._title_label, 0, Qt.AlignHCenter)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def set_playing(self, playing):
        self._playing = playing
        self._overlay.setVisible(playing)

    def set_age_label(self, text):
        if text:
            self._age_label.setText(text)
            self._age_label.show()
        else:
            self._age_label.hide()

    def update_banner(self, banner_path, zoom_pct):
        self._zoom_pct = zoom_pct
        if self._mode != "Banners":
            return
        if not os.path.isfile(banner_path):
            banner_path = _BANNER_PLACEHOLDER
        px = _banner_pixmap(banner_path, zoom_pct)
        self._image_label.setPixmap(px)
        self._image_label.setFixedSize(px.size())

    def set_favorite(self, fav):
        self.game.favorite = fav
        self._update_fav_icon()

    # ------------------------------------------------------------------ #
    # Context menu                                                         #
    # ------------------------------------------------------------------ #

    def contextMenuEvent(self, event):
        game = self.game
        menu = QMenu(self)

        menu.addAction("Play").triggered.connect(
            lambda: self.context_action.emit("play", game))
        menu.addAction("Edit").triggered.connect(
            lambda: self.context_action.emit("edit", game))
        menu.addAction("Delete").triggered.connect(
            lambda: self.context_action.emit("delete", game))
        menu.addSeparator()
        menu.addAction("Duplicate").triggered.connect(
            lambda: self.context_action.emit("duplicate", game))

        hide_text = "Remove from hidden" if game.hidden else "Hide"
        menu.addAction(hide_text).triggered.connect(
            lambda: self.context_action.emit("hide", game))

        fav_text = "Remove from favorites" if getattr(game, "favorite", False) else "Add to favorites"
        menu.addAction(fav_text).triggered.connect(
            lambda: self.context_action.emit("favorite", game))

        menu.addSeparator()

        cat_menu = menu.addMenu("Category")
        categories = self._load_categories()
        current_cats = self._current_categories()
        for cat in categories:
            prefix = "\u2713 " if cat in current_cats else "   "
            act = cat_menu.addAction(f"{prefix}{cat}")
            act.triggered.connect(
                lambda checked=False, c=cat: self.context_action.emit("category", (game, c)))

        menu.addSeparator()

        game_dir = os.path.dirname(game.path) if game.path else ""
        act_loc = menu.addAction("Open game location")
        act_loc.setEnabled(bool(game_dir))
        act_loc.triggered.connect(
            lambda: self.context_action.emit("game_location", game))

        act_pre = menu.addAction("Open prefix location")
        act_pre.setEnabled(bool(game.prefix and os.path.isdir(game.prefix)))
        act_pre.triggered.connect(
            lambda: self.context_action.emit("prefix_location", game))

        menu.addAction("Run file").triggered.connect(
            lambda: self.context_action.emit("run_file", game))

        proton_log = f"{_LOGS_DIR}/{game.gameid}/proton.log"
        act_logs = menu.addAction("Show logs")
        act_logs.setEnabled(os.path.exists(proton_log))
        act_logs.triggered.connect(
            lambda: self.context_action.emit("show_logs", game))

        menu.exec_(QCursor.pos())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.game)
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _on_fav_clicked(self):
        new_val = not getattr(self.game, "favorite", False)
        self.set_favorite(new_val)
        self.context_action.emit("favorite", self.game)

    def _update_fav_icon(self):
        if getattr(self.game, "favorite", False):
            self._fav_btn.setText("\u2605")
            self._fav_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; border-radius: 6px;"
                " font-size: 18px; color: #c084fc; }"
                "QPushButton:hover { background: rgba(138, 92, 246, 0.2); }"
            )
        else:
            self._fav_btn.setText("\u2606")
            self._fav_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none; border-radius: 6px;"
                " font-size: 18px; color: rgba(200, 184, 224, 0.4); }"
                "QPushButton:hover { background: rgba(138, 92, 246, 0.2); }"
            )

    def _load_categories(self):
        if not os.path.exists(_CATEGORIES_FILE):
            return []
        try:
            with open(_CATEGORIES_FILE, "r", encoding="utf-8") as f:
                return sorted([l.strip() for l in f if l.strip()], key=str.lower)
        except OSError:
            return []

    def _current_categories(self):
        raw = getattr(self.game, "category", [])
        if isinstance(raw, str):
            return [raw] if raw else []
        if isinstance(raw, list):
            return raw
        return []

    def _card_stylesheet(self):
        return """
            #GameCard {
                background-color: rgba(25, 18, 38, 180);
                border-radius: 12px;
                border: 1px solid rgba(138, 92, 246, 0.12);
            }
            #GameCard:hover {
                background-color: rgba(35, 25, 52, 220);
                border-color: rgba(138, 92, 246, 0.35);
            }
        """
