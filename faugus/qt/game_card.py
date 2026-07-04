"""Game card widget — modern glassmorphism design."""

import logging
import os

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor, QCursor, QPainter, QBrush, QPen, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMenu, QSizePolicy, QGraphicsDropShadowEffect,
)

from faugus.core.models import Game
from faugus.path_manager import PathManager

_BANNER_PLACEHOLDER = PathManager.system_data("faugus-launcher/faugus-banner.png")
_DEFAULT_ICON = PathManager.get_icon("faugus-launcher.svg")
_LOGS_DIR = PathManager.user_config("faugus-launcher/logs")
_CATEGORIES_FILE = PathManager.user_config("faugus-launcher/categories.txt")


def _scaled_pixmap(path, width, height):
    logger.debug("_scaled_pixmap: path=%s, width=%s, height=%s", path, width, height)
    if path and os.path.isfile(path):
        pixmap = QPixmap(path)
    else:
        pixmap = QPixmap(_DEFAULT_ICON)
    if pixmap.isNull():
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(25, 18, 38))
    dpr = pixmap.devicePixelRatio() or 1.0
    scaled = pixmap.scaled(
        int(width * dpr), int(height * dpr),
        Qt.KeepAspectRatio, Qt.SmoothTransformation,
    )
    scaled.setDevicePixelRatio(dpr)
    return scaled


def _banner_pixmap(path, zoom_pct=100):
    logger.debug("_banner_pixmap: path=%s, zoom_pct=%s", path, zoom_pct)
    w = int(230 * (zoom_pct / 100.0))
    h = int(w * 1.5)
    return _scaled_pixmap(path, w, h)


