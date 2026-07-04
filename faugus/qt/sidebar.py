"""Sidebar widget — modern design with active indicator."""

import logging

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QButtonGroup, QMenu, QPushButton, QVBoxLayout, QWidget, QLabel, QFrame,
)


class Sidebar(QWidget):
    view_changed = Signal(str)
    clear_recents_clicked = Signal()

    _NAV_ITEMS = [
        ("library", "\U0001f4da  Library"),
        ("recents", "\U0001f552  Recents"),
        ("favorites", "\u2b50  Favorites"),
    ]

    def __init__(self, is_big=True, show_sidebar=True, parent=None):
        logger.debug("Sidebar.__init__: is_big=%s, show_sidebar=%s", is_big, show_sidebar)
        super().__init__(parent)
        self.buttons = {}
        self.setObjectName("sidebar")
        self.setProperty("class", "sidebar")

        self.setFixedWidth(230 if is_big else 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        if is_big:
            header = QWidget()
            header_layout = QVBoxLayout(header)
            header_layout.setContentsMargins(20, 20, 20, 24)
            header_layout.setSpacing(4)

            brand = QLabel("Faugus")
            brand.setStyleSheet(
                "font-size: 22px; font-weight: 700; color: #ffffff;"
                " letter-spacing: 0.5px; background: transparent;"
            )
            header_layout.addWidget(brand)

            subtitle = QLabel("umu frontend")
            subtitle.setStyleSheet(
                "font-size: 12px; color: rgba(200, 184, 224, 0.4);"
                " background: transparent;"
            )
            header_layout.addWidget(subtitle)

            layout.addWidget(header)

            # Divider
            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet("background: rgba(138, 92, 246, 0.08);")
            layout.addWidget(div)

        layout.addSpacing(8)

        # Navigation group (exclusive selection)
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        for view_name, label in self._NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("class", "sidebar-btn")
            btn.clicked.connect(lambda checked, v=view_name: self.set_view(v))

            if view_name == "recents":
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(
                    self._show_recents_context_menu)

            self._nav_group.addButton(btn)
            layout.addWidget(btn)
            self.buttons[view_name] = btn

        layout.addStretch()

        # Bottom section divider
        bot_div = QFrame()
        bot_div.setFixedHeight(1)
        bot_div.setStyleSheet("background: rgba(138, 92, 246, 0.08);")
        bot_div.setContentsMargins(8, 0, 8, 0)
        layout.addWidget(bot_div)

        layout.addSpacing(4)

        # Add game
        btn_add = QPushButton("\u2795  Add Game")
        btn_add.setCheckable(True)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setProperty("class", "sidebar-btn")
        btn_add.clicked.connect(lambda: self.set_view("add"))
        layout.addWidget(btn_add)
        self.buttons["add"] = btn_add
        self._nav_group.addButton(btn_add)

        # Settings
        btn_settings = QPushButton("\u2699  Settings")
        btn_settings.setCheckable(True)
        btn_settings.setCursor(Qt.PointingHandCursor)
        btn_settings.setProperty("class", "sidebar-btn")
        btn_settings.clicked.connect(lambda: self.set_view("settings"))
        layout.addWidget(btn_settings)

        self.buttons["settings"] = btn_settings
        self._nav_group.addButton(btn_settings)

        layout.addSpacing(4)

        # Footer version label
        ver = QLabel("v2.0.0")
        ver.setStyleSheet(
            "font-size: 11px; color: rgba(200, 184, 224, 0.2);"
            " background: transparent; padding: 8px 20px;"
        )
        layout.addWidget(ver)

        self._is_big = is_big
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setVisible(show_sidebar)

    def set_big_mode(self, is_big):
        logger.debug("Sidebar.set_big_mode: is_big=%s", is_big)
        self._is_big = is_big
        self.setFixedWidth(230 if is_big else 160)

    def clear_selection(self):
        self._nav_group.setExclusive(False)
        for btn in self._nav_group.buttons():
            btn.setChecked(False)
        self._nav_group.setExclusive(True)

    def set_view(self, view_name):
        logger.debug("Sidebar.set_view: view_name=%s", view_name)
        for name, btn in self.buttons.items():
            btn.setChecked(name == view_name)
            if name == view_name:
                btn.setProperty("class", "sidebar-btn sidebar-active")
            else:
                btn.setProperty("class", "sidebar-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.view_changed.emit(view_name)

    def _show_recents_context_menu(self, pos):
        logger.debug("Sidebar._show_recents_context_menu")
        menu = QMenu(self)
        clear_action = menu.addAction("\U0001f5d1  Clear recents")
        clear_action.triggered.connect(self.clear_recents_clicked.emit)
        menu.exec_(QCursor.pos())