class GameCard(QWidget):
    context_action = Signal(str, object)
    doubleClicked = Signal(object)

    def __init__(self, game, mode="Banners", zoom_pct=100, parent=None):
        logger.debug("GameCard.__init__: gameid=%s, mode=%s, zoom_pct=%s", game.gameid, mode, zoom_pct)
        super().__init__(parent)
        self.game = game
        self._mode = mode
        self._zoom_pct = zoom_pct
        self._playing = False
        self._hovered = False

        self.setObjectName("GameCard")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        # Content layout
        body = QVBoxLayout(self)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setMouseTracking(True)
        self._image_label.setStyleSheet(
            "QLabel { border-top-left-radius: 14px; border-top-right-radius: 14px;"
            " border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; }"
        )

        self._title_label = QLabel(game.title)
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setWordWrap(True)
        self._title_label.setMaximumHeight(52)
        self._title_label.setMouseTracking(True)
        self._title_label.setStyleSheet(
            "color: #e8e0f0; font-size: 14px; font-weight: 500;"
            " padding: 2px 8px; background: transparent; border: none;"
        )

        if self._mode == "List":
            self._build_list_mode(body)
        elif self._mode == "Blocks":
            self._build_blocks_mode(body)
        else:
            self._build_banners_mode(body)

        # Overlay: playing indicator
        self._overlay = QLabel("\u25b6", self)
        self._overlay.setAlignment(Qt.AlignCenter)
        self._overlay.setStyleSheet(
            "color: rgba(255,255,255,0.9); font-size: 36px;"
            " background: rgba(0,0,0,0.55); border-radius: 14px;"
        )
        self._overlay.hide()

        # Selection frame
        self._sel_frame = QWidget(self)
        self._sel_frame.setStyleSheet(
            "background: transparent; border: 3px solid rgba(167, 139, 250, 0.9);"
            " border-radius: 14px;"
        )
        self._sel_frame.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._sel_frame.hide()

        # Favorite button — created last so it's on top in z-order
        self._fav_btn = QPushButton(self)
        self._fav_btn.setFixedSize(34, 34)
        self._fav_btn.setCursor(Qt.PointingHandCursor)
        self._fav_btn.clicked.connect(self._on_fav_clicked)
        self._update_fav_icon()

        # Age label
        self._age_label = QLabel(self)
        self._age_label.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 500; color: #e8e0f0;"
            " background: rgba(12, 9, 22, 0.75); padding: 4px 10px;"
            " border-radius: 8px; }"
        )
        self._age_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._age_label.hide()

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # Force button to top of z-order
        self._fav_btn.raise_()
        self._age_label.raise_()

    def resizeEvent(self, event):
        logger.debug("GameCard.resizeEvent: w=%s, h=%s", self.width(), self.height())
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        pad = 8
        self._overlay.setGeometry(0, 0, w, h)
        self._sel_frame.setGeometry(0, 0, w, h)
        self._fav_btn.move(w - 34 - pad, pad)
        aw = self._age_label.sizeHint().width()
        self._age_label.move(w - aw - pad, h - 30)

    def enterEvent(self, event):
        logger.debug("GameCard.enterEvent: game=%s", self.game.title)
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        logger.debug("GameCard.leaveEvent: game=%s", self.game.title)
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        logger.debug("GameCard.paintEvent: hasFocus=%s, _hovered=%s", self.hasFocus(), self._hovered)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = 14

        grad = QLinearGradient(0, 0, 0, h)
        if self.hasFocus():
            grad.setColorAt(0, QColor(138, 92, 246, 35))
            grad.setColorAt(0.5, QColor(138, 92, 246, 18))
            grad.setColorAt(1, QColor(138, 92, 246, 5))
            border = QColor(167, 139, 250, 180)
            pen_w = 2
        elif self._hovered:
            grad.setColorAt(0, QColor(138, 92, 246, 22))
            grad.setColorAt(0.5, QColor(138, 92, 246, 12))
            grad.setColorAt(1, QColor(138, 92, 246, 4))
            border = QColor(138, 92, 246, 80)
            pen_w = 1
        else:
            grad.setColorAt(0, QColor(138, 92, 246, 12))
            grad.setColorAt(0.5, QColor(138, 92, 246, 6))
            grad.setColorAt(1, QColor(138, 92, 246, 2))
            border = QColor(138, 92, 246, 18)
            pen_w = 1

        p.setBrush(QBrush(grad))
        p.setPen(QPen(border, pen_w))
        p.drawRoundedRect(0, 0, w, h, r, r)
        p.end()

    # ---- Mode builders ----

    def _build_list_mode(self, layout):
        logger.debug("GameCard._build_list_mode: game=%s", self.game.title)
        row = QHBoxLayout()
        row.setContentsMargins(12, 12, 12, 12)
        row.setSpacing(12)
        icon_px = _scaled_pixmap(self.game.icon, 42, 42)
        self._image_label.setPixmap(icon_px)
        self._image_label.setFixedSize(42, 42)
        self._title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._title_label.setStyleSheet(
            "color: #e8e0f0; font-size: 15px; font-weight: 500;"
            " padding: 0; background: transparent; border: none;"
        )
        row.addWidget(self._image_label)
        row.addWidget(self._title_label, 1)
        layout.addLayout(row)
        self.setFixedHeight(66)

    def _build_blocks_mode(self, layout):
        logger.debug("GameCard._build_blocks_mode: game=%s", self.game.title)
        block = 110
        icon_px = _scaled_pixmap(self.game.icon, block, block)
        self._image_label.setPixmap(icon_px)
        self._image_label.setFixedSize(block, block)
        self._title_label.setMaximumWidth(block + 40)
        self._title_label.setStyleSheet(
            "margin: 10px; font-size: 13px; font-weight: 500;"
            " color: #e8e0f0; background: transparent; border: none;"
        )
        layout.addWidget(self._image_label, 0, Qt.AlignHCenter)
        layout.addWidget(self._title_label, 0, Qt.AlignHCenter)
        self.setFixedWidth(block + 40)

    def _build_banners_mode(self, layout):
        logger.debug("GameCard._build_banners_mode: game=%s, banner=%s", self.game.title, self.game.banner)
        banner_path = self.game.banner
        if not os.path.isfile(banner_path):
            banner_path = _BANNER_PLACEHOLDER
        px = _banner_pixmap(banner_path, self._zoom_pct)
        self._image_label.setPixmap(px)
        self._image_label.setFixedSize(px.size())
        self._title_label.setFixedHeight(52)
        layout.addWidget(self._image_label, 0, Qt.AlignHCenter)
        layout.addWidget(self._title_label, 0, Qt.AlignHCenter)

    # ---- Public API ----

    def set_playing(self, playing):
        logger.debug("GameCard.set_playing: game=%s, playing=%s", self.game.title, playing)
        self._playing = playing
        self._overlay.setVisible(playing)

    def set_age_label(self, text):
        logger.debug("GameCard.set_age_label: text=%s", text)
        if text:
            self._age_label.setText(text)
            self._age_label.setFixedWidth(self._age_label.sizeHint().width())
            self._age_label.show()
        else:
            self._age_label.hide()

    def update_banner(self, banner_path, zoom_pct):
        logger.debug("GameCard.update_banner: path=%s, zoom_pct=%s", banner_path, zoom_pct)
        self._zoom_pct = zoom_pct
        if self._mode != "Banners":
            return
        if not os.path.isfile(banner_path):
            banner_path = _BANNER_PLACEHOLDER
        px = _banner_pixmap(banner_path, zoom_pct)
        self._image_label.setPixmap(px)
        self._image_label.setFixedSize(px.size())

    def set_favorite(self, fav):
        logger.debug("GameCard.set_favorite: game=%s, fav=%s", self.game.title, fav)
        self.game.favorite = fav
        self._update_fav_icon()

    # ---- Context menu ----

    def _add_action(self, menu, text, callback, enabled=True):
        act = menu.addAction(text)
        act.setEnabled(enabled)
        act.triggered.connect(callback)
        return act

    def contextMenuEvent(self, event):
        logger.debug("GameCard.contextMenuEvent: game=%s", self.game.title)
        game = self.game
        menu = QMenu(self)

        self._add_action(menu, "Play", lambda: self.context_action.emit("play", game))
        self._add_action(menu, "Edit", lambda: self.context_action.emit("edit", game))
        self._add_action(menu, "Delete", lambda: self.context_action.emit("delete", game))

        menu.addSeparator()

        hide_label = "Unhide" if game.hidden else "Hide"
        self._add_action(menu, hide_label, lambda: self.context_action.emit("hide", game))
        fav_label = "Remove favorite" if getattr(game, "favorite", False) else "Add favorite"
        self._add_action(menu, fav_label, lambda: self.context_action.emit("favorite", game))

        menu.addSeparator()

        # Category submenu
        cat_menu = menu.addMenu("Category")
        categories = self._load_categories()
        current_cats = self._current_categories()
        for cat in categories:
            act = cat_menu.addAction(cat)
            act.setCheckable(True)
            act.setChecked(cat in current_cats)
            act.triggered.connect(
                lambda checked=False, c=cat: self.context_action.emit("category", (game, c)))

        menu.addSeparator()

        game_dir = os.path.dirname(game.path) if game.path else ""
        self._add_action(menu, "Open game folder",
                         lambda: self.context_action.emit("game_location", game),
                         enabled=bool(game_dir))
        self._add_action(menu, "Open prefix folder",
                         lambda: self.context_action.emit("prefix_location", game),
                         enabled=bool(game.prefix and os.path.isdir(game.prefix)))

        proton_log = f"{_LOGS_DIR}/{game.gameid}/proton.log"
        self._add_action(menu, "Show logs",
                         lambda: self.context_action.emit("show_logs", game),
                         enabled=os.path.exists(proton_log))

        menu.exec_(QCursor.pos())

    # ---- Events ----

    def mousePressEvent(self, event):
        logger.debug("GameCard.mousePressEvent: button=%s", event.button())
        if event.button() == Qt.LeftButton:
            self.setFocus()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        logger.debug("GameCard.mouseDoubleClickEvent: game=%s", self.game.title)
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.game)
        super().mouseDoubleClickEvent(event)

    def focusInEvent(self, event):
        logger.debug("GameCard.focusInEvent: game=%s", self.game.title)
        super().focusInEvent(event)
        self._sel_frame.show()
        self.update()

    def focusOutEvent(self, event):
        logger.debug("GameCard.focusOutEvent: game=%s", self.game.title)
        super().focusOutEvent(event)
        self._sel_frame.hide()
        self.update()

    # ---- Helpers ----

    def _on_fav_clicked(self):
        logger.debug("GameCard._on_fav_clicked: game=%s", self.game.title)
        self.context_action.emit("favorite", self.game)

    def _update_fav_icon(self):
        logger.debug("GameCard._update_fav_icon: game=%s", self.game.title)
        is_fav = getattr(self.game, "favorite", False)
        self._fav_btn.setText("\u2605" if is_fav else "\u2606")
        color = "#c084fc" if is_fav else "rgba(224, 216, 240, 0.4)"
        hover = "rgba(138, 92, 246, 0.25)" if not is_fav else "rgba(192, 132, 252, 0.3)"
        self._fav_btn.setStyleSheet(
            f"QPushButton {{ background: rgba(0,0,0,0.4); border: none;"
            f" border-radius: 8px; font-size: 20px; color: {color}; }}"
            f"QPushButton:hover {{ background: {hover}; }}"
        )

    def _load_categories(self):
        logger.debug("GameCard._load_categories")
        if not os.path.exists(_CATEGORIES_FILE):
            return []
        try:
            with open(_CATEGORIES_FILE, "r", encoding="utf-8") as f:
                return sorted([l.strip() for l in f if l.strip()], key=str.lower)
        except OSError:
            return []

    def _current_categories(self):
        logger.debug("GameCard._current_categories: game=%s", self.game.title)
        raw = getattr(self.game, "category", [])
        if isinstance(raw, str):
            return [raw] if raw else []
        if isinstance(raw, list):
            return raw
        return []
